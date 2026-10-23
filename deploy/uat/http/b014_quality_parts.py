"""Nguồn giảm một phần độc lập phần giữ giá; nhận trả/hoàn không dùng giá bình quân cả mã."""
import json
import os
from pathlib import Path
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError


def chay(rpc,get,insert,submit,lst,denied,ktt,f,phien,emit):
    old=get('Item',f['A'],ktt)
    item=f['p']+'-PHAN-GIAM'
    insert({'doctype':'Item','item_code':item,'item_name':'Hàng thử phân biệt phần giảm','item_group':old['item_group'],
        'stock_uom':'Kg','is_stock_item':1,'valuation_method':'Moving Average','kh_aph_kg_per_bag':25,
        'taxes':[{'item_tax_template':t['item_tax_template']} for t in old['taxes']]},ktt)
    submit(insert({'doctype':'Stock Entry','stock_entry_type':'Material Receipt','company':f['aph'],
        'posting_date':f['date'],'items':[{'item_code':item,'t_warehouse':f['kho'],'qty':150,'basic_rate':20000,
        'kh_aph_bags':6,'kh_aph_kg_per_bag':25,'expense_account':f['acc']['cp']}]},ktt),ktt)
    def make(amount=55000,legacy=False):
        order=submit(insert({'doctype':'APH Shared Sales Order','customer':f['kh2'],'transaction_date':f['date'],
            'delivery_date':f['date'],'selling_price_list':f['pl'],'currency':'VND','kh_aph_xuat_hoa_don':'Không',
            'items':[{'item_code':item,'warehouse':f['kho'],'qty':25,'rate':35000,'kh_aph_bags':1,'kh_aph_kg_per_bag':25}]},ktt),ktt)
        row=rpc('kh_aph.ban_nhanh.preview',{'shared_order':order['name']},ktt)['rows'][0]
        made=rpc('kh_aph.ban_nhanh.create_and_dispatch',{'shared_order':order['name'],'request_id':uuid.uuid4().hex,
            'selections':json.dumps([{'source_row':row['source_row'],'qty':25}]),'dispatcher':'Kho UAT',
            'delivery':json.dumps({'delivery_method':'Khách đến lấy','recipient':'Khách UAT','customer_signature':'Không'})},ktt)
        dn=get('Delivery Note',made['delivery_notes'][0]['name'],ktt)
        invoices=[get('Sales Invoice',r['name'],ktt) for r in lst('Sales Invoice',{'customer':f['kh2'],'docstatus':1,'is_return':0},['name'],ktt)]
        si=next(doc for doc in invoices if any(r.get('delivery_note')==dn['name'] for r in doc['items']))
        assert si['grand_total']==962500, si['grand_total']
        result=rpc('kh_aph.sales_p1.giam_gia_sau_giao',{'sales_invoice':si['name'],'so_tien':amount,
            'ly_do':'Chỉ giảm5kg hàng có vấn đề,20kg giữ giá',**({} if legacy else {'selections':json.dumps([
                {'invoice_row':si['items'][0]['name'],'qty':5,'amount':amount}])})},ktt)
        je=get('Journal Entry',result['but_toan'],ktt)
        if not legacy:
            rows=json.loads(je['kh_aph_phan_bo_giam'])
            assert float(rows[0]['qty'])==5 and rows[0]['invoice_row']==si['items'][0]['name']
        denied(lambda:rpc('frappe.client.save',{'doc':json.dumps({**je,'kh_aph_phan_bo_giam':'[]'})},ktt))
        submit(je,ktt)
        return dn,si,je['name']
    def draft(dn,parts,settlement='Bù trừ công nợ',caller=None):
        return rpc('kh_aph.sales_return.create_draft',{'delivery_note':dn['name'],'request_id':uuid.uuid4().hex,
            'selections':json.dumps([{'source_row':dn['items'][0]['name'],'qty':sum(q for _,q in parts),'bags':0,
                'parts':[{'key':key,'qty':qty} for key,qty in parts]}]),
            'reason':'Nhận đúng phần hàng đã đối chiếu','condition':'Cách ly','settlement':settlement},caller if caller is not None else ktt)
    dn,si,key=make()
    assert os.environ.get('GITHUB_ACTIONS')=='true'
    before={dt:len(lst(dt,{},['name'],ktt)) for dt in ('Journal Entry','Delivery Note','Sales Invoice','Payment Entry')}
    browser=phien(f['ktt'])
    result=subprocess.run(['node','--experimental-websocket',str(Path(__file__).with_name('ban-nhanh-desk.mjs')),
        json.dumps({'invoice':si['name'],'delivery':dn['name'],'agreement':key,'user':f['ktt']}),'giam-theo-phan'],
        input=json.dumps({'cookies':browser.browser_cookies()}),text=True,capture_output=True,timeout=240)
    assert result.returncode==0,(result.stdout[-2000:],result.stderr[-2500:])
    browser_events=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"case":')]
    expected=[event for event in browser_events if event.get('case')=='NATIVE_DESK_GIAM_THEO_PHAN']
    assert len(expected)==1, browser_events
    evidence=expected[0]
    assert evidence['status']=='PASS'
    assert before=={dt:len(lst(dt,{},['name'],ktt)) for dt in before}
    emit(evidence['case'],'PASS',evidence['detail'])
    sales=phien(f['ktbh'])
    view=rpc('kh_aph.sales_return.preview',{'delivery_note':dn['name']},sales)['rows'][0]
    parts={p['key']:p for p in view['parts']}
    assert float(parts[key]['remaining'])==5 and float(parts[key]['net_rate'])==25000
    assert float(parts['']['remaining'])==20 and float(parts['']['net_rate'])==35000
    def race(caller):
        try:
            return draft(dn,[(key,3)],caller=caller)['name']
        except HTTPError as exc:
            data=json.loads(exc.read())
            assert data.get('exc_type')=='ValidationError',data
            return None
    with ThreadPoolExecutor(2) as pool:
        outcomes=list(pool.map(race,[phien(f['ktt']),phien(f['ktt'])]))
    winners=[name for name in outcomes if name]
    assert len(winners)==1,outcomes
    ktt('/api/method/frappe.client.delete',{'doctype':'Delivery Note','name':winners[0]})
    assert not lst('Delivery Note',{'name':winners[0]},['name'],ktt)

    assert {p['key']:float(p['remaining']) for p in rpc('kh_aph.sales_return.preview',{'delivery_note':dn['name']},ktt)['rows'][0]['parts']}=={key:5,'':20}
    made=draft(dn,[(key,3),('',2)],caller=sales)
    ret=get('Delivery Note',made['name'],ktt)
    assert ret['items'][0]['qty']==-5 and ret['items'][0]['rate']==29000 and ret['grand_total']==-159500
    denied(lambda:draft(dn,[(key,3)]))  # Đã giữ3kg, chỉ còn2kg ở đúng phần giảm.
    denied(lambda:rpc('frappe.client.cancel',{'doctype':'Journal Entry','name':key},ktt))
    bad=get('Delivery Note',made['name'],ktt);bad['items'][0]['rate']=35000
    denied(lambda:rpc('frappe.client.save',{'doc':json.dumps(bad)},ktt))
    submit(get('Delivery Note',made['name'],sales),sales)
    assert abs(get('Sales Invoice',si['name'],ktt)['outstanding_amount']-748000)<1
    left=rpc('kh_aph.sales_return.preview',{'delivery_note':dn['name']},ktt)['rows'][0]['parts']
    assert {p['key']:float(p['remaining']) for p in left}=={key:2,'':18}
    emit('HTTP_014_GIAM_THEO_PHAN_HANG','PASS',{'five_discounted_twenty_original':True,'mixed_return':159500,
        'draft_reserves_own_part':True,'concurrent_single_reservation':True,'tampered_price_and_cancel_denied':True,'remaining_debt':748000,'sales_clerk_without_general_journal_permission':True})

    dn,si,key=make()
    pe=rpc('erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry',
        {'dt':'Sales Invoice','dn':si['name'],'bank_account':f['acc']['tien']},ktt)
    pe['kh_aph_nguoi_giu_tien']=f['ktbh'];submit(insert(pe,ktt),ktt)
    made=draft(dn,[(key,5)],'Hoàn tiền');posted=submit(get('Delivery Note',made['name'],ktt),ktt)
    posted=get('Delivery Note',posted['name'],ktt)
    refund=get('Payment Entry',posted['kh_aph_chung_tu_xu_ly'],ktt)
    assert refund['docstatus']==0 and refund['paid_amount']==137500
    refund['kh_aph_nguoi_giao_tien']=f['ktbh'];submit(refund,ktt)
    assert get('Sales Invoice',refund['references'][0]['reference_name'],ktt)['outstanding_amount']==0
    # Không nhận lại khoản đã giảm100% lần thứ hai; vẫn nhận đủ hàng vật lý.
    zero_dn,zero_si,zero_key=make(192500)
    before=len(lst('Payment Entry',{},['name'],ktt))
    zero=draft(zero_dn,[(zero_key,5)],'Hoàn tiền')
    zero=submit(get('Delivery Note',zero['name'],ktt),ktt)
    assert zero['items'][0]['qty']==-5 and zero['grand_total']==0
    assert len(lst('Payment Entry',{},['name'],ktt))==before
    emit('HTTP_014_HOAN_DUNG_PHAN_DA_GIAM','PASS',{'discounted_five_refund':137500,
        'native_payment_cleared':True,'fully_reduced_stock_return_no_second_refund':True})

    old_dn,old_si,old_key=make(legacy=True)
    source=get('Journal Entry',old_key,ktt)
    before={dt:len(lst(dt,{},['name'],ktt)) for dt in ('Journal Entry','GL Entry','Payment Ledger Entry','Stock Ledger Entry','Payment Entry')}
    before_debt=get('Sales Invoice',old_si['name'],ktt)['outstanding_amount']
    classify={'journal_entry':old_key,'modified':source['modified'],'reason':'Đối chiếu giấy thỏa thuận cũ, đúng5kg',
        'selections':json.dumps([{'invoice_row':old_si['items'][0]['name'],'qty':5,'amount':55000}])}
    denied(lambda:rpc('kh_aph.sales_p1.classify_quality',classify,phien(f['dung'])),('PermissionError',))
    result=rpc('kh_aph.sales_p1.classify_quality',classify,ktt)
    assert result=={'but_toan':old_key,'da_co':False}
    assert get('Journal Entry',old_key,ktt)['docstatus']==1
    assert get('Sales Invoice',old_si['name'],ktt)['outstanding_amount']==before_debt
    assert before=={dt:len(lst(dt,{},['name'],ktt)) for dt in before}
    assert rpc('kh_aph.sales_p1.classify_quality',classify,ktt)=={'but_toan':old_key,'da_co':True}
    denied(lambda:rpc('kh_aph.sales_p1.classify_quality',{**classify,'selections':json.dumps([
        {'invoice_row':old_si['items'][0]['name'],'qty':6,'amount':55000}])},ktt))
    made=draft(old_dn,[(old_key,3)])
    submit(get('Delivery Note',made['name'],ktt),ktt)
    assert abs(get('Sales Invoice',old_si['name'],ktt)['outstanding_amount']-(before_debt-82500))<1
    assert rpc('kh_aph.sales_p1.classify_quality',classify,ktt)['da_co'] is True
    emit('HTTP_014_PHAN_LOAI_GIAM_CU','PASS',{'posted_journal_unchanged':True,'debt_gl_cash_unchanged':True,
        'source_scope_and_retry':True,'return_after_explicit_classification':82500})
