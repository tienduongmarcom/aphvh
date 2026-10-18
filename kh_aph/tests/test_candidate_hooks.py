from pathlib import Path
import runpy,unittest
class CandidateHooks(unittest.TestCase):
 def setUp(self):self.h=runpy.run_path(str(Path(__file__).resolve().parents[1]/'hooks.py'))
 def test_native_vat_and_dispatch_preserved(self):
  dn=self.h['doc_events']['Delivery Note']
  self.assertIn('kh_aph.vat.before_validate_sales',dn['before_validate'])
  self.assertIn('kh_aph.sales_flow.make_draft_invoice',dn['on_submit'])
  self.assertIn('kh_aph.invoice_flag.apply_invoice_flag',dn['validate'])
 def test_warning_and_risk_guards_are_wired_once(self):
  ev=self.h['doc_events']
  self.assertEqual(ev['Delivery Note']['validate'].count('kh_aph.global_credit.validate_delivery'),1)
  self.assertEqual(ev['Delivery Note']['before_submit'].count('kh_aph.credit_release.before_submit_delivery'),1)
  self.assertIn('kh_aph.vat.validate_customer',ev['Customer']['validate'])
  self.assertIn('kh_aph.credit_release.validate_customer',ev['Customer']['validate'])
  self.assertIn('kh_aph.credit_release.validate_release',ev['APH Credit Release']['validate'])
 def test_query_and_kg_extension_preserved(self):
  self.assertEqual(self.h['override_whitelisted_methods']['frappe.client.get_value'],'kh_aph.cost_query_api.get_value')
  self.assertIn('kh_aph.stock_entry_kg.StockEntryKgCosting',self.h['extend_doctype_class']['Stock Entry'])
  self.assertIn('kh_aph.server_cost_guard.CostReadGuard',self.h['extend_doctype_class']['Stock Entry'])
 def test_no_automatic_candidate_setup(self):
  for key in ('after_install','before_migrate','after_migrate'):
   self.assertNotIn('uat_candidate_setup',str(self.h.get(key)))
 def test_stock_closing_costs_are_guarded(self):
  for dt in ('Stock Closing Entry','Stock Closing Balance'):
   self.assertEqual(self.h['has_permission'][dt],'kh_aph.dung_cost_policy.closing_has_permission')
   self.assertEqual(self.h['permission_query_conditions'][dt],'kh_aph.dung_cost_policy.closing_query_conditions')
