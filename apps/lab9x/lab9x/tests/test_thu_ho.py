import datetime
import unittest

from lab9x import thu_ho_rules as T


class TestThuHo(unittest.TestCase):
    def test_khong_danh_dau(self):
        self.assertEqual(T.kiem_tra(0, "", "", 0, None, ""), {"loi": [], "trang_thai": None})

    def test_thieu_khach_chu_hang_so_tien(self):
        kq = T.kiem_tra(1, "", "", 0, None, "")
        self.assertEqual(len(kq["loi"]), 3)
        self.assertEqual(kq["trang_thai"], T.TT_CAN_XU_LY)

    def test_hop_le_mac_dinh_can_xu_ly(self):
        kq = T.kiem_tra(1, "KH001", "TL", 30_000_000, None, "")
        self.assertEqual((kq["loi"], kq["trang_thai"]), ([], T.TT_CAN_XU_LY))

    def test_da_xu_ly_phai_co_ghi_chu(self):
        self.assertTrue(T.kiem_tra(1, "KH001", "TL", 1, T.TT_DA_XU_LY, "")["loi"])
        kq = T.kiem_tra(1, "KH001", "TL", 1, T.TT_DA_XU_LY, "PT25301 trên MISA")
        self.assertEqual((kq["loi"], kq["trang_thai"]), ([], T.TT_DA_XU_LY))

    def test_trang_thai_la_ve_can_xu_ly(self):
        self.assertEqual(T.kiem_tra(1, "K", "TL", 1, "linh tinh", "")["trang_thai"], T.TT_CAN_XU_LY)

    def test_tk_thu_ho(self):
        self.assertTrue(T.la_tk_thu_ho("33880", T.TEN_TK_THU_HO))
        self.assertFalse(T.la_tk_thu_ho("3388", "Phải trả, phải nộp khác"))
        self.assertFalse(T.la_tk_thu_ho("33881", "Phải trả – vay mượn công ty liên quan"))
        self.assertFalse(T.la_tk_thu_ho("3381", "3381 - Tài sản thừa chờ xử lý - VH"))
        self.assertFalse(T.la_tk_thu_ho("1121", "1121 - Tiền gửi - VH"))

    def test_so_tien(self):
        dong = [{"so_tk": "1121", "ten_tk": "Tiền gửi", "debit": 30_000_000, "credit": 0},
                {"so_tk": "33880", "ten_tk": T.TEN_TK_THU_HO, "debit": 0, "credit": 30_000_000}]
        self.assertEqual(T.so_tien_thu_ho(dong), 30_000_000)
        self.assertEqual(T.so_tien_thu_ho([dong[0]]), 0)
        # chuyển tiền trả TL: Nợ 3388 -> số tiền thu hộ ròng âm, bị chặn khi tích "Thu hộ"
        self.assertLess(T.so_tien_thu_ho([{"so_tk": "33880", "ten_tk": T.TEN_TK_THU_HO, "debit": 5, "credit": 0}]), 0)

    def test_so_ngay_cho(self):
        self.assertEqual(T.so_ngay_cho(datetime.date(2026, 10, 1), datetime.date(2026, 10, 6)), 5)
        self.assertEqual(T.so_ngay_cho(datetime.date(2026, 10, 9), datetime.date(2026, 10, 6)), 0)


if __name__ == "__main__":
    unittest.main()
