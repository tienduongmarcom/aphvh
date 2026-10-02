"""Kho dùng chung theo địa điểm (0.4.17) — quy tắc thuần."""
import unittest

from aphvh import kho_chung as k


def r(n, cha=None, nhom=0, tat=0, loai=""):
    return {"warehouse_name": n, "parent_name": cha, "is_group": nhom, "disabled": tat, "warehouse_type": loai}


APH = [
    r("Nhà máy An Phú Hưng", nhom=1), r("Kho hàng hóa nhà máy", "Nhà máy An Phú Hưng"),
    r("Hà Nội", nhom=1), r("Kho bán hàng Hà Nội", "Hà Nội"), r("Kho vệ tinh chị Thoa", "Hà Nội"),
    r("Kho vệ tinh bác Hiền", "Hà Nội"), r("Hàng chờ xử lý Hà Nội", "Hà Nội"),
    r("Đà Nẵng", nhom=1), r("Kho Đà Nẵng", "Đà Nẵng"), r("Hồ Chí Minh", nhom=1), r("Kho Hồ Chí Minh", "Hồ Chí Minh"),
    r("Hàng đang vận chuyển", loai="Transit"), r("Stores", tat=1), r("Hàng nhận ký gửi (TEST)", "Hà Nội"),
]


class TestKhoChung(unittest.TestCase):
    def test_cay_mau_bo_nha_may(self):
        ten = [x[0] for x in k.cay_mau(APH)]
        self.assertNotIn("Kho hàng hóa nhà máy", ten)
        self.assertNotIn("Nhà máy An Phú Hưng", ten)
        self.assertNotIn("Stores", ten)
        self.assertNotIn("Hàng nhận ký gửi (TEST)", ten)
        for n in ("Kho bán hàng Hà Nội", "Kho vệ tinh chị Thoa", "Kho vệ tinh bác Hiền", "Kho Đà Nẵng", "Kho Hồ Chí Minh", "Hàng đang vận chuyển"):
            self.assertIn(n, ten)

    def test_cha_truoc_con(self):
        cay = k.cay_mau(list(reversed(APH)))
        vt = {x[0]: i for i, x in enumerate(cay)}
        for n, cha, *_ in cay:
            if cha:
                self.assertLess(vt[cha], vt[n], n)

    def test_khong_co_mau_dung_mac_dinh(self):
        self.assertEqual(k.cay_mau([r("Stores")]), k.CAY_MAC_DINH)

    def test_plan_tao_bat_khong_trung(self):
        cay = k.cay_mau(APH)
        dich = {"Hà Nội": {"disabled": 0}, "Kho bán hàng Hà Nội": {"disabled": 0}, "Kho vệ tinh bác Hiền": {"disabled": 1}}
        jobs = k.plan(cay, dich)
        self.assertIn(("bat", "Kho vệ tinh bác Hiền"), jobs)
        tao = [j[1][0] for j in jobs if j[0] == "tao"]
        self.assertNotIn("Kho bán hàng Hà Nội", tao)
        self.assertNotIn("Hà Nội", tao)
        self.assertIn("Kho vệ tinh chị Thoa", tao)
        # chạy lại sau khi đủ -> không còn việc
        du = {x[0]: {"disabled": 0} for x in cay}
        self.assertEqual(k.plan(cay, du), [])


if __name__ == "__main__":
    unittest.main()
