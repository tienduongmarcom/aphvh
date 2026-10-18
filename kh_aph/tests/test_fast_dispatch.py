"""Ranh giới xuất ngay; giao dịch/rollback và sổ được kiểm bằng HTTP thật."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class FastDispatch(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.throw = lambda msg, exc=ValueError: (_ for _ in ()).throw(exc(msg))
        self.f.PermissionError = PermissionError
        self.f.has_permission = Mock(return_value=True)
        self.f.conf = {"kh_aph_post_receivable_on_delivery": 1}
        utils = types.ModuleType("frappe.utils")
        utils.cint = lambda v: int(v or 0)
        utils.flt = lambda v: float(v or 0)
        utils.now_datetime = Mock()
        self.mods = patch.dict(sys.modules, {"frappe": self.f, "frappe.utils": utils})
        self.mods.start()
        for name in ("kh_aph.ban_nhanh", "kh_aph.delivery_info"): sys.modules.pop(name, None)
        self.m = importlib.import_module("kh_aph.ban_nhanh")
        self.m._guard = Mock()

    def tearDown(self):
        for name in ("kh_aph.ban_nhanh", "kh_aph.delivery_info"): sys.modules.pop(name, None)
        self.mods.stop()

    def test_draft_and_immediate_are_distinct_operations(self):
        with patch.object(self.m, "_create") as create:
            self.m.create_drafts("ROOT", [], "TOKEN", {})
            self.assertEqual(create.call_args.kwargs, {})
            self.m.create_and_dispatch("ROOT", [], "TOKEN", {}, "Kho A")
            self.assertEqual(create.call_args.kwargs, {"dispatcher": "Kho A", "dispatch": True})

    def test_permission_checked_before_any_create(self):
        self.f.has_permission.return_value = False
        with self.assertRaises(PermissionError): self.m.create_and_dispatch("ROOT", [], "TOKEN", {}, "Kho A")
        self.f.has_permission.return_value = True; self.f.conf = {}
        with self.assertRaises(ValueError): self.m.create_and_dispatch("ROOT", [], "TOKEN", {}, "Kho A")

    def test_actual_dispatcher_not_fabricated_or_unbounded(self):
        for value in (None, 12, " ", "a\nb", "a"*141):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.m.create_and_dispatch("ROOT", [], "TOKEN", {}, value)

    def note(self, **kw):
        values = {"customer": "KH", "docstatus": 1, "is_return": 0,
                  "kh_aph_delivery_state": "Đang giao", "kh_aph_ban_giao_luc": "now", "kh_aph_ban_giao_boi": "kho",
                  "kh_aph_nguoi_thuc_giao": "Kho A", **kw}
        note = types.SimpleNamespace(**values)
        note.get = lambda key: getattr(note, key, None)
        note.check_permission = Mock()
        note.items = [types.SimpleNamespace(so_detail="ROW", qty=2.0, against_sales_order="SO")]
        return note

    def test_retry_validates_live_quantity_and_status(self):
        root = types.SimpleNamespace(name="ROOT", customer="KH")
        info = {key: "" for key in self.m.delivery_info.MAPPING}
        self.m._dispatch_permissions = Mock()
        so = types.SimpleNamespace(check_permission=Mock(), get=lambda key: "ROOT")
        self.f.get_doc = Mock(return_value=so)
        note = self.note()
        self.m._dispatched_matches(root, [note], [{"source_row": "ROW", "qty": 2}], info, "Kho A")
        for bad in (self.note(docstatus=0), self.note(docstatus=2), self.note(customer="KH-khác"), self.note(is_return=1)):
            with self.assertRaises(ValueError): self.m._dispatched_matches(root, [bad], [{"source_row": "ROW", "qty": 2}], info, "Kho A")
        with self.assertRaises(ValueError): self.m._dispatched_matches(root, [note], [{"source_row": "ROW", "qty": 3}], info, "Kho A")
        with self.assertRaises(ValueError): self.m._dispatched_matches(root, [note], [{"source_row": "ROW", "qty": "NaN"}], info, "Kho A")

    def test_retry_rechecks_native_write_submit_print_scope(self):
        note = self.note(); self.m._note_scope = Mock()
        self.m._dispatch_permissions(note)
        self.assertEqual([c.args[0] for c in note.check_permission.call_args_list], ["write", "submit", "print"])
        note.check_permission.side_effect = PermissionError("thu hồi")
        with self.assertRaises(PermissionError): self.m._dispatch_permissions(note)
