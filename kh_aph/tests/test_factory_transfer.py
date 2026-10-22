"""NM01c: nhận chuyến chuyển đến không được nhận vượt, đổi đơn vị, nhận vào kho đang vận chuyển hay giả dấu."""
import importlib
import json
import sys
import types
import unittest
from decimal import Decimal
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class Doc(Row):
    items = property(lambda self: dict.get(self, 'items'))


def outgoing(**kw):
    rows = kw.pop('items', [Row(name='D1', item_code='A', t_warehouse='Transit - APH', transfer_qty=10,
                                conversion_factor=1, material_request_item=None)])
    doc = Doc(name='SE-OUT', company='APH', docstatus=1, purpose='Material Transfer', add_to_transit=1,
              outgoing_stock_entry=None, posting_date='2026-10-18', items=rows, check_permission=Mock())
    doc.update(kw)
    return doc


class Transfer(unittest.TestCase):
    def setUp(self):
        f = self.f = types.ModuleType('frappe')
        f.conf = {'kh_aph_factory_receiving': 1, 'kh_aph_quantity_valuation_mvp': 1, 'kh_aph_server_cost_guard': 1}
        f.session = Row(user='dung')
        f.PermissionError = PermissionError
        f.throw = lambda text, exc=ValueError: (_ for _ in ()).throw(exc(text))
        f.whitelist = lambda **kw: lambda fn: fn
        f.get_roles = lambda: ['Kế toán nhà máy', 'APH Không xem giá vốn']
        f.db = Mock(); f.db.get_value.return_value = 1; f.db.sql.return_value = []
        f.parse_json = lambda raw: json.loads(raw) if isinstance(raw, str) else raw
        f.get_doc = Mock(); f.get_list = Mock()
        f._dict = Row
        utils = types.ModuleType('frappe.utils')
        utils.cint = lambda v: int(v or 0)
        utils.getdate = lambda v: str(v)
        utils.today = lambda: '2026-10-20'
        utils.now_datetime = lambda: '2026-10-20 08:00:00'
        cash = types.ModuleType('kh_aph.cash_transaction')
        cash.retry_rpc = lambda fn: fn
        self.patch = patch.dict(sys.modules, {'frappe': f, 'frappe.utils': utils, 'kh_aph.cash_transaction': cash})
        self.patch.start()
        import kh_aph.factory_receiving as r
        importlib.reload(r)
        import kh_aph.factory_transfer as m
        self.m = importlib.reload(m)

    def tearDown(self):
        self.patch.stop()
        for name in ('kh_aph.factory_transfer', 'kh_aph.factory_receiving'):
            sys.modules.pop(name, None)

    def test_disabled_and_roles_before_reading_sources(self):
        self.f.conf['kh_aph_factory_receiving'] = 0
        with self.assertRaises(ValueError): self.m.preview('SE-OUT')
        self.f.conf['kh_aph_factory_receiving'] = 1
        self.f.get_roles = lambda: ['Sales User']
        with self.assertRaises(PermissionError): self.m.incoming('APH')
        self.f.get_doc.assert_not_called()

    def test_only_confirmed_transit_outgoing_entries(self):
        for bad in ({'docstatus': 0}, {'purpose': 'Material Receipt'}, {'add_to_transit': 0},
                    {'outgoing_stock_entry': 'SE-OTHER'}):
            self.f.get_doc.return_value = outgoing(**bad)
            with self.assertRaises(ValueError): self.m._outgoing('SE-OUT')

    def test_selection_rejects_prices_duplicates_fractions(self):
        r = {'source_row': 'D1', 'warehouse': 'NM - APH', 'qty': 4, 'bags': 0}
        for rows in ([], [r, r], [{**r, 'rate': 1}], [{**r, 'qty': 0}], [{**r, 'bags': 1.5}], [{**r, 'source_row': ''}]):
            with self.assertRaises(ValueError): self.m._selection(rows)
        self.assertEqual(self.m._selection([r]), self.m._selection([{**r, 'qty': '4.000'}]))

    def test_destination_same_company_leaf_not_transit(self):
        wh = Row(company='APH', disabled=0, is_group=0, warehouse_type=None, check_permission=Mock())
        self.f.get_doc.return_value = wh
        self.m._destination('NM - APH', 'APH', 'Transit - APH')
        for bad in ({'company': 'VH'}, {'is_group': 1}, {'disabled': 1}, {'warehouse_type': 'Transit'}):
            self.f.get_doc.return_value = Row(wh, **bad)
            with self.assertRaises(ValueError): self.m._destination('NM - APH', 'APH', 'Transit - APH')
        with self.assertRaises(ValueError): self.m._destination('Transit - APH', 'APH', 'Transit - APH')

    def test_remaining_reads_submitted_receipts(self):
        self.f.db.sql.return_value = [('D1', 6.0)]
        self.assertEqual(self.m.remaining_rows(outgoing()), {'D1': Decimal('4')})

    def _receive(self, qty, date='2026-10-20'):
        self.m._outgoing = Mock(return_value=outgoing())
        self.m._item = Mock(return_value=Row(kh_aph_kg_per_bag=0))
        self.m._destination = Mock()
        self.f.db.sql.side_effect = lambda q, *a: [('D1', 6.0)] if 'SUM(d.transfer_qty)' in q else []
        rows = json.dumps([{'source_row': 'D1', 'warehouse': 'NM - APH', 'qty': qty, 'bags': 0}])
        return self.m.receive('SE-OUT', 'req-1', rows, date, 'Người ký')

    def test_receive_blocks_over_remaining_and_bad_dates_before_writing(self):
        with self.assertRaises(ValueError): self._receive(5)
        with self.assertRaises(ValueError): self._receive(1, date='2026-10-21')
        with self.assertRaises(ValueError): self._receive(1, date='2026-10-17')

    def test_receive_replay_returns_same_entry_or_rejects_changed_content(self):
        self.m._outgoing = Mock(return_value=outgoing())
        entry = Row(name='SE-IN', docstatus=1, check_permission=Mock())
        rows = json.dumps([{'source_row': 'D1', 'warehouse': 'NM - APH', 'qty': 4, 'bags': 0}])
        self.f.db.sql.side_effect = lambda q, *a: [('SE-IN',)] if 'kh_aph_transfer_request' in q else []
        self.f.get_doc.return_value = entry
        body = json.dumps(['SE-OUT', self.m._selection(rows), '2026-10-20', 'Người ký', ''], sort_keys=True, ensure_ascii=False)
        import hashlib
        entry[self.m.PREFIX + 'payload'] = hashlib.sha256(body.encode()).hexdigest()
        self.assertEqual(self.m.receive('SE-OUT', 'req-1', rows, '2026-10-20', 'Người ký')['name'], 'SE-IN')
        with self.assertRaises(ValueError):
            self.m.receive('SE-OUT', 'req-1', rows, '2026-10-20', 'Người khác')

    def test_stamps_only_from_window_and_immutable(self):
        doc = Row({self.m.PREFIX + 'request': 'k', self.m.PREFIX + 'payload': 'p'}, is_new=lambda: True)
        with self.assertRaises(ValueError): self.m.protect(doc)
        token = self.m._INTERNAL.set(('dung', 'k', 'p'))
        try:
            self.m.protect(doc)
        finally:
            self.m._INTERNAL.reset(token)
        old = Row({self.m.PREFIX + 'request': 'k', self.m.PREFIX + 'receiver': 'A'})
        doc = Row({self.m.PREFIX + 'request': 'k', self.m.PREFIX + 'receiver': 'B'}, is_new=lambda: False,
                  get_doc_before_save=lambda: old)
        with self.assertRaises(ValueError): self.m.protect(doc)
        self.m.protect(Row(is_new=lambda: True))  # phiếu kho thường không có dấu: không đụng
        with self.assertRaises(ValueError): self.m.prevent_delete(Row({self.m.PREFIX + 'request': 'k'}))

    def test_native_receipt_locked_and_capped(self):
        self.f.get_doc.return_value = outgoing()
        self.f.db.get_value.return_value = 'APH'
        self.f.db.sql.side_effect = lambda q, *a: [('D1', 6.0)] if 'SUM(d.transfer_qty)' in q else []
        doc = Doc(purpose='Material Transfer', outgoing_stock_entry='SE-OUT', company='APH',
                  items=[Row(against_stock_entry='SE-OUT', ste_detail='D1', transfer_qty=3),
                         Row(against_stock_entry='SE-OUT', ste_detail='D1', transfer_qty=2)])
        with self.assertRaises(ValueError): self.m.lock_outgoing(doc, 'before_submit')
        locks = [c.args[0] for c in self.f.db.sql.call_args_list if 'FOR UPDATE' in c.args[0]]
        self.assertTrue(any('tabStock Entry' in q for q in locks))
        doc['items'] = doc['items'][:1]
        self.m.lock_outgoing(doc, 'before_submit')
        self.f.db.get_value.return_value = 'VH'
        with self.assertRaises(ValueError): self.m.lock_outgoing(doc, 'before_submit')
        self.f.conf['kh_aph_factory_receiving'] = 0
        self.m.lock_outgoing(doc, 'before_submit')

    def test_send_requires_transit_valid_source_and_no_future(self):
        rows = json.dumps([{'item_code': 'A', 'warehouse': 'HN - APH', 'qty': 5, 'bags': 0}])
        self.f.get_doc.return_value = Row(check_permission=Mock())
        transit = {'v': None}
        self.f.db.get_value.side_effect = lambda dt, name, field: 1 if dt == 'User' else transit['v']
        with self.assertRaises(ValueError): self.m.send('APH', 'r', rows, '2026-10-20', 'Xe 29C')
        transit['v'] = 'Transit - APH'
        with self.assertRaises(ValueError): self.m.send('APH', 'r', rows, '2026-10-21', 'Xe 29C')
        with self.assertRaises(ValueError): self.m.send('APH', 'r', rows, '2026-10-20', '')
        with self.assertRaises(ValueError):
            self.m.send('APH', 'r', json.dumps([{'item_code': 'A', 'warehouse': 'HN', 'qty': 5, 'bags': 0, 'rate': 1}]), '2026-10-20', 'Xe')
        self.m._item = Mock(return_value=Row(kh_aph_kg_per_bag=0))
        self.f.get_doc.return_value = Row(name='Transit - APH', company='APH', is_group=0, disabled=0, check_permission=Mock())
        with self.assertRaises(ValueError):
            self.m.send('APH', 'r', json.dumps([{'item_code': 'A', 'warehouse': 'Transit - APH', 'qty': 5, 'bags': 0}]), '2026-10-20', 'Xe')

    def test_store_transfer_does_not_require_factory_screen(self):
        self.f.conf['kh_aph_factory_receiving'] = 0
        self.f.conf['kh_aph_kho_van_hanh'] = 1
        self.f.get_roles = lambda: ['Stock User']
        self.m.guard()
        self.f.conf['kh_aph_server_cost_guard'] = 0
        with self.assertRaises(ValueError): self.m.guard()

    def test_prepare_inserts_draft_and_replay_never_submits(self):
        src = Row(name='HN - APH', company='APH', is_group=0, disabled=0, check_permission=Mock())
        entry = Doc(name='SE-DRAFT', docstatus=0, check_permission=Mock(), insert=Mock(), submit=Mock())
        entry.set = lambda k, v: entry.update({k: v})
        self.f.get_doc.side_effect = lambda dt, *a, **kw: entry if isinstance(dt, dict) else src
        self.f.db.get_value.side_effect = lambda dt, *a: 1 if dt == 'User' else 'Transit - APH'
        self.m._item = Mock(return_value=Row(kh_aph_kg_per_bag=0))
        self.m._destination = Mock()
        args = dict(company='APH', request_id='draft-1', rows=[dict(item_code='A', warehouse='HN - APH', qty=5, bags=0)],
                    sent_date='2026-10-20', carrier='Xe', prepare_only=1, destination='CH - APH')
        self.assertEqual(self.m.send(**args)['docstatus'], 0)
        entry.insert.assert_called_once(); entry.submit.assert_not_called()
        self.f.db.sql.side_effect = lambda q, *a: [('SE-DRAFT',)] if 'kh_aph_transfer_request' in q else []
        self.f.get_doc.side_effect = lambda dt, *a, **kw: entry if dt == 'Stock Entry' else src
        self.assertEqual(self.m.send(**args)['name'], 'SE-DRAFT')
        entry['docstatus'] = 1
        self.assertEqual(self.m.send(**args)['docstatus'], 1)
        entry.submit.assert_not_called()
        with self.assertRaises(ValueError): self.m.send(**{**args, 'destination': 'OTHER'})
        entry['docstatus'] = 2
        with self.assertRaises(ValueError): self.m.send(**args)

    def test_prepare_requires_destination_and_strict_mode(self):
        self.f.get_doc.return_value = Row(check_permission=Mock())
        args = dict(company='APH', request_id='r', rows=[], sent_date='2026-10-20', carrier='Xe')
        for options in ({'prepare_only': 1}, {'prepare_only': 'yes'}, {'destination': []}):
            with self.assertRaises(ValueError): self.m.send(**args, **options)

    def test_posted_destination_frozen_and_only_unposted_preparation_can_be_deleted(self):
        old = Row(docstatus=1, **{self.m.DESTINATION: 'CH'})
        doc = Row(docstatus=1, is_new=lambda: False, get_doc_before_save=lambda: old,
                  **{self.m.DESTINATION: 'KHAC'})
        with self.assertRaises(ValueError): self.m.protect(doc)
        draft = Row(docstatus=0, add_to_transit=1, **{self.m.PREFIX + 'request': 'k', self.m.DESTINATION: 'CH'})
        self.m.prevent_delete(draft)
        draft['docstatus'] = 1
        with self.assertRaises(ValueError): self.m.prevent_delete(draft)

    def test_prepared_request_cannot_be_moved_to_another_company_or_operation(self):
        values = dict(company='APH', purpose='Material Transfer', stock_entry_type='Material Transfer', add_to_transit=1,
                      outgoing_stock_entry=None, docstatus=0, **{self.m.PREFIX + 'request': 'k'})
        old = Row(**values)
        for field, value in [('company', 'VH'), ('purpose', 'Material Receipt'), ('add_to_transit', 0),
                             ('stock_entry_type', 'Material Receipt'), ('outgoing_stock_entry', 'KHAC')]:
            doc = Row(**{**values, field: value}, is_new=lambda: False, get_doc_before_save=lambda: old)
            with self.subTest(field=field), self.assertRaises(ValueError): self.m.protect(doc)

    def test_driver_can_change_while_preparing_but_is_frozen_after_issue(self):
        values = dict(company='APH', purpose='Material Transfer', stock_entry_type='Material Transfer', add_to_transit=1,
                      outgoing_stock_entry=None, docstatus=0, items=[Row(s_warehouse='VT')],
                      **{self.m.PREFIX+'request':'k', self.m.PREFIX+'receiver':'Xe cũ', self.m.DESTINATION:'CH'})
        old = Row(**values)
        doc = Doc(**{**values, self.m.PREFIX+'receiver':'Xe thực tế'}, is_new=lambda:False, get_doc_before_save=lambda:old)
        self.m._destination = Mock()
        self.m.protect(doc)
        doc[self.m.DESTINATION] = None
        with self.assertRaises(ValueError): self.m.protect(doc)
        doc[self.m.DESTINATION] = 'CH'
        old['docstatus'] = 1; doc['docstatus'] = 1
        with self.assertRaises(ValueError): self.m.protect(doc)

    def test_wired_in_hooks_and_installer(self):
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        hooks = (root / 'hooks.py').read_text(encoding='utf-8')
        for name in ('protect', 'prevent_delete', 'lock_outgoing'):
            self.assertIn('"' + name + '"', hooks)
        self.assertIn('kh_aph.factory_transfer.', hooks)
        self.assertIn('public/js/factory_transfer.js', hooks)
        self.assertIn('factory_transfer.schema()', (root / 'uat_candidate_setup.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
