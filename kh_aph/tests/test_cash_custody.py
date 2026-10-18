"""Người giữ tiền: không đoán lịch sử, giữ quyền và bất biến nguồn đã ghi sổ."""
import datetime
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Doc(types.SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self, key, default)


class CashCustody(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package = kh_aph
        self.old_attribute = getattr(kh_aph, "cash_custody", None)
        f = self.f = types.ModuleType("frappe")
        f.conf = {"kh_aph_cash_custody": 1}
        f.whitelist = lambda **kwargs: lambda fn: fn
        f.throw = lambda msg, exc=ValueError: (_ for _ in ()).throw(exc(msg))
        f.PermissionError = PermissionError
        f.get_roles = Mock(return_value=["Accounts User"])
        f.has_permission = Mock(return_value=True)
        f.db = Mock()
        f.db.get_value.return_value = Doc(enabled=1, user_type="System User")
        f.get_cached_value = Mock(side_effect=lambda dt, name, field: "Cash" if name == "1111" else "Bank")
        self.co = Doc(default_currency="VND", check_permission=Mock())
        f.get_doc = Mock(return_value=self.co)
        u = types.ModuleType("frappe.utils")
        u.cint = lambda value: int(value or 0)
        u.getdate = lambda value: datetime.date.fromisoformat(value)
        self.mods = patch.dict(sys.modules, {"frappe": f, "frappe.utils": u})
        self.mods.start()
        sys.modules.pop("kh_aph.cash_custody", None)
        self.m = importlib.import_module("kh_aph.cash_custody")

    def tearDown(self):
        sys.modules.pop("kh_aph.cash_custody", None)
        if self.old_attribute is None:
            delattr(self.package, "cash_custody")
        else:
            self.package.cash_custody = self.old_attribute
        self.mods.stop()

    def journal(self, users):
        return Doc(doctype="Journal Entry", company="APH", docstatus=0,
            accounts=[Doc(name=str(i), account="1111", **{self.m.HOLDER: user}) for i, user in enumerate(users)],
            get_doc_before_save=lambda: None)

    def test_flag_off_has_no_queries_or_effects(self):
        self.f.conf = {}
        self.m.validate(Doc())
        self.m.schema()
        row = {"account": "1111", "debit_in_account_currency": 12}
        self.assertEqual(self.m.stamp_rows([row], {"1111": "a"}), [row])
        self.f.db.get_value.assert_not_called()
        self.f.get_cached_value.assert_not_called()
        with self.assertRaises(ValueError):
            self.m.review("APH", "2026-10-01", "2026-10-01")

    def test_unknown_person_never_defaults_to_owner(self):
        doc = self.journal([None, None])
        doc.owner = "administrator"
        self.m.validate(doc)
        self.assertFalse(self.m._source_holder(doc, "1111"))
        self.f.db.get_value.assert_not_called()

    def test_one_cash_account_cannot_be_merged_across_holders(self):
        for users in (("a", "b"), ("a", None)):
            with self.assertRaisesRegex(ValueError, "Cùng tài khoản"):
                self.m.validate(self.journal(users))
        self.m.validate(self.journal(["a", "a"]))

    def test_disabled_external_or_out_of_company_holder_denied(self):
        for data in (None, Doc(enabled=0, user_type="System User"), Doc(enabled=1, user_type="Website User")):
            self.f.db.get_value.return_value = data
            with self.assertRaises(ValueError): self.m.validate(self.journal(["a"]))
        self.f.db.get_value.return_value = Doc(enabled=1, user_type="System User")
        self.f.has_permission.return_value = False
        with self.assertRaises(PermissionError): self.m.validate(self.journal(["a"]))

    def test_bank_line_cannot_claim_cash_holder(self):
        doc = self.journal(["a"])
        doc.accounts[0].account = "1121"
        with self.assertRaisesRegex(ValueError, "Chỉ chọn"):
            self.m.validate(doc)

    def test_submitted_source_cannot_reassign_or_clear_holder(self):
        old = self.journal(["a"])
        old.docstatus = 1
        for holder in (None, "b"):
            doc = self.journal([holder]); doc.get_doc_before_save = lambda: old
            with self.assertRaisesRegex(ValueError, "Không đổi"):
                self.m.validate(doc)
        old.get_doc_before_save = lambda: old
        self.m.validate(old)

    def test_stamp_changes_only_cash_metadata(self):
        rows = [{"account": "1111", "debit_in_account_currency": 123}, {"account": "1121", "credit_in_account_currency": 123}]
        self.m.stamp_rows(rows, {"1111": "a", "1121": "b"})
        self.assertEqual(rows, [{"account": "1111", "debit_in_account_currency": 123, self.m.HOLDER: "a"},
                                {"account": "1121", "credit_in_account_currency": 123}])

    def test_payment_entry_sides_are_independent(self):
        doc = Doc(doctype="Payment Entry", paid_to="IN", paid_from="OUT", **{self.m.HOLDER: "receiver", self.m.PAYER: "sender"})
        self.assertEqual(self.m._source_holder(doc, "IN"), "receiver")
        self.assertEqual(self.m._source_holder(doc, "OUT"), "sender")
        self.assertIsNone(self.m._source_holder(doc, "OTHER"))

    def test_report_restricted_roles_denied_before_queries(self):
        for roles in (["Accounts Manager", "APH Không xem giá vốn"], ["Accounts Manager", "Kế toán nhà máy"], ["Sales User"]):
            self.f.get_roles.return_value = roles
            with self.assertRaises(PermissionError): self.m.review("APH", "2026-10-01", "2026-10-01")
        self.f.get_doc.assert_not_called()

    def test_report_period_and_company_checked(self):
        with self.assertRaises(ValueError): self.m.review("APH", "2026-10-01", "2026-11-01")
        with self.assertRaises(ValueError): self.m.review({}, "2026-10-01", "2026-10-02")
        self.co.check_permission.side_effect = PermissionError
        with self.assertRaises(PermissionError): self.m.review("VH", "2026-10-01", "2026-10-02")

    def test_report_reads_gl_once_and_hides_unreadable_source(self):
        def line(name, voucher):
            return Doc(name=name, posting_date="2026-10-01", account="1111", voucher_type="Journal Entry", voucher_no=voucher, debit=100, credit=0)
        self.f.get_list = Mock(side_effect=[["1111"], [line("GL1", "JE"), line("GL2", "JE"), line("GL3", "SECRET")]])
        known = self.journal(["a"]); known.has_permission = Mock(return_value=True)
        secret = self.journal(["SECRET USER"]); secret.has_permission = Mock(return_value=False)
        self.f.get_doc.side_effect = lambda dt, name: self.co if dt == "Company" else known if name == "JE" else secret
        data = self.m.review("APH", "2026-10-01", "2026-10-01")
        self.assertEqual([r["holder"] for r in data], ["a", "a", ""])
        self.assertEqual(data[-1]["status"], "Chưa xác minh")
        self.assertEqual(self.f.get_doc.call_count, 3)
        self.assertEqual(self.f.get_list.call_args.kwargs["filters"]["is_cancelled"], 0)
        self.f.db.set_value.assert_not_called()
        self.f.db.commit.assert_not_called()

    def test_report_refuses_silent_truncation(self):
        self.f.get_list = Mock(side_effect=[["1111"], [None] * 5001])
        with self.assertRaisesRegex(ValueError, "5.000"):
            self.m.review("APH", "2026-10-01", "2026-10-01")
