import datetime
import unittest

from lab9x import ban_hang as B


class TestGiamGia(unittest.TestCase):
    def test_chia_co_thue(self):
        # 2 dòng: 10 triệu (thuế 10%) và 5 triệu (thuế 5%); khách được giảm 1.000.000 đã gồm thuế
        kq = B.chia_giam_gia(1_000_000, [("d1", 10_000_000, 10), ("d2", 5_000_000, 5)])
        self.assertEqual(sum(c + t for _k, c, t in kq), 1_000_000)
        d1 = kq[0]
        self.assertAlmostEqual(d1[2] / d1[1], 0.10, places=3)
        self.assertAlmostEqual((kq[0][1] + kq[0][2]) / (kq[1][1] + kq[1][2]), 11_000_000 / 5_250_000, places=3)

    def test_khong_thue_va_loi(self):
        kq = B.chia_giam_gia(300, [("a", 200, 0), ("b", 100, 0), ("c", 0, 0)])
        self.assertEqual(kq, [("a", 200, 0), ("b", 100, 0)])
        with self.assertRaises(ValueError):
            B.chia_giam_gia(0, [("a", 1, 0)])
        with self.assertRaises(ValueError):
            B.chia_giam_gia(1000, [("a", 100, 10)])

    def test_tk_giam_tru(self):
        self.assertEqual(B.tk_giam_tru({"511", "521"}), "521")
        self.assertIsNone(B.tk_giam_tru({"511", "5111"}))


class TestHan(unittest.TestCase):
    def test_han(self):
        self.assertEqual(B.han_chung("2026-10-01", 30), datetime.date(2026, 10, 31))
        self.assertIsNone(B.han_chung("2026-10-01", None))
        self.assertEqual(B.han_hoa_don(datetime.date(2026, 10, 5), "2026-10-10"), datetime.date(2026, 10, 10))
        self.assertEqual(B.han_hoa_don("2026-10-31", "2026-10-10"), datetime.date(2026, 10, 31))

    def test_tra_hang(self):
        self.assertIsNone(B.kiem_tra_hang(False, None, None))
        self.assertIn("hàng trả về", B.kiem_tra_hang(True, None, B.TIEN_HOAN))
        self.assertIn("xử lý tiền", B.kiem_tra_hang(True, B.HANG_CACH_LY, "x"))
        self.assertIsNone(B.kiem_tra_hang(True, B.HANG_CACH_LY, B.TIEN_DOI_HANG))


if __name__ == "__main__":
    unittest.main()
