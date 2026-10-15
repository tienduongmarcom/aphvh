import datetime
import unittest

from lab9x import van_hanh as V

D = datetime.date


class TestVanHanh(unittest.TestCase):
    def test_xu_ly(self):
        self.assertEqual(V.kiem_xu_ly(100, 0, [("Thiếu: ghi giá vốn (hao hụt)", 60), ("Thiếu: cá nhân bồi thường", 40)]), [])
        self.assertTrue(V.kiem_xu_ly(100, 0, [("Thiếu: ghi giá vốn (hao hụt)", 101)]))
        self.assertTrue(V.kiem_xu_ly(0, 50, [("Thừa: không rõ chủ, ghi thu nhập khác", 60)]))
        self.assertTrue(V.kiem_xu_ly(10, 10, [("xx", 1)]))
        self.assertTrue(V.kiem_xu_ly(10, 10, [("Thiếu: ghi giá vốn (hao hụt)", 0)]))

    def test_bo_sung(self):
        self.assertEqual(V.kha_dung(100, 20, 30), 50)
        self.assertEqual(V.kha_dung(10, 20), 0)
        self.assertEqual(V.so_de_nghi(50, 0, 100, 20), 50)
        self.assertEqual(V.so_de_nghi(90, 0, 100, 20), 20)
        self.assertEqual(V.so_de_nghi(60, 50, 100, 20), 0)
        self.assertEqual(V.so_de_nghi(0, 0, 0, 20), 0)

    def test_gia_san(self):
        self.assertEqual(V.phan_tram_duoi_san(90, 100), 10)
        self.assertEqual(V.phan_tram_duoi_san(100, 100), 0)
        self.assertEqual(V.phan_tram_duoi_san(90, 0), 0)
        bang = [{"user": "ktbh", "muc": 5, "cong_ty": "APH", "tu_duyet": 1},
                {"user": "tp", "muc": None, "cong_ty": None, "tu_duyet": 0}]
        self.assertTrue(V.quyen_duyet("ktbh", "ktbh", "APH", 4, bang)[0])
        self.assertFalse(V.quyen_duyet("ktbh", "ktbh", "APH", 6, bang)[0])
        self.assertFalse(V.quyen_duyet("ktbh", "x", "VH", 1, bang)[0])
        self.assertTrue(V.quyen_duyet("tp", "ktbh", "VH", 50, bang)[0])
        self.assertFalse(V.quyen_duyet("tp", "tp", "VH", 1, bang)[0])
        self.assertFalse(V.quyen_duyet("la", "x", "APH", 1, bang)[0])

    def test_thu(self):
        self.assertEqual(V.tach_thu(100, 50, "FT123"), [("Tiền mặt", 100), ("Chuyển khoản", 50)])
        self.assertEqual(V.tach_thu(100, 0, ""), [("Tiền mặt", 100)])
        with self.assertRaises(ValueError):
            V.tach_thu(0, 50, " ")
        with self.assertRaises(ValueError):
            V.tach_thu(0, 0, "x")
        self.assertEqual(V.phan_bo(150, [("A", 100), ("B", 100)]), ([("A", 100), ("B", 50)], 0))
        self.assertEqual(V.phan_bo(250, [("A", 100), ("B", 100)]), ([("A", 100), ("B", 100)], 50))

    def test_can_goi(self):
        h = D(2026, 10, 15)
        self.assertEqual(V.can_goi(0, 0, 0, None, h, None), [])
        self.assertIn("Quá hạn", V.can_goi(100, 50, 0, None, h, h))
        self.assertEqual(V.can_goi(100, 0, 0, D(2026, 10, 15), h, h), ["Đến ngày hẹn trả"])
        self.assertEqual(V.can_goi(100, 0, 10, D(2026, 10, 20), h, D(2026, 8, 1)), [])
        self.assertEqual(V.can_goi(100, 0, 0, None, h, D(2026, 10, 1)), [])


if __name__ == "__main__":
    unittest.main()
