import unittest
from copy import deepcopy
from kh_aph.shared_order_rules import plan_orders

class TestSharedOrder(unittest.TestCase):
    def setUp(self):
        self.w={c+'-WH':{'company':c+' Company','abbr':c,'is_group':0,'disabled':0} for c in ['APH','VH','MK','TL']}
        self.rows=[{'line_id':c,'item_code':'RICE','warehouse':c+'-WH','qty':2,'rate':20000} for c in ['APH','VH','MK','TL']]

    def test_one_order_splits_four_owned_companies(self):
        result=plan_orders(self.rows,self.w)
        self.assertEqual(list(result['companies']),[c+' Company' for c in ['APH','VH','MK','TL']])
        self.assertEqual(result['net_total'],'160000')
        for company,rows in result['companies'].items():self.assertEqual(rows[0]['company'],company)

    def test_decimal_kg_price_and_no_input_mutation(self):
        original=deepcopy(self.rows)
        self.rows[0].update(qty='0.125',rate='12345.6')
        before=deepcopy(self.rows)
        result=plan_orders(self.rows,self.w)
        self.assertEqual(result['companies']['APH Company'][0]['amount'],'1543.2000')
        self.assertEqual(self.rows,before)
        self.assertNotEqual(self.rows,original)

    def test_warehouse_company_cannot_be_overridden(self):
        self.rows[0]['company']='VH Company'
        with self.assertRaises(ValueError):plan_orders(self.rows,self.w)

    def test_group_disabled_foreign_warehouse_rejected(self):
        for field,value in [('is_group',1),('disabled',1),('abbr','OTHER')]:
            w=deepcopy(self.w);w['APH-WH'][field]=value
            with self.assertRaises(ValueError):plan_orders(self.rows,w)

    def test_repeat_fingerprint_and_line_identity(self):
        self.assertEqual(plan_orders(self.rows,self.w)['fingerprint'],plan_orders(deepcopy(self.rows),self.w)['fingerprint'])
        self.rows[1]['line_id']=self.rows[0]['line_id']
        with self.assertRaises(ValueError):plan_orders(self.rows,self.w)

    def test_invalid_quantity_or_rate_rejected(self):
        for key in ['qty','rate']:
            for value in [0,-1,'NaN','Infinity','bad']:
                rows=deepcopy(self.rows);rows[0][key]=value
                with self.assertRaises(ValueError):plan_orders(rows,self.w)

if __name__=='__main__':unittest.main()
