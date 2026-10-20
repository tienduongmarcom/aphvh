"""NM02–04: ghi sản xuất/đóng gói một lần không được dùng vượt dở dang, tự quy hao hụt hay giả dấu."""
import hashlib
import importlib
import json
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class Production(unittest.TestCase):
    def setUp(self):
        f = self.f = types.ModuleType('frappe')
        f.conf = {'kh_aph_factory_production': 1, 'kh_aph_factory_costing': 1, 'kh_aph_server_cost_guard': 1}
        f.session = Row(user='dung')
        f.PermissionError = PermissionError
        f.throw = lambda text, exc=ValueError: (_ for _ in ()).throw(exc(text))
        f.whitelist = lambda **kw: lambda fn: fn
        f.get_roles = lambda: ['Kế toán nhà máy', 'APH Không xem giá vốn']
        f.db = Mock(); f.db.sql.return_value = []
        f.parse_json = lambda raw: json.loads(raw) if isinstance(raw, str) else raw
        self.created = []

        def get_doc(arg, name=None, **kw):
            if isinstance(arg, dict):
                doc = Row(arg, insert=Mock(), submit=Mock(), check_permission=Mock(), name='SE-NEW', docstatus=1)
                doc.set = lambda k, v: doc.__setitem__(k, v)
                self.created.append(doc)
                return doc
            return Row(check_permission=Mock(), name=name)
        f.get_doc = get_doc
        f.get_cached_doc = lambda dt, name: Row(stock_uom='Kg')
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
        import kh_aph.factory_production as m
        self.m = importlib.reload(m)
        self.m._item = Mock(return_value=Row(stock_uom='Kg'))
        self.m._warehouse = Mock()

    def tearDown(self):
        self.patch.stop()
        for name in ('kh_aph.factory_production', 'kh_aph.factory_receiving'):
            sys.modules.pop(name, None)

    def bins(self, have):
        self.f.db.sql.side_effect = lambda q, *a: [(have,)] if 'tabBin' in q else []

    def call(self, kind='san_xuat', ins=None, outs=None, **kw):
        ins = ins or [{'item_code': 'BOT', 'warehouse': 'DD - APH', 'qty': 280}]
        outs = outs or [{'item_code': 'BANH', 'warehouse': 'CDG - APH', 'qty': 280}]
        args = dict(kind=kind, company='APH', request_id='r1', posting_date='2026-10-20',
                    inputs=json.dumps(ins), outputs=json.dumps(outs), workshop='Xưởng PT - APH')
        args.update(kw)
        return self.m.record(**args)

    def test_flags_and_roles_before_any_read(self):
        self.f.conf['kh_aph_factory_costing'] = 0
        with self.assertRaises(ValueError): self.m.context('APH')
        self.f.conf['kh_aph_factory_costing'] = 1
        self.f.get_roles = lambda: ['Sales User']
        with self.assertRaises(PermissionError): self.m.context('APH')

    def test_rows_reject_prices_and_zero(self):
        r = {'item_code': 'A', 'warehouse': 'W', 'qty': 1}
        for rows in ([], [{**r, 'rate': 1}], [{**r, 'qty': 0}], [{**r, 'qty': 'NaN'}]):
            with self.assertRaises(ValueError): self.m._rows(rows, ('item_code', 'warehouse', 'qty'))

    def test_production_needs_workshop_reason_single_line_and_no_future(self):
        self.bins(500)
        with self.assertRaises(ValueError): self.call(workshop='')
        with self.assertRaises(ValueError): self.call(outs=[{'item_code': 'BANH', 'warehouse': 'CDG - APH', 'qty': 270}])
        with self.assertRaises(ValueError): self.call(ins=[{'item_code': 'BOT', 'warehouse': 'DD1', 'qty': 1},
                                                          {'item_code': 'BOT', 'warehouse': 'DD2', 'qty': 1}])
        with self.assertRaises(ValueError): self.call(posting_date='2026-10-21')
        with self.assertRaises(ValueError): self.call(kind='khac')
        self.assertEqual(self.created, [])

    def test_cannot_use_more_than_in_wip(self):
        self.bins(100)
        with self.assertRaises(ValueError): self.call()
        self.assertEqual(self.created, [])

    def test_single_output_is_manufacture_loss_recorded_with_reason(self):
        self.bins(500)
        got = self.call(outs=[{'item_code': 'BANH', 'warehouse': 'CDG - APH', 'qty': 270}], note='giảm ẩm')
        doc = self.created[0]
        self.assertEqual(got['type'], 'Sản xuất theo kg')
        self.assertEqual(doc['kh_aph_xuong'], 'Xưởng PT - APH')
        self.assertEqual((doc['kh_aph_loss_type'], doc['kh_aph_loss_reason']), ('Hao hụt tự nhiên', 'giảm ẩm'))
        self.assertEqual([r.get('is_finished_item') for r in doc['items']], [None, 1])
        self.assertEqual(doc['items'][0]['s_warehouse'], 'DD - APH')
        doc.insert.assert_called_once(); doc.submit.assert_called_once()

    def test_several_outputs_use_kg_split_type_without_forcing_loss(self):
        self.bins(500)
        self.call(outs=[{'item_code': 'TP1', 'warehouse': 'CDG - APH', 'qty': 200},
                        {'item_code': 'PHU', 'warehouse': 'CDG - APH', 'qty': 80}])
        doc = self.created[0]
        self.assertEqual(doc['stock_entry_type'], 'Đóng gói theo kg')
        self.assertNotIn('kh_aph_loss_type', doc)

    def test_packaging_confirmation_needs_reason_and_is_passed_through(self):
        self.bins(500)
        with self.assertRaises(ValueError): self.call(kind='dong_goi', confirm_difference=1, note='')
        self.call(kind='dong_goi', confirm_difference=1, note='cân lại thiếu 0,2 kg')
        doc = self.created[0]
        self.assertEqual(doc['stock_entry_type'], 'Đóng gói thành phẩm')
        self.assertEqual(doc['kh_aph_xac_nhan_lech_kg'], 1)
        self.assertNotIn('kh_aph_xuong', doc)

    def test_replay_returns_same_or_rejects_changed(self):
        ins = [{'item_code': 'BOT', 'warehouse': 'DD - APH', 'qty': 280}]
        outs = [{'item_code': 'BANH', 'warehouse': 'CDG - APH', 'qty': 280}]
        body = json.dumps(['san_xuat', 'APH', '2026-10-20', self.m._rows(ins, ('item_code', 'warehouse', 'qty')),
                           self.m._rows(outs, ('item_code', 'warehouse', 'qty')), 'Xưởng PT - APH', '', 0],
                          sort_keys=True, ensure_ascii=False)
        entry = Row(name='SE-OLD', docstatus=1, check_permission=Mock())
        entry[self.m.PREFIX + 'payload'] = hashlib.sha256(body.encode()).hexdigest()
        self.f.db.sql.side_effect = lambda q, *a: [('SE-OLD',)] if 'kh_aph_production_request' in q else []
        self.f.get_doc = lambda *a, **k: entry
        self.assertEqual(self.call(ins=ins, outs=outs)['name'], 'SE-OLD')
        with self.assertRaises(ValueError): self.call(ins=ins, outs=outs, note='khác')

    def test_stamps_only_from_window(self):
        doc = Row({self.m.PREFIX + 'request': 'k', self.m.PREFIX + 'payload': 'p'}, is_new=lambda: True)
        with self.assertRaises(ValueError): self.m.protect(doc)
        old = Row({self.m.PREFIX + 'note': 'a'})
        doc = Row({self.m.PREFIX + 'note': 'b'}, is_new=lambda: False, get_doc_before_save=lambda: old)
        with self.assertRaises(ValueError): self.m.protect(doc)
        with self.assertRaises(ValueError): self.m.prevent_delete(Row({self.m.PREFIX + 'request': 'k'}))


if __name__ == '__main__':
    unittest.main()
