"""Nhận nhanh không được thành lối gán giá/dấu nguồn hay bỏ qua quyền."""
import importlib
import json
import sys
import types
import unittest
from unittest.mock import Mock, patch
from decimal import Decimal


class Row(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class Receiving(unittest.TestCase):
    def setUp(self):
        self.f = types.ModuleType('frappe')
        self.f.conf = {'kh_aph_factory_receiving': 1, 'kh_aph_quantity_valuation_mvp': 1, 'kh_aph_server_cost_guard': 1}
        self.f.session = Row(user='dung')
        self.f.PermissionError = PermissionError
        self.f.throw = lambda text, exc=ValueError: (_ for _ in ()).throw(exc(text))
        self.f.whitelist = lambda **kw: lambda fn: fn
        self.f.get_roles = lambda: ['Kế toán nhà máy', 'APH Không xem giá vốn']
        self.f.db = Mock(); self.f.db.get_value.return_value = 1
        self.f.parse_json = lambda raw: json.loads(raw) if isinstance(raw, str) else raw
        self.f.get_doc = Mock(); self.f.get_list = Mock()
        utils = types.ModuleType('frappe.utils')
        utils.cint = lambda v: int(v or 0)
        utils.getdate = lambda v: str(v)
        utils.today = lambda: '2026-10-19'
        utils.now_datetime = lambda: '2026-10-19 12:00:00'
        self.patch = patch.dict(sys.modules, {'frappe': self.f, 'frappe.utils': utils})
        self.patch.start()
        import kh_aph.factory_receiving as m
        self.m = importlib.reload(m)

    def tearDown(self):
        self.patch.stop()
        sys.modules.pop('kh_aph.factory_receiving', None)

    def test_disabled_guest_roles_before_sources(self):
        self.f.conf['kh_aph_factory_receiving'] = 0
        with self.assertRaises(ValueError): self.m.preview('PO')
        self.f.conf['kh_aph_factory_receiving'] = 1
        self.f.session.user = 'Guest'
        with self.assertRaises(PermissionError): self.m.preview('PO')
        self.f.session.user = 'sales'; self.f.get_roles = lambda: ['Sales User']
        with self.assertRaises(PermissionError): self.m.preview('PO')
        self.f.get_doc.assert_not_called()

    def test_quantity_finite_six_places_and_whole_bags(self):
        for n in ('NaN', 'Infinity', '-1', '0.0000001', True, None):
            with self.assertRaises(ValueError): self.m._number(n)
        self.assertEqual(self.m._number('0.000001'), Decimal('0.000001'))
        with self.assertRaises(ValueError): self.m._selection([{'source_row':'R','warehouse':'WH','qty':1,'bags':0.5,'quality_qty':0}])

    def test_selection_rejects_forged_prices_duplicates_and_empty(self):
        r = {'source_row': 'R', 'warehouse': 'WH', 'qty': 5, 'bags': 0, 'quality_qty': 0}
        for rows in ([], [r,r], [{**r,'rate':1}], [{**r,'source_row':''}]):
            with self.assertRaises(ValueError): self.m._selection(rows)
        self.assertEqual(self.m._selection([r]), self.m._selection([{**r,'qty':'5.000000'}]))

    def test_warehouse_company_permission_not_only_role(self):
        wh = Row(company='VH', disabled=0, is_group=0, check_permission=Mock())
        self.f.get_doc.return_value = wh
        with self.assertRaises(ValueError): self.m._warehouse('WH','APH')
        wh.company='APH';wh.check_permission.side_effect=PermissionError('kho')
        with self.assertRaises(PermissionError): self.m._warehouse('WH','APH')

    def test_preview_allows_only_quantity_fields(self):
        row=Row(name='R',qty=10,received_qty=3,item_code='A',warehouse='WH')
        self.m._source=Mock(return_value=types.SimpleNamespace(name='PO',company='APH',supplier='NCC',items=[row],get=lambda key:1 if key=='kh_aph_gia_tam' else None))
        self.m._item=Mock(return_value=Row(kh_aph_kg_per_bag=0));self.m._warehouse=Mock()
        got=self.m.preview('PO')
        self.assertEqual(got['items'][0]['remaining'],7)
        self.assertNotIn('rate',json.dumps(got))
        self.assertEqual(got['price_mode'],'Giá tạm theo đơn mua')

    def test_stamp_cannot_be_forged_even_if_flag_off(self):
        self.f.conf['kh_aph_factory_receiving']=0
        doc=Row(kh_aph_receiving_request='fake',kh_aph_receiving_payload='fake',is_new=lambda:True,set=Mock())
        with self.assertRaises(ValueError):self.m.protect(doc)
        self.f.conf['kh_aph_factory_receiving']=1
        old=Row(kh_aph_receiving_request='real',kh_aph_receiving_note='ký cũ')
        doc=Row(old);doc.update(is_new=lambda:False,get_doc_before_save=lambda:old,kh_aph_receiving_note='đổi')
        with self.assertRaises(ValueError):self.m.protect(doc)
        with self.assertRaises(ValueError):self.m.prevent_delete(old)

    def test_native_blank_unique_key_normalized(self):
        d=Row(is_new=lambda:True,set=Mock())
        self.m.protect(d)
        d.set.assert_called_once_with('kh_aph_receiving_request',None)

    def test_ticket_must_be_private_unique_owned_and_unbound(self):
        self.f.get_list.return_value=[]
        with self.assertRaises(ValueError):self.m._claim_ticket('/files/public.pdf')
        file=Row(owner='other',attached_to_name=None,check_permission=Mock())
        self.f.get_list.return_value=['F'];self.f.get_doc.return_value=file
        with self.assertRaises(ValueError):self.m._claim_ticket('/private/files/a.pdf')
        file.owner='dung';file.attached_to_name='PR-other'
        with self.assertRaises(ValueError):self.m._claim_ticket('/private/files/a.pdf')
        file.attached_to_name=None
        self.assertIs(self.m._claim_ticket('/private/files/a.pdf'),file)

    def test_retry_uses_current_lookup_after_company_and_po_locks(self):
        self.m.guard=Mock()
        self.m._source=Mock(return_value=Row(company='APH'))
        self.f.db.sql.side_effect=[[],[],[['PR']]]
        old=Row(name='PR',docstatus=1,kh_aph_receiving_payload='hash',check_permission=Mock())
        self.f.get_doc.return_value=old
        row={'source_row':'R','warehouse':'WH','qty':4,'bags':0,'quality_qty':0}
        with patch.object(self.m.hashlib,'sha256',return_value=Mock(hexdigest=lambda:'hash')):
            result=self.m.receive('PO','nonce',[row],'2026-10-19','Người ký')
        self.assertEqual(result['name'],'PR')
        self.assertIn('tabCompany',self.f.db.sql.call_args_list[0].args[0])
        self.assertIn('tabPurchase Order',self.f.db.sql.call_args_list[1].args[0])
        self.assertIn('FOR UPDATE',self.f.db.sql.call_args_list[2].args[0])
        self.m._source.assert_called_with('PO',state=False,lock=True)
        self.f.get_doc.assert_called_once_with('Purchase Receipt','PR',for_update=True)

    def test_readonly_time_and_quantity_survive_native_json_roundtrip(self):
        from datetime import datetime
        old=Row(kh_aph_receiving_at=datetime(2026,10,19,12),kh_aph_receiving_request='real',items=[Row(name='R',kh_aph_receiving_quality_qty=1)])
        doc=Row(old);doc.update(is_new=lambda:False,get_doc_before_save=lambda:old,
            kh_aph_receiving_at='2026-10-19 12:00:00',items=[Row(name='R',kh_aph_receiving_quality_qty='1.0')])
        self.m.protect(doc)
        doc['items'][0]['kh_aph_receiving_quality_qty']=2
        with self.assertRaises(ValueError):self.m.protect(doc)
