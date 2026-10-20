"""UX-01 — giao diện theo công việc (docs/dac-ta-ux-01.md). Cờ `kh_aph_ux_task_first`, mặc định tắt.

PR-A: bốn Workspace mới SONG SONG ("Việc bán hàng", "Việc kho", "Việc tiền và công nợ", "Việc nhà máy"), không sửa
Workspace cũ; quay lui = đổi Workspace mặc định về cũ / tắt cờ. Ba khối: Việc cần làm (có số đếm theo quyền native của
danh sách), Thao tác nhanh, Tra cứu. Áp cấu hình người dùng bằng bảng ánh xạ, mặc định CHẠY THỬ (chỉ in thay đổi).
PR-B: nút "Việc tiếp theo" trên chứng từ (public/js/ux_buoc_tiep.js) chỉ bấm hộ các nút nghiệp vụ đã có; không hàm ghi mới.
"""
import json

import frappe
from frappe.utils import cint

FLAG = 'kh_aph_ux_task_first'
MODULE = 'Kh Aph'

NHOM = {
    'ban_hang': 'Việc bán hàng',
    'kho': 'Việc kho',
    'tien': 'Việc tiền và công nợ',
    'nha_may': 'Việc nhà máy',
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
        ('Yêu cầu chuyển kho chờ xử lý', 'DocType', 'Material Request', {'docstatus': 1, 'status': ['not in', ['Transferred', 'Stopped']]}, 'List'),
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
                 ('Ghi nhận thu tiền', 'DocType', 'Payment Entry', None, 'New'),
                 ('Xem công nợ khách', 'Report', 'Tong hop ban hang theo khach', None, '')],
    'kho': [('Tồn kho và nhận/chuyển hàng', 'Report', 'Ton kho so luong', None, ''),
            ('Kiểm kê', 'DocType', 'Stock Reconciliation', None, 'New')],
    'tien': [('Ghi nhận thu tiền', 'DocType', 'Payment Entry', None, 'New'),
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
    'ban_hang': ('Kế toán bán hàng', 'Sales User', 'Sales Manager', 'Accounts Manager', 'System Manager'),
    'kho': ('Thủ kho bán hàng', 'Stock User', 'Stock Manager', 'Accounts Manager', 'System Manager'),
    'tien': ('Accounts User', 'Accounts Manager', 'Kế toán bán hàng', 'System Manager'),
    'nha_may': ('Kế toán nhà máy', 'Stock Manager', 'Accounts Manager', 'System Manager'),
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


def _workspace(nhom):
    ten = NHOM[nhom]
    khoi = [('Việc cần làm hôm nay', _LAM[nhom], 6), ('Thao tác nhanh', _NHANH[nhom], 4), ('Tra cứu', _TRA[nhom], 3)]
    content, shortcuts, dung = [], [], set()
    for i, (tieu_de, ds, col) in enumerate(khoi):
        ds = [x for x in ds if _hop_le(x)]
        content.append({'id': f'{nhom}-h{i}', 'type': 'header', 'data': {'text': f'<span class="h4"><b>{tieu_de}</b></span>', 'col': 12}})
        for j, x in enumerate(ds):
            nhan, loai, dich, loc, view = x
            khoa = nhan if nhan not in dung else f'{nhan} ({tieu_de.lower()})'
            dung.add(khoa)
            content.append({'id': f'{nhom}-{i}-{j}', 'type': 'shortcut', 'data': {'shortcut_name': khoa, 'col': col}})
            sc = {'label': khoa, 'type': loai, 'link_to': dich, 'color': 'Blue' if i == 1 else 'Grey', 'doc_view': view or ''}
            if loc:
                sc.update({'stats_filter': json.dumps(loc, ensure_ascii=False), 'format': '{} việc'})
            shortcuts.append(sc)
        content.append({'id': f'{nhom}-s{i}', 'type': 'spacer', 'data': {'col': 12}})
    ws = frappe.get_doc('Workspace', ten) if frappe.db.exists('Workspace', ten) else frappe.new_doc('Workspace')
    ws.update({'label': ten, 'title': ten, 'public': 1, 'module': MODULE, 'icon': {'ban_hang': 'sell', 'kho': 'stock', 'tien': 'money-coins-1', 'nha_may': 'stock'}[nhom],
               'content': json.dumps(content, ensure_ascii=False)})
    ws.set('shortcuts', shortcuts)
    ws.set('roles', [{'role': r} for r in VAI_TRO[nhom] if frappe.db.exists('Role', r)])
    ws.flags.ignore_permissions = True
    ws.save() if not ws.is_new() else ws.insert()
    return ten


def schema():
    """Dựng/làm mới bốn Workspace mới (idempotent). Không đụng Workspace cũ."""
    if not enabled():
        return
    return [_workspace(n) for n in NHOM]


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
        if k['viec'] == 'default_workspace':
            frappe.db.set_value('User', k['user'], 'default_workspace', k['den'])
        else:
            frappe.get_doc({'doctype': 'User Permission', 'user': k['user'], 'allow': 'Warehouse',
                            'for_value': k['den'], 'apply_to_all_doctypes': 1}).insert()
    return {'chay_thu': False, 'thay_doi': ke}
