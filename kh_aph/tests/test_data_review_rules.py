import unittest

from kh_aph import data_review_rules as R


class TestTaiSan(unittest.TestCase):
    # Số liệu từ Sheet 5 file "Mẫu nhập tài sản APH 31/08/2026"
    def test_may_cat_phong_tom_luy_ke_bang_nguyen_gia(self):
        ma = [m for m, _ in R.kiem_tai_san(142_000_000, 142_000_000, 84, 0, 1, "PT", None, None, None)]
        self.assertEqual(ma, ["a1"])

    def test_xe_nang_luy_ke_lon_hon(self):
        ma = [m for m, _ in R.kiem_tai_san(110_000_000, 155_392_476, 60, 8, 1, "BH", None, None, None)]
        self.assertEqual(ma, ["a2"])

    def test_may_say_khau_hao_bat_thuong(self):
        ma = [m for m, _ in R.kiem_tai_san(1_809_777_650, 43_089_946, 84, 82, 1, "SC", None, "Xưởng sản xuất", "15484")]
        self.assertEqual(ma, ["a3"])

    def test_vi_tri_khac_ttcp_va_tai_khoan(self):
        ma = [m for m, _ in R.kiem_tai_san(1_852_072_976, 1_275_872_512, 180, 56, 1, "SC", "PT", "Xưởng sản xuất", "64224")]
        self.assertEqual(ma, ["a4", "a5"])

    def test_binh_thuong(self):
        self.assertEqual(R.kiem_tai_san(170_880_000, 131_008_000, 240, 56, 1, "CHUNG", "CHUNG", "Nhà máy chung", "15484"), [])


class TestTon(unittest.TestCase):
    def test_ton(self):
        self.assertEqual(R.kiem_ton(5, 100), [])
        self.assertEqual(R.kiem_ton(0, 500)[0][0], "c")
        self.assertEqual(R.kiem_ton(-1, 0)[0][0], "c")


if __name__ == "__main__":
    unittest.main()
