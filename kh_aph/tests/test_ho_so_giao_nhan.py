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
        self.f.flags = types.SimpleNamespace()
        self.f.flags.get = lambda key: getattr(self.f.flags, key, None)
        self.f.session = types.SimpleNamespace(user="kt")
        self.f.TimestampMismatchError = ValueError
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.throw = lambda msg, *a: (_ for _ in ()).throw(ValueError(msg))
        self.f.get_all = Mock(return_value=[{"name": "file-1"}])
        self.f.db = Mock()
        self.f.db.sql.return_value = []
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

    def test_khong_cong_khai_hoac_doi_nguon_file_da_chon(self):
        self.f.get_meta = lambda dt: types.SimpleNamespace(has_field=lambda f: True)
        self.f.db.exists.return_value = True
        old = self.doc(file_url="/private/files/ky.pdf", is_private=1, attached_to_name="DN-1")
        old.file_url = old.get("file_url")
        for change in ({"is_private": 0}, {"attached_to_name": "DN-2"}, {"content": "ghi de"}):
            d = self.doc(old, **{"file_url": old.file_url, "is_private": 1, "attached_to_name": "DN-1", **change})
            with self.assertRaises(ValueError): self.m.protect_file_update(d)

    def test_thay_ban_ky_giu_tap_cu_va_nguoi_da_doi_chieu(self):
        import json
        old = self.doc(kh_aph_ban_ky='/private/files/cu.pdf', kh_aph_doi_chieu_boi='kt', kh_aph_doi_chieu_luc='hom qua')
        doc = self.doc(old, kh_aph_ban_ky='/private/files/moi.pdf', kh_aph_doi_chieu_boi='kt', kh_aph_doi_chieu_luc='hom qua')
        self.m.validate(doc)
        history = json.loads(doc.get(self.m.HISTORY))
        self.assertEqual(history['files'], ['/private/files/cu.pdf', '/private/files/moi.pdf'])
        self.assertEqual(history['events'][0]['before'][self.m.ACTOR], 'kt')
        self.assertEqual(history['events'][0]['after'][self.m.ACTOR], '')
        self.assertEqual(history['events'][0]['by'], 'kt')
        with self.assertRaises(ValueError):
            self.m.validate(self.doc(old, **{self.m.HISTORY: '{}'}))

    def test_chan_xoa_ca_tap_da_thay_va_phieu_da_huy(self):
        self.f.get_meta = lambda dt: types.SimpleNamespace(has_field=lambda f: True)
        self.f.db.exists.return_value = False
        self.f.db.sql.return_value = [('DN-CU',)]
        with self.assertRaises(ValueError):
            self.m.protect_file(types.SimpleNamespace(file_url='/private/files/cu.pdf'))
        query, params = self.f.db.sql.call_args.args
        self.assertIn('JSON_CONTAINS', query)
        self.assertEqual(params, ('"/private/files/cu.pdf"',))
        self.assertNotIn('docstatus', query)
        with self.assertRaises(ValueError):
            self.m.prevent_delete(self.doc(docstatus=2, kh_aph_ban_ky='/private/files/cu.pdf'))

    def test_moc_thoi_gian_json_va_db_la_cung_gia_tri(self):
        from datetime import datetime
        stamp = datetime(2026, 10, 17, 15, 0, 0, 123456)
        old = self.doc(kh_aph_doi_chieu_boi="kt", kh_aph_doi_chieu_luc=stamp)
        d = self.doc(old, kh_aph_doi_chieu_boi="kt", kh_aph_doi_chieu_luc=str(stamp))
        self.m.validate(d)

    def review_doc(self, **kw):
        d = self.doc(kh_aph_ban_ky="/private/files/ky.pdf", kh_aph_delivery_state="Khách đã nhận", **kw)
        d.modified = "2026-10-17 14:00:00"
        d.check_permission = Mock()
        d.save = Mock()
        d.add_comment = Mock()
        self.f.get_doc = Mock(return_value=d)
        return d

    def test_doi_chieu_kiem_quyen_doc_va_ghi(self):
        d = self.review_doc()
        d.check_permission.side_effect = ValueError("khong co quyen")
        with self.assertRaises(ValueError): self.m.doi_chieu("DN-1", d.modified)
        self.f.get_all.assert_not_called()
        d.save.assert_not_called()

    def test_phien_cu_va_chua_nhan_khong_duoc_doi_chieu(self):
        d = self.review_doc()
        with self.assertRaises(ValueError): self.m.doi_chieu("DN-1", "cu")
        d.save.assert_not_called()
        d.set("kh_aph_delivery_state", "Đang giao")
        with self.assertRaises(ValueError): self.m.doi_chieu("DN-1", d.modified)
        d.save.assert_not_called()

    def test_xac_nhan_va_bam_lai_khong_them_dau_moi(self):
        d = self.review_doc()
        result = self.m.doi_chieu("DN-1", d.modified)
        self.assertEqual(result["doi_chieu_boi"], "kt")
        self.assertEqual([x.args[0] for x in d.check_permission.call_args_list], ["read", "write"])
        self.m.doi_chieu("DN-1", d.modified)
        d.save.assert_called_once()
        d.add_comment.assert_called_once()
        self.assertIsNone(self.f.flags.get("kh_aph_doi_chieu_ban_ky"))

    def test_save_loi_phuc_hoi_co_noi_bo(self):
        d = self.review_doc()
        d.save.side_effect = ValueError("save loi")
        with self.assertRaises(ValueError): self.m.doi_chieu("DN-1", d.modified)
        self.assertIsNone(self.f.flags.get("kh_aph_doi_chieu_ban_ky"))
        d.add_comment.assert_not_called()

    def test_ho_so_khong_doi_bo_cuc_cac_truong_chuan(self):
        fields = self.m.fields()
        self.assertFalse(any(f["fieldtype"] in ("Section Break", "Tab Break", "Column Break") for f in fields))
        self.assertTrue(all(f.get("depends_on") for f in fields))

    def test_chan_truoc_khi_native_xoa_blob(self):
        called = []
        class NativeFile:
            def on_trash(self):
                called.append("da xoa")
        class File(self.m.HoSoFileMixin, NativeFile):
            file_url = "/private/files/ky.pdf"
        self.f.get_meta = lambda dt: types.SimpleNamespace(has_field=lambda f: True)
        self.f.db.exists.return_value = True
        with self.assertRaises(ValueError): File().on_trash()
        self.assertEqual(called, [])
        self.f.db.exists.return_value = False
        File().on_trash()
        self.assertEqual(called, ["da xoa"])
