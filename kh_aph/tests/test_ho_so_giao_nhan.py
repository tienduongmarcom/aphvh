"""Kiểm ranh giới hồ sơ ký nhận: tệp riêng đúng nguồn, dấu xác nhận không thể sửa tay."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class HoSoGiaoNhan(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.conf = {"kh_aph_trung_tam_ban": 1}
        self.f.flags = types.SimpleNamespace(get=lambda key: None)
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.throw = lambda msg, *a: (_ for _ in ()).throw(ValueError(msg))
        self.f.get_all = Mock(return_value=[{"name": "file-1"}])
        self.f.db = Mock()
        utils = types.ModuleType("frappe.utils")
        utils.cint = lambda v: int(v or 0)
        utils.now_datetime = lambda: "2026-10-17 15:00:00"
        self.modules = patch.dict(sys.modules, {"frappe": self.f, "frappe.utils": utils})
        self.modules.start()
        sys.modules.pop("kh_aph.ho_so_giao_nhan", None)
        self.m = importlib.import_module("kh_aph.ho_so_giao_nhan")

    def tearDown(self):
        sys.modules.pop("kh_aph.ho_so_giao_nhan", None)
        self.modules.stop()

    def doc(self, old=None, **kw):
        values = {"docstatus": 1, "is_return": 0, **kw}
        d = types.SimpleNamespace(name="DN-1", docstatus=values["docstatus"], is_return=values["is_return"],
                                  meta=types.SimpleNamespace(has_field=lambda f: True))
        d.get = lambda k: values.get(k)
        d.set = lambda k, v: values.update({k: v})
        d.get_doc_before_save = lambda: old
        return d

    def test_file_phai_rieng_va_gan_dung_phieu(self):
        d = self.doc(kh_aph_ban_ky="/private/files/ky.pdf")
        self.m.validate(d)
        filters = self.f.get_all.call_args.kwargs["filters"]
        self.assertEqual(filters["attached_to_name"], "DN-1")
        self.assertEqual(filters["is_private"], 1)
        self.f.get_all.return_value = []
        with self.assertRaises(ValueError): self.m.validate(d)
        self.f.get_all.return_value = [{"name": "f"}]
        with self.assertRaises(ValueError): self.m.validate(self.doc(kh_aph_ban_ky="https://ngoai.example/ky.pdf"))

    def test_thay_ho_so_lam_mat_doi_chieu(self):
        old = self.doc(kh_aph_ban_ky="/private/files/1.pdf", kh_aph_doi_chieu_boi="kt", kh_aph_doi_chieu_luc="hom qua")
        for change in ({"kh_aph_ban_ky": "/private/files/2.pdf"}, {"kh_aph_ban_ky": ""}, {"kh_aph_ghi_chu_ban_ky": "Thieu 2 bao"}):
            d = self.doc(old, kh_aph_doi_chieu_boi="kt", kh_aph_doi_chieu_luc="hom qua",
                         **{"kh_aph_ban_ky": "/private/files/1.pdf", **change})
            self.m.validate(d)
            self.assertIsNone(d.get(self.m.ACTOR))
            self.assertIsNone(d.get(self.m.TIME))

    def test_khong_sua_tay_nguoi_va_thoi_gian(self):
        for field in (self.m.ACTOR, self.m.TIME):
            with self.assertRaises(ValueError): self.m.validate(self.doc(**{field: "gia mao"}))

    def test_khong_bat_buoc_ho_so_khi_giao_hang(self):
        self.m.validate(self.doc())
        self.f.get_all.assert_not_called()

    def test_nhap_va_phieu_tra_khong_nhan_ban_ky(self):
        for props in ({"docstatus": 0}, {"is_return": 1}):
            with self.assertRaises(ValueError): self.m.validate(self.doc(kh_aph_ban_ky="/private/files/ky.pdf", **props))

    def test_co_tat_khong_tac_dong(self):
        self.f.conf = {}
        self.m.validate(self.doc(kh_aph_doi_chieu_boi="x"))
        self.f.get_all.assert_not_called()

    def test_chan_xoa_file_dang_lam_ho_so(self):
        self.f.get_meta = lambda dt: types.SimpleNamespace(has_field=lambda f: True)
        self.f.db.exists.return_value = True
        with self.assertRaises(ValueError): self.m.protect_file(types.SimpleNamespace(file_url="/private/files/ky.pdf"))
        self.f.db.exists.return_value = False
        self.m.protect_file(types.SimpleNamespace(file_url="/private/files/ky.pdf"))
