"""Mất phản hồi không cho phép ghi thu lại hoặc thay nội dung lượt đã ghi."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Doc(dict):
    __getattr__ = dict.get


class CashierRequest(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.session = Doc(user="cashier")
        self.f.flags = Doc()
        self.f.db = Mock()
        self.f.db.sql.return_value = []
        self.f.get_doc = Mock(return_value=Doc(check_permission=Mock()))
        self.f.throw = lambda msg: (_ for _ in ()).throw(ValueError(msg))
        self.c = types.ModuleType("kh_aph.cash_custody")
        self.c.enabled = lambda: True
        import kh_aph
        self.old = getattr(kh_aph, "cash_custody", None)
        kh_aph.cash_custody = self.c
        self.p = patch.dict(sys.modules, {"frappe": self.f, "kh_aph.cash_custody": self.c})
        self.p.start()
        self.addCleanup(self.p.stop)
        self.addCleanup(lambda: setattr(kh_aph, "cash_custody", self.old) if self.old is not None else delattr(kh_aph, "cash_custody"))
        spec = importlib.util.spec_from_file_location("unit_cashier", Path(__file__).resolve().parents[1]/"cashier_request.py")
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.payload = {"company": "APH", "customer": "KH", "amount": "100.00"}

    def test_missing_token_or_scope_does_not_search_payments(self):
        for token in (None, "short", "x"*65, "x"*16+"_"):
            with self.assertRaises(ValueError): self.m.begin(token, self.payload)
        self.f.db.sql.assert_not_called()
        self.f.get_doc.return_value.check_permission.side_effect = ValueError("phạm vi")
        with self.assertRaises(ValueError): self.m.begin("a"*32, self.payload)
        self.f.db.sql.assert_not_called()

    def test_lock_then_replay_exact_submitted_payment(self):
        key, digest, previous = self.m.begin("a"*32, self.payload)
        self.assertIsNone(previous)
        self.assertIn("tabCompany", self.f.db.sql.call_args_list[0].args[0])
        self.f.db.sql.side_effect = [[], [Doc(name="PE1", digest=digest, docstatus=1)]]
        self.assertEqual(self.m.begin("a"*32, self.payload), (key, digest, {"phieu_thu": ["PE1"]}))

    def test_changed_payload_cancelled_or_unreadable_cannot_replay(self):
        _, digest, _ = self.m.begin("a"*32, self.payload)
        for row in (Doc(name="PE", digest="other", docstatus=1), Doc(name="PE", digest=digest, docstatus=2)):
            self.f.db.sql.side_effect = [[], [row]]
            with self.assertRaises(ValueError): self.m.begin("a"*32, self.payload)
        self.f.db.sql.side_effect = [[], [Doc(name="PE", digest=digest, docstatus=1)]]
        self.f.get_doc.side_effect = [Doc(check_permission=Mock()), Doc(check_permission=Mock()),
                                     Doc(check_permission=Mock(side_effect=ValueError("quyền")))]
        with self.assertRaises(ValueError): self.m.begin("a"*32, self.payload)

    def test_metadata_cannot_be_forged_copied_changed_or_deleted(self):
        doc = Doc(get_doc_before_save=lambda: None, **{self.m.KEY: "key", self.m.HASH: "hash"})
        with self.assertRaises(ValueError): self.m.protect(doc)
        self.f.flags = Doc(kh_aph_cashier_request=("key", "hash"))
        self.m.protect(doc)
        old = Doc(doc)
        doc["get_doc_before_save"] = lambda: old
        self.f.flags = Doc()
        self.m.protect(doc)
        with self.assertRaises(ValueError): self.m.protect(doc, "on_trash")
        doc[self.m.HASH] = "changed"
        with self.assertRaises(ValueError): self.m.protect(doc)

    def test_disabled_does_not_touch_schema_or_payments(self):
        self.c.enabled = lambda: False
        self.assertEqual(self.m.begin(None, self.payload), (None, None, None))
        self.f.db.sql.assert_not_called()
