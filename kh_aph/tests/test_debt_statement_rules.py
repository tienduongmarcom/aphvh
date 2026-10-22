"""Bản ký ròng0 vẫn hiện tăng/giảm; không dùng tín dụng Company khác để giảm tổng phải thu."""
import unittest
from kh_aph.debt_statement_rules import snapshot, base_unallocated


class StatementRules(unittest.TestCase):
    def entry(self, company, kind, name, value):
        return {'company': company, 'voucher_type': kind, 'voucher_no': name, 'amount': value}

    def test_paid_in_full_still_keeps_both_movements(self):
        result = snapshot(['CO'], [self.entry('CO', 'Sales Invoice', 'SI', 10),
            self.entry('CO', 'Payment Entry', 'PE', -10)], {('Sales Invoice', 'SI'), ('Payment Entry', 'PE')})
        row = result['positions'][0]
        self.assertEqual((row['increase'], row['decrease'], row['current']), ('10', '10', '0'))

    def test_other_amount_is_same_cutoff_not_a_guessed_historical_opening(self):
        result = snapshot(['CO'], [self.entry('CO', 'Sales Invoice', 'CU', 20),
            self.entry('CO', 'Sales Invoice', 'MOI', 10), self.entry('CO', 'Payment Entry', 'KHAC', -5)],
            {('Sales Invoice', 'MOI')})
        self.assertEqual(result['positions'][0]['other'], '15')
        self.assertEqual(result['positions'][0]['current'], '25')

    def test_credit_does_not_net_another_company_receivable(self):
        result = snapshot(['APH', 'VH'], [self.entry('APH', 'Sales Invoice', 'SI', 100),
            self.entry('VH', 'Payment Entry', 'PE', -30)], set())
        self.assertEqual(result['receivable'], '100'); self.assertEqual(result['credit'], '30')

    def test_duplicate_source_is_not_counted_twice(self):
        result = snapshot(['CO'], [self.entry('CO', 'Sales Invoice', 'SI', 10)],
            [('Sales Invoice', 'SI'), ('Sales Invoice', 'SI')])
        self.assertEqual(result['positions'][0]['increase'], '10')

    def test_internal_reconciliation_net_zero_is_not_new_customer_debt(self):
        result = snapshot(['CO'], [self.entry('CO', 'Journal Entry', 'JE', 8),
            self.entry('CO', 'Journal Entry', 'JE', -8)], {('Journal Entry', 'JE')})
        self.assertEqual(result['positions'][0]['increase'], '0')
        self.assertEqual(result['positions'][0]['decrease'], '0')

    def test_nonfinite_or_foreign_scope_cannot_enter_statement(self):
        for entry in [self.entry('CO', 'Sales Invoice', 'SI', 'NaN'), self.entry('KHAC', 'Sales Invoice', 'SI', 1)]:
            with self.assertRaises(ValueError): snapshot(['CO'], [entry], set())

    def test_foreign_unallocated_uses_party_side_exchange_rate_in_base_currency(self):
        self.assertEqual(base_unallocated('Receive',10,25000,1),250000)
        self.assertEqual(base_unallocated('Pay',10,1,25000),250000)
        self.assertEqual(base_unallocated('Receive',250000,1,25000),250000)
        self.assertEqual(base_unallocated('Pay',250000,25000,1),250000)

    def test_unallocated_conversion_is_finite_positive_rate_and_rounds_each_voucher(self):
        from decimal import Decimal
        self.assertEqual(base_unallocated('Receive','1.005',1,1),Decimal('1.01'))
        for kind,value,source,target in [('Receive',10,0,1),('Pay',10,1,None),('Pay',-1,1,1),('Receive','NaN',1,1)]:
            with self.subTest(kind=kind), self.assertRaises(ValueError): base_unallocated(kind,value,source,target)
