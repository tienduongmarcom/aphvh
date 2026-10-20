"""UX-01 — giao diện theo công việc (docs/dac-ta-ux-01.md). Cờ `kh_aph_ux_task_first`, mặc định tắt.

Năm khu nghiệp vụ, giữ Nhà máy riêng; gom đủ danh mục trước khi ẩn các thế hệ cũ; quay lui = đổi Workspace mặc định về cũ / tắt cờ. Ba khối: Việc cần làm (có số đếm theo quyền native của
danh sách), Thao tác nhanh, Tra cứu. Áp cấu hình người dùng bằng bảng ánh xạ, mặc định CHẠY THỬ (chỉ in thay đổi).
PR-B: nút "Việc tiếp theo" trên chứng từ (public/js/ux_buoc_tiep.js) chỉ bấm hộ các nút nghiệp vụ đã có; không hàm ghi mới.
"""
import json

import frappe
from frappe.utils import cint

FLAG = 'kh_aph_ux_task_first'
MODULE = 'Kh Aph'

NHOM = {
    'ban_hang': 'Bán hàng',
    'kho': 'Kho vận',
    'tien': 'Tiền và kế toán',
    'nha_may': 'Nhà máy',
    'du_lieu': 'Dữ liệu và cấu hình',
}

# (nhãn, loại, đích, bộ lọc số đếm hoặc None, doc_view)
_LAM = {
    'ban_hang': [
        ('Đơn chờ xác nhận', 'DocType', 'APH Shared Sales Order', {'docstatus': 0}, 'List'),
        ('Đơn chờ duyệt giá', 'DocType', 'APH Shared Sales Order', {'docstatus': 0, 'kh_aph_duoi_san': 1, 'kh_aph_duyet_san_boi': ['is', 'not set']}, 'List'),
        ('Phiếu chờ xuất kho', 'DocType', 'Delivery Note', {'docstatus': 0}, 'List'),
        ('Hàng đang giao', 'DocType', 'Delivery Note', {'docstatus': 1, 'kh_aph_delivery_state': 'Đang giao'}, 'List'),
        ('Đã nhận, thiếu bản ký', 'DocType', 'Delivery Note', {'docstatus': 1, 'is_return': 0, 'kh_aph_delivery_state': 'Khách đã nhận', 'kh_aph_ban_ky': ['is', 'not set']}, 'List'),
    ],
    'kho': [
        ('Phiếu chờ xuất kho', 'DocType', 'Delivery Note', {'docstatus': 0}, 'List'),
        ('Hàng đang giao', 'DocType', 'Delivery Note', {'docstatus': 1, 'kh_aph_delivery_state': 'Đang giao'}, 'List'),
        ('Chuyến đang trên đường', 'DocType', 'Stock Entry', {'docstatus': 1, 'purpose': 'Material Transfer', 'add_to_transit': 1, 'per_transferred': ['<', 100]}, 'List'),
        ('Yêu cầu chuyển kho chờ xử lý', 'DocType', 'Material Request', {'docstatus': 1, 'material_request_type': 'Material Transfer', 'status': ['not in', ['Transferred', 'Stopped']]}, 'List'),
    ],
    'tien': [
        ('Hóa đơn còn nợ', 'DocType', 'Sales Invoice', {'docstatus': 1, 'outstanding_amount': ['>', 0]}, 'List'),
        ('Hóa đơn quá hạn', 'DocType', 'Sales Invoice', {'docstatus': 1, 'status': 'Overdue'}, 'List'),
        ('Phiếu thu chờ xác nhận', 'DocType', 'Payment Entry', {'docstatus': 0, 'payment_type': 'Receive'}, 'List'),
    ],
    'nha_may': [
        ('Chuyến đang trên đường', 'DocType', 'Stock Entry', {'docstatus': 1, 'purpose': 'Material Transfer', 'add_to_transit': 1, 'per_transferred': ['<', 100]}, 'List'),
        ('Hàng chờ định giá', 'DocType', 'APH Pending Receipt', {'docstatus': 1, 'status': 'Chờ định giá'}, 'List'),
        ('Đơn mua chờ nhận', 'DocType', 'Purchase Order', {'docstatus': 1, 'per_received': ['<', 100], 'status': ['not in', ['Closed', 'On Hold']]}, 'List'),
    ],
}
_NHANH = {
    'ban_hang': [('Lập đơn bán hàng', 'DocType', 'APH Shared Sales Order', None, 'New'),
                 ('Tìm khách, xem nợ, thu tiền', 'DocType', 'Customer', None, 'List'),
                 ('Tổng hợp bán theo khách', 'Report', 'Tong hop ban hang theo khach', None, '')],
    'kho': [('Tồn kho và nhận/chuyển hàng', 'Report', 'Ton kho so luong', None, ''),
            ('Kiểm kê', 'DocType', 'Stock Reconciliation', None, 'New')],
    'tien': [('Tìm khách, xem nợ, thu tiền', 'DocType', 'Customer', None, 'List'),
             ('Khách cần gọi hôm nay', 'Report', 'Khach can goi hom nay', None, '')],
    'nha_may': [('Nhận hàng / chuyển / ghi sản xuất', 'Report', 'Ton kho so luong', None, ''),
                ('Phiếu quỹ nhà máy', 'DocType', 'APH Phieu quy nha may', None, 'New')],
}
_TRA = {
    'ban_hang': [('Khách hàng', 'DocType', 'Customer', None, 'List'), ('Đơn bán', 'DocType', 'APH Shared Sales Order', None, 'List'),
                 ('Phiếu giao hàng', 'DocType', 'Delivery Note', None, 'List'), ('Đơn quá hạn giao', 'Report', 'Don qua han giao', None, '')],
    'kho': [('Phiếu kho', 'DocType', 'Stock Entry', None, 'List'), ('Chênh lệch kiểm kê chờ xử lý', 'Report', 'Chenh lech kiem ke cho xu ly', None, ''),
            ('Đề nghị bổ sung hàng', 'Report', 'De nghi bo sung hang', None, '')],
    'tien': [('Sổ quỹ và tiền gửi', 'Report', 'So quy va tien gui', None, ''), ('Tiền thu hộ chưa xử lý', 'Report', 'Tien thu ho chua xu ly', None, ''),
             ('Khách chưa xác nhận công nợ', 'Report', 'Khach chua xac nhan cong no', None, '')],
    'nha_may': [('Phiếu kho', 'DocType', 'Stock Entry', None, 'List'), ('Tiêu hao so với định mức', 'Report', 'Tieu hao so voi dinh muc', None, '')],
}
VAI_TRO = {
    'ban_hang': ('Kế toán bán hàng', 'Sales User', 'Sales Manager', 'Accounts User', 'Accounts Manager', 'System Manager'),
    'kho': ('Thủ kho bán hàng', 'Stock User', 'Stock Manager', 'Kế toán nhà máy', 'Accounts User', 'Accounts Manager', 'System Manager'),
    'tien': ('Accounts User', 'Accounts Manager', 'Kế toán bán hàng', 'Kế toán nhà máy', 'System Manager'),
    'nha_may': ('Kế toán nhà máy', 'Stock Manager', 'Accounts Manager', 'System Manager'),
}


# Module Profile theo nhóm: chỉ ẩn phân hệ chắc chắn không dùng (ẩn menu, không thay quyền chứng từ).
_AN = ('Manufacturing', 'Projects', 'Assets', 'Quality Management', 'Support', 'Maintenance', 'Subcontracting',
       'Website', 'Portal', 'Social', 'CRM', 'Telephony', 'Communication', 'EDI', 'Regional', 'Bulk Transaction')
AN_THEO_NHOM = {
    'ban_hang': _AN + ('Buying',),
    'kho': _AN,
    'tien': tuple(m for m in _AN if m != 'Assets'),
    'du_lieu': (),
    'nha_may': tuple(m for m in _AN if m != 'Manufacturing'),
}


def enabled():
    return bool(cint(frappe.conf.get(FLAG)))


def _hop_le(x):
    nhan, loai, dich, loc, _view = x
    if not frappe.db.exists(loai, dich):
        return False
    if loc and loai == 'DocType':
        meta = frappe.get_meta(dich)
        return all(k == 'docstatus' or meta.has_field(k) for k in loc)
    return True


def _khoi(nhom):
    """Một danh mục nguồn cho mỗi lối cũ; native vẫn kiểm quyền từng đích."""
    from kh_aph import trung_tam_ban, kho_van_hanh, tien_vay, du_lieu
    nguon = {'ban_hang': trung_tam_ban, 'kho': kho_van_hanh, 'tien': tien_vay, 'du_lieu': du_lieu}
    if nhom == 'du_lieu':
        cau_hinh = [
            ('Giá sàn bán hàng', 'DocType', 'APH Gia san', None, 'List'),
            ('Tài khoản nhận tiền và thu hộ', 'DocType', 'APH Funds Route', None, 'List'),
            ('Khoản mục chi nhà máy', 'DocType', 'APH Khoan muc chi nha may', None, 'List'),
            ('Mã hàng', 'DocType', 'Item', None, 'List'),
            ('Định mức sản xuất', 'DocType', 'BOM', None, 'List'),
        ]
        ds = [(x[0], x[1], x[2], None, 'List' if x[1] == 'DocType' else '') for x in du_lieu.workspace_links()]
        return [('Dữ liệu và đầu kỳ', ds, 4), ('Cấu hình theo nhiệm vụ', cau_hinh, 4)]
    tra = list(_TRA[nhom])
    if nhom in nguon:
        tra += [(x[0], x[1], x[2], x[3], 'List' if x[1] == 'DocType' else '') for x in nguon[nhom].workspace_links()]
    if nhom in ('kho', 'nha_may'):
        tra += [
            ('Bản ký chờ đối chiếu', 'DocType', 'Delivery Note', {'docstatus': 1, 'is_return': 0, 'kh_aph_ban_ky': ['is', 'set'], 'kh_aph_doi_chieu_boi': ['is', 'not set']}, 'List'),
            ('Chênh lệch giao nhận', 'DocType', 'Delivery Note', {'docstatus': 1, 'is_return': 0, 'kh_aph_chenh_lech_state': ['in', ['Cần xử lý', 'Đang xử lý']]}, 'List'),
        ]
    if nhom == 'tien':
        tra += [('Công nợ nhà cung cấp', 'Report', 'Accounts Payable', None, ''),
                ('Sổ kế toán hộ kinh doanh', 'Report', 'So ke toan HKD', None, ''),
                ('Sổ doanh thu hộ kinh doanh', 'Report', 'So doanh thu HKD', None, ''),
                ('Bán hàng và hóa đơn MISA', 'Report', 'Ban hang co hoa don', None, ''),
                ('Lãi gộp quản trị', 'Report', 'Lai gop quan tri', None, ''),
                ('Dòng tiền 7/30 ngày', 'Report', 'Dong tien 7 30 ngay', None, ''),
                ('Tồn kho theo tài khoản và địa điểm', 'Report', 'Ton kho theo tai khoan va dia diem', None, '')]
    return [('Hôm nay cần xử lý', _LAM[nhom], 6), ('Thao tác nhanh', _NHANH[nhom], 4), ('Tra cứu', tra, 3)]


def _workspace(nhom):
    ten = NHOM[nhom]
    khoi = _khoi(nhom)
    content, shortcuts, dung, dich_da_co = [], [], set(), set()
    for i, (tieu_de, ds, col) in enumerate(khoi):
        ds = [x for x in ds if _hop_le(x)]
        content.append({'id': f'{nhom}-h{i}', 'type': 'header', 'data': {'text': f'<span class="h4"><b>{tieu_de}</b></span>', 'col': 12}})
        for j, x in enumerate(ds):
            nhan, loai, dich, loc, view = x
            key = (loai, dich, json.dumps(loc or {}, sort_keys=True), view or ('List' if loai == 'DocType' else ''))
            if key in dich_da_co:
                continue
            dich_da_co.add(key)
            khoa = nhan if nhan not in dung else f'{nhan} ({tieu_de.lower()})'
            dung.add(khoa)
            content.append({'id': f'{nhom}-{i}-{j}', 'type': 'shortcut', 'data': {'shortcut_name': khoa, 'col': col}})
            sc = {'label': khoa, 'type': loai, 'link_to': dich, 'color': 'Blue' if i == 1 else 'Grey', 'doc_view': view or ''}
            if loc:
                sc.update({'stats_filter': json.dumps(loc, ensure_ascii=False), 'format': '{} việc'})
            shortcuts.append(sc)
        content.append({'id': f'{nhom}-s{i}', 'type': 'spacer', 'data': {'col': 12}})
    ws = frappe.get_doc('Workspace', ten) if frappe.db.exists('Workspace', ten) else frappe.new_doc('Workspace')
    ws.update({'label': ten, 'title': ten, 'public': 1, 'is_hidden': 0, 'module': MODULE, 'icon': {'ban_hang': 'sell', 'kho': 'stock', 'tien': 'money-coins-1', 'nha_may': 'stock', 'du_lieu': 'database'}[nhom],
               'content': json.dumps(content, ensure_ascii=False)})
    ws.set('shortcuts', shortcuts)
    from kh_aph.du_lieu import VAI_TRO_LAP
    roles = VAI_TRO_LAP if nhom == 'du_lieu' else VAI_TRO[nhom]
    ws.set('roles', [{'role': r} for r in sorted(roles) if frappe.db.exists('Role', r)])
    ws.flags.ignore_permissions = True
    ws.save() if not ws.is_new() else ws.insert()
    return ten


def _module_profile(nhom):
    ten = '9xLab - ' + NHOM[nhom]
    muon = [m for m in AN_THEO_NHOM[nhom] if frappe.db.exists('Module Def', m)]
    if frappe.db.exists('Module Profile', ten):
        doc = frappe.get_doc('Module Profile', ten)
        # Module Profile.on_update khóa chứng từ và xếp hàng cập nhật người dùng: không lưu lại khi không đổi
        # (chạy lại bộ cài liên tiếp từng gặp DocumentLockedError, UAT 39358739479 / Cổng 3 39358741700).
        if sorted(d.module for d in doc.block_modules) == sorted(muon):
            return ten
    else:
        doc = frappe.new_doc('Module Profile')
        doc.module_profile_name = ten
    doc.set('block_modules', [{'module': m} for m in muon])
    doc.flags.ignore_permissions = True
    doc.save() if not doc.is_new() else doc.insert()
    return ten


def schema():
    """Dựng năm khu và profile, chuyển mặc định tên cũ sau khi dựng đủ; không tự cấp quyền."""
    if not enabled():
        return
    _hien_ten_khi_chon()
    result = [_workspace(n) for n in NHOM] + [_module_profile(n) for n in NHOM]
    _an_ten_cu()  # Chỉ ẩn sau khi mọi nơi thay thế dựng thành công.
    return result


# Ô chọn khách/nhà cung cấp hiện TÊN sau khi chọn (chủ dự án 20/10/2026). Mặt hàng thì KHÔNG: cột "Mã hàng" phải hiện mã,
# tên hàng có cột riêng (chủ dự án 20/10/2026, sau 0.16.1). Bản 0.16.1 đã bật cho Item -> tắt lại tường minh.
HIEN_TEN = {'Customer': ('customer_name', '1'), 'Item': ('item_name', '0'), 'Supplier': ('supplier_name', '1')}
# Ô chọn khách: danh sách gợi ý hiện thêm số điện thoại để phân biệt khách trùng tên.
TIM_KHACH = ['customer_name', 'mobile_no', 'primary_address']


def _hien_ten_khi_chon():
    for dt, (truong, hien) in HIEN_TEN.items():
        meta = frappe.get_meta(dt)
        if not meta.has_field(truong):
            continue
        muon = (('title_field', truong, 'Data'), ('show_title_field_in_link', hien, 'Check')) if hien == '1' \
            else (('show_title_field_in_link', hien, 'Check'),)
        for prop, val, kieu in muon:
            hien_tai = str(meta.get(prop) or ('0' if prop == 'show_title_field_in_link' else ''))
            if hien_tai != val:
                frappe.make_property_setter({'doctype': dt, 'doctype_or_field': 'DocType', 'property': prop,
                                             'value': val, 'property_type': kieu}, validate_fields_for_doctype=False)
    meta = frappe.get_meta('Customer')
    co = [x.strip() for x in (meta.get('search_fields') or '').split(',') if x.strip()]
    them = [f for f in TIM_KHACH if f not in co and meta.has_field(f)]
    if them:
        frappe.make_property_setter({'doctype': 'Customer', 'doctype_or_field': 'DocType', 'property': 'search_fields',
                                     'value': ','.join(co + them), 'property_type': 'Data'}, validate_fields_for_doctype=False)


# Tên cũ 0.16.0 ("Việc …" tạo cảm giác áp lực, chủ dự án đổi 20/10/2026). Chỉ ẩn Workspace cũ do bộ cài này tạo; xóa Module
# Profile cũ chỉ khi chưa ai dùng. Người đã đặt mặc định Workspace cũ được chuyển sang tên mới.
TEN_CU = {
    'ban_hang': ('Việc bán hàng', 'Bàn bán hàng', 'Trung tâm Bán hàng'),
    'kho': ('Việc kho', 'Bàn kho', 'Trung tâm Kho'),
    'tien': ('Việc tiền và công nợ', 'Bàn tiền và công nợ', 'Tiền và vay'),
    'nha_may': ('Việc nhà máy', 'Bàn nhà máy'),
    'du_lieu': ('Trung tâm dữ liệu',),
}


def _an_ten_cu():
    for nhom, cac_ten in TEN_CU.items():
        for cu in cac_ten:
            if not frappe.db.exists('Workspace', cu) or frappe.db.get_value('Workspace', cu, 'module') != MODULE:
                continue  # Không đụng Workspace ngoài module của app.
            frappe.db.set_value('Workspace', cu, 'is_hidden', 1, update_modified=False)
            for u in frappe.get_all('User', filters={'default_workspace': cu}, pluck='name'):
                frappe.db.set_value('User', u, 'default_workspace', NHOM[nhom], update_modified=False)
            mp = '9xLab - ' + cu
            moi = '9xLab - ' + NHOM[nhom]
            if frappe.db.exists('Module Profile', mp) and frappe.db.exists('Module Profile', moi):
                for user in frappe.get_all('User', filters={'module_profile': mp}, pluck='name'):
                    doc = frappe.get_doc('User', user)
                    doc.set('module_profile', moi)
                    doc.save(ignore_permissions=True)  # Bộ cài quản trị, chỉ map profile app của Workspace cũ.
            if frappe.db.exists('Module Profile', mp) and not frappe.db.exists('User', {'module_profile': mp}):
                frappe.delete_doc('Module Profile', mp, ignore_permissions=True, force=True)


def _ke_hoach(bang):
    """Tính thay đổi cho từng người: Workspace mặc định; kho/nhà máy thêm User Permission kho được giao.
    Bán hàng/tiền KHÔNG khóa Company/kho (đơn chung nhiều đơn vị)."""
    ke = []
    for dong in bang:
        user, nhom = dong.get('user'), dong.get('nhom')
        if nhom not in NHOM or not frappe.db.exists('User', user):
            frappe.throw(f'Dòng không hợp lệ: {user} / {nhom}')
        cu = frappe.db.get_value('User', user, 'default_workspace')
        if cu != NHOM[nhom]:
            ke.append({'user': user, 'viec': 'default_workspace', 'tu': cu, 'den': NHOM[nhom]})
        if dong.get('module_profile'):
            mp = '9xLab - ' + NHOM[nhom]
            cu_mp = frappe.db.get_value('User', user, 'module_profile')
            if cu_mp != mp:
                ke.append({'user': user, 'viec': 'module_profile', 'tu': cu_mp, 'den': mp})
        for kho in dong.get('kho') or []:
            if nhom not in ('kho', 'nha_may'):
                frappe.throw(f'{user}: chỉ nhóm kho/nhà máy mới giới hạn kho; bán hàng giữ chọn nhiều nguồn')
            if not frappe.db.exists('Warehouse', kho):
                frappe.throw(f'{user}: không có kho {kho}')
            if not frappe.db.exists('User Permission', {'user': user, 'allow': 'Warehouse', 'for_value': kho}):
                ke.append({'user': user, 'viec': 'User Permission Warehouse', 'tu': None, 'den': kho})
    return ke


@frappe.whitelist(methods=['POST'])
def ap_dung_nguoi_dung(bang, chay_that=0):
    """Áp cấu hình theo bảng [{user, nhom, kho?}]. Mặc định chạy thử: trả danh sách thay đổi, không ghi."""
    if not enabled():
        frappe.throw('Chưa bật giao diện theo công việc')
    if 'System Manager' not in frappe.get_roles() and frappe.session.user != 'Administrator':
        frappe.throw('Chỉ quản trị hệ thống áp cấu hình người dùng', frappe.PermissionError)
    bang = frappe.parse_json(bang)
    if not isinstance(bang, list) or not bang:
        frappe.throw('Cần bảng ánh xạ người dùng')
    ke = _ke_hoach(bang)
    if not cint(chay_that):
        return {'chay_thu': True, 'thay_doi': ke}
    for k in ke:
        if k['viec'] in ('default_workspace', 'module_profile'):
            u = frappe.get_doc('User', k['user'])
            u.set(k['viec'], k['den'])
            u.save(ignore_permissions=True)
        else:
            frappe.get_doc({'doctype': 'User Permission', 'user': k['user'], 'allow': 'Warehouse',
                            'for_value': k['den'], 'apply_to_all_doctypes': 1}).insert()
    return {'chay_thu': False, 'thay_doi': ke}


# ---------------------------------------------------------------- UX-3: tìm khách, công nợ một khách (chỉ đọc)

def _guard_doc():
    if not enabled():
        frappe.throw('Chưa bật giao diện theo công việc')
    if frappe.session.user == 'Guest':
        frappe.throw('Cần đăng nhập', frappe.PermissionError)


@frappe.whitelist(methods=['POST'])
def tim_khach(q):
    """Tìm khách theo mã, tên, tên gọi tắt, MST, số điện thoại (khách hoặc liên hệ). Chỉ trong phạm vi quyền đọc;
    trả danh sách để người dùng tự chọn, không tự chọn kết quả đầu tiên."""
    _guard_doc()
    q = str(q or '').strip()
    if len(q) < 2 or len(q) > 60:
        frappe.throw('Gõ từ 2 đến 60 ký tự')
    like = f'%{q}%'
    found = {}
    def add(rows, reason):
        for r in rows:
            found.setdefault(r.name, {'name': r.name, 'customer_name': r.customer_name, 'tax_id': r.get('tax_id') or '',
                                       'mobile_no': r.get('mobile_no') or '', 'primary_address': r.get('primary_address') or '', 'khop': reason})
    fields = ['name', 'customer_name', 'tax_id', 'mobile_no', 'primary_address']
    for field, reason in (('name', 'mã'), ('customer_name', 'tên'), ('tax_id', 'MST'), ('mobile_no', 'điện thoại')):
        add(frappe.get_list('Customer', filters={field: ['like', like], 'disabled': 0}, fields=fields, limit_page_length=20), reason)
    digits = ''.join(ch for ch in q if ch.isdigit())
    if len(digits) >= 6:
        contacts = frappe.get_list('Contact', filters=[['Contact Phone', 'phone', 'like', f'%{digits}%']], pluck='name',
                                   limit_page_length=20)
        if contacts:
            links = frappe.get_all('Dynamic Link', filters={'parenttype': 'Contact', 'parent': ['in', contacts],
                                   'link_doctype': 'Customer'}, pluck='link_name')
            if links:
                add(frappe.get_list('Customer', filters={'name': ['in', links], 'disabled': 0}, fields=fields,
                                    limit_page_length=20), 'điện thoại liên hệ')
    return sorted(found.values(), key=lambda r: (r['customer_name'] or '', r['name']))[:30]


@frappe.whitelist(methods=['POST'])
def cong_no_khach(customer):
    """Công nợ một khách theo từng đơn vị người dùng được xem: hóa đơn còn nợ, quá hạn, tiền đã nhận chưa phân bổ.
    Mỗi số tách theo đơn vị, không cộng/trừ chéo đơn vị."""
    _guard_doc()
    from frappe.utils import getdate, today, flt
    frappe.get_doc('Customer', customer).check_permission('read')
    companies = frappe.get_list('Company', pluck='name', limit_page_length=0)
    def safe(fn):
        try:
            return fn(), True
        except frappe.PermissionError:
            return [], False
    invoices, xem_hd = safe(lambda: frappe.get_list('Sales Invoice', filters={'customer': customer, 'docstatus': 1, 'outstanding_amount': ['>', 0],
                               'company': ['in', companies]}, fields=['name', 'company', 'posting_date', 'due_date', 'outstanding_amount'],
                               order_by='posting_date asc', limit_page_length=5001))
    payments, xem_tien = safe(lambda: frappe.get_list('Payment Entry', filters={'party_type': 'Customer', 'party': customer, 'docstatus': 1,
                               'unallocated_amount': ['>', 0], 'company': ['in', companies]},
                               fields=['name', 'company', 'posting_date', 'unallocated_amount'], limit_page_length=5001))
    if len(invoices) > 5000 or len(payments) > 5000:
        frappe.throw('Công nợ vượt phạm vi hiển thị; mở báo cáo chi tiết để đối chiếu đầy đủ')
    out = {}
    for c in companies:
        out[c] = {'company': c, 'phai_thu': 0.0, 'qua_han': 0.0, 'chua_phan_bo': 0.0, 'hoa_don': [], 'tien_chua_phan_bo': []}
    for r in invoices:
        d = out[r.company]
        d['phai_thu'] += flt(r.outstanding_amount)
        if r.due_date and getdate(r.due_date) < getdate(today()):
            d['qua_han'] += flt(r.outstanding_amount)
        d['hoa_don'].append({'name': r.name, 'posting_date': str(r.posting_date), 'due_date': str(r.due_date or ''),
                             'outstanding': flt(r.outstanding_amount)})
    for r in payments:
        d = out[r.company]
        d['chua_phan_bo'] += flt(r.unallocated_amount)
        d['tien_chua_phan_bo'].append({'name': r.name, 'posting_date': str(r.posting_date), 'amount': flt(r.unallocated_amount)})
    return {'customer': customer, 'xem_hoa_don': xem_hd, 'xem_tien': xem_tien, 'don_vi': [v for v in out.values() if v['hoa_don'] or v['tien_chua_phan_bo']]}


@frappe.whitelist()
def customer_query(doctype, txt, searchfield, start, page_len, filters=None):
    """Gợi ý khách cho đơn: mã/tên/SĐT/địa chỉ, truy vấn theo quyền đọc native."""
    _guard_doc()
    if doctype != 'Customer':
        frappe.throw('Chỉ tìm khách hàng')
    text = str(txt or '').strip()[:140]
    rows = frappe.get_list('Customer', filters={'disabled': 0},
        or_filters={f: ['like', '%' + text + '%'] for f in ('name', 'customer_name', 'mobile_no')},
        fields=['name', 'customer_name', 'mobile_no', 'primary_address'],
        order_by='customer_name asc, name asc', start=max(0, cint(start)),
        limit_page_length=min(30, max(1, cint(page_len))))
    from frappe.utils import strip_html
    return [[r.name, r.customer_name, r.mobile_no or 'Chưa có số điện thoại',
             strip_html(r.primary_address or '') or 'Chưa có địa chỉ'] for r in rows]


@frappe.whitelist(methods=['POST'])
def customer_identity(customer):
    """Danh tính hiện tại của khách, không ghi đè thông tin lịch sử trên đơn."""
    _guard_doc()
    from frappe.utils import strip_html
    values = frappe.get_list('Customer', filters={'name': customer},
        fields=['name', 'customer_name', 'mobile_no', 'primary_address'], limit_page_length=1)
    if not values:
        frappe.throw('Không có quyền xem khách hoặc khách không còn tồn tại', frappe.PermissionError)
    value = values[0]
    return {'name': value.name, 'customer_name': value.customer_name,
            'mobile_no': value.mobile_no or '', 'primary_address': strip_html(value.primary_address or '')}
