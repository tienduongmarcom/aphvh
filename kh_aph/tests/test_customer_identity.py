"""Địa chỉ import riêng: đọc Link được phép, không cần sửa cache Customer."""
import importlib
import re
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get


class CustomerIdentity(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.PermissionError = PermissionError
        self.f.get_list = Mock(return_value=[])
        self.f.db = Mock()
        utils = types.ModuleType('frappe.utils')
        utils.strip_html = lambda s: re.sub('<[^>]+>', '', s)
        address = types.ModuleType('frappe.contacts.doctype.address.address')
        address.get_address_display = lambda d: '<br>'.join(d.get(k, '') for k in ('address_line1', 'city'))
        self.patch = patch.dict(sys.modules, {'frappe': self.f, 'frappe.utils': utils,
            'frappe.contacts.doctype.address.address': address})
        self.patch.start()
        import kh_aph.customer_identity as m
        self.m = importlib.reload(m)
        self.customer = Row(name='KH-test', customer_name='Khách thử', mobile_no='', primary_address='')

    def tearDown(self):
        self.patch.stop()
        sys.modules.pop('kh_aph.customer_identity', None)

    def address(self, name='DC1', customer='KH-test', **kw):
        value = Row(name=name, linked_customer=customer, address_line1='Địa chỉ nhập riêng', city='Hà Nội')
        value.update(kw)
        return value

    def test_linked_address_without_customer_cache_and_phone_on_address(self):
        self.f.get_list.side_effect = [[self.address(phone='0900000001')], []]
        before = dict(self.customer)
        value = self.m.details([self.customer])['KH-test']
        self.assertEqual(value['primary_address'], 'Địa chỉ nhập riêng, Hà Nội')
        self.assertEqual(value['mobile_no'], '0900000001')
        self.assertEqual(dict(self.customer), before)
        self.f.db.set_value.assert_not_called()
        call = self.f.get_list.call_args_list[0]
        self.assertIn(['Address', 'disabled', '=', 0], call.kwargs['filters'])
        self.assertIn(['Dynamic Link', 'parenttype', '=', 'Address'], call.kwargs['filters'])
        self.assertIn(['Dynamic Link', 'link_doctype', '=', 'Customer'], call.kwargs['filters'])

    def test_legacy_customer_only_fields_remain_when_no_linked_records(self):
        self.customer.update(mobile_no='0911', primary_address='A<br>B')
        self.assertEqual(self.m.details([self.customer])['KH-test']['primary_address'], 'A, B')
        self.assertEqual(self.f.get_list.call_count, 2)

    def test_explicit_primary_links_win_among_readable_linked_records(self):
        self.customer.update(customer_primary_address='DC2', customer_primary_contact='LH2')
        self.f.get_list.side_effect = [[self.address(), self.address('DC2', address_line1='Địa chỉ ưu tiên')],
            [Row(name='LH1', linked_customer='KH-test', mobile_no='01'),
             Row(name='LH2', linked_customer='KH-test', mobile_no='02')]]
        value = self.m.details([self.customer])['KH-test']
        self.assertEqual(value['mobile_no'], '02')
        self.assertEqual(value['primary_address'], 'Địa chỉ ưu tiên, Hà Nội')

    def test_unrelated_customer_records_do_not_supply_address_or_phone(self):
        self.customer.update(customer_primary_address='DC-khac')
        self.f.get_list.side_effect = [[self.address('DC-khac', customer='KH-khac', phone='KHONG-DUNG')],
            [Row(name='LH-khac', linked_customer='KH-khac', mobile_no='KHONG-DUNG')]]
        value = self.m.details([self.customer])['KH-test']
        self.assertEqual((value['primary_address'], value['mobile_no']), ('', ''))

    def test_address_permission_error_does_not_leak_or_claim_no_address(self):
        self.f.get_list.side_effect = [PermissionError(),
            [Row(name='LH1', linked_customer='KH-test', phone='0912')]]
        value = self.m.details([self.customer])['KH-test']
        self.assertIn('Không có quyền', value['primary_address'])
        self.assertEqual(value['mobile_no'], '0912')

    def test_contact_permission_error_can_still_use_readable_address_phone(self):
        self.f.get_list.side_effect = [[self.address(phone='0913')], PermissionError()]
        value = self.m.details([self.customer])['KH-test']
        self.assertEqual(value['mobile_no'], '0913')

    def test_missing_phone_is_not_invented(self):
        self.f.get_list.side_effect = [[self.address()], []]
        self.assertEqual(self.m.details([self.customer])['KH-test']['mobile_no'], '')

    def test_batch_does_not_query_each_customer_separately(self):
        customers = [Row(name=f'KH{i}', customer_name=f'Khách{i}') for i in range(30)]
        values = self.m.details(customers)
        self.assertEqual(len(values), 30)
        self.assertEqual(self.f.get_list.call_count, 2)
        self.assertEqual(self.f.get_list.call_args_list[0].kwargs['filters'][2][3], [c.name for c in customers])

    def test_linked_changes_override_stale_customer_cache(self):
        self.customer.update(mobile_no='CU', primary_address='Địa chỉ cũ')
        self.f.get_list.side_effect = [[self.address(address_line1='Địa chỉ mới')],
            [Row(name='LH1', linked_customer='KH-test', mobile_no='MOI')]]
        value = self.m.details([self.customer])['KH-test']
        self.assertEqual(value['mobile_no'], 'MOI')
        self.assertEqual(value['primary_address'], 'Địa chỉ mới, Hà Nội')

    def test_adding_then_updating_then_clearing_contact_is_read_fresh(self):
        self.customer.update(mobile_no='CACHE-CU')
        self.f.get_list.side_effect = [[], [], [],
            [Row(name='LH1', linked_customer='KH-test', phone='THEM')], [],
            [Row(name='LH1', linked_customer='KH-test', mobile_no='SUA')], [],
            [Row(name='LH1', linked_customer='KH-test', phone='', mobile_no='')]]
        self.assertEqual([self.m.details([self.customer])['KH-test']['mobile_no'] for _ in range(4)],
                         ['CACHE-CU', 'THEM', 'SUA', ''])

    def test_unavailable_explicit_links_do_not_revive_stale_cache(self):
        self.customer.update(customer_primary_address='AN', customer_primary_contact='AN',
                             primary_address='CACHE-CU', mobile_no='CACHE-CU')
        value = self.m.details([self.customer])['KH-test']
        self.assertEqual((value['primary_address'], value['mobile_no']), ('', ''))
