"""NM01c — nhận chuyến chuyển đến bằng phiên nhà máy (Dũng, không xem giá vốn); phiếu native giữ sổ kho."""
import json
from concurrent.futures import ThreadPoolExecutor

TRANSIT = "Hàng đang vận chuyển - APH"
NHA_MAY = "Kho thành phẩm nhà máy - APH"


def chay(rpc, get, insert, submit, lst, denied, f, phien, emit):
    dung = phien(f['dung'])
    out = submit(insert({'doctype': 'Stock Entry', 'stock_entry_type': 'Material Transfer', 'purpose': 'Material Transfer',
        'company': f['aph'], 'add_to_transit': 1, 'posting_date': f['date'],
        'items': [{'item_code': f['A'], 'qty': 10, 'uom': 'Kg', 'conversion_factor': 1,
                   's_warehouse': f['kho'], 't_warehouse': TRANSIT}]}))
    listed = rpc('kh_aph.factory_transfer.incoming', {'company': f['aph']}, dung)
    assert out['name'] in [x['name'] for x in listed] and all(set(x) == {'name', 'posting_date'} for x in listed)
    denied(lambda: rpc('kh_aph.factory_transfer.incoming', {'company': f['vh']}, phien(f['scope_co'])), ('PermissionError',))
    denied(lambda: rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, phien(f['tp'])), ('PermissionError',))
    view = rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, dung)
    assert set(view) == {'stock_entry', 'company', 'sent_date', 'items'} and view['items'][0]['remaining'] == 10
    assert not any(k in json.dumps(view) for k in ('rate', 'amount', 'valuation'))
    emit('HTTP_NM01C_SCOPE_PREVIEW', 'PASS', {'quantity_only': True, 'restricted_principal': True})

    src = view['items'][0]['source_row']
    row = {'source_row': src, 'warehouse': NHA_MAY, 'qty': 4, 'bags': 0}
    args = {'stock_entry': out['name'], 'request_id': f['p'] + '-chuyen-1', 'rows': json.dumps([row]),
            'received_date': f['date'], 'receiver': 'Thủ kho nhà máy ký giấy', 'note': 'UAT nhận một phần'}

    def counts():
        return {dt: len(lst(dt, {}, ['name'])) for dt in ('Stock Entry', 'Stock Ledger Entry', 'GL Entry', 'Payment Ledger Entry')}
    before = counts()
    result = rpc('kh_aph.factory_transfer.receive', args, dung)
    entry = get('Stock Entry', result['name'])
    assert entry['docstatus'] == 1 and entry['outgoing_stock_entry'] == out['name'] and entry['kh_aph_transfer_actor'] == f['dung']
    assert len(entry['items']) == 1 and entry['items'][0]['qty'] == 4 and entry['items'][0]['t_warehouse'] == NHA_MAY
    assert entry['items'][0]['s_warehouse'] == TRANSIT and entry['items'][0]['ste_detail'] == src
    masked = get('Stock Entry', result['name'], dung)
    assert not masked['items'][0].get('basic_rate') and not masked['items'][0].get('valuation_rate')
    after = counts()
    assert after['Stock Entry'] == before['Stock Entry'] + 1 and after['Payment Ledger Entry'] == before['Payment Ledger Entry']
    assert rpc('kh_aph.factory_transfer.receive', args, dung) == result and counts() == after
    denied(lambda: rpc('kh_aph.factory_transfer.receive', {**args, 'note': 'đổi nội dung'}, dung))
    assert rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, dung)['items'][0]['remaining'] == 6
    assert get('Stock Entry', out['name'])['per_transferred'] == 40
    emit('HTTP_NM01C_PARTIAL_REPLAY', 'PASS', {'received': 4, 'remaining': 6, 'retry_one_entry': True})

    for bad in ({**row, 'qty': 7}, {**row, 'warehouse': TRANSIT}, {**row, 'warehouse': f['kho_vh']}):
        denied(lambda bad=bad: rpc('kh_aph.factory_transfer.receive', {**args, 'request_id': 'bad-' + json.dumps(bad)[-20:],
                                                                      'rows': json.dumps([bad])}, dung))
    denied(lambda: rpc('kh_aph.factory_transfer.receive', {**args, 'request_id': 'forged', 'rows': json.dumps([{**row, 'rate': 1}])}, dung))
    denied(lambda: rpc('frappe.client.set_value', {'doctype': 'Stock Entry', 'name': result['name'],
                                                   'fieldname': 'kh_aph_transfer_receiver', 'value': 'sửa người nhận'}))
    assert counts() == after
    emit('HTTP_NM01C_TAMPER', 'PASS', {'over_qty': 'denied', 'transit_or_other_company_target': 'denied', 'stamp_kept': True})

    a, b = phien(f['dung']), phien(f['dung'])

    def racing(pair):
        token, caller = pair
        try:
            return rpc('kh_aph.factory_transfer.receive', {**args, 'request_id': token}, caller)['name']
        except Exception as exc:
            if not hasattr(exc, 'read'):
                raise
            data = json.loads(exc.read())
            assert data.get('exc_type') == 'ValidationError', data
            return None
    with ThreadPoolExecutor(2) as pool:
        outcomes = list(pool.map(racing, [(f['p'] + '-race-a', a), (f['p'] + '-race-b', b)]))
    assert len([r for r in outcomes if r]) == 1, outcomes
    assert rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, dung)['items'][0]['remaining'] == 2
    emit('HTTP_NM01C_RACE', 'PASS', {'two_sessions_only_one': True, 'remaining': 2})

    native = rpc('erpnext.stock.doctype.stock_entry.stock_entry.make_stock_in_entry', {'source_name': out['name']})
    for item in native['items']:
        item['t_warehouse'] = NHA_MAY
        item['qty'] = 3
    denied(lambda: submit(insert(native)))
    for item in native['items']:
        item['qty'] = 2
    closing = submit(insert(native))
    assert get('Stock Entry', out['name'])['per_transferred'] == 100
    denied(lambda: rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, dung))
    assert out['name'] not in [x['name'] for x in rpc('kh_aph.factory_transfer.incoming', {'company': f['aph']}, dung)]
    emit('HTTP_NM01C_NATIVE_CAP', 'PASS', {'native_over_denied': True, 'native_rest_ok': True, 'fully_received': True})

    rpc('frappe.client.cancel', {'doctype': 'Stock Entry', 'name': closing['name']})
    assert rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, dung)['items'][0]['remaining'] == 2
    rpc('frappe.client.cancel', {'doctype': 'Stock Entry', 'name': result['name']})
    assert rpc('kh_aph.factory_transfer.preview', {'stock_entry': out['name']}, dung)['items'][0]['remaining'] == 6
    denied(lambda: rpc('frappe.client.delete', {'doctype': 'Stock Entry', 'name': result['name']}))
    assert get('Stock Entry', result['name'])['kh_aph_transfer_receiver'] == 'Thủ kho nhà máy ký giấy'
    emit('HTTP_NM01C_CANCEL_RESTORE', 'PASS', {'cancel_restores_in_transit': True, 'history_kept': True})

    send = {'company': f['aph'], 'request_id': f['p'] + '-gui-1', 'sent_date': f['date'], 'carrier': 'Xe UAT 29C',
            'rows': json.dumps([{'item_code': f['A'], 'warehouse': f['kho'], 'qty': 5, 'bags': 0}]), 'note': 'UAT chuyển về nhà máy'}
    before = counts()
    sent = rpc('kh_aph.factory_transfer.send', send, dung)
    doc = get('Stock Entry', sent['name'])
    assert doc['docstatus'] == 1 and doc['add_to_transit'] == 1 and doc['items'][0]['t_warehouse'] == TRANSIT
    assert doc['kh_aph_transfer_actor'] == f['dung'] and doc['kh_aph_transfer_receiver'] == 'Xe UAT 29C'
    assert rpc('kh_aph.factory_transfer.send', send, dung) == sent and counts()['Stock Entry'] == before['Stock Entry'] + 1
    denied(lambda: rpc('kh_aph.factory_transfer.send', {**send, 'request_id': 'gui-transit',
        'rows': json.dumps([{'item_code': f['A'], 'warehouse': TRANSIT, 'qty': 1, 'bags': 0}])}, dung))
    denied(lambda: rpc('kh_aph.factory_transfer.send', {**send, 'request_id': 'gui-vh',
        'rows': json.dumps([{'item_code': f['A'], 'warehouse': f['kho_vh'], 'qty': 1, 'bags': 0}])}, dung))
    assert sent['name'] in [x['name'] for x in rpc('kh_aph.factory_transfer.incoming', {'company': f['aph']}, dung)]
    emit('HTTP_NM05_SEND_TRANSIT', 'PASS', {'via_transit': True, 'retry_one_entry': True, 'other_company_source': 'denied'})


def chay_chuan_bi(rpc, get, submit, lst, denied, ktt, f, phien, emit):
    """Kho cửa hàng chuẩn bị giấy trước; xuất/nhận thực tế vẫn là Stock Entry chuẩn."""
    def counts():
        return {dt: len(lst(dt, {}, ['name'], ktt)) for dt in
                ('Stock Entry', 'Stock Ledger Entry', 'GL Entry', 'Payment Ledger Entry')}
    args = {'company': f['aph'], 'request_id': f['p'] + '-chuan-bi-chuyen', 'sent_date': f['date'],
            'carrier': 'Xe gom kho UAT', 'destination': f['kho2'], 'prepare_only': 1,
            'rows': json.dumps([{'item_code': f['A'], 'warehouse': f['kho'], 'qty': 3, 'bags': 0}])}
    before = counts()
    result = rpc('kh_aph.factory_transfer.send', args, ktt)
    doc = get('Stock Entry', result['name'], ktt)
    assert doc['docstatus'] == 0 and doc['kh_aph_transfer_destination'] == f['kho2']
    after = counts()
    assert after == {**before, 'Stock Entry': before['Stock Entry'] + 1}, 'Chuẩn bị giấy đã ghi sổ'
    assert rpc('kh_aph.factory_transfer.send', args, ktt) == result and counts() == after
    html = rpc('frappe.www.printview.get_html_and_style', {'doc': json.dumps(doc), 'print_format': 'Phiếu kho'}, ktt)['html']
    assert 'CHƯA GHI SỔ' in html and 'Xe gom kho UAT' in html and 'Kho nhận cuối dự kiến' in html
    denied(lambda: rpc('kh_aph.factory_transfer.send', {**args, 'request_id': f['p'] + '-chuan-bi-scope'}, phien(f['scope_wh'])), ('PermissionError',))
    doc['kh_aph_transfer_receiver'] = 'Xe gom kho thực tế'
    doc = rpc('frappe.client.save', {'doc': json.dumps(doc)}, ktt)
    assert doc['kh_aph_transfer_receiver'] == 'Xe gom kho thực tế'
    denied(lambda: rpc('frappe.client.save', {'doc': json.dumps({**doc, 'company': f['vh']})}, ktt))
    posted = submit(doc, ktt)
    assert posted['docstatus'] == 1 and posted['items'][0]['t_warehouse'] == TRANSIT
    assert counts()['Stock Ledger Entry'] > before['Stock Ledger Entry']
    assert rpc('kh_aph.factory_transfer.send', args, ktt)['name'] == posted['name']
    view = rpc('kh_aph.factory_transfer.preview', {'stock_entry': posted['name']}, ktt)
    assert view['items'][0]['warehouse'] == f['kho2']
    received = rpc('kh_aph.factory_transfer.receive', {'stock_entry': posted['name'],
        'request_id': f['p'] + '-nhan-gom-kho', 'received_date': f['date'], 'receiver': 'Thủ kho cửa hàng',
        'rows': json.dumps([{'source_row': view['items'][0]['source_row'], 'warehouse': f['kho2'], 'qty': 3, 'bags': 0}])}, ktt)
    receipt = get('Stock Entry', received['name'], ktt)
    assert receipt['docstatus'] == 1 and receipt['items'][0]['t_warehouse'] == f['kho2']
    assert not receipt.get('kh_aph_transfer_destination')
    assert get('Stock Entry', posted['name'], ktt)['per_transferred'] == 100
    assert counts()['Payment Ledger Entry'] == before['Payment Ledger Entry'], 'Chuyển nội bộ sinh công nợ khách'
    shared = rpc('frappe.client.insert', {'doc': json.dumps({'doctype': 'APH Shared Sales Order',
        'customer': f['kh1'], 'transaction_date': f['date'], 'delivery_date': f['date'],
        'selling_price_list': f['pl'], 'currency': 'VND',
        'items': [{'item_code': f['A'], 'warehouse': f['kho2'], 'qty': 5, 'rate': 35000}]})}, ktt)
    shared = submit(shared, ktt)
    before_plan = counts()
    plan = rpc('kh_aph.order_transfer.preview', {'shared_order': shared['name']}, ktt)
    assert counts() == before_plan and len(plan['groups']) == 1
    group = plan['groups'][0]
    assert group['company'] == f['aph'] and group['destination'] == f['kho2']
    assert group['items'][0]['qty'] == 5 and group['items'][0]['item_code'] == f['A']
    assert 'rate' not in group['items'][0] and 'valuation_rate' not in group['items'][0]
    denied(lambda: rpc('kh_aph.order_transfer.preview', {'shared_order': shared['name']}, phien(f['scope_wh'])), ('PermissionError',))
    order_args = {**args, 'request_id': f['p'] + '-gom-theo-don',
        'note': 'Gom cho đơn ' + shared['name'], 'rows': json.dumps([{
            'item_code': row['item_code'], 'warehouse': f['kho'], 'qty': row['qty'], 'bags': row['bags']
        } for row in group['items']])}
    planned = rpc('kh_aph.factory_transfer.send', order_args, ktt)
    assert get('Stock Entry', planned['name'], ktt)['docstatus'] == 0
    after_plan = counts()
    assert after_plan == {**before_plan, 'Stock Entry': before_plan['Stock Entry'] + 1}
    assert rpc('kh_aph.factory_transfer.send', order_args, ktt) == planned and counts() == after_plan
    assert rpc('kh_aph.order_transfer.preview', {'shared_order': shared['name']}, ktt)['groups'][0]['items'][0]['qty'] == 5
    emit('HTTP_014_CHUAN_BI_GOM_KHO', 'PASS', {'draft_print_no_posting': True, 'repeat_one_entry': True,
         'native_issue_transit_receive': True, 'planned_destination': True, 'warehouse_scope': True,
         'no_customer_debt': True, 'order_remaining_suggestion_no_reservation': True})


def chay_phan_quyen(rpc,get,insert,submit,lst,denied,ktt,f,phien,emit):
    """Hai hồ sơ thật, UserPermission tách kho và NoCost; không mượn Accounts Manager."""
    factory=phien(f['staff_dung']);store=phien(f['staff_hanh'])
    origin='Kho nguyên liệu - APH';destination=f['kho']
    seed=submit(insert({'doctype':'Stock Entry','stock_entry_type':'Material Receipt','purpose':'Material Receipt',
        'company':f['aph'],'posting_date':f['date'],'items':[{'item_code':f['A'],'qty':3,'uom':'Kg','conversion_factor':1,
        't_warehouse':origin,'basic_rate':37000,'expense_account':f['acc']['cp']}]},ktt),ktt)
    args={'company':f['aph'],'request_id':f['p']+'-factory-store','rows':json.dumps([
        {'item_code':f['A'],'warehouse':origin,'qty':2,'bags':0}]),'sent_date':f['date'],
        'carrier':'Xe nội bộ','prepare_only':1,'destination':destination}
    prepared=rpc('kh_aph.factory_transfer.send',args,factory)
    source=get('Stock Entry',prepared['name'],factory)
    assert source['docstatus']==0
    submit(source,factory)
    # Cửa hàng vẫn không được mở Warehouse/phiếu nguồn của nhà máy.
    denied(lambda:get('Warehouse',origin,store),('PermissionError',))
    denied(lambda:get('Stock Entry',prepared['name'],store),('PermissionError',))
    assert prepared['name'] in {row['name'] for row in rpc('kh_aph.factory_transfer.incoming',{'company':f['aph']},store)}
    view=rpc('kh_aph.factory_transfer.preview',{'stock_entry':prepared['name']},store)
    assert len(view['items'])==1 and view['items'][0]['remaining']==2
    assert not any(key in json.dumps(view) for key in ('rate','amount','valuation'))
    receive={'stock_entry':prepared['name'],'request_id':f['p']+'-store-receive','rows':json.dumps([
        {'source_row':view['items'][0]['source_row'],'warehouse':destination,'qty':2,'bags':0}]),
        'received_date':f['date'],'receiver':'Kho cửa hàng nhận','note':'Đúng phiếu vận chuyển'}
    before={dt:len(lst(dt,{},['name'],ktt)) for dt in ('Stock Entry','Stock Ledger Entry','GL Entry','Payment Ledger Entry')}
    denied(lambda:rpc('kh_aph.factory_transfer.receive',{**receive,'request_id':f['p']+'-wrong-target-before',
        'rows':json.dumps([{'source_row':view['items'][0]['source_row'],'warehouse':origin,'qty':1,'bags':0}])},store),('PermissionError',))
    assert {dt:len(lst(dt,{},['name'],ktt)) for dt in before}==before
    receipt=rpc('kh_aph.factory_transfer.receive',receive,store)
    entry=get('Stock Entry',receipt['name'],ktt)
    assert entry['docstatus']==1 and entry['outgoing_stock_entry']==prepared['name']
    assert entry['items'][0]['s_warehouse']==TRANSIT and entry['items'][0]['t_warehouse']==destination
    after={dt:len(lst(dt,{},['name'],ktt)) for dt in before}
    assert after['Stock Entry']==before['Stock Entry']+1 and after['Payment Ledger Entry']==before['Payment Ledger Entry']
    assert rpc('kh_aph.factory_transfer.receive',receive,store)==receipt
    assert {dt:len(lst(dt,{},['name'],ktt)) for dt in before}==after
    denied(lambda:rpc('kh_aph.factory_transfer.receive',{**receive,'request_id':f['p']+'-wrong-target',
        'rows':json.dumps([{'source_row':view['items'][0]['source_row'],'warehouse':origin,'qty':1,'bags':0}])},store))
    # Chiều ngược lại: cửa hàng gửi, nhà máy chỉ nhận vào nhóm nhà máy mình.
    back=rpc('kh_aph.factory_transfer.send',{'company':f['aph'],'request_id':f['p']+'-store-factory',
        'rows':json.dumps([{'item_code':f['A'],'warehouse':destination,'qty':1,'bags':0}]),
        'sent_date':f['date'],'carrier':'Xe quay lại','destination':origin},store)
    back_view=rpc('kh_aph.factory_transfer.preview',{'stock_entry':back['name']},factory)
    raw_redirect=insert({'doctype':'Stock Entry','stock_entry_type':'Material Transfer','purpose':'Material Transfer',
        'company':f['aph'],'posting_date':f['date'],'outgoing_stock_entry':back['name'],'items':[
            {'item_code':f['A'],'qty':1,'uom':'Kg','conversion_factor':1,'s_warehouse':TRANSIT,'t_warehouse':destination,
             'against_stock_entry':back['name'],'ste_detail':back_view['items'][0]['source_row']}]},ktt)
    denied(lambda:submit(raw_redirect,store),text='Nhận khác kho dự kiến')
    back_receipt=rpc('kh_aph.factory_transfer.receive',{'stock_entry':back['name'],'request_id':f['p']+'-factory-receive',
        'rows':json.dumps([{'source_row':back_view['items'][0]['source_row'],'warehouse':origin,'qty':1,'bags':0}]),
        'received_date':f['date'],'receiver':'Kho nhà máy nhận'},factory)
    assert get('Stock Entry',back_receipt['name'],ktt)['items'][0]['t_warehouse']==origin
    denied(lambda:get('Warehouse',destination,factory),('PermissionError',))
    assert seed['docstatus']==1
    emit('HTTP_014_CHUYEN_KHO_TACH_NHAN_SU','PASS',{'factory_sender_store_receiver':True,'quantity_projection_only':True,
        'native_receipt_and_retry':True,'source_warehouse_and_document_still_denied':True,'no_customer_debt':True})
