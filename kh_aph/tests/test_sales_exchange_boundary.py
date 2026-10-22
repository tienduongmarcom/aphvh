"""Nguồn đổi hàng bất biến, không cấn chéo đơn vị hoặc mở hai đơn thay còn hiệu lực."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get
    def set(self, key, value): self[key] = value
    def get_doc_before_save(self): return self.get('_old')


class SalesExchangeBoundary(unittest.TestCase):
    def setUp(self):
        f = self.f = types.ModuleType('frappe')
        f.throw = Mock(side_effect=ValueError('Nguồn đổi hàng không hợp lệ'))
        f.whitelist = lambda *a, **kw: lambda fn: fn
        f.PermissionError = PermissionError
        f.has_permission = Mock(return_value=True)
        self.wh = Row(company='CONG-TY-1', check_permission=Mock())
        f.get_doc = Mock(return_value=self.wh)
        utils = types.ModuleType('frappe.utils'); utils.cint = lambda x: int(x or 0); utils.nowdate = lambda: '2026-10-21'
        returns = types.ModuleType('kh_aph.sales_return'); returns.REQUEST = 'kh_aph_ma_nhan_tra'; returns.enabled = lambda: True
        context = patch.dict(sys.modules, {'frappe': f, 'frappe.utils': utils, 'kh_aph.sales_return': returns})
        context.start(); self.addCleanup(context.stop)
        path = pathlib.Path(__file__).resolve().parents[1] / 'sales_exchange.py'
        spec = importlib.util.spec_from_file_location('test_exchange_boundary', path)
        self.api = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.api)
        self.api._return = Mock(return_value=Row(name='TRA-1', customer='KH-1', company='CONG-TY-1'))
        self.api._active = Mock(return_value=None)

    def doc(self, **extra):
        return Row(**{'name': 'DON-DOI', 'customer': 'KH-1', 'items': [Row(warehouse='KHO-1')],
                      self.api.SOURCE: 'TRA-1', self.api.ACTIVE: 'GIA-1', **extra})

    def test_active_key_is_derived_and_warehouse_permissions_checked(self):
        doc = self.doc(); self.api.validate(doc)
        self.assertEqual(doc.get(self.api.ACTIVE), 'TRA-1')
        self.wh.check_permission.assert_called_with('read')
        self.api._return.assert_called_with('TRA-1', lock=True)

    def test_customer_company_and_old_source_cannot_be_changed_or_removed(self):
        with self.assertRaises(ValueError): self.api.validate(self.doc(customer='KH-KHAC'))
        self.wh.company = 'CONG-TY-KHAC'
        with self.assertRaises(ValueError): self.api.validate(self.doc())
        for changed in ('TRA-KHAC', None):
            with self.subTest(source=changed), self.assertRaises(ValueError):
                self.api.validate(self.doc(**{self.api.SOURCE: changed, '_old': Row(**{self.api.SOURCE: 'TRA-1'})}))

    def test_an_existing_active_order_blocks_another_native_insert(self):
        self.api._active.return_value = 'DON-KHAC'
        with self.assertRaises(ValueError): self.api.validate(self.doc())

    def test_cancel_preserves_source_but_releases_active_key(self):
        doc = self.doc(); doc['_old'] = Row(**{self.api.SOURCE: 'TRA-1'})
        self.api.before_cancel(doc)
        self.assertEqual(doc.get(self.api.SOURCE), 'TRA-1')
        self.assertIsNone(doc.get(self.api.ACTIVE))
        doc[self.api.SOURCE] = None
        with self.assertRaises(ValueError): self.api.before_cancel(doc)

    def test_ordinary_order_cannot_reserve_a_forged_exchange_key(self):
        doc = self.doc(**{self.api.SOURCE: None})
        self.api.validate(doc)
        self.assertIsNone(doc.get(self.api.ACTIVE)); self.api._return.assert_not_called()

    def test_reopen_checks_read_permission_and_does_not_create_another_order(self):
        self.api._active.return_value = 'DON-CU'
        self.assertEqual(self.api.prepare('TRA-1'), {'existing': 'DON-CU'})
        self.f.get_doc.assert_called_with('APH Shared Sales Order', 'DON-CU')
        self.wh.check_permission.assert_called_with('read')

    def test_source_change_cannot_cross_company_for_replacement_order(self):
        shared = Row(**{self.api.SOURCE: 'TRA-1', 'check_permission': Mock()})
        self.f.get_doc.return_value = shared
        with self.assertRaises(ValueError):
            self.api.validate_source_change(Row(shared_order='DON-DOI', target_company='CONG-TY-KHAC'))
        self.api.validate_source_change(Row(shared_order='DON-DOI', target_company='CONG-TY-1'))
