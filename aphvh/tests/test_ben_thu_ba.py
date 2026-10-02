import unittest

from aphvh import ben_thu_ba_rules as B


class TestBenThuBa(unittest.TestCase):
    def test_khong_danh_dau(self):
        self.assertEqual(B.kiem_tra(0, "", "", False), {"loi": [], "trang_thai": None})

    def test_thieu_ten_can_cu(self):
        kq = B.kiem_tra(1, "", "", False)
        self.assertEqual(len(kq["loi"]), 2)

    def test_chua_co_giay_to_van_ghi_duoc(self):
        kq = B.kiem_tra(1, "Trần Văn X", B.CAN_CU_CHUA_CO, False)
        self.assertEqual(kq["loi"], [])
        self.assertEqual(kq["trang_thai"], B.TT_CAN_RA_SOAT)

    def test_uy_quyen_bat_buoc_file(self):
        self.assertTrue(B.kiem_tra(1, "Công ty A", B.CAN_CU_UY_QUYEN, False)["loi"])
        kq = B.kiem_tra(1, "Công ty A", B.CAN_CU_UY_QUYEN, True)
        self.assertEqual((kq["loi"], kq["trang_thai"]), ([], B.TT_DU_HO_SO))

    def test_giu_trang_thai_da_duyet(self):
        self.assertEqual(B.kiem_tra(1, "X", B.CAN_CU_CHUA_CO, False, B.TT_DA_DUYET)["trang_thai"], B.TT_DA_DUYET)

    def test_canh_bao_thue(self):
        self.assertIsNotNone(B.canh_bao_thue(1, "0101234567", "0109999999", True))
        self.assertIsNone(B.canh_bao_thue(1, "0101234567", "0101234567-001", True))  # cùng MST (chi nhánh)
        self.assertIsNone(B.canh_bao_thue(1, "038079028024", "0109999999", True))  # cá nhân
        self.assertIsNone(B.canh_bao_thue(1, "0101234567", "0109999999", False))  # không HĐ GTGT

    def test_nguoi_tren_phieu(self):
        self.assertEqual(B.nguoi_tren_phieu(1, "Trần Văn X", "Công ty Minh Tâm", "thu"), "Trần Văn X (nộp thay cho Công ty Minh Tâm)")
        self.assertEqual(B.nguoi_tren_phieu(1, "Y", "NCC B", "chi"), "Y (nhận thay cho NCC B)")
        self.assertIsNone(B.nguoi_tren_phieu(0, "Y", "NCC B", "thu"))


if __name__ == "__main__":
    unittest.main()
