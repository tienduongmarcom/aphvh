"""Regression behaviours; Frappe integration must still run on aphvh-uat."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = pathlib.Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class Row(dict):
    def __getattribute__(self, key):
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)
        return super().__getattribute__(key)
    __getattr__ = dict.get
    def __setattr__(self, key, value):
        self[key] = value
    def set(self, key, value):
        self[key] = value


class Rejected(Exception):
    pass


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType("frappe")
        self.frappe.conf = Row(kh_aph_post_receivable_on_delivery=1)
        self.frappe.get_meta = Mock(return_value=Row(has_field=lambda _: True))
        self.frappe.db = Row(sql=Mock())
        self.frappe.get_all = Mock(return_value=[])
        self.frappe.get_doc = Mock()
        self.frappe.throw = Mock(side_effect=Rejected)
        utils = types.ModuleType("frappe.utils")
        utils.cint = lambda x: int(x or 0)
        utils.flt = lambda x: float(x or 0)
        self.si = Row(docstatus=0, update_stock=0)
        def submit():
            self.si.docstatus = 1
        self.si.submit = Mock(side_effect=submit)
        flow = types.ModuleType("kh_aph.sales_flow")
        flow._build_invoice = self.build = Mock(return_value=self.si)
        flow._original_invoices = self.originals = Mock(return_value=["SI-ORIGINAL"])
        self.context = patch.dict(sys.modules, {
            "frappe": self.frappe, "frappe.utils": utils, "kh_aph.sales_flow": flow
        })
        self.context.start()
        self.addCleanup(self.context.stop)
        self.api = module("test_delivery_receivable", "delivery_receivable.py")
        self.doc = Row(name="DN-1", is_return=0, per_billed=0,
                       grand_total=80000, items=[Row(against_sales_invoice=None)])

    def test_opt_in_defaults_off(self):
        self.frappe.conf.clear()
        self.assertFalse(self.api.enabled())

    def test_dispatch_submits_and_never_posts_stock_twice(self):
        self.api.post_receivable(self.doc)
        self.build.assert_called_once_with(self.doc, None)
        self.si.submit.assert_called_once()
        self.assertEqual(self.si.update_stock, 0)

    def test_failure_propagates_to_dispatch_transaction(self):
        self.si.submit.side_effect = RuntimeError("posting failed")
        with self.assertRaisesRegex(RuntimeError, "posting failed"):
            self.api.post_receivable(self.doc)

    def test_partial_prebilling_fails_closed(self):
        self.doc.per_billed = 20
        with self.assertRaises(Rejected):
            self.api.post_receivable(self.doc)
        self.build.assert_not_called()

    def test_existing_draft_is_not_silently_submitted(self):
        self.frappe.get_all.return_value = ["OLD-DRAFT"]
        self.frappe.get_doc.return_value = Row(docstatus=0)
        with self.assertRaises(Rejected):
            self.api.post_receivable(self.doc)
        self.build.assert_not_called()

    def test_repeat_hook_does_not_create_second_invoice(self):
        from kh_aph.constants import SI_AUTO
        self.frappe.get_all.return_value = ["SI-1"]
        self.frappe.get_doc.return_value = Row(
            docstatus=1, grand_total=80000, items=[Row(delivery_note="DN-1")],
            **{SI_AUTO: 1})
        self.api.post_receivable(self.doc)
        self.build.assert_not_called()

    def test_return_links_one_original(self):
        self.doc.is_return = 1
        self.api.post_receivable(self.doc)
        self.build.assert_called_once_with(self.doc, "SI-ORIGINAL")

    def test_ambiguous_return_is_not_posted_unlinked(self):
        self.doc.is_return = 1
        self.originals.return_value = ["SI-A", "SI-B"]
        with self.assertRaises(Rejected):
            self.api.post_receivable(self.doc)
        self.build.assert_not_called()


class TestCostRead(unittest.TestCase):
    def setUp(self):
        self.frappe = types.ModuleType("frappe")
        self.frappe.conf = Row(kh_aph_server_cost_guard=1)
        self.frappe.session = Row(user="restricted@example.invalid")
        self.frappe._ = lambda s: s
        self.frappe.whitelist = lambda *a, **k: lambda fn: fn
        from kh_aph.constants import ROLE_FACTORY
        self.frappe.get_roles = Mock(return_value=[ROLE_FACTORY])
        utils = types.ModuleType("frappe.utils")
        utils.cint = lambda x: int(x or 0)
        self.context = patch.dict(sys.modules, {"frappe": self.frappe, "frappe.utils": utils})
        self.context.start()
        self.addCleanup(self.context.stop)
        self.visibility = module("test_real_visibility", "price_visibility.py")
        self.context2 = patch.dict(sys.modules, {"kh_aph.price_visibility": self.visibility})
        self.context2.start()
        self.addCleanup(self.context2.stop)
        guard = module("test_guard", "server_cost_guard.py")
        class Base(Row):
            def apply_fieldlevel_read_permissions(self):
                self.base_called = True
        self.cls = type("TestDoc", (guard.CostReadGuard, Base), {})
        self.meta = Row(has_field=lambda _: True)

    def doc(self):
        return self.cls(doctype="Stock Entry", meta=self.meta, total_amount=1000000,
                        items=[Row(meta=self.meta, qty=100, basic_rate=10000,
                                   basic_amount=1000000, valuation_rate=10000)],
                        additional_costs=[Row(amount=1000)])

    def test_restricted_reader_gets_quantity_without_cost(self):
        doc = self.doc()
        doc.apply_fieldlevel_read_permissions()
        self.assertTrue(doc.base_called)
        self.assertEqual(doc.items[0].qty, 100)
        self.assertIsNone(doc.items[0].basic_rate)
        self.assertIsNone(doc.items[0].basic_amount)
        self.assertIsNone(doc.total_amount)
        self.assertEqual(doc.additional_costs, [])

    def test_admin_read_is_unchanged(self):
        self.frappe.session.user = "Administrator"
        doc = self.doc()
        doc.apply_fieldlevel_read_permissions()
        self.assertEqual(doc.items[0].basic_rate, 10000)

    def test_disabled_flag_preserves_legacy(self):
        self.frappe.conf.clear()
        doc = self.doc()
        doc.apply_fieldlevel_read_permissions()
        self.assertEqual(doc.items[0].basic_rate, 10000)

    def test_sales_rate_is_preserved_while_cost_hidden(self):
        doc = self.cls(doctype="Sales Order", meta=self.meta,
                       items=[Row(meta=self.meta, rate=20000,
                                  valuation_rate=10000, gross_profit=10000)])
        doc.apply_fieldlevel_read_permissions()
        self.assertEqual(doc.items[0].rate, 20000)
        self.assertIsNone(doc.items[0].valuation_rate)
        self.assertIsNone(doc.items[0].gross_profit)


    def test_explicit_cost_deny_wins_over_privileged_role_union(self):
        from kh_aph.constants import ROLE_FACTORY, ROLE_NO_COST
        for role in ("Accounts User", "Accounts Manager", "Stock Manager", "Sales Manager"):
            self.frappe.get_roles.return_value = [ROLE_FACTORY, ROLE_NO_COST, role]
            doc = self.doc()
            doc.apply_fieldlevel_read_permissions()
            self.assertEqual(doc.items[0].qty, 100)
            self.assertIsNone(doc.items[0].basic_rate)
            self.assertTrue(self.visibility.is_price_restricted())

    def test_response_mask_does_not_mutate_source_transaction(self):
        from kh_aph.constants import ROLE_NO_COST
        self.frappe.get_roles.return_value = [ROLE_NO_COST, "Accounts User"]
        policy = module("test_dung_policy", "dung_cost_policy.py")
        source = {"doctype": "Stock Entry", "items": [{"qty": 2, "basic_rate": 10000}],
                  "additional_costs": [{"amount": 100}], "total_amount": 20000,
                  "helper": {"basic_rate": 10000, "qty": 2}}
        import copy
        response = copy.deepcopy(source)
        policy.mask_response(response)
        self.assertEqual(source["items"][0]["basic_rate"], 10000)
        self.assertEqual(response["items"][0]["qty"], 2)
        self.assertIsNone(response["items"][0]["basic_rate"])
        self.assertEqual(response["additional_costs"], [])
        self.assertIsNone(response["helper"]["basic_rate"])
        self.assertEqual(response["helper"]["qty"], 2)
