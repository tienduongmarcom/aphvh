"""Bảng ngày phải giữ dấu công nợ, phạm vi và giới hạn đầy đủ dữ liệu."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
from datetime import date


class Row(dict):
    __getattr__=dict.get


class DayClose(unittest.TestCase):
    def setUp(self):
        import kh_aph
        self.package=kh_aph;self.names=('cash_closing','cash_handover','factory_handover','day_close')
        self.saved={n:getattr(kh_aph,n,None) for n in self.names}
        self.f=types.ModuleType('frappe');self.f.whitelist=lambda **kw:lambda fn:fn;self.f.ValidationError=ValueError
        self.f.throw=lambda msg,*a:(_ for _ in ()).throw(ValueError(msg));self.f.get_doc=Mock(return_value=Row(check_permission=Mock()))
        self.f.get_list=Mock(return_value=[])
        self.c=types.ModuleType('kh_aph.cash_closing');self.c.guard=Mock()
        self.h=types.ModuleType('kh_aph.cash_handover')
        self.factory=types.ModuleType('kh_aph.factory_handover');self.factory.enabled=lambda:True;self.factory.guard=Mock()
        self.u=types.ModuleType('frappe.utils');self.u.cint=lambda value:int(value or 0);self.u.now_datetime=lambda:'now';self.u.getdate=lambda v=None:date.fromisoformat(str(v)) if v else date(2026,10,19)
        mapping={'frappe':self.f,'frappe.utils':self.u}
        for n,value in [('cash_closing',self.c),('cash_handover',self.h),('factory_handover',self.factory)]:mapping['kh_aph.'+n]=value;setattr(kh_aph,n,value)
        self.patch=patch.dict(sys.modules,mapping);self.patch.start();sys.modules.pop('kh_aph.day_close',None);self.m=importlib.import_module('kh_aph.day_close')
    def tearDown(self):
        sys.modules.pop('kh_aph.day_close',None)
        for n,v in self.saved.items():
            if v is None:
                if hasattr(self.package,n):delattr(self.package,n)
            else:setattr(self.package,n,v)
        self.patch.stop()
    def test_role_flag_and_company_precede_financial_reads(self):
        self.factory.enabled=lambda:False
        with self.assertRaises(ValueError):self.m.review('APH','2026-10-19')
        self.f.get_doc.assert_not_called();self.f.get_list.assert_not_called()
        self.factory.enabled=lambda:True;self.c.guard.side_effect=PermissionError
        with self.assertRaises(PermissionError):self.m.review('APH','2026-10-19')
        self.f.get_list.assert_not_called();self.c.guard.assert_called_with(manager=True)
    def test_limit_is_error_never_truncated_success(self):
        self.f.get_list.return_value=[{}]*(self.m.LIMIT+1)
        with self.assertRaisesRegex(ValueError,'không cắt'):self.m.rows('Account',{},['name'])
        self.assertEqual(self.f.get_list.call_args.kwargs['limit_page_length'],self.m.LIMIT+1)
    def test_customer_debt_keeps_opening_increase_and_decrease_separate(self):
        values=[Row(party='KH',posting_date='2026-10-18',amount=10),Row(party='KH',posting_date='2026-10-19',amount=7),Row(party='KH',posting_date='2026-10-19',amount=-3)]
        self.m.rows=Mock(side_effect=lambda dt,*a,**kw:values if dt=='Payment Ledger Entry' else [])
        result=self.m._debt('APH','2026-10-19')
        self.assertEqual((result[0]['opening'],result[0]['increase'],result[0]['decrease'],result[0]['amount']),(10,7,3,14))
        filters=self.m.rows.call_args_list[0].args[1]
        self.assertEqual(filters,{'company':'APH','party_type':'Customer','delinked':0,'posting_date':['<=','2026-10-19']})
    def test_bank_status_requires_saved_native_allocation_and_scope(self):
        banks=[Row(name='BA',account='bank')]
        tx=[Row(name='matched',bank_account='BA',date='2026-10-19',deposit=10,withdrawal=0,unallocated_amount=0,party=None),Row(name='unknown',bank_account='BA',date='2026-10-19',deposit=12,withdrawal=0,unallocated_amount=12,party=None)]
        self.m.rows=Mock(side_effect=[banks,tx]);result=self.m._bank('APH','2026-10-19')
        self.assertEqual([r['status'] for r in result],['Đã khớp theo sao kê native','Chưa xác định đối tượng'])
        self.f.get_doc.assert_any_call('Bank Account','BA')
        self.assertEqual(self.m.rows.call_args.args[1]['company'],'APH')

    def test_handled_verification_error_keeps_row_but_not_duplicate_popup(self):
        self.f.local=types.SimpleNamespace(message_log=['prior message'])
        def invalid(*args):
            self.f.local.message_log.append('reverify this cash')
            raise ValueError('cần xác minh lại')
        self.c._state=Mock(side_effect=invalid)
        with self.assertRaisesRegex(ValueError,'cần xác minh lại'):
            self.m._position('APH','cash','me')
        self.assertEqual(self.f.local.message_log,['prior message'])
        def forbidden(*args):
            self.f.local.message_log.append('permission denied')
            raise PermissionError('scope')
        self.c._state.side_effect=forbidden
        with self.assertRaises(PermissionError):self.m._position('APH','cash','me')
        self.assertEqual(self.f.local.message_log,['prior message','permission denied'])

    def test_review_keeps_old_day_receipt_pending_until_paper_returns(self):
        issue=types.SimpleNamespace(STATE='issue',ASSIGNEE='assignee',DUE='due')
        paper=types.SimpleNamespace(FILE='photo',ACTOR='reviewer',ORIGINAL_AT='original_at')
        self.f.get_meta=lambda dt:Row(has_field=lambda field:True)
        value=Row(name='DN',docstatus=1,is_return=0,posting_date='2026-10-18',kh_aph_delivery_state='Khách đã nhận',
                  photo='PRIVATE',reviewer='accountant',kh_aph_mau_giao_nhan=1,original_at=None)
        self.m.rows=Mock(return_value=[value])
        item=Row(warehouse='WH',item_code='HANG',stock_qty=5,stock_uom='Kg',kh_aph_bags=0)
        doc=types.SimpleNamespace(items=[item],check_permission=Mock())
        self.f.get_doc.return_value=doc
        with patch.object(self.package,'delivery_issue',issue,create=True), patch.object(self.package,'ho_so_giao_nhan',paper,create=True):
            result=self.m._goods('CONG-TY','2026-10-19')
            self.assertEqual(len(result),1)
            self.assertIn('Thiếu giấy gốc',result[0]['status'])
            value['original_at']='2026-10-19 10:00:00'
            self.assertEqual(self.m._goods('CONG-TY','2026-10-19'),[])

    def test_required_customer_paper_is_independent_and_keeps_old_day_in_work(self):
        issue=types.SimpleNamespace(STATE='issue',ASSIGNEE='assignee',DUE='due')
        paper=types.SimpleNamespace(FILE='photo',ACTOR='reviewer',ORIGINAL_AT='original_at')
        self.f.get_meta=lambda dt:Row(has_field=lambda field:True)
        value=Row(name='DN',docstatus=1,is_return=0,posting_date='2026-10-18',kh_aph_delivery_state='Khách đã nhận',
            photo='WAREHOUSE',reviewer='kt',original_at='2026-10-19',kh_aph_mau_giao_nhan=1,
            kh_aph_cach_giao='Vận chuyển',kh_aph_can_ky_khach='Có')
        self.m.rows=Mock(return_value=[value])
        self.f.get_doc.return_value=types.SimpleNamespace(items=[Row(warehouse='WH',item_code='A',stock_qty=1,stock_uom='Kg')],check_permission=Mock())
        with patch.object(self.package,'delivery_issue',issue,create=True),patch.object(self.package,'ho_so_giao_nhan',paper,create=True):
            self.assertIn('Khách ký: chưa kiểm hồ sơ',self.m._goods('CO','2026-10-19')[0]['status'])
            value['kh_aph_kiem_ky_khach_boi']='kt'
            self.assertIn('Khách ký: thiếu giấy gốc',self.m._goods('CO','2026-10-19')[0]['status'])
            value['kh_aph_nhan_goc_khach_luc']='2026-10-19'
            self.assertEqual(self.m._goods('CO','2026-10-19'),[])
            value['kh_aph_can_ky_khach']='Không';value['kh_aph_kiem_ky_khach_boi']=None;value['kh_aph_nhan_goc_khach_luc']=None
            self.assertEqual(self.m._goods('CO','2026-10-19'),[])
