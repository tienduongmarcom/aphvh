import pathlib
import unittest

from lab9x import nhom_hang as N


class TestNhomHang(unittest.TestCase):
    def test_tk_hieu_luc_lay_gan_nhat(self):
        chuoi = [{}, {"APH": "1551"}, {"APH": "156", "VH": "1561"}]  # con chưa có, cha 1551, gốc 156/1561
        self.assertEqual(N.tk_hieu_luc(chuoi), {"APH": "1551", "VH": "1561"})

    def test_doi_nhom_cung_tai_khoan(self):
        self.assertEqual(N.khac_tai_khoan({"APH": "1551"}, {"APH": "1551"}), {})
        self.assertEqual(N.khac_tai_khoan({"APH": "156"}, {"APH": "1551"}), {"APH": ("156", "1551")})
        self.assertEqual(N.khac_tai_khoan({"APH": "156"}, {}), {"APH": ("156", None)})

    def test_tk_bi_doi(self):
        self.assertEqual(N.tk_bi_doi({"APH": "156"}, {"APH": "156", "VH": "1561"}), {})  # thêm công ty mới thì được
        self.assertEqual(N.tk_bi_doi({"APH": "156"}, {"APH": "1551"}), {"APH": ("156", "1551")})
        self.assertEqual(N.tk_bi_doi({"APH": "156"}, {}), {"APH": ("156", None)})

    def test_gan_hook(self):
        h = (pathlib.Path(N.__file__).parent / "hooks.py").read_text(encoding="utf-8")
        for fn in ("item_group_after_insert", "item_group_validate", "item_validate"):
            self.assertIn(f"lab9x.nhom_hang.{fn}", h)
