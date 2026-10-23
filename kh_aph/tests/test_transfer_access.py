"""Không mở nguồn chuyển kho nếu không đúng kho nhận; mapper không cấp quyền ghi."""
import importlib.util
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch


class TransferAccess(TestCase):
    def setUp(self):
        import kh_aph
        self.f=ModuleType('frappe');self.f.PermissionError=PermissionError
        self.f.throw=lambda message,error=ValueError:(_ for _ in ()).throw(error(message))
        self.f.has_permission=Mock(return_value=True)
        self.f.get_doc=Mock(return_value=SimpleNamespace(check_permission=Mock()))
        self.t=ModuleType('kh_aph.factory_transfer');self.t.guard=Mock();self.t._destination=Mock();self.t.DESTINATION='dest'
        utils=ModuleType('frappe.utils');utils.cint=lambda value:int(value or 0)
        self.patches=[patch.dict('sys.modules',{'frappe':self.f,'frappe.utils':utils,'kh_aph.factory_transfer':self.t}),
                      patch.object(kh_aph,'factory_transfer',self.t,create=True)]
        for item in self.patches:item.start();self.addCleanup(item.stop)
        spec=importlib.util.spec_from_file_location('_transfer_access_test',Path(__file__).resolve().parents[1]/'transfer_access.py')
        self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        self.source=SimpleNamespace(name='OUT',company='APH',docstatus=1,purpose='Material Transfer',add_to_transit=1,
            get=lambda key:{'dest':'STORE','outgoing_stock_entry':None}.get(key))

    def test_only_expected_destination_can_read_quantity_projection(self):
        self.m.expected_receiver(self.source)
        self.t._destination.assert_called_once_with('STORE','APH',None)
        self.t._destination.side_effect=PermissionError('Ngoài kho được giao')
        with self.assertRaises(PermissionError):self.m.expected_receiver(self.source)

    def test_missing_destination_or_nonposted_source_cannot_bypass_native_read(self):
        self.source.get=lambda key:None
        with self.assertRaises(PermissionError):self.m.expected_receiver(self.source)
        self.source.docstatus=0
        with self.assertRaises(PermissionError):self.m.expected_receiver(self.source)
        self.t._destination.assert_not_called()

    def test_mapper_resets_target_permission_and_checks_native_create(self):
        mapper=ModuleType('frappe.model.mapper')
        entry=SimpleNamespace(flags=SimpleNamespace(ignore_permissions=True),check_permission=Mock())
        mapper.get_mapped_doc=Mock(return_value=entry)
        with patch.dict('sys.modules',{'frappe.model.mapper':mapper}):result=self.m.make_incoming(self.source)
        self.assertIs(result,entry)
        self.assertFalse(entry.flags.ignore_permissions)
        entry.check_permission.assert_called_once_with('create')
        call=mapper.get_mapped_doc.call_args
        self.assertEqual(call.args[:2],('Stock Entry','OUT'))
        self.assertTrue(call.kwargs['ignore_permissions'])
