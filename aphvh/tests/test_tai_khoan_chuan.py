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
