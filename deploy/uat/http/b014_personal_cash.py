"""Tiền cá nhân không GL, đối chiếu nguồn thật trên quỹ UAT dùng một lần."""
import json
import os
from pathlib import Path
import subprocess

H = 'kh_aph_nguoi_giu_tien'
API = 'kh_aph.personal_cash.'


def chay(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit):
    parent = get('Account', f['acc']['tien'], ktt)['parent_account']
    account = insert({'doctype':'Account','account_name':f['p']+'-Ca-nhan','company':f['aph'],
        'parent_account':parent,'account_type':'Cash','account_currency':'VND','is_group':0},ktt)['name']
    args = {'company': f['aph'], 'account': account}
    def counts():
        return {dt:len(lst(dt, {}, ['name'], ktt)) for dt in ('GL Entry','Payment Ledger Entry','Payment Entry','Journal Entry')}
    def journal(amount, holder=None):
        return submit(insert({'doctype':'Journal Entry','company':f['aph'],'posting_date':f['date'],'accounts':[
            {'account':account,'debit_in_account_currency':amount,H:holder},
            {'account':f['acc']['cp'],'credit_in_account_currency':amount}]}, ktt), ktt)
    initial = journal(1000)
    opening = submit(insert({'doctype':'APH Xac minh quy',**args,'reason':'UAT tiền cá nhân không cấp GL',
        'allocations':[{'holder':f['dung'],'amount':300},{'holder':f['ktt'],'amount':600}], 'unverified_amount':100},ktt),ktt)
    old = get('Company', f['aph'], ktt).get('kh_aph_quy_nha_may')
    old_vh = get('Company', f['vh'], ktt).get('kh_aph_quy_nha_may')
    vh_account = lst('Account', {'company':f['vh'],'account_type':'Cash','is_group':0,'disabled':0}, ['name'], ktt)[0]['name']
    dung = phien(f['dung'])
    def current(caller=dung, **extra): return rpc(API+'current', {**args, **extra}, caller)
    try:
        rpc('frappe.client.set_value',{'doctype':'Company','name':f['aph'],'fieldname':'kh_aph_quy_nha_may','value':account},ktt)
        rpc('frappe.client.set_value',{'doctype':'Company','name':f['vh'],'fieldname':'kh_aph_quy_nha_may','value':vh_account},ktt)
        before = counts()
        assert rpc(API+'accounts',{'company':f['aph']},dung)==[account]
        value = current()
        assert set(value)=={'expected_amount','reserved_amount','available_amount','disputed','checked_at'},value
        assert value['expected_amount']==300 and value['available_amount']==300 and not value['disputed']
        assert current(holder=f['ktt'])['expected_amount']==300
        assert current(ktt)['expected_amount']==600
        assert current(ktt)['expected_amount']==rpc('kh_aph.cash_closing.current',args,ktt)['expected_amount']
        assert counts()==before
        denied(lambda: get('APH Xac minh quy',opening['name'],dung),('PermissionError',))
        gl = lst('GL Entry',{'account':account},['name'],ktt)[0]['name']
        denied(lambda:get('GL Entry',gl,dung),('PermissionError',))
        denied(lambda:rpc('kh_aph.cash_closing.current',args,dung),('PermissionError',))
        denied(lambda:current(account=f['acc']['tien']),('PermissionError',))
        denied(lambda:current(account=f['acc']['bank']),('PermissionError',))
        denied(lambda:rpc(API+'accounts',{'company':f['vh']},phien(f['scope_co'])),('PermissionError',))
        denied(lambda:current(phien(f['nvbh'])),('PermissionError',))
        denied(lambda:current(account=None))
        permission = insert({'doctype':'User Permission','user':f['dung'],'allow':'Account','for_value':f['acc']['tien'],
            'apply_to_all_doctypes':0,'applicable_for':'Account'},ktt)
        try:
            denied(lambda:current(),('PermissionError',))
            denied(lambda:rpc(API+'accounts',{'company':f['aph']},dung),('PermissionError',))
        finally:
            # Native delete không có message; dùng caller thô như ca quyền cũ.
            ktt('/api/method/frappe.client.delete',{'doctype':'User Permission','name':permission['name']})
        emit('HTTP_2B_PERSONAL_SCOPE_NO_GL','PASS',{'own_only':True,'factory_with_manager_still_restricted':True,'native_gl_opening_still_denied':True,'read_only':True})

        # Hai nghiệp vụ chuẩn tăng trách nhiệm, không cộng lại cả phiếu quỹ và JE.
        source = submit(insert({'doctype':'APH Phieu quy nha may','company':f['aph'],'posting_date':f['date'],
            'loai':'Thu tiền khách','customer':f['kh2'],H:f['dung'],
            'dong':[{'dien_giai':'UAT thu nhà máy theo người giữ','so_tien':25}]},dung),dung)
        assert current()['expected_amount']==325
        template = get('Company',f['aph'],ktt)['default_receivable_account']
        payment = submit(insert({'doctype':'Payment Entry','payment_type':'Receive','company':f['aph'],'posting_date':f['date'],
            'party_type':'Customer','party':f['kh2'],'paid_from':template,'paid_to':account,
            'paid_amount':7,'received_amount':7,'source_exchange_rate':1,'target_exchange_rate':1,H:f['dung']},ktt),ktt)
        unknown = journal(11)
        baseline = counts()
        assert current()['expected_amount']==332 and current()['available_amount']==332
        assert counts()==baseline
        # Không suy quyền JE của người có sẵn Accounts Manager là bị chặn.
        # Facade này phải không trả JE/nguồn, bất kể quyền native có sẵn.
        own = current()
        assert set(own)==set(value) and source['journal_entry'] not in json.dumps(own)
        emit('HTTP_2B_PERSONAL_SOURCES_UNKNOWN','PASS',{'factory_je_once':True,'pe_holder':True,'unknown_not_owner':True,'no_source_exposure':True})

        handover = insert({'doctype':'APH Ban giao tien','company':f['aph'],'from_account':account,'to_account':account,
            'from_holder':f['ktt'],'to_holder':f['ktt2'],'requested_amount':40,'reason':'UAT giữ chỗ cá nhân'},ktt)
        rpc('kh_aph.cash_handover.send',{'name':handover['name']},ktt)
        value = current(ktt)
        assert value['expected_amount']==600 and value['reserved_amount']==40 and value['available_amount']==560
        assert current()['reserved_amount']==0  # Không trả giữ chỗ của người khác.
        rpc('kh_aph.cash_handover.receive',{'name':handover['name'],'amount':40},phien(f['ktt2']))
        assert current(ktt)['expected_amount']==560 and current(phien(f['ktt2']))['expected_amount']==40
        assert current(ktt)['reserved_amount']==0 and counts()==baseline
        emit('HTTP_2B_PERSONAL_HANDOVER_DELTA','PASS',{'own_reservations':True,'same_cash_delta':True,'no_extra_gl_ple':True})

        if os.environ.get('GITHUB_ACTIONS')!='true': raise RuntimeError('Chrome chỉ chạy UAT CI dùng một lần')
        payload = {'company':f['aph'],'source':source['name'],'user':f['dung'],'expected':332,'account':account,
            'other_company':f['vh'],'other_account':vh_account}
        proc = subprocess.run(['node', str(Path(__file__).with_name('ban-nhanh-desk.mjs')), json.dumps(payload), 'tien-ca-nhan'],
            input=json.dumps({'cookies':dung.browser_cookies()}), text=True,capture_output=True,timeout=180)
        assert proc.returncode==0,(proc.stdout[-2000:],proc.stderr[-2000:])
        results=[json.loads(line) for line in proc.stdout.splitlines() if line.startswith('{"case":')]
        assert len(results)==1 and results[0]['case']=='DESK_2B_PERSONAL_NO_GL' and results[0]['status']=='PASS',proc.stdout
        emit(results[0]['case'],'PASS',results[0].get('detail'))
        assert counts()==baseline

        # Hủy phát sinh sau mốc chỉ đảo đúng phần đã ghi; không tự phân lại tiền.
        rpc('frappe.client.cancel',{'doctype':'Payment Entry','name':payment['name']},ktt)
        assert current()['expected_amount']==325
        # Một ca của người khác lệch không mở chi tiết hoặc chặn người đang xem.
        shift = insert({'doctype':'APH Chot ca tien',**args,'holder':f['ktt'],'counted_amount':559,
            'reason':'UAT lệch riêng người giữ','assignee':f['ktt2'],'due_date':f['date']},ktt)
        rpc('kh_aph.cash_closing.close',{'name':shift['name']},ktt)
        assert current(ktt)['disputed'] and current(ktt)['available_amount']==0
        assert not current()['disputed'] and current()['available_amount']==325
        # Sửa metadata tại nguồn trước mốc không được suy/ghi lại mốc mới.
        before_snapshot = counts()
        rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':unknown['name']},ktt)
        assert current()['expected_amount']==325
        assert counts()['Payment Entry']==before_snapshot['Payment Entry']
        rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':initial['name']},ktt)
        before_invalid = counts()
        denied(lambda:current(),text='cần xác minh lại quỹ')
        assert counts()==before_invalid
        emit('HTTP_2B_PERSONAL_CANCEL_AND_ISSUE','PASS',{'cancel_delta_correct':True,'own_issue_only':True,'invalid_anchor_denied':True,'no_reassignment':True})
    finally:
        rpc('frappe.client.set_value',{'doctype':'Company','name':f['aph'],'fieldname':'kh_aph_quy_nha_may','value':old or ''},ktt)
        rpc('frappe.client.set_value',{'doctype':'Company','name':f['vh'],'fieldname':'kh_aph_quy_nha_may','value':old_vh or ''},ktt)
