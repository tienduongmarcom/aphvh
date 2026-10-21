"""Hàng đang vận chuyển không trở thành nguồn bán ở các đường chứng từ chuẩn."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get


class TransitSaleBoundary(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.conf = {'kh_aph_kho_chuan': 1}
        self.f.throw = Mock(side_effect=ValueError('Không bán từ kho'))
        self.f.whitelist = lambda *a, **kw: lambda fn: fn
        self.f.get_meta = Mock(return_value=Row(has_field=lambda name: True))
        self.f.get_cached_value = Mock(return_value='Vận chuyển')
        utils = types.ModuleType('frappe.utils')
        utils.cint = lambda value: int(value or 0)
        utils.flt = lambda value: float(value or 0)
        for key in ('get_datetime', 'nowdate', 'nowtime'):
            setattr(utils, key, Mock())
        context = patch.dict(sys.modules, {'frappe': self.f, 'frappe.utils': utils})
        context.start(); self.addCleanup(context.stop)
        path = pathlib.Path(__file__).resolve().parents[1] / 'kho_chuan.py'
        spec = importlib.util.spec_from_file_location('test_transit_kho_chuan', path)
        self.api = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.api)

    def doc(self, dt='Delivery Note', **extra):
        return Row(doctype=dt, items=[Row(idx=1, warehouse='KHO-DANG-DI')], **extra)

    def test_all_stock_sales_paths_block_transit(self):
        for dt in ('Sales Order', 'APH Shared Sales Order', 'Delivery Note', 'Sales Invoice'):
            with self.subTest(doctype=dt), self.assertRaises(ValueError):
                self.api.validate_kho_ban(self.doc(dt, update_stock=1))

    def test_physical_sale_warehouses_remain_usable(self):
        for kind in ('Bán hàng', 'Thành phẩm', 'Nguyên liệu'):
            self.f.get_cached_value.return_value = kind
            self.api.validate_kho_ban(self.doc())
        self.f.throw.assert_not_called()

    def test_return_and_non_stock_invoice_do_not_issue_stock(self):
        self.api.validate_kho_ban(self.doc(is_return=1))
        self.api.validate_kho_ban(self.doc('Sales Invoice', update_stock=0))
        self.f.get_cached_value.assert_not_called()

    def test_disabled_feature_does_not_query_warehouses(self):
        self.f.conf = {}
        self.api.validate_kho_ban(self.doc())
        self.f.get_cached_value.assert_not_called()
