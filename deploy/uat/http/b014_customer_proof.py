"""Nhận hồ sơ khách cuối khi yêu cầu; tách bản nhà xe, giấy gốc/ảnh và không ghi lại sổ."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktt, f, emit):
    order = submit(insert({'doctype':'APH Shared Sales Order','customer':f['kh2'],'transaction_date':f['date'],
        'delivery_date':f['date'],'selling_price_list':f['pl'],'currency':'VND',
        'items':[{'item_code':f['A'],'warehouse':f['kho'],'qty':1,'rate':35000}]},ktt),ktt)
    row = rpc('kh_aph.ban_nhanh.preview',{'shared_order':order['name']},ktt)['rows'][0]
    result = rpc('kh_aph.ban_nhanh.create_and_dispatch',{'shared_order':order['name'],'request_id':uuid.uuid4().hex,
        'selections':json.dumps([{'source_row':row['source_row'],'qty':1}]),'dispatcher':'Kho UAT',
        'delivery':json.dumps({'delivery_method':'Vận chuyển','recipient':'Lái xe UAT','carrier':'Nhà xe quen',
            'carrier_phone':'0901111222','customer_signature':'Có'})},ktt)
    name = result['delivery_notes'][0]['name']
    def save(doc): return rpc('frappe.client.save',{'doc':json.dumps(doc)},ktt)
    def counts():
        return {dt:len(lst(dt,{},['name'],ktt)) for dt in
                ('GL Entry','Stock Ledger Entry','Payment Ledger Entry','Sales Invoice','Payment Entry')}
    def file(kind):
        return insert({'doctype':'File','file_name':uuid.uuid4().hex+'.txt','is_private':1,
            'attached_to_doctype':'Delivery Note','attached_to_name':name,'content':json.dumps({'uat':kind})},ktt)
    warehouse = file('ban-ky-giao-nha-xe')
    doc=get('Delivery Note',name,ktt); doc['kh_aph_ban_ky']=warehouse['file_url']; doc=save(doc)
    rpc('kh_aph.ho_so_giao_nhan.doi_chieu',{'name':name,'modified':doc['modified']},ktt)
    before = counts(); doc=get('Delivery Note',name,ktt)
    args={'name':name,'modified':doc['modified'],'location':'Tập khách ký tại kế toán cửa hàng','received_on':f['date']}
    physical=rpc('kh_aph.customer_delivery_proof.receive',args,ktt)
    latest=get('Delivery Note',name,ktt)
    assert latest['kh_aph_delivery_state']=='Khách đã nhận' and latest['kh_aph_nhan_goc_khach_boi']==f['ktt']
    assert latest['kh_aph_doi_chieu_boi']==f['ktt'] and latest['kh_aph_ban_ky']==warehouse['file_url']
    assert not latest.get('kh_aph_ban_ky_khach') and counts()==before
    first=latest['kh_aph_nhan_goc_khach_luc']
    assert rpc('kh_aph.customer_delivery_proof.receive',args,ktt)==physical
    customer=file('khach-ky-tai-dich')
    args.update(modified=latest['modified'],file_url=customer['file_url'])
    rpc('kh_aph.customer_delivery_proof.receive',args,ktt)
    latest=get('Delivery Note',name,ktt)
    assert latest['kh_aph_ban_ky_khach']==customer['file_url'] and latest['kh_aph_nhan_goc_khach_luc']==first
    assert latest['kh_aph_ban_ky']==warehouse['file_url'] and latest['kh_aph_doi_chieu_boi']==f['ktt']
    history=json.loads(latest['kh_aph_lich_su_ban_ky'])
    assert set(history['files'])=={warehouse['file_url'],customer['file_url']}
    denied(lambda:save({**latest,'kh_aph_kiem_ky_khach_boi':'Administrator'}))
    denied(lambda:rpc('frappe.client.delete',{'doctype':'File','name':customer['name']},ktt))
    assert counts()==before and ktt(customer['file_url'])=={'uat':'khach-ky-tai-dich'}
    pickup=lst('Delivery Note',{'company':f['aph'],'docstatus':1,'is_return':0,
        'kh_aph_cach_giao':'Khách đến lấy'},['name'],ktt)[0]['name']
    old=get('Delivery Note',pickup,ktt)
    denied(lambda:rpc('kh_aph.customer_delivery_proof.receive',{'name':pickup,'modified':old['modified'],'location':'Không cần'},ktt))
    emit('HTTP_014_KHACH_KY_TAI_DICH','PASS',{'required_shipping_only':True,'warehouse_proof_separate':True,
        'paper_before_photo':True,'original_timestamp_kept':True,'retry_kept':True,'no_second_posting':True,
        'private_files_kept':True,'pickup_not_forced':True})
