import unittest

from kh_aph import sales_adjust_rules as R


class TestDieuChinh(unittest.TestCase):
    def test_khong_phai_tra_lai(self):
        self.assertIsNone(R.kiem_dieu_chinh("Delivery Note", 0, 0, None))

    def test_bat_buoc_loai(self):
        self.assertTrue(R.kiem_dieu_chinh("Delivery Note", 1, 0, None))
        self.assertIsNone(R.kiem_dieu_chinh("Delivery Note", 1, 0, R.DC_TRA_HANG))

    def test_mat_tren_duong_khong_nhap_kho(self):
        self.assertTrue(R.kiem_dieu_chinh("Delivery Note", 1, 0, R.DC_MAT))
        self.assertTrue(R.kiem_dieu_chinh("Sales Invoice", 1, 1, R.DC_MAT))
        self.assertIsNone(R.kiem_dieu_chinh("Sales Invoice", 1, 0, R.DC_MAT))

    def test_cho_ve_phai_nhap_kho(self):
        self.assertIsNone(R.kiem_dieu_chinh("Delivery Note", 1, 0, R.DC_CHO_VE))
        self.assertTrue(R.kiem_dieu_chinh("Sales Invoice", 1, 0, R.DC_CHO_VE))
        # hóa đơn giảm tự sinh từ phiếu giao trả lại: kho đã nhập qua phiếu
        self.assertIsNone(R.kiem_dieu_chinh("Sales Invoice", 1, 0, R.DC_CHO_VE, theo_phieu_tra=True))


class TestGiaVon(unittest.TestCase):
    def test_canh_bao(self):
        loi = R.canh_bao_gia_von([(1, "A", 20000, 21000), (2, "B", 25000, 21000), (3, "C", 1, 0)])
        self.assertEqual(len(loi), 1)
        self.assertIn("Dòng 1", loi[0])


class TestHienThi(unittest.TestCase):
    def test_bao_kg(self):
        self.assertEqual(R.hien_thi_sl(500, "Kg", 500, "Kg", 10), "10 bao (500 Kg)")

    def test_thung(self):
        self.assertEqual(R.hien_thi_sl(3, "Thùng", 36, "Hộp"), "3 Thùng (= 36 Hộp)")

    def test_le(self):
        self.assertEqual(R.hien_thi_sl(-12.5, "Kg", 12.5, "Kg"), "12,5 Kg")


if __name__ == "__main__":
    unittest.main()
