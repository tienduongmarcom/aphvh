import unittest

from kh_aph.don_vi_noi_bo import co_xuat_hoa_don, gia_gom_thue


class TestChuyenTiep(unittest.TestCase):
    def test_phap_nhan_theo_khach(self):
        self.assertEqual(co_xuat_hoa_don(False, "", "Không"), ("Không", None))  # khách không lấy HĐ (vẫn xuất trên MISA)
        self.assertEqual(co_xuat_hoa_don(False, "Có", "Không"), ("Có", None))
        self.assertEqual(co_xuat_hoa_don(False, "", ""), ("", None))

    def test_don_vi_chuyen_tiep_luon_khong(self):
        self.assertEqual(co_xuat_hoa_don(True, "Có", "Có"), ("Không", None))

    def test_gia_gom_thue(self):
        self.assertTrue(gia_gom_thue(False, "Không"))
        self.assertFalse(gia_gom_thue(False, "Có"))
        self.assertFalse(gia_gom_thue(True, "Không"))  # TL không có VAT


if __name__ == "__main__":
    unittest.main()
