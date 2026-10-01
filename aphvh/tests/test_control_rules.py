"""Kiểm thử quy tắc kiểm soát 0.3.4 và móc nối hooks.py — không cần Frappe."""

import ast
import pathlib
import unittest
from datetime import date

from aphvh import control_rules as R

APP = pathlib.Path(__file__).resolve().parents[1]


class TestStockAccount(unittest.TestCase):
    def test_detects_stock_rows(self):
        types = {"156 - Hàng hóa - APH": "Stock", "6321 - Giá vốn - APH": "Cost of Goods Sold", "1111 - TM - APH": "Cash"}
        rows = [{"idx": 1, "account": "6321 - Giá vốn - APH"}, {"idx": 2, "account": "156 - Hàng hóa - APH"}, {"idx": 3, "account": "1111 - TM - APH"}]
        bad = R.stock_account_rows(rows, lambda a: types.get(a, ""))
        self.assertEqual(bad, [(2, "156 - Hàng hóa - APH")])
        self.assertIn("dòng 2", R.stock_account_message(bad))

    def test_no_stock_rows(self):
        self.assertEqual(R.stock_account_rows([{"idx": 1, "account": "1111"}], lambda a: "Cash"), [])


class TestDates(unittest.TestCase):
    def test_future(self):
        self.assertTrue(R.is_future("2026-10-15", "2026-10-01"))
        self.assertFalse(R.is_future("2026-10-01", "2026-10-01"))
        self.assertFalse(R.is_future(date(2026, 9, 25), date(2026, 10, 1)))
        self.assertFalse(R.is_future(None, "2026-10-01"))

    def test_override(self):
        self.assertTrue(R.can_override(["Accounts User", "Accounts Manager"]))
        self.assertFalse(R.can_override(["Accounts User", "Sales User"]))


class TestCashAndDeposit(unittest.TestCase):
    def test_cash_limit(self):
        self.assertIsNone(R.cash_warning(19_999_999))
        msg = R.cash_warning(30_000_000)
        self.assertIn("30.000.000", msg)
        self.assertIn("20.000.000", msg)

    def test_deposit(self):
        self.assertIsNone(R.deposit_warning(True, 2_800_000))
        self.assertIsNone(R.deposit_warning(False, 0))
        self.assertIn("2.800.000", R.deposit_warning(False, 2_800_000))

    def test_walk_in(self):
        self.assertIsNone(R.walk_in_problem(False, None, False))
        self.assertIsNone(R.walk_in_problem(True, "1111 - TM - APH", False))
        self.assertIsNone(R.walk_in_problem(True, None, True))
        self.assertIn("thu tiền ngay", R.walk_in_problem(True, None, False))


class TestHooks(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((APP / "hooks.py").read_text())
        env = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("_BLANK", "_PD", "doc_events"):
                exec(compile(ast.Module([node], []), "hooks", "exec"), env)
        self.ev = env["doc_events"]

    def _has(self, dt, event, fn):
        v = self.ev[dt][event]
        return fn in (v if isinstance(v, list) else [v])

    def test_wired(self):
        self.assertTrue(self._has("Journal Entry", "validate", "aphvh.controls.validate_journal_entry"))
        self.assertTrue(self._has("Item", "validate", "aphvh.controls.validate_item"))
        self.assertTrue(self._has("Sales Invoice", "validate", "aphvh.controls.validate_sales_invoice"))
        self.assertTrue(self._has("Sales Invoice", "on_submit", "aphvh.controls.sales_invoice_on_submit"))
        self.assertTrue(self._has("Payment Entry", "validate", "aphvh.controls.validate_payment_entry"))
        for dt in ("Delivery Note", "Purchase Receipt", "Stock Entry", "Stock Reconciliation", "Journal Entry"):
            self.assertTrue(self._has(dt, "validate", "aphvh.controls.validate_posting_date"), dt)
        # quy tắc cũ vẫn còn
        self.assertTrue(self._has("Sales Invoice", "validate", "aphvh.invoice_flag.apply_invoice_flag"))
        self.assertTrue(self._has("Purchase Receipt", "validate", "aphvh.price_visibility.validate_purchase_receipt"))


if __name__ == "__main__":
    unittest.main()
