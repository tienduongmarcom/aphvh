"""NM02–04 — ghi sản xuất/đóng gói một lần bằng phiên nhà máy (Dũng, không xem giá vốn) trên loại phiếu kg sẵn có."""
import json

DD = "Dở dang dây chuyền đậu - APH"
CDG = "Kho chờ đóng gói - APH"
TP = "Kho thành phẩm nhà máy - APH"


def chay(rpc, get, insert, submit, lst, denied, f, phien, emit):
    dung = phien(f['dung'])
    roots = [c for c in lst('Cost Center', {'company': f['aph'], 'is_group': 1}, ['name', 'parent_cost_center']) if not c['parent_cost_center']]
    xuong = insert({'doctype': 'Cost Center', 'cost_center_name': f['p'] + ' Xưởng đậu', 'company': f['aph'],
                    'parent_cost_center': roots[0]['name'], 'is_group': 0, 'kh_aph_loai_ttcp': 'Xưởng sản xuất'})['name']
    group = get('Item', f['A'])['item_group']
    C = insert({'doctype': 'Item', 'item_code': f['p'] + '-C', 'item_name': f['p'] + '-C phụ phẩm', 'item_group': group,
                'stock_uom': 'Kg', 'is_stock_item': 1, 'valuation_method': 'Moving Average'})['name']
    submit(insert({'doctype': 'Stock Entry', 'stock_entry_type': 'Material Transfer', 'company': f['aph'], 'posting_date': f['date'],
                   'items': [{'item_code': f['A'], 'qty': 100, 'uom': 'Kg', 'conversion_factor': 1,
                              's_warehouse': f['kho'], 't_warehouse': DD}]}))
    ctx = rpc('kh_aph.factory_production.context', {'company': f['aph']}, dung)
    assert DD in [l['warehouse'] for l in ctx['lines']] and xuong in ctx['workshops'], ctx
    wip = {r['item_code']: r['qty'] for r in rpc('kh_aph.factory_production.wip', {'warehouse': DD}, dung)}
    assert wip.get(f['A']) == 100 and 'rate' not in json.dumps(ctx)
    denied(lambda: rpc('kh_aph.factory_production.context', {'company': f['aph']}, phien(f['tp'])), ('PermissionError',))
    emit('HTTP_NM02_CONTEXT_WIP', 'PASS', {'line': DD, 'wip_kg': 100, 'quantity_only': True})

    def counts():
        return {dt: len(lst(dt, {}, ['name'])) for dt in ('Stock Entry', 'Stock Ledger Entry', 'Payment Ledger Entry')}
    ins = [{'item_code': f['A'], 'warehouse': DD, 'qty': 60}]
    outs = [{'item_code': f['B'], 'warehouse': CDG, 'qty': 55}]
    args = {'kind': 'san_xuat', 'company': f['aph'], 'request_id': f['p'] + '-sx-1', 'posting_date': f['date'],
            'inputs': json.dumps(ins), 'outputs': json.dumps(outs), 'workshop': xuong, 'note': 'UAT giảm ẩm tự nhiên'}
    before = counts()
    result = rpc('kh_aph.factory_production.record', args, dung)
    entry = get('Stock Entry', result['name'])
    assert entry['docstatus'] == 1 and entry['stock_entry_type'] == 'Sản xuất theo kg' and entry['kh_aph_xuong'] == xuong
    assert entry['kh_aph_loss_type'] == 'Hao hụt tự nhiên' and abs(float(entry['kh_aph_process_loss_kg']) - 5) < 1e-6
    assert entry['kh_aph_costing_rule'] == 'kg-v4' and entry['kh_aph_production_actor'] == f['dung']
    masked = get('Stock Entry', result['name'], dung)
    assert not any(r.get('basic_rate') or r.get('valuation_rate') for r in masked['items'])
    after = counts()
    assert after['Stock Entry'] == before['Stock Entry'] + 1 and after['Payment Ledger Entry'] == before['Payment Ledger Entry']
    assert rpc('kh_aph.factory_production.record', args, dung) == result and counts() == after
    denied(lambda: rpc('kh_aph.factory_production.record', {**args, 'note': 'đổi nội dung'}, dung))
    wip = {r['item_code']: r['qty'] for r in rpc('kh_aph.factory_production.wip', {'warehouse': DD}, dung)}
    assert wip.get(f['A']) == 40, wip
    emit('HTTP_NM02_RECORD_REPLAY', 'PASS', {'used': 60, 'out': 55, 'loss_natural': 5, 'wip_left': 40, 'retry_one_entry': True})

    for bad in ({**args, 'request_id': 'over', 'inputs': json.dumps([{**ins[0], 'qty': 41}])},
                {**args, 'request_id': 'no-shop', 'workshop': ''},
                {**args, 'request_id': 'no-reason', 'note': ''},
                {**args, 'request_id': 'sell-wh', 'outputs': json.dumps([{**outs[0], 'warehouse': f['kho']}])},
                {**args, 'request_id': 'price', 'outputs': json.dumps([{**outs[0], 'rate': 1}])},
                {**args, 'request_id': 'vh', 'inputs': json.dumps([{**ins[0], 'warehouse': f['kho_vh']}])}):
        denied(lambda bad=bad: rpc('kh_aph.factory_production.record', bad, dung))
    denied(lambda: rpc('frappe.client.set_value', {'doctype': 'Stock Entry', 'name': result['name'],
                                                   'fieldname': 'kh_aph_production_note', 'value': 'sửa'}))
    assert counts() == after
    emit('HTTP_NM02_TAMPER', 'PASS', {'over_wip': 'denied', 'no_workshop_or_reason': 'denied', 'sales_target': 'denied', 'stamp_kept': True})

    multi = rpc('kh_aph.factory_production.record', {**args, 'request_id': f['p'] + '-sx-2', 'note': '',
        'inputs': json.dumps([{**ins[0], 'qty': 40}]),
        'outputs': json.dumps([{'item_code': f['B'], 'warehouse': CDG, 'qty': 30}, {'item_code': C, 'warehouse': CDG, 'qty': 10}])}, dung)
    me = get('Stock Entry', multi['name'])
    assert me['stock_entry_type'] == 'Đóng gói theo kg' and me['docstatus'] == 1 and me['kh_aph_xuong'] == xuong
    assert not rpc('kh_aph.factory_production.wip', {'warehouse': DD}, dung)
    emit('HTTP_NM02_MULTI_OUTPUT', 'PASS', {'type': 'Đóng gói theo kg', 'outputs': 2, 'wip_left': 0})

    pack = {'kind': 'dong_goi', 'company': f['aph'], 'posting_date': f['date'], 'workshop': '', 'note': ''}
    ok = rpc('kh_aph.factory_production.record', {**pack, 'request_id': f['p'] + '-dg-1',
        'inputs': json.dumps([{'item_code': f['B'], 'warehouse': CDG, 'qty': 20}]),
        'outputs': json.dumps([{'item_code': f['B'], 'warehouse': TP, 'qty': 20}])}, dung)
    assert get('Stock Entry', ok['name'])['stock_entry_type'] == 'Đóng gói thành phẩm'
    lech = {**pack, 'request_id': f['p'] + '-dg-2', 'inputs': json.dumps([{'item_code': f['B'], 'warehouse': CDG, 'qty': 10}]),
            'outputs': json.dumps([{'item_code': f['B'], 'warehouse': TP, 'qty': 9.5}])}
    denied(lambda: rpc('kh_aph.factory_production.record', lech, dung))
    denied(lambda: rpc('kh_aph.factory_production.record', {**lech, 'confirm_difference': 1}, dung))
    done = rpc('kh_aph.factory_production.record', {**lech, 'confirm_difference': 1, 'note': 'UAT cân lại thiếu 0,5 kg'}, dung)
    de = get('Stock Entry', done['name'])
    assert de['kh_aph_xac_nhan_lech_kg'] == 1 and abs(float(de['kh_aph_process_loss_kg']) - 0.5) < 1e-6
    emit('HTTP_NM04_PACK_BALANCE', 'PASS', {'balanced': ok['name'], 'difference_needs_confirm_and_reason': True})
