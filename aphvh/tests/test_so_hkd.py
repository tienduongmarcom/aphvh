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
