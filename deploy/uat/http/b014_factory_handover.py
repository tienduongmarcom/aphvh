"""Luồng quỹ nhà máy/cá nhân/chốt ngày trên dữ liệu giả, cờ25 bật riêng cuối bộ."""
import json
import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOLDER='kh_aph_nguoi_giu_tien'
FDT='APH Phieu quy nha may'
HDT='APH Ban giao tien'
SHIFT='APH Chot ca tien'


def chay(rpc,get,insert,submit,lst,denied,ktt,f,phien,emit,feature):
    dung=phien(f['dung'])
    def counts(): return {dt:len(lst(dt,{},['name'],ktt)) for dt in ('Journal Entry','GL Entry','Payment Entry','Payment Ledger Entry')}
    def account(suffix,kind='Cash'):
        parent=get('Account',f['acc']['bank' if kind=='Bank' else 'tien'],ktt)['parent_account']
        return insert({'doctype':'Account','account_name':f['p']+'-NM-'+suffix,'company':f['aph'],'parent_account':parent,'account_type':kind,'account_currency':'VND','is_group':0},ktt)['name']
    source_account,target,bank=account('nguon'),account('nhan'),account('bank','Bank')
    def journal(acc,amount,holder=None): return submit(insert({'doctype':'Journal Entry','company':f['aph'],'posting_date':f['date'],'accounts':[
        {'account':acc,'debit_in_account_currency':amount,HOLDER:holder},{'account':f['acc']['cp'],'credit_in_account_currency':amount}]},ktt),ktt)
    journal(source_account,1000)
    old=get('Company',f['aph'],ktt).get('kh_aph_quy_nha_may')
    rpc('frappe.client.set_value',{'doctype':'Company','name':f['aph'],'fieldname':'kh_aph_quy_nha_may','value':source_account},ktt)
    def source(amount,target_account=None): return submit(insert({'doctype':FDT,'company':f['aph'],'posting_date':f['date'],'loai':'Bàn giao tiền',
        HOLDER:f['dung'],'nguoi_nhan':f['ktt'],'tai_khoan_nhan':target_account,
        'dong':[{'dien_giai':'UAT chuyển quỹ nhà máy','so_tien':amount}]},dung),dung)
    legacy=source(20)
    old_received=source(5)
    old_result=rpc('kh_aph.factory_cash.xac_nhan_nhan',{'name':old_received['name'],'so_thuc_nhan':5,'tai_khoan_nhan':target},ktt)
    def verify(dung_amount,ktt_amount,unknown):return submit(insert({'doctype':'APH Xac minh quy','company':f['aph'],'account':source_account,'reason':'UAT mốc nhà máy',
        'allocations':[{'holder':f['dung'],'amount':dung_amount},{'holder':f['ktt'],'amount':ktt_amount}],'unverified_amount':unknown},ktt),ktt)
    verify(600,200,195)
    submit(insert({'doctype':'APH Xac minh quy','company':f['aph'],'account':target,'reason':'UAT mốc quỹ nhận',
        'allocations':[{'holder':f['ktt'],'amount':5}],'unverified_amount':0},ktt),ktt)
    def current(caller=dung,acc=source_account): return rpc('kh_aph.personal_cash.current',{'company':f['aph'],'account':acc},caller)
    def hcall(method,args,caller=ktt):return rpc('kh_aph.cash_handover.'+method,args,caller)
    enabled=False
    try:
        denied(lambda:rpc('kh_aph.personal_cash.prepare_shift',{'company':f['aph'],'account':source_account,'request_id':'off','counted_amount':600},dung))
        enabled=True;feature(True)
        assert rpc('kh_aph.factory_cash.xac_nhan_nhan',{'name':old_received['name'],'so_thuc_nhan':5,'tai_khoan_nhan':target},ktt)==old_result
        denied(lambda:rpc('kh_aph.factory_cash.xac_nhan_nhan',{'name':legacy['name'],'so_thuc_nhan':20,'tai_khoan_nhan':target},ktt),text='chuyển tiếp')
        denied(lambda:rpc('kh_aph.factory_handover.connect_pending',{'name':legacy['name'],'tai_khoan_nhan':target},ktt),('PermissionError',))
        denied(lambda:source(1),text='Chọn quỹ')
        emit('HTTP_2B_FACTORY_TRANSITION_OFF_HISTORY','PASS',{'off_path_retained':True,'received_legacy_replays_only':'same','pending_requires_sender_and_reservation':True})

        before=counts()
        handover=rpc('kh_aph.factory_handover.connect_pending',{'name':legacy['name'],'tai_khoan_nhan':target},dung)
        assert handover['status']=='Chờ nhận' and 'journal_entry' not in handover
        assert rpc('kh_aph.factory_handover.connect_pending',{'name':legacy['name'],'tai_khoan_nhan':target},dung)==handover
        assert current()['reserved_amount']==20 and current()['available_amount']==580
        denied(lambda:rpc('kh_aph.factory_handover.connect_pending',{'name':legacy['name'],'tai_khoan_nhan':bank},dung))
        denied(lambda:hcall('receive',{'name':handover['name'],'amount':20},phien(f['ktt2'])),('PermissionError',))
        denied(lambda:get(HDT,handover['name'],dung),('PermissionError',))
        assert counts()==before
        emit('HTTP_2B_FACTORY_RESERVE_SCOPE','PASS',{'one_root':True,'reserved':20,'available':580,'native_h_gl_rights_unchanged':True})

        callers=[phien(f['ktt']),phien(f['ktt'])]
        def accept(i):
            if i:return rpc('kh_aph.factory_cash.xac_nhan_nhan',{'name':legacy['name'],'so_thuc_nhan':20,'tai_khoan_nhan':target},callers[i])
            return hcall('receive',{'name':handover['name'],'amount':20},callers[i])
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(accept,range(2)))
        assert results[0]==results[1],results
        after=counts();assert after['Journal Entry']==before['Journal Entry']+1 and after['GL Entry']==before['GL Entry']+2
        assert after['Payment Entry']==before['Payment Entry'] and after['Payment Ledger Entry']==before['Payment Ledger Entry']
        synced=get(FDT,legacy['name'],ktt)
        assert synced['journal_entry']==results[0]['journal_entry'] and synced['trang_thai']=='Đã nhận'
        assert current()['expected_amount']==580 and current()['reserved_amount']==0
        assert hcall('receive',{'name':handover['name'],'amount':'20.00'})==results[0]
        denied(lambda:hcall('receive',{'name':handover['name'],'amount':21}))
        denied(lambda:rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':synced['journal_entry']},ktt))
        assert counts()==after
        emit('HTTP_2B_FACTORY_TWO_ROUTES_ONE_JE','PASS',{'two_sessions_old_and_native':True,'one_je_two_gl':True,'no_new_customer_receipt_or_debt':True,'source_synced':True})

        reverse=hcall('create_reverse',{'name':handover['name'],'request_id':'factory-return','reason':'UAT trả lại đủ tiền'})
        hcall('receive',{'name':reverse['name'],'amount':20},dung)
        returned=counts();assert returned['Journal Entry']==after['Journal Entry']+1 and returned['GL Entry']==after['GL Entry']+2
        assert returned['Payment Ledger Entry']==after['Payment Ledger Entry'] and current()['expected_amount']==600
        assert get('Journal Entry',synced['journal_entry'],ktt)['docstatus']==1
        again=hcall('receive',{'name':reverse['name'],'amount':20},dung);assert 'journal_entry' not in again
        assert counts()==returned
        emit('HTTP_2B_FACTORY_REVERSE_RESTRICTED','PASS',{'factory_receives_own_return':True,'one_reverse_je':True,'original_kept':True,'no_native_gl_grant':True})

        same=source(30,source_account)
        same_h=get(FDT,same['name'],ktt)['ban_giao_tien']
        before=counts()
        receive_args={'name':same_h,'amount':25,'reason':'UAT thiếu5','assignee':f['ktt2'],'due_date':f['date']}
        hcall('receive',receive_args)
        assert counts()==before and current()['expected_amount']==575 and current()['available_amount']==0
        root=get(HDT,same_h,ktt);assert root['difference']==-5 and root['issue_state']=='Chờ xử lý'
        assert get(FDT,same['name'],ktt)['trang_thai']=='Chênh lệch chờ điều tra'
        denied(lambda:hcall('cancel',{'name':same_h},dung))
        denied(lambda:source(10,target),text='chênh lệch')
        emit('HTTP_2B_FACTORY_SAME_CASH_ISSUE','PASS',{'same_cash_no_je':True,'difference_kept':-5,'outgoing_blocked':True})

        new=verify(575,225,195)
        def prepare(caller,amount,request):return rpc('kh_aph.personal_cash.prepare_shift',{'company':f['aph'],'account':source_account,'request_id':request,'counted_amount':amount},caller)
        draft=prepare(dung,575,'ca-factory')
        assert prepare(dung,'575.00','ca-factory')==draft
        denied(lambda:prepare(dung,576,'ca-factory'))
        denied(lambda:rpc('kh_aph.personal_cash.confirm_shift',{'name':draft['name']},ktt),('PermissionError',))
        shift_before=counts()
        ds=[phien(f['dung']),phien(f['dung'])]
        with ThreadPoolExecutor(max_workers=2) as pool:closed=list(pool.map(lambda i:rpc('kh_aph.personal_cash.confirm_shift',{'name':draft['name']},ds[i]),range(2)))
        assert closed[0]==closed[1] and closed[0]['docstatus']==1 and closed[0]['difference']==0
        assert counts()==shift_before
        denied(lambda:get(SHIFT,draft['name'],dung),('PermissionError',))
        kt_shift=prepare(ktt,225,'ca-ktt-factory');rpc('kh_aph.personal_cash.confirm_shift',{'name':kt_shift['name']},ktt)
        emit('HTTP_2B_FACTORY_OWN_SHIFT','PASS',{'same_request_one_draft':True,'two_confirms_one_shift':True,'own_only':True,'no_gl_or_native_snapshot_grant':True})

        resolution=insert({'doctype':'APH Doi chieu lech tien','source_type':HDT,'source_name':same_h,'result':'UAT xác minh phần chưa giao còn ở người giữ'},ktt)
        file=insert({'doctype':'File','file_name':uuid.uuid4().hex+'.txt','is_private':1,'attached_to_doctype':'APH Doi chieu lech tien','attached_to_name':resolution['name'],'content':'UAT căn cứ kiểm đếm nhà máy'},ktt)
        shifts={f['dung']:draft['name'],f['ktt']:kt_shift['name']}
        resolution=rpc('frappe.client.save',{'doc':json.dumps({**resolution,'evidence':file['file_url'],
            'proofs':[{**r,'verification':new['name'],'shift':shifts[r['holder']]} for r in resolution['proofs']]})},ktt)
        before=counts();rpc('kh_aph.cash_issue.confirm',{'name':resolution['name']},ktt)
        assert get(HDT,same_h,ktt)['issue_state']=='Đã đối chiếu' and current()['available_amount']==575 and counts()==before
        # Hủy đề nghị chưa nhận giải phóng giữ chỗ nhưng không xóa lịch sử.
        pending=source(10,target);pending_h=get(FDT,pending['name'],ktt)['ban_giao_tien']
        assert current()['reserved_amount']==10
        hcall('cancel',{'name':pending_h},dung)
        assert current()['reserved_amount']==0 and counts()==before
        assert get(FDT,pending['name'],ktt)['trang_thai']=='Đã hủy'
        denied(lambda:rpc('frappe.client.delete',{'doctype':HDT,'name':pending_h},ktt))
        emit('HTTP_2B_FACTORY_RESOLVE_CANCEL_AUDIT','PASS',{'new_verification_and_own_counts':True,'issue_closed_without_je':True,'cancel_releases_reservation':True,'history_kept':True})

        deposit=source(10,bank);deposit_h=get(FDT,deposit['name'],ktt)['ban_giao_tien']
        before=counts();hcall('receive',{'name':deposit_h,'amount':10})
        back=hcall('create_reverse',{'name':deposit_h,'request_id':'bank-return','reason':'UAT hoàn đúng quỹ gốc'})
        hcall('receive',{'name':back['name'],'amount':10},dung)
        assert current()['expected_amount']==575 and counts()['Journal Entry']==before['Journal Entry']+2
        assert counts()['Payment Ledger Entry']==before['Payment Ledger Entry']
        emit('HTTP_2B_FACTORY_BANK_AND_RETURN','PASS',{'deposit_and_exact_return':True,'two_transfer_je':True,'no_customer_debt':True})

        stale=prepare(dung,575,'ca-stale')
        change=journal(source_account,1,f['dung']);after_change=counts()
        denied(lambda:rpc('kh_aph.personal_cash.confirm_shift',{'name':stale['name']},dung),text='Sổ đã đổi')
        assert counts()==after_change and get(SHIFT,stale['name'],ktt)['docstatus']==0
        rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':change['name']},ktt)
        assert current()['expected_amount']==575
        emit('HTTP_2B_FACTORY_STALE_SHIFT','PASS',{'ledger_changed_after_preview_denied':True,'no_partial_close_or_ledger':True,'old_draft_preserved':True})

        def browser(mode,payload,actor):
            if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Chrome chỉ chạy UAT dùng một lần')
            result=subprocess.run(['node',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),json.dumps(payload),mode],
                input=json.dumps({'cookies':phien(actor).browser_cookies()}),text=True,capture_output=True,timeout=180)
            assert result.returncode==0,(result.stdout[-1800:],result.stderr[-2200:])
            values=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"case":')]
            assert len(values)==1 and values[0]['status']=='PASS',result.stdout
            emit(values[0]['case'],'PASS',values[0].get('detail'))
            return values[0]
        before=counts();before_shifts=len(lst(SHIFT,{'holder':f['dung']},['name'],ktt))
        web=browser('quy-nha-may',{'source':same['name'],'company':f['aph'],'account':source_account,'user':f['dung'],'amount':575},f['dung'])
        assert counts()==before and len(lst(SHIFT,{'holder':f['dung']},['name'],ktt))==before_shifts+1
        webshift=get(SHIFT,web['detail']['shift'],ktt)
        assert webshift['holder']==f['dung'] and webshift['closed_by']==f['dung'] and webshift['expected_amount']==575 and webshift['counted_amount']==575 and webshift['docstatus']==1

        # Nguồn thật trên site giả cho bảng ngân hàng; sao kê không ghi GL.
        insert_bank=submit(insert({'doctype':'Bank Transaction','company':f['aph'],'bank_account':f['bank_account'],'date':f['date'],'deposit':12,
            'currency':'VND','description':'UAT khoản sao kê chưa xác định'},ktt),ktt)
        before=counts();review=rpc('kh_aph.day_close.review',{'company':f['aph'],'day':f['date']},ktt)
        own=[r for r in review['rows'] if r['group']=='Tiền mặt hiện tại' and r.get('holder')==f['dung'] and r.get('account')==source_account]
        assert len(own)==1 and own[0]['amount']==575 and own[0]['counted']==575
        assert any(r.get('document')==insert_bank['name'] and r['status']=='Chưa xác định đối tượng' for r in review['rows'])
        assert any(r['group']=='Hàng / hồ sơ' and r.get('item_code') for r in review['rows'])
        for row in review['rows']:
            if row['group']=='Công nợ khách': assert row['opening']+row['increase']-row['decrease']==row['amount']
        denied(lambda:rpc('kh_aph.day_close.review',{'company':f['aph'],'day':f['date']},dung),('PermissionError',))
        denied(lambda:rpc('kh_aph.day_close.review',{'company':f['vh'],'day':f['date']},phien(f['scope_co'])),('PermissionError',))
        assert counts()==before
        emit('HTTP_2B_FACTORY_DAY_CLOSE','PASS',{'own_money_last_count':575,'native_unidentified_bank':True,'goods_and_debt':True,'restricted_and_company_scope':True,'read_only':True})
        # Cửa hàng vẫn chốt ngày khi tắt riêng cầu nối Nhà máy.
        feature(False)
        store_review=rpc('kh_aph.day_close.review',{'company':f['aph'],'day':f['date']},ktt)
        assert not any(r['group']=='Chuyển tiếp nhà máy' for r in store_review['rows'])
        assert any(r.get('document')==insert_bank['name'] for r in store_review['rows'])
        denied(lambda:rpc('kh_aph.day_close.review',{'company':f['aph'],'day':f['date']},dung),('PermissionError',))
        browser('chot-ngay',{'company':f['aph'],'day':f['date'],'user':f['ktt']},f['ktt'])
        assert counts()==before
    finally:
        if enabled:feature(False)
        rpc('frappe.client.set_value',{'doctype':'Company','name':f['aph'],'fieldname':'kh_aph_quy_nha_may','value':old or ''},ktt)
