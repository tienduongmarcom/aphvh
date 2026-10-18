"""Bàn giao trên quỹ giả; số lần ghi GL/PLE và trách nhiệm đều phải đối chiếu."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
import urllib.error

DT='APH Ban giao tien'
H='kh_aph_nguoi_giu_tien'
J='kh_aph_ban_giao_tien'


def chay(rpc,get,insert,submit,lst,denied,ktt,f,phien,emit):
    recipient=phien(f['ktt2'])
    def call(method,args,caller=ktt):return rpc('kh_aph.cash_handover.'+method,args,caller)
    def counts():return {dt:len(lst(dt,{},['name'],ktt)) for dt in ['GL Entry','Payment Ledger Entry','Payment Entry','Journal Entry']}
    parent=get('Account',f['acc']['tien'],ktt)['parent_account']
    def account(suffix):return insert({'doctype':'Account','account_name':f['p']+'-BG-'+suffix,'company':f['aph'],'parent_account':parent,'account_type':'Cash','account_currency':'VND','is_group':0},ktt)['name']
    def journal(account,amount,holder=None):
        return submit(insert({'doctype':'Journal Entry','company':f['aph'],'posting_date':f['date'],'accounts':[
            {'account':account,'debit_in_account_currency':max(amount,0),'credit_in_account_currency':max(-amount,0),H:holder},
            {'account':f['acc']['cp'],'debit_in_account_currency':max(-amount,0),'credit_in_account_currency':max(amount,0)}]},ktt),ktt)
    def verify(account,a=0,b=0,unknown=0):
        return submit(insert({'doctype':'APH Xac minh quy','company':f['aph'],'account':account,'reason':'UAT xác minh bàn giao',
            'allocations':[{'holder':f['ktt'],'amount':a},{'holder':f['ktt2'],'amount':b}], 'unverified_amount':unknown},ktt),ktt)
    def wallet(account,caller=ktt):return rpc('kh_aph.cash_closing.current',{'company':f['aph'],'account':account},caller)
    def draft(source,dest,amount,receiver=None):return insert({'doctype':DT,'company':f['aph'],'from_account':source,'to_account':dest,
        'from_holder':f['ktt'],'to_holder':receiver or f['ktt2'],'requested_amount':amount,'reason':'UAT bàn giao có căn cứ'},ktt)
    def send(source,dest,amount,receiver=None):
        doc=draft(source,dest,amount,receiver);call('send',{'name':doc['name']});return doc
    source=account('same');journal(source,1000);verify(source,700,200,100)
    before=counts();first=draft(source,source,50)
    evidence=insert({'doctype':'File','file_name':first['name']+'.txt','is_private':1,'attached_to_doctype':DT,
        'attached_to_name':first['name'],'content':json.dumps({'uat':'ban-giao-tien'})},ktt)
    first=rpc('frappe.client.save',{'doc':json.dumps({**first,'evidence':evidence['file_url']})},ktt)
    call('send',{'name':first['name']})
    assert wallet(source)['expected_amount']==700 and wallet(source)['reserved_amount']==50 and wallet(source)['available_amount']==650
    assert wallet(source,recipient)['expected_amount']==200
    denied(lambda:call('receive',{'name':first['name'],'amount':50}),('PermissionError',))
    denied(lambda:rpc('kh_aph.cash_handover.receive',{'name':first['name'],'amount':50}),('PermissionError',))
    denied(lambda:insert({'doctype':DT,'company':f['aph'],'from_account':source,'to_account':source,
        'from_holder':f['ktt'],'to_holder':f['ktt'],'requested_amount':1,'reason':'UAT tự nhận'},ktt),text='phải khác nhau')
    call('receive',{'name':first['name'],'amount':50},recipient)
    denied(lambda:rpc('frappe.client.delete',{'doctype':'File','name':evidence['name']},ktt))
    assert ktt(evidence['file_url'])=={'uat':'ban-giao-tien'}
    assert wallet(source)['expected_amount']==650 and wallet(source,recipient)['expected_amount']==250 and counts()==before
    stale=insert({'doctype':'APH Chot ca tien','company':f['aph'],'account':source,'holder':f['ktt'],'counted_amount':650},ktt)
    second=send(source,source,20);call('receive',{'name':second['name'],'amount':20},recipient)
    denied(lambda:rpc('kh_aph.cash_closing.close',{'name':stale['name']},ktt),text='Trách nhiệm tiền đã đổi')
    emit('HTTP_2B_HANDOVER_SAME_CASH','PASS',{'reservation_only_until_receive':True,'no_gl_ple':True,'no_self_or_manager_proxy':True,'shift_snapshot_stale':True})
    short=send(source,source,100)
    denied(lambda:verify(source,630,270,100),text='bàn giao chờ nhận')
    args={'name':short['name'],'amount':95,'reason':'UAT thực nhận thiếu5','assignee':f['ktt'],'due_date':f['date']}
    before=counts();result=call('receive',args,recipient)
    assert result['difference']==-5 and result['status']=='Có chênh lệch'
    assert call('receive',args,recipient)==result
    denied(lambda:call('receive',{**args,'amount':96},recipient),text='nội dung khác')
    assert wallet(source)['expected_amount']==535 and wallet(source,recipient)['expected_amount']==365
    denied(lambda:call('send',{'name':draft(source,source,1)['name']}),text='chênh lệch chưa xử lý')
    assert counts()==before
    emit('HTTP_2B_HANDOVER_SHORT_RETRY','PASS',{'actual_95_not_100':True,'retry_same_result':True,'changed_payload_denied':True,'dispute_blocks_outgoing':True,'no_gl_ple':True})
    source2,dest=account('source'),account('dest');journal(source2,1000);verify(source2,1000);verify(dest)
    moved=send(source2,dest,100);before=counts();result=call('receive',{'name':moved['name'],'amount':100},recipient)
    after=counts();assert after['GL Entry']==before['GL Entry']+2 and after['Journal Entry']==before['Journal Entry']+1
    assert after['Payment Ledger Entry']==before['Payment Ledger Entry'] and after['Payment Entry']==before['Payment Entry']
    assert wallet(source2)['expected_amount']==900 and wallet(dest,recipient)['expected_amount']==100
    je=get('Journal Entry',result['journal_entry'],ktt)
    assert {r['account'] for r in je['accounts']}=={source2,dest} and all(not r.get('party') for r in je['accounts'])
    assert next(r for r in je['accounts'] if r['account']==source2)[H]==f['ktt']
    assert next(r for r in je['accounts'] if r['account']==dest)[H]==f['ktt2']
    denied(lambda:rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':je['name']},ktt))
    denied(lambda:rpc('frappe.client.set_value',{'doctype':'Journal Entry','name':je['name'],'fieldname':J,'value':''},ktt))
    denied(lambda:call('cancel',{'name':moved['name']}),text='đã nhận không được hủy')
    emit('HTTP_2B_HANDOVER_NATIVE_CASH','PASS',{'one_native_transfer':True,'not_counted_twice':True,'no_customer_or_revenue':True,'linked_je_protected':True})
    bank=send(source2,f['acc']['bank'],500);before=counts();result=call('receive',{'name':bank['name'],'amount':500},recipient)
    after=counts();assert after['GL Entry']==before['GL Entry']+2 and after['Payment Ledger Entry']==before['Payment Ledger Entry']
    assert wallet(source2)['expected_amount']==400
    assert {r['account'] for r in get('Journal Entry',result['journal_entry'],ktt)['accounts']}=={source2,f['acc']['bank']}
    emit('HTTP_2B_HANDOVER_TO_BANK','PASS',{'native_cash_to_bank_only':True,'source_holder_reduced_once':True,'no_ple':True})
    pending=send(source2,dest,200);assert wallet(source2)['available_amount']==200
    call('cancel',{'name':pending['name']});assert call('cancel',{'name':pending['name']})['status']=='Đã hủy'
    assert wallet(source2)['available_amount']==400
    choices=[draft(source2,dest,300),draft(source2,dest,300)];sessions=[phien(f['ktt']),phien(f['ktt'])]
    def attempt(i):
        try:return ('ok',call('send',{'name':choices[i]['name']},sessions[i]))
        except urllib.error.HTTPError as exc:
            body=json.loads(exc.read());assert body['exc_type']=='ValidationError',body
            return ('denied',body['exc_type'])
    with ThreadPoolExecutor(max_workers=2) as pool:answers=list(pool.map(attempt,range(2)))
    assert sorted(r[0] for r in answers)==['denied','ok'],answers
    winner=next(r[1] for r in answers if r[0]=='ok')
    before=counts();recipients=[phien(f['ktt2']),phien(f['ktt2'])]
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies=list(pool.map(lambda i:call('receive',{'name':winner['name'],'amount':300},recipients[i]),range(2)))
    assert replies[0]==replies[1] and counts()['Journal Entry']==before['Journal Entry']+1
    assert wallet(source2)['expected_amount']==100
    emit('HTTP_2B_HANDOVER_CONCURRENT','PASS',{'cancel_releases_source':True,'two_requests_one_reservation':True,'two_receivers_one_je':True})
    over_source=account('over');journal(over_source,100);verify(over_source,100)
    over=send(over_source,over_source,50);journal(over_source,-90,f['ktt']);before=counts()
    args={'name':over['name'],'amount':50,'reason':'UAT đã chi tiền trước nhận','assignee':f['ktt'],'due_date':f['date']}
    result=call('receive',args,recipient)
    assert result['status']=='Vượt nguồn cần xử lý' and result['received_amount']==50 and not result['journal_entry']
    assert wallet(over_source)['expected_amount']==10 and wallet(over_source,recipient)['expected_amount']==0 and counts()==before
    call('cancel',{'name':over['name']})
    denied(lambda:rpc('kh_aph.cash_handover.send',{'name':first['name']},phien(f['dung'])),('PermissionError',))
    denied(lambda:insert({'doctype':DT,'company':f['vh'],'from_account':source2,'to_account':dest,'from_holder':f['scope_co'],'to_holder':f['ktt2'],'requested_amount':1,'reason':'ngoài phạm vi'},phien(f['scope_co'])),('PermissionError',))
    emit('HTTP_2B_HANDOVER_OVER_SOURCE','PASS',{'count_saved_without_transfer':True,'money_not_invented':True,'scope_and_no_cost':True})
    if os.environ.get('GITHUB_ACTIONS'):
        import subprocess
        from pathlib import Path
        ui=send(source2,dest,20,'Administrator')
        proc=subprocess.run(['node',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),ui['name'],'ban-giao-tien'],text=True,capture_output=True,timeout=180)
        assert proc.returncode==0,(proc.stdout[-2500:],proc.stderr[-2500:])
        for line in proc.stdout.splitlines():
            if line.startswith('{"case":'):
                value=json.loads(line);emit(value['case'],value['status'],value.get('detail'))
