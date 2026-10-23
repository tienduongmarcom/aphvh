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
        self.f=types.ModuleType('frappe');self.f.throw=lambda msg:(_ for _ in ()).throw(ValueError(msg))
        self.f.get_doc=Mock();self.f.db=Row(sql=Mock(return_value=[]))
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
