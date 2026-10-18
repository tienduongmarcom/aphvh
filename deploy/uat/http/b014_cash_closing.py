"""Xác minh/chốt ca 2B trên quỹ giả riêng; không dùng tiền thật."""
import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import uuid
H = 'kh_aph_nguoi_giu_tien'
O, S = 'APH Xac minh quy', 'APH Chot ca tien'


def chay(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit):
    def call(method, args): return rpc('kh_aph.cash_closing.'+method, args, ktt)
    original = get('Account', f['acc']['tien'], ktt)
    account = insert({'doctype':'Account', 'account_name':f['p']+'-Chot-ca', 'company':f['aph'],
        'parent_account':original['parent_account'], 'account_type':'Cash', 'account_currency':'VND', 'is_group':0}, ktt)['name']
    args = {'company':f['aph'], 'account':account}
    def counts(): return {dt:len(lst(dt, {}, ['name'], ktt)) for dt in ('GL Entry','Payment Ledger Entry','Payment Entry','Journal Entry')}
    def je(amount, holder=None, date=None):
        return submit(insert({'doctype':'Journal Entry','company':f['aph'],'posting_date':date or f['date'], 'accounts':[
            {'account':account,'debit_in_account_currency':amount,H:holder},
            {'account':f['acc']['cp'],'credit_in_account_currency':amount}]},ktt),ktt)
    def opening(a=700, b=200, unknown=100):
        return insert({'doctype':O,**args,'reason':'UAT kiểm đếm có căn cứ, không sửa sổ',
            'allocations':[{'holder':f['ktt'],'amount':a},{'holder':f['ktt2'],'amount':b}], 'unverified_amount':unknown},ktt)
    def shift(amount, **kw):
        return insert({'doctype':S,**args,'holder':f['ktt'],'counted_amount':amount,**kw}, ktt)
    je(1000)
    before=counts()
    draft=opening()
    denied(lambda:rpc('frappe.client.save',{'doc':json.dumps({**draft,'evidence':'/files/public.txt'})},ktt),text='Tệp kiểm đếm phải riêng tư')
    evidence=insert({'doctype':'File','file_name':'kiem-dem-'+uuid.uuid4().hex+'.txt','is_private':1,
        'attached_to_doctype':O,'attached_to_name':draft['name'],'content':json.dumps({'uat':'kiem-dem'})},ktt)
    draft=rpc('frappe.client.save',{'doc':json.dumps({**draft,'evidence':evidence['file_url']})},ktt)
    denied(lambda:submit({**draft,'unverified_amount':101},ktt),text='phải bằng đúng')
    confirmed=submit(draft,ktt)
    assert confirmed['gl_balance']==1000 and confirmed['unverified_amount']==100
    assert call('current',args)['expected_amount']==700 and counts()==before
    denied(lambda:rpc('frappe.client.delete',{'doctype':'File','name':evidence['name']},ktt))
    assert ktt(evidence['file_url'])=={'uat':'kiem-dem'}
    denied(lambda:rpc('frappe.client.save',{'doc':json.dumps({**get('File',evidence['name'],ktt),'is_private':0})},ktt))
    emit('HTTP_2B_VERIFY_BALANCED_NO_GL','PASS',{'balance':1000,'known':900,'unknown':100,'no_gl_ple':True})
    denied(lambda: submit(shift(680), ktt), text='Ca lệch phải có')
    draft_close=shift(680,reason='UAT thiếu tiền cần điều tra',assignee=f['ktt2'],due_date=f['date'])
    result=call('close',{'name':draft_close['name']})
    assert result['difference']==-20 and result['status']=='Có chênh lệch'
    assert call('close',{'name':draft_close['name']})==result
    assert call('current',args)['expected_amount']==700
    denied(lambda:rpc('frappe.client.cancel',{'doctype':S,'name':draft_close['name']},ktt))
    denied(lambda:rpc('frappe.client.set_value',{'doctype':S,'name':draft_close['name'],'fieldname':'counted_amount','value':700},ktt))
    assert get(S,draft_close['name'],ktt)['counted_amount']==680 and counts()==before
    emit('HTTP_2B_SHIFT_DIFFERENCE_RETRY_IMMUTABLE','PASS',{'difference':-20,'same_result_on_retry':True,'no_gl_ple':True})
    stale=shift(700)
    known=je(100,f['ktt']); je(50)
    assert call('current',args)['expected_amount']==800
    denied(lambda:call('close',{'name':stale['name']}),text='Sổ đã đổi')
    first,second=shift(800),shift(800)
    before=counts()
    sessions=[phien(f['ktt']), phien(f['ktt'])]
    def send(index):
        try: return ('ok',rpc('kh_aph.cash_closing.close',{'name':first['name']},sessions[index]))
        except urllib.error.HTTPError as exc: return ('error',exc.read().decode())
    with ThreadPoolExecutor(max_workers=2) as pool: replies=list(pool.map(send,range(2)))
    assert all(r[0]=='ok' for r in replies),replies
    assert replies[0][1]==replies[1][1]
    denied(lambda:call('close',{'name':second['name']}),text='Ca khác đã chốt')
    assert counts()==before
    emit('HTTP_2B_SHIFT_CONCURRENT_STALE','PASS',{'two_sessions_one_close':True,'second_draft_denied':True,'stale_ledger_denied':True})
    rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':known['name']},ktt)
    denied(lambda:call('current',args),text='Sổ trước ca đã chốt đã đổi')
    assert get(S,first['name'],ktt)['expected_amount']==800
    fresh=submit(opening(700,200,150),ktt)
    assert fresh['previous_verification']==confirmed['name'] and fresh['gl_balance']==1050
    assert call('current',args)['expected_amount']==700
    final=shift(710,reason='UAT đếm thừa',assignee=f['ktt2'],due_date=f['date'])
    assert call('close',{'name':final['name']})['difference']==10
    ordinary=phien(f['ktt2'])
    own=insert({'doctype':S,**args,'holder':f['ktt2'],'counted_amount':200},ordinary)
    assert rpc('kh_aph.cash_closing.close',{'name':own['name']},ordinary)['difference']==0
    denied(lambda:get(O,fresh['name'],ordinary),('PermissionError',))
    yesterday=(datetime.date.fromisoformat(f['date'])-datetime.timedelta(days=1)).isoformat()
    je(5,f['ktt'],yesterday)
    denied(lambda:call('current',args),text='ghi lùi ngày')
    emit('HTTP_2B_CANCEL_BACKDATE_REVERIFY','PASS',{'old_close_preserved':True,'new_verification_linked':True,'backdate_detected':True})
    denied(lambda:rpc('kh_aph.cash_closing.current',args,phien(f['dung'])),('PermissionError',))
    denied(lambda:rpc('kh_aph.cash_closing.current',{**args,'company':f['vh']},phien(f['scope_co'])),('PermissionError',))
    denied(lambda:insert({'doctype':S,**args,'holder':f['ktt2'],'counted_amount':0},ktt),('PermissionError',))
    denied(lambda:rpc('kh_aph.cash_closing.close',{'name':first['name']},phien(f['ktt2'])),('PermissionError',))
    denied(lambda:rpc('frappe.client.get',{'doctype':S,'name':first['name']},phien(f['ktt2'])),('PermissionError',))
    proof=json.loads(get(S,first['name'],ktt)['source_rows'])
    assert proof and all(len(v)==64 for v in proof.values()) and f['ktt2'] not in json.dumps(proof)
    emit('HTTP_2B_PERMISSION_SELF_SCOPE','PASS',{'no_cost_denied':True,'company_scope':True,'self_close_only':True,'other_shift_hidden':True,'proof_contains_no_amount':True})
    import os
    if os.environ.get('GITHUB_ACTIONS'):
        import subprocess
        from pathlib import Path
        proc=subprocess.run(['node',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),first['name'],'chot-ca'],text=True,capture_output=True,timeout=150)
        assert proc.returncode==0,(proc.stdout[-2000:],proc.stderr[-2000:])
        for line in proc.stdout.splitlines():
            if line.startswith('{"case":'):
                value=json.loads(line);emit(value['case'],value['status'],value.get('detail'))
