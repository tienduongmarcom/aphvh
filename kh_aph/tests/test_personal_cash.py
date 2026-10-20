"""Capability tiền cá nhân: chỉ Cash đúng scope, không mở quyền GL/nguồn."""
import importlib
import sys
import types
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get


class PersonalCash(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package = kh_aph
        self.names = ('cash_closing', 'cash_custody', 'cash_handover', 'personal_cash')
        self.saved = {k: getattr(kh_aph, k, None) for k in self.names}
        self.f = types.ModuleType('frappe')
        self.f.session = Row(user='me')
        self.f.conf = {'kh_aph_factory_cash': 1}
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.throw = lambda msg, exc=ValueError: (_ for _ in ()).throw(exc(msg))
        self.f.PermissionError = PermissionError
        self.f.db = Mock()
        self.f.db.sql.return_value = []
        self.f.get_list = Mock(return_value=['cash'])
        self.co = Row(default_currency='VND', kh_aph_quy_nha_may='factory', check_permission=Mock())
        self.acc = Row(company='APH', account_type='Cash', is_group=0, disabled=0, account_currency='VND', check_permission=Mock())
        self.f.get_doc = Mock(side_effect=lambda dt, name: self.co if dt == 'Company' else self.acc)
        self.c = types.ModuleType('kh_aph.cash_closing')
        self.c.enabled = Mock(return_value=True)
        self.c.roles_for = Mock(return_value={'Accounts User'})
        self.c.MANAGERS = {'Accounts Manager', 'System Manager'}
        self.c.SHIFT = 'APH Chot ca tien'
        self.c._state = Mock(return_value=(None, None, [], {'me': Decimal(75), 'other': Decimal(999)}))
        self.custody = types.ModuleType('kh_aph.cash_custody')
        self.custody.enabled = Mock(return_value=True)
        self.custody._person = Mock()
        self.custody.SOURCES = ('Payment Entry', 'Journal Entry', 'Sales Invoice', 'Purchase Invoice', 'POS Invoice')
        self.custody.HOLDER = 'kh_aph_nguoi_giu_tien'
        self.custody.PAYER = 'kh_aph_nguoi_giao_tien'
        self.h = types.ModuleType('kh_aph.cash_handover')
        self.h.enabled = Mock(return_value=True)
        self.h.PENDING = ('Chờ nhận', 'Vượt nguồn cần xử lý')
        self.h._query = Mock(return_value=[])
        self.h._disputed = Mock(return_value=False)
        self.utils = types.ModuleType('frappe.utils')
        self.utils.cint = lambda value: int(value or 0)
        self.utils.now_datetime = lambda: 'now'
        self.permissions = types.ModuleType('frappe.permissions')
        self.permissions.has_user_permission = Mock(return_value=True)
        self.p = patch.dict(sys.modules, {'frappe': self.f, 'frappe.utils': self.utils,
            'frappe.permissions': self.permissions,
            'kh_aph.cash_closing': self.c, 'kh_aph.cash_custody': self.custody, 'kh_aph.cash_handover': self.h})
        self.p.start()
        kh_aph.cash_closing, kh_aph.cash_custody, kh_aph.cash_handover = self.c, self.custody, self.h
        sys.modules.pop('kh_aph.personal_cash', None)
        self.m = importlib.import_module('kh_aph.personal_cash')

    def tearDown(self):
        sys.modules.pop('kh_aph.personal_cash', None)
        for key, value in self.saved.items():
            if value is None:
                if hasattr(self.package, key): delattr(self.package, key)
            else: setattr(self.package, key, value)
        self.p.stop()

    def test_shift_capability_never_allows_other_holder_or_opening(self):
        doc = Row(doctype=self.c.SHIFT,company='APH',account='cash',holder='me',personal_request='R',flags=Row())
        self.assertFalse(self.m.shift_allowed(doc))
        with self.m._shift_operation(doc):
            self.assertTrue(self.m.shift_allowed(doc))
            for key,value in [('holder','other'),('company','VH'),('doctype','APH Xac minh quy'),('personal_request','other')]:
                old=doc[key];doc[key]=value;self.assertFalse(self.m.shift_allowed(doc));doc[key]=old
        self.assertFalse(self.m.shift_allowed(doc))
        with self.assertRaises(PermissionError):self.m.shift_origin(doc)

    def test_shift_prepare_retry_normalizes_money_and_rejects_changed_payload(self):
        from kh_aph.cash_closing_rules import money
        self.c._money=money
        self.m._shift_scope=Mock()
        saved=[]
        self.f.db.sql.side_effect=lambda *a,**k:[] if not saved else [('S',)]
        def get_doc(*args,**kwargs):
            if len(args)==1:
                doc=Row(args[0]);doc.flags=Row();doc.name='S';doc.docstatus=0
                doc.insert=lambda:saved.append(doc)
                return doc
            return saved[0]
        self.f.get_doc=get_doc
        first=self.m.prepare_shift('APH','cash','R',10,reason='đếm')
        self.assertEqual(self.m.prepare_shift('APH','cash','R','10.00',reason='đếm'),first)
        self.assertEqual(len(saved),1)
        with self.assertRaisesRegex(ValueError,'nội dung khác'):self.m.prepare_shift('APH','cash','R',11,reason='đếm')
        self.assertFalse(self.m.shift_allowed(saved[0]))
        self.assertNotIn('personal_payload',first);self.assertNotIn('source_rows',first)

    def test_shift_confirm_checks_actor_before_native_submit(self):
        self.m._shift_scope=Mock()
        doc=Row(company='APH',account='cash',holder='other',personal_request='R',docstatus=0,flags=Row(),submit=Mock())
        self.f.get_doc=Mock(return_value=doc)
        with self.assertRaises(PermissionError):self.m.confirm_shift('S')
        doc.submit.assert_not_called()

    def test_flags_guest_and_unrelated_roles_fail_before_read(self):
        self.c.enabled.return_value = False
        with self.assertRaises(ValueError): self.m.current('APH', 'cash')
        self.c.enabled.return_value = True
        self.custody.enabled.return_value = False
        with self.assertRaises(ValueError): self.m.accounts('APH')
        self.custody.enabled.return_value = True
        self.f.session.user = 'Guest'
        with self.assertRaises(PermissionError): self.m.current('APH', 'cash')
        self.f.session.user = 'me'
        self.c.roles_for.return_value = {'Stock User'}
        with self.assertRaises(PermissionError): self.m.current('APH', 'cash')
        self.f.get_doc.assert_not_called(); self.f.db.sql.assert_not_called()

    def test_company_and_active_person_checked_before_cash_read(self):
        self.custody._person.side_effect = PermissionError('company denied')
        with self.assertRaises(PermissionError): self.m.current('VH', 'cash')
        self.f.get_doc.assert_not_called(); self.f.db.sql.assert_not_called()

    def test_no_cost_with_managers_still_only_configured_factory_cash(self):
        self.c.roles_for.return_value = {'APH Không xem giá vốn', 'Accounts Manager', 'System Manager'}
        with self.assertRaises(PermissionError): self.m.current('APH', 'cash')
        self.f.db.sql.assert_not_called()
        self.assertEqual(self.m.accounts('APH'), ['factory'])
        self.acc.check_permission.assert_not_called()
        self.co.check_permission.assert_called_with('read')
        self.f.get_list.assert_not_called()
        self.permissions.has_user_permission.return_value = False
        with self.assertRaises(PermissionError): self.m.current('APH', 'factory')
        self.f.conf = {}
        with self.assertRaises(PermissionError): self.m.accounts('APH')

    def test_other_company_bank_group_disabled_and_currency_fail_before_lock(self):
        for key, value in [('company', 'VH'), ('account_type', 'Bank'), ('is_group', 1), ('disabled', 1), ('account_currency', 'USD')]:
            before = self.acc[key]
            self.acc[key] = value
            with self.assertRaises(ValueError): self.m.current('APH', 'cash')
            self.acc[key] = before
        self.f.db.sql.assert_not_called()
        self.acc.check_permission.assert_called_with('read')

    def test_missing_cash_cannot_use_account_enumeration_scope(self):
        for value in (None, '', [], {}):
            with self.assertRaises(ValueError): self.m.current('APH', value)
        self.c._state.assert_not_called(); self.f.db.sql.assert_not_called()

    def test_only_session_amount_and_own_pending_reservations_returned(self):
        def row(holder, amount, state='Chờ nhận', account='cash'):
            return Row(from_holder=holder, requested_amount=amount, status=state, from_account=account)
        self.h._query.return_value = [row('me', 20), row('other', 900), row('me', 7, 'Đã nhận'), row('me', 4, account='other')]
        result = self.m.current('APH', 'cash')
        self.assertEqual(result, {'expected_amount': 75, 'reserved_amount': 20, 'available_amount': 55, 'disputed': False, 'checked_at': 'now'})
        self.c._state.assert_called_once_with('APH', 'cash', 'me', ledger_reader=self.m._ledger)
        self.assertNotIn('other', str(result))

    def test_negative_unknown_or_unresolved_shift_blocks_available_only(self):
        self.c._state.return_value = (None, None, [], {'me': Decimal(75), '': Decimal(-1)})
        result = self.m.current('APH', 'cash')
        self.assertTrue(result['disputed']); self.assertEqual(result['available_amount'], 0)
        self.assertEqual(result['expected_amount'], 75)
        self.h.enabled.return_value = False
        self.c._state.return_value = (None, None, [], {'me': Decimal(75)})
        self.f.db.sql.side_effect = [[], [('shift',)]]
        self.assertTrue(self.m.current('APH', 'cash')['disputed'])

    def test_projection_uses_allowlisted_columns_and_caches_source(self):
        rows = [Row(name='a', voucher_type='Journal Entry', voucher_no='JE'), Row(name='b', voucher_type='Journal Entry', voucher_no='JE')]
        self.f.db.sql.return_value = rows
        with patch.object(self.m, '_holder', return_value='me') as holder:
            result = self.m._ledger('APH', 'cash')
        holder.assert_called_once_with('Journal Entry', 'JE', 'APH', 'cash')
        self.assertEqual([r.holder for r in result], ['me', 'me'])
        sql, args = self.f.db.sql.call_args.args
        self.assertNotIn('select *', sql.lower())
        self.assertNotIn('against', sql.lower()); self.assertNotIn('remarks', sql.lower())
        self.assertEqual(args, ('APH', 'cash')); self.assertIn('for update', sql)
        self.f.get_doc.assert_not_called()

    def test_no_silent_truncation_or_dynamic_source_tables(self):
        self.f.db.sql.return_value = [None] * 10001
        with self.assertRaises(ValueError): self.m._ledger('APH', 'cash')
        self.f.db.sql.reset_mock()
        self.assertEqual(self.m._holder('arbitrary', 'x', 'APH', 'cash'), '')
        self.f.db.sql.assert_not_called()

    def test_receipt_payer_journal_ambiguity_and_company_mismatch(self):
        h, p = self.custody.HOLDER, self.custody.PAYER
        source = Row(company='APH', paid_to='other', paid_from='cash', **{h: 'other', p: 'me'})
        self.f.db.sql.return_value = [source]
        self.assertEqual(self.m._holder('Payment Entry', 'PE', 'APH', 'cash'), 'me')
        for dt in ('Sales Invoice', 'Purchase Invoice', 'POS Invoice'):
            self.assertEqual(self.m._holder(dt, 'invoice', 'APH', 'cash'), 'other')
        self.f.db.sql.side_effect = [[Row(company='APH')], [Row(**{h: 'me'}), Row(**{h: ''})]]
        self.assertEqual(self.m._holder('Journal Entry', 'JE', 'APH', 'cash'), '')
        self.f.db.sql.side_effect = None
        self.f.db.sql.return_value = [Row(company='VH')]
        with self.assertRaises(ValueError): self.m._holder('Journal Entry', 'JE', 'APH', 'cash')
