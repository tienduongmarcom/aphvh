"""Capability nhận tiền chỉ tồn tại đúng actor/nguồn và không mở quyền sổ."""
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch


class Row(dict):
    def __getattr__(self, key): return self.get(key)
    def __setattr__(self, key, value): self[key] = value


class CashReceiver(TestCase):
    def setUp(self):
        import kh_aph
        self.f=ModuleType('frappe');self.f.session=SimpleNamespace(user='owner')
        self.f.PermissionError=PermissionError
        self.f.throw=lambda message,error=ValueError:(_ for _ in ()).throw(error(message))
        self.c=ModuleType('kh_aph.cash_closing');self.c.enabled=lambda:True
        self.c.MANAGERS={'Accounts Manager','System Manager'}
        self.roles={'Nhận bàn giao tiền'};self.c.roles_for=lambda:self.roles
        self.custody=ModuleType('kh_aph.cash_custody');self.custody.enabled=lambda:True
        self.h=ModuleType('kh_aph.cash_handover');self.h.enabled=lambda:True
        self.acc=Row(company='APH',account_type='Cash',is_group=0,disabled=0,account_currency='VND',check_permission=Mock())
        self.co=Row(default_currency='VND',check_permission=Mock())
        self.f.get_doc=lambda dt,name:self.co if dt=='Company' else self.acc
        self.contexts=[patch.dict('sys.modules',{'frappe':self.f,'kh_aph.cash_closing':self.c,'kh_aph.cash_custody':self.custody,'kh_aph.cash_handover':self.h}),
                       patch.multiple(kh_aph,cash_closing=self.c,cash_custody=self.custody,cash_handover=self.h,create=True)]
        for item in self.contexts:item.start();self.addCleanup(item.stop)
        spec=importlib.util.spec_from_file_location('_cash_receiver_test',Path(__file__).resolve().parents[1]/'cash_receiver.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.doc=Row(doctype='APH Ban giao tien',name='H',company='APH',from_account='a',to_account='b',from_holder='sales',to_holder='owner',requested_amount=100,docstatus=1,flags=SimpleNamespace())

    def test_context_resets_and_no_other_document_or_account(self):
        self.assertFalse(self.m.active())
        with self.m.operation(self.doc):
            self.assertTrue(self.m.bound(self.doc))
            self.m.check(self.doc,'write');self.assertTrue(self.doc.flags.ignore_permissions)
            with self.assertRaises(PermissionError):self.m.target('VH','a')
            with self.assertRaises(PermissionError):self.m.target('APH','other')
            with self.assertRaises(PermissionError):self.m.check(self.doc,'cancel')
        self.assertFalse(self.m.active())
        with self.assertRaises(PermissionError):self.m.check(self.doc)

    def test_changed_tuple_or_actor_cannot_use_context(self):
        with self.m.operation(self.doc):
            self.doc.requested_amount=101
            with self.assertRaises(PermissionError):self.m.scope(self.doc)
            self.doc.requested_amount=100;self.f.session.user='other'
            self.assertFalse(self.m.active())

    def test_self_other_recipient_draft_factory_reverse_denied(self):
        for field,value in [('from_holder','owner'),('to_holder','other'),('docstatus',0),('factory_source','F'),('reversal_of','R')]:
            old=self.doc.get(field);self.doc[field]=value
            with self.assertRaises(PermissionError):
                with self.m.operation(self.doc):pass
            self.doc[field]=old

    def test_no_cost_or_factory_cannot_add_role_to_bypass(self):
        for role in ('APH Không xem giá vốn','Kế toán nhà máy'):
            self.roles.add(role)
            with self.assertRaises(PermissionError):
                with self.m.operation(self.doc):pass
            self.roles.remove(role)

    def test_native_account_permission_still_required(self):
        self.acc.check_permission.side_effect=PermissionError('Ngoài phạm vi')
        with self.assertRaises(PermissionError):
            with self.m.operation(self.doc):pass
        self.assertFalse(self.m.active())
