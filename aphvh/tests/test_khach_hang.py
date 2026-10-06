import json
import os
import unittest

from aphvh import cai_ban_trang as C
from aphvh import khach_hang as K

MAU = os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "khach", "mau-aph-vh.json")


class TestKhachHang(unittest.TestCase):
    def test_mau_hop_le(self):
        cfg = json.load(open(MAU, encoding="utf-8"))
        self.assertEqual(K.kiem_cau_hinh(cfg), [])
        self.assertEqual([K.loai_cua(c) for c in cfg["cong_ty"]], ["aph", "vh"])

    def test_cay_nha_may_mau(self):
        c = json.load(open(MAU, encoding="utf-8"))["cong_ty"][0]
        cay = C.cay_nha_may(c["ten_nha_may"], c["kho_them"])
        self.assertEqual(C.kiem_cay_nha_may(cay), [])
        self.assertEqual(cay[0], ("Nhà máy An Phú Hưng", None, 1))
        self.assertIn(("Kho nguyên liệu đỗ", C.NL_NM, 0), cay)

    def test_loi_cau_hinh(self):
        loi = K.kiem_cau_hinh({"cong_ty": [{"ten": "A", "abbr": "a", "thong_tu": 200, "kho_them": [{"ten": "x"}]}, {"ten": "A", "abbr": "A1", "thong_tu": 99}]})
        self.assertTrue(any("khach_hang" in x for x in loi))
        self.assertTrue(any("abbr" in x for x in loi))
        self.assertTrue(any("133 hoặc 99" in x for x in loi))
        self.assertTrue(any("nha_may" in x for x in loi))
        self.assertTrue(any("trùng tên" in x for x in loi))

    def test_trung_viet_tat(self):
        loi = K.kiem_cau_hinh({"khach_hang": "k", "cong_ty": [{"ten": "A", "abbr": "AB", "thong_tu": 99}, {"ten": "B", "abbr": "AB", "thong_tu": 133}]})
        self.assertTrue(any("trùng viết tắt" in x for x in loi))

    def test_khong_co_cong_ty(self):
        self.assertTrue(K.kiem_cau_hinh({"khach_hang": "k"}))
