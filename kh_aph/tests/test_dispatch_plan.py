import unittest
from pathlib import Path
from kh_aph.dispatch_plan import plan


class DispatchPlan(unittest.TestCase):
    def setUp(self):
        self.rows = [{"source_row": "APH-1", "ordered_qty": 100, "delivered_qty": 25,
                      "draft_qty": 25, "kg_per_bag": 25},
                     {"source_row": "VH-1", "ordered_qty": 10, "delivered_qty": 1,
                      "draft_qty": 2, "kg_per_bag": 0}]

    def test_partial_bags_and_loose_kg(self):
        selected = plan(self.rows, [{"source_row": "APH-1", "qty": 50}, {"source_row": "VH-1", "qty": "2.5"}])
        self.assertEqual([(r["qty"], r["bags"]) for r in selected], [(50, 2), (2.5, 0)])

    def test_no_overdelivery_or_fractional_bags(self):
        for qty in (0, -1, 51, 12.5, 75, "NaN", "Infinity", "abc"):
            with self.subTest(qty=qty), self.assertRaises(ValueError):
                plan(self.rows, [{"source_row": "APH-1", "qty": qty}])

    def test_unknown_duplicate_empty_and_invalid_selection(self):
        for selected in ([], None, {}, [None], [{"source_row": "OTHER", "qty": 1}],
                         [{"source_row": "VH-1", "qty": 1}] * 2):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                plan(self.rows, selected)

    def test_released_draft_does_not_change_delivered_quantity(self):
        self.rows[0]["draft_qty"] = 0
        selected = plan(self.rows, [{"source_row": "APH-1", "qty": 75}])
        self.assertEqual(selected[0]["bags"], 3)
        self.assertEqual(self.rows[0]["delivered_qty"], 25)

    def test_exact_decimal_bag_snapshot(self):
        self.rows[0].update(ordered_qty="0.3", delivered_qty=0, draft_qty=0, kg_per_bag="0.1")
        self.assertEqual(plan(self.rows, [{"source_row": "APH-1", "qty": "0.3"}])[0]["bags"], 3)


try:
    from jinja2.sandbox import SandboxedEnvironment
except ImportError:
    SandboxedEnvironment = None


@unittest.skipUnless(SandboxedEnvironment, "Cần Jinja2 như runtime ERPNext")
class DispatchPrint(unittest.TestCase):
    def test_draft_quantity_and_untrusted_text(self):
        source = Path(__file__).resolve().parents[1] / "templates/ban_nhanh/phieu_dot_xuat.html"
        note = {"name": "DN-1", "company": "APH", "posting_date": "2026-10-16",
                "customer_name": "Khách <script>", "docstatus": 0, "recipient": "Nhận <script>",
                "address": "Kho <img>", "created_by": "Người lập", "dispatcher": "Kho A",
                "items": [{"item_code": "A", "item_name": "Đậu", "warehouse": "HN", "qty": 50,
                           "bags": 2, "kg_per_bag": 25}]}
        html = SandboxedEnvironment().from_string(source.read_text()).render(shared_order="SO-1", notes=[note])
        self.assertIn("CHỜ XUẤT", html)
        self.assertIn("Khách &lt;script&gt;", html)
        self.assertNotIn("Khách <script>", html)
        self.assertIn("Người thực giao hàng", html)
        self.assertIn("50", html)
        self.assertNotIn("Giá bán", html)
        self.assertIn("Nhận &lt;script&gt;", html)
        self.assertIn("Kho &lt;img&gt;", html)
        self.assertEqual(html.count("<h1>PHIẾU XUẤT KHO</h1>"), 2)
        self.assertIn("Liên: Lưu kho", html)
        self.assertIn("Liên: Giao nhận", html)
        self.assertIn("Kg dự kiến", html)
        note["docstatus"] = 1
        printed = SandboxedEnvironment().from_string(source.read_text()).render(shared_order="SO-1", notes=[note])
        self.assertIn("BẢN SAO, KHÔNG DÙNG ĐỂ NHẬN HÀNG LẦN NỮA", printed)
        self.assertIn("Kg đã xuất", printed)
