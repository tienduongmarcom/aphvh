"""Kiểm các ranh giới phân quyền, nguồn chứng từ và lịch sử của hồ sơ chênh lệch."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from kh_aph import delivery_issue_rules as R


class IssueRules(unittest.TestCase):
    def test_schema_payload_and_dates(self):
        self.assertEqual(R.normalize("report", {"noi_dung": "  Lệch 1 bao  "}), {"noi_dung": "Lệch 1 bao"})
        for action, value in [("bad", {}), ("report", []), ("report", {"noi_dung": 5}),
                ("report", {"noi_dung": "x", "docstatus": 1}), ("report", {"noi_dung": "x"*2001}),
                ("report", {"noi_dung": "x\0"}), ("assign", {"nguoi_phu_trach": "a", "han_xu_ly": "2026-02-30"}),
                ("assign", {"nguoi_phu_trach": "a", "han_xu_ly": "2026-10-18T01:00:00"})]:
            with self.subTest(action=action, value=value), self.assertRaises(ValueError): R.normalize(action, value)

    def test_proof_matches_outcome(self):
        for mode, ret, credit in [(R.NO_LEDGER, "DN", ""), (R.RETURN, "", ""), (R.CREDIT, "DN", "SI")]:
            with self.assertRaises(ValueError):
                R.normalize("resolve", {"cach_xu_ly": mode, "ket_qua": "Đã kiểm", "phieu_tra": ret, "hoa_don_giam": credit})
        self.assertEqual(R.normalize("resolve", {"cach_xu_ly": R.RETURN, "ket_qua": "Đã nhập lại", "phieu_tra": "DN"})["phieu_tra"], "DN")

    def test_transition_never_closes_from_note_or_review(self):
        self.assertEqual(R.transition("", "report"), R.PENDING)
        self.assertEqual(R.transition(R.PENDING, "assign"), R.ACTIVE)
        self.assertEqual(R.transition(R.ACTIVE, "report"), R.ACTIVE)
        self.assertEqual(R.transition(R.ACTIVE, "resolve"), R.CLOSED)
        for state, action in [("", "resolve"), (R.PENDING, "resolve"), (R.CLOSED, "report"), (R.CLOSED, "resolve")]:
            with self.assertRaises(ValueError): R.transition(state, action)


class IssueBoundary(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.conf = {"kh_aph_trung_tam_ban": 1}
        self.f.flags = {}
        self.f.session = types.SimpleNamespace(user="chief")
        self.f.PermissionError = PermissionError
        self.f.TimestampMismatchError = RuntimeError
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.throw = lambda msg, exc=ValueError: (_ for _ in ()).throw(exc(msg))
        self.f.get_roles = Mock(return_value=["Accounts Manager"])
        self.f.parse_json = __import__("json").loads
        self.f.has_permission = Mock(return_value=True)
        self.f.db = Mock()
        self.f.db.sql.return_value = []
        self.f.db.get_value.return_value = types.SimpleNamespace(enabled=1, user_type="System User")
        self.f.db.exists.return_value = False
        self.f.get_meta = lambda dt: types.SimpleNamespace(has_field=lambda f: True)
        self.f.get_all = Mock(return_value=[{"name": "File"}])
        utils = types.ModuleType("frappe.utils")
        utils.cint = lambda v: int(v or 0)
        utils.now_datetime = lambda: "2026-10-18 01:00:00"
        self.mods = patch.dict(sys.modules, {"frappe": self.f, "frappe.utils": utils})
        self.mods.start()
        for name in ("kh_aph.delivery_issue", "kh_aph.ho_so_giao_nhan"): sys.modules.pop(name, None)
        self.m = importlib.import_module("kh_aph.delivery_issue")

    def tearDown(self):
        for name in ("kh_aph.delivery_issue", "kh_aph.ho_so_giao_nhan"): sys.modules.pop(name, None)
        self.mods.stop()

    def doc(self, old=None, **kw):
        values = {"docstatus": 1, "is_return": 0, "company": "APH", "customer": "KH", **kw}
        doc = types.SimpleNamespace(name="DN", doctype="Delivery Note", modified="now", **values)
        doc.get = lambda key: getattr(doc, key, None)
        doc.set = lambda key, value: setattr(doc, key, value)
        doc.meta = types.SimpleNamespace(has_field=lambda f: True)
        doc.get_doc_before_save = lambda: old
        doc.check_permission = Mock()
        doc.add_comment = Mock()
        doc.save = Mock()
        return doc

    def ready(self):
        return self.doc(**{self.m.STATE: R.ACTIVE, self.m.ASSIGNEE: "kho", self.m.DUE: "2026-10-18",
            self.m.FILE: "/private/files/ky.pdf", self.m.ACTOR: "kho", self.m.TIME: "stamp"})

    def call(self, doc, action, values, stamp="now"):
        self.f.get_doc = Mock(return_value=doc)
        return self.m.cap_nhat(doc.name, stamp, action, values)

    def test_direct_state_fields_all_protected(self):
        for field in self.m.FIELDS:
            with self.subTest(field=field), self.assertRaises(ValueError): self.m.validate(self.doc(**{field: "giả"}))
        self.m.validate(self.doc())

    def test_native_scope_and_chief_are_required(self):
        doc = self.doc(); doc.check_permission.side_effect = PermissionError("scope")
        with self.assertRaises(PermissionError): self.call(doc, "report", {"noi_dung": "Lệch"})
        doc.save.assert_not_called()
        self.f.get_roles.return_value = ["Accounts User"]
        with self.assertRaises(PermissionError): self.call(self.ready(), "assign", {"nguoi_phu_trach": "x", "han_xu_ly": "2026-10-18"})
        result = self.call(self.doc(), "report", {"noi_dung": "Lệch"})
        self.assertEqual(result[self.m.STATE], R.PENDING)

    def test_stale_and_draft_or_return_never_save(self):
        for doc, stamp, exc in [(self.doc(), "stale", RuntimeError), (self.doc(docstatus=0), "now", ValueError),
                                (self.doc(is_return=1), "now", ValueError), (self.doc(docstatus=2), "now", ValueError)]:
            with self.assertRaises(exc): self.call(doc, "report", {"noi_dung": "Lệch"}, stamp)
            doc.save.assert_not_called()

    def test_assignee_needs_live_native_document_permissions(self):
        doc = self.doc(**{self.m.STATE: R.PENDING})
        self.f.has_permission.return_value = False
        with self.assertRaises(ValueError): self.call(doc, "assign", {"nguoi_phu_trach": "ngoài kho", "han_xu_ly": "2026-10-18"})
        self.assertEqual(self.f.has_permission.call_args.kwargs["user"], "ngoài kho")
        doc.save.assert_not_called()

    def test_resolve_needs_reviewed_current_file(self):
        doc = self.ready(); doc.set(self.m.ACTOR, None)
        with self.assertRaises(ValueError): self.call(doc, "resolve", {"ket_qua": "Đã kiểm", "cach_xu_ly": R.NO_LEDGER})
        doc.save.assert_not_called()
        doc.set(self.m.ACTOR, "kho"); self.f.get_all.return_value = []
        with self.assertRaises(ValueError): self.call(doc, "resolve", {"ket_qua": "Đã kiểm", "cach_xu_ly": R.NO_LEDGER})

    def test_close_and_reopen_preserve_comment_and_server_stamps(self):
        doc = self.ready()
        result = self.call(doc, "resolve", {"ket_qua": "<script>x</script>", "cach_xu_ly": R.NO_LEDGER})
        self.assertEqual(result[self.m.CLOSE_BY], "chief")
        self.assertEqual(result[self.m.CLOSE_AT], "2026-10-18 01:00:00")
        self.assertEqual(result[self.m.STATE], R.CLOSED)
        self.assertNotIn("<script>", doc.add_comment.call_args.args[1])
        self.call(doc, "reopen", {"ly_do": "Cần kiểm lại"})
        self.assertIsNone(doc.get(self.m.RESULT))
        self.assertEqual(doc.get(self.m.STATE), R.ACTIVE)
        self.assertEqual(doc.add_comment.call_count, 2)
        self.assertIsNone(self.f.flags.get(self.m.FLAG))

    def test_return_proof_requires_source_company_customer_and_read(self):
        doc = self.ready()
        for change in ({"company": "VH"}, {"customer": "Khác"}, {"docstatus": 0}, {"is_return": 0}, {"return_against": "DN-khác"}):
            proof = self.doc(**{"return_against": "DN", "is_return": 1, **change})
            self.f.get_doc = Mock(return_value=proof)
            with self.assertRaises(ValueError): self.m._proof(doc, R.RETURN, "RET")
            proof.check_permission.assert_called_with("read")
        proof = self.doc(return_against="DN", is_return=1)
        self.f.get_doc = Mock(return_value=proof)
        self.m._proof(doc, R.RETURN, "RET")
        proof.check_permission.side_effect = PermissionError("ẩn")
        with self.assertRaises(PermissionError): self.m._proof(doc, R.RETURN, "RET")

    def test_credit_proof_never_adds_stock_or_accepts_ambiguous_invoice(self):
        doc = self.ready()
        proof = self.doc(return_against="SI", is_return=1, update_stock=0, items=[])
        original = self.doc(items=[{"delivery_note": "DN-khác"}])
        self.f.get_doc = Mock(side_effect=lambda dt,n,**kw: proof if n=="CREDIT" else original)
        with self.assertRaises(ValueError): self.m._proof(doc, R.CREDIT, "CREDIT")
        original.items = [{"delivery_note": "DN"}, {"delivery_note": "DN-khác"}]
        with self.assertRaises(ValueError): self.m._proof(doc, R.CREDIT, "CREDIT")
        proof.items = [{"delivery_note": "DN"}]
        self.m._proof(doc, R.CREDIT, "CREDIT")
        proof.update_stock = 1
        with self.assertRaises(ValueError): self.m._proof(doc, R.CREDIT, "CREDIT")

    def test_change_evidence_reopens_and_clears_proof_but_keeps_audit(self):
        old = self.ready(); old.set(self.m.STATE, R.CLOSED); old.set(self.m.RETURN, "RET"); old.set(self.m.RESULT, "Đã nhập lại")
        doc = self.doc(old, **{f: old.get(f) for f in self.m.FIELDS}, **{self.m.FILE: "/private/files/ky-moi.pdf"})
        self.m.validate(doc)
        self.assertEqual(doc.get(self.m.STATE), R.ACTIVE)
        self.assertIsNone(doc.get(self.m.RETURN))
        self.assertIsNone(doc.get(self.m.RESULT))
        self.assertIn("RET", doc.add_comment.call_args.args[1])

    def test_cancel_requires_reopening_linked_proof_and_closing_active_source(self):
        doc = self.ready()
        with self.assertRaises(ValueError): self.m.before_cancel(doc)
        doc.set(self.m.STATE, None); self.f.db.sql.return_value = [("DN",)]
        with self.assertRaises(ValueError): self.m.before_cancel(doc)
        self.f.db.sql.return_value = []
        self.m.before_cancel(doc)

    def test_flag_off_no_database_or_mutation(self):
        self.f.conf = {}
        doc = self.ready()
        self.m.validate(doc); self.m.before_cancel(doc)
        with self.assertRaises(ValueError): self.call(doc, "report", {"noi_dung": "x"})
        self.f.db.sql.assert_not_called()
        doc.save.assert_not_called()

    def test_save_failure_restores_private_flag(self):
        doc = self.ready(); doc.save.side_effect = ValueError("rollback")
        with self.assertRaises(ValueError): self.call(doc, "resolve", {"ket_qua": "Đã kiểm", "cach_xu_ly": R.NO_LEDGER})
        self.assertIsNone(self.f.flags.get(self.m.FLAG))
        doc.add_comment.assert_not_called()
