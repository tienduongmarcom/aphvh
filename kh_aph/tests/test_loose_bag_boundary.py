"""Trả lẻ không trở thành lối tắt sửa số kg hoặc giả dòng nguồn trên chứng từ chuẩn."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    def __getattribute__(self, key):
        if dict.__contains__(self, key): return dict.__getitem__(self, key)
        return super().__getattribute__(key)
    __getattr__ = dict.get
    def __setattr__(self, key, value): self[key] = value


class LooseBagBoundary(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.conf = {'kh_aph_quantity_valuation_mvp': 1}
        self.f.throw = lambda message, *a, **kw: (_ for _ in ()).throw(ValueError(message))
        self.f.get_cached_doc = Mock(return_value=Row(kh_aph_kg_per_bag=25, stock_uom='Kg'))
        self.original = Row(parent='DN-GOC', item_code='HANG', qty=25, kh_aph_bags=1, kh_aph_kg_per_bag=25)
        self.f.db = Row(exists=Mock(return_value=False), get_value=Mock(return_value=self.original))
        utils = types.ModuleType('frappe.utils'); utils.cint = lambda x: int(x or 0); utils.flt = lambda x: float(x or 0)
        returns = types.ModuleType('kh_aph.sales_return'); returns.enabled = lambda: True
        self.context = patch.dict(sys.modules, {'frappe': self.f, 'frappe.utils': utils, 'kh_aph.sales_return': returns})
        self.context.start(); self.addCleanup(self.context.stop)
        path = pathlib.Path(__file__).resolve().parents[1] / 'bag_stock.py'
        spec = importlib.util.spec_from_file_location('test_loose_bag_stock', path)
        self.api = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.api)

    def doc(self, **changes):
        row = Row(item_code='HANG', name=None, doctype='Delivery Note Item', qty=-5, kh_aph_bags=0,
                  kh_aph_kg_per_bag=25, kh_aph_tra_le_kg=1, uom='Kg', conversion_factor=1, dn_detail='DONG-GOC', **changes)
        return Row(doctype='Delivery Note', is_return=1, return_against='DN-GOC', items=[row])

    def test_five_kg_without_a_bag_stays_five_kg(self):
        doc = self.doc(); self.api.validate(doc)
        self.assertEqual((doc['items'][0].qty, doc['items'][0].kh_aph_bags), (-5, 0))
        self.assertEqual(doc['items'][0].kh_aph_bag_rate, 0)

    def test_source_parent_and_item_are_not_trusted_from_client(self):
        for source in [Row(**{**self.original, 'parent': 'KHAC'}), Row(**{**self.original, 'item_code': 'KHAC'})]:
            self.f.db.get_value.return_value = source
            with self.assertRaises(ValueError): self.api.validate(self.doc())

    def test_manual_normal_issue_cannot_use_loose_return(self):
        doc = self.doc(); doc.is_return = 0
        with self.assertRaises(ValueError): self.api.validate(doc)

    def test_original_package_snapshot_wins_over_current_item_weight(self):
        self.f.get_cached_doc.return_value.kh_aph_kg_per_bag = 50
        doc = self.doc(); self.api.validate(doc)
        self.assertEqual(doc['items'][0].kh_aph_kg_per_bag, 25)

    def test_bag_ledger_records_kg_without_fabricating_fractional_bags(self):
        doc = self.doc(); doc['items'][0].warehouse = 'KHO-CACH-LY'; doc['items'][0].stock_qty = -5
        moves = self.api._moves(doc)
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0][2], 0)
