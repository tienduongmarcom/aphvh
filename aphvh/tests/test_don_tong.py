"""Kiểm thử Đơn tổng (0.3.9) — không cần Frappe."""

import json
import pathlib
import unittest

from aphvh import don_tong_rules as R

APP = pathlib.Path(__file__).resolve().parents[1]
DT = APP / "aph_vh" / "doctype"


def row(idx, cong_ty, hd, qty=1, rate=100):
    return {"idx": idx, "cong_ty": cong_ty, "xuat_hoa_don": hd, "qty": qty, "rate": rate}


class TestRules(unittest.TestCase):
    def test_group(self):
        rows = [row(1, "APH", "Có"), row(2, "VH", "Không"), row(3, "APH", "Không"), row(4, "APH", "Có")]
        g = R.group_rows(rows)
        self.assertEqual([k for k, _ in g], [("APH", "Có"), ("VH", "Không"), ("APH", "Không")])
        self.assertEqual([r["idx"] for r in g[0][1]], [1, 4])

    def test_problems(self):
        self.assertEqual(R.row_problems([row(1, "APH", "Có")]), [])
        loi = R.row_problems([row(1, "", "Có"), row(2, "APH", ""), row(3, "APH", "Có", qty=0)])
        self.assertEqual(len(loi), 3)
        self.assertIn("Dòng 1", loi[0])

    def test_tong_hop(self):
        t = R.tong_hop([{"tong": 1_050_000, "da_lap_hd": 1_050_000, "da_thu": 840_000},
                        {"tong": 560_000, "da_lap_hd": 0, "da_thu": 0}])
        self.assertEqual(t["tong"], 1_610_000)
        self.assertEqual(t["chua_lap_hd"], 560_000)
        self.assertEqual(t["con_phai_thu"], 770_000)


class TestThuGop(unittest.TestCase):
    CHO = [
        {"cong_ty": "VHT", "loai": "SI", "ten": "V1", "con_lai": 560, "ngay": "2026-10-01"},
        {"cong_ty": "APH", "loai": "SI", "ten": "A1", "con_lai": 300, "ngay": "2026-10-02"},
        {"cong_ty": "APH", "loai": "SO", "ten": "S1", "con_lai": 500, "ngay": "2026-10-01"},
        {"cong_ty": "MKT", "loai": "SO", "ten": "M1", "con_lai": 200, "ngay": "2026-10-01"},
    ]

    def test_order_and_split(self):
        p = R.phan_bo_thu_gop(1000, "APH", self.CHO)
        self.assertEqual([(d["ten"], d["so_tien"]) for d in p["dong"]], [("A1", 300), ("V1", 560), ("S1", 140)])
        self.assertEqual(p["tra_truoc"], 0)

    def test_excess_is_prepayment(self):
        p = R.phan_bo_thu_gop(2000, "VHT", self.CHO)
        self.assertEqual(p["dong"][0]["ten"], "V1")  # hóa đơn của đơn vị nhận tiền trước
        self.assertEqual(sum(d["so_tien"] for d in p["dong"]), 1560)
        self.assertEqual(p["tra_truoc"], 440)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            R.phan_bo_thu_gop(0, "APH", self.CHO)

    def test_noi_bo_symmetric(self):
        for a, m in R.NOI_BO.items():
            for b in m:
                self.assertIn(a, R.NOI_BO[b], f"{b} thiếu TK nội bộ với {a}")
        self.assertEqual(R.tk_noi_bo("APH", "VHT"), ("13883", "33885"))


class TestDoctype(unittest.TestCase):
    def test_json(self):
        p = json.loads((DT / "don_tong_aph" / "don_tong_aph.json").read_text(encoding="utf-8"))
        c = json.loads((DT / "don_tong_aph_item" / "don_tong_aph_item.json").read_text(encoding="utf-8"))
        self.assertEqual(p["name"], "Don Tong APH")
        self.assertEqual(p["is_submittable"], 1)
        names = [f["fieldname"] for f in p["fields"]]
        self.assertEqual(p["field_order"], names)
        self.assertIn("amended_from", names)
        table = next(f for f in p["fields"] if f["fieldname"] == "items")
        self.assertEqual(table["options"], c["name"])
        self.assertEqual(c["istable"], 1)
        for f in ("item_code", "qty", "rate", "cong_ty", "xuat_hoa_don", "sales_order"):
            self.assertIn(f, [x["fieldname"] for x in c["fields"]])
        roles = {x["role"] for x in p["permissions"]}
        self.assertNotIn("Nhân viên bán hàng APH", roles)  # vai trò của app cấp qua install (có thể chưa tồn tại lúc đồng bộ)
        self.assertIn("Sales User", roles)

    def test_dashboard_and_hooks(self):
        import importlib

        dash = importlib.import_module("aphvh.aph_vh.doctype.don_tong_aph.don_tong_aph_dashboard").get_data()
        self.assertEqual(dash["fieldname"], "aphvh_don_tong")
        hooks = (APP / "hooks.py").read_text()
        self.assertIn("aphvh.print_utils.aphvh_don_tong", hooks)
        inst = (APP / "install.py").read_text()
        self.assertIn('"Don Tong APH": _DOC', inst)
        self.assertIn("DON_TONG_CUSTOM_FIELDS", inst)


if __name__ == "__main__":
    unittest.main()
