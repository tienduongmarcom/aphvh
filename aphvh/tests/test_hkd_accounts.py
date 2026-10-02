import unittest

from aphvh import hkd_accounts as H


class TestHkdAccounts(unittest.TestCase):
    def test_plan_tu_tai_khoan_thu(self):
        ex = {
            "1111": {"name": "1111 - Tiền mặt - MKT", "account_name": "Tiền mặt", "parent_number": None, "is_group": 0},
            "5111": {"name": "x", "account_name": "Doanh thu bán hàng hóa (sổ S2a)", "parent_number": None, "is_group": 0},
            "6422": {"name": "y", "account_name": "Chi phí (chỉ quản trị, hộ nộp theo tỷ lệ không trừ chi phí)", "parent_number": None, "is_group": 0},
        }
        jobs = H.plan(ex)
        self.assertEqual(jobs[0], ("doi_so", "6422", "6428"))
        self.assertIn(("sua", "5111", {"account_name": "Doanh thu bán hàng hóa"}), jobs)
        self.assertIn(("tao", "6422"), jobs)  # số 6422 mới: vận chuyển
        self.assertIn(("tao", "642"), jobs)
        sua6428 = [j for j in jobs if j[0] == "sua" and j[1] == "6428"][0]
        self.assertEqual(sua6428[2], {"account_name": "Chi phí khác", "parent_number": "642"})
        self.assertNotIn(("tao", "1111"), jobs)
        # nhóm 642 phải tạo trước khi chuyển 6428 vào
        self.assertLess(jobs.index(("tao", "642")), jobs.index(sua6428))

    def test_chay_lai_khong_lam_gi(self):
        ex = {no: {"name": no, "account_name": name, "parent_number": parent, "is_group": g}
              for no, name, _r, _t, parent, g in H.ACCOUNTS}
        self.assertEqual(H.plan(ex), [])

    def test_khong_doi_so_tai_khoan_6422_da_dung_dung(self):
        ex = {"6422": {"name": "z", "account_name": "Chi phí vận chuyển, bốc xếp", "parent_number": "642", "is_group": 0}}
        self.assertNotIn(("doi_so", "6422", "6428"), H.plan(ex))


if __name__ == "__main__":
    unittest.main()
