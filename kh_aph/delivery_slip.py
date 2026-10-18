"""Read-only quantity slip for selected company deliveries of one shared order."""
import html
import json
import frappe
from frappe.utils import cint, flt


def _orders(shared_order):
    shared = frappe.get_doc('APH Shared Sales Order', shared_order)
    shared.check_permission('read')
    shared.check_permission('print')
    if cint(shared.docstatus) != 1:
        frappe.throw('Chỉ in giao hàng từ đơn chung đã xác nhận')
    names = frappe.get_all('Sales Order', filters={'kh_aph_shared_order': shared.name}, pluck='name')
    allowed = {name for name in names if frappe.has_permission('Sales Order', 'read', doc=name)}
    return shared, allowed


@frappe.whitelist()
def deliveries(shared_order):
    shared, orders = _orders(shared_order)
    if not orders:
        return []
    names = frappe.get_all('Delivery Note Item', filters={'against_sales_order': ['in', sorted(orders)]}, pluck='parent')
    result = []
    for name in sorted(set(names)):
        doc = frappe.get_doc('Delivery Note', name)
        if (cint(doc.docstatus) != 1 or cint(doc.is_return)
            or not frappe.has_permission('Delivery Note', 'print', doc=doc)
            or not frappe.has_permission('Delivery Note', 'read', doc=doc)):
            continue
        if doc.customer != shared.customer or any(row.against_sales_order not in orders for row in doc.items):
            continue
        result.append({'name': doc.name, 'company': doc.company,
                       'state': doc.get('kh_aph_delivery_state') or '', 'date': str(doc.posting_date)})
    return result


def render(shared, documents):
    from kh_aph.delivery_info_rules import print_snapshot
    escape = lambda value: html.escape(str(value or ''), quote=True)
    rows = []
    signatures = []
    for doc in documents:
        info = print_snapshot(doc)
        signatures.append('<div class="handoff"><b>Phiếu ' + escape(doc.name) + '</b> - ' + escape(doc.company)
            + '<br>Cách giao: ' + escape(info['method']) + '; Người nhận: ' + escape(info['recipient'])
            + '; Điện thoại: ' + escape(info['phone']) + '<br>Lái xe: ' + escape(info['driver'])
            + '; Biển số: ' + escape(info['vehicle']) + '; Thời điểm xuất: ' + escape(info['time'])
            + '<br>Người thực giao: ' + escape(info['dispatcher'])
            + '<p>Người giao ký: ____________________ &nbsp; Người nhận ký: ____________________</p></div>')
        for item in doc.items:
            cells = [doc.name, doc.company, item.warehouse, item.item_code, item.item_name,
                     format(flt(item.stock_qty), '.9f').rstrip('0').rstrip('.'), item.stock_uom, doc.get('kh_aph_delivery_state')]
            rows.append('<tr>' + ''.join('<td>' + escape(value) + '</td>' for value in cells) + '</tr>')
    headers = ('Phiếu giao', 'Đơn vị sở hữu', 'Kho xuất', 'Mã hàng', 'Tên hàng', 'Số lượng', 'ĐVT', 'Trạng thái')
    return ('<!doctype html><html lang="vi"><meta charset="utf-8"><title>Phiếu giao hàng tổng hợp</title>'
            '<style>@page{size:A4;margin:12mm}body{font:13px Arial;margin:24px}table{width:100%;border-collapse:collapse}'
            'td,th{border:1px solid #444;padding:6px;text-align:left}h1{font-size:20px;text-align:center}'
            '.handoff{break-inside:avoid;border-top:1px solid #777;margin-top:14px;padding-top:8px;min-height:85px}'
            '@media print{body{margin:0}tr{break-inside:avoid}thead{display:table-header-group}}</style>'
            '<h1>PHIẾU GIAO HÀNG TỔNG HỢP</h1><p>Mẫu quản trị nội bộ - không thay chứng từ kế toán từng đơn vị.</p><p>Đơn chung: ' + escape(shared.name)
            + '<br>Khách hàng: ' + escape(shared.customer) + '</p><table><thead><tr>'
            + ''.join('<th>' + escape(h) + '</th>' for h in headers) + '</tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table>' + ''.join(signatures) + '</html>')


@frappe.whitelist(methods=['POST'])
def consolidated(shared_order, delivery_notes):
    shared, orders = _orders(shared_order)
    selected = json.loads(delivery_notes) if isinstance(delivery_notes, str) else delivery_notes
    if (not isinstance(selected, list) or not selected or len(selected) > 50
        or any(not isinstance(n, str) for n in selected) or len(selected) != len(set(selected))):
        frappe.throw('Chọn từ 1 đến 50 phiếu giao, không chọn trùng')
    documents = []
    for name in selected:
        doc = frappe.get_doc('Delivery Note', name)
        doc.check_permission('read')
        doc.check_permission('print')
        if (cint(doc.docstatus) != 1 or cint(doc.is_return) or doc.customer != shared.customer
            or not doc.items or any(row.against_sales_order not in orders for row in doc.items)):
            frappe.throw('Phiếu giao không thuộc đơn chung hoặc chưa được xuất')
        documents.append(doc)
    return {'html': render(shared, documents), 'delivery_notes': selected}
