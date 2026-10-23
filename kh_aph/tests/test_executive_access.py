"""Quyền đọc điều hành không kèm quyền sửa sổ hoặc bỏ qua phạm vi chi tiết."""
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch


class ExecutiveAccess(TestCase):
    def setUp(self):
        self.f = ModuleType('frappe')
        self.f.session = SimpleNamespace(user='ceo@example.invalid')
        self.f.conf = {'kh_aph_quan_tri': 1}
        self.f.PermissionError = PermissionError
        self.f.throw = lambda message, error=ValueError: (_ for _ in ()).throw(error(message))
        self.f.get_roles = Mock(return_value=['Xem báo cáo điều hành'])
        self.f.get_all = Mock(return_value=[])
        self.f.db = Mock()
        self.k = ModuleType('kh_aph.quan_tri')
        self.k.VAI_TRO_XEM = {'Accounts Manager', 'System Manager'}
        self.k.can_quyen = Mock()
        utils = ModuleType('frappe.utils'); utils.cint = lambda value: int(value or 0)
        import kh_aph
        self.patches = [patch.dict('sys.modules', {'frappe':self.f,'frappe.utils':utils,'kh_aph.quan_tri':self.k}),
                        patch.object(kh_aph, 'quan_tri', self.k, create=True)]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)
        spec = importlib.util.spec_from_file_location('_executive_access_test', Path(__file__).resolve().parents[1]/'executive_access.py')
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)

    def test_report_role_is_additive_only_in_explicit_guard(self):
        self.m.guard()
        self.k.can_quyen.assert_called_once_with(self.k.VAI_TRO_XEM | {self.m.ROLE})
        self.assertNotIn(self.m.ROLE, self.k.VAI_TRO_XEM)

    def test_company_scope_allowed_but_item_or_warehouse_scope_denied(self):
        self.f.get_all.return_value = [SimpleNamespace(allow='Company')]
        self.m.guard()
        for dimension in ('Customer', 'Warehouse', 'Item'):
            self.f.get_all.return_value = [SimpleNamespace(allow=dimension)]
            with self.assertRaises(PermissionError): self.m.guard()

    def test_native_no_cost_denial_is_not_swallowed(self):
        self.k.can_quyen.side_effect = PermissionError('Ẩn giá vốn')
        with self.assertRaises(PermissionError): self.m.guard()
        self.f.get_all.assert_not_called()

    def test_schema_never_grants_writes_or_user_admin(self):
        self.f.session.user = 'Administrator'
        report = Mock(module='Kh Aph', report_type='Script Report')
        report.roles = [SimpleNamespace(role=self.m.ROLE)]
        self.f.get_doc = Mock(return_value=report)
        perms = ModuleType('frappe.permissions')
        perms.add_permission = Mock(); perms.update_permission_property = Mock()
        custom = ModuleType('frappe.core.doctype.custom_role.custom_role')
        custom.get_custom_allowed_roles = Mock(return_value=[])
        with patch.dict('sys.modules', {'frappe.permissions':perms,'frappe.core.doctype.custom_role.custom_role':custom}):
            self.m.schema()
        self.assertTrue(perms.update_permission_property.called)
        self.assertTrue(all(call.args[3] in ('read', 'report') for call in perms.update_permission_property.call_args_list))
        self.assertFalse(any(call.args[0] in ('User', 'Journal Entry') for call in perms.add_permission.call_args_list))
        report.save.assert_not_called()
