import unittest
from decimal import Decimal
from kh_aph.quantity_rules import bag_conversion, weighted_cost

class QuantityRules(unittest.TestCase):
    def test_price_base_and_stock_are_kg(self):
        r=bag_conversion(3,25,20000)
        self.assertEqual(r['qty'],75)
        self.assertEqual(r['rate_per_bag'],500000)
        self.assertEqual(r['amount'],1500000)
    def test_return_sign_is_preserved(self):
        r=bag_conversion(-1,25,20000)
        self.assertEqual(r['qty'],-25)
        self.assertEqual(r['amount'],-500000)
    def test_no_fractional_or_zero_or_unbounded_bags(self):
        for bags,weight in [(0,25),(1.5,25),(1,0),(1,-2),('NaN',25),(1,'Infinity')]:
            with self.assertRaises(ValueError):bag_conversion(bags,weight)
    def test_trip_cost_uses_kg_not_purchase_value(self):
        self.assertEqual(weighted_cost(100000,[25,75]),[25000,75000])
    def test_rounded_cost_is_conserved(self):
        self.assertEqual(sum(weighted_cost(100,[1,1,1])),Decimal(100))
    def test_invalid_cost_basis_fails_closed(self):
        for cost,weights in [(-1,[1]),(10,[0]),(10,[]),('NaN',[1])]:
            with self.assertRaises(ValueError):weighted_cost(cost,weights)
