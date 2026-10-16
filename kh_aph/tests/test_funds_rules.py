import unittest
from decimal import Decimal
from kh_aph.funds_rules import position, check_action, order_figures, money


def row(name, kind, amount, source=None):
    return {"name": name, "action_type": kind, "amount": amount, "source_reservation": source}


class FundsRulesTest(unittest.TestCase):
    def test_receipt_does_not_allocate_old_debt(self):
        self.assertEqual(position(100000, [])['available'], Decimal(100000))
        self.assertEqual(position(100000, [])['spent'], 0)

    def test_partial_reserve_allocation_refund_and_transfer(self):
        actions = [row('a', 'Giữ cọc', 60000), row('b', 'Cấn hóa đơn', 10000, 'a'),
                   row('c', 'Chuyển cọc', 20000, 'a'), row('d', 'Hoàn tiền', 5000, 'c')]
        p = position(100000, actions)
        self.assertEqual((p['unspent'], p['reserved'], p['available']), (85000, 45000, 40000))
        self.assertEqual(p['reservations'], {'a': Decimal(30000), 'c': Decimal(15000)})

    def test_reserved_cash_cannot_be_spent_as_free_cash(self):
        with self.assertRaises(ValueError):
            check_action(100000, [row('a', 'Giữ cọc', 90000)], row('b', 'Cấn hóa đơn', 20000))

    def test_cannot_overconsume_specific_reservation(self):
        with self.assertRaises(ValueError):
            check_action(100000, [row('a', 'Giữ cọc', 10000)], row('b', 'Hoàn tiền', 10001, 'a'))

    def test_release_returns_to_unallocated_without_payment(self):
        p = position(100000, [row('a', 'Giữ cọc', 50000), row('b', 'Giải phóng cọc', 20000, 'a')])
        self.assertEqual((p['spent'], p['reserved'], p['available']), (0, 30000, 70000))

    def test_physical_owner_payout_does_not_allocate_customer_cash_twice(self):
        p = check_action(10000, [row('a', 'Cấn hóa đơn', 10000)], row('b', 'Trả tiền thu hộ', 10000))
        self.assertEqual((p['spent'], p['unspent'], p['available']), (10000, 0, 0))

    def test_full_order_debt_and_undelivered_are_separate(self):
        f = order_figures(180000, 80000, 60000, 30000)
        self.assertEqual((f['remaining_to_pay'], f['dispatched_debt'], f['undelivered_value']), (130000, 60000, 100000))

    def test_invalid_money_and_history_fail_closed(self):
        for value in ('NaN', 'Infinity', '1.001', 'x'):
            with self.assertRaises(ValueError): money(value)
        with self.assertRaises(ValueError): position(10, [row('a','Hoàn tiền',11)])
        with self.assertRaises(ValueError): position(10, [row('a','Chuyển cọc',1,'a')])
