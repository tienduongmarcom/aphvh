"""Kiểm thử quy tắc mẫu in tiếng Việt (0.3.7) — không cần Frappe."""

import unittest

from lab9x import print_rules as P


class TestPrintRules(unittest.TestCase):
    def test_can_cu(self):
        self.assertIn("133/2016/TT-BTC", P.can_cu_mau("APH"))
        self.assertIn("99/2025/TT-BTC ngày 27/10/2025", P.can_cu_mau("VHT"))
        self.assertEqual(P.can_cu_mau("MKT"), "")

    def test_thu_chi(self):
        self.assertEqual(P.loai_thu_chi("Receive", "Receivable", "Cash"), {"kieu": "thu", "tien_mat": True})
        self.assertEqual(P.loai_thu_chi("Receive", "Receivable", "Bank"), {"kieu": "thu", "tien_mat": False})
        self.assertEqual(P.loai_thu_chi("Pay", "Cash", "Payable"), {"kieu": "chi", "tien_mat": True})
        self.assertEqual(P.loai_thu_chi("Internal Transfer", "Bank", "Cash")["kieu"], "thu")
        self.assertEqual(P.loai_thu_chi("Internal Transfer", "Cash", "Bank")["kieu"], "chi")
        self.assertEqual(P.loai_thu_chi("Internal Transfer", "Bank", "Bank")["kieu"], "chuyen")
        self.assertEqual(P.tieu_de_thu_chi("thu", True), ("PHIẾU THU", "01-TT"))
        self.assertEqual(P.tieu_de_thu_chi("chi", True), ("PHIẾU CHI", "02-TT"))
        self.assertEqual(P.tieu_de_thu_chi("chi", False)[1], "")

    def test_ly_do(self):
        refs = [("Sales Invoice", "SI-1"), ("Sales Invoice", "SI-2")]
        self.assertEqual(P.ly_do("Receive", "Customer", refs), "Thu tiền hàng theo hóa đơn SI-1, SI-2")
        self.assertEqual(P.ly_do("Receive", "Customer", [("Sales Order", "SO-1")]), "Thu tiền đặt cọc theo đơn hàng SO-1")
        self.assertEqual(P.ly_do("Receive", "Customer", []), "Thu tiền khách hàng trả trước")
        self.assertEqual(P.ly_do("Pay", "Supplier", [("Purchase Invoice", "PI-1")]), "Chi trả tiền hàng theo hóa đơn mua PI-1")
        self.assertEqual(P.ly_do("Pay", "Supplier", [("Purchase Order", "PO-1")]), "Chi đặt cọc theo đơn mua hàng PO-1")
        self.assertEqual(P.ly_do("Internal Transfer", None, [], "Bank", "Cash"), "Rút tiền gửi ngân hàng nhập quỹ tiền mặt")
        self.assertEqual(P.ly_do("Receive", "Customer", refs, ghi_chu="Thu nợ tháng 9"), "Thu nợ tháng 9")
        self.assertNotIn("Amount", P.ly_do("Pay", "Employee", []))

    def test_loai_phieu_kho(self):
        self.assertEqual(P.ten_loai_phieu_kho("Manufacture"), "Sản xuất")
        self.assertEqual(P.ten_loai_phieu_kho("Material Transfer"), "Chuyển kho")
        self.assertEqual(P.ten_loai_phieu_kho("Đóng gói theo kg"), "Đóng gói theo kg")

    def test_nhan_thue(self):
        self.assertEqual(P.nhan_thue_suat("Không kê khai tính nộp", 0), "KKKNT")
        self.assertEqual(P.nhan_thue_suat("Không chịu thuế GTGT", 0), "KCT")
        self.assertEqual(P.nhan_thue_suat("GTGT 5%", 5), "5%")
        self.assertEqual(P.nhan_thue_suat("", 8.0), "8%")
        self.assertEqual(P.nhan_thue_suat("", 3.5), "3,5%")
        self.assertEqual(P.chu_tien_te("USD"), "đô la Mỹ")


if __name__ == "__main__":
    unittest.main()


class MauMacDinhERPNext(unittest.TestCase):
    def test_nhan_ca_ba_kieu_ten(self):
        from lab9x.print_rules import la_mau_mac_dinh_erpnext as f
        self.assertTrue(f("Sales Invoice", "Sales Invoice with Item Image"))
        self.assertTrue(f("Sales Invoice", "Sales Invoice Modern with Images"))
        self.assertTrue(f("Sales Invoice", "Sales Invoice Classic"))
        self.assertTrue(f("Sales Invoice", None))
        self.assertTrue(f("Sales Invoice", ""))

    def test_mau_nguoi_dung_chon_thi_giu(self):
        from lab9x.print_rules import la_mau_mac_dinh_erpnext as f
        self.assertFalse(f("Sales Invoice", "Phiếu bán hàng"))
        self.assertFalse(f("Sales Invoice", "Delivery Note Modern with Images"))
        self.assertFalse(f("Sales Invoice", "Delivery Note Classic"))
        self.assertFalse(f("Sales Invoice", "Sales Invoice Classic riêng"))
