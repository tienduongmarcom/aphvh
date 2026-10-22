"""Giấy nhập bổ sung không đổi định danh hoặc cho dùng tệp của phiếu khác."""
import datetime
import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get
    def set(self, key, value): self[key] = value


class PaperArchive(unittest.TestCase):
    def setUp(self):
        f = self.f = types.ModuleType('frappe')
        f.conf = {'kh_aph_kho_van_hanh': 1, 'kh_aph_cash_custody': 1}
        f.throw = lambda text: (_ for _ in ()).throw(ValueError(text))
        f.db = Row(exists=Mock(return_value=False))
        f.get_doc = Mock(return_value=Row(check_permission=Mock()))
        utils = types.ModuleType('frappe.utils')
        utils.cint = lambda v: int(v or 0)
        utils.get_datetime = lambda v: v if isinstance(v, datetime.datetime) else datetime.datetime.fromisoformat(v)
        utils.now_datetime = lambda: datetime.datetime(2026, 10, 22, 12)
        ctx = patch.dict(sys.modules, {'frappe': f, 'frappe.utils': utils})
        ctx.start(); self.addCleanup(ctx.stop)
        spec = importlib.util.spec_from_file_location('test_paper', pathlib.Path(__file__).resolve().parents[1] / 'paper_archive.py')
        self.api = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.api)

    def doc(self, old=None, **values):
        data = Row(doctype='Delivery Note', company='CO', name='DN1', docstatus=0,
            meta=Row(has_field=lambda f: True), is_new=lambda: old is None,
            get_doc_before_save=lambda: old, **{
                self.api.FLAG: 1, self.api.NUMBER: ' ch1 / q01 / 001 ',
                self.api.ACTUAL: '2026-10-22 08:00:00', self.api.LOCATION: 'Tập cửa hàng'})
        data.update(values)
        return data

    def test_number_normalized_and_company_scoped_key(self):
        self.assertEqual(self.api.paper_number(' ch1  / q01 '), 'CH1 / Q01')
        self.assertNotEqual(self.api.paper_key('CO1', '001'), self.api.paper_key('CO2', '001'))
        doc = self.doc(**{self.api.KEY: 'TU-GAN'})
        self.api.validate(doc)
        self.assertEqual(doc[self.api.KEY], self.api.paper_key('CO', 'CH1 / Q01 / 001'))

    def test_disabled_flags_do_not_add_behavior(self):
        self.f.conf = {}
        self.api.validate(self.doc(**{self.api.NUMBER: ''}))
        self.f.get_doc.assert_not_called()

    def test_draft_can_be_corrected_before_it_posts(self):
        old = self.doc(); self.api.validate(old)
        doc = self.doc(old, **{self.api.NUMBER: 'CH1 / Q1 / 002'})
        self.api.validate(doc)
        self.assertEqual(doc[self.api.KEY], self.api.paper_key('CO', 'CH1 / Q1 / 002'))
        cleared = self.doc(old, **{self.api.FLAG: 0})
        self.api.validate(cleared)
        self.assertIsNone(cleared[self.api.NUMBER]); self.assertIsNone(cleared[self.api.KEY])

    def test_number_date_company_cannot_be_changed_or_cleared(self):
        old = self.doc(docstatus=1); self.api.validate(old)
        for field, value in [(self.api.FLAG, 0), (self.api.NUMBER, 'KHAC'), (self.api.ACTUAL, '2026-10-21 08:00:00'), ('company', 'CO2')]:
            doc = self.doc(old, **{self.api.NUMBER: old[self.api.NUMBER], field: value})
            with self.subTest(field=field), self.assertRaises(ValueError): self.api.validate(doc)

    def test_actual_time_is_required_not_future_and_does_not_change_posting_date(self):
        for value in [None, '2026-10-23 00:00:00']:
            with self.assertRaises(ValueError): self.api.validate(self.doc(**{self.api.ACTUAL: value}))
        doc = self.doc(posting_date='2026-10-22'); self.api.validate(doc)
        self.assertEqual(doc.posting_date, '2026-10-22')

    def test_cancel_releases_only_active_key_preserving_paper_identity(self):
        doc = self.doc(docstatus=2)
        self.api.validate(doc)
        self.assertIsNone(doc[self.api.KEY]); self.assertTrue(doc[self.api.NUMBER])

    def test_existing_cancelled_paper_requires_native_amendment(self):
        self.f.db.exists.return_value = True
        with self.assertRaises(ValueError): self.api.validate(self.doc())

    def test_amendment_inherits_current_source_when_no_copy_fields_are_empty(self):
        original = self.doc(docstatus=2); self.api.validate(original)
        original['check_permission'] = Mock()
        original[self.api.LOCATION] = 'Tập kế toán cửa hàng'
        self.f.get_doc.side_effect = lambda dt, name: original if dt == 'Delivery Note' else Row(check_permission=Mock())
        doc = self.doc(amended_from='DN-CU', **{self.api.FLAG: 0, self.api.NUMBER: None,
            self.api.ACTUAL: None, self.api.LOCATION: None})
        self.api.validate(doc)
        self.assertEqual(doc[self.api.NUMBER], original[self.api.NUMBER])
        self.assertEqual(doc[self.api.LOCATION], original[self.api.LOCATION])
        self.assertTrue(doc[self.api.KEY])

    def test_public_or_unrelated_file_is_rejected(self):
        for value in ['/files/paper.pdf', 'https://example.invalid/paper.pdf', '/private/files/other.pdf']:
            with self.subTest(url=value), self.assertRaises(ValueError): self.api.validate(self.doc(**{self.api.FILE: value}))

    def test_original_file_is_kept_location_can_follow_physical_paper(self):
        old = self.doc(docstatus=1); self.api.validate(old)
        old[self.api.FILE] = '/private/files/paper.pdf'
        with self.assertRaises(ValueError):
            self.api.validate(self.doc(old, **{self.api.NUMBER: old[self.api.NUMBER], self.api.FILE: None}))
        self.f.db.exists.return_value = True
        doc = self.doc(old, **{self.api.NUMBER: old[self.api.NUMBER], self.api.FILE: old[self.api.FILE], self.api.LOCATION: 'Tập kế toán cửa hàng'})
        self.api.validate(doc)
        self.assertEqual(doc[self.api.LOCATION], 'Tập kế toán cửa hàng')
