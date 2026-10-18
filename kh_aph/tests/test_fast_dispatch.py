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

    def test_print_uses_document_net_sales_values_including_zero(self):
        class Record(types.SimpleNamespace):
            def get(self, key, default=None): return getattr(self, key, default)
        helpers = types.ModuleType("kh_aph.print_utils")
        helpers.kh_aph_cong_ty = lambda company: {"ten": company, "dia_chi": "Địa chỉ công ty"}
        helpers.kh_aph_ngay = lambda date: "Ngày 18 tháng 10 năm 2026"
        helpers.kh_aph_mau_info = lambda *args: {"nhan": "Mẫu số 02 - VT (vận dụng)"}
        helpers.kh_aph_no_co = lambda doc: {"no": "", "co": ""}
        self.m._order = Mock(return_value=Record(name="ROOT"))
        self.m._note_scope = Mock()
        self.f.get_all = Mock(return_value=["DN-1"])
        self.f.utils = Record(strip_html=lambda text: text, get_fullname=lambda user: "Người lập")
        self.f.render_template = Mock(side_effect=lambda path, context: context)
        for net_rate in (30000, 0):
            row = Record(item_code="A", item_name="Đậu", warehouse="HN", qty=100, uom="Kg",
                         rate=37500, amount=3750000, net_rate=net_rate, net_amount=net_rate*100,
                         valuation_rate="KHÔNG ĐƯỢC IN GIÁ VỐN")
            note = Record(name="DN-1", company="APH", posting_date="2026-10-18", customer="KH-1",
                          customer_name="Khách", currency="VND", docstatus=0, owner="ktbh", items=[row],
                          check_permission=Mock())
            self.f.get_doc = Mock(return_value=note)
            with self.subTest(net_rate=net_rate), patch.dict(sys.modules, {"kh_aph.print_utils": helpers}):
                printed = self.m.print_batch("ROOT", "TOKEN")["html"]["notes"][0]
                self.assertEqual(printed["items"][0]["rate"], "30.000" if net_rate else "0")
                self.assertEqual(printed["total"], "3.000.000" if net_rate else "0")
                self.assertEqual(printed["total_qty"], "100")
                self.assertNotIn("valuation_rate", repr(printed))
                self.assertNotIn("KHÔNG ĐƯỢC IN GIÁ VỐN", repr(printed))
                note.check_permission.assert_called_once_with("print")

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
