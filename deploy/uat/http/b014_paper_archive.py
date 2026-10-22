"""Nhập sau từ giấy dự phòng bằng phiếu chuẩn; lưu giấy không ghi sổ lần hai."""
import json
import uuid


def chay(rpc, get, insert, submit, lst, denied, ktt, f, emit):
    flag, number, actual, location, file = ('kh_aph_tu_giay_tay', 'kh_aph_so_giay_tay',
        'kh_aph_thuc_te_luc', 'kh_aph_noi_luu_giay_tay', 'kh_aph_anh_giay_tay')
    paper = {flag: 1, number: f["p"] + ' / CH1 / Q1 / 001', actual: f["date"] + ' 00:00:00',
             location: 'Tập giấy tay tại kho vệ tinh'}
    payload = {'doctype': 'Stock Entry', 'stock_entry_type': 'Material Receipt', 'company': f['aph'],
        'posting_date': f['date'], **paper, 'items': [{'item_code': f['A'], 't_warehouse': f['kho'],
            'qty': 2, 'basic_rate': 20000, 'expense_account': f['acc']['cp']}]}
    def counts():
        return {dt: len(lst(dt, {}, ['name'], ktt)) for dt in ('GL Entry', 'Stock Ledger Entry', 'Sales Invoice', 'Payment Entry')}
    def save(doc): return rpc('frappe.client.save', {'doc': json.dumps(doc)}, ktt)
    before = counts()
    draft = insert(payload, ktt)
    assert counts() == before and draft[number] == paper[number].upper()
    denied(lambda: insert(payload, ktt), ('DuplicateEntryError', 'UniqueValidationError'))
    assert len(lst('Stock Entry', {number: draft[number], 'company': f['aph']}, ['name'], ktt)) == 1
    proof = insert({'doctype': 'File', 'file_name': uuid.uuid4().hex + '.txt', 'is_private': 1,
        'attached_to_doctype': 'Stock Entry', 'attached_to_name': draft['name'], 'content': json.dumps({'uat': 'giay-tay'})}, ktt)
    draft[file] = proof['file_url']; draft = save(draft)
    denied(lambda: save({**draft, file: '/files/giay-cong-khai.pdf'}))
    denied(lambda: rpc('frappe.client.delete', {'doctype': 'File', 'name': proof['name']}, ktt))
    assert ktt(proof['file_url']) == {'uat': 'giay-tay'}
    posted = submit(draft, ktt)
    assert posted['docstatus'] == 1 and posted[actual] == paper[actual]
    denied(lambda: save({**posted, number: 'DOI-SO-GIAY'}))
    denied(lambda: save({**posted, flag: 0}))
    posted[location] = 'Tập kế toán cửa hàng / giấy tay / tháng10'
    posted = save(posted)
    assert posted[location].startswith('Tập kế toán')
    after_posting = counts()
    assert after_posting['Stock Ledger Entry'] > before['Stock Ledger Entry']
    posted = save(posted)
    assert counts() == after_posting, 'Lưu giấy nguồn ghi sổ lần hai'
    denied(lambda: save({**posted, actual: f['date'] + ' 01:00:00'}))
    cancelled = rpc('frappe.client.cancel', {'doctype': 'Stock Entry', 'name': posted['name']}, ktt)
    old = get('Stock Entry', posted['name'], ktt)
    assert old['docstatus'] == 2 and not old.get('kh_aph_khoa_giay_tay') and old[file] == proof['file_url']
    denied(lambda: insert(payload, ktt))
    # Như Sửa đổi native: các ô no_copy không lấy từ bản payload đã cũ;
    # controller kế thừa giấy/vị trí hiện tại từ phiếu đã hủy.
    amended = {key: value for key, value in payload.items() if key not in paper}
    amended['amended_from'] = old['name']
    amended = insert(amended, ktt)
    assert amended['amended_from'] == old['name'] and amended[number] == old[number] and amended[file] == old[file]
    assert amended.get('kh_aph_khoa_giay_tay')

    # Đính giấy vào phiếu xuất/thu đã nhập đúng chỉ thay hồ sơ, không xuất/thu lần nữa.
    state = counts()
    for dt in ('Delivery Note', 'Payment Entry'):
        filters = {'company': f['aph'], 'docstatus': 1}
        if dt == 'Delivery Note': filters['is_return'] = 0
        source = get(dt, lst(dt, filters, ['name'], ktt)[0]['name'], ktt)
        source.update({**paper, number: f['p'] + ' / ' + dt + ' / 001', location: 'Tập kế toán cửa hàng'})
        marked = save(source)
        assert marked[flag] == 1 and marked[number] == source[number].upper()
    assert counts() == state
    emit('HTTP_014_GIAY_TAY_NHAP_BO_SUNG', 'PASS', {'native_documents_only': True,
        'draft_no_ledger': True, 'unique_paper': True, 'paper_identity_kept': True,
        'private_file_kept': True, 'cancel_amend_history': True, 'actual_date_separate': True,
        'archive_on_posted_issue_payment_no_second_posting': True})
