import unittest

from aphvh.don_vi_noi_bo import co_xuat_hoa_don


class TestChuyenTiep(unittest.TestCase):
    def test_phap_nhan_mac_dinh_co(self):
        self.assertEqual(co_xuat_hoa_don(False, "", "Không"), ("Có", None))  # bỏ qua mặc định "Không" của khách
        self.assertEqual(co_xuat_hoa_don(False, "Có", ""), ("Có", None))

    def test_phap_nhan_chon_khong_bi_chan(self):
        flag, loi = co_xuat_hoa_don(False, "Không", "")
        self.assertTrue(loi)

    def test_don_vi_chuyen_tiep_luon_khong(self):
        self.assertEqual(co_xuat_hoa_don(True, "Có", "Có"), ("Không", None))
        self.assertEqual(co_xuat_hoa_don(True, "", ""), ("Không", None))


if __name__ == "__main__":
    unittest.main()
