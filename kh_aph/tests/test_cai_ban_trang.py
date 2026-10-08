import unittest

from kh_aph import cai_ban_trang as c


class TestCaiBanTrang(unittest.TestCase):
    def test_mac_dinh_hop_le(self):
        for loai in ("aph", "vh"):
            self.assertEqual(c.kiem_mac_dinh(loai), [], loai)

    def test_kho_mac_dinh(self):
        self.assertEqual(c.mac_dinh("aph")["default_inventory_account"], "156")
        self.assertEqual(c.mac_dinh("vh")["default_inventory_account"], "1561")

    def test_tk_tam_khong_phai_3389(self):
        self.assertNotEqual(c.TK_TAM[0], "3389")
        self.assertEqual(c.TK_TAM[3], "Temporary")

    def test_nhom_hang_va_kho(self):
        for loai in ("aph", "vh"):
            self.assertEqual(c.kiem_nhom_hang(loai), [], loai)
        self.assertFalse(hasattr(c, "cay_nha_may"))  # 0.8.0: không tạo cây kho, khách tự tạo
