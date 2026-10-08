"""Tồn kho theo tài khoản × địa điểm (0.4.18) — quy tắc thuần."""
import unittest

from lab9x import ton_kho_tk_rules as t

CHA = {"Kho bán hàng Hà Nội - APH": "Hà Nội - APH", "Hà Nội - APH": "All Warehouses - APH", "Kho Đà Nẵng - APH": "Đà Nẵng - APH",
       "Đà Nẵng - APH": "All Warehouses - APH", "Kho NL dầu - APH": "Nhà máy - APH", "Nhà máy - APH": "All Warehouses - APH",
       "Hàng đang vận chuyển - APH": "All Warehouses - APH", "All Warehouses - APH": None}
GOC = {"All Warehouses - APH"}


class TestTonKhoTk(unittest.TestCase):
    def test_dia_diem(self):
        self.assertEqual(t.dia_diem("Kho bán hàng Hà Nội - APH", CHA, GOC), "Hà Nội - APH")
        self.assertEqual(t.dia_diem("Kho NL dầu - APH", CHA, GOC), "Nhà máy - APH")
        self.assertEqual(t.dia_diem("Hàng đang vận chuyển - APH", CHA, GOC), "Hàng đang vận chuyển - APH")
        self.assertEqual(t.dia_diem("Kho lạ", {}, GOC), "Kho lạ")

    def test_dia_diem_vong_lap(self):
        self.assertEqual(t.dia_diem("A", {"A": "B", "B": "A"}, set()), t.KHAC)

    def test_tai_khoan_thu_tu(self):
        self.assertEqual(t.tai_khoan("155", "156", "1561"), "155")
        self.assertEqual(t.tai_khoan(None, "156", "1561"), "156")
        self.assertEqual(t.tai_khoan(None, None, "1561"), "1561")
        self.assertEqual(t.tai_khoan(None, None, None), t.KHONG_RO)

    def test_tong_hop_doi_chieu(self):
        dong = [{"tk": "155", "dia_diem": "HN", "gia_tri": 100}, {"tk": "155", "dia_diem": "NM", "gia_tri": 50},
                {"tk": "155", "dia_diem": "HN", "gia_tri": 25}, {"tk": "156", "dia_diem": "HN", "gia_tri": 40}]
        r = t.tong_hop(dong, {"155": 175, "156": 40, "152": 10})
        tk155 = [x for x in r if x["tk"] == "155" and x["kieu"] == "tong_tk"][0]
        self.assertEqual((tk155["gia_tri"], tk155["so_cai"], tk155["chenh_lech"]), (175, 175, 0))
        hn = [x for x in r if x["tk"] == "155" and x["dia_diem"] == "HN"][0]
        self.assertEqual(hn["gia_tri"], 125)
        tk152 = [x for x in r if x["tk"] == "152" and x["kieu"] == "tong_tk"][0]  # có sổ cái, không có tồn kho
        self.assertEqual(tk152["chenh_lech"], -10)
        cuoi = r[-1]
        self.assertEqual((cuoi["kieu"], cuoi["gia_tri"], cuoi["so_cai"], cuoi["chenh_lech"]), ("tong", 215, 225, -10))


if __name__ == "__main__":
    unittest.main()
