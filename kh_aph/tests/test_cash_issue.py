"""Không gỡ chặn lệch bằng mốc cũ, ca lệch hoặc bằng chứng đã lỗi thời."""
import importlib
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import Mock,patch

class Doc(dict):
    __getattr__=dict.get
    __setattr__=dict.__setitem__

class Issue(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package=kh_aph
        self.saved={n:getattr(kh_aph,n,None) for n in ('cash_closing','cash_handover','cash_issue')}
        self.f=types.ModuleType('frappe');self.f.session=Doc(user='chief');self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.throw=lambda msg,exc=ValueError:(_ for _ in ()).throw(exc(msg))
        self.c=types.ModuleType('kh_aph.cash_closing');self.c.SHIFT='APH Chot ca tien';self.c.MANAGERS={'Accounts Manager','System Manager'}
        self.c.guard=Mock();self.c.scope=Mock();self.c.check_evidence=Mock();self.c.roles_for=Mock(return_value={'Accounts Manager'})
        self.h=types.ModuleType('kh_aph.cash_handover');self.h.DT='APH Ban giao tien';self.h.PENDING=('Chờ nhận','Vượt nguồn cần xử lý');self.h.enabled=lambda:True;self.h.guard=Mock();self.h.transfer_state=Mock(return_value=({},'transfers'))
        self.u=types.ModuleType('frappe.utils');self.u.now_datetime=Mock();self.u.get_datetime=lambda v:datetime.fromisoformat(v)
        self.p=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':self.u,'kh_aph.cash_closing':self.c,'kh_aph.cash_handover':self.h})
        self.p.start();kh_aph.cash_closing=self.c;kh_aph.cash_handover=self.h
        self.cached=sys.modules.pop('kh_aph.cash_issue',None)
        self.m=importlib.import_module('kh_aph.cash_issue')
        self.source=Doc(doctype=self.c.SHIFT,name='old',docstatus=1,company='APH',account='1111',holder='a',difference=-10,closed_at='2026-10-19 00:01:00')
        self.opening=Doc(name='new',closed_at='2026-10-19 00:02:00')
        self.shift=Doc(name='clean',verification='new',difference=0,closed_at='2026-10-19 00:03:00',source_hash='ledger',transfer_hash='transfers',check_permission=Mock())
        self.c._state=Mock(return_value=(self.opening,self.shift,[],{}))
        self.m.source_for=Mock(return_value=self.source);self.m._active=Mock(return_value=[]);self.m.anchor=Mock(return_value=('rows','ledger'))
        self.doc=Doc(name='R',_action='submit',result='đã đối chiếu',evidence='/private/files/proof.txt',get_doc_before_save=lambda:None,
            proofs=[Doc(account='1111',holder='a',verification='new',shift='clean')])
    def tearDown(self):
        sys.modules.pop('kh_aph.cash_issue',None)
        if self.cached:sys.modules['kh_aph.cash_issue']=self.cached
        for n,v in self.saved.items():
            if v is None:
                if hasattr(self.package,n):delattr(self.package,n)
            else:setattr(self.package,n,v)
        self.p.stop()
    def test_complete_proof_passes_without_altering_source_money(self):
        original=dict(self.source);self.m.validate(self.doc)
        self.assertEqual(self.source,original);self.c.check_evidence.assert_called_once_with(self.doc)
    def test_prior_verification_is_not_resolution(self):
        self.opening.closed_at='2026-10-19 00:00:00'
        with self.assertRaisesRegex(ValueError,'mốc xác minh mới'):self.m.validate(self.doc)
    def test_nonzero_count_does_not_release_wallet(self):
        self.shift.difference=1
        with self.assertRaisesRegex(ValueError,'Ca căn cứ phải khớp'):self.m.validate(self.doc)
    def test_new_ledger_or_transfer_requires_another_count(self):
        self.shift.source_hash='old'
        with self.assertRaisesRegex(ValueError,'Sổ hoặc trách nhiệm đã đổi'):self.m.validate(self.doc)
        self.shift.source_hash='ledger';self.shift.transfer_hash='old'
        with self.assertRaisesRegex(ValueError,'Sổ hoặc trách nhiệm đã đổi'):self.m.validate(self.doc)
    def test_cannot_substitute_other_holder_or_reuse_active_resolution(self):
        self.doc.proofs[0].holder='b'
        with self.assertRaisesRegex(ValueError,'đúng quỹ/người'):self.m.validate(self.doc)
        self.doc.proofs[0].holder='a';self.m._active.return_value=[['other']]
        with self.assertRaisesRegex(ValueError,'đối chiếu khác'):self.m.validate(self.doc)
    def test_evidence_required_at_confirmation(self):
        self.doc.evidence=None
        with self.assertRaisesRegex(ValueError,'căn cứ riêng tư'):self.m.validate(self.doc)
    def test_no_cost_manager_cannot_read_results(self):
        self.c.roles_for.return_value={'Accounts Manager','APH Không xem giá vốn'}
        self.assertFalse(self.m.has_permission(self.doc));self.assertEqual(self.m.query_conditions(),'1=0')
    def test_confirmed_result_is_immutable(self):
        with self.assertRaisesRegex(ValueError,'Giữ nguyên kết quả'):self.m.prevent_change(self.doc)
    def test_cancelled_history_cannot_be_deleted(self):
        self.m.prevent_delete(Doc(docstatus=0))
        for status in (1,2):
            with self.assertRaisesRegex(ValueError,'không xóa hồ sơ'):self.m.prevent_delete(Doc(docstatus=status))
    def test_cancelled_observed_handover_is_history_not_a_new_transfer(self):
        self.doc.source_type=self.h.DT
        self.source.docstatus=2;self.source.receive_hash='observed';self.source.issue_state='Chờ xử lý'
        links=[('source_name','H','nguồn'),('other_field','V','căn cứ khác')]
        self.assertEqual(self.m.cancelled_links(self.doc,links),[links[1]])
        self.m.source_for.assert_called_once_with(self.doc)
    def test_cancelled_unobserved_source_does_not_get_exception(self):
        self.doc.source_type=self.h.DT;self.source.docstatus=2;self.source.receive_hash=None
        links=[('source_name','H','nguồn')]
        self.assertEqual(self.m.cancelled_links(self.doc,links),links)
    def test_cancelled_other_source_type_keeps_native_validation(self):
        self.doc.source_type=self.c.SHIFT
        links=[('source_name','S','ca')]
        self.assertEqual(self.m.cancelled_links(self.doc,links),links)
        self.m.source_for.assert_not_called()
