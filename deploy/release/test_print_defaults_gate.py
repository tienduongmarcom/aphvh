"""Kiểm ngoại lệ schema trên checkout CI; workflow không thuộc image phát hành."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PrintDefaultGate(unittest.TestCase):
    def test_gate_ignores_only_exact_native_defaults(self):
        workflow = (ROOT / ".github/workflows/cong-3-nang-cap-production.yml").read_text()
        pattern = re.search(r"--bo-qua '([^']+)'", workflow).group(1)
        rule = re.compile(pattern)
        for dt in ("POS Invoice", "Purchase Invoice", "Purchase Order", "Quotation",
                   "Request for Quotation", "Sales Order"):
            for suffix in (" with Item Image", " Modern with Images", " Classic"):
                self.assertRegex(f"PS|{dt}||default_print_format|{dt}{suffix}", rule)
            self.assertIsNone(rule.search(f"PS|{dt}||default_print_format|Mẫu riêng Classic"))
            self.assertIsNone(rule.search(f"PS|{dt}||default_print_format|Delivery Note Classic"))
        for dt in ("Purchase Receipt", "Stock Entry", "Delivery Note", "Payment Entry", "Sales Invoice"):
            self.assertIsNone(rule.search(f"PS|{dt}||default_print_format|{dt} Classic"))
        self.assertIsNone(rule.search("PS|Sales Order|items|default_print_format|Sales Order Classic"))


if __name__ == "__main__":
    unittest.main()
