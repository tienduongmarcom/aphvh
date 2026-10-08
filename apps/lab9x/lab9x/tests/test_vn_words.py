import unittest

from lab9x.vn_words import so_thanh_chu, so_tien_bang_chu


class TestSoThanhChu(unittest.TestCase):
    def test_small(self):
        cases = {
            0: "không",
            5: "năm",
            10: "mười",
            11: "mười một",
            14: "mười bốn",
            15: "mười lăm",
            20: "hai mươi",
            21: "hai mươi mốt",
            24: "hai mươi tư",
            25: "hai mươi lăm",
            100: "một trăm",
            105: "một trăm linh năm",
            110: "một trăm mười",
            999: "chín trăm chín mươi chín",
        }
        for n, text in cases.items():
            with self.subTest(n=n):
                self.assertEqual(so_thanh_chu(n), text)

    def test_groups(self):
        self.assertEqual(so_thanh_chu(1000), "một nghìn")
        self.assertEqual(so_thanh_chu(1010), "một nghìn không trăm mười")
        self.assertEqual(so_thanh_chu(1_005_000), "một triệu không trăm linh năm nghìn")
        self.assertEqual(so_thanh_chu(1_000_005), "một triệu không trăm linh năm")
        self.assertEqual(so_thanh_chu(2_000_500_000_000), "hai nghìn tỷ năm trăm triệu")
        self.assertEqual(so_thanh_chu(10**12), "một nghìn tỷ")
        self.assertEqual(so_thanh_chu(10**18), "một tỷ tỷ")

    def test_real_amount(self):
        # Tổng tồn kho đầu kỳ APH 31/08/2026 (làm tròn đồng)
        self.assertEqual(
            so_tien_bang_chu(49_707_344_935.47),
            "Bốn mươi chín tỷ bảy trăm linh bảy triệu ba trăm bốn mươi tư nghìn chín trăm ba mươi lăm đồng",
        )

    def test_money(self):
        self.assertEqual(so_tien_bang_chu(0), "Không đồng")
        self.assertEqual(so_tien_bang_chu(-1500), "Âm một nghìn năm trăm đồng")
        self.assertEqual(so_tien_bang_chu(None), "Không đồng")

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            so_thanh_chu(-1)



class TestSoVn(unittest.TestCase):
    def test_format(self):
        from lab9x.vn_words import so_vn

        self.assertEqual(so_vn(1234567.5), "1.234.567,5")
        self.assertEqual(so_vn(1000), "1.000")
        self.assertEqual(so_vn(100), "100")
        self.assertEqual(so_vn(0.125, 3), "0,125")
        self.assertEqual(so_vn(49707344935.47, 0), "49.707.344.935")
        self.assertEqual(so_vn(-0.0001), "0")
        self.assertEqual(so_vn(None), "")


if __name__ == "__main__":
    unittest.main()
