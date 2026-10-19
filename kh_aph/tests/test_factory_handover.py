"""Capability nguồn nhà máy không trở thành quyền chung lên H/JE/sổ cái."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from decimal import Decimal


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class FactoryHandover(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package=kh_aph
        self.names=('cash_closing','cash_custody','personal_cash','factory_cash','cash_handover','factory_handover')
        self.saved={n:getattr(kh_aph,n,None) for n in self.names}
        self.f=types.ModuleType('frappe');self.f.session=Row(user='dung');self.f.conf={'kh_aph_factory_handover':1}
        self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.throw=lambda msg,exc=ValueError:(_ for _ in ()).throw(exc(msg));self.f.PermissionError=PermissionError
        self.f.db=Mock();self.f.db.sql.return_value=[]
        self.c=types.ModuleType('kh_aph.cash_closing');self.c.enabled=lambda:True;self.c.roles_for=lambda user=None:{'Kế toán nhà máy'} if not user or user=='dung' else {'Accounts User'}
        self.c.scope=Mock()
        self.custody=types.ModuleType('kh_aph.cash_custody');self.custody.enabled=lambda:True;self.custody.HOLDER='holder';self.custody._person=Mock()
        self.p=types.ModuleType('kh_aph.personal_cash');self.p.ROLES={'Kế toán nhà máy','Accounts User'};self.p.RESTRICTED={'Kế toán nhà máy'};self.p._scope=Mock();self.p._ledger=Mock()
        self.factory=types.ModuleType('kh_aph.factory_cash');self.factory.enabled=lambda:True;self.factory.DT='Factory';self.factory.LOAI_BAN_GIAO='Bàn giao tiền';self.factory._quy=lambda co:'factory';self.factory.TT_HUY='Đã hủy';self.factory.TT_CHO_NHAN='Chờ nhận'
        self.h=types.ModuleType('kh_aph.cash_handover');self.h.enabled=lambda:True;self.h.DT='APH Ban giao tien';self.h.target=Mock()
        self.u=types.ModuleType('frappe.utils');self.u.cint=lambda v:int(v or 0)
        self.permissions=types.ModuleType('frappe.permissions');self.permissions.has_user_permission=Mock(return_value=True)
        mapping={'frappe':self.f,'frappe.utils':self.u,'frappe.permissions':self.permissions}
        for n,value in [('cash_closing',self.c),('cash_custody',self.custody),('personal_cash',self.p),('factory_cash',self.factory),('cash_handover',self.h)]:
            mapping['kh_aph.'+n]=value;setattr(kh_aph,n,value)
        self.patch=patch.dict(sys.modules,mapping);self.patch.start();sys.modules.pop('kh_aph.factory_handover',None)
        self.m=importlib.import_module('kh_aph.factory_handover')
        self.source=Row(name='S',company='APH',loai='Bàn giao tiền',holder='dung',nguoi_nhan='kt',quy_giao='factory',tai_khoan_nhan='cash',tong_tien=100,ban_giao_tien='H',docstatus=1)
        self.doc=Row(doctype=self.h.DT,name='H',company='APH',from_account='factory',to_account='cash',from_holder='dung',to_holder='kt',requested_amount=100,factory_source='S',flags=Row(),check_permission=Mock(),get_doc_before_save=lambda:None)
        self.co=Row(company='APH',default_currency='VND',check_permission=Mock())
        self.acc=Row(company='APH',account_type='Cash',is_group=0,disabled=0,account_currency='VND',check_permission=Mock())
        self.f.get_doc=Mock(side_effect=lambda dt,name,**kw:self.co if dt=='Company' else self.acc if dt=='Account' else self.source if dt=='Factory' else self.doc)
    def tearDown(self):
        sys.modules.pop('kh_aph.factory_handover',None)
        for n,value in self.saved.items():
            if value is None:
                if hasattr(self.package,n):delattr(self.package,n)
            else:setattr(self.package,n,value)
        self.patch.stop()
    def test_off_guest_role_denied_before_source_or_ledger(self):
        self.f.conf={}
        ordinary=Mock(return_value="native")
        self.assertEqual(self.m.route(ordinary)("H"),"native")
        with self.assertRaises(ValueError):self.m._load('S')
        self.f.conf={'kh_aph_factory_handover':1};self.f.session.user='Guest'
        with self.assertRaises(PermissionError):self.m._load('S')
        self.f.session.user='dung';self.c.roles_for=lambda *a:{'Stock User'}
        with self.assertRaises(PermissionError):self.m._load('S')
        self.f.get_doc.assert_not_called();self.f.db.sql.assert_not_called()
    def test_capability_is_actor_and_source_bound_and_always_restored(self):
        with self.m.operation(self.source):
            self.assertTrue(self.m.active());self.m.check(self.doc,'submit');self.assertTrue(self.doc.flags.ignore_permissions)
            wrong=Row(self.doc);wrong.from_holder='other';wrong.check_permission=Mock(side_effect=PermissionError)
            with self.assertRaises(PermissionError):self.m.check(wrong)
            self.f.session.user='kt';self.assertFalse(self.m.active());self.f.session.user='dung'
        self.assertFalse(self.m.active())
        with self.assertRaises(RuntimeError):
            with self.m.operation(self.source):raise RuntimeError('rollback')
        self.assertFalse(self.m.active())
    def test_native_origin_cannot_be_forged_or_unlinked(self):
        with self.assertRaises(PermissionError):self.m.validate_origin(self.doc)
        self.doc.factory_source=None;self.doc.get_doc_before_save=lambda:Row(factory_source='S')
        with self.assertRaises(ValueError):self.m.validate_origin(self.doc)
    def test_company_actor_and_cash_lock_checked_before_source_mutation(self):
        self.assertEqual(self.m._load('S'),self.source)
        self.co.check_permission.assert_called_once_with('read');self.custody._person.assert_called_with('dung','APH')
        self.assertIn('order by name for update',self.f.db.sql.call_args.args[0])
        self.source.holder='other'
        with self.assertRaises(PermissionError):self.m._load('S')
    def test_scope_rejects_changed_factory_and_account_permission(self):
        with self.m.operation(self.source):
            self.m.scope(self.doc);self.p._scope.assert_called_once_with('APH','factory')
            self.acc.check_permission.assert_not_called()
            self.permissions.has_user_permission.return_value=False
            with self.assertRaises(PermissionError):self.m.scope(self.doc)
            self.permissions.has_user_permission.return_value=True;self.factory._quy=lambda co:'changed'
            with self.assertRaises(ValueError):self.m.scope(self.doc)
    def test_cash_and_target_cannot_escape_source_tuple(self):
        with self.m.operation(self.source):
            for company,account in [('VH','cash'),('APH','other')]:
                with self.assertRaises(PermissionError):self.m.cash_scope(company,account)
                with self.assertRaises(PermissionError):self.m.target(company,account)
            self.assertIs(self.m.ledger_reader(),self.p._ledger)
        self.assertIsNone(self.m.ledger_reader())
    def test_pending_legacy_cannot_receive_without_reservation(self):
        self.source.ban_giao_tien=None
        with self.assertRaisesRegex(ValueError,'giữ chỗ'):self.m.receive_source('S',100,'cash')
        self.source.ban_giao_tien='H'
        with self.assertRaisesRegex(ValueError,'Quỹ nhận khác'):self.m.receive_source('S',100,'other')
    def test_reverse_capability_requires_exact_original_money_accounts_and_people(self):
        self.doc.received_amount=95
        reverse=Row(doctype=self.h.DT,reversal_of='H',company='APH',from_account='cash',to_account='factory',from_holder='kt',to_holder='dung',requested_amount=95)
        with self.m.operation(self.source):
            self.assertTrue(self.m._bound(reverse))
            for field,value in [('requested_amount',100),('from_account','bank'),('to_holder','other'),('company','VH')]:
                old=reverse[field];reverse[field]=value;self.assertFalse(self.m._bound(reverse));reverse[field]=old
    def test_private_result_never_returns_je_or_snapshots(self):
        value=self.m._result({'name':'H','journal_entry':'JE','status':'Đã nhận'})
        self.assertEqual(value,{'name':'H','status':'Đã nhận'})
    def test_sender_is_explicit_not_owner_and_target_required_before_h_insert(self):
        self.source.holder='';self.source.owner='dung'
        with self.assertRaises(PermissionError):self.m.send_source(self.source)
        self.source.holder='dung';self.source.tai_khoan_nhan=None
        with self.assertRaisesRegex(ValueError,'Chọn quỹ'):self.m.send_source(self.source)
        self.f.db.sql.assert_not_called()
