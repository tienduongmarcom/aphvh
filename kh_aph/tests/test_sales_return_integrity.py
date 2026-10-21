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
