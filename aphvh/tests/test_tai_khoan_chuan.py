import unittest

from aphvh import tai_khoan_chuan as C


class TestTaiKhoanChuan(unittest.TestCase):
    def test_thieu(self):
        co = {"1111", "11211", "131", "3388"}
        self.assertEqual(C.thieu(co, ["1111", "1121", "131", "3388", "242"]), ["242"])  # 11211 là con của 1121

    def test_chon_so(self):
        self.assertEqual(C.chon_so_thu_ho({"3388", "33881"}), "33880")
        self.assertEqual(C.chon_so_thu_ho({f"{n}" for n in range(33880, 33889)}), "33889")
        self.assertIsNone(C.chon_so_thu_ho({f"{n}" for n in range(33880, 33890)}))

    def test_chon_cha(self):
        ds = [{"name": "338 - X", "account_number": "338", "is_group": 1, "parent_account": "3 - X", "root_type": "Liability"},
              {"name": "33 - X", "account_number": "33", "is_group": 1, "parent_account": "3 - X", "root_type": "Liability"},
              {"name": "Chi phi - X", "account_number": None, "is_group": 1, "parent_account": None, "root_type": "Expense"}]
        self.assertEqual(C.chon_cha("3381", ds, "Liability"), "338 - X")
        self.assertEqual(C.chon_cha("641", ds, "Expense"), "Chi phi - X")
        self.assertIsNone(C.chon_cha("242", ds, "Asset"))

    def test_ten_chuan_phu_cac_so_hay_thieu(self):
        for k in ("153", "242", "1381", "3381", "641"):
            self.assertIn(k, C.TEN_CHUAN)

    def test_loai_don_vi(self):
        self.assertEqual(C.loai_don_vi("VHT"), "vh")
        self.assertEqual(C.loai_don_vi("tl"), "tl")
        self.assertIsNone(C.loai_don_vi("XYZ"))

    def test_thu_ho_chi_aph_vh(self):
        self.assertEqual(set(C.CO_THU_HO), {"aph", "vh"})
        for k in C.CO_THU_HO:
            self.assertIn("3388", C.CAN[k])

    def test_cac_ben_deu_co_bo_can(self):
        self.assertEqual(set(C.CAN), {"aph", "vh", "mk", "tl"})


if __name__ == "__main__":
    unittest.main()
