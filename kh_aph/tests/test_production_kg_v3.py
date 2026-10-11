import sys,types,unittest
from unittest.mock import patch
from kh_aph.tests.test_p0_dispatch_and_cost import Row,module,Rejected

class ProductionKgV3(unittest.TestCase):
    def setUp(self):
        f=types.ModuleType('frappe');f._=lambda x:x;f.throw=lambda *a,**k: (_ for _ in ()).throw(Rejected(a))
        u=types.ModuleType('frappe.utils');u.flt=lambda x,p=None: round(float(x or 0),p) if p is not None else float(x or 0)
        self.context=patch.dict(sys.modules,{'frappe':f,'frappe.utils':u});self.context.start();self.addCleanup(self.context.stop)
        self.api=module('unit_stock_kg_v3','stock_entry_kg.py')
        def row(**kw):return Row(precision=lambda _:2,**kw)
        self.doc=Row(name='SE',purpose='Manufacture',kh_aph_costing_rule='kg-v3',items=[
            row(item_code='RAW',s_warehouse='WH',t_warehouse=None,is_finished_item=0,basic_amount=1000000),
            row(item_code='FG',s_warehouse=None,t_warehouse='WH',is_finished_item=1,kh_aph_kg=70,transfer_qty=70),
            row(item_code='BY',s_warehouse=None,t_warehouse='WH',is_finished_item=0,secondary_item_type='By-Product',kh_aph_kg=20,transfer_qty=20),
            row(item_code='FIXED',s_warehouse=None,t_warehouse='WH',is_finished_item=0,secondary_item_type='By-Product',kh_aph_gia_co_dinh=1,kh_aph_kg=5,transfer_qty=5,basic_rate=5000)],get_costed_out_items_cost=lambda:25000)
        from kh_aph.constants import SED_FIXED_RATE
        self.doc['items'][3][SED_FIXED_RATE]=1
    def test_fixed_secondary_value_deducted_once(self):
        self.api.allocate_finished_cost_by_kg(self.doc)
        self.assertEqual(sum(r.basic_amount for r in self.doc['items'][1:]),1000000)
        self.assertEqual(self.doc['items'][3].basic_amount,25000)
    def test_late_input_price_reallocates_without_master_weights(self):
        self.doc['items'][0].basic_amount=1100000
        self.api.allocate_finished_cost_by_kg(self.doc)
        self.assertEqual(sum(r.basic_amount for r in self.doc['items'][1:]),1100000)
        self.assertEqual(self.doc['items'][3].basic_rate,5000)
    def test_extra_cost_weight_basis_excludes_fixed_byproduct(self):
        obj=type('Doc',(self.api.StockEntryKgCosting,Row),{})(self.doc)
        rows,basis,total=obj.get_additional_cost_allocation()
        self.assertEqual([r.item_code for r in rows],['FG','BY'])
        self.assertEqual((basis,total),('kh_aph_kg',90))
    def test_fixed_value_cannot_exceed_input(self):
        self.doc['items'][0].basic_amount=20000
        with self.assertRaises(Rejected):self.api.allocate_finished_cost_by_kg(self.doc)
    def test_historical_rule_does_not_include_secondary_rows(self):
        self.doc.kh_aph_costing_rule='kg-v2';self.doc.purpose='Repack'
        self.assertEqual([r.item_code for r in self.api.finished_rows(self.doc)],['FG'])
    def test_production_and_repack_share_stored_rule(self):
        self.assertTrue(self.api.uses_kg_rule(self.doc))
        self.doc.purpose='Repack';self.assertTrue(self.api.uses_kg_rule(self.doc))
        self.doc.purpose='Material Receipt';self.assertFalse(self.api.uses_kg_rule(self.doc))
