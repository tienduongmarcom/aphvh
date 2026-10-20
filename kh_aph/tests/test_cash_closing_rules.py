"""Kiểm bất biến tiền mặt: số hữu hạn, tổng trách nhiệm và thay đổi lịch sử."""
import unittest
from decimal import Decimal
from kh_aph.cash_closing_rules import anchor, balance, money, position, unchanged


def row(name, debit=0, credit=0, holder='', cancelled=0, date='2026-10-18'):
    return dict(name=name, debit=debit, credit=credit, holder=holder, is_cancelled=cancelled,
                posting_date=date, creation='2026-10-18 08:00:00', voucher_type='Journal Entry', voucher_no=name+'-JE')


class CashClosingRules(unittest.TestCase):
    def test_money_rejects_nonfinite_precision_and_overflow(self):
        for value in ('NaN', 'Infinity', '-Infinity', 'abc', '0.001', '1000000000000000'):
            with self.subTest(value=value), self.assertRaises(ValueError): money(value)
        self.assertEqual(money('123.45'), Decimal('123.45'))

    def test_opening_and_new_cash_are_counted_once(self):
        initial = [row('opening', 1000)]
        saved, _ = anchor(initial)
        rows = initial + [row('receipt', 100, holder='a'), row('refund', credit=20, holder='a'), row('unknown', 50)]
        totals = position({'a': 700, 'b': 200, '': 100}, saved, rows)
        self.assertEqual(totals, {'a': Decimal(780), 'b': Decimal(200), '': Decimal(150)})
        self.assertEqual(sum(totals.values()), balance(rows))
        self.assertEqual(position({'a':700, 'b':200, '':100}, saved, rows), totals)

    def test_anchor_order_independent_and_contains_no_money_or_holder(self):
        rows = [row('gl-a', 123456, holder='secret@example.invalid'), row('gl-b', credit=2)]
        self.assertEqual(anchor(rows), anchor(list(reversed(rows))))
        encoded, _ = anchor(rows)
        self.assertNotIn('secret', encoded)
        self.assertNotIn('123456', encoded)

    def test_anchored_cancel_deletion_reassign_and_same_total_repost_detected(self):
        rows = [row('a', 100, holder='a'), row('b', credit=50, holder='a')]
        saved, _ = anchor(rows)
        cases = [[{**rows[0], 'is_cancelled': 1}, rows[1]], rows[:1],
                 [{**rows[0], 'holder': 'b'}, rows[1]], [row('replacement',100,holder='a'), rows[1]],
                 [{**rows[0], 'posting_date':'2026-10-17'}, rows[1]]]
        for changed in cases:
            self.assertFalse(unchanged(saved, changed))
            with self.assertRaisesRegex(ValueError, 'đã đổi'): position({'a':50}, saved, changed)

    def test_no_owner_guess_and_cancelled_new_rows_not_counted(self):
        rows = [row('before', 100)]
        saved, _ = anchor(rows)
        totals = position({'':100}, saved, rows+[row('u',10), row('cancelled',999,cancelled=1)])
        self.assertEqual(totals, {'':Decimal(110)})

    def test_bad_initial_total_cannot_create_responsibility(self):
        rows=[row('a',100)]; saved,_=anchor(rows)
        with self.assertRaisesRegex(ValueError,'không khớp'): position({'a':101},saved,rows)
