import unittest

from lab9x import quan_tri as Q


class TestQuanTri(unittest.TestCase):
    def test_cong_ngang(self):
        kq = Q.cong_ngang([
            {"khoa": "A", "abbr": "APH", "doanh_thu": 100, "gia_von": 60, "cp_truc_tiep": 5, "tam_tinh": {"chưa khóa kỳ"}},
            {"khoa": "A", "abbr": "VH", "doanh_thu": 50, "gia_von": 40},
            {"khoa": "B", "abbr": "VH", "doanh_thu": 0, "gia_von": 10}], ["APH", "VH"])
        a = kq["A"]
        self.assertEqual((a["APH_lg"], a["VH_lg"], a["lg"], a["lai_sau_cp"]), (40, 10, 50, 45))
        self.assertAlmostEqual(a["ty_le"], 33.33)
        self.assertEqual(a["tam_tinh"], "chưa khóa kỳ")
        self.assertIsNone(kq["B"]["ty_le"])
        self.assertEqual(kq["B"]["tam_tinh"], "")

    def test_ky(self):
        self.assertEqual(Q.trang_thai_ky(True, True, True), set())
        self.assertEqual(Q.trang_thai_ky(False, True, False), {"chưa khóa kỳ", "chưa phân bổ chi phí sản xuất"})
        self.assertEqual(Q.trang_thai_ky(True, False, False), set())

    def test_dong_tien(self):
        kq = Q.dong_tien(1000, [("2026-10-05", 100), ("2026-10-20", 200), ("2026-09-30", 50), ("2026-12-01", 9)],
                         [("2026-10-03", 30)], "2026-10-01")
        self.assertEqual((kq["thu_7"], kq["thu_30"], kq["qua_han_thu"]), (100, 300, 50))
        self.assertEqual((kq["rong_7"], kq["rong_30"]), (1070, 1270))

    def test_noi_bo(self):
        cty = ["CÔNG TY CỔ PHẦN THƯƠNG MẠI VĨNH HƯNG", "TL"]
        self.assertTrue(Q.la_noi_bo("công ty cổ phần  thương mại vĩnh hưng", 0, cty))
        self.assertTrue(Q.la_noi_bo("X", 1, cty))
        self.assertFalse(Q.la_noi_bo("Khách lẻ", 0, cty))

    def test_xac_nhan(self):
        self.assertTrue(Q.qua_han_xac_nhan(None, "2026-10-14", 30))
        self.assertFalse(Q.qua_han_xac_nhan("2026-09-20", "2026-10-14", 30))
        self.assertTrue(Q.qua_han_xac_nhan("2026-09-01", "2026-10-14", 30))


if __name__ == "__main__":
    unittest.main()
