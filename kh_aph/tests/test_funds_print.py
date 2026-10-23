"""Phiếu thu cọc phải bám đúng bút toán gốc; in không tạo chứng từ thu lần hai."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    def __getattribute__(self,key):
        return dict.__getitem__(self,key) if key in self else super().__getattribute__(key)
    __getattr__=dict.get


class FundsPrint(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda fn:fn
        self.f.throw=lambda msg:(_ for _ in ()).throw(ValueError(msg))
        self.f._dict=Row;self.f.render_template=Mock(return_value='PHIẾU THU')
        self.receipt=Row(doctype='APH Funds Receipt',name='R',company='CO',docstatus=1,journal_entry='JE',
            bank_account='CASH',holding_account='HOLD',amount=100,customer='KH',posting_date='2026-10-23',
            owner='KT',reason='Thực nhận',external_reference='GD',check_permission=Mock())
        self.journal=Row(doctype='Journal Entry',name='JE',company='CO',docstatus=1,kh_aph_funds_receipt='R',
            check_permission=Mock(),accounts=[Row(account='CASH',debit_in_account_currency=100,credit_in_account_currency=0),
                Row(account='HOLD',debit_in_account_currency=0,credit_in_account_currency=100)])
        self.account=Row(company='CO',is_group=0,account_currency='VND',check_permission=Mock())
        self.docs={'APH Funds Receipt':self.receipt,'Journal Entry':self.journal,'Account':self.account,
            'Customer':Row(customer_name='Khách',check_permission=Mock()),'Print Format':Row(css='CSS',html='HTML')}
        self.f.get_doc=Mock(side_effect=lambda dt,name:self.docs[dt])
        funds=types.ModuleType('kh_aph.funds');funds.require=Mock();funds.company=Mock()
        prints=types.ModuleType('kh_aph.print_utils');prints.kh_aph_no_co=Mock(return_value={'no':'111','co':'3388'})
        self.guard=funds.require;self.noco=prints.kh_aph_no_co
        context=patch.dict(sys.modules,{'frappe':self.f,'kh_aph.funds':funds,'kh_aph.print_utils':prints})
        context.start();self.addCleanup(context.stop)
        spec=importlib.util.spec_from_file_location('funds_print_test',Path(__file__).resolve().parents[1]/'funds_print.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)

    def test_print_uses_receipt_number_and_original_journal_without_new_payment(self):
        self.assertEqual(self.m.print_receipt('R'),{'html':'PHIẾU THU'})
        context=self.f.render_template.call_args.args[1]
        view=context['doc']
        self.assertEqual((view.doctype,view.name,view.payment_type),('APH Funds Receipt','R','Receive'))
        self.assertEqual((view.paid_to,view.paid_from,view.received_amount),('CASH','HOLD',100))
        self.assertEqual(context['kh_aph_no_co'](view),{'no':'111','co':'3388'})
        self.noco.assert_called_once_with(self.journal)
        self.assertFalse(any(call.args[0]=='Payment Entry' for call in self.f.get_doc.call_args_list))
        self.receipt.check_permission.assert_any_call('read')
        self.receipt.check_permission.assert_any_call('print')

    def test_flag_and_financial_role_gate_precede_source_read(self):
        self.guard.side_effect=PermissionError('không được in')
        with self.assertRaises(PermissionError):self.m.print_receipt('R')
        self.f.get_doc.assert_not_called()

    def test_native_print_permission_is_required(self):
        self.receipt.check_permission.side_effect=PermissionError('ngoài phạm vi')
        with self.assertRaises(PermissionError):self.m.receipt_html(self.receipt)
        self.f.get_doc.assert_not_called()

    def test_wrong_journal_source_or_company_cannot_be_printed(self):
        for key,value in [('kh_aph_funds_receipt','KHAC'),('company','CO2'),('docstatus',2)]:
            old=self.journal[key];self.journal[key]=value
            with self.assertRaises(ValueError):self.m.receipt_html(self.receipt)
            self.journal[key]=old
        self.f.render_template.assert_not_called()

    def test_mismatched_money_or_extra_account_is_not_hidden(self):
        self.journal.accounts[0]['debit_in_account_currency']=99
        with self.assertRaises(ValueError):self.m.receipt_html(self.receipt)
        self.journal.accounts[0]['debit_in_account_currency']=100
        self.journal.accounts.append(Row(account='OTHER',debit_in_account_currency=10,credit_in_account_currency=0))
        with self.assertRaises(ValueError):self.m.receipt_html(self.receipt)
        self.f.render_template.assert_not_called()

    def test_foreign_currency_and_nonpositive_or_draft_receipts_are_blocked(self):
        self.account['account_currency']='USD'
        with self.assertRaises(ValueError):self.m.receipt_html(self.receipt)
        self.account['account_currency']='VND'
        self.receipt['docstatus']=0
        with self.assertRaises(ValueError):self.m.receipt_html(self.receipt)
        self.receipt['docstatus']=1;self.receipt['amount']=0
        with self.assertRaises(ValueError):self.m.receipt_html(self.receipt)
