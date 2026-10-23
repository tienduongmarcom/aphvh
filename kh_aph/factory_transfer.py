"""NM01c — nhận chuyến chuyển kho đến nhà máy (cùng đơn vị) trên Stock Entry native.

Phiếu chuyển đi (Material Transfer, add_to_transit) do kho nguồn lập như hiện có; cửa sổ này chỉ lập phiếu nhận
(Stock Entry nhận từ hàng đang vận chuyển, `outgoing_stock_entry`) theo lượng thực nhận, nhận từng phần được.
Không dùng phiếu mua (PR) cho chuyến chuyển; chuyển khác đơn vị là mua bán nội bộ, không thuộc cửa sổ này.
Lượng thiếu nằm lại kho đang vận chuyển chờ đối soát, không tự ghi hao hụt; nhận vượt lượng chuyển bị chặn.
Tái dùng cờ nhận nhà máy hoặc kho vận hành (mặc định tắt); không phụ thuộc màn Nhà máy khi dùng ở cửa hàng.
"""
from contextvars import ContextVar
import hashlib
import json

import frappe
from frappe.utils import cint, getdate, today, now_datetime
from kh_aph.cash_transaction import retry_rpc
from kh_aph.factory_receiving import _number, ROLES

DESTINATION = "kh_aph_transfer_destination"


def enabled():
    return bool(cint(frappe.conf.get("kh_aph_factory_receiving")) or cint(frappe.conf.get("kh_aph_kho_van_hanh")))


def guard():
    if not enabled() or not cint(frappe.conf.get("kh_aph_quantity_valuation_mvp")):
        frappe.throw("Chưa bật chuyển và nhận hàng giữa các kho")
    if not cint(frappe.conf.get("kh_aph_server_cost_guard")):
        frappe.throw("Cần bật bảo vệ giá vốn trước khi chuyển kho")
    if (frappe.session.user == "Guest" or (frappe.session.user != "Administrator"
            and not (set(frappe.get_roles()) & (ROLES | {"Thủ kho bán hàng"})))):
        frappe.throw("Không đủ quyền chuyển và nhận hàng giữa các kho", frappe.PermissionError)
    if not frappe.db.get_value("User", frappe.session.user, "enabled"):
        frappe.throw("Tài khoản chưa hoạt động", frappe.PermissionError)

PREFIX = 'kh_aph_transfer_'
STAMP = ('request', 'payload', 'actor', 'at', 'receiver', 'note')
_INTERNAL = ContextVar('factory_transfer', default=None)


def _outgoing(name, lock=False):
    doc = frappe.get_doc('Stock Entry', name, for_update=lock)
    if frappe.has_permission('Stock Entry','read',doc=doc):
        doc.check_permission('read')
    else:
        from kh_aph.transfer_access import expected_receiver
        expected_receiver(doc)
    frappe.get_doc('Company', doc.company).check_permission('read')
    if (doc.docstatus != 1 or doc.purpose != 'Material Transfer' or not cint(doc.add_to_transit)
            or doc.get('outgoing_stock_entry')):
        frappe.throw('Chọn phiếu chuyển đi đang trên đường (đã xác nhận, qua kho đang vận chuyển)')
    return doc


def _destination(name, company, transit, planning=False):
    doc = frappe.get_doc('Warehouse', name)
    if planning:
        frappe.get_doc('Company',company).check_permission('read')
        if not frappe.has_permission('Stock Entry','create'):
            frappe.throw('Cần quyền chuẩn bị chuyến chuyển',frappe.PermissionError)
    else:
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
    rows=[row for row in rows if frappe.has_permission('Stock Entry','read',doc=frappe.get_doc('Stock Entry',row.name))]
    # Ngoài phiếu nguồn được đọc native, đầu nhận chỉ thấy mã/ngày chuyến có
    # kho dự kiến nằm trong phạm vi mình. Không lấy qty/giá hoặc trả doc nguồn.
    allowed=frappe.get_list('Warehouse',filters={'company':company,'is_group':0,'disabled':0},pluck='name',limit_page_length=0)
    if allowed and frappe.has_permission('Stock Entry','create') and frappe.has_permission('Stock Entry','submit'):
        addressed=frappe.get_all('Stock Entry',filters={'company':company,'docstatus':1,'purpose':'Material Transfer',
            'add_to_transit':1,'per_transferred':['<',100],DESTINATION:['in',allowed]},
            fields=['name','posting_date'],order_by='posting_date desc',limit_page_length=201)
        rows=list({row.name:row for row in list(rows)+list(addressed)}.values())
    if len(rows)>200:frappe.throw('Có hơn200chuyến; mở đúng phiếu chuyển để nhận')
    rows=sorted(rows,key=lambda row:(str(row.posting_date),row.name),reverse=True)
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
        suggested = doc.get(DESTINATION) or ''
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
    planned = doc.get(DESTINATION)
    if planned and any(v['warehouse'] != planned for v in selected.values()) and not note:
        frappe.throw('Nhận khác kho dự kiến: ghi lý do và kho thực nhận trong ghi chú')
    if planned and any(v['warehouse'] != planned for v in selected.values()):
        note = ('Kho dự kiến: ' + planned + '; kho thực nhận: ' + ', '.join(sorted({v['warehouse'] for v in selected.values()})) + '. ' + note)
        if len(note) > 2000:
            frappe.throw('Ghi chú đổi kho nhận quá dài')
    from erpnext.stock.doctype.stock_entry.stock_entry import make_stock_in_entry
    if frappe.has_permission('Stock Entry','read',doc=doc):
        entry = make_stock_in_entry(stock_entry)
    else:
        from kh_aph.transfer_access import make_incoming
        entry = make_incoming(doc)
    entry.items = [r for r in entry.items if r.ste_detail in selected]
    if {r.ste_detail for r in entry.items} != set(selected):
        frappe.throw('Phiếu chuyển đã đổi; mở lại cửa sổ nhận chuyến')
    for row in entry.items:
        values = selected[row.ste_detail]
        row.qty = float(_number(values['qty']))
        row.transfer_qty = row.qty
        row.t_warehouse = values['warehouse']
        # Ghi đúng số bao thực nhận (không để mapper chép số bao của cả chuyến khi nhận một phần).
        row.kh_aph_bags = float(_number(values['bags']))
    entry.set(DESTINATION, None)  # Phiếu nhận không mang kho dự kiến của phiếu chuyển đi.
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
def send(company, request_id, rows, sent_date, carrier, note=None, prepare_only=0, destination=None):
    """Chuẩn bị để in trước hoặc xác nhận chuyển thực tế qua kho đang vận chuyển, cùng đơn vị."""
    guard()
    frappe.get_doc('Company', company).check_permission('read')
    if prepare_only not in (0, 1, '0', '1'):
        frappe.throw('Chọn chuẩn bị phiếu hoặc xác nhận chuyển thực tế')
    prepare_only = cint(prepare_only)
    if destination is not None and not isinstance(destination, str):
        frappe.throw('Kho nhận dự kiến không hợp lệ')
    destination = (destination or '').strip()
    if prepare_only and not destination:
        frappe.throw('Chọn kho nhận dự kiến trước khi chuẩn bị phiếu')
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
    identity = ['send', company, clean, str(getdate(sent_date)), carrier, note]
    if prepare_only or destination:
        identity.extend([prepare_only, destination])
    body = json.dumps(identity, sort_keys=True, ensure_ascii=False)
    payload = hashlib.sha256(body.encode()).hexdigest()
    key = hashlib.sha256(json.dumps(['transfer-send', frappe.session.user, company, request_id]).encode()).hexdigest()
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', company)
    old = frappe.db.sql('SELECT name FROM `tabStock Entry` WHERE kh_aph_transfer_request=%s FOR UPDATE', key)
    if old:
        entry = frappe.get_doc('Stock Entry', old[0][0], for_update=True)
        entry.check_permission('read')
        if entry.get(PREFIX + 'payload') != payload or entry.docstatus not in ((0, 1) if prepare_only else (1,)):
            frappe.throw('Lượt chuyển đã có nội dung khác hoặc phiếu đã thay đổi; kiểm tra phiếu cũ')
        return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus}
    if destination:
        _destination(destination, company, transit, planning=True)
    items = []
    for r in clean:
        row = frappe._dict(item_code=r['item_code'], conversion_factor=1)
        item = _item(row)
        src = frappe.get_doc('Warehouse', r['warehouse'])
        src.check_permission('read')
        if src.company != company or src.is_group or src.disabled or src.name == transit or src.get('warehouse_type') == 'Transit' or src.name == destination:
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
                            'set_posting_time': 1, DESTINATION: destination or None, 'items': items})
    for field, value in {'request': key, 'payload': payload, 'actor': frappe.session.user, 'at': now_datetime(),
                         'receiver': carrier, 'note': note}.items():
        entry.set(PREFIX + field, value)
    token = _INTERNAL.set((frappe.session.user, key, payload))
    try:
        entry.insert()
        if not prepare_only:
            entry.submit()
    finally:
        _INTERNAL.reset(token)
    entry.check_permission('read')
    return {'name': entry.name, 'doctype': 'Stock Entry', 'docstatus': entry.docstatus}


def _stamp(doc, field):
    return str(doc.get(PREFIX + field) or '')


def protect(doc, method=None):
    """Dấu nhận chuyến chỉ do cửa sổ tạo, không sửa sau đó (giữ cả khi tắt cờ)."""
    old = doc.get_doc_before_save() if not doc.is_new() else None
    destination = doc.get(DESTINATION)
    if old and old.get(PREFIX + 'request') and old.get(DESTINATION) and not destination:
        frappe.throw('Giữ kho nhận dự kiến của bản chuẩn bị; chọn kho nhận đúng hoặc bỏ bản nháp chưa ghi')
    if old and cint(old.docstatus) != 0 and (destination or '') != (old.get(DESTINATION) or ''):
        frappe.throw('Không đổi kho nhận dự kiến sau khi đã chuyển; nhận vào kho khác phải ghi lý do')
    if destination and cint(doc.docstatus) != 2:
        if doc.get('purpose') != 'Material Transfer' or not cint(doc.get('add_to_transit')) or doc.get('outgoing_stock_entry'):
            frappe.throw('Kho nhận dự kiến chỉ dùng trên phiếu chuyển đi qua kho đang vận chuyển')
        _destination(destination, doc.company, None, planning=True)
        if any(row.get('s_warehouse') == destination for row in doc.items):
            frappe.throw('Kho nhận dự kiến phải khác kho chuyển đi')
    if old and old.get(PREFIX + 'request') and any(str(old.get(field) or '') != str(doc.get(field) or '')
            for field in ('company', 'purpose', 'stock_entry_type', 'add_to_transit', 'outgoing_stock_entry')):
        frappe.throw('Không đổi đơn vị hoặc loại chuyến của phiếu đã có mã lượt; bỏ nháp chưa ghi và chuẩn bị đúng chuyến')
    values = [doc.get(PREFIX + f) for f in STAMP]
    if not any(values):
        return
    if doc.is_new():
        if _INTERNAL.get() != (frappe.session.user, values[0], values[1]):
            frappe.throw('Dấu nhận chuyến chỉ được tạo qua cửa sổ nhận chuyến')
        return
    old = doc.get_doc_before_save()
    planning = (old and cint(old.docstatus) == 0 and old.get(DESTINATION)
                and cint(old.get('add_to_transit')) and not old.get('outgoing_stock_entry'))
    frozen = tuple(field for field in STAMP if not planning or field not in ('receiver', 'note'))
    if old and any(_stamp(old, field) != _stamp(doc, field) for field in frozen):
        frappe.throw('Không sửa dấu và hồ sơ thực nhận chuyến; giữ lịch sử trên phiếu gốc')
    if planning:
        carrier, note = _stamp(doc, 'receiver').strip(), _stamp(doc, 'note').strip()
        if not carrier or len(carrier) > 140 or len(note) > 2000:
            frappe.throw('Ghi người/xe chở và ghi chú trong giới hạn trước khi xác nhận chuyển')


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
    source = _outgoing(doc.outgoing_stock_entry)
    planned = source.get(DESTINATION)
    if planned and any(row.get('t_warehouse') and row.t_warehouse != planned for row in doc.items):
        if not doc.get(PREFIX+'request') or not doc.get(PREFIX+'note'):
            frappe.throw('Nhận khác kho dự kiến: dùng cửa sổ nhận chuyến và ghi lý do, không bỏ qua trên phiếu kho chuẩn')
    left = remaining_rows(source)
    asked = {}
    for row in doc.items:
        if row.get('against_stock_entry') == doc.outgoing_stock_entry and row.get('ste_detail'):
            asked[row.ste_detail] = asked.get(row.ste_detail, _number(0)) + _number(round(float(row.transfer_qty or 0), 6))
    for key, qty in asked.items():
        if qty > left.get(key, _number(0)):
            frappe.throw('Lượng nhận vượt lượng còn đang trên đường của phiếu chuyển')


def prevent_delete(doc, method=None):
    if doc.get(PREFIX + 'request'):
        if (cint(doc.docstatus) == 0 and doc.get(DESTINATION) and cint(doc.get('add_to_transit'))
                and not doc.get('outgoing_stock_entry')):
            return  # Bỏ bản chuẩn bị chưa ghi kho bằng xóa native; giữ Deleted Document chuẩn.
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
    for field in fields:
        if field['fieldname'] in (PREFIX + 'receiver', PREFIX + 'note'):
            field.update(read_only=0, read_only_depends_on='eval:doc.docstatus!=0 || !doc.kh_aph_transfer_request || !doc.kh_aph_transfer_destination || !doc.add_to_transit || doc.outgoing_stock_entry')
    fields.append({'fieldname': DESTINATION, 'label': 'Kho nhận dự kiến', 'fieldtype': 'Link', 'options': 'Warehouse',
                   'insert_after': 'add_to_transit', 'no_copy': 1, 'ignore_user_permissions': 1,
                   'depends_on': 'eval:doc.add_to_transit && !doc.outgoing_stock_entry',
                   'read_only_depends_on': 'eval:doc.docstatus != 0'})
    create_custom_fields({'Stock Entry': fields})


@frappe.whitelist()
def destination_query(doctype,txt,searchfield,start,page_len,filters=None):
    """Tên kho dự kiến cùng Company, không cấp xem tồn/phiếu ở kho ngoài quyền."""
    guard()
    filters=frappe.parse_json(filters) if isinstance(filters,str) else filters or {}
    company=filters.get('company') if isinstance(filters,dict) else None
    if doctype!='Warehouse' or not isinstance(company,str) or not company:
        frappe.throw('Chọn đúng đơn vị trước khi tìm kho nhận')
    frappe.get_doc('Company',company).check_permission('read')
    if not frappe.has_permission('Stock Entry','create'):
        frappe.throw('Cần quyền lập chuyến chuyển',frappe.PermissionError)
    rows=frappe.get_all('Warehouse',filters={'company':company,'is_group':0,'disabled':0,
        'warehouse_type':['!=','Transit'],'name':['like','%'+str(txt or '')[:140]+'%']},
        fields=['name'],start=max(0,cint(start)),limit_page_length=min(30,max(1,cint(page_len))),order_by='name')
    return [[row.name] for row in rows]
