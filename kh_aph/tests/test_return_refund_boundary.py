"""Hoàn tiền phải bám hóa đơn đang giữ số dư có, không suy từ tổng hàng trả."""
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
    __setattr__ = dict.__setitem__


class ReturnRefundBoundary(unittest.TestCase):
    def setUp(self):
        f=self.f=types.ModuleType('frappe')
        f.whitelist=lambda *a,**kw:lambda fn:fn
        f.throw=Mock(side_effect=ValueError('Sai khoản hoàn'))
        f.msgprint=Mock();f.has_permission=Mock(return_value=True)
        f.get_meta=lambda dt:Row(has_field=lambda key:True)
        f.get_cached_value=Mock(return_value='QUY')
        f.db=Row(sql=Mock(),set_value=Mock(),get_value=Mock(side_effect=lambda dt,name,field:'Hoàn tiền' if field=='kh_aph_xu_ly_tien' else 'REQUEST'))
        utils=types.ModuleType('frappe.utils')
        utils.cint=lambda x:int(x or 0);utils.flt=lambda x,*a:float(x or 0)
        utils.getdate=Mock();utils.now_datetime=Mock()
        returns=types.ModuleType('kh_aph.sales_return');returns.REQUEST='kh_aph_ma_nhan_tra'
        context=patch.dict(sys.modules,{'frappe':f,'frappe.utils':utils,'kh_aph.sales_return':returns})
        context.start();self.addCleanup(context.stop)
        path=pathlib.Path(__file__).resolve().parents[1]/'sales_p1.py'
        spec=importlib.util.spec_from_file_location('test_return_refund_boundary',path)
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)
        self.api.enabled=lambda:True
        self.original=Row(name='SI-GOC',company='CO',customer='KH',docstatus=1,currency='VND',party_account_currency='VND',
                          outstanding_amount=0,grand_total=962500,debit_to='PHAI-THU',cost_center='CC')
        self.credit=Row(name='SI-GIAM',outstanding_amount=-192500,grand_total=-192500,cost_center='CC')
        self.doc=Row(name='SI-GIAM',company='CO',customer='KH',is_return=1,items=[Row(delivery_note='DN-TRA')],
                     return_against='SI-GOC',update_outstanding_for_self=1,base_grand_total=-192500,base_rounded_total=0,
                     debit_to='PHAI-THU',posting_date='2026-10-21',cost_center='CC')
        self.built=[]
        def get_doc(dt,name=None,**kw):
            if isinstance(dt,dict):
                self.built.append(dt)
                return Row(name='PE-NHAP',flags=Row(),insert=Mock())
            return self.original if name=='SI-GOC' else self.credit
        f.get_doc=Mock(side_effect=get_doc)

    def test_fully_paid_return_references_credit_invoice_not_zero_debt_original(self):
        self.api.sau_ghi_hoa_don_giam(self.doc)
        self.assertEqual(len(self.built),1)
        payment=self.built[0]
        self.assertEqual((payment['payment_type'],payment['paid_amount']),('Pay',192500))
        self.assertEqual(payment['references'][0]['reference_name'],'SI-GIAM')
        self.assertEqual(payment['references'][0]['allocated_amount'],-192500)
        self.f.get_doc.assert_any_call('Sales Invoice','SI-GOC',for_update=True)

    def test_partial_debt_without_journal_authority_keeps_credit_but_no_cash_draft(self):
        self.original.outstanding_amount=96250
        self.f.has_permission.return_value=False
        self.api.sau_ghi_hoa_don_giam(self.doc)
        self.assertEqual(self.built,[])
        self.assertEqual(self.original.outstanding_amount,96250)
        self.assertEqual(self.credit.outstanding_amount,-192500)
        self.f.msgprint.assert_called_once();self.f.db.set_value.assert_not_called()

    def test_unpaid_credit_reduces_debt_without_creating_a_payment(self):
        self.doc.update_outstanding_for_self=0
        self.original.outstanding_amount=577500
        self.api.sau_ghi_hoa_don_giam(self.doc)
        self.assertEqual(self.built,[])
        self.f.has_permission.assert_not_called()

    def test_currency_outside_supported_scope_does_not_create_an_unconverted_refund(self):
        self.original.currency='USD'
        self.api.sau_ghi_hoa_don_giam(self.doc)
        self.assertEqual(self.built,[])
        self.f.msgprint.assert_called_once()

    def test_quality_source_cannot_be_cleared_or_switched_on_existing_draft(self):
        for value in (None,'SI-KHAC'):
            with self.subTest(source=value),self.assertRaises(ValueError):
                self.api.protect_quality_source(Row(**{self.api.F_JE_HD:value,
                    'get_doc_before_save':lambda:Row(**{self.api.F_JE_HD:'SI-GOC'})}))

    def test_amendment_keeps_quality_source_for_final_debt_validation(self):
        self.f.db.get_value=Mock(return_value='SI-GOC')
        doc=Row(amended_from='JE-DA-HUY',get_doc_before_save=lambda:None)
        doc.set=lambda key,value:doc.__setitem__(key,value)
        self.api.protect_quality_source(doc)
        self.assertEqual(doc.get(self.api.F_JE_HD),'SI-GOC')
