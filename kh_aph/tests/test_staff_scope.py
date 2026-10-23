import unittest
from kh_aph.staff_scope import FULL_CUSTOMER_DEBT_ROLE, financial_summary_only


class StaffScope(unittest.TestCase):
    def test_only_explicit_financial_authority_and_stock_scoped_permissions(self):
        rows={'Warehouse':[{'doc':'WH','applicable_for':'Delivery Note'}, {'doc':'WH','applicable_for':'Warehouse'}]}
        self.assertTrue(financial_summary_only({FULL_CUSTOMER_DEBT_ROLE},rows))
        self.assertFalse(financial_summary_only({'Kế toán bán hàng'},rows))
        self.assertFalse(financial_summary_only({FULL_CUSTOMER_DEBT_ROLE},{}))
        for row in ({'doc':'WH'}, {'applicable_for':'GL Entry'}, 'WH'):
            self.assertFalse(financial_summary_only({FULL_CUSTOMER_DEBT_ROLE},{'Warehouse':[row]}))
