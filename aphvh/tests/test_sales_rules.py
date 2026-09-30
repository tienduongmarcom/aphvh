"""Kiểm thử quy tắc cảnh báo bán hàng (0.3) và móc nối trong hooks.py — không cần Frappe."""

import ast
import pathlib
import re
import unittest

from aphvh.sales_rules import below_price_rows, credit_lines, gia_gom_thue, pick_limit, price_lines

APP = pathlib.Path(__file__).resolve().parents[1]


class TestPriceWarning(unittest.TestCase):
    def test_below_price_only(self):
        rows = [
            {"idx": 1, "item_code": "HH.DXA", "item_name": "Đậu xanh hạt loại A", "rate": 30000, "price_list_rate": 32000},
            {"idx": 2, "item_code": "HH.LAC", "item_name": "Lạc nhân", "rate": 45000, "price_list_rate": 45000},
            {"idx": 3, "item_code": "HH.VUNG", "item_name": "Vừng", "rate": 60000, "price_list_rate": 55000},
            {"idx": 4, "item_code": "HH.MOI", "item_name": "Mã mới", "rate": 10000, "price_list_rate": 0},
            {"idx": 5, "item_code": "HH.X", "item_name": "Làm tròn", "rate": 31999.9995, "price_list_rate": 32000},
        ]
        found = below_price_rows(rows)
        self.assertEqual([r["idx"] for r in found], [1])
        self.assertAlmostEqual(found[0]["pct"], 6.25)
        lines = price_lines(rows)
        self.assertEqual(len(lines), 1)
        self.assertIn("Dòng 1 – HH.DXA Đậu xanh hạt loại A: giá 30.000 thấp hơn bảng giá 32.000", lines[0])

    def test_accepts_document_like_rows(self):
        class R:
            idx, item_code, item_name, rate, price_list_rate = 2, "TP.PT8", "TP.PT8", 1, 2

        lines = price_lines([R()])
        self.assertEqual(len(lines), 1)
        self.assertIn("Dòng 2 – TP.PT8: giá 1", lines[0])  # tên trùng mã thì không lặp


class TestCreditWarning(unittest.TestCase):
    def test_pick_limit(self):
        groups = [("Doanh nghiệp/HTX", 0), ("Tất cả nhóm khách", 500_000_000)]
        self.assertEqual(pick_limit(200_000_000, groups), (200_000_000, "riêng của khách"))
        self.assertEqual(pick_limit(0, groups), (500_000_000, "nhóm khách Tất cả nhóm khách"))
        self.assertEqual(pick_limit(None, [("A", None)]), (0.0, None))

    def test_over_limit_and_overdue(self):
        over, lines = credit_lines(1_000_000_000, "nhóm khách Doanh nghiệp/HTX", 900_000_000, 150_000_000, 80_000_000)
        self.assertTrue(over)
        self.assertEqual(len(lines), 2)
        self.assertIn("1.050.000.000 đ", lines[0])
        self.assertIn("vượt hạn mức cảnh báo 1.000.000.000 đ (nhóm khách Doanh nghiệp/HTX) 50.000.000 đ", lines[0])
        self.assertIn("80.000.000 đ nợ quá hạn", lines[1])

    def test_within_limit_or_no_limit(self):
        self.assertEqual(credit_lines(1_000_000_000, "x", 500_000_000, 500_000_000, 0), (False, []))
        self.assertEqual(credit_lines(0, None, 9e12, 1, 0), (False, []))
        over, lines = credit_lines(0, None, 0, 1, 5)
        self.assertTrue(over)
        self.assertIn("nợ quá hạn", lines[0])


class TestGiaGomThue(unittest.TestCase):
    def test_exact(self):
        out = gia_gom_thue([(500, 16_000_000, 800_000), (200, 5_600_000, 448_000)], 22_848_000)
        self.assertEqual([o["thanh_tien"] for o in out], [16_800_000, 6_048_000])
        self.assertEqual([o["don_gia"] for o in out], [33_600, 30_240])
        self.assertEqual([o["le"] for o in out], [0, 0])

    def test_rounding_goes_to_largest_line(self):
        # 3 dòng 333,33 đ thuế → làm tròn lệch 1 đ, dồn vào dòng lớn nhất; tổng đúng tổng thanh toán.
        out = gia_gom_thue([(3, 10_001, 500.05), (1, 20_003, 1000.15), (7, 7, 0.35)], 31_512)
        self.assertEqual(sum(o["thanh_tien"] for o in out), 31_512)
        self.assertEqual(out[2]["thanh_tien"], 7)
        self.assertEqual(out[0]["le"], 2)

    def test_return_negative(self):
        out = gia_gom_thue([(-50, -1_600_000, -80_000)], -1_680_000)
        self.assertEqual(out[0]["thanh_tien"], 1_680_000)
        self.assertEqual(out[0]["don_gia"], 33_600)


def _module_defs(dotted: str) -> tuple[pathlib.Path, set[str]]:
    parts = dotted.split(".")
    path = APP.parent.joinpath(*parts[:-1]).with_suffix(".py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.ClassDef)}
    return path, names


class TestHooksResolve(unittest.TestCase):
    """Mọi đường dẫn aphvh.x.y trong hooks.py trỏ tới hàm có thật; tệp JS khai báo có thật."""

    def test_python_paths(self):
        text = (APP / "hooks.py").read_text(encoding="utf-8")
        paths = set(re.findall(r'"(aphvh(?:\.\w+)+)"', text))
        self.assertTrue(paths)
        for dotted in paths:
            path, names = _module_defs(dotted)
            self.assertIn(dotted.rsplit(".", 1)[1], names, f"{dotted} không có trong {path.name}")

    def test_js_files(self):
        text = (APP / "hooks.py").read_text(encoding="utf-8")
        for rel in re.findall(r'"(public/js/[\w/]+\.js)"', text):
            self.assertTrue((APP / rel).exists(), rel)

    def test_print_helpers_declared(self):
        """Hàm aphvh_* dùng trong mẫu in đều khai báo trong hooks.jinja."""
        hooks = (APP / "hooks.py").read_text(encoding="utf-8")
        used = set()
        for html in (APP / "aph_vh" / "print_format").glob("*/*.html"):
            used |= set(re.findall(r"\b(aphvh_\w+)\(", html.read_text(encoding="utf-8")))
        for fn in used:
            self.assertIn(f'"aphvh.print_utils.{fn}"', hooks, fn)


if __name__ == "__main__":
    unittest.main()
