"""Không xóa dấu yêu cầu hoặc tăng giá dòng trả để đi vòng kiểm lượng/giá trị."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    def __getattribute__(self,key):
        if dict.__contains__(self,key):return dict.__getitem__(self,key)
        return super().__getattribute__(key)
    __getattr__=dict.get


class ReturnIntegrity(unittest.TestCase):
    def setUp(self):
        f=self.f=types.ModuleType('frappe')
        f.conf={'kh_aph_sales_adjust':1,'kh_aph_sales_p1':1}
        f.whitelist=lambda *a,**kw:lambda fn:fn
        f.throw=Mock(side_effect=ValueError('Dòng trả không hợp lệ'))
        utils=types.ModuleType('frappe.utils');utils.cint=lambda x:int(x or 0);utils.flt=lambda x,*a:float(x or 0)
        closing=types.ModuleType('kh_aph.cash_closing');closing.lock_ledger=Mock()
        self.closing=closing
        p1=types.ModuleType('kh_aph.sales_p1');p1.F_JE_HD='kh_aph_giam_gia_hd'
        context=patch.dict(sys.modules,{'frappe':f,'frappe.utils':utils,'kh_aph.cash_closing':closing,'kh_aph.sales_p1':p1})
        context.start();self.addCleanup(context.stop)
        path=pathlib.Path(__file__).resolve().parents[1]/'sales_return.py'
        spec=importlib.util.spec_from_file_location('test_return_integrity',path)
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
        self.cheap=Row(name='DONG-RE',item_code='HANG',qty=25,kh_aph_bags=1,uom='Kg',conversion_factor=1,net_rate=20)
        self.source=Row(name='DN-GOC',company='CO',customer='KH',items=[self.cheap,Row(name='DONG-DAT',item_code='HANG',net_rate=50)])
        self.api._source=Mock(return_value=self.source);self.api._reserved=Mock(return_value=[])

    def doc(self,rate=20):
        return Row(name='DN-TRA',doctype='Delivery Note',is_return=1,return_against='DN-GOC',company='CO',customer='KH',
            items=[Row(dn_detail='DONG-RE',item_code='HANG',qty=-5,kh_aph_bags=0,uom='Kg',conversion_factor=1,net_rate=rate)],
            **{self.api.REQUEST:'TOKEN',self.api.SIGNATURE:'HASH',
               'get_doc_before_save':lambda:Row(**{self.api.REQUEST:'TOKEN',self.api.SIGNATURE:'HASH'})})

    def test_repeated_item_with_a_higher_price_on_another_source_row_is_not_a_refund_limit(self):
        with self.assertRaises(ValueError):self.api.validate(self.doc(50))
        self.api.validate(self.doc(20));self.api.validate(self.doc(10))

    def test_cannot_move_return_to_another_order_or_invoice_line(self):
        self.cheap.update(against_sales_order='SO-GOC', so_detail='SO-DONG-GOC',
                          against_sales_invoice='SI-GOC', si_detail='SI-DONG-GOC')
        original = {key: self.cheap[key] for key in ('against_sales_order', 'so_detail', 'against_sales_invoice')}
        doc = self.doc(); doc['items'][0].update(original)
        self.api.validate(doc)
        for field in original:
            bad = self.doc(); bad['items'][0].update(original); bad['items'][0][field] = 'KHAC'
            with self.subTest(field=field), self.assertRaises(ValueError): self.api.validate(bad)

    def test_request_and_signature_cannot_be_cleared_or_replaced(self):
        for key,value in [(self.api.REQUEST,None),(self.api.REQUEST,'KHAC'),(self.api.SIGNATURE,'KHAC')]:
            with self.subTest(field=key),self.assertRaises(ValueError):
                doc=self.doc();doc[key]=value;self.api.validate(doc)
        self.api._source.assert_not_called()

    def test_negative_return_unit_price_is_not_a_discount_authority(self):
        with self.assertRaises(ValueError):self.api.validate(self.doc(-1))

    def test_old_quality_discount_on_multiple_lines_needs_line_allocation_before_return(self):
        self.f.get_doc=Mock(return_value=Row(name='SI',company='CO',customer='KH',docstatus=1,currency='VND',
            party_account_currency='VND',debit_to='REC',grand_total=1000,items=[Row(),Row()]))
        self.f.db=Row(sql=Mock(side_effect=[[],[],[Row(credit_in_account_currency=100,debit_in_account_currency=0)]]))
        doc=self.doc();doc['grand_total']=-100
        with self.assertRaises(ValueError):self.api.validate_credit_limit(doc,'SI')
        self.closing.lock_ledger.assert_called_once_with(doc)

    def test_partial_quantity_after_quality_discount_also_requires_explicit_allocation(self):
        self.f.get_doc=Mock(return_value=Row(name='SI',company='CO',customer='KH',docstatus=1,currency='VND',
            party_account_currency='VND',debit_to='REC',grand_total=1000,items=[Row(qty=25)]))
        self.f.db=Row(sql=Mock(side_effect=[[],[],[Row(credit_in_account_currency=100,debit_in_account_currency=0)]]))
        doc=self.doc();doc['grand_total']=-100
        with self.assertRaises(ValueError):self.api.validate_credit_limit(doc,'SI')

    def money_docs(self, **payment_values):
        note = Row(docstatus=1, is_return=1, company='CO', customer='KH', check_permission=Mock(),
            kh_aph_ma_nhan_tra='REQUEST', kh_aph_xu_ly_tien='Hoàn tiền', kh_aph_chung_tu_xu_ly='PE')
        payment = Row(name='PE', company='CO', party_type='Customer', party='KH', payment_type='Pay', docstatus=0,
                      check_permission=Mock())
        payment.update(payment_values)
        self.f.get_doc = Mock(side_effect=[note, payment])
        return note, payment

    def test_open_refund_is_read_only_and_checks_both_documents(self):
        note, payment = self.money_docs()
        self.assertEqual(self.api.money_document('DN-TRA'), {'doctype': 'Payment Entry', 'name': 'PE', 'docstatus': 0})
        note.check_permission.assert_called_once_with('read'); payment.check_permission.assert_called_once_with('read')

    def test_open_refund_rejects_wrong_company_customer_direction_or_cancelled_payment(self):
        for change in ({'company': 'CO2'}, {'party': 'KH2'}, {'payment_type': 'Receive'}, {'docstatus': 2}):
            self.money_docs(**change)
            with self.subTest(change=change), self.assertRaises(ValueError): self.api.money_document('DN-TRA')

    def test_open_refund_cannot_bypass_payment_read_permission(self):
        _, payment = self.money_docs()
        payment.check_permission.side_effect = PermissionError('Không đọc được phiếu tiền')
        with self.assertRaises(PermissionError): self.api.money_document('DN-TRA')
