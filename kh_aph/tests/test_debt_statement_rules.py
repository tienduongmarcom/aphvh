"""Bản ký ròng0 vẫn hiện tăng/giảm; không dùng tín dụng Company khác để giảm tổng phải thu."""
import unittest
from kh_aph.debt_statement_rules import snapshot, base_unallocated, deposit_snapshot


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


class DepositDetails(unittest.TestCase):
    def test_transfer_and_release_keep_exact_order_source(self):
        actions=[{'name':'GIU','action_type':'Giữ cọc','amount':70,'shared_order':'DON1','source_company':'CO1'},
            {'name':'CHUYEN','action_type':'Chuyển cọc','amount':20,'source_reservation':'GIU','shared_order':'DON2','source_company':'CO2'},
            {'name':'NHA','action_type':'Giải phóng cọc','amount':10,'source_reservation':'GIU'}]
        state, details=deposit_snapshot({'name':'THU','company':'CO1','amount':100},actions)
        self.assertEqual(state['reserved'],60)
        self.assertEqual(state['available'],40)
        self.assertEqual({r['shared_order']:r['reserved'] for r in details},{'DON1':'40','DON2':'20'})
        self.assertTrue(all(r['receipt']=='THU' and r['company']=='CO1' for r in details))

    def test_fully_allocated_deposit_is_not_printed_as_still_held(self):
        state, details=deposit_snapshot({'name':'THU','company':'CO','amount':50},[
            {'name':'GIU','action_type':'Giữ cọc','amount':50,'shared_order':'DON'},
            {'name':'CAN','action_type':'Cấn hóa đơn','amount':50,'source_reservation':'GIU'}])
        self.assertEqual(state['reserved'],0)
        self.assertEqual(details,[])

    def test_missing_order_cannot_be_invented_from_customer_or_invoice(self):
        with self.assertRaises(ValueError):deposit_snapshot({'name':'THU','company':'CO','amount':50},[
            {'name':'GIU','action_type':'Giữ cọc','amount':50}])

    def test_common_deposit_keeps_empty_source_company(self):
        _, details=deposit_snapshot({'name':'THU','company':'CO','amount':50},[
            {'name':'GIU','action_type':'Giữ cọc','amount':20,'shared_order':'DON'}])
        self.assertEqual(details[0]['source_company'],'')
