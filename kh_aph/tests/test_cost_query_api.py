import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class TestChildCostQuery(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType("frappe")
        self.f.conf = {"kh_aph_server_cost_guard": 1}
        self.f.whitelist = lambda *a, **k: lambda fn: fn
        def parse(v):
            if not isinstance(v, str): return v
            try: return json.loads(v)
            except ValueError: return v
        self.f.parse_json = parse
        self.f.get_meta = lambda dt: types.SimpleNamespace(get_valid_columns=lambda: ["name","qty","basic_rate"])
        self.f.DataError = ValueError
        def fail(message, exc): raise exc(message)
        self.f.throw = fail
        utils = types.ModuleType("frappe.utils")
        utils.cint = lambda v: int(v or 0)
        model = types.ModuleType("frappe.model")
        self.permissions = Mock(return_value=["name","qty","basic_rate"])
        model.get_permitted_fields = self.permissions
        vis = types.ModuleType("kh_aph.price_visibility")
        vis.COST_MASK = vis.PRINT_MASK = {"Stock Entry":{"tables":{"items":["basic_rate"]}}}
        self.cost = vis.is_cost_restricted = Mock(return_value=False)
        self.price = vis.is_price_restricted = Mock(return_value=False)
        self.context = patch.dict(sys.modules,{"frappe":self.f,"frappe.utils":utils,"frappe.model":model,"kh_aph.price_visibility":vis})
        self.context.start();self.addCleanup(self.context.stop)
        spec=importlib.util.spec_from_file_location("query_candidate",Path(__file__).parents[1]/"cost_query_api.py")
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)

    def test_authorized_child_cost_uses_parent_permissions(self):
        self.assertEqual(self.api._fields("Stock Entry Detail","Stock Entry",'["qty","basic_rate"]'),["qty","basic_rate"])
        self.permissions.assert_called_once_with("Stock Entry Detail",parenttype="Stock Entry",ignore_virtual=True)

    def test_factory_sales_manager_price_mask_is_preserved(self):
        self.price.return_value=True
        self.assertEqual(self.api._fields("Stock Entry Detail","Stock Entry",["qty","basic_rate"]),["qty"])

    def test_cost_restricted_user_cannot_get_cost_with_wildcard(self):
        self.cost.return_value=True
        self.assertEqual(self.api._fields("Stock Entry Detail","Stock Entry",["*"]),["name","qty"])

    def test_single_field_and_native_permissions(self):
        self.assertEqual(self.api._fields("Stock Entry Detail","Stock Entry","basic_rate"),["basic_rate"])
        self.permissions.return_value=["name","qty"]
        self.assertEqual(self.api._fields("Stock Entry Detail","Stock Entry",["qty","basic_rate"]),["qty"])

    def test_unknown_scope_and_expressions_delegate(self):
        self.assertIsNone(self.api._fields("Stock Entry Detail","Sales Order",["basic_rate"]))
        self.assertIsNone(self.api._fields("Stock Entry Detail","Stock Entry",["sum(basic_rate)"]))
        self.f.conf.clear()
        self.assertIsNone(self.api._fields("Stock Entry Detail","Stock Entry",["basic_rate"]))

    def test_nonexistent_field_is_rejected(self):
        with self.assertRaises(ValueError):self.api._fields("Stock Entry Detail","Stock Entry",["unknown_column"])

if __name__=="__main__":unittest.main()
