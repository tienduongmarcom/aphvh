"""Kiểm thử thuế GTGT theo loại khách (0.3.5) — không cần Frappe."""

import ast
import pathlib
import unittest

from aphvh import vat_rules as V

APP = pathlib.Path(__file__).resolve().parents[1]


class TestClassify(unittest.TestCase):
    def check(self, name, mst, cat):
        self.assertEqual(V.classify_customer(name, mst)[0], cat, (name, mst))

    def test_dn(self):
        self.check("CÔNG TY TNHH SẢN XUẤT NÔNG SẢN THẾ ANH", "0110777303", V.CAT_DN)
        self.check("C.Ty TNHH Đồng Minh", "0100793031", V.CAT_DN)
        self.check("CHI NHÁNH CÔNG TY CỔ PHẦN TRÀNG TIỀN", "0101605410-002", V.CAT_DN)
        self.check("HỢP TÁC XÃ NÔNG NGHIỆP AN BÌNH", "", V.CAT_DN)
        self.check("Nhà máy kem Thanh Nhàn", "5400200429", V.CAT_DN)
        self.check("TRƯỜNG CAO ĐẲNG KĨ THUẬT MẬT MÃ", "", V.CAT_DN)

    def test_hkd(self):
        self.check("HỘ KINH DOANH PHƯƠNG NAM", "001083052893", V.CAT_HKD)  # 12 số
        self.check("CƠ SỞ CHẾ BIẾN THỰC PHẨM MINH HƯƠNG", "8557357889", V.CAT_HKD)  # bắt đầu 8
        self.check("HỘ KINH DOANH VŨ TRƯỜNG GIANG", "0101209199", V.CAT_HKD)
        self.check("NGUYỄN VĂN TRƯỜNG", "", V.CAT_HKD)  # tên người có chữ Trường không phải trường học
        self.check("Trương Thị Tiếp", "0101690776", V.CAT_HKD)
        self.check("ANH CƯỜNG CÁM - CHƯƠNG MỸ", "", V.CAT_HKD)
        self.check("", None, V.CAT_HKD)

    def test_reason(self):
        self.assertIn("12 số", V.classify_customer("ĐÀM THỊ NGÂN", "027180010408")[1])

    def test_tax_id_digits(self):
        self.assertEqual(V.tax_id_digits("0101605410-002"), "0101605410")
        self.assertEqual(V.tax_id_digits(" 0101 605 410 "), "0101605410")


class TestLabels(unittest.TestCase):
    def test_default(self):
        self.assertIsNone(V.templates_for_label("Mặc định"))

    def test_kkktn_only_for_dn(self):
        m = V.templates_for_label("Không kê khai tính nộp")
        self.assertEqual(m, {V.CAT_DN: V.T_KKKTN, V.CAT_HKD: V.T_5})

    def test_rates_same_for_all(self):
        self.assertEqual(V.templates_for_label("8%"), {V.CAT_DN: V.T_8, V.CAT_HKD: V.T_8})
        self.assertEqual(V.templates_for_label("10 %"), {V.CAT_DN: V.T_10, V.CAT_HKD: V.T_10})
        self.assertEqual(V.templates_for_label("Không chịu thuế")[V.CAT_HKD], V.T_KCT)

    def test_row_two_columns(self):
        self.assertEqual(V.templates_for_row({"dn": "8%", "hkd": "8%"}), {V.CAT_DN: V.T_8, V.CAT_HKD: V.T_8})
        self.assertEqual(V.templates_for_row({"dn": "Không kê khai tính nộp", "hkd": None}), {V.CAT_DN: V.T_KKKTN})
        self.assertIsNone(V.templates_for_row({"dn": "Mặc định", "hkd": ""}))
        with self.assertRaises(ValueError):
            V.templates_for_row({"hkd": "Không kê khai tính nộp"})
        self.assertEqual(V.templates_for_row({"nhan": "10%"})[V.CAT_DN], V.T_10)

    def test_unknown(self):
        with self.assertRaises(ValueError):
            V.templates_for_label("0%")

    def test_templates(self):
        rates = dict(V.VAT_TEMPLATES)
        self.assertEqual(rates[V.T_KKKTN], 0)
        self.assertEqual(rates[V.T_5], 5)
        self.assertNotIn("GTGT 0%", rates)  # 0% chỉ dành cho xuất khẩu, không dùng


class TestHooks(unittest.TestCase):
    def test_wired(self):
        tree = ast.parse((APP / "hooks.py").read_text())
        env = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and node.targets[0].id in ("_BLANK", "_PD", "_VAT", "doc_events"):
                exec(compile(ast.Module([node], []), "hooks", "exec"), env)
        ev = env["doc_events"]
        for dt in ("Sales Order", "Delivery Note", "Sales Invoice"):
            self.assertEqual(ev[dt]["before_validate"], "aphvh.vat.before_validate_sales", dt)
        self.assertEqual(ev["Customer"]["validate"], "aphvh.vat.validate_customer")


if __name__ == "__main__":
    unittest.main()
