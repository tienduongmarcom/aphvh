"""Bản khách ký riêng, không ép ký cuối cho chuyến không yêu cầu và không ghi lại kho/tiền."""
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    def set(self, key, value): self[key] = value


class CustomerProof(unittest.TestCase):
    def setUp(self):
        f = self.f = types.ModuleType('frappe')
        f.session = Row(user='kt'); f.db = Mock(); f.get_doc = Mock()
        f.whitelist = lambda **kw: lambda fn: fn
        f.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        f.TimestampMismatchError = ValueError
        utils = types.ModuleType('frappe.utils'); utils.cint = lambda value: int(value or 0)
        utils.now_datetime = lambda: '2026-10-22 09:00:00'
        h = self.h = types.ModuleType('kh_aph.ho_so_giao_nhan'); h.enabled = lambda: 1; h._file = Mock()
        d = self.d = types.ModuleType('kh_aph.delivery_status'); d.confirm = Mock()
        context = patch.dict(sys.modules, {'frappe': f, 'frappe.utils': utils, 'kh_aph.ho_so_giao_nhan': h,
            'kh_aph.delivery_status': d})
        context.start(); self.addCleanup(context.stop)
        spec = importlib.util.spec_from_file_location('customer_proof_test', pathlib.Path(__file__).resolve().parents[1]/'customer_delivery_proof.py')
        self.api = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.api)

    def doc(self, **values):
        return Row(name='DN', docstatus=1, is_return=0, kh_aph_mau_giao_nhan=1, kh_aph_cach_giao='Vận chuyển',
            kh_aph_can_ky_khach='Có', kh_aph_delivery_state='Khách đã nhận', modified='m',
            meta=Row(has_field=lambda field: True), check_permission=Mock(), save=Mock(), **values)

    def test_only_required_shipping_has_final_customer_proof(self):
        doc = self.doc(); self.assertTrue(self.api.required(doc))
        for key, value in [('kh_aph_can_ky_khach', 'Không'), ('kh_aph_cach_giao', 'Khách đến lấy'), ('is_return', 1)]:
            other = self.doc(); other[key] = value
            self.assertFalse(self.api.required(other))
            other[self.api.FILE] = '/private/files/khach.pdf'
            with self.assertRaises(ValueError): self.api.validate(other, None)

    def test_direct_file_change_resets_only_customer_review_and_checks_private_source(self):
        old = self.doc(**{self.api.FILE: '/private/files/cu.pdf', self.api.ACTOR: 'kt', self.api.TIME: 'cu'})
        doc = self.doc(**{self.api.FILE: '/private/files/moi.pdf', self.api.ACTOR: 'kt', self.api.TIME: 'cu',
            'kh_aph_doi_chieu_boi': 'kho'})
        self.api.validate(doc, old)
        self.h._file.assert_called_once_with(doc, self.api.FILE)
        self.assertIsNone(doc[self.api.ACTOR]); self.assertEqual(doc.kh_aph_doi_chieu_boi, 'kho')

    def test_manual_stamps_and_original_location_are_blocked(self):
        for key in (self.api.ACTOR, self.api.TIME, self.api.ORIGINAL_BY, self.api.ORIGINAL_AT, self.api.LOCATION):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.api.validate(self.doc(**{key: 'gia mao'}), None)

    def test_paper_first_then_photo_keeps_first_original_timestamp_and_retry_saves_once(self):
        doc = self.doc(); self.f.get_doc.return_value = doc
        result = self.api.receive('DN', 'm', location='Tập khách ký tại cửa hàng')
        self.assertEqual(result['received_by'], 'kt'); self.assertEqual(doc[self.api.ORIGINAL_BY], 'kt')
        first = doc[self.api.ORIGINAL_AT]
        self.assertEqual(self.api.receive('DN', 'cu', location='Tập khách ký tại cửa hàng'), result)
        doc.save.assert_called_once()
        self.api.receive('DN', 'm', file_url='/private/files/khach.pdf')
        self.assertEqual(doc[self.api.ORIGINAL_AT], first)
        self.assertEqual(doc[self.api.FILE], '/private/files/khach.pdf')
        self.assertEqual(doc.save.call_count, 2)
        self.d.confirm.assert_not_called()

    def test_source_write_permission_and_stale_version_before_any_transition(self):
        doc = self.doc(); self.f.get_doc.return_value = doc
        with self.assertRaises(ValueError): self.api.receive('DN', 'cu', location='Tập')
        doc.check_permission.side_effect = PermissionError('Không có quyền')
        with self.assertRaises(PermissionError): self.api.receive('DN', 'm', location='Tập')
        doc.save.assert_not_called(); self.d.confirm.assert_not_called()

    def test_proof_received_while_in_transit_uses_existing_receipt_mark_only(self):
        transit = self.doc(); transit.kh_aph_delivery_state = 'Đang giao'
        received = self.doc(); self.f.get_doc.side_effect = [transit, received]
        self.api.receive('DN', 'm', location='Tập khách ký', received_on='2026-10-22')
        self.d.confirm.assert_called_once_with('DN', 'receive', reported_by='Khách báo', received_on='2026-10-22')
        received.save.assert_called_once()
        self.assertTrue(all(call.args[0].startswith('SELECT ') for call in self.f.db.sql.call_args_list))
