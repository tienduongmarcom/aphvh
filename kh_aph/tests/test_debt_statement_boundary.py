"""Không tạo/sửa snapshot bằng form giả, không đọc bộ giấy vượt Company hoặc hồ sơ ẩn vốn."""
import hashlib
import importlib.util
import json
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


class StatementBoundary(unittest.TestCase):
    def setUp(self):
        f=self.f=types.ModuleType('frappe')
        f.conf={'kh_aph_quan_tri':1}; f.session=Row(user='account@example.invalid')
        f.get_roles=Mock(return_value=['Accounts Manager'])
        f.get_meta=Mock(return_value=Row(fields=[]))
        f.get_all=Mock(return_value=[]); f.whitelist=lambda *a,**kw:lambda fn:fn
        f.PermissionError=PermissionError; f.TimestampMismatchError=ValueError
        f.throw=lambda message,exc=ValueError:(_ for _ in ()).throw(exc(message))
        f.parse_json=lambda value:json.loads(value) if isinstance(value,str) else value
        f.db=Row(sql=Mock(), get_value=Mock(return_value=None))
        f.get_doc=Mock(side_effect=lambda dt,name:Row(name=name,check_permission=Mock()))
        f.has_permission=Mock(return_value=True)
        utils=types.ModuleType('frappe.utils');utils.cint=lambda v:int(v or 0)
        utils.getdate=Mock();utils.now_datetime=Mock();utils.today=Mock()
        permissions=types.ModuleType('frappe.permissions');permissions.get_user_permissions=Mock(return_value={})
        self.permissions=permissions
        document=types.ModuleType('frappe.model.document');document.Document=type('Document',(),{})
        context=patch.dict(sys.modules,{'frappe':f,'frappe.utils':utils,'frappe.permissions':permissions,
                                       'frappe.model.document':document})
        context.start();self.addCleanup(context.stop)
        spec=importlib.util.spec_from_file_location('test_statement_boundary',pathlib.Path(__file__).resolve().parents[1]/'debt_statement.py')
        self.api=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.api)

    def test_direct_document_insert_or_edit_cannot_forge_snapshot(self):
        doc=self.api.Statement()
        with self.assertRaises(PermissionError):doc.validate()
        token=self.api._INTERNAL.set(id(doc))
        try:doc.validate()
        finally:self.api._INTERNAL.reset(token)

    def test_no_cost_role_stays_denied_even_with_accounts_manager(self):
        self.f.get_roles.return_value=['Accounts Manager','APH Không xem giá vốn']
        self.assertFalse(self.api.has_permission())
        self.assertEqual(self.api.query_conditions(),'1=0')
        with self.assertRaises(PermissionError):self.api._guard()

    def test_financial_dimension_restrictions_cannot_read_whole_customer_snapshot(self):
        self.permissions.get_user_permissions.return_value={'Cost Center':[{'doc':'CC1'}]}
        self.assertFalse(self.api.has_permission())
        with self.assertRaises(PermissionError):self.api._guard()

    def test_multi_company_document_requires_all_company_permissions(self):
        self.f.has_permission.side_effect=lambda dt,kind,doc,user:doc.name!='CO2'
        doc=Row(customer='KH',scope=json.dumps(['CO1','CO2']),is_new=lambda:False)
        self.assertFalse(self.api.has_permission(doc))
        doc['scope']=json.dumps(['CO1'])
        self.assertTrue(self.api.has_permission(doc))

    def test_request_keys_reject_other_doctypes_and_untyped_names(self):
        for rows in [[{'doctype':'File','name':'SECRET'}],[{'doctype':'Sales Invoice','name':{}}],[]]:
            with self.subTest(rows=rows),self.assertRaises(ValueError):self.api._source_keys(rows)

    def test_same_request_opens_frozen_copy_without_rechecking_cancelled_source(self):
        self.api._scope=Mock(return_value=(Row(),['CO']))
        self.api._sources=Mock(side_effect=AssertionError('Không đọc lại nguồn đã hủy khi mở bản cũ'))
        keys=[('Payment Entry','PE')]
        signature=hashlib.sha256(json.dumps(['KH',['CO'],keys,''],sort_keys=True).encode()).hexdigest()
        self.f.db.get_value.return_value=Row(name='BB',request_hash=signature)
        doc=Row(name='BB',bundle_file='/private/files/BB.pdf',check_permission=Mock())
        self.f.get_doc=Mock(return_value=doc)
        result=self.api.create('KH',['CO'],[{'doctype':'Payment Entry','name':'PE'}],'request-1234567890')
        self.assertTrue(result['reused']); self.assertEqual(result['name'],'BB')
        self.api._sources.assert_not_called();doc.check_permission.assert_called_once_with('read')

    def test_existing_pdf_and_signature_files_cannot_be_made_public_or_relinked(self):
        self.api.file_in_use=Mock(return_value=True)
        old=Row(file_url='/private/files/BB.pdf',is_private=1,attached_to_doctype=self.api.DT,attached_to_name='BB')
        doc=Row(**old,get_doc_before_save=lambda:old)
        self.api.protect_file_update(doc)
        doc['is_private']=0
        with self.assertRaises(ValueError):self.api.protect_file_update(doc)

    def test_pickup_authorization_is_not_debt_signing_authorization(self):
        doc=Row(check_permission=Mock())
        self.f.get_doc=Mock(return_value=doc)
        with self.assertRaises(ValueError):
            self.api.record_signature('BB','MOD','Lái xe','Được ủy quyền ký nợ',authorization='',location='Tập cửa hàng')

    def test_current_source_must_still_be_posted_after_ledger_lock(self):
        source=Row(docstatus=2, company='CO', customer='KH', check_permission=Mock())
        self.f.get_doc=Mock(return_value=source)
        with self.assertRaises(ValueError):
            self.api._lock_sources('KH',['CO'],{('Sales Invoice','SI')},{('Delivery Note','DN'):Row()})
        self.f.get_doc.assert_called_once_with('Delivery Note','DN',for_update=True)

    def test_stock_and_custom_link_restrictions_block_aggregate_list_and_pdf_scope(self):
        self.f.get_meta.return_value=Row(fields=[Row(fieldtype='Table',options='ChiTiet')])
        self.f.get_meta.side_effect=lambda doctype:Row(fields=[Row(fieldtype='Link',options='Warehouse')]) if doctype=='ChiTiet' else Row(fields=[Row(fieldtype='Table',options='ChiTiet')])
        self.permissions.get_user_permissions.return_value={'Warehouse':[{'doc':'WH'}]}
        self.assertTrue(self.api._limited_dimensions())
        self.assertEqual(self.api.query_conditions(),'1=0')
        with self.assertRaises(PermissionError):self.api._guard()
        self.permissions.get_user_permissions.return_value={'Employee':[{'doc':'NHAN-SU'}]}
        self.assertFalse(self.api._limited_dimensions())

    def test_administrator_and_factory_price_policy_match_existing_app(self):
        self.f.get_roles.return_value=['APH Không xem giá vốn','System Manager']
        self.assertTrue(self.api._allowed('Administrator'))
        self.assertFalse(self.api._allowed('nhan-vien'))
        self.f.get_roles.return_value=['Kế toán bán hàng','Kế toán nhà máy']
        self.assertFalse(self.api._allowed('nhan-vien'))
        self.f.get_roles.return_value=['Kế toán bán hàng','Kế toán nhà máy','Accounts User']
        self.assertTrue(self.api._allowed('nhan-vien'))
