import json
import pathlib
import unittest

from lab9x import cay_kho as K
from lab9x import gia_thanh as G

KHACH = pathlib.Path(__file__).resolve().parents[4] / "khach" / "aph-vh" / "khach.json"


class TestCayKho(unittest.TestCase):
    def setUp(self):
        self.cay = {"dia_diem": [
            {"ten": "Nhà máy Phú Thọ", "loai": "nha_may", "cong_ty": ["APH"], "gui": ["VH", "MK"]},
            {"ten": "Hà Nội", "loai": "ban_hang", "cong_ty": ["APH", "VH"], "kho_ve_tinh": ["Bác Hiền", "Chị Thoa"]}]}

    def test_hop_le(self):
        self.assertEqual(K.kiem_cau_hinh(self.cay, ["APH", "VH", "MK", "TL"]), [])

    def test_loi(self):
        xau = {"dia_diem": [{"ten": "HN", "loai": "ban_hang", "cong_ty": ["XX"], "gui": ["VH"]},
                            {"ten": "HN", "loai": "kho", "cong_ty": []}]}
        loi = K.kiem_cau_hinh(xau, ["APH", "VH"])
        self.assertTrue(any("không phải công ty" in l for l in loi))
        self.assertTrue(any("trùng tên" in l for l in loi))
        self.assertTrue(any("chỉ nhà máy" in l for l in loi))
        self.assertTrue(any("'loai'" in l for l in loi))

    def test_mot_nha_may_va_ten_tinh_trang(self):
        cay = {"dia_diem": [{"ten": "NM1", "loai": "nha_may", "cong_ty": ["APH"]},
                            {"ten": "NM2", "loai": "nha_may", "cong_ty": ["APH"]}]}
        self.assertTrue(any("một nhà máy" in x for x in K.kiem_cau_hinh(cay, {"APH"})))
        self.assertEqual(K.ten_kho_tinh_trang(K.TEN_CHO_XU_LY, "Hà Nội"), "Hàng chờ xử lý Hà Nội")
        self.assertEqual(K.ten_kho_tinh_trang(K.TEN_CACH_LY, None), "Hàng cách ly")

    def test_ke_hoach(self):
        ke = K.ke_hoach(self.cay, ["APH", "VH", "MK", "TL"])
        ten = {(k["abbr"], k["ten"]): k for k in ke}
        self.assertEqual(ten[("APH", "Dở dang dây chuyền phồng tôm")]["day_chuyen"], "Phồng tôm")
        self.assertEqual(ten[("APH", "Kho chờ đóng gói")]["cha"], "Nhà máy Phú Thọ - APH")
        self.assertEqual(ten[("VH", "Gửi tại Nhà máy Phú Thọ")]["loai_kho"], K.GUI)
        self.assertIn(("VH", "Kho vệ tinh Chị Thoa"), ten)
        self.assertNotIn(("TL", K.TEN_VAN_CHUYEN), ten)  # TL không có địa điểm nào
        self.assertEqual(ten[("MK", K.TEN_VAN_CHUYEN)]["transit"], 1)
        # cha luôn đứng trước con
        thu_tu = [K.ten_kho(k["ten"], k["abbr"]) for k in ke]
        for k in ke:
            if k["cha"]:
                self.assertLess(thu_tu.index(k["cha"]), thu_tu.index(K.ten_kho(k["ten"], k["abbr"])))
        self.assertEqual(len(thu_tu), len(set(thu_tu)))

    def test_so_sanh_khong_xoa(self):
        ke = K.ke_hoach(self.cay, ["APH"])
        hien = {"Kho bán hàng Hà Nội - APH": {"company_abbr": "APH", "loai_kho": "Nguyên liệu", "is_group": 0},
                "Kho cũ - APH": {"company_abbr": "APH", "loai_kho": None, "is_group": 0},
                "Hàng chờ xử lý - APH": {"company_abbr": "APH", "loai_kho": K.CHO_XU_LY, "is_group": 0}}
        tao, cb = K.so_sanh(ke, hien)
        self.assertNotIn("Kho bán hàng Hà Nội - APH", [K.ten_kho(k["ten"], k["abbr"]) for k in tao])
        self.assertTrue(any("Kho cũ" in c for c in cb))
        self.assertTrue(any("loại kho đang là" in c for c in cb))
        self.assertFalse(any("Hàng chờ xử lý" in c for c in cb))

    def test_khach_json_that(self):
        if not KHACH.exists():
            self.skipTest("trong image không có khach/")
        cfg = json.loads(KHACH.read_text(encoding="utf-8"))
        abbr = [c["abbr"] for c in cfg["cong_ty"]]
        self.assertEqual(K.kiem_cau_hinh(cfg["cay_kho"], abbr), [])
        ke = K.ke_hoach(cfg["cay_kho"], abbr)
        self.assertEqual(sum(1 for k in ke if k["ten"].startswith("Kho vệ tinh")), 24)
        self.assertEqual(sum(1 for k in ke if k["loai_kho"] == K.DO_DANG), 2)


class TestDinhMuc(unittest.TestCase):
    # Định mức thật: 1 mẻ 160 kg bột ra 180 kg bánh khô (bánh rau củ, file định mức 2026)
    DM = {"BANH_KHO": (180, {"BOT": 160, "DUONG": 16})}

    def test_nhu_cau(self):
        can, thieu = G.nhu_cau_dinh_muc({"BANH_KHO": 324, "X": 5}, self.DM)
        self.assertAlmostEqual(can["BOT"], 288)
        self.assertEqual(thieu, ["X"])

    def test_chia_trong_va_vuot(self):
        # cấp 2 mẻ (320 bột), ghi tiêu hao 280, còn 40 trên sổ; ra 1,8 mẻ -> cần 288
        kq = G.chia_hao_hut_dinh_muc({"BOT": 40}, {"BOT": 280}, {"BOT": 288})
        self.assertAlmostEqual(kq["BOT"]["tu_nhien"], 8)
        self.assertAlmostEqual(kq["BOT"]["bat_thuong"], 32)
        kq2 = G.chia_hao_hut_dinh_muc({"BOT": 40}, {"BOT": 280}, {"BOT": 288}, 10)
        self.assertAlmostEqual(kq2["BOT"]["tu_nhien"], 36.8)

    def test_khong_dinh_muc_va_dung_it(self):
        kq = G.chia_hao_hut_dinh_muc({"LA": 2, "BOT": 1}, {"BOT": 100}, {"BOT": 200})
        self.assertEqual(kq["LA"]["bat_thuong"], 2)
        self.assertIn("ít hơn", kq["BOT"]["ghi_chu"])

    def test_muc_theo_tung_bom(self):
        dm = {"A": (180, {"BOT": 160}, 2), "B": (100, {"BOT": 100}, 0)}
        muc, _ = G.nhu_cau_dinh_muc({"A": 180, "B": 100}, dm, cong_ty_le=True)
        self.assertAlmostEqual(muc["BOT"], 160 * 1.02 + 100)
        can, _ = G.nhu_cau_dinh_muc({"A": 180, "B": 100}, dm)
        kq = G.chia_hao_hut_dinh_muc({"BOT": 10}, {"BOT": 260}, can, muc=muc)
        self.assertAlmostEqual(kq["BOT"]["tu_nhien"], 3.2)
        self.assertAlmostEqual(kq["BOT"]["bat_thuong"], 6.8)
        with self.assertRaises(ValueError):
            G.nhu_cau_dinh_muc({"A": 1}, {"A": (1, {"X": 1}, -1)})

    def test_lech(self):
        self.assertEqual(G.lech_dinh_muc({"BOT": 165}, {"BOT": 160}, 5), [])
        self.assertEqual(G.lech_dinh_muc({"BOT": 170}, {"BOT": 160}, 5)[0][0], "BOT")


if __name__ == "__main__":
    unittest.main()
