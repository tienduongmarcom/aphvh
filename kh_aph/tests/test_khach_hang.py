import json
import os
import unittest

from kh_aph import cai_ban_trang as C
from kh_aph import khach_hang as K

MAU = os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "khach", "mau-aph-vh.json")


class TestKhachHang(unittest.TestCase):
    def test_mau_hop_le(self):
        cfg = json.load(open(MAU, encoding="utf-8"))
        self.assertEqual(K.kiem_cau_hinh(cfg), [])
        self.assertEqual([K.loai_cua(c) for c in cfg["cong_ty"]], ["aph", "vh"])

    def test_khong_khai_kho(self):
        loi = K.kiem_cau_hinh({"khach_hang": "k", "cong_ty": [{"ten": "A", "abbr": "AB", "thong_tu": 99, "nha_may": True}]})
        self.assertTrue(any("không khai kho" in x for x in loi))

    def test_loi_cau_hinh(self):
        loi = K.kiem_cau_hinh({"cong_ty": [{"ten": "A", "abbr": "a", "thong_tu": 200, "kho_them": [{"ten": "x"}]}, {"ten": "A", "abbr": "A1", "thong_tu": 99}]})
        self.assertTrue(any("khach_hang" in x for x in loi))
        self.assertTrue(any("abbr" in x for x in loi))
        self.assertTrue(any("133 hoặc 99" in x for x in loi))
        self.assertTrue(any("không khai kho" in x for x in loi))
        self.assertTrue(any("trùng tên" in x for x in loi))

    def test_trung_viet_tat(self):
        loi = K.kiem_cau_hinh({"khach_hang": "k", "cong_ty": [{"ten": "A", "abbr": "AB", "thong_tu": 99}, {"ten": "B", "abbr": "AB", "thong_tu": 133}]})
        self.assertTrue(any("trùng viết tắt" in x for x in loi))

    def test_khong_co_cong_ty(self):
        self.assertTrue(K.kiem_cau_hinh({"khach_hang": "k"}))

    def test_che_do_du_lieu(self):
        co = {"khach_hang": "k", "cong_ty": [{"ten": "A", "abbr": "AB", "thong_tu": 99}]}
        self.assertEqual(K.kiem_cau_hinh(co), [])  # mặc định tu_nhap, không cần ngày chốt
        self.assertEqual(K.kiem_cau_hinh({**co, "che_do_du_lieu": "tu_nhap", "ngay_chot": "2026-01-01"}), [])
        self.assertEqual(K.kiem_cau_hinh({**co, "che_do_du_lieu": "import_mot_phan", "ngay_chot": "2026-01-01"}), [])
        self.assertTrue(any("ngay_chot" in x for x in K.kiem_cau_hinh({**co, "che_do_du_lieu": "import_mot_phan"})))
        self.assertTrue(any("che_do_du_lieu" in x for x in K.kiem_cau_hinh({**co, "che_do_du_lieu": "khac"})))
        self.assertTrue(any("YYYY-MM-DD" in x for x in K.kiem_cau_hinh({**co, "ngay_chot": "31/12/2025"})))
        self.assertTrue(any("YYYY-MM-DD" in x for x in K.kiem_cau_hinh({**co, "ngay_chot": "2026-02-30"})))

    def test_khach_dau_tien_hop_le(self):
        d = os.path.join(os.path.dirname(__file__), "..", "..", "khach")
        thay = 0
        for ten in sorted(os.listdir(d)):
            f = os.path.join(d, ten, "khach.json")
            if os.path.isfile(f):
                thay += 1
                self.assertEqual(K.kiem_cau_hinh(json.load(open(f, encoding="utf-8"))), [], ten)
        self.assertGreaterEqual(thay, 1)
