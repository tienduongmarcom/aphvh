import unittest

from lab9x import du_lieu as D


class TestDuLieu(unittest.TestCase):
    def test_mst(self):
        self.assertIsNone(D.kiem_mst("2601002157"))
        self.assertIsNone(D.kiem_mst("0500470349-001"))
        self.assertIsNone(D.kiem_mst(""))
        self.assertTrue(D.kiem_mst("12345"))
        self.assertTrue(D.kiem_mst("0963689911x"))

    def test_trung_mst(self):
        kq = D.nhom_trung_mst([("A", "APH", "2601002157"), ("B", "APH", " 2601002157"), ("C", "VH", "2601002157"),
                               ("D", "APH", "")])
        self.assertEqual(kq, [("APH", "2601002157", ["A", "B"])])

    def test_kg_tinh(self):
        self.assertIsNone(D.kiem_kg_tinh(18, 72, 250))
        self.assertEqual(D.kiem_kg_tinh(18.5, 72, 250)[0], D.LOI)
        self.assertIsNone(D.kiem_kg_tinh(18.05, 72, 250))  # trong 0,5%
        self.assertEqual(D.kiem_kg_tinh(0)[0], D.LOI)
        self.assertIsNone(D.kiem_kg_tinh("13,5"))
        self.assertIsNone(D.kiem_kg_tinh(13.5, 0, 0))  # ô trống lưu là 0
        self.assertEqual(D.kiem_kg_tinh(13.5, 54, 0)[0], D.LOI)

    def test_gia_tri(self):
        self.assertEqual(D.kiem_gia_tri("san_luong_me", 0)[0], D.LOI)
        self.assertIsNone(D.kiem_gia_tri("san_luong_me", 500))
        self.assertEqual(D.kiem_gia_tri("hao_hut", -1)[0], D.LOI)
        self.assertEqual(D.kiem_gia_tri("hao_hut", 12)[0], D.CANH_BAO)
        self.assertIsNone(D.kiem_gia_tri("hao_hut", 0))
        self.assertIsNone(D.kiem_gia_tri("dinh_muc_mac_dinh", "1"))
        self.assertEqual(D.kiem_gia_tri("gia_ban", 1)[0], D.LOI)

    def test_lech(self):
        self.assertTrue(D.lech_san_luong(100, 75))
        self.assertFalse(D.lech_san_luong(100, 85))
        self.assertFalse(D.lech_san_luong(0, 50))

    def test_dau_ky(self):
        self.assertEqual(D.trang_thai_dau_ky(0, 0), D.CHUA_NAP)
        self.assertEqual(D.trang_thai_dau_ky(100, 100.4), D.KHOP)
        self.assertEqual(D.trang_thai_dau_ky(100, 90), D.LECH)
        self.assertEqual(D.trang_thai_dau_ky(0, 90, da_nhap_nguon=False), D.LECH)
        self.assertEqual(D.can_bang_tk_tam(-300, 300), 0)
        self.assertEqual(D.can_bang_tk_tam(-500, 300), -200)


if __name__ == "__main__":
    unittest.main()
