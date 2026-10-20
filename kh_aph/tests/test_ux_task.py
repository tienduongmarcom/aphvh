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
        self.assertEqual(name, 'Việc bán hàng')
        content = json.loads(self.ws['content'])
        headers = [c['data']['text'] for c in content if c['type'] == 'header']
        self.assertEqual(len(headers), 3)
        labels = [s['label'] for s in self.ws['shortcuts']]
        self.assertEqual(len(labels), len(set(labels)))
        shortcut_names = {c['data']['shortcut_name'] for c in content if c['type'] == 'shortcut'}
        self.assertEqual(shortcut_names, set(labels))
        self.assertTrue(any(s.get('stats_filter') for s in self.ws['shortcuts']))
        self.assertNotIn('Trung tâm', name)

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

    def test_next_step_js_only_clicks_existing_buttons(self):
        js = (pathlib.Path(__file__).resolve().parents[1] / 'public/js/ux_buoc_tiep.js').read_text(encoding='utf-8')
        self.assertNotIn('frappe.call', js)
        self.assertNotIn('"Xuất và In"', js)
        self.assertIn('Lập phiếu xuất & In', js)


if __name__ == '__main__':
    unittest.main()
