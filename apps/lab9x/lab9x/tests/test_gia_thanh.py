import unittest

from lab9x import gia_thanh as g
from lab9x.bang_tai_khoan import bang


class TestHeSo(unittest.TestCase):
    def test_mac_dinh_va_am(self):
        self.assertEqual(g.he_so_hop_le(None), 1.0)
        self.assertEqual(g.he_so_hop_le(0), 1.0)
        self.assertEqual(g.he_so_hop_le(1.4), 1.4)
        with self.assertRaises(ValueError):
            g.he_so_hop_le(-1)

    def test_trong_so(self):
        self.assertEqual(g.trong_so(100, 0.7), 70)
        self.assertEqual(g.trong_so(100, None), 100)

    def test_lech_kg(self):
        self.assertEqual(g.lech_kg(100, 100.0005), 0)
        self.assertEqual(g.lech_kg(100, 98), 2)
        self.assertEqual(g.lech_kg(100, 101), -1)


class TestTaiKhoan(unittest.TestCase):
    def test_tai_khoan_yeu_to_khong_trung_bang_chuan(self):
        so = {d["so"] for d in bang("aph")} | {d["so"] for d in bang("vh")}
        for tk, _ten in g.TK_YEU_TO_154:
            self.assertTrue(tk.startswith("154"))
            self.assertNotIn(tk, so, "1548x là tài khoản tính năng, không nằm trong cây chuẩn")
        self.assertNotIn(g.TK_KHONG_PHAN_BO[1], so)
        self.assertIn(g.TK_TON_THAT, {d["so"] for d in bang("aph")})
        self.assertIn(g.TK_HAO_HUT_TU_NHIEN, {t for t, _ in g.TK_YEU_TO_154})


class TestKeHoachPhanBo(unittest.TestCase):
    def test_hai_xuong_va_nha_may_chung(self):
        so_du = {("15484", "SC"): 140_120_000, ("15482", "SC"): 35_120_000,
                 ("15484", "PT"): 12_810_000, ("15484", "CHUNG"): 60_720_000,
                 ("15481", "BH"): 1_000_000}
        dong = {"SC": [("SE1", "r1", 1000, 1.0), ("SE1", "r2", 1000, 0.7), ("SE2", "r3", 500, 1.0)],
                "PT": [("SE3", "r4", 200, 1.0)]}
        kq = g.ke_hoach_phan_bo(so_du, ["SC", "PT"], "CHUNG", dong)
        sc = kq["lcv"]["SC"]
        self.assertEqual(sorted(sc["thue"]), [("15482", 35_120_000), ("15484", 140_120_000)])
        tien = [t for *_x, t in sc["dong"]]
        self.assertEqual(sum(tien), 175_240_000)
        # trọng số 1000 : 700 : 500
        self.assertAlmostEqual(tien[0] / tien[1], 1000 / 700, places=4)
        self.assertEqual(kq["lcv"]["PT"]["dong"], [("SE3", "r4", 12_810_000)])
        self.assertEqual(kq["chung"], [("15484", 60_720_000)])
        self.assertEqual([b[0] for b in kq["bo_qua"]], ["BH"])

    def test_xuong_khong_co_phieu_giu_so_du(self):
        kq = g.ke_hoach_phan_bo({("15484", "PT"): 5}, ["PT"], None, {})
        self.assertEqual(kq["lcv"], {})
        self.assertEqual(kq["bo_qua"][0][0], "PT")

    def test_so_du_co_bao_lai(self):
        kq = g.ke_hoach_phan_bo({("15484", "SC"): -10, ("15482", "SC"): 0}, ["SC"], None,
                                {"SC": [("SE", "r", 1, 1)]})
        self.assertEqual(kq["lcv"], {})
        self.assertEqual(len(kq["bo_qua"]), 1)


class TestVetBon(unittest.TestCase):
    def test_vet_bon(self):
        xuat, bt = g.ke_hoach_vet_bon([("A", 80_080, 1), ("B", 0, 0), ("C", 0, 5), ("D", -3, -10)])
        self.assertEqual(xuat, [("A", 80_080.0)])
        self.assertEqual([b[0] for b in bt], ["C", "D"])


if __name__ == "__main__":
    unittest.main()
