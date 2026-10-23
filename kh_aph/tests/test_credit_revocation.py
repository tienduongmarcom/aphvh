import importlib.util
from pathlib import Path
from types import SimpleNamespace,ModuleType
from unittest import TestCase
from unittest.mock import Mock,patch

class RevocationTests(TestCase):
 def setUp(self):
  self.f=ModuleType('frappe');self.f.session=SimpleNamespace(user='chief@example.invalid')
  self.f.conf={'kh_aph_high_risk_credit_guard':1};self.f.get_roles=Mock(return_value=['Accounts Manager'])
  self.f.PermissionError=PermissionError
  def throw(msg,exc=RuntimeError,**kw):raise exc(msg)
  self.f.throw=throw;self.f.whitelist=lambda **kw:lambda fn:fn
  self.f.db=Mock();self.f.db.get_value.return_value=0
  self.release=Mock(name='approval');self.release.name='AUDIT';self.release.customer='C';self.release.delivery_note='DN'
  self.release.get.return_value=None;self.f.get_doc=Mock(return_value=self.release)
  utils=ModuleType('frappe.utils');utils.cint=lambda n:int(n or 0);utils.now_datetime=lambda:'2026-10-11 13:00:00'
  credit=ModuleType('kh_aph.global_credit');credit.balance_for=Mock(return_value=80000)
  path=Path(__file__).resolve().parents[1]/'credit_release.py'
  spec=importlib.util.spec_from_file_location('_release_test',path);self.m=importlib.util.module_from_spec(spec)
  with patch.dict('sys.modules',{'frappe':self.f,'frappe.utils':utils,'kh_aph.global_credit':credit}):spec.loader.exec_module(self.m)
 def test_accounts_user_cannot_revoke(self):
  self.f.get_roles.return_value=['Accounts User']
  with self.assertRaises(PermissionError):self.m.revoke('AUDIT','why')
  self.f.db.set_value.assert_not_called()
 def test_chief_stamps_revocation(self):
  result=self.m.revoke('AUDIT','  reason  ')
  self.assertEqual(result['revoked_by'],'chief@example.invalid')
  values=self.f.db.set_value.call_args.args[2]
  self.assertEqual(values['revocation_reason'],'reason')
  self.assertEqual(values['revoked_at'],'2026-10-11 13:00:00')
 def test_posted_shipment_cannot_revoke(self):
  self.f.db.get_value.return_value=1
  with self.assertRaises(RuntimeError):self.m.revoke('AUDIT','reason')
  self.f.db.set_value.assert_not_called()
 def test_replay_preserves_original_audit(self):
  self.release.get.return_value='2026-10-11 12:00:00'
  self.release.revoked_by='original';self.release.revoked_at='2026-10-11 12:00:00'
  result=self.m.revoke('AUDIT','new reason')
  self.assertEqual(result['revoked_by'],'original')
  self.f.db.set_value.assert_not_called()

 def invoice(self,source='DN'):
  return SimpleNamespace(customer='C',company='APH',grand_total=15000,items=[SimpleNamespace(delivery_note=source)])
 def test_direct_invoice_cannot_bypass_release(self):
  self.f.db.get_value.return_value=1
  with self.assertRaises(RuntimeError):self.m.before_submit_invoice(self.invoice(None))
 def test_approved_delivery_invoice_allowed(self):
  self.f.db.get_value.return_value=1
  self.f.db.sql.side_effect=[[],[('APPROVAL',)]]
  self.f.get_doc.return_value=SimpleNamespace(docstatus=1,customer='C',company='APH',as_dict=lambda:{'customer':'C','company':'APH','items':[]})
  self.m.before_submit_invoice(self.invoice())
 def test_revoked_delivery_cannot_back_invoice(self):
  self.f.db.get_value.return_value=1;self.f.db.sql.return_value=[]
  self.f.get_doc.return_value=SimpleNamespace(docstatus=1,customer='C',company='APH',as_dict=lambda:{'customer':'C','company':'APH','items':[]})
  with self.assertRaises(RuntimeError):self.m.before_submit_invoice(self.invoice())
 def test_other_company_delivery_cannot_back_invoice(self):
  self.f.db.get_value.return_value=1
  self.f.get_doc.return_value=SimpleNamespace(docstatus=1,customer='C',company='VH')
  with self.assertRaises(RuntimeError):self.m.before_submit_invoice(self.invoice())
 def test_prepaid_invoice_does_not_increase_net_credit(self):
  self.f.db.get_value.return_value=1;self.m.balance_for=lambda customer:-20000
  self.m.before_submit_invoice(self.invoice(None))
 def test_credit_note_does_not_need_credit_release(self):
  doc=self.invoice(None);doc.grand_total=-15000
  self.m.before_submit_invoice(doc)
  self.f.db.sql.assert_not_called()
 def test_accounts_user_cannot_change_global_limit(self):
  self.f.get_roles.return_value=['Accounts User']
  previous={'kh_aph_credit_high_risk':1,'kh_aph_global_credit_limit':70000}
  current={'kh_aph_credit_high_risk':1,'kh_aph_global_credit_limit':80000}
  doc=SimpleNamespace(get=current.get,get_doc_before_save=lambda:SimpleNamespace(get=previous.get))
  with self.assertRaises(PermissionError):self.m.validate_customer(doc)

 def test_sales_approver_can_revoke_without_accounts_manager(self):
  self.f.get_roles.return_value=[self.m.ROLE_APPROVER]
  result=self.m.revoke('AUDIT','Duyệt lại số lượng')
  self.assertEqual(result['revoked_by'],'chief@example.invalid')
 def test_sales_approver_cannot_change_limit_master(self):
  self.f.get_roles.return_value=[self.m.ROLE_APPROVER]
  previous={'kh_aph_credit_high_risk':1,'kh_aph_global_credit_limit':70000}
  current={'kh_aph_credit_high_risk':1,'kh_aph_global_credit_limit':80000}
  doc=SimpleNamespace(get=current.get,get_doc_before_save=lambda:SimpleNamespace(get=previous.get))
  with self.assertRaises(PermissionError):self.m.validate_customer(doc)
 def test_no_cost_cannot_approve_even_with_manager_or_approver(self):
  from kh_aph.constants import ROLE_NO_COST
  self.f.get_roles.return_value=[ROLE_NO_COST,'Accounts Manager',self.m.ROLE_APPROVER]
  with self.assertRaises(PermissionError):self.m.approve('DN','Không được vượt chặn')
  with self.assertRaises(PermissionError):self.m.revoke('AUDIT','Không được vượt chặn')
  self.f.get_doc.assert_not_called()
