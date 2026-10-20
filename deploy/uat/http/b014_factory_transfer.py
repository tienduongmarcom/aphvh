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
