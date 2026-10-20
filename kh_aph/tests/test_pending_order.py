"""Giữ chỗ phải áp cả lối nhập chuẩn và khi tắt cờ giao diện."""
import importlib
import sys
import unittest
from unittest.mock import Mock
from decimal import Decimal
from kh_aph.tests import test_factory_receiving as fixture


class Row(fixture.Row):
    def __getattribute__(self, name):
        if name in self:
            return self[name]
        return super().__getattribute__(name)


class PendingOrder(unittest.TestCase):
    def setUp(self):
        fixture.Receiving.setUp(self)
        self.receiving = self.m
        import kh_aph.pending_order as module
        self.m = importlib.reload(module)
        self.f.db.has_column.return_value = True

    def tearDown(self):
        fixture.Receiving.tearDown(self)

    def test_reservation_uses_current_rows_and_excludes_only_own_pending(self):
        self.f.db.sql.return_value = [('P1','R',4),('P2','R',2),('P3','X',1)]
        self.assertEqual(self.m.reserved('PO','P1',True),{'R':Decimal(2),'X':Decimal(1)})
        query,args = self.f.db.sql.call_args.args
        self.assertIn('r.docstatus!=1',query)
        self.assertIn('FOR UPDATE',query)
        self.assertEqual(args,'PO')
        self.f.conf['kh_aph_factory_receiving']=0
        self.assertEqual(self.m.reserved('PO')['R'],6)

    def test_missing_schema_does_not_query_custom_columns(self):
        self.f.db.has_column.return_value=False
        self.assertEqual(self.m.reserved('PO'),{})
        self.f.db.sql.assert_not_called()

    def test_lock_order_company_then_sorted_orders_and_scope(self):
        self.f.get_doc.side_effect=lambda dt,name,**kwargs:Row(company='APH',check_permission=Mock())
        self.m.lock_orders('APH',['B','A','B'])
        self.assertIn('tabCompany',self.f.db.sql.call_args.args[0])
        self.assertEqual([x.args[1] for x in self.f.get_doc.call_args_list],['A','B'])
        self.f.get_doc.return_value=Row(company='VH',check_permission=Mock());self.f.get_doc.side_effect=None
        with self.assertRaises(ValueError):self.m.lock_orders('APH',['A'])

    def source(self):
        return Row(name='PO',company='APH',supplier='S',docstatus=1,status='To Receive',items=[
            Row(name='R',item_code='A',qty=10,received_qty=2,conversion_factor=1,uom='Kg')])

    def test_native_pr_and_stock_pi_cannot_take_reserved_quantity_flag_off(self):
        self.f.conf['kh_aph_factory_receiving']=0
        self.m.lock_orders=Mock(return_value={'PO':self.source()})
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        for dt,key in [('Purchase Receipt','purchase_order_item'),('Purchase Invoice','po_detail')]:
            row=Row(purchase_order='PO',received_qty=5,qty=5,conversion_factor=1,**{key:'R'})
            doc=Row(doctype=dt,update_stock=1,items=[row])
            with self.assertRaises(ValueError):self.m.native_receipt(doc)
            row.qty=row.received_qty=4
            self.m.native_receipt(doc)

    def test_native_duplicate_source_rows_are_summed_not_checked_separately(self):
        self.m.lock_orders=Mock(return_value={'PO':self.source()})
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        row=Row(purchase_order='PO',purchase_order_item='R',qty=3,received_qty=3,conversion_factor=1)
        with self.assertRaises(ValueError):self.m.native_receipt(Row(doctype='Purchase Receipt',items=[row,row]))

    def test_client_link_cannot_exempt_reservation(self):
        self.m.lock_orders=Mock(return_value={'PO':self.source()})
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        row=Row(purchase_order='PO',purchase_order_item='R',qty=5,received_qty=5,conversion_factor=1)
        doc=Row(doctype='Purchase Receipt',items=[row],kh_aph_pending_receipt='P1')
        with self.assertRaises(ValueError):self.m.native_receipt(doc)
        self.m.reserved.assert_called_with('PO',exclude=None,lock=True)

    def test_pending_submit_rechecks_source_and_remaining(self):
        self.m.lock_orders=Mock(return_value={'PO':self.source()})
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        self.receiving._item=Mock();self.receiving._warehouse=Mock()
        row=Row(item_code='A',warehouse='WH',qty=5,kh_aph_receiving_source_row='R')
        doc=Row(name='P',company='APH',supplier='S',items=[row],kh_aph_receiving_purchase_order='PO')
        with self.assertRaises(ValueError):self.m.pending_transition(doc)
        row.qty=4;self.m.pending_transition(doc)
        self.receiving._item.assert_called_with(self.source().items[0],require_price=False)
        row.item_code='forged'
        with self.assertRaises(ValueError):self.m.pending_transition(doc)

    def test_order_reduction_or_cancel_cannot_discard_pending(self):
        source=self.source();source.items[0].qty=5
        self.m.lock_orders=Mock(return_value={'PO':source})
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        self.f.db.sql.return_value=[('A',)]
        with self.assertRaises(ValueError):self.m.protect_order(source,'before_update_after_submit')
        source.items[0].qty=6;self.m.protect_order(source,'before_update_after_submit')
        with self.assertRaises(ValueError):self.m.protect_order(source,'before_cancel')

    def test_pending_source_cannot_be_erased_after_receipt(self):
        self.receiving.protect=Mock()
        old=Row(kh_aph_receiving_purchase_order='PO')
        doc=Row(kh_aph_receiving_purchase_order='',items=[],get_doc_before_save=lambda:old)
        with self.assertRaises(ValueError):self.m.validate_pending(doc)

    def test_cancel_backlinks_exempt_only_exact_pending_source(self):
        import types
        from unittest.mock import patch
        module=types.ModuleType('frappe.model.delete_doc')
        module.get_linked_docs=Mock(return_value=[{'reference_doctype':'APH Pending Receipt','reference_docname':'P'}])
        module.get_dynamic_linked_docs=Mock(return_value=[])
        module.raise_link_exists_exception=lambda *args: (_ for _ in ()).throw(ValueError('còn liên kết khác'))
        doc=Row(docstatus=2,name='PR',kh_aph_pending_receipt='P',kh_aph_receiving_request='key')
        self.m.cancelled_source=Mock(return_value=Row(name='P'))
        with patch.dict(sys.modules,{'frappe.model.delete_doc':module}):
            self.m.PendingReceiptLinks.check_no_back_links_exist(doc)
            module.get_dynamic_linked_docs.return_value=[{'reference_doctype':'Purchase Invoice','reference_docname':'PI'}]
            with self.assertRaisesRegex(ValueError,'còn liên kết khác'):
                self.m.PendingReceiptLinks.check_no_back_links_exist(doc)

    def test_cancel_source_requires_exact_server_stamp_and_write_permission(self):
        pending=Row(name='P',docstatus=1,purchase_receipt='PR',kh_aph_receiving_purchase_order='PO',
            kh_aph_receiving_request='key',kh_aph_receiving_payload='payload',check_permission=Mock())
        self.f.get_doc.return_value=pending
        doc=Row(name='PR',kh_aph_pending_receipt='P',kh_aph_receiving_request='key',kh_aph_receiving_payload='payload')
        self.assertIs(self.m.cancelled_source(doc),pending)
        pending.check_permission.assert_any_call('write')
        pending.kh_aph_receiving_payload='forged'
        with self.assertRaises(ValueError):self.m.cancelled_source(doc)

    def test_finalizing_capability_does_not_exempt_unlinked_native_receipt(self):
        self.m.lock_orders=Mock(return_value={'PO':self.source()})
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        row=Row(purchase_order='PO',purchase_order_item='R',qty=5,received_qty=5,conversion_factor=1)
        doc=Row(doctype='Purchase Receipt',items=[row])
        token=self.m.FINALIZING.set('P1')
        try:
            with self.assertRaises(ValueError):self.m.native_receipt(doc)
            self.m.reserved.assert_called_with('PO',exclude=None,lock=True)
        finally:self.m.FINALIZING.reset(token)

    def test_pending_mode_preview_accepts_unpriced_source_and_deducts_hold(self):
        self.receiving.guard=Mock()
        source=self.source();source.items[0].rate=0
        source.items[0].warehouse='WH'
        self.receiving._source=Mock(return_value=source)
        self.receiving._item=Mock(return_value=Row(kh_aph_kg_per_bag=0))
        self.receiving._warehouse=Mock()
        self.m.reserved=Mock(return_value={'R':Decimal(4)})
        result=self.receiving.preview('PO',mode='pending')
        self.assertEqual(result['items'][0]['remaining'],4)
        self.receiving._item.assert_called_once_with(source.items[0],require_price=False)
        self.assertNotIn('"rate"',__import__('json').dumps(result))
