"""Nhận nhanh theo đơn mua; native Purchase Receipt vẫn sở hữu tồn kho và sổ."""
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation
import hashlib
import json

import frappe
from frappe.utils import cint, getdate, today, now_datetime

FLAG = 'kh_aph_factory_receiving'
PREFIX = 'kh_aph_receiving_'
STAMP = ('request', 'payload', 'actor', 'at', 'receiver', 'ticket', 'note', 'price_review')
_INTERNAL = ContextVar('factory_receiving', default=None)
ROLES = {'Kế toán nhà máy', 'Stock User', 'Stock Manager', 'Accounts Manager', 'System Manager'}


def enabled():
    return bool(cint(frappe.conf.get(FLAG)))


def guard():
    if not enabled() or not cint(frappe.conf.get('kh_aph_quantity_valuation_mvp')):
        frappe.throw('Chưa bật nhận hàng nhà máy')
    if not cint(frappe.conf.get('kh_aph_server_cost_guard')):
        frappe.throw('Cần bật bảo vệ giá vốn trước khi nhận hàng nhà máy')
    if (frappe.session.user == 'Guest' or (frappe.session.user != 'Administrator'
            and not (set(frappe.get_roles()) & ROLES))):
        frappe.throw('Không đủ quyền nhận hàng nhà máy', frappe.PermissionError)
    if not frappe.db.get_value('User', frappe.session.user, 'enabled'):
        frappe.throw('Tài khoản chưa hoạt động', frappe.PermissionError)


def _number(value):
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0 or n != n.quantize(Decimal('0.000001')):
            raise ValueError()
        return n
    except (InvalidOperation, ValueError, TypeError):
        frappe.throw('Số lượng phải hữu hạn, không âm và tối đa 6 số lẻ')


def _source(name, state=True):
    doc = frappe.get_doc('Purchase Order', name)
    doc.check_permission('read')
    frappe.get_doc('Company', doc.company).check_permission('read')
    frappe.get_doc('Supplier', doc.supplier).check_permission('read')
    if state and (doc.docstatus != 1 or doc.status in ('Closed', 'Cancelled', 'On Hold') or doc.get('is_subcontracted') or doc.get('has_unit_price_items')):
        frappe.throw('Chọn đơn mua đã xác nhận, còn nhận hàng; đơn gia công/giá đơn vị dùng màn hình chuẩn')
    return doc


def _warehouse(name, company):
    doc = frappe.get_doc('Warehouse', name)
    doc.check_permission('read')
    if doc.company != company or doc.disabled or doc.is_group:
        frappe.throw('Chọn kho lá đang dùng đúng đơn vị sở hữu')


def _item(row):
    item = frappe.get_doc('Item', row.item_code)
    item.check_permission('read')
    if item.disabled or not item.is_stock_item or item.stock_uom != 'Kg' or row.uom != 'Kg' or _number(row.conversion_factor) != 1:
        frappe.throw('Cửa sổ nhận nhanh chỉ nhận hàng tồn Kg, hệ số 1')
    if item.has_serial_no or item.has_batch_no or row.get('delivered_by_supplier'):
        frappe.throw('Hàng theo lô/sê-ri hoặc giao thẳng dùng phiếu nhập chuẩn để đủ hồ sơ')
    if _number(row.rate) <= 0:
        frappe.throw('Đơn mua chưa có giá hợp lệ: dùng phiếu chờ định giá, không nhập giá 0')
    return item


@frappe.whitelist(methods=['POST'])
def orders(company):
    guard()
    frappe.get_doc('Company', company).check_permission('read')
    rows = frappe.get_list('Purchase Order', filters={'company': company, 'docstatus': 1,
        'status': ['not in', ['Closed', 'Cancelled', 'On Hold', 'Completed']], 'per_received': ['<', 100]},
        fields=['name', 'supplier'], order_by='modified desc', limit_page_length=201)
    if len(rows) > 200:
        frappe.throw('Có hơn 200 đơn chờ nhận; mở đúng đơn mua để nhận hoặc thu hẹp danh sách')
    return rows


@frappe.whitelist(methods=['POST'])
def preview(purchase_order):
    guard()
    doc = _source(purchase_order)
    rows = []
    for row in doc.items:
        remaining = _number(row.qty) - _number(row.received_qty or 0)
        if remaining <= 0:
            continue
        item = _item(row)
        if row.warehouse:
            _warehouse(row.warehouse, doc.company)
        rows.append({'source_row': row.name, 'item_code': row.item_code, 'warehouse': row.warehouse,
                     'remaining': float(remaining), 'qty': 0, 'bags': 0, 'quality_qty': 0,
                     'kg_per_bag': float(_number(item.get('kh_aph_kg_per_bag') or 0))})
    if not rows:
        frappe.throw('Đơn mua không còn lượng được nhận')
    return {'purchase_order': doc.name, 'company': doc.company, 'supplier': doc.supplier,
            'price_mode': 'Giá tạm theo đơn mua' if cint(doc.get('kh_aph_gia_tam')) else 'Giá theo đơn mua', 'items': rows}


def _selection(raw):
    values = frappe.parse_json(raw)
    if not isinstance(values, list) or not values or len(values) > 100:
        frappe.throw('Chọn từ 1 đến 100 dòng thực nhận')
    selected = {}
    for row in values:
        if not isinstance(row, dict) or set(row) != {'source_row', 'warehouse', 'qty', 'bags', 'quality_qty'}:
            frappe.throw('Dữ liệu nhận hàng không hợp lệ')
        key = str(row['source_row'] or '')
        if not key or key in selected:
            frappe.throw('Dòng đơn mua bị thiếu hoặc trùng')
        qty, bags, quality = _number(row['qty']), _number(row['bags']), _number(row['quality_qty'])
        if qty <= 0 or quality > qty or bags != bags.to_integral_value():
            frappe.throw('Kg nhận phải dương, lượng có vấn đề không vượt thực nhận, số bao phải nguyên')
        selected[key] = {'warehouse': str(row['warehouse'] or '').strip(), 'qty': str(qty.normalize()), 'bags': str(bags.normalize()), 'quality_qty': str(quality.normalize())}
    return selected


def _result(doc):
    doc.check_permission('read')
    return {'name': doc.name, 'doctype': 'Purchase Receipt', 'docstatus': doc.docstatus}


def _claim_ticket(url):
    if not url:
        return None
    if not url.startswith('/private/files/'):
        frappe.throw('Phiếu cân phải là tệp riêng tư được tải lên hệ thống')
    names = frappe.get_list('File', filters={'file_url': url, 'is_private': 1}, pluck='name', limit_page_length=2)
    if len(names) != 1:
        frappe.throw('Chọn một tệp phiếu cân riêng tư có quyền truy cập')
    frappe.db.sql('SELECT name FROM `tabFile` WHERE name=%s FOR UPDATE', names[0])
    file = frappe.get_doc('File', names[0])
    file.check_permission('read'); file.check_permission('write')
    if file.owner != frappe.session.user or file.attached_to_name:
        frappe.throw('Tải phiếu cân mới của bạn cho lần nhận này; không lấy tệp của hồ sơ khác')
    return file


@frappe.whitelist(methods=['POST'])
def receive(purchase_order, request_id, rows, received_date, receiver, ticket=None, note=None):
    guard()
    doc = _source(purchase_order, state=False)
    selected = _selection(rows)
    receiver, ticket, note = str(receiver or '').strip(), str(ticket or '').strip(), str(note or '').strip()
    if not receiver or len(receiver) > 140 or len(note) > 2000 or len(ticket) > 140:
        frappe.throw('Cần người thực nhận và nội dung trong giới hạn cho phép')
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 100:
        frappe.throw('Thiếu mã lượt nhận; mở lại cửa sổ nhận hàng')
    if not received_date or getdate(received_date) > getdate(today()):
        frappe.throw('Ngày nhận không được ở tương lai')
    price_review = any(_number(v['quality_qty']) > 0 for v in selected.values())
    if price_review and not note:
        frappe.throw('Ghi rõ vấn đề chất lượng và nội dung cần đàm phán giảm giá')
    body = json.dumps([purchase_order, selected, str(getdate(received_date)), receiver, ticket, note], sort_keys=True, ensure_ascii=False)
    payload = hashlib.sha256(body.encode()).hexdigest()
    key = hashlib.sha256(json.dumps([frappe.session.user, purchase_order, request_id]).encode()).hexdigest()
    # Cùng company tuần tự qua mọi lượt; PO được khóa trước đọc lại lượng còn nhận.
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', doc.company)
    frappe.db.sql('SELECT name FROM `tabPurchase Order` WHERE name=%s FOR UPDATE', purchase_order)
    doc = _source(purchase_order, state=False)
    old = frappe.db.get_value('Purchase Receipt', {PREFIX+'request': key}, 'name')
    if old:
        receipt = frappe.get_doc('Purchase Receipt', old)
        receipt.check_permission('read')
        if receipt.get(PREFIX+'payload') != payload or receipt.docstatus != 1:
            frappe.throw('Lượt nhận đã có nội dung khác hoặc phiếu đã thay đổi; kiểm tra phiếu cũ')
        return _result(receipt)
    doc = _source(purchase_order)
    for name, values in selected.items():
        row = next((r for r in doc.items if r.name == name), None)
        if not row:
            frappe.throw('Dòng không thuộc đơn mua đã chọn')
        item = _item(row)
        qty, bags = _number(values['qty']), _number(values['bags'])
        if qty > _number(row.qty) - _number(row.received_qty or 0):
            frappe.throw('Lượng thực nhận vượt lượng còn được nhận')
        _warehouse(values['warehouse'], doc.company)
        weight = _number(item.get('kh_aph_kg_per_bag') or 0)
        if (weight and (not bags or qty != bags * weight)) or (not weight and bags):
            frappe.throw('Kg/số bao không khớp quy cách; không tự sửa kg/bao để cân bằng')
    file = _claim_ticket(ticket)
    from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
    receipt = make_purchase_receipt(purchase_order, args={'filtered_children': list(selected)})
    if {r.purchase_order_item for r in receipt.items} != set(selected):
        frappe.throw('Lượng đơn mua đã đổi; mở lại cửa sổ nhận')
    for row in receipt.items:
        values = selected[row.purchase_order_item]
        row.qty = row.received_qty = float(_number(values['qty']))
        row.rejected_qty = 0
        row.warehouse = values['warehouse']
        row.kh_aph_bags = float(_number(values['bags']))
        row.kh_aph_receiving_quality_qty = float(_number(values['quality_qty']))
    receipt.posting_date = str(getdate(received_date))
    receipt.set_posting_time = 1
    receipt.kh_aph_gia_tam = cint(doc.get('kh_aph_gia_tam'))
    for field, value in {'request': key, 'payload': payload, 'actor': frappe.session.user, 'at': now_datetime(),
                         'receiver': receiver, 'ticket': ticket, 'note': note, 'price_review': int(price_review)}.items():
        receipt.set(PREFIX+field, value)
    token = _INTERNAL.set((frappe.session.user, key, payload))
    try:
        receipt.insert()
        receipt.submit()
    finally:
        _INTERNAL.reset(token)
    if file:
        file.attached_to_doctype = 'Purchase Receipt'; file.attached_to_name = receipt.name
        file.attached_to_field = PREFIX+'ticket'; file.save()
    return _result(receipt)


def protect(doc, method=None):
    values = [doc.get(PREFIX+f) for f in STAMP]
    quality = any(r.get('kh_aph_receiving_quality_qty') for r in (doc.get('items') or []))
    if not enabled() and not any(values) and not quality:
        return
    if doc.is_new():
        if not values[0]:
            doc.set(PREFIX+'request', None)
        if (any(values) or quality) and _INTERNAL.get() != (frappe.session.user, values[0], values[1]):
            frappe.throw('Dấu nhận hàng chỉ được tạo qua cửa sổ nhận hàng')
    else:
        old = doc.get_doc_before_save()
        if old and any((old.get(PREFIX+f) or '') != (doc.get(PREFIX+f) or '') for f in STAMP):
            frappe.throw('Không sửa dấu và hồ sơ thực nhận; giữ lịch sử trên phiếu gốc')
        if old:
            previous = {r.name: r.get('kh_aph_receiving_quality_qty') or 0 for r in (old.get('items') or [])}
            if any((r.get('kh_aph_receiving_quality_qty') or 0) != previous.get(r.name, 0) for r in (doc.get('items') or [])):
                frappe.throw('Không sửa lượng hàng có vấn đề đã ghi nhận')


def prevent_delete(doc, method=None):
    if doc.get(PREFIX+'request'):
        frappe.throw('Giữ phiếu nhận đã có mã lượt để đối soát, kể cả sau hủy')


def schema():
    if not enabled():
        return
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    labels = {'request': 'Mã lượt nhận hàng', 'payload': 'Dấu nội dung nhận', 'actor': 'Người nhập nhận hàng',
              'at': 'Thời điểm ghi nhận', 'receiver': 'Người thực nhận hàng', 'ticket': 'Phiếu cân', 'note': 'Ghi chú thực nhận / đàm phán giảm giá', 'price_review': 'Có hàng đàm phán giảm giá lúc nhận'}
    fields = []
    for key in STAMP:
        fields.append({'fieldname': PREFIX+key, 'label': labels[key], 'fieldtype': 'Check' if key == 'price_review' else 'Datetime' if key == 'at' else 'Small Text' if key == 'note' else 'Data',
                       'read_only': 1, 'no_copy': 1, 'hidden': int(key in ('request', 'payload')),
                       **({'unique': 1} if key == 'request' else {})})
    create_custom_fields({'Purchase Receipt': fields, 'Purchase Receipt Item': [
        {'fieldname': 'kh_aph_receiving_quality_qty', 'label': 'Kg có vấn đề, vẫn nhận dùng',
         'fieldtype': 'Float', 'read_only': 1, 'no_copy': 1, 'insert_after': 'qty'}]})
