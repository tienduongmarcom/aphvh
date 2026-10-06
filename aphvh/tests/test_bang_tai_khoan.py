import unittest

from aphvh import bang_tai_khoan as B
from aphvh import tai_khoan_chuan as T


class TestBangTaiKhoan(unittest.TestCase):
    def test_cau_truc(self):
        for loai in ("aph", "vh"):
            self.assertEqual(B.loi_cau_truc(B.bang(loai), loai), [])

    def test_du_tk_app_can(self):
        for loai in ("aph", "vh"):
            so = {d["so"] for d in B.bang(loai)}
            self.assertEqual(T.thieu(so, T.CAN[loai]), [], loai)

    def test_aph_theo_tt133(self):
        so = {d["so"] for d in B.bang("aph")}
        for k in ("621", "622", "623", "627", "641", "3389"):
            self.assertNotIn(k, so)
        for k in ("6421", "6422", "3385", "154", "642"):
            self.assertIn(k, so)

    def test_vh_theo_tt99(self):
        so = {d["so"] for d in B.bang("vh")}
        for k in ("621", "622", "623", "627", "641", "642", "113", "215"):
            self.assertIn(k, so)

    def test_nguon_ghi_ro(self):
        for loai in ("aph", "vh"):
            for d in B.bang(loai):
                self.assertIn(d["nguon"], ("TT", "DN"))
        thu_ho = [d for d in B.bang("aph") if d["so"] == "33880"][0]
        self.assertEqual((thu_ho["cha"], thu_ho["nguon"]), ("338", "DN"))

    def test_nhom_co_con(self):
        ds = B.bang("aph")
        cha = {d["cha"] for d in ds if d["cha"]}
        for d in ds:
            self.assertEqual(bool(d["nhom"]), d["so"] in cha)


if __name__ == "__main__":
    unittest.main()
