import unittest
from copy import deepcopy
from kh_aph.credit_release_rules import credit_increase,shipment_fingerprint
class ReleaseRules(unittest.TestCase):
 def setUp(self):
  self.doc={'customer':'C','company':'APH','grand_total':20000,'items':[{'item_code':'R','warehouse':'APH-W','qty':1,'rate':20000}],'taxes':[]}
 def test_current_debt_increases(self):self.assertEqual(credit_increase(80000,20000),20000)
 def test_deposit_covers_shipment(self):self.assertEqual(credit_increase(-30000,20000),0)
 def test_partial_deposit(self):self.assertEqual(credit_increase(-10000,20000),10000)
 def test_same_content_bound(self):self.assertEqual(shipment_fingerprint(self.doc),shipment_fingerprint(deepcopy(self.doc)))
 def test_change_revokes_binding(self):
  for field,value in [('customer','D'),('company','VH'),('grand_total',30000)]:
   changed=deepcopy(self.doc);changed[field]=value
   self.assertNotEqual(shipment_fingerprint(self.doc),shipment_fingerprint(changed))
  for field,value in [('warehouse','VH-W'),('qty',2),('rate',10000)]:
   changed=deepcopy(self.doc);changed['items'][0][field]=value
   self.assertNotEqual(shipment_fingerprint(self.doc),shipment_fingerprint(changed))
 def test_no_client_approval_fields_affect_binding(self):
  changed=deepcopy(self.doc);changed['approved_by']='Administrator';changed['docstatus']=1
  self.assertEqual(shipment_fingerprint(self.doc),shipment_fingerprint(changed))
