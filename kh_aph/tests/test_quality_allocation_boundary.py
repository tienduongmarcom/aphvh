"""Quyền sửa nguồn và tiền bút toán không được tách khỏi phần hàng đã thỏa thuận."""
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
    def set(self,key,value):self[key]=value


class Boundary(unittest.TestCase):
    def setUp(self):
        self.f=types.ModuleType('frappe');self.f.throw=lambda msg,error=ValueError:(_ for _ in ()).throw(error(msg))
        self.f.get_doc=Mock();self.f.db=Row(sql=Mock(return_value=[]));self.f.get_meta=Mock(return_value=Row(has_field=lambda f:True))
        utils=types.ModuleType('frappe.utils');utils.flt=lambda x:float(x or 0)
        p1=types.ModuleType('kh_aph.sales_p1');p1.enabled=lambda:True;p1.F_JE_HD='invoice'
        p1._thue_suat=lambda *a:(10,'VAT')
        self.patch=patch.dict(sys.modules,{'frappe':self.f,'frappe.utils':utils,'kh_aph.sales_p1':p1});self.patch.start();self.addCleanup(self.patch.stop)
        spec=importlib.util.spec_from_file_location('qa_boundary',Path(__file__).resolve().parents[1]/'quality_allocation.py')
        self.q=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.q)
        self.si=Row(name='SI',currency='VND',party_account_currency='VND',precision=lambda k:0,
            items=[Row(name='DONG',uom='Kg',conversion_factor=1,qty=25,net_rate=35000,dn_detail='DN-DONG')])

    def test_exact_quantity_and_vat_allocation(self):
        allocation, chia=self.q.prepare(self.si,[{'invoice_row':'DONG','qty':5,'amount':55000}],55000)
        self.assertEqual(allocation,[{'invoice_row':'DONG','qty':'5','net_discount':'50000.0','tax_discount':'5000.0'}])
        self.assertEqual(chia,[('DONG',50000,5000)])

    def test_no_overlap_with_pending_or_posted_agreement(self):
        self.q.agreements=Mock(return_value=[Row(name='JE',allocation='[{"invoice_row":"DONG","qty":"23"}]')])
        with self.assertRaises(ValueError):self.q.prepare(self.si,[{'invoice_row':'DONG','qty':5,'amount':55000}],55000)

    def test_prior_unclassified_return_cannot_be_silently_assigned_to_normal_goods(self):
        self.q.agreements=Mock(return_value=[]);self.f.db.sql.return_value=[Row(name='TRA')]
        with self.assertRaises(ValueError):self.q.prepare(self.si,[{'invoice_row':'DONG','qty':5,'amount':55000}],55000)

    def test_native_insert_cannot_forge_allocation_but_trusted_insert_can(self):
        doc=Row(**{self.q.ALLOCATION:'[{"invoice_row":"DONG"}]'})
        with self.assertRaises(ValueError):self.q.protect(doc,None)
        doc['insert']=lambda:self.q.protect(doc,None)
        self.q.insert(doc)
        with self.assertRaises(ValueError):self.q.protect(doc,None)

    def test_cannot_clear_or_change_existing_allocation(self):
        old=Row(**{self.q.ALLOCATION:'[{"qty":"5"}]'})
        for raw in ('','[{"qty":"25"}]'):
            with self.assertRaises(ValueError):self.q.protect(Row(**{self.q.ALLOCATION:raw}),old)

    def test_amount_does_not_drift_from_agreed_portion(self):
        doc=Row(name='JE',**{self.q.ALLOCATION:'[{"net_discount":"50000","tax_discount":"5000"}]'})
        with self.assertRaises(ValueError):self.q.guard_credit(doc,56000,self.si)

    def test_cancellation_cannot_orphan_existing_return_partition_even_normal_portion(self):
        self.f.db.sql.return_value=[Row(parts='[{"key":"","qty":"2"}]')]
        doc=Row(name='JE',kh_aph_giam_gia_hd='SI',**{self.q.ALLOCATION:'[{"invoice_row":"DONG"}]'})
        with self.assertRaises(ValueError):self.q.prevent_cancel(doc)

    def test_return_cannot_replace_untouched_price_with_discounted_price(self):
        self.q.parts_for_dn=Mock(return_value={'DONG':[{'key':'','remaining':20,'net_rate':35000}]})
        doc=Row(name='TRA',items=[Row(dn_detail='DONG',qty=-5,net_rate=25000,
            **{self.q.RETURN_PARTS:'[{"key":"","qty":"5"}]'})])
        with self.assertRaises(ValueError):self.q.validate_return(doc,Row())
        doc['items'][0]['net_rate']=35000
        self.assertTrue(self.q.validate_return(doc,Row()))

    def posted(self):
        p1=sys.modules['kh_aph.sales_p1'];p1._so_hieu_la=lambda co:set()
        self.si.update(company='CO',customer='KH',debit_to='REC')
        self.si['items'][0].update(income_account='REV',cost_center='CC')
        allocation=[{'invoice_row':'DONG','qty':'5','net_discount':'50000','tax_discount':'5000'}]
        je=Row(name='JE',company='CO',posting_date='2026-10-01',accounts=[
            Row(account='REV',cost_center='CC',debit_in_account_currency=50000,credit_in_account_currency=0),
            Row(account='VAT',cost_center='CC',debit_in_account_currency=5000,credit_in_account_currency=0),
            Row(account='REC',party_type='Customer',party='KH',reference_type='Sales Invoice',reference_name='SI',
                debit_in_account_currency=0,credit_in_account_currency=55000)],add_comment=Mock())
        return je,allocation

    def test_posted_classification_matches_original_accounts_and_tax(self):
        je,allocation=self.posted()
        self.q.check_posted_debits(je,self.si,allocation)
        je['accounts'][0]['debit_in_account_currency']=55000
        je['accounts'][1]['debit_in_account_currency']=0
        with self.assertRaises(ValueError):self.q.check_posted_debits(je,self.si,allocation)

    def test_different_party_credit_cannot_become_quality_authority(self):
        je,allocation=self.posted();je['accounts'][2]['party']='KHAC'
        with self.assertRaises(ValueError):self.q.check_posted_debits(je,self.si,allocation)

    def test_posted_metadata_is_write_once_with_private_capability(self):
        je,allocation=self.posted()
        # Frappe as_dict chỉ trả ô dữ liệu; mô phỏng đủ ô sổ, không đưa callable vào fingerprint.
        class Account(Row):
            def as_dict(self):return {k:v for k,v in self.items() if k!='as_dict'}
        je['accounts']=[Account(r) for r in je.accounts]
        old=Row(**{self.q.ALLOCATION:''})
        je[self.q.ALLOCATION]=self.q.encode(allocation)
        with self.assertRaises(ValueError):self.q.protect(je,old)
        def save():
            self.q.protect(je,old)
            for row in je.accounts:row['modified']='new audit timestamp'
        je['save']=save
        self.q.save_existing(je,allocation,'Giấy <gốc>')
        self.assertIn('&lt;gốc&gt;',je.add_comment.call_args.args[1])
        with self.assertRaises(ValueError):self.q.protect(je,old)

    def test_posted_metadata_save_never_changes_financial_rows(self):
        class Account(Row):
            def as_dict(self):return dict(self)
        je,allocation=self.posted();je['accounts']=[Account(r) for r in je.accounts]
        je['save']=lambda:je.accounts[0].update(debit_in_account_currency=40000)
        with self.assertRaises(ValueError):self.q.save_existing(je,allocation,'Đối chiếu')
        je.add_comment.assert_not_called()

    def test_retry_compares_quantity_and_gross_amount_not_numeric_spelling(self):
        _,allocation=self.posted()
        self.assertTrue(self.q.same_selection(allocation,[{'invoice_row':'DONG','qty':'5.0','amount':55000}]))
        self.assertFalse(self.q.same_selection(allocation,[{'invoice_row':'DONG','qty':6,'amount':55000}]))
        self.assertFalse(self.q.same_selection(allocation,[{'invoice_row':'DONG','qty':5,'amount':'NaN'}]))

    def test_legacy_records_can_be_classified_one_by_one_but_not_assumed_for_new_discount(self):
        self.q.agreements=Mock(return_value=[Row(name='CU',allocation=None)])
        choices=[{'invoice_row':'DONG','qty':5,'amount':55000}]
        with self.assertRaises(ValueError):self.q.prepare(self.si,choices,55000)
        allocation,_=self.q.prepare(self.si,choices,55000,allow_unclassified=True)
        self.assertEqual(allocation[0]['qty'],'5')

    def test_missing_schema_keeps_legacy_reads_but_never_accepts_new_unstored_allocation(self):
        self.f.get_meta.return_value=Row(has_field=lambda f:False)
        self.assertEqual(self.q.agreements('SI'),[])
        with self.assertRaises(ValueError):self.q.prepare(self.si,[{'invoice_row':'DONG','qty':5,'amount':55000}],55000)
        self.f.db.sql.assert_not_called()

    def test_existing_agreement_permission_is_checked_before_quantity_is_reused(self):
        self.q.agreements=Mock(return_value=[Row(name='KHAC',allocation='[{"invoice_row":"DONG","qty":"2"}]')])
        self.f.get_doc.side_effect=PermissionError('Ngoài phạm vi bút toán')
        with self.assertRaises(PermissionError):self.q.prepare(self.si,[{'invoice_row':'DONG','qty':5,'amount':55000}],55000)

    def test_return_facade_keeps_financial_source_scope_without_granting_journal_access(self):
        self.f.has_permission=Mock(side_effect=lambda dt,*a,**kw:dt=='Delivery Note')
        self.f.session=Row(user='BAN-HANG');self.f.PermissionError=PermissionError
        permissions=types.ModuleType('frappe.permissions');permissions.has_user_permission=Mock(return_value=True)
        source=Row(doctype='Journal Entry',company='CO',check_permission=Mock())
        dn=Row(company='CO',check_permission=Mock())
        with patch.dict(sys.modules,{'frappe.permissions':permissions}):
            self.q._read_return_basis(source,dn)
            source.check_permission.assert_not_called()
            permissions.has_user_permission.assert_called_once_with(source,user='BAN-HANG',ptype='read')
            permissions.has_user_permission.return_value=False
            with self.assertRaises(PermissionError):self.q._read_return_basis(source,dn)
        dn.check_permission.assert_called_with('read')
