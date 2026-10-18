"""Đối chiếu/hoàn trên quỹ giả tách biệt; không sửa tiền hoặc hồ sơ gốc."""
import json
import os
import uuid
import urllib.error
from concurrent.futures import ThreadPoolExecutor

H, O, S, R = 'APH Ban giao tien', 'APH Xac minh quy', 'APH Chot ca tien', 'APH Doi chieu lech tien'
HOLDER = 'kh_aph_nguoi_giu_tien'


def chay(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit):
    recipient = phien(f['ktt2'])
    def call(method, args, caller=ktt): return rpc('kh_aph.cash_handover.'+method,args,caller)
    def confirm(doc, caller=ktt):
        rpc('kh_aph.cash_issue.confirm',{'name':doc['name']},caller)
        return get(R,doc['name'],caller)
    def counts(): return {dt:len(lst(dt,{},['name'],ktt)) for dt in ['Journal Entry','GL Entry','Payment Ledger Entry','Payment Entry']}
    def account(suffix, kind='Cash'):
        parent=get('Account',f['acc']['bank' if kind=='Bank' else 'tien'],ktt)['parent_account']
        return insert({'doctype':'Account','account_name':f['p']+'-HL-'+suffix,'company':f['aph'],'parent_account':parent,'account_type':kind,'account_currency':'VND','is_group':0},ktt)['name']
    def je(acc, amount, holder=None, caller=ktt):
        return submit(insert({'doctype':'Journal Entry','company':f['aph'],'posting_date':f['date'],'accounts':[
            {'account':acc,'debit_in_account_currency':max(0,amount),'credit_in_account_currency':max(0,-amount),HOLDER:holder},
            {'account':f['acc']['cp'],'credit_in_account_currency':max(0,amount),'debit_in_account_currency':max(0,-amount)}]},caller),caller)
    def verify(acc,a,b=0):return submit(insert({'doctype':O,'company':f['aph'],'account':acc,'reason':'UAT kiểm lại sau điều tra',
        'allocations':[{'holder':f['ktt'],'amount':a},{'holder':f['ktt2'],'amount':b}],'unverified_amount':0},ktt),ktt)
    def shift(acc, amount, caller=ktt, **kw):
        holder=f['ktt'] if caller is ktt else f['ktt2']
        d=insert({'doctype':S,'company':f['aph'],'account':acc,'holder':holder,'counted_amount':amount,**kw},caller)
        rpc('kh_aph.cash_closing.close',{'name':d['name']},caller)
        return get(S,d['name'],caller)
    def wallet(acc, caller=ktt):return rpc('kh_aph.cash_closing.current',{'company':f['aph'],'account':acc},caller)
    def transfer(acc,dest,planned,actual=None):
        d=insert({'doctype':H,'company':f['aph'],'from_account':acc,'to_account':dest,'from_holder':f['ktt'],'to_holder':f['ktt2'],'requested_amount':planned,'reason':'UAT giao có căn cứ'},ktt)
        call('send',{'name':d['name']})
        args={'name':d['name'],'amount':planned if actual is None else actual}
        if actual is not None and actual!=planned:args.update(reason='UAT thiếu tiền cần đối chiếu',assignee=f['ktt'],due_date=f['date'])
        call('receive',args,recipient)
        return get(H,d['name'],ktt)
    def resolution(source,dt=H):return insert({'doctype':R,'source_type':dt,'source_name':source['name'],'result':'UAT tìm thấy khoản chưa giao, kiểm đếm và xác minh lại có căn cứ'},ktt)
    def evidence(doc):
        file=insert({'doctype':'File','file_name':uuid.uuid4().hex+'.txt','is_private':1,'attached_to_doctype':R,'attached_to_name':doc['name'],'content':json.dumps({'uat':'doi-chieu-lech'})},ktt)
        return rpc('frappe.client.save',{'doc':json.dumps({**doc,'evidence':file['file_url']})},ktt), file
    def proof(doc, verification, shifts):
        rows=[{**r,'verification':verification['name'],'shift':shifts[r['holder']]['name']} for r in doc['proofs']]
        return rpc('frappe.client.save',{'doc':json.dumps({**doc,'proofs':rows})},ktt)
    acc=account('resolve');je(acc,1000);old=verify(acc,1000)
    original=transfer(acc,acc,100,95);before=counts();draft=resolution(original)
    assert len(draft['proofs'])==2 and wallet(acc)['available_amount']==0
    denied(lambda:confirm(draft,ktt),text='căn cứ riêng tư')
    draft,file=evidence(draft)
    clean={f['ktt']:shift(acc,905),f['ktt2']:shift(acc,95,recipient)}
    draft=proof(draft,old,clean)
    denied(lambda:confirm(draft,ktt),text='mốc xác minh mới')
    new=verify(acc,905,95);clean={f['ktt']:shift(acc,905),f['ktt2']:shift(acc,95,recipient)}
    draft=proof(draft,new,clean)
    denied(lambda:confirm(draft,recipient),('PermissionError',))
    denied(lambda:confirm(draft,phien(f['dung'])),('PermissionError',))
    resolved=confirm(draft,ktt)
    source=get(H,original['name'],ktt)
    assert source['issue_state']=='Đã đối chiếu' and source['issue_resolution']==resolved['name']
    assert (source['received_amount'],source['difference'],source['status'])==(95,-5,'Có chênh lệch')
    assert wallet(acc)['available_amount']==905 and wallet(acc,recipient)['available_amount']==95 and counts()==before
    denied(lambda:rpc('frappe.client.set_value',{'doctype':H,'name':source['name'],'fieldname':'difference','value':0},ktt))
    emit('HTTP_2B_ISSUE_RESOLVE_PROOF','PASS',{'new_verification_and_clean_each_holder':True,'old_values_preserved':True,'no_gl_ple':True,'role_guard':True})
    rpc('kh_aph.cash_issue.reopen',{'name':resolved['name']},ktt)
    denied(lambda:rpc('frappe.client.delete',{'doctype':R,'name':resolved['name']}))
    assert wallet(acc)['disputed'] and wallet(acc,recipient)['available_amount']==0 and counts()==before
    denied(lambda:rpc('frappe.client.delete',{'doctype':'File','name':file['name']},ktt))
    assert ktt(file['file_url'])=={'uat':'doi-chieu-lech'}
    denied(lambda:rpc('frappe.client.set_value',{'doctype':H,'name':original['name'],'fieldname':'issue_state','value':'Đã đối chiếu'},ktt))
    emit('HTTP_2B_ISSUE_REOPEN_AUDIT','PASS',{'reopen_blocks_wallet':True,'evidence_survives_cancel':True,'no_gl_ple':True})
    choices=[]
    for i in range(2):
        d,reused=evidence(resolution(original))
        assert reused['file_url']==file['file_url'] and ktt(file['file_url'])=={'uat':'doi-chieu-lech'}
        choices.append(proof(d,new,clean))
    sessions=[phien(f['ktt']),phien(f['ktt'])]
    def resolve_at(i):
        try:return ('ok',confirm(choices[i],sessions[i]))
        except urllib.error.HTTPError as exc:
            body=json.loads(exc.read());assert body['exc_type'] in ('ValidationError',),body
            return ('denied',body['exc_type'])
    with ThreadPoolExecutor(max_workers=2) as pool:answers=list(pool.map(resolve_at,range(2)))
    assert sorted(a[0] for a in answers)==['denied','ok'],answers
    assert len(lst(R,{'source_type':H,'source_name':original['name'],'docstatus':1},['name'],ktt))==1
    emit('HTTP_2B_ISSUE_CONCURRENT','PASS',{'two_results_one_confirmed':True,'wallet_released_once':True})
    ca=account('shift');je(ca,100);verify(ca,100)
    mismatch=shift(ca,90,reason='UAT đếm thiếu10',assignee=f['ktt'],due_date=f['date'])
    v=verify(ca,100);clean_ca=shift(ca,100);d,unused=evidence(resolution(mismatch,S));d=proof(d,v,{f['ktt']:clean_ca})
    je(ca,1,f['ktt']);denied(lambda:confirm(d,ktt),text='Sổ hoặc trách nhiệm đã đổi')
    v=verify(ca,101);clean_ca=shift(ca,101);d=proof(d,v,{f['ktt']:clean_ca});before=counts();confirm(d,ktt)
    assert wallet(ca)['available_amount']==101 and get(S,mismatch['name'],ktt)['counted_amount']==90 and counts()==before
    emit('HTTP_2B_ISSUE_SHIFT_AND_STALE','PASS',{'shift_difference_kept':True,'stale_proof_denied':True,'new_count_required':True})
    over=account('cancelled');je(over,100);verify(over,100)
    pending=insert({'doctype':H,'company':f['aph'],'from_account':over,'to_account':over,'from_holder':f['ktt'],'to_holder':f['ktt2'],'requested_amount':50,'reason':'UAT nguồn đã chi'},ktt)
    call('send',{'name':pending['name']});je(over,-90,f['ktt'])
    call('receive',{'name':pending['name'],'amount':50,'reason':'UAT vượt nguồn','assignee':f['ktt'],'due_date':f['date']},recipient)
    denied(lambda:resolution(pending),text='Nhận hoặc hủy')
    call('cancel',{'name':pending['name']});v=verify(over,10);clean_over={f['ktt']:shift(over,10),f['ktt2']:shift(over,0,recipient)}
    d,unused=evidence(resolution(pending));d=proof(d,v,clean_over);before=counts();confirm(d,ktt)
    assert wallet(over)['available_amount']==10 and wallet(over,recipient)['expected_amount']==0 and counts()==before
    assert get(H,pending['name'],ktt)['docstatus']==2
    emit('HTTP_2B_ISSUE_CANCELLED_OVER','PASS',{'cancelled_observation_resolved':True,'no_transfer_invented':True})
    # Hủy phiếu hoàn phải gỡ liên kết đang hiệu lực để native cancel không bị
    # chặn bởi backlink; token cũ trả hồ sơ hủy, token mới được lập lại.
    temporary=account('cancel-return');je(temporary,100);verify(temporary,100);base=transfer(temporary,temporary,20)
    args={'name':base['name'],'request_id':uuid.uuid4().hex,'reason':'UAT hủy đề nghị hoàn'}
    cancelled=call('create_reverse',args,recipient)
    call('cancel',{'name':cancelled['name']},recipient)
    denied(lambda:rpc('frappe.client.delete',{'doctype':H,'name':cancelled['name']}))
    assert call('create_reverse',args,recipient)['status']=='Đã hủy'
    assert not get(H,base['name'],ktt).get('reversal_doc') and wallet(temporary,recipient)['reserved_amount']==0
    replacement=call('create_reverse',{**args,'request_id':uuid.uuid4().hex},recipient)
    call('receive',{'name':replacement['name'],'amount':20})
    assert wallet(temporary)['expected_amount']==100
    same=account('return-same');je(same,200);verify(same,200);first=transfer(same,same,40)
    before=counts();token=uuid.uuid4().hex
    args={'name':first['name'],'request_id':token,'reason':'UAT hoàn do giao nhầm người'}
    denied(lambda:call('create_reverse',args),('PermissionError',))
    clients=[phien(f['ktt2']),phien(f['ktt2'])]
    with ThreadPoolExecutor(max_workers=2) as pool:replies=list(pool.map(lambda i:call('create_reverse',args,clients[i]),range(2)))
    assert replies[0]==replies[1]
    reverse=replies[0];assert wallet(same,recipient)['reserved_amount']==40
    denied(lambda:call('create_reverse',{**args,'request_id':uuid.uuid4().hex},recipient),text='đã có phiếu hoàn')
    denied(lambda:call('receive',{'name':reverse['name'],'amount':40},recipient),('PermissionError',))
    denied(lambda:call('receive',{'name':reverse['name'],'amount':39}),text='phải nhận đủ')
    call('receive',{'name':reverse['name'],'amount':40})
    assert wallet(same)['expected_amount']==200 and wallet(same,recipient)['expected_amount']==0 and counts()==before
    assert get(H,first['name'],ktt)['received_amount']==40 and get(H,first['name'],ktt)['status']=='Đã nhận'
    denied(lambda:call('create_reverse',{'name':reverse['name'],'request_id':uuid.uuid4().hex,'reason':'UAT hoàn tiếp'}),text='bàn giao gốc')
    emit('HTTP_2B_REVERSE_SAME_CONCURRENT','PASS',{'two_create_one_return':True,'same_cash_no_gl':True,'exact_two_actors':True,'original_kept':True})
    for kind in ['Cash','Bank']:
        src=account('return-'+kind);dest=account('target-'+kind,kind);je(src,200);verify(src,200)
        if kind=='Cash':verify(dest,0)
        original=transfer(src,dest,60);before=counts()
        args={'name':original['name'],'request_id':uuid.uuid4().hex,'reason':'UAT hoàn toàn bộ về Cash gốc'}
        r=call('create_reverse',args,recipient)
        clients=[phien(f['ktt']),phien(f['ktt'])]
        with ThreadPoolExecutor(max_workers=2) as pool:answers=list(pool.map(lambda i:call('receive',{'name':r['name'],'amount':60},clients[i]),range(2)))
        assert answers[0]==answers[1]
        after=counts();assert after['Journal Entry']==before['Journal Entry']+1 and after['GL Entry']==before['GL Entry']+2
        assert after['Payment Entry']==before['Payment Entry'] and after['Payment Ledger Entry']==before['Payment Ledger Entry']
        assert wallet(src)['expected_amount']==200
        reverse_je=get('Journal Entry',answers[0]['journal_entry'],ktt)
        assert reverse_je['docstatus']==1 and get('Journal Entry',original['journal_entry'],ktt)['docstatus']==1
        assert next(a for a in reverse_je['accounts'] if a['account']==src)[HOLDER]==f['ktt']
        if kind=='Bank':assert not next(a for a in reverse_je['accounts'] if a['account']==dest).get(HOLDER)
        emit('HTTP_2B_REVERSE_'+kind.upper(),'PASS',{'one_compensating_je':True,'no_customer_ple':True,'original_je_kept':True,'two_receive_one_je':True})
    spent=account('spent');je(spent,100);verify(spent,100);original=transfer(spent,spent,50);je(spent,-45,f['ktt2'],recipient)
    before=counts();args={'name':original['name'],'request_id':uuid.uuid4().hex,'reason':'UAT tiền đã dùng tiếp'}
    denied(lambda:call('create_reverse',args,recipient),text='khả dụng không đủ')
    assert not lst(H,{'reversal_of':original['name']},['name'],ktt) and counts()==before
    emit('HTTP_2B_REVERSE_SPENT_DENIED','PASS',{'spent_money_not_reused':True,'no_partial_return_or_je':True})

    if os.environ.get('GITHUB_ACTIONS'):
        import subprocess
        from pathlib import Path
        ui=account('browser');je(ui,100);verify(ui,100)
        doc=insert({'doctype':H,'company':f['aph'],'from_account':ui,'to_account':ui,'from_holder':f['ktt'],'to_holder':'Administrator','requested_amount':20,'reason':'UAT trình duyệt hoàn tiền'},ktt)
        call('send',{'name':doc['name']})
        rpc('kh_aph.cash_handover.receive',{'name':doc['name'],'amount':20})
        before=counts()
        proc=subprocess.run(['node',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),doc['name'],'hoan-tien'],text=True,capture_output=True,timeout=180)
        assert proc.returncode==0,(proc.stdout[-2500:],proc.stderr[-2500:])
        for line in proc.stdout.splitlines():
            if line.startswith('{"case":'):
                value=json.loads(line);emit(value['case'],value['status'],value.get('detail'))
        reverse=get(H,get(H,doc['name'],ktt)['reversal_doc'],ktt)
        call('receive',{'name':reverse['name'],'amount':20})
        assert wallet(ui)['expected_amount']==100 and counts()==before
