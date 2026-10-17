"""Ranh giới thông tin đợt giao: không tin field ngoài allowlist, quyền và lịch sử."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from kh_aph.delivery_info_rules import normalize


class DeliveryInfoRules(unittest.TestCase):
    def test_normalize(self):
        r = normalize({"delivery_method": "Vận chuyển", "recipient": "  Anh Nam  ", "phone": " 0901 "})
        self.assertEqual(r["recipient"], "Anh Nam")
        self.assertEqual(r["phone"], "0901")
        self.assertEqual(r["vehicle_no"], "")
        self.assertEqual(normalize(None), {})
        self.assertEqual(normalize({}), {})

    def test_invalid_payload(self):
        good = {"delivery_method": "Khách đến lấy", "recipient": "Bình"}
        for value in ([], "abc", {**good, "docstatus": 1}, {**good, "phone": 123},
                      {**good, "recipient": " "}, {**good, "phone": "x" * 61},
                      {**good, "recipient": "a\nb"}, {**good, "delivery_method": "khác"}):
            with self.subTest(value=value), self.assertRaises(ValueError): normalize(value)


class DeliveryInfoBoundary(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.conf = {"kh_aph_trung_tam_ban": 1}
        self.f.PermissionError = PermissionError
        self.f.flags = {}
        self.f.session = types.SimpleNamespace(user="kho")
        self.f.has_permission = Mock(return_value=True)
        self.f.throw = lambda msg, exc=ValueError: (_ for _ in ()).throw(exc(msg))
        self.address = types.SimpleNamespace(disabled=0, check_permission=Mock(),
                    links=[types.SimpleNamespace(link_doctype="Customer", link_name="KH")])
        self.f.get_doc = Mock(return_value=self.address)
        utils = types.ModuleType("frappe.utils"); utils.cint = lambda v: int(v or 0)
        utils.now_datetime = lambda: "2026-10-17 21:00:00"
        self.mods = patch.dict(sys.modules, {"frappe": self.f, "frappe.utils": utils})
        self.mods.start(); sys.modules.pop("kh_aph.delivery_info", None)
        self.m = importlib.import_module("kh_aph.delivery_info")

    def tearDown(self):
        sys.modules.pop("kh_aph.delivery_info", None); self.mods.stop()

    def doc(self, old=None, **kwargs):
        values = {self.m.METHOD: "Vận chuyển", self.m.RECIPIENT: "Nam", self.m.DISPATCHER: "Kho A",
                  "docstatus": 1, "shipping_address_name": "DC", **kwargs}
        d = types.SimpleNamespace(customer="KH", name="DN", docstatus=values["docstatus"], is_return=0,
                                  meta=types.SimpleNamespace(has_field=lambda f: True))
        d.get = lambda k: values.get(k); d.set = lambda k,v: values.update({k:v})
        d.get_doc_before_save = lambda: old
        return d

    def test_address_checked_with_native_read_and_customer_link(self):
        self.m.check_address("KH", "DC")
        self.address.check_permission.assert_called_once_with("read")
        with self.assertRaises(ValueError): self.m.check_address("KH-khac", "DC")
        self.address.disabled = 1
        with self.assertRaises(ValueError): self.m.check_address("KH", "DC")
        self.address.check_permission.side_effect = PermissionError("riêng")
        with self.assertRaises(PermissionError): self.m.check_address("KH", "DC")

    def test_submitted_metadata_cannot_be_overwritten(self):
        old = self.doc()
        with self.assertRaises(ValueError): self.m.validate(self.doc(old=old, kh_aph_nguoi_nhan_tai_kho="Người khác"))
        with self.assertRaises(ValueError): self.m.validate(self.doc(old=old, kh_aph_cach_giao=""))

    def test_signed_file_update_does_not_regenerate_posted_address(self):
        old = self.doc(); d = self.doc(old=old)
        self.m.validate(d)
        self.f.get_doc.assert_not_called()

    def test_dispatcher_needs_submit_permission(self):
        old = self.doc(docstatus=0, kh_aph_nguoi_thuc_giao="")
        self.f.has_permission.return_value = False
        with self.assertRaises(PermissionError): self.m.validate(self.doc(old=old, docstatus=0))

    def test_submit_requires_actual_dispatcher_and_correct_action(self):
        with self.assertRaises(ValueError): self.m.before_submit(self.doc(kh_aph_nguoi_thuc_giao=""))
        self.f.flags = {"kh_aph_delivery_pickup": "DN"}
        with self.assertRaises(ValueError): self.m.before_submit(self.doc())
        self.m.before_submit(self.doc(kh_aph_cach_giao="Khách đến lấy"))
        self.f.flags = {}
        self.m.before_submit(self.doc())

    def test_handoff_stamp_is_server_owned_and_kept_on_receive(self):
        d = self.doc()
        self.m.before_submit(d)
        self.assertEqual(d.get(self.m.HANDED_BY), "kho")
        self.assertEqual(d.get(self.m.HANDED_AT), "2026-10-17 21:00:00")
        old = self.doc(kh_aph_ban_giao_boi="kho", kh_aph_ban_giao_luc=d.get(self.m.HANDED_AT))
        current = self.doc(old=old, kh_aph_ban_giao_boi="kho", kh_aph_ban_giao_luc=d.get(self.m.HANDED_AT))
        self.m.validate(current)
        with self.assertRaises(ValueError): self.m.validate(self.doc(old=old, kh_aph_ban_giao_boi="giả"))

    def test_flag_off_does_not_change_old_docs(self):
        self.f.conf = {}
        self.m.validate(self.doc()); self.m.before_submit(self.doc(kh_aph_nguoi_thuc_giao=""))
        self.f.get_doc.assert_not_called()
