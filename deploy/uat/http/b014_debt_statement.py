"""Đối soát theo lượt lưu bộ PDF; thử phạm vi, bản ký và ảnh hưởng sổ bằng HTTP thật."""
import hashlib
import json
from pathlib import Path
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktt, f, phien, emit):
    dt = 'Bien ban doi soat no'
    order = submit(insert({'doctype':'APH Shared Sales Order','customer':f['kh2'], 'transaction_date':f['date'],
        'delivery_date':f['date'],'selling_price_list':f['pl'],'currency':'VND',
        'items':[{'item_code':f['A'],'warehouse':f['kho'],'qty':1,'rate':35000}]},ktt),ktt)
    row = rpc('kh_aph.ban_nhanh.preview',{'shared_order':order['name']},ktt)['rows'][0]
    made = rpc('kh_aph.ban_nhanh.create_and_dispatch',{'shared_order':order['name'],'request_id':uuid.uuid4().hex,
        'selections':json.dumps([{'source_row':row['source_row'],'qty':1}]),'dispatcher':'Kho UAT',
        'delivery':json.dumps({'delivery_method':'Khách đến lấy','recipient':'Khách ký nợ UAT'})},ktt)
    dn = get('Delivery Note',made['delivery_notes'][0]['name'],ktt)
    invoices = [get('Sales Invoice',r['name'],ktt) for r in lst('Sales Invoice',{'customer':f['kh2'],'docstatus':1},['name'],ktt)]
    invoice = next(doc for doc in invoices if any(i.get('delivery_note')==dn['name'] for i in doc['items']))
    payment = rpc('erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry',
        {'dt':'Sales Invoice','dn':invoice['name'],'bank_account':f['acc']['tien']},ktt)
    payment['kh_aph_nguoi_giu_tien']=f['ktbh']
    payment=submit(insert(payment,ktt),ktt)
    def counts():
        return {kind:len(lst(kind,{},['name'],ktt)) for kind in
            ('GL Entry','Stock Ledger Entry','Payment Ledger Entry','Delivery Note','Sales Invoice','Payment Entry','Journal Entry')}
    args={'customer':f['kh2'],'companies':json.dumps([f['aph'],f['vh']]),'request_id':uuid.uuid4().hex,
        'vouchers':json.dumps([{'doctype':'Delivery Note','name':dn['name']},{'doctype':'Payment Entry','name':payment['name']}])}
    before=counts()
    created=rpc('kh_aph.debt_statement.create',args,ktt)
    statement=get(dt,created['name'],ktt)
    frozen=statement['payload']
    data=json.loads(frozen)
    aph=next(r for r in data['positions'] if r['company']==f['aph'])
    assert abs(float(aph['increase'])-invoice['grand_total'])<1
    assert abs(float(aph['decrease'])-invoice['grand_total'])<1
    assert abs(float(aph['other'])-float(aph['current']))<1
    assert len(data['positions'])==2 and data['sources']
    assert counts()==before
    pdf=ktt.binary_get(created['file_url'])
    assert pdf.startswith(b'%PDF') and len(pdf)>1000
    Path('doi-soat-bo-giay.pdf').write_bytes(pdf)
    digest=hashlib.sha256(pdf).hexdigest()
    assert rpc('kh_aph.debt_statement.create',args,ktt)['name']==statement['name']
    assert len(lst(dt,{'request_id':args['request_id']},['name'],ktt))==1
    denied(lambda:rpc('frappe.client.save',{'doc':json.dumps({**statement,'payload':'{}'})},ktt),('PermissionError',))
    denied(lambda:insert({'doctype':dt,'customer':f['kh2'],'scope':args['companies'],'payload':'{}'},ktt),('PermissionError',))
    no_cost, scoped=phien(f['dung']),phien(f['scope_co'])
    for caller in (no_cost,scoped):
        denied(lambda caller=caller:get(dt,statement['name'],caller),('PermissionError',))
        denied(lambda caller=caller:caller.binary_get(created['file_url']),('PermissionError',))
    assert not lst(dt,{'name':statement['name']},['name'],scoped)
    denied(lambda:rpc('kh_aph.debt_statement.create',{**args,'request_id':uuid.uuid4().hex},scoped),('PermissionError',))
    denied(lambda:rpc('kh_aph.debt_statement.create',{**args,'request_id':uuid.uuid4().hex},no_cost),('PermissionError',))
    partial=rpc('kh_aph.debt_statement.create',{**args,'companies':json.dumps([f['aph']]),'request_id':uuid.uuid4().hex},scoped)
    assert json.loads(get(dt,partial['name'],scoped)['scope'])==[f['aph']]
    assert scoped.binary_get(partial['file_url']).startswith(b'%PDF')
    daily=rpc('frappe.www.printview.get_html_and_style',{'doc':'Customer','name':f['kh2'],
        'print_format':'Biên bản đối soát công nợ'},scoped)['html']
    assert f['aph'] in daily and f['vh'] not in daily
    emit('HTTP_014_DOI_SOAT_PHAM_VI','PASS',{'zero_net_keeps_increase_decrease':True,
        'two_companies':True,'partial_scope_positive_control':True,'no_cost_and_foreign_scope_denied':True,
        'private_pdf_denied':True,'native_sources_only':True,'no_financial_mutation':True})

    stamp={'name':statement['name'],'modified':statement['modified'],'signer':'Khách UAT',
        'authority':'Được ủy quyền ký nợ','authorization':'','location':'Tập đối soát tại cửa hàng'}
    denied(lambda:rpc('kh_aph.debt_statement.record_signature',stamp,ktt))
    stamp.update(authority='Khách hàng')
    signed=rpc('kh_aph.debt_statement.record_signature',stamp,ktt)
    assert signed['status']=='Đã nhận giấy gốc'
    assert rpc('kh_aph.debt_statement.record_signature',stamp,ktt)==signed
    signed_doc=get(dt,statement['name'],ktt)
    first_at=signed_doc['signed_at']; first_original=signed_doc['original_at']
    assert signed_doc['original_by']==f['ktt'] and not signed_doc.get('signed_file')
    evidence=insert({'doctype':'File','file_name':uuid.uuid4().hex+'.txt','content':json.dumps({'uat':'ban-ky-doi-soat'}),
        'is_private':1,'attached_to_doctype':dt,'attached_to_name':statement['name']},ktt)
    rpc('kh_aph.debt_statement.record_signature',{**stamp,'modified':signed_doc['modified'],'file_url':evidence['file_url']},ktt)
    latest=get(dt,statement['name'],ktt)
    assert latest['signed_at']==first_at and latest['original_at']==first_original
    assert latest['signed_file']==evidence['file_url'] and counts()==before
    denied(lambda:rpc('frappe.client.delete',{'doctype':'File','name':evidence['name']},ktt))
    denied(lambda:rpc('frappe.client.save',{'doc':json.dumps({**evidence,'is_private':0})},ktt))
    assert get(dt,statement['name'],ktt)['payload']==frozen
    assert hashlib.sha256(ktt.binary_get(created['file_url'])).hexdigest()==digest

    # Hủy khoản thu về sau: số cũ/PDF cũ giữ nguyên; request cũ vẫn mở bản đã cấp.
    rpc('frappe.client.cancel',{'doctype':'Payment Entry','name':payment['name']},ktt)
    assert rpc('kh_aph.debt_statement.create',args,ktt)['name']==statement['name']
    assert get(dt,statement['name'],ktt)['payload']==frozen
    assert hashlib.sha256(ktt.binary_get(created['file_url'])).hexdigest()==digest
    replacement=rpc('kh_aph.debt_statement.create',{**args,'request_id':uuid.uuid4().hex,'supersedes':statement['name'],
        'vouchers':json.dumps([{'doctype':'Delivery Note','name':dn['name']}])},ktt)
    newer=get(dt,replacement['name'],ktt)
    newer_aph=next(r for r in json.loads(newer['payload'])['positions'] if r['company']==f['aph'])
    assert abs(float(newer_aph['current'])-float(aph['current'])-invoice['grand_total'])<1
    assert newer['supersedes']==statement['name']
    emit('HTTP_014_DOI_SOAT_BAN_KY_BAT_BIEN','PASS',{'paper_and_photo_independent':True,'separate_debt_authority':True,
        'old_payload_pdf_frozen_after_cancel':True,'retry_after_cancel_opens_old_copy':True,'new_version_links_old':True,
        'private_evidence_kept':True,'pdf_sha256':digest})
    import os
    if os.environ.get('GITHUB_ACTIONS')=='true':
        import subprocess
        browser=phien(f['ktbh'])  # Phiên riêng: Desk khởi tạo CSRF, không tái dùng cho HTTP POST.
        state=counts()
        result=subprocess.run(['node','--experimental-websocket',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),
            json.dumps({'delivery':dn['name'],'user':f['ktbh']}),'doi-soat'],
            input=json.dumps({'cookies':browser.browser_cookies()}),text=True,capture_output=True,timeout=240)
        assert result.returncode==0,(result.stdout[-2000:],result.stderr[-2500:])
        evidence=json.loads(next(line for line in result.stdout.splitlines() if line.startswith('{"case":')))
        assert evidence['status']=='PASS' and counts()==state
        copies=lst(dt,{'request_id':evidence['detail']['requestId']},['name'],ktt)
        assert len(copies)==1 and copies[0]['name']==evidence['detail']['name']
        emit(evidence['case'],'PASS',evidence['detail'])


def chay_ngoai_te(rpc, get, insert, submit, lst, ktt, f, emit):
    """Nợ ròng lấy PLE theo tiền cơ sở; unallocated lấy đúng tỷ giá phía khách trên PE."""
    receivable=get('Company',f['aph'],ktt)['default_receivable_account']
    parent=get('Account',receivable,ktt)['parent_account']
    account=insert({'doctype':'Account','account_name':f['p']+'-PhaiThuUSD','company':f['aph'],
        'parent_account':parent,'account_type':'Receivable','account_currency':'USD','is_group':0},ktt)
    source=get('Customer',f['kh2'],ktt)
    customer=insert({'doctype':'Customer','customer_name':f['p']+'-KhachUSD','customer_type':'Company',
        'customer_group':source['customer_group'],'territory':source['territory'],'default_currency':'USD',
        'accounts':[{'company':f['aph'],'account':account['name']}]},ktt)
    payment=submit(insert({'doctype':'Payment Entry','payment_type':'Receive','party_type':'Customer',
        'party':customer['name'],'company':f['aph'],'posting_date':f['date'],'paid_from':account['name'],
        'paid_to':f['acc']['tien'],'paid_amount':10,'received_amount':250000,'source_exchange_rate':25000,
        'target_exchange_rate':1,'kh_aph_nguoi_giu_tien':f['ktbh']},ktt),ktt)
    assert payment['unallocated_amount']==10
    before={dt:len(lst(dt,{},['name'],ktt)) for dt in ('GL Entry','Payment Entry','Payment Ledger Entry')}
    result=rpc('kh_aph.debt_statement.create',{'customer':customer['name'],'companies':json.dumps([f['aph']]),
        'vouchers':json.dumps([{'doctype':'Payment Entry','name':payment['name']}]),'request_id':uuid.uuid4().hex},ktt)
    data=json.loads(get('Bien ban doi soat no',result['name'],ktt)['payload'])
    assert abs(float(data['positions'][0]['current'])+250000)<.01
    assert abs(float(data['funds'][0]['unallocated_received'])-250000)<.01
    assert before=={dt:len(lst(dt,{},['name'],ktt)) for dt in before}
    emit('HTTP_014_DOI_SOAT_TIEN_CHUA_PHAN_BO_NGOAI_TE','PASS',{'party_currency':'USD','unallocated':10,
        'rate':25000,'base_unallocated_vnd':250000,'no_financial_mutation':True})
