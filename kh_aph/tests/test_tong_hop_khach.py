"""Kiểm thử Tổng hợp bán hàng theo khách (0.4.1) — không cần Frappe."""

import pathlib
import unittest

from lab9x.tong_hop_khach_rules import dong_bao_cao

APP = pathlib.Path(__file__).resolve().parents[1]


class TestTongHop(unittest.TestCase):
    def test_rows(self):
        rows = dong_bao_cao([
            {"don_vi": "APH", "ten": "An Phú Hưng", "dau_ky": 1_000_000, "chung_tu": [
                {"ngay": "2026-10-01", "loai": "Hóa đơn", "so": "SI-1", "no": 588_000, "co": 0, "tien_hang": 560_000, "thue": 28_000},
                {"ngay": "2026-10-02", "loai": "Phiếu thu", "so": "PE-1", "no": 0, "co": 1_000_000}]},
            {"don_vi": "VHT", "ten": "Vĩnh Hưng", "dau_ky": 0, "chung_tu": [
                {"ngay": "2026-10-01", "loai": "Hóa đơn", "so": "SI-2", "no": 560_000, "co": 0, "tien_hang": 560_000, "thue": 0}]},
            {"don_vi": "MKT", "ten": "HKD Minh Khang", "dau_ky": 0, "chung_tu": []},
        ])
        kieu = [r["kieu"] for r in rows]
        self.assertEqual(kieu, ["dau_ky", "chung_tu", "chung_tu", "cong", "dau_ky", "chung_tu", "cong", "tong"])  # HKD không phát sinh: bỏ
        self.assertEqual(rows[2]["so_du"], 588_000)
        self.assertEqual(rows[3]["so_du"], 588_000)
        self.assertEqual(rows[-1]["so_du"], 1_148_000)
        self.assertEqual(rows[-1]["no"], 1_148_000)
        self.assertEqual(rows[-1]["co"], 1_000_000)
        self.assertEqual(rows[-1]["dau_ky"], 1_000_000)

    def test_so_gon(self):
        from lab9x.tong_hop_khach_rules import so_gon, dien_giai_gon
        self.assertEqual(so_gon("Hóa đơn", "ACC-SINV-2026-00043"), "HĐ 43")
        self.assertEqual(so_gon("Phiếu thu", "ACC-PAY-2026-00105"), "PT 105")
        self.assertEqual(so_gon("Trả hàng", "ACC-SINV-RET-2026-00007"), "TH 7")
        self.assertEqual(so_gon("Phiếu thu", "PT-0915"), "PT-0915")  # số tự đặt giữ nguyên
        self.assertEqual(dien_giai_gon("a " * 50, 10), "a a a a a…")

    def test_empty(self):
        self.assertEqual(dong_bao_cao([{"don_vi": "APH", "dau_ky": 0, "chung_tu": []}]), [])

    def test_wired(self):
        self.assertIn('"Customer": "public/js/customer.js"', (APP / "hooks.py").read_text())
        rep = APP / "kh_aph" / "report" / "tong_hop_ban_hang_theo_khach"
        for ext in ("json", "py", "js", "html"):
            self.assertTrue((rep / f"tong_hop_ban_hang_theo_khach.{ext}").exists(), ext)
        # Legacy aggregate order stays removed; only the new agreed coordinator is introduced.
        root = APP / "kh_aph" / "doctype"
        names = {p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("__")}
        self.assertEqual(names, {"aph_shared_sales_order", "aph_shared_sales_order_item", "aph_pending_receipt", "aph_pending_receipt_item", "aph_bag_movement", "aph_funds_receipt", "aph_funds_action", "aph_funds_route"})


if __name__ == "__main__":
    unittest.main()


class TestTranslations(unittest.TestCase):
    def test_print_dialog(self):
        src = (APP / "install.py").read_text()
        for a, b in (("Orientation", "Hướng giấy"), ("Landscape", "Ngang"), ("Portrait", "Dọc")):
            self.assertIn(f'"{a}": "{b}"', src)
        self.assertNotIn('"Landscape": "Phong cảnh"', src.split("OLD_TRANSLATIONS")[0])
