import unittest

from lab9x import vat_rules as V


class TestThueMua(unittest.TestCase):
    def test_lay_theo_ban_cho_doanh_nghiep(self):
        self.assertEqual(V.mau_thue_mua_mac_dinh({V.CAT_DN: "GTGT 10% - APH", V.CAT_HKD: "GTGT 5% - APH"}), "GTGT 10% - APH")

    def test_mot_mau_duy_nhat(self):
        self.assertEqual(V.mau_thue_mua_mac_dinh({"": "GTGT 8% - VH"}), "GTGT 8% - VH")

    def test_khong_ro(self):
        self.assertIsNone(V.mau_thue_mua_mac_dinh({}))
        self.assertIsNone(V.mau_thue_mua_mac_dinh({"": "GTGT 5% - VH", V.CAT_HKD: "GTGT 10% - VH"}))
