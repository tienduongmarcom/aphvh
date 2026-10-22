"""Lối tìm biến thể của báo cáo số lượng không mở quyền Report hoặc đọc SQL."""
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from kh_aph.constants import ROLE_NO_COST, REPORT_QTY


class ReportDiscoveryBoundary(unittest.TestCase):
    def setUp(self):
        self.f=f=types.ModuleType('frappe')
        f.conf={'kh_aph_server_cost_guard':1};f.session=types.SimpleNamespace(user='factory@example.invalid')
        f.get_roles=Mock(return_value=[ROLE_NO_COST,'Accounts Manager'])
        f.whitelist=lambda *a,**kw:lambda fn:fn
        f.parse_json=lambda v:json.loads(v) if isinstance(v,str) else v
        f.PermissionError=PermissionError
        f.throw=lambda text,*a:(_ for _ in ()).throw(PermissionError(text))
        f.request=types.SimpleNamespace(path='/api/method/frappe.desk.reportview.get_list',method='GET')
        utils=types.ModuleType('frappe.utils');utils.cint=lambda v:int(v or 0)
        native=types.ModuleType('frappe.desk.reportview');self.native=native.get_list=Mock(return_value=[{'name':'OWN'}])
        context=patch.dict(sys.modules,{'frappe':f,'frappe.utils':utils,'frappe.desk.reportview':native})
        context.start();self.addCleanup(context.stop)
        root=pathlib.Path(__file__).resolve().parents[1]
        def load(name,path):
            spec=importlib.util.spec_from_file_location(name,root/path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
        self.api=load('test_discovery','report_discovery.py')
        self.policy=load('test_discovery_policy','dung_cost_policy.py')
        modules=patch.dict(sys.modules,{'kh_aph.report_discovery':self.api,'kh_aph.dung_cost_policy':self.policy})
        modules.start();self.addCleanup(modules.stop)
        self.f.form_dict=self.args()

    def args(self):
        return {'doctype':'Report','fields':json.dumps(['name','report_name']),
            'filters':json.dumps({'reference_report':REPORT_QTY,'report_type':'Custom Report','disabled':0}),
            'order_by':'report_name asc','limit':'0'}

    def test_exact_native_lookup_is_empty_without_database_or_metadata_reads(self):
        self.policy.before_request()
        self.assertEqual(self.api.get_list(),[])
        self.native.assert_not_called()

    def test_cost_report_wildcard_query_or_extra_options_stay_denied(self):
        changes=[{'fields':'["query"]'},{'fields':'["*"]'},{'doctype':'Bin'},
                 {'filters':json.dumps({'reference_report':'Stock Balance','report_type':'Custom Report','disabled':0})},
                 {'or_filters':'[]'},{'ignore_permissions':'1'},{'group_by':'name'}, {'as_csv':1},
                 {'order_by':'report_name asc; select valuation_rate'},{'filters':'invalid'}]
        for change in changes:
            with self.subTest(change=change):
                self.f.form_dict={**self.args(),**change}
                with self.assertRaises(PermissionError):self.policy.before_request()
                with self.assertRaises(PermissionError):self.api.get_list()
        self.native.assert_not_called()

    def test_native_query_shape_cannot_bypass_another_request_path(self):
        self.f.form_dict['cmd']=self.api.METHOD
        self.f.request.path='/api/resource/Report'
        # Explicit REST list remains denied; safe-shaped args cannot bypass its guard.
        self.f.get_meta=lambda dt:types.SimpleNamespace(istable=False)
        with self.assertRaises(PermissionError):self.policy.before_request()

    def test_allowed_owned_factory_list_keeps_native_permissions(self):
        self.f.form_dict={'doctype':'APH Phieu quy nha may','fields':'["name"]'}
        self.policy.before_request()
        self.assertEqual(self.api.get_list(),[{'name':'OWN'}]);self.native.assert_called_once_with()

    def test_administrator_keeps_native_report_discovery(self):
        self.f.session.user='Administrator'
        self.policy.before_request()
        self.assertEqual(self.api.get_list(),[{'name':'OWN'}]);self.native.assert_called_once_with()

    def test_disabled_guard_keeps_original_behavior(self):
        self.f.conf={}
        self.policy.before_request()
        self.assertEqual(self.api.get_list(),[{'name':'OWN'}]);self.native.assert_called_once_with()
