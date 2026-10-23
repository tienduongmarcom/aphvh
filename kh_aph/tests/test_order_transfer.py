"""Gom theo đơn chỉ cung cấp nhu cầu còn lại trong đúng phạm vi, không giữ tồn/ghi sổ."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class OrderTransfer(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe')
        self.f.conf={'kh_aph_shared_sales_order':1}
        self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.PermissionError=PermissionError
        self.f.throw=lambda msg,error=ValueError:(_ for _ in ()).throw(error(msg))
        self.f.has_permission=Mock(return_value=True)
        self.f.db=Mock()
        self.transfer=types.ModuleType('kh_aph.factory_transfer')
        self.transfer.guard=Mock();self.transfer._destination=Mock();self.transfer.send=Mock()
        self.ban=types.ModuleType('kh_aph.ban_nhanh')
        self.ban._order=Mock(return_value=types.SimpleNamespace(name='CHUNG'))
        self.ban._rows=Mock(return_value=[])
        utils=types.ModuleType('frappe.utils');utils.cint=lambda value:int(value or 0)
        self.context=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils,
            'kh_aph.factory_transfer':self.transfer,'kh_aph.ban_nhanh':self.ban})
        self.context.start();self.addCleanup(self.context.stop)
        # Module cha có thể giữ bản đã import từ test khác: cô lập đúng hai dependency.
        import kh_aph
        self.parent=patch.multiple(kh_aph,factory_transfer=self.transfer,ban_nhanh=self.ban,create=True)
        self.parent.start();self.addCleanup(self.parent.stop)
        spec=importlib.util.spec_from_file_location('order_transfer_test',Path(__file__).resolve().parents[1]/'order_transfer.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)

    def row(self,**changes):
        return dict({'company':'CO','warehouse':'CUA-HANG','item_code':'A','item_name':'Hàng A',
            'remaining_qty':25,'kg_per_bag':25},**changes)

    def test_permission_or_disabled_stops_before_order_read(self):
        self.f.has_permission.return_value=False
        with self.assertRaises(PermissionError):self.m.preview('CHUNG')
        self.f.has_permission.return_value=True;self.f.conf['kh_aph_shared_sales_order']=0
        with self.assertRaises(ValueError):self.m.preview('CHUNG')
        self.ban._order.assert_not_called()

    def test_stock_guard_and_order_scope_cannot_be_skipped(self):
        self.transfer.guard.side_effect=PermissionError('kho')
        with self.assertRaises(PermissionError):self.m.preview('CHUNG')
        self.ban._order.assert_not_called()
        self.transfer.guard.side_effect=None
        self.ban._order.side_effect=PermissionError('đơn')
        with self.assertRaises(PermissionError):self.m.preview('CHUNG')
        self.ban._rows.assert_not_called()

    def test_same_item_combines_only_in_same_company_and_destination(self):
        self.ban._rows.return_value=[self.row(),self.row(remaining_qty=25),self.row(company='CO2'),
            self.row(warehouse='CUA-HANG2'),self.row(remaining_qty=0)]
        result=self.m.preview('CHUNG')
        self.assertEqual(len(result['groups']),3)
        group=next(g for g in result['groups'] if g['company']=='CO' and g['destination']=='CUA-HANG')
        self.assertEqual(group['items'][0]['qty'],50)
        self.assertEqual(group['items'][0]['bags'],2)
        self.assertNotIn('rate',group['items'][0])
        self.transfer.send.assert_not_called();self.f.db.assert_not_called()

    def test_partial_bag_does_not_invent_whole_bags_or_round_kg(self):
        self.ban._rows.return_value=[self.row(remaining_qty=5)]
        item=self.m.preview('CHUNG')['groups'][0]['items'][0]
        self.assertEqual((item['qty'],item['bags']),(5,0))

    def test_target_warehouse_permissions_are_checked(self):
        self.ban._rows.return_value=[self.row()]
        self.transfer._destination.side_effect=PermissionError('ngoài kho')
        with self.assertRaises(PermissionError):self.m.preview('CHUNG')
        self.transfer._destination.assert_called_once_with('CUA-HANG','CO',None)

    def test_conflicting_weight_requires_source_review(self):
        self.ban._rows.return_value=[self.row(),self.row(kg_per_bag=20)]
        with self.assertRaises(ValueError):self.m.preview('CHUNG')

    def test_large_demand_is_not_silently_truncated(self):
        self.ban._rows.return_value=[self.row(item_code=str(i)) for i in range(101)]
        with self.assertRaises(ValueError):self.m.preview('CHUNG')
