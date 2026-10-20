"""NM02–NM04 — ghi sản xuất / đóng gói / đổi bao một lần theo lượng, trên các loại phiếu kho đã có.

Không tạo sổ sản xuất riêng: mỗi lần ghi là MỘT Stock Entry native thuộc loại đã kiểm (`stock_entry_kg`, `factory_costing`):
- Sản xuất (CĐ1): đầu vào lấy từ kho Dở dang dây chuyền theo lượng THỰC DÙNG (phần còn lại vẫn nằm ở dở dang, không vét);
  một thành phẩm → "Sản xuất theo kg" (Manufacture), nhiều đầu ra/phụ phẩm → "Đóng gói theo kg" (Repack, kg-v4).
  Đầu vào > đầu ra là hao hụt tự nhiên theo quy tắc sẵn có, phải ghi lý do; không tự quy mọi chênh lệch.
- Đóng gói thành phẩm (CĐ2) và Đổi bao/đóng gói lại: bảo toàn kg; lệch phải xác nhận kèm lý do (quy tắc sẵn có Q103).
API chỉ trả mã/kho/lượng; giá thành do lớp kg-v4 tính, người không xem giá vốn không thấy. Cờ `kh_aph_factory_production`.
"""
from contextvars import ContextVar
import hashlib
import json

import frappe
from frappe.utils import cint, getdate, today, now_datetime
from kh_aph.cash_transaction import retry_rpc

FLAG = 'kh_aph_factory_production'
PREFIX = 'kh_aph_production_'
STAMP = ('request', 'payload', 'actor', 'at', 'note')
ROLES = {'Kế toán nhà máy', 'Stock User', 'Stock Manager', 'Accounts Manager', 'System Manager'}
_INTERNAL = ContextVar('factory_production', default=None)
F_LOAI, F_DAY, F_XUONG = 'kh_aph_loai_kho', 'kh_aph_day_chuyen', 'kh_aph_xuong'
DO_DANG, CHO_DONG_GOI, THANH_PHAM, CHO_XU_LY = 'Dở dang dây chuyền', 'Chờ đóng gói', 'Thành phẩm', 'Chờ xử lý'
SAN_XUAT, DONG_GOI_KG = 'Sản xuất theo kg', 'Đóng gói theo kg'
DONG_GOI_TP, DOI_BAO = 'Đóng gói thành phẩm', 'Đổi bao, đóng gói lại'
KINDS = {
    # loại: (kho nguồn được phép theo loại kho, kho đích được phép theo loại kho)
    'san_xuat': ((DO_DANG,), (CHO_DONG_GOI, THANH_PHAM, CHO_XU_LY)),
    'dong_goi': (None, (THANH_PHAM,)),
    'doi_bao': (None, (THANH_PHAM, CHO_DONG_GOI)),
}


def enabled():
    return bool(cint(frappe.conf.get(FLAG)))


def guard():
    if not enabled() or not cint(frappe.conf.get('kh_aph_factory_costing')):
        frappe.throw('Chưa bật ghi sản xuất nhà máy')
    if not cint(frappe.conf.get('kh_aph_server_cost_guard')):
        frappe.throw('Cần bật bảo vệ giá vốn trước khi ghi sản xuất')
    if (frappe.session.user == 'Guest' or (frappe.session.user != 'Administrator'
            and not (set(frappe.get_roles()) & ROLES))):
        frappe.throw('Không đủ quyền ghi sản xuất nhà máy', frappe.PermissionError)


def _number(value):
    from kh_aph.factory_receiving import _number as n
    return n(value)


def _warehouse(name, company, allowed):
    doc = frappe.get_doc('Warehouse', name)
    doc.check_permission('read')
    if doc.company != company or doc.disabled or doc.is_group or doc.get('warehouse_type') == 'Transit':
        frappe.throw(f'{name}: chọn kho lá đang dùng của {company}')
    if allowed and doc.get(F_LOAI) not in allowed:
        frappe.throw(f'{name}: loại kho phải là {" / ".join(allowed)}')
    return doc


def _item(code):
    item = frappe.get_doc('Item', code)
    item.check_permission('read')
    if item.disabled or not item.is_stock_item or item.has_serial_no or item.has_batch_no:
        frappe.throw(f'{code}: chỉ ghi hàng tồn kho đang dùng, không lô/sê-ri')
    return item


@frappe.whitelist(methods=['POST'])
def context(company):
    guard()
    frappe.get_doc('Company', company).check_permission('read')
    meta_ok = frappe.get_meta('Warehouse').has_field(F_LOAI)
    whs = frappe.get_list('Warehouse', filters={'company': company, 'is_group': 0, 'disabled': 0},
                          fields=['name'] + ([F_LOAI, F_DAY] if meta_ok else []), limit_page_length=0)
    workshops = frappe.get_list('Cost Center', filters={'company': company, 'is_group': 0,
                                'kh_aph_loai_ttcp': 'Xưởng sản xuất'}, pluck='name', limit_page_length=0)
    return {'company': company, 'workshops': workshops,
            'lines': [{'warehouse': w.name, 'line': w.get(F_DAY) or ''} for w in whs if w.get(F_LOAI) == DO_DANG],
            'warehouses': [{'warehouse': w.name, 'type': w.get(F_LOAI) or ''} for w in whs]}


@frappe.whitelist(methods=['POST'])
def wip(warehouse):
    """Lượng đang nằm ở kho dở dang (chỉ mã + kg), để người nhập thấy phần còn dở trước/sau khi ghi."""
    guard()
    doc = frappe.get_doc('Warehouse', warehouse)
    doc.check_permission('read')
    if doc.get(F_LOAI) != DO_DANG:
        frappe.throw('Chọn kho dở dang dây chuyền')
    rows = frappe.db.sql('SELECT item_code, actual_qty FROM `tabBin` WHERE warehouse=%s AND actual_qty!=0 ORDER BY item_code',
                         warehouse)
    return [{'item_code': code, 'qty': float(qty)} for code, qty in rows]


def _rows(raw, keys, limit=50):
    values = frappe.parse_json(raw)
    if not isinstance(values, list) or not values or len(values) > limit:
        frappe.throw(f'Cần từ 1 đến {limit} dòng')
    out = []
    for row in values:
        if not isinstance(row, dict) or set(row) != set(keys):
            frappe.throw('Dữ liệu dòng không hợp lệ')
        qty = _number(row['qty'])
        if qty <= 0:
            frappe.throw('Lượng mỗi dòng phải lớn hơn 0')
        clean = {k: str(row[k] or '').strip() for k in keys if k != 'qty'}
        clean['qty'] = str(qty.normalize())
        out.append(clean)
    return out


@frappe.whitelist(methods=['POST'])
@retry_rpc
def record(kind, company, request_id, posting_date, inputs, outputs, workshop=None, note=None, confirm_difference=0):
    guard()
    if kind not in KINDS:
        frappe.throw('Chọn sản xuất, đóng gói thành phẩm hoặc đổi bao')
    frappe.get_doc('Company', company).check_permission('read')
    ins = _rows(inputs, ('item_code', 'warehouse', 'qty'))
    outs = _rows(outputs, ('item_code', 'warehouse', 'qty'))
    note = str(note or '').strip()
    if len(note) > 2000 or not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 100:
        frappe.throw('Thiếu mã lượt ghi hoặc ghi chú quá dài; mở lại cửa sổ')
    if not posting_date or getdate(posting_date) > getdate(today()):
        frappe.throw('Ngày ghi không được ở tương lai')
    src_types, dst_types = KINDS[kind]
    kg_in = sum(_number(r['qty']) for r in ins)
    kg_out = sum(_number(r['qty']) for r in outs)
    difference = kg_in - kg_out
    if kind == 'san_xuat':
        if not workshop:
            frappe.throw('Chọn xưởng sản xuất')
        if difference > 0 and not note:
            frappe.throw('Đầu vào nhiều hơn đầu ra: ghi lý do hao hụt tự nhiên; hao hụt bất thường xuất chi phí riêng')
        if len({r['warehouse'] for r in ins}) != 1:
            frappe.throw('Một lần ghi sản xuất lấy đầu vào từ một kho dở dang (một dây chuyền)')
    elif cint(confirm_difference) and not note:
        frappe.throw('Xác nhận lệch kg cần ghi lý do')
    body = json.dumps([kind, company, str(getdate(posting_date)), ins, outs, workshop or '', note, cint(confirm_difference)],
                      sort_keys=True, ensure_ascii=False)
    payload = hashlib.sha256(body.encode()).hexdigest()
    key = hashlib.sha256(json.dumps(['production', frappe.session.user, company, request_id]).encode()).hexdigest()
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', company)
    old = frappe.db.sql('SELECT name FROM `tabStock Entry` WHERE kh_aph_production_request=%s FOR UPDATE', key)
    if old:
        entry = frappe.get_doc('Stock Entry', old[0][0], for_update=True)
        entry.check_permission('read')
        if entry.get(PREFIX + 'payload') != payload or entry.docstatus != 1:
            frappe.throw('Lượt ghi đã có nội dung khác hoặc phiếu đã thay đổi; kiểm tra phiếu cũ')
        return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus, 'type': entry.stock_entry_type}
    for r in ins + outs:
        item = _item(r['item_code'])
        if kind == 'san_xuat' and item.stock_uom != 'Kg':
            frappe.throw(f"{r['item_code']}: ghi sản xuất chỉ nhận hàng tồn Kg")
    for r in ins:
        _warehouse(r['warehouse'], company, src_types)
    for r in outs:
        _warehouse(r['warehouse'], company, dst_types)
    # Khóa tồn nguồn theo thứ tự cố định, đọc hiện tại; không cho ghi dùng vượt lượng đang có.
    need = {}
    for r in ins:
        k = (r['item_code'], r['warehouse'])
        need[k] = need.get(k, _number(0)) + _number(r['qty'])
    for (code, wh), qty in sorted(need.items()):
        got = frappe.db.sql('SELECT actual_qty FROM `tabBin` WHERE item_code=%s AND warehouse=%s FOR UPDATE', (code, wh))
        have = _number(round(float(got[0][0]), 6)) if got else _number(0)
        if qty > have:
            frappe.throw(f'{code} tại {wh} chỉ còn {have} kg; ghi đúng lượng thực dùng')
    if kind == 'san_xuat':
        entry_type = SAN_XUAT if len(outs) == 1 else DONG_GOI_KG
    else:
        entry_type = DONG_GOI_TP if kind == 'dong_goi' else DOI_BAO
    items = [{'item_code': r['item_code'], 'qty': float(_number(r['qty'])), 's_warehouse': r['warehouse']} for r in ins]
    for i, r in enumerate(outs):
        row = {'item_code': r['item_code'], 'qty': float(_number(r['qty'])), 't_warehouse': r['warehouse']}
        if entry_type == SAN_XUAT:
            row['is_finished_item'] = 1
        items.append(row)
    for row in items:
        item = frappe.get_cached_doc('Item', row['item_code'])
        row.update({'uom': item.stock_uom, 'conversion_factor': 1})
    entry = frappe.get_doc({'doctype': 'Stock Entry', 'stock_entry_type': entry_type, 'company': company,
                            'posting_date': str(getdate(posting_date)), 'set_posting_time': 1, 'items': items})
    if kind == 'san_xuat':
        entry.set(F_XUONG, workshop)
        if difference > 0:
            entry.kh_aph_loss_type = 'Hao hụt tự nhiên'
            entry.kh_aph_loss_reason = note
    elif cint(confirm_difference):
        # Lệch kg (không tính bao bì) do lớp đóng gói sẵn có tự tính và chặn nếu chưa xác nhận.
        entry.kh_aph_xac_nhan_lech_kg = 1
        entry.kh_aph_ly_do_lech_kg = note
    for field, value in {'request': key, 'payload': payload, 'actor': frappe.session.user, 'at': now_datetime(),
                         'note': note}.items():
        entry.set(PREFIX + field, value)
    token = _INTERNAL.set((frappe.session.user, key, payload))
    try:
        entry.insert()
        entry.submit()
    finally:
        _INTERNAL.reset(token)
    entry.check_permission('read')
    return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus, 'type': entry_type}


def _stamp(doc, field):
    return str(doc.get(PREFIX + field) or '')


def protect(doc, method=None):
    values = [doc.get(PREFIX + f) for f in STAMP]
    if not any(values):
        return
    if doc.is_new():
        if _INTERNAL.get() != (frappe.session.user, values[0], values[1]):
            frappe.throw('Dấu ghi sản xuất chỉ được tạo qua cửa sổ ghi sản xuất')
        return
    old = doc.get_doc_before_save()
    if old and any(_stamp(old, f) != _stamp(doc, f) for f in STAMP):
        frappe.throw('Không sửa dấu ghi sản xuất; giữ lịch sử trên phiếu gốc')


def prevent_delete(doc, method=None):
    if doc.get(PREFIX + 'request'):
        frappe.throw('Giữ phiếu ghi sản xuất đã có mã lượt để đối soát, kể cả sau hủy')


def schema():
    if not enabled():
        return
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    labels = {'request': 'Mã lượt ghi sản xuất', 'payload': 'Dấu nội dung ghi sản xuất', 'actor': 'Người ghi sản xuất',
              'at': 'Thời điểm ghi sản xuất', 'note': 'Ghi chú ghi sản xuất'}
    create_custom_fields({'Stock Entry': [
        {'fieldname': PREFIX + k, 'label': labels[k],
         'fieldtype': 'Datetime' if k == 'at' else 'Small Text' if k == 'note' else 'Data',
         'read_only': 1, 'no_copy': 1, 'hidden': int(k in ('request', 'payload')),
         **({'unique': 1} if k == 'request' else {})} for k in STAMP]})
