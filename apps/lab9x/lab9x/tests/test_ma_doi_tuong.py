import unittest

from lab9x import ma_doi_tuong as M


class MaDoiTuong(unittest.TestCase):
    def test_giu_nguyen(self):
        self.assertEqual(M.chuan_hoa(" KH0000069 "), "KH0000069")
        self.assertEqual(M.chuan_hoa("ncc-007"), "ncc-007")
        self.assertEqual(M.kiem("KH0000069"), "")
        self.assertIn("ký tự", M.kiem("KH%01"))

    def test_ma_tiep(self):
        self.assertEqual(M.ma_tiep("KH", []), "KH0000001")
        self.assertEqual(M.ma_tiep("KH", ["KH0000069", "KH0001998", "KH-00001", "KHX12", "NCC0000005"]), "KH0001999")
        self.assertEqual(M.ma_tiep("NCC", ["NCC0005"]), "NCC0006")
        self.assertEqual(M.ma_tiep("KH", ["KH9999999"]), "KH10000000")


if __name__ == "__main__":
    unittest.main()
