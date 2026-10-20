"""NM01c — nhận chuyến chuyển kho đến nhà máy (cùng đơn vị) trên Stock Entry native.

Phiếu chuyển đi (Material Transfer, add_to_transit) do kho nguồn lập như hiện có; cửa sổ này chỉ lập phiếu nhận
(Stock Entry nhận từ hàng đang vận chuyển, `outgoing_stock_entry`) theo lượng thực nhận, nhận từng phần được.
Không dùng phiếu mua (PR) cho chuyến chuyển; chuyển khác đơn vị là mua bán nội bộ, không thuộc cửa sổ này.
Lượng thiếu nằm lại kho đang vận chuyển chờ đối soát, không tự ghi hao hụt; nhận vượt lượng chuyển bị chặn.
Tái dùng cờ `kh_aph_factory_receiving` (mặc định tắt).
"""
from contextvars import ContextVar
import hashlib
import json

import frappe
from frappe.utils import cint, getdate, today, now_datetime
from kh_aph.cash_transaction import retry_rpc
from kh_aph.factory_receiving import enabled, guard, _number

PREFIX = 'kh_aph_transfer_'
STAMP = ('request', 'payload', 'actor', 'at', 'receiver', 'note')
_INTERNAL = ContextVar('factory_transfer', default=None)


def _outgoing(name, lock=False):
    doc = frappe.get_doc('Stock Entry', name, for_update=lock)
    doc.check_permission('read')
    frappe.get_doc('Company', doc.company).check_permission('read')
    if (doc.docstatus != 1 or doc.purpose != 'Material Transfer' or not cint(doc.add_to_transit)
            or doc.get('outgoing_stock_entry')):
        frappe.throw('Chọn phiếu chuyển đi đang trên đường (đã xác nhận, qua kho đang vận chuyển)')
    return doc


def _destination(name, company, transit):
    doc = frappe.get_doc('Warehouse', name)
    doc.check_permission('read')
    if (doc.company != company or doc.disabled or doc.is_group or doc.get('warehouse_type') == 'Transit'
            or name == transit):
        frappe.throw('Chọn kho nhận lá đang dùng, cùng đơn vị với phiếu chuyển, không phải kho đang vận chuyển')


def _item(row):
    item = frappe.get_doc('Item', row.item_code)
    item.check_permission('read')
    if item.stock_uom != 'Kg' or _number(row.conversion_factor or 1) != 1:
        frappe.throw('Cửa sổ nhận chuyến chỉ nhận hàng tồn Kg, hệ số 1; hàng khác dùng phiếu kho chuẩn')
    if item.has_serial_no or item.has_batch_no:
        frappe.throw('Hàng theo lô/sê-ri dùng phiếu kho chuẩn để đủ hồ sơ')
    return item


def received(outgoing):
    """Tổng lượng (đơn vị tồn) đã nhận theo từng dòng phiếu chuyển, đọc trực tiếp các phiếu nhận đã xác nhận.
    Gọi sau khi đã khóa phiếu chuyển đi (mọi lối nhận đều khóa cùng dòng đó) nên không cần khóa tổng."""
    rows = frappe.db.sql('''SELECT d.ste_detail, SUM(d.transfer_qty) FROM `tabStock Entry Detail` d
        INNER JOIN `tabStock Entry` se ON se.name=d.parent
        WHERE d.against_stock_entry=%s AND se.docstatus=1 AND se.outgoing_stock_entry=%s
        GROUP BY d.ste_detail''', (outgoing, outgoing))
    return {key: _number(round(float(qty or 0), 6)) for key, qty in rows}


def remaining_rows(doc):
    done = received(doc.name)
    return {row.name: _number(round(float(row.transfer_qty or 0), 6)) - done.get(row.name, _number(0)) for row in doc.items}


@frappe.whitelist(methods=['POST'])
def incoming(company):
    guard()
    frappe.get_doc('Company', company).check_permission('read')
    rows = frappe.get_list('Stock Entry', filters={'company': company, 'docstatus': 1, 'purpose': 'Material Transfer',
        'add_to_transit': 1, 'per_transferred': ['<', 100]}, fields=['name', 'posting_date'],
        order_by='posting_date desc', limit_page_length=201)
    if len(rows) > 200:
        frappe.throw('Có hơn 200 chuyến đang trên đường; mở đúng phiếu chuyển để nhận')
    return [{'name': r.name, 'posting_date': str(r.posting_date)} for r in rows]


@frappe.whitelist(methods=['POST'])
def preview(stock_entry):
    guard()
    doc = _outgoing(stock_entry)
    left = remaining_rows(doc)
    items = []
    for row in doc.items:
        qty = left.get(row.name, 0)
        if qty <= 0:
            continue
        item = _item(row)
        suggested = ''
        if row.get('material_request_item'):
            suggested = frappe.db.get_value('Material Request Item', row.material_request_item, 'warehouse') or ''
        items.append({'source_row': row.name, 'item_code': row.item_code, 'transit_warehouse': row.t_warehouse,
                      'warehouse': suggested, 'remaining': float(qty),
                      'kg_per_bag': float(_number(item.get('kh_aph_kg_per_bag') or 0))})
    if not items:
        frappe.throw('Chuyến này đã nhận đủ')
    return {'stock_entry': doc.name, 'company': doc.company, 'sent_date': str(doc.posting_date), 'items': items}


def _selection(raw):
    values = frappe.parse_json(raw)
    if not isinstance(values, list) or not values or len(values) > 100:
        frappe.throw('Chọn từ 1 đến 100 dòng thực nhận')
    selected = {}
    for row in values:
        if not isinstance(row, dict) or set(row) != {'source_row', 'warehouse', 'qty', 'bags'}:
            frappe.throw('Dữ liệu nhận chuyến không hợp lệ')
        key = str(row['source_row'] or '')
        if not key or key in selected:
            frappe.throw('Dòng phiếu chuyển bị thiếu hoặc trùng')
        qty, bags = _number(row['qty']), _number(row['bags'])
        if qty <= 0 or bags != bags.to_integral_value():
            frappe.throw('Kg nhận phải dương, số bao phải nguyên')
        selected[key] = {'warehouse': str(row['warehouse'] or '').strip(), 'qty': str(qty.normalize()),
                         'bags': str(bags.normalize())}
    return selected


@frappe.whitelist(methods=['POST'])
@retry_rpc
def receive(stock_entry, request_id, rows, received_date, receiver, note=None):
    guard()
    doc = _outgoing(stock_entry)
    selected = _selection(rows)
    receiver, note = str(receiver or '').strip(), str(note or '').strip()
    if not receiver or len(receiver) > 140 or len(note) > 2000:
        frappe.throw('Cần người thực nhận và ghi chú trong giới hạn cho phép')
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 100:
        frappe.throw('Thiếu mã lượt nhận; mở lại cửa sổ nhận chuyến')
    if not received_date or getdate(received_date) > getdate(today()) or getdate(received_date) < getdate(doc.posting_date):
        frappe.throw('Ngày nhận phải từ ngày chuyển đi đến hôm nay')
    body = json.dumps([stock_entry, selected, str(getdate(received_date)), receiver, note], sort_keys=True, ensure_ascii=False)
    payload = hashlib.sha256(body.encode()).hexdigest()
    key = hashlib.sha256(json.dumps(['transfer', frappe.session.user, stock_entry, request_id]).encode()).hexdigest()
    # Khóa Company → phiếu chuyển đi rồi đọc hiện tại; cùng thứ tự với hook phiếu nhận native.
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', doc.company)
    frappe.db.sql('SELECT name FROM `tabStock Entry` WHERE name=%s FOR UPDATE', stock_entry)
    old = frappe.db.sql('SELECT name FROM `tabStock Entry` WHERE kh_aph_transfer_request=%s FOR UPDATE', key)
    if old:
        entry = frappe.get_doc('Stock Entry', old[0][0], for_update=True)
        entry.check_permission('read')
        if entry.get(PREFIX + 'payload') != payload or entry.docstatus != 1:
            frappe.throw('Lượt nhận đã có nội dung khác hoặc phiếu đã thay đổi; kiểm tra phiếu cũ')
        return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus}
    doc = _outgoing(stock_entry, lock=True)
    left = remaining_rows(doc)
    by_name = {r.name: r for r in doc.items}
    for name, values in selected.items():
        row = by_name.get(name)
        if not row:
            frappe.throw('Dòng không thuộc phiếu chuyển đã chọn')
        item = _item(row)
        qty, bags = _number(values['qty']), _number(values['bags'])
        if qty > left.get(name, 0):
            frappe.throw('Lượng nhận vượt lượng còn đang trên đường; phần thừa xử lý bằng kiểm kê, không nhận vượt')
        _destination(values['warehouse'], doc.company, row.t_warehouse)
        weight = _number(item.get('kh_aph_kg_per_bag') or 0)
        if (weight and (not bags or qty != bags * weight)) or (not weight and bags):
            frappe.throw('Kg/số bao không khớp quy cách; không tự sửa kg/bao để cân bằng')
    from erpnext.stock.doctype.stock_entry.stock_entry import make_stock_in_entry
    entry = make_stock_in_entry(stock_entry)
    entry.items = [r for r in entry.items if r.ste_detail in selected]
    if {r.ste_detail for r in entry.items} != set(selected):
        frappe.throw('Phiếu chuyển đã đổi; mở lại cửa sổ nhận chuyến')
    for row in entry.items:
        values = selected[row.ste_detail]
        row.qty = float(_number(values['qty']))
        row.transfer_qty = row.qty
        row.t_warehouse = values['warehouse']
        if _number(values['bags']):
            row.kh_aph_bags = float(_number(values['bags']))
    entry.posting_date = str(getdate(received_date))
    entry.set_posting_time = 1
    for field, value in {'request': key, 'payload': payload, 'actor': frappe.session.user, 'at': now_datetime(),
                         'receiver': receiver, 'note': note}.items():
        entry.set(PREFIX + field, value)
    token = _INTERNAL.set((frappe.session.user, key, payload))
    try:
        entry.insert()
        entry.submit()
    finally:
        _INTERNAL.reset(token)
    entry.check_permission('read')
    return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus}


@frappe.whitelist(methods=['POST'])
@retry_rpc
def send(company, request_id, rows, sent_date, carrier, note=None):
    """NM05: lập + xác nhận phiếu chuyển đi qua kho đang vận chuyển của chính đơn vị (cùng đơn vị, không đổi chủ sở hữu)."""
    guard()
    frappe.get_doc('Company', company).check_permission('read')
    transit = frappe.db.get_value('Company', company, 'default_in_transit_warehouse')
    if not transit:
        frappe.throw('Đơn vị chưa có kho đang vận chuyển mặc định')
    values = frappe.parse_json(rows)
    if not isinstance(values, list) or not values or len(values) > 100:
        frappe.throw('Chọn từ 1 đến 100 dòng chuyển')
    clean = []
    for row in values:
        if not isinstance(row, dict) or set(row) != {'item_code', 'warehouse', 'qty', 'bags'}:
            frappe.throw('Dữ liệu chuyển kho không hợp lệ')
        qty, bags = _number(row['qty']), _number(row['bags'])
        if qty <= 0 or bags != bags.to_integral_value():
            frappe.throw('Kg chuyển phải dương, số bao phải nguyên')
        clean.append({'item_code': str(row['item_code']), 'warehouse': str(row['warehouse']),
                      'qty': str(qty.normalize()), 'bags': str(bags.normalize())})
    carrier, note = str(carrier or '').strip(), str(note or '').strip()
    if not carrier or len(carrier) > 140 or len(note) > 2000:
        frappe.throw('Cần người/xe chở và ghi chú trong giới hạn cho phép')
    if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 100:
        frappe.throw('Thiếu mã lượt chuyển; mở lại cửa sổ')
    if not sent_date or getdate(sent_date) > getdate(today()):
        frappe.throw('Ngày chuyển không được ở tương lai')
    body = json.dumps(['send', company, clean, str(getdate(sent_date)), carrier, note], sort_keys=True, ensure_ascii=False)
    payload = hashlib.sha256(body.encode()).hexdigest()
    key = hashlib.sha256(json.dumps(['transfer-send', frappe.session.user, company, request_id]).encode()).hexdigest()
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', company)
    old = frappe.db.sql('SELECT name FROM `tabStock Entry` WHERE kh_aph_transfer_request=%s FOR UPDATE', key)
    if old:
        entry = frappe.get_doc('Stock Entry', old[0][0], for_update=True)
        entry.check_permission('read')
        if entry.get(PREFIX + 'payload') != payload or entry.docstatus != 1:
            frappe.throw('Lượt chuyển đã có nội dung khác hoặc phiếu đã thay đổi; kiểm tra phiếu cũ')
        return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus}
    items = []
    for r in clean:
        row = frappe._dict(item_code=r['item_code'], conversion_factor=1)
        item = _item(row)
        src = frappe.get_doc('Warehouse', r['warehouse'])
        src.check_permission('read')
        if src.company != company or src.is_group or src.disabled or src.name == transit:
            frappe.throw('Kho chuyển đi phải là kho lá đang dùng của đơn vị')
        weight = _number(item.get('kh_aph_kg_per_bag') or 0)
        qty, bags = _number(r['qty']), _number(r['bags'])
        if (weight and (not bags or qty != bags * weight)) or (not weight and bags):
            frappe.throw('Kg/số bao không khớp quy cách; không tự sửa kg/bao để cân bằng')
        line = {'item_code': r['item_code'], 'qty': float(qty), 'uom': 'Kg', 'conversion_factor': 1,
                's_warehouse': r['warehouse'], 't_warehouse': transit}
        if bags:
            line['kh_aph_bags'] = float(bags)
        items.append(line)
    entry = frappe.get_doc({'doctype': 'Stock Entry', 'stock_entry_type': 'Material Transfer', 'purpose': 'Material Transfer',
                            'company': company, 'add_to_transit': 1, 'posting_date': str(getdate(sent_date)),
                            'set_posting_time': 1, 'items': items})
    for field, value in {'request': key, 'payload': payload, 'actor': frappe.session.user, 'at': now_datetime(),
                         'receiver': carrier, 'note': note}.items():
        entry.set(PREFIX + field, value)
    token = _INTERNAL.set((frappe.session.user, key, payload))
    try:
        entry.insert()
        entry.submit()
    finally:
        _INTERNAL.reset(token)
    entry.check_permission('read')
    return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus}


def _stamp(doc, field):
    return str(doc.get(PREFIX + field) or '')


def protect(doc, method=None):
    """Dấu nhận chuyến chỉ do cửa sổ tạo, không sửa sau đó (giữ cả khi tắt cờ)."""
    values = [doc.get(PREFIX + f) for f in STAMP]
    if not any(values):
        return
    if doc.is_new():
        if _INTERNAL.get() != (frappe.session.user, values[0], values[1]):
            frappe.throw('Dấu nhận chuyến chỉ được tạo qua cửa sổ nhận chuyến')
        return
    old = doc.get_doc_before_save()
    if old and any(_stamp(old, f) != _stamp(doc, f) for f in STAMP):
        frappe.throw('Không sửa dấu và hồ sơ thực nhận chuyến; giữ lịch sử trên phiếu gốc')


def lock_outgoing(doc, method=None):
    """Mọi phiếu nhận từ hàng đang vận chuyển (kể cả màn chuẩn) khóa phiếu chuyển đi trước khi ERPNext cộng lượng,
    để hai phiên không cùng nhận vượt lượng chuyển."""
    if not enabled() or doc.get('purpose') != 'Material Transfer' or not doc.get('outgoing_stock_entry'):
        return
    company = frappe.db.get_value('Stock Entry', doc.outgoing_stock_entry, 'company')
    if company != doc.company:
        frappe.throw('Phiếu nhận phải cùng đơn vị với phiếu chuyển đi')
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', company)
    frappe.db.sql('SELECT name FROM `tabStock Entry` WHERE name=%s FOR UPDATE', doc.outgoing_stock_entry)
    if method == 'before_cancel':
        return
    left = remaining_rows(frappe.get_doc('Stock Entry', doc.outgoing_stock_entry))
    asked = {}
    for row in doc.items:
        if row.get('against_stock_entry') == doc.outgoing_stock_entry and row.get('ste_detail'):
            asked[row.ste_detail] = asked.get(row.ste_detail, _number(0)) + _number(round(float(row.transfer_qty or 0), 6))
    for key, qty in asked.items():
        if qty > left.get(key, _number(0)):
            frappe.throw('Lượng nhận vượt lượng còn đang trên đường của phiếu chuyển')


def prevent_delete(doc, method=None):
    if doc.get(PREFIX + 'request'):
        frappe.throw('Giữ phiếu nhận chuyến đã có mã lượt để đối soát, kể cả sau hủy')


def schema():
    if not enabled():
        return
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    labels = {'request': 'Mã lượt nhận chuyến', 'payload': 'Dấu nội dung nhận chuyến', 'actor': 'Người nhập nhận chuyến',
              'at': 'Thời điểm ghi nhận chuyến', 'receiver': 'Người nhận / người chở chuyến', 'note': 'Ghi chú nhận chuyến'}
    fields = [{'fieldname': PREFIX + k, 'label': labels[k],
               'fieldtype': 'Datetime' if k == 'at' else 'Small Text' if k == 'note' else 'Data',
               'read_only': 1, 'no_copy': 1, 'hidden': int(k in ('request', 'payload')),
               **({'unique': 1} if k == 'request' else {})} for k in STAMP]
    create_custom_fields({'Stock Entry': fields})
