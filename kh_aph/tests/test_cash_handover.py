"""Bàn giao: không tự nhận, không cộng hai lần, giữ quyền và kết quả retry."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock,patch
from decimal import Decimal

class Row(dict):
    __getattr__=dict.get

class Handover(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package=kh_aph
        self.names=('cash_handover','cash_closing','cash_custody')
        self.saved={k:getattr(kh_aph,k,None) for k in self.names}
        self.f=types.ModuleType('frappe');self.f.conf={'kh_aph_cash_handover':1}
        self.f.session=Row(user='a');self.f.flags=Row()
        self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.throw=lambda msg,exc=ValueError:(_ for _ in ()).throw(exc(msg))
        self.f.PermissionError=PermissionError
        self.f.get_roles=Mock(return_value=['Accounts User'])
        self.f.db=Mock();self.f.db.escape=lambda s:repr(s)
        self.c=types.ModuleType('kh_aph.cash_closing');self.c.MANAGERS={'Accounts Manager','System Manager'}
        self.c.guard=Mock();self.c.enabled=lambda:True
        self.c.roles_for=lambda user=None: set(self.f.get_roles(user))
        self.u=types.ModuleType('frappe.utils');self.u.cint=lambda n:int(n or 0);self.u.now_datetime=Mock();self.u.getdate=Mock()
        self.custody=types.ModuleType('kh_aph.cash_custody')
        self.p=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':self.u,'kh_aph.cash_closing':self.c,'kh_aph.cash_custody':self.custody})
        self.p.start();kh_aph.cash_closing=self.c;kh_aph.cash_custody=self.custody
        sys.modules.pop('kh_aph.cash_handover',None)
        self.m=importlib.import_module('kh_aph.cash_handover')
    def tearDown(self):
        sys.modules.pop('kh_aph.cash_handover',None)
        for k,v in self.saved.items():
            if v is None:
                if hasattr(self.package,k):delattr(self.package,k)
            else:setattr(self.package,k,v)
        self.p.stop()
    def test_flag_off_has_no_db_or_setup_effects(self):
        self.f.conf={}
        self.assertEqual(self.m.transfer_state('APH','1111','T'),({},''))
        self.m.before_verification('APH','1111');self.m.schema()
        self.f.db.sql.assert_not_called()
        with self.assertRaises(ValueError):self.m.guard()
    def test_same_cash_transfers_conserve_total_and_do_not_count_native_je(self):
        def r(name,source='1111',target='1111',state='Đã nhận',ver='T'):
            return Row(name=name,from_account=source,to_account=target,status=state,from_verification=ver,from_holder='a',to_holder='b',received_amount=95,receive_hash=name)
        self.m._query=Mock(return_value=[r('same'),r('native',target='1112'),r('pending',state='Chờ nhận'),r('old',ver='old')])
        changes,proof=self.m.transfer_state('APH','1111','T')
        self.assertEqual(changes,{'a':Decimal(-95),'b':Decimal(95)})
        self.assertEqual(sum(changes.values()),0);self.assertEqual(len(proof),64)
    def test_pending_blocks_reverification_but_accepted_does_not(self):
        self.m._query=Mock(return_value=[Row(status='Chờ nhận')])
        with self.assertRaisesRegex(ValueError,'chờ nhận'):self.m.before_verification('APH','1111')
        self.m._query.return_value=[Row(status='Đã nhận')]
        self.m.before_verification('APH','1111')
    def test_manager_and_admin_cannot_receive_for_target_or_from_self(self):
        self.m._locked=Mock(return_value=Row(from_holder='sender',to_holder='recipient'))
        for user in ['sender','a','Administrator']:
            self.f.session.user=user
            with self.assertRaises(PermissionError):self.m.receive('H',95)
        self.m._locked.return_value=Row(from_holder='a',to_holder='a')
        self.f.session.user='a'
        with self.assertRaises(PermissionError):self.m.receive('H',95)
    def test_accepted_journal_cannot_clear_link_or_cancel(self):
        old=Row(kh_aph_ban_giao_tien='H')
        doc=Row(kh_aph_ban_giao_tien='',get_doc_before_save=lambda:old)
        with self.assertRaisesRegex(ValueError,'Không gỡ'):self.m.protect_journal(doc,'validate')
        doc['kh_aph_ban_giao_tien']='H'
        with self.assertRaises(ValueError):self.m.protect_journal(doc,'before_cancel')
    def test_no_cost_role_cannot_read_even_with_manager(self):
        self.f.get_roles.return_value=['Accounts Manager','APH Không xem giá vốn']
        self.assertFalse(self.m.has_permission(Row(from_holder='a',to_holder='b')))
        self.assertEqual(self.m.query_conditions(),'1=0')
    def test_participants_only_for_accountant(self):
        self.assertTrue(self.m.has_permission(Row(from_holder='a',to_holder='b')))
        self.assertFalse(self.m.has_permission(Row(from_holder='b',to_holder='c')))
        self.assertIn("from_holder='a'",self.m.query_conditions())
    def test_bank_source_only_for_linked_return_to_cash(self):
        self.c.scope=Mock()
        self.custody.cash=lambda account:account.startswith('cash')
        self.m.target=Mock()
        for doc in [Row(company='APH',from_account='bank',to_account='cash',reversal_of=None),Row(company='APH',from_account='bank',to_account='bank2',reversal_of='H')]:
            with self.assertRaisesRegex(ValueError,'Bank chỉ làm nguồn'):self.m._scope(doc)
        self.m._scope(Row(company='APH',from_account='bank',to_account='cash',reversal_of='H'))
        self.c.scope.assert_called_once_with('APH','cash')
    def test_bank_return_journal_has_holder_only_on_cash(self):
        self.custody.cash=lambda account:account.startswith('cash')
        self.custody.HOLDER='holder'
        self.u.getdate.return_value='2026-10-19'
        self.f.get_doc=Mock(return_value=Mock(name='journal'))
        self.m._journal(Row(name='R',company='APH',from_account='bank',to_account='cash',from_holder='b',to_holder='a'),Decimal(50))
        rows=self.f.get_doc.call_args.args[0]['accounts']
        self.assertNotIn('holder',rows[0]);self.assertEqual(rows[1]['holder'],'a')
        self.assertEqual(rows[0]['credit_in_account_currency'],50);self.assertEqual(rows[1]['debit_in_account_currency'],50)
    def test_reverse_rejects_native_creation_or_changed_relationship(self):
        doc=Row(reversal_of='H',reversal_request='T',get_doc_before_save=lambda:None,is_new=lambda:True)
        with self.assertRaisesRegex(ValueError,'Dùng thao tác'):self.m._reverse_origin(doc)
        old=Row(reversal_of='H',reversal_request='T')
        doc=Row(reversal_of='',reversal_request='',get_doc_before_save=lambda:old,is_new=lambda:False)
        with self.assertRaisesRegex(ValueError,'Không thêm, gỡ'):self.m._reverse_origin(doc)
    def test_sent_or_cancelled_history_cannot_be_deleted(self):
        self.m.prevent_delete(Row(docstatus=0))
        for status in (1,2):
            with self.assertRaisesRegex(ValueError,'không xóa hồ sơ'):self.m.prevent_delete(Row(docstatus=status))
    def test_pending_retry_response_is_same_before_and_after_native_db_defaults(self):
        fresh=Row(name='H',status='Chờ nhận',requested_amount=Decimal('40'),received_amount=None,difference=None,journal_entry=None)
        loaded=Row(name='H',status='Chờ nhận',requested_amount=40.0,received_amount=0.0,difference=0.0,journal_entry='')
        self.assertEqual(self.m.result(fresh),self.m.result(loaded))
        self.assertEqual(self.m.result(fresh)['received_amount'],Decimal(0))
