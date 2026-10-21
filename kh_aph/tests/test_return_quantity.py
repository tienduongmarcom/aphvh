"""Các ca trả lẻ bao: số hàng và bao vật lý độc lập, không dùng bao thập phân."""
import unittest
from decimal import Decimal
from kh_aph.return_quantity import loose_return, refund_after_credit


class ReturnQuantity(unittest.TestCase):
    def test_five_kg_out_of_twenty_five_without_a_bag(self):
        result = loose_return(-5, 0, 25, 25, 1)
        self.assertEqual(result, {"qty": Decimal(-5), "bags": Decimal(0), "kg_per_bag": Decimal(25)})

    def test_opened_bag_is_one_physical_bag_not_point_two(self):
        self.assertEqual(loose_return(-5, -1, 25, 25, 1)["bags"], -1)

    def test_remaining_quantity_and_bags_are_limits(self):
        loose_return(-5, 0, 25, 5, 0)
        for values in [(-6, 0, 25, 5, 0), (-5, -1, 25, 25, 0), (-26, -1, 25, 25, 1)]:
            with self.subTest(values=values), self.assertRaises(ValueError): loose_return(*values)

    def test_forbid_fractional_or_wrong_sign_and_non_finite(self):
        for q, bags in [(-5, -.2), (-5, 1), (5, 0), (0, 0), ('NaN', 0), ('Infinity', 0), (-5, 'NaN')]:
            with self.subTest(q=q, bags=bags), self.assertRaises(ValueError): loose_return(q, bags, 25, 25, 1)

    def test_reject_missing_original_weight(self):
        for weight in [0, -25, None, 'NaN']:
            with self.subTest(weight=weight), self.assertRaises(ValueError): loose_return(-5, 0, weight, 25, 1)


class RefundAfterCredit(unittest.TestCase):
    def test_unpaid_or_part_paid_debt_remains_no_refund(self):
        self.assertEqual(refund_after_credit(175000, 700000), 0)
        self.assertEqual(refund_after_credit(175000, 0), 0)

    def test_only_excess_after_reducing_old_debt_is_refunded(self):
        self.assertEqual(refund_after_credit(175000, -75000), 75000)
        self.assertEqual(refund_after_credit(175000, -175000), 175000)

    def test_preexisting_credit_does_not_increase_this_refund(self):
        self.assertEqual(refund_after_credit(175000, -300000), 175000)
        for credit, outstanding in [(0, -1), (-1, -1), ('NaN', -1), (1, 'Infinity')]:
            with self.subTest(credit=credit, outstanding=outstanding), self.assertRaises(ValueError):
                refund_after_credit(credit, outstanding)
