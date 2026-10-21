"""UX-01 PR-A: Workspace mới song song và áp cấu hình người dùng (chạy thử mặc định)."""
import json


def chay(rpc, get, lst, denied, f, phien, emit):
    for ten in ('Bán hàng', 'Kho vận', 'Tiền và kế toán', 'Nhà máy'):
        ws = get('Workspace', ten)
        heads = [c for c in json.loads(ws['content']) if c['type'] == 'header']
        assert len(heads) == 3 and ws['shortcuts'] and ws['roles'], ten
    assert get('Workspace', 'Trung tâm Bán hàng')['is_hidden'] == 1
    assert get('Workspace', 'Dữ liệu và cấu hình')['shortcuts']
    sidebar = lst('Custom Sidebar', {'module': 'Kh Aph', 'user': ['is', 'not set']}, ['name', 'label'])
    assert len(sidebar) == 1 and sidebar[0]['label'] == 'Vận hành', sidebar
    configured = get('Custom Sidebar', sidebar[0]['name'])['sidebar_items']
    assert {r['link_to'] for r in configured if r['link_type'] == 'Workspace' and not r['hidden']} == {'Bán hàng', 'Kho vận', 'Tiền và kế toán', 'Nhà máy', 'Dữ liệu và cấu hình'}
    assert all(r['hidden'] for r in configured if r['link_type'] in ('DocType', 'Report'))
    assert any(r['link_type'] == 'Workspace' and r['link_to'] == 'Trung tâm Bán hàng' and r['hidden'] for r in configured)
    assert get('Workspace', 'Trung tâm Bán hàng')['name']  # Workspace cũ giữ nguyên để quay lui
    assert get('DocType', 'APH Shared Sales Order')['autoname'] == 'format:DBC-{YYYY}-{#####}'
    bang = [{'user': f['dung'], 'nhom': 'nha_may'}]
    thu = rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps(bang)})
    assert thu['chay_thu'] and get('User', f['dung'])['default_workspace'] != 'Nhà máy'
    denied(lambda: rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps(bang)}, phien(f['ktbh'])), ('PermissionError',))
    denied(lambda: rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps([{'user': f['ktbh'], 'nhom': 'ban_hang', 'kho': [f['kho']]}])}))
    that = rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps(bang), 'chay_that': 1})
    assert not that['chay_thu'] and get('User', f['dung'])['default_workspace'] == 'Nhà máy'
    mp = rpc('kh_aph.ux_task.ap_dung_nguoi_dung', {'bang': json.dumps([{'user': f['ktbh'], 'nhom': 'ban_hang', 'module_profile': 1}]), 'chay_that': 1})
    assert any(k['viec'] == 'module_profile' for k in mp['thay_doi'])
    ktbh = phien(f['ktbh'])
    assert get('User', f['ktbh'])['module_profile'] == '9xLab - Bán hàng'
    assert lst('Sales Invoice', {}, ['name'], ktbh) is not None and lst('Customer', {}, ['name'], ktbh) is not None
    emit('HTTP_UX01_WORKSPACE_APPLY', 'PASS', {'workspaces': 5, 'old_kept': True, 'dry_run_default': True,
                                               'sales_not_locked': True, 'admin_only': True})


def do_ux3(rpc, get, insert, lst, denied, f, phien, emit):
    """UX-3: tìm khách theo SĐT liên hệ/MST/tên, công nợ một khách tách theo đơn vị, chỉ trong phạm vi quyền."""
    import hashlib
    so = '09' + str(int(hashlib.sha256(f['p'].encode()).hexdigest(), 16))[:8]
    insert({'doctype': 'Contact', 'first_name': f['p'] + ' Liên hệ', 'phone_nos': [{'phone': so, 'is_primary_phone': 1}],
            'links': [{'link_doctype': 'Customer', 'link_name': f['kh1']}]})
    ktbh = phien(f['ktbh'])
    kq = rpc('kh_aph.ux_task.tim_khach', {'q': so}, ktbh)
    assert [x['name'] for x in kq] == [f['kh1']] and kq[0]['khop'] == 'điện thoại liên hệ', kq
    ten = rpc('kh_aph.ux_task.tim_khach', {'q': f['p']}, ktbh)
    assert {f['kh1'], f['kh2']} <= {x['name'] for x in ten} and len(ten) >= 2  # trùng nhiều khách: trả danh sách, không tự chọn
    denied(lambda: rpc('kh_aph.ux_task.tim_khach', {'q': 'a'}, ktbh))
    identity = rpc('kh_aph.ux_task.customer_identity', {'customer': f['kh1']}, ktbh)
    assert set(identity) == {'name', 'customer_name', 'mobile_no', 'primary_address'} and identity['name'] == f['kh1'], identity
    suggestions = rpc('kh_aph.ux_task.customer_query', {'doctype': 'Customer', 'txt': f['p'], 'searchfield': 'name', 'start': 0, 'page_len': 20}, ktbh)
    assert {f['kh1'], f['kh2']} <= {x[0] for x in suggestions} and all(len(x) == 4 for x in suggestions), suggestions
    denied(lambda: rpc('kh_aph.ux_task.customer_query', {'doctype': 'User', 'txt': '', 'searchfield': 'name', 'start': 0, 'page_len': 20}, ktbh))
    # Mô phỏng import Address riêng, không đánh dấu chính và không điền cache Customer.
    source = get('Customer', f['kh1'])
    def customer(suffix):
        return insert({'doctype': 'Customer', 'customer_name': f['p'] + suffix, 'customer_type': 'Company',
                       'customer_group': source['customer_group'], 'territory': source['territory'],
                       'kh_aph_xuat_hoa_don': source['kh_aph_xuat_hoa_don']})['name']
    imported, empty = customer('-IMPORT-DC'), customer('-KHONG-DC')
    def address(line, owner, disabled=0):
        return insert({'doctype': 'Address', 'address_title': f['p'] + line, 'address_type': 'Billing',
            'address_line1': line, 'city': 'Ha Noi', 'country': 'Vietnam', 'disabled': disabled,
            'is_primary_address': 0, 'is_shipping_address': 0,
            'links': [{'link_doctype': 'Customer', 'link_name': owner}]})
    address('KHONG-DUNG-DA-NGUNG', imported, 1)
    address('KHONG-DUNG-KHACH-KHAC', empty)
    marker = 'Dia chi import UX04'
    addr = address(marker, imported)
    before = get('Customer', imported)
    assert not before.get('primary_address') and not before.get('customer_primary_address'), before['name']
    def identity():
        value = rpc('kh_aph.ux_task.customer_identity', {'customer': imported}, ktbh)
        assert marker in value['primary_address'] and 'KHONG-DUNG' not in value['primary_address'], value
        return value
    assert not identity()['mobile_no']
    # Thêm rồi sửa SĐT sau khi địa chỉ đã import: đọc lại hồ sơ liên kết, không sửa Customer.
    contact = insert({'doctype': 'Contact', 'first_name': f['p'] + ' Import', 'is_primary_contact': 0,
        'phone_nos': [{'phone': '0900000141', 'is_primary_phone': 1}],
        'links': [{'link_doctype': 'Customer', 'link_name': imported}]})
    assert identity()['mobile_no'] == '0900000141'
    contact['phone_nos'][0]['phone'] = '0900000142'
    contact = rpc('frappe.client.save', {'doc': json.dumps(contact)})
    assert identity()['mobile_no'] == '0900000142'
    contact['phone_nos'] = []
    contact = rpc('frappe.client.save', {'doc': json.dumps(contact)})
    assert not identity()['mobile_no']
    contact['phone_nos'] = [{'phone': '0900000143'}]  # số đã thêm nhưng chưa chọn ô SĐT chính
    rpc('frappe.client.save', {'doc': json.dumps(contact)})
    assert identity()['mobile_no'] == '0900000143'
    query = rpc('kh_aph.ux_task.customer_query', {'doctype': 'Customer', 'txt': f['p'] + '-IMPORT-DC',
        'searchfield': 'name', 'start': 0, 'page_len': 20}, ktbh)
    assert len(query) == 1 and query[0][0] == imported and query[0][2] == '0900000143' and marker in query[0][3], query
    matches = rpc('kh_aph.ux_task.tim_khach', {'q': f['p'] + '-IMPORT-DC'}, ktbh)
    assert len(matches) == 1 and matches[0]['mobile_no'] == '0900000143' and marker in matches[0]['primary_address'], matches
    after = get('Customer', imported)
    assert all(before.get(k) == after.get(k) for k in ('modified', 'primary_address', 'mobile_no',
        'customer_primary_address', 'customer_primary_contact')), imported
    # Khách rỗng riêng để Chrome kiểm chuyển khách không giữ dữ liệu người trước.
    f.update(ux_identity_customer=imported, ux_identity_address=marker, ux_identity_phone='0900000143',
             ux_empty_customer=customer('-RONG-DC'))
    cn = rpc('kh_aph.ux_task.cong_no_khach', {'customer': f['kh1']}, ktbh)
    assert set(cn) == {'customer', 'xem_hoa_don', 'xem_tien', 'don_vi'}
    for d in cn['don_vi']:
        assert abs(sum(h['outstanding'] for h in d['hoa_don']) - d['phai_thu']) < 0.01 and d['qua_han'] <= d['phai_thu'] + 0.01
    assert 'valuation' not in json.dumps(cn) and 'incoming_rate' not in json.dumps(cn)
    scoped = rpc('kh_aph.ux_task.cong_no_khach', {'customer': f['kh1']}, phien(f['scope_co']))
    assert all(d['company'] == f['aph'] for d in scoped['don_vi']), scoped
    emit('HTTP_UX03_TIM_KHACH_CONG_NO', 'PASS', {'phone_contact_match': True, 'many_matches_listed': len(ten),
         'per_company': [d['company'] for d in cn['don_vi']], 'company_scope': True, 'linked_identity_add_update_clear': True, 'customer_not_backfilled': True})


def do_ux0(get, insert, submit, lst, f, emit):
    """UX-0 số đo máy trên trình duyệt: Desk hiện tại (A) so với UX-01 (B), cùng dữ liệu UAT, không ghi."""
    import os, subprocess
    from pathlib import Path
    assert os.environ.get('GITHUB_ACTIONS') == 'true'
    orders = lst('APH Shared Sales Order', {'docstatus': 1}, ['name'])
    inv = [x['name'] for x in lst('Sales Invoice', {'docstatus': 1, 'is_return': 0, 'outstanding_amount': ['>', 0]}, ['name'])]
    if not inv:
        si = submit(insert({'doctype': 'Sales Invoice', 'company': f['aph'], 'customer': f['kh1'], 'posting_date': f['date'],
                            'due_date': f['date'], 'items': [{'item_code': f['A'], 'qty': 1, 'rate': 30000, 'uom': 'Kg', 'conversion_factor': 1}]}))
        inv = [si['name']]
    data = {'order': orders[0]['name'] if orders else '', 'invoice': inv[0],
            **{k: f[k] for k in ('ux_identity_customer', 'ux_identity_address', 'ux_identity_phone', 'ux_empty_customer')}}
    before = lst('APH Shared Sales Order', {}, ['name'])
    r = subprocess.run(['node', str(Path(__file__).with_name('ux0-desk.mjs')), json.dumps(data)], text=True, capture_output=True, timeout=300)
    assert r.returncode == 0, (r.stdout[-1500:], r.stderr[-2500:])
    cases = [json.loads(x) for x in r.stdout.splitlines() if x.startswith('{"case":')]
    assert len(cases) == 1 and cases[0]['status'] == 'PASS', r.stdout[-1500:]
    assert lst('APH Shared Sales Order', {}, ['name']) == before  # Chrome chỉ mở đơn nháp, không ghi
    emit(cases[0]['case'], 'PASS', cases[0]['detail'])
