"""UX-01: Workspace mới song song, áp cấu hình người dùng chạy thử mặc định, không khóa kho người bán."""
import importlib
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class UX(unittest.TestCase):
    def setUp(self):
        f = self.f = types.ModuleType('frappe')
        f.conf = {'kh_aph_ux_task_first': 1}
        f.session = Row(user='admin@x')
        f.PermissionError = PermissionError
        f.throw = lambda text, exc=ValueError: (_ for _ in ()).throw(exc(text))
        f.whitelist = lambda **kw: lambda fn: fn
        f.get_roles = lambda: ['System Manager']
        f.parse_json = lambda raw: json.loads(raw) if isinstance(raw, str) else raw
        f.db = Mock(); f.db.exists.return_value = True; f.db.get_value.return_value = 'Trung tâm Bán hàng'
        f.get_meta = lambda dt: Row(has_field=lambda k: True)
        self.saved = []
        ws = Row(is_new=lambda: True, insert=Mock(), flags=Row())
        ws.update = lambda d: dict.update(ws, d)
        ws.set = lambda k, v: dict.__setitem__(ws, k, v)
        self.ws = ws
        f.new_doc = lambda dt: ws
        f.get_doc = Mock()
        utils = types.ModuleType('frappe.utils'); utils.cint = lambda v: int(v or 0)
        for key in ('flt','add_days','get_first_day','get_last_day','getdate','nowdate','now_datetime'):
            setattr(utils, key, Mock())
        self.patch = patch.dict(sys.modules, {'frappe': f, 'frappe.utils': utils})
        self.patch.start()
        self.f.db.exists.side_effect = lambda dt, name=None: dt != 'Workspace' and not (dt == 'User Permission')
        import kh_aph.ux_task as m
        self.m = importlib.reload(m)

    def tearDown(self):
        self.patch.stop()
        sys.modules.pop('kh_aph.ux_task', None)

    def test_workspace_three_blocks_unique_labels_and_new_name(self):
        name = self.m._workspace('ban_hang')
        self.assertEqual(name, 'Bán hàng')
        content = json.loads(self.ws['content'])
        headers = [c['data']['text'] for c in content if c['type'] == 'header']
        self.assertEqual(len(headers), 3)
        labels = [s['label'] for s in self.ws['shortcuts']]
        self.assertEqual(len(labels), len(set(labels)))
        shortcut_names = {c['data']['shortcut_name'] for c in content if c['type'] == 'shortcut'}
        self.assertEqual(shortcut_names, set(labels))
        self.assertTrue(any(s.get('stats_filter') for s in self.ws['shortcuts']))
        self.assertNotIn('Trung tâm', name)

    def test_module_profile_not_resaved_when_unchanged(self):
        saved = Mock()
        prof = Row(block_modules=[Row(module='Projects')], save=saved, flags=Row(), is_new=lambda: False)
        prof.set = lambda k, v: dict.__setitem__(prof, k, v)
        self.f.db.exists.side_effect = lambda dt, name=None: dt in ('Module Profile',) or (dt == 'Module Def' and name == 'Projects')
        self.f.get_doc = Mock(return_value=prof)
        self.m._module_profile('kho')
        saved.assert_not_called()

    def test_old_names_hidden_users_moved_unused_profile_removed(self):
        self.f.db.exists.side_effect = lambda dt, name=None: (dt == 'Workspace' and name == 'Việc kho') or (dt == 'Module Profile' and name == '9xLab - Việc kho')
        self.f.db.get_value.side_effect = lambda dt, name, field: self.m.MODULE
        self.f.get_all = Mock(return_value=['kho@x'])
        self.f.delete_doc = Mock()
        self.m._an_ten_cu()
        self.f.db.set_value.assert_any_call('Workspace', 'Việc kho', 'is_hidden', 1, update_modified=False)
        self.f.db.set_value.assert_any_call('User', 'kho@x', 'default_workspace', 'Kho vận', update_modified=False)
        self.f.delete_doc.assert_called_once_with('Module Profile', '9xLab - Việc kho', ignore_permissions=True, force=True)
        self.assertNotIn('Việc', ''.join(self.m.NHOM.values()))

    def test_link_fields_show_names_but_item_shows_code(self):
        self.f.get_meta = lambda dt: Mock(has_field=lambda k: True, get=lambda k: {'show_title_field_in_link': 1}.get(k) if dt == 'Item' else None)
        self.f.make_property_setter = Mock()
        self.m._hien_ten_khi_chon()
        got = {(c.args[0]['doctype'], c.args[0]['property'], c.args[0]['value']) for c in self.f.make_property_setter.call_args_list}
        self.assertIn(('Customer', 'show_title_field_in_link', '1'), got)
        self.assertIn(('Item', 'show_title_field_in_link', '0'), got)   # cột Mã hàng phải hiện mã
        self.assertNotIn(('Item', 'title_field', 'item_name'), got)
        self.assertIn(('Customer', 'search_fields', 'customer_name,mobile_no,primary_address'), got)
        self.f.make_property_setter.reset_mock()
        da = {'Customer': {'title_field': 'customer_name', 'show_title_field_in_link': 1, 'search_fields': 'customer_name,mobile_no,primary_address'},
              'Item': {'show_title_field_in_link': 0}, 'Supplier': {'title_field': 'supplier_name', 'show_title_field_in_link': 1}}
        self.f.get_meta = lambda dt: Mock(has_field=lambda k: True, get=lambda k: da[dt].get(k))
        self.m._hien_ten_khi_chon()
        self.f.make_property_setter.assert_not_called()

    def test_order_shows_item_name_and_customer_contact(self):
        base = pathlib.Path(__file__).resolve().parents[1] / 'kh_aph/doctype'
        it = json.loads((base / 'aph_shared_sales_order_item/aph_shared_sales_order_item.json').read_text(encoding='utf-8'))
        f = {x['fieldname']: x for x in it['fields']}
        self.assertEqual(f['item_name']['fetch_from'], 'item_code.item_name'); self.assertTrue(f['item_name']['in_list_view'])
        so = json.loads((base / 'aph_shared_sales_order/aph_shared_sales_order.json').read_text(encoding='utf-8'))
        g = {x['fieldname']: x for x in so['fields']}
        self.assertEqual(g['customer_phone']['fetch_from'], 'customer.mobile_no')
        self.assertEqual(g['customer_address']['fetch_from'], 'customer.primary_address')
        self.assertTrue(g['customer_address']['read_only'] and g['customer_phone']['read_only'])

    def test_disabled_no_schema(self):
        self.f.conf['kh_aph_ux_task_first'] = 0
        self.assertIsNone(self.m.schema())

    def test_apply_dry_run_by_default_and_admin_only(self):
        bang = [{'user': 'kho@x', 'nhom': 'kho', 'kho': ['NM - APH']}]
        got = self.m.ap_dung_nguoi_dung(json.dumps(bang))
        self.assertTrue(got['chay_thu'])
        self.assertEqual({k['viec'] for k in got['thay_doi']}, {'default_workspace', 'User Permission Warehouse'})
        self.f.db.set_value.assert_not_called()
        self.f.get_roles = lambda: ['Stock User']
        with self.assertRaises(PermissionError): self.m.ap_dung_nguoi_dung(json.dumps(bang))

    def test_sales_staff_never_warehouse_locked(self):
        with self.assertRaises(ValueError):
            self.m._ke_hoach([{'user': 'ban@x', 'nhom': 'ban_hang', 'kho': ['HN - APH']}])
        with self.assertRaises(ValueError):
            self.m._ke_hoach([{'user': 'ban@x', 'nhom': 'khac'}])

    def test_search_needs_two_chars_and_lists_all_matches(self):
        with self.assertRaises(ValueError): self.m.tim_khach('a')
        self.f.get_list = Mock(side_effect=lambda dt, **kw: [Row(name='KH1', customer_name='Minh Anh'), Row(name='KH2', customer_name='Minh Anh')]
                               if dt == 'Customer' else [])
        got = self.m.tim_khach('Minh Anh')
        self.assertEqual([r['name'] for r in got], ['KH1', 'KH2'])

    def test_receivable_split_per_company_no_cross_netting(self):
        self.f.get_doc = Mock(return_value=Row(check_permission=Mock()))
        utils = sys.modules['frappe.utils']
        utils.getdate = lambda v: str(v); utils.today = lambda: '2026-10-20'; utils.flt = lambda v: float(v or 0)
        def gl(dt, **kw):
            if dt == 'Company': return ['APH', 'VH']
            if dt == 'Sales Invoice': return [Row(name='SI1', company='APH', posting_date='2026-10-01', due_date='2026-10-10', outstanding_amount=100)]
            if dt == 'Payment Entry': return [Row(name='PE1', company='VH', posting_date='2026-10-02', unallocated_amount=70)]
        self.f.get_list = gl
        got = {d['company']: d for d in self.m.cong_no_khach('KH1')['don_vi']}
        self.assertEqual((got['APH']['phai_thu'], got['APH']['qua_han'], got['APH']['chua_phan_bo']), (100.0, 100.0, 0.0))
        self.assertEqual((got['VH']['phai_thu'], got['VH']['chua_phan_bo']), (0.0, 70.0))

    def test_next_step_js_only_clicks_existing_buttons(self):
        js = (pathlib.Path(__file__).resolve().parents[1] / 'public/js/ux_buoc_tiep.js').read_text(encoding='utf-8')
        self.assertNotIn('frappe.call', js)
        pay = (pathlib.Path(__file__).resolve().parents[1] / 'public/js/ux_thu_tien.js').read_text(encoding='utf-8')
        self.assertIn('kh_aph.ban_quay.thu_tien', pay)  # ghi bằng hàm thu tiền đã kiểm, không hàm ghi mới
        self.assertEqual(pay.count('method: "kh_aph.'), 3)
        self.assertNotIn('"Xuất và In"', js)
        self.assertIn('Lập phiếu xuất & In', js)

    def test_all_old_destinations_are_preserved_and_new_menu_has_no_duplicates(self):
        def key(x):
            return (x[1], x[2], json.dumps(x[3] or {}, sort_keys=True))
        from kh_aph import trung_tam_ban, kho_van_hanh, tien_vay, du_lieu
        for group, module in [('ban_hang', trung_tam_ban), ('kho', kho_van_hanh), ('tien', tien_vay)]:
            expected = {key(x) for x in module.workspace_links()}
            self.m._workspace(group)
            actual = {(x['type'], x['link_to'], json.dumps(json.loads(x.get('stats_filter', '{}')), sort_keys=True)) for x in self.ws['shortcuts']}
            self.assertTrue(expected <= actual, (group, expected - actual))
            exact = [(x['type'], x['link_to'], x.get('stats_filter', '{}'), x.get('doc_view')) for x in self.ws['shortcuts']]
            self.assertEqual(len(exact), len(set(exact)))
        self.m._workspace('du_lieu')
        self.assertTrue(any(x['link_to'] == 'Data Import' for x in self.ws['shortcuts']))
        self.assertNotIn('Assets', self.m.AN_THEO_NHOM['tien'])

    def test_transfer_queue_does_not_include_purchase_requests(self):
        values = [x for x in self.m._LAM['kho'] if x[2] == 'Material Request']
        self.assertEqual(values[0][3]['material_request_type'], 'Material Transfer')

    def test_native_sidebar_keeps_unrelated_customization_and_is_idempotent(self):
        unrelated = Row(link_type='DocType', link_to='Customer', hidden=0, label='Khách riêng')
        doc = Row(label=None, sidebar_items=[unrelated], insert=Mock(), save=Mock())
        doc.append = lambda key, value: doc[key].append(Row(value))
        self.f.db.get_value.return_value = None
        self.f.get_doc = Mock(return_value=doc)
        self.f.get_all = Mock(side_effect=lambda dt, **kw: {
            'DocType': ['APH Shared Sales Order', 'Chung tu rieng cua nguoi dung'],
            'Workspace': ['Trung tâm Bán hàng', 'Bàn kho', 'Trang rieng'],
            'Report': ['Tong hop ban hang theo khach', 'Bao cao rieng']}[dt])
        self.m._sidebar()
        self.assertEqual(doc.label, 'Vận hành')
        doc.insert.assert_called_once()
        self.f.db.get_value.assert_called_with('Custom Sidebar', {'module': self.m.MODULE, 'user': ['is', 'not set']}, 'name')
        rows = {(r.link_type, r.link_to): r for r in doc.sidebar_items}
        self.assertEqual(rows[('DocType', 'APH Shared Sales Order')].hidden, 1)
        self.assertEqual(rows[('Report', 'Tong hop ban hang theo khach')].hidden, 1)
        self.assertNotIn(('DocType', 'Chung tu rieng cua nguoi dung'), rows)
        self.assertNotIn(('Report', 'Bao cao rieng'), rows)
        self.assertTrue(all(rows[('Workspace', n)].hidden == 0 for n in self.m.NHOM.values()))
        self.assertEqual(rows[('Workspace', 'Trung tâm Bán hàng')].hidden, 1)
        self.assertEqual(rows[('Workspace', 'Bàn kho')].hidden, 1)
        self.assertNotIn(('Workspace', 'Trang rieng'), rows)
        self.assertEqual((unrelated.hidden, unrelated.label), (0, 'Khách riêng'))
        self.f.db.get_value.return_value = 'CS1'
        self.m._sidebar()
        doc.save.assert_not_called()
        self.f.conf['kh_aph_ux_task_first'] = 0
        self.f.get_doc.reset_mock()
        self.m._sidebar()
        self.f.get_doc.assert_not_called()

    def test_customer_identity_and_query_are_scoped_read_only(self):
        utils = sys.modules['frappe.utils']
        utils.strip_html = lambda v: v.replace('<br>', ' ')
        self.f.get_list = Mock(return_value=[Row(name='KH1', customer_name='Minh Anh', mobile_no='0912', primary_address='A<br>B')])
        self.assertEqual(self.m.customer_identity('KH1')['primary_address'], 'A B')
        self.f.get_list.assert_called_with('Customer', filters={'name': 'KH1'}, fields=['name', 'customer_name', 'mobile_no', 'primary_address'], limit_page_length=1)
        self.assertEqual(self.m.customer_query('Customer', 'Minh', 'name', 0, 100)[0], ['KH1', 'Minh Anh', '0912', 'A B'])
        self.assertEqual(self.f.get_list.call_args.kwargs['limit_page_length'], 30)
        with self.assertRaises(ValueError): self.m.customer_query('User', '', 'password', 0, 20)
        self.f.get_list.return_value = []
        with self.assertRaises(PermissionError): self.m.customer_identity('KH-KHONG-CO-QUYEN')
        self.f.db.set_value.assert_not_called()
        self.f.conf['kh_aph_ux_task_first'] = 0
        with self.assertRaises(ValueError): self.m.customer_identity('KH1')


if __name__ == '__main__':
    unittest.main()
