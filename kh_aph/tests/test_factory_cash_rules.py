import unittest

from kh_aph import factory_cash_rules as R


class TestPhieuQuy(unittest.TestCase):
    def test_chi_phi_nho(self):
        self.assertEqual(R.kiem_phieu(R.LOAI_CHI, [("bốc xếp", "Bốc xếp", 300000), ("nước", "Khác", 20000)]), [])
        loi = R.kiem_phieu(R.LOAI_CHI, [("bốc xếp", None, 0)])
        self.assertEqual(len(loi), 2)

    def test_thu_va_ban_giao(self):
        self.assertTrue(R.kiem_phieu(R.LOAI_THU, [("thu", None, 1)]))
        self.assertEqual(R.kiem_phieu(R.LOAI_THU, [("thu", None, 1)], customer="KH-00001"), [])
        self.assertTrue(R.kiem_phieu(R.LOAI_BAN_GIAO, [("nộp", None, 1)]))
        self.assertTrue(R.kiem_phieu(R.LOAI_BAN_GIAO, [("nộp", "Bốc xếp", 1)], nguoi_nhan="u"))
        self.assertTrue(R.kiem_phieu("Khác", [("x", None, 1)]))
        self.assertTrue(R.kiem_phieu(R.LOAI_CHI, []))

    def test_trang_thai_nhan(self):
        self.assertEqual(R.trang_thai_nhan(5_000_000, 5_000_000), R.TT_DA_NHAN)
        self.assertEqual(R.trang_thai_nhan(5_000_000, 4_800_000), R.TT_CHENH)


class TestKhoaGia(unittest.TestCase):
    def test_ai_bi_khoa(self):
        self.assertTrue(R.bi_khoa_gia(["APH Không xem giá vốn", "Kế toán nhà máy"]))
        self.assertTrue(R.bi_khoa_gia(["Kế toán nhà máy", "Sales User"]))
        self.assertFalse(R.bi_khoa_gia(["Kế toán nhà máy", "Accounts User"]))
        self.assertFalse(R.bi_khoa_gia(["Nhân viên bán hàng"]))

    def test_vi_pham(self):
        dong = [(1, "TP", 30000, 30000, True), (2, "TP2", 29000, 30000, True), (3, "PP", 1000, None, False),
                (4, "TP3", 1, None, True)]
        loi = R.vi_pham_khoa_gia(dong)
        self.assertEqual(len(loi), 2)
        self.assertIn("Dòng 2", loi[0])
        self.assertIn("chưa có giá", loi[1])


if __name__ == "__main__":
    unittest.main()
