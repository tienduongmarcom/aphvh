import unittest
from kh_aph.global_credit_rules import measure_credit

class GlobalCreditTests(unittest.TestCase):
    def test_four_company_debt(self):
        self.assertTrue(measure_credit(80000, 0, 70000)['over_limit'])
    def test_verified_receipts_already_netted_once(self):
        r=measure_credit(80000-40000-20000,0,70000)
        self.assertEqual(r['projected'],'20000')
        self.assertFalse(r['over_limit'])
    def test_dispatch_recheck(self):
        self.assertTrue(measure_credit(60000,20000,70000)['over_limit'])
    def test_order_projection(self):
        self.assertTrue(measure_credit(0,180000,70000)['over_limit'])
    def test_deposit_net_and_boundary(self):
        self.assertEqual(measure_credit(-50000,20000,70000)['projected'],'0')
        self.assertFalse(measure_credit(50000,20000,70000)['over_limit'])
    def test_unset_limit_and_invalid(self):
        self.assertFalse(measure_credit(80000,20000,0)['over_limit'])
        for args in [(0,-1,1),(0,1,-1),('NaN',1,1)]:
            with self.assertRaises(ValueError):measure_credit(*args)
