"""Guard và quyền tiền cá nhân phải được kiểm ở server, kể cả cộng role."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class ClosingAccess(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package=kh_aph
        self.attributes={k:getattr(kh_aph,k,None) for k in ('cash_closing','cash_custody')}
        self.f=types.ModuleType('frappe')
        self.f.conf={'kh_aph_cash_closing':1}
        self.f.session=types.SimpleNamespace(user='a')
        self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.throw=lambda msg,exc=ValueError:(_ for _ in ()).throw(exc(msg))
        self.f.PermissionError=PermissionError
        self.f.get_roles=Mock(return_value=['Accounts User'])
        self.f.db=Mock()
        self.f.db.escape=lambda v:repr(v)
        utils=types.ModuleType('frappe.utils')
        utils.cint=lambda v:int(v or 0)
        utils.getdate=Mock();utils.now_datetime=Mock()
        self.custody=types.ModuleType('kh_aph.cash_custody')
        self.custody.enabled=lambda:True
        self.patcher=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils,'kh_aph.cash_custody':self.custody})
        self.patcher.start()
        kh_aph.cash_custody=self.custody
        sys.modules.pop('kh_aph.cash_closing',None)
        self.m=importlib.import_module('kh_aph.cash_closing')

    def tearDown(self):
        sys.modules.pop('kh_aph.cash_closing',None)
        for k,v in self.attributes.items():
            if v is None:
                if hasattr(self.package,k): delattr(self.package,k)
            else: setattr(self.package,k,v)
        self.patcher.stop()

    def test_flag_off_ledger_hook_has_no_queries(self):
        self.f.conf={}
        self.m.lock_ledger({})
        self.m.schema()
        self.f.db.sql.assert_not_called()
        with self.assertRaises(ValueError):self.m.guard()

    def test_no_cost_and_factory_denied_even_with_manager_roles(self):
        for role in ('APH Không xem giá vốn','Kế toán nhà máy'):
            self.f.get_roles.return_value=[role,'Accounts Manager','System Manager']
            with self.assertRaises(PermissionError):self.m.guard()
            self.assertEqual(self.m.query_conditions(),'1=0')
            self.assertEqual(self.m.opening_query_conditions(),'1=0')
            self.assertFalse(self.m.has_permission(types.SimpleNamespace(doctype=self.m.SHIFT,holder='a')))
        self.f.db.sql.assert_not_called()

    def test_personal_shift_does_not_grant_other_holders_or_opening(self):
        self.m.guard()
        self.assertTrue(self.m.has_permission(types.SimpleNamespace(doctype=self.m.SHIFT,holder='a')))
        self.assertFalse(self.m.has_permission(types.SimpleNamespace(doctype=self.m.SHIFT,holder='b')))
        self.assertFalse(self.m.has_permission(types.SimpleNamespace(doctype=self.m.OPENING,holder='a')))
        self.assertIn("holder='a'",self.m.query_conditions())
        self.assertEqual(self.m.opening_query_conditions(),'1=0')
        with self.assertRaises(PermissionError):self.m.guard(manager=True)

    def test_account_scope_checked_before_any_lock(self):
        company=types.SimpleNamespace(default_currency='VND',check_permission=Mock())
        acc=types.SimpleNamespace(company='VH',check_permission=Mock(),account_type='Cash',is_group=0,disabled=0,account_currency='VND')
        self.f.get_doc=Mock(side_effect=[company,acc])
        with self.assertRaises(ValueError):self.m.scope('APH','wrong')
        company.check_permission.assert_called_once_with('read')
        acc.check_permission.assert_called_once_with('read')
        self.f.db.sql.assert_not_called()

    def test_admin_automatic_all_roles_is_not_a_no_cost_profile(self):
        self.f.session.user='Administrator'
        self.f.get_roles.return_value=['System Manager','APH Không xem giá vốn','Kế toán nhà máy']
        self.m.guard()
        self.assertEqual(self.m.roles_for(),{'System Manager'})
