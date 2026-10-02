"""Kiểm thử sổ doanh thu hộ kinh doanh TT152 (0.4.5) — không cần Frappe."""

import pathlib
import unittest

from aphvh import so_hkd_rules as S

APP = pathlib.Path(__file__).resolve().parents[1]
SX = "Sản xuất, vận tải, dịch vụ có gắn với hàng hóa, xây dựng có bao thầu nguyên vật liệu"
DONG = [
    {"ngay": "2026-10-01", "so": "HD1", "dien_giai": "Bán đậu", "nganh": S.NGANH_MAC_DINH, "so_tien": 1_000_000},
    {"ngay": "2026-10-02", "so": "HD2", "dien_giai": "Gia công", "nganh": SX, "so_tien": 2_000_000},
    {"ngay": "2026-10-03", "so": "HD3", "dien_giai": "Trả hàng", "nganh": S.NGANH_MAC_DINH, "so_tien": -200_000},
]


class TestSoHKD(unittest.TestCase):
    def test_s1a(self):
        r = S.dong_so("S1a-HKD", DONG)
        self.assertEqual([x["kieu"] for x in r], ["ct", "ct", "ct", "tong"])
        self.assertEqual(r[-1]["so_tien"], 2_800_000)

    def test_s2a(self):
        r = S.dong_so("S2a-HKD", DONG)
        kieu = [x["kieu"] for x in r]
        self.assertEqual(kieu, ["nganh", "ct", "ct", "cong", "gtgt", "tncn", "nganh", "ct", "cong", "gtgt", "tncn", "tong_gtgt", "tong_tncn"])
        cong = [x for x in r if x["kieu"] == "cong"]
        self.assertEqual(cong[0]["so_tien"], 800_000)  # phân phối: 1.000.000 − 200.000
        gtgt = [x["so_tien"] for x in r if x["kieu"] == "gtgt"]
        self.assertEqual(gtgt, [8_000, 60_000])  # 1% và 3%
        tncn = [x["so_tien"] for x in r if x["kieu"] == "tncn"]
        self.assertEqual(tncn, [4_000, 30_000])  # 0,5% và 1,5%
        self.assertEqual(r[-2]["so_tien"], 68_000)
        self.assertEqual(r[-1]["so_tien"], 34_000)
        self.assertIn("1%", r[4]["dien_giai"])
        self.assertIn("0,5%", r[5]["dien_giai"])

    def test_s2b_no_tncn(self):
        kieu = [x["kieu"] for x in S.dong_so("S2b-HKD", DONG)]
        self.assertNotIn("tncn", kieu)
        self.assertEqual(kieu[-1], "tong_gtgt")

    def test_bad_form(self):
        with self.assertRaises(ValueError):
            S.dong_so("S3a-HKD", DONG)

    def test_nguong(self):
        self.assertEqual(S.tncn_sau_nguong(400_000_000, 2_000_000), 0)
        self.assertAlmostEqual(S.tncn_sau_nguong(1_000_000_000, 5_000_000), 2_500_000)

    def test_report_files(self):
        rep = APP / "aph_vh" / "report" / "so_doanh_thu_hkd"
        for ext in ("json", "py", "js", "html"):
            self.assertTrue((rep / f"so_doanh_thu_hkd.{ext}").exists(), ext)
        self.assertIn("152/2025/TT-BTC", (rep / "so_doanh_thu_hkd.html").read_text())


if __name__ == "__main__":
    unittest.main()


class TestSoThuNhap(unittest.TestCase):
    def test_s2c(self):
        r = S.dong_s2c([{"so": "H1", "so_tien": 100_000_000}, {"so": "H2", "so_tien": -5_000_000}],
                       [{"so": "J1", "so_tien": 80_000_000}, {"so": "J2", "so_tien": 5_000_000}])
        self.assertEqual([x["kieu"] for x in r], ["muc", "ct", "ct", "cong", "muc", "ct", "ct", "cong", "tong", "tong"])
        self.assertEqual(r[3]["so_tien"], 95_000_000)
        self.assertEqual(r[7]["so_tien"], 85_000_000)
        self.assertEqual(r[8]["so_tien"], 10_000_000)
        self.assertEqual(r[9]["so_tien"], 2_000_000)  # 20%
        lo = S.dong_s2c([{"so_tien": 1}], [{"so_tien": 5}])
        self.assertEqual(lo[-1]["so_tien"], 0)  # lỗ: không có thuế

    def test_s2d(self):
        r = S.dong_s2d([
            {"ma": "HH.DEN6", "ten": "Đậu đen", "dvt": "Kg", "ton_sl": 100, "ton_tt": 2_000_000,
             "ps": [{"so": "PN1", "nhap_sl": 50, "nhap_tt": 1_000_000}, {"so": "PX1", "xuat_sl": 120, "xuat_tt": 2_400_000}]},
            {"ma": "HH.X", "ten": "Không phát sinh", "dvt": "Kg", "ton_sl": 0, "ton_tt": 0, "ps": []},
        ])
        self.assertEqual([x["kieu"] for x in r], ["muc", "dau_ky", "ct", "ct", "cong"])
        self.assertEqual((r[3]["ton_sl"], r[3]["ton_tt"]), (30, 600_000))
        self.assertEqual((r[-1]["nhap_sl"], r[-1]["xuat_tt"], r[-1]["ton_tt"]), (50, 2_400_000, 600_000))

    def test_s2e(self):
        r = S.dong_s2e([{"ten": "Tiền mặt", "dau_ky": 1_000_000, "ps": [{"so": "PT1", "thu": 500_000}, {"so": "PC1", "chi": 200_000}]},
                        {"ten": "Ngân hàng trống", "dau_ky": 0, "ps": []}])
        self.assertEqual([x["kieu"] for x in r], ["muc", "dau_ky", "ct", "ct", "cong", "cuoi_ky"])
        self.assertEqual(r[3]["ton"], 1_300_000)
        self.assertEqual((r[4]["thu"], r[4]["chi"]), (500_000, 200_000))
        self.assertEqual(r[-1]["ton"], 1_300_000)

    def test_files(self):
        rep = APP / "aph_vh" / "report" / "so_ke_toan_hkd"
        for ext in ("json", "py", "js", "html"):
            self.assertTrue((rep / f"so_ke_toan_hkd.{ext}").exists(), ext)
        html = (rep / "so_ke_toan_hkd.html").read_text()
        for t in ("SỔ CHI TIẾT DOANH THU, CHI PHÍ", "SỔ CHI TIẾT VẬT LIỆU, DỤNG CỤ, SẢN PHẨM, HÀNG HÓA", "SỔ CHI TIẾT TIỀN"):
            self.assertIn(t, html)
