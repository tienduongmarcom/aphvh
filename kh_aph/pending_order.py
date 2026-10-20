"""Giữ chỗ lượng nhận vật lý chưa có giá trên đúng dòng đơn mua."""
from collections import defaultdict
from contextvars import ContextVar

import frappe
from frappe.utils import cint

PO_FIELD = 'kh_aph_receiving_purchase_order'
ROW_FIELD = 'kh_aph_receiving_source_row'
FINALIZING = ContextVar('pending_order_finalizing', default=None)


def installed():
    # Hồ sơ đã phát sinh vẫn giữ chỗ khi tắt tính năng; không đọc cột chưa cài.
    return frappe.db.has_column('APH Pending Receipt', PO_FIELD)


def pending_source(source):
    # Phiếu chờ hiện hữu và cửa sổ chốt giá dùng VND; không suy giá ngoại tệ thành VND.
    from kh_aph.factory_receiving import _number
    if source.currency != 'VND' or _number(source.conversion_rate) != 1:
        frappe.throw('Nhận chờ định giá hiện chỉ hỗ trợ đơn mua VND, tỷ giá 1')


def lock_orders(company, names):
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', company)
    result = {}
    for name in sorted(set(names)):
        doc = frappe.get_doc('Purchase Order', name, for_update=True)
        doc.check_permission('read')
        if doc.company != company:
            frappe.throw('Đơn mua không thuộc đơn vị nhận hàng')
        result[name] = doc
    return result


def reserved(order, exclude=None, lock=False):
    """Chỉ tổng nội bộ; caller đã kiểm quyền/khóa nguồn, không trả hồ sơ ngoài quyền."""
    if not installed():
        return {}
    rows = frappe.db.sql('''SELECT p.name, i.kh_aph_receiving_source_row, i.qty
        FROM `tabAPH Pending Receipt` p
        INNER JOIN `tabAPH Pending Receipt Item` i ON i.parent=p.name
        LEFT JOIN `tabPurchase Receipt` r ON r.name=p.purchase_receipt
        WHERE p.kh_aph_receiving_purchase_order=%s AND p.docstatus=1
        AND (r.name IS NULL OR r.docstatus!=1)''' + (' FOR UPDATE' if lock else ''), order)
    from kh_aph.factory_receiving import _number
    totals = defaultdict(lambda: _number(0))
    for name, source, qty in rows:
        if name != exclude:
            totals[source] += _number(qty)
    return dict(totals)


def remaining(order, row, exclude=None, lock=False):
    from kh_aph.factory_receiving import _number
    return _number(row.qty) - _number(row.received_qty or 0) - reserved(order, exclude, lock).get(row.name, 0)


def validate_pending(doc, method=None):
    from kh_aph import factory_receiving as receiving
    receiving.protect(doc)
    order = doc.get(PO_FIELD)
    old = doc.get_doc_before_save()
    if old and old.get(PO_FIELD) != order:
        frappe.throw('Không đổi đơn mua nguồn của phiếu nhận')
    if not order:
        if any(r.get(ROW_FIELD) for r in doc.items):
            frappe.throw('Dòng nhận chờ giá thiếu đơn mua nguồn')
        return
    if doc.is_new():
        context = receiving._INTERNAL.get()
        if context != (frappe.session.user, doc.get(receiving.PREFIX+'request'), doc.get(receiving.PREFIX+'payload')):
            frappe.throw('Nguồn đơn mua chỉ tạo qua cửa sổ nhận hàng')
    if old and old.docstatus == 1:
        if any(str(old.get(f) or '') != str(doc.get(f) or '') for f in ('company', 'supplier', 'received_date')):
            frappe.throw('Không đổi đơn vị, nhà cung cấp hoặc ngày của hồ sơ thực nhận')
        def snapshot(rows):
            return [(r.name, r.item_code, r.warehouse, r.get(ROW_FIELD),
                receiving._number(r.qty), receiving._number(r.kh_aph_bags or 0)) for r in rows]
        if snapshot(old.items) != snapshot(doc.items):
            frappe.throw('Không sửa nguồn hoặc lượng đã nhận; xử lý hủy theo lịch sử')
    for row in doc.items:
        if receiving._number(row.get('kh_aph_receiving_quality_qty') or 0) > receiving._number(row.qty):
            frappe.throw('Lượng có vấn đề không được vượt tổng thực nhận')


def pending_transition(doc, method=None):
    order = doc.get(PO_FIELD)
    if not order:
        return
    from kh_aph.factory_receiving import _number, _item, _warehouse
    source = lock_orders(doc.company, [order])[order]
    if method == 'before_cancel':
        return  # Controller cũ vẫn chặn nếu PR còn hoạt động.
    if source.docstatus != 1 or source.status in ('Closed', 'Cancelled', 'On Hold'):
        frappe.throw('Đơn mua phải đang xác nhận và còn được nhận hàng')
    if source.get('is_subcontracted') or source.get('has_unit_price_items'):
        frappe.throw('Đơn gia công/giá đơn vị không nhận qua cửa sổ này')
    pending_source(source)
    if source.supplier != doc.supplier:
        frappe.throw('Nhà cung cấp không khớp đơn mua')
    quantities = defaultdict(lambda: _number(0))
    for row in doc.items:
        key = row.get(ROW_FIELD)
        original = next((r for r in source.items if r.name == key), None)
        if not original or original.item_code != row.item_code:
            frappe.throw('Dòng chờ giá không đúng dòng đơn mua')
        _item(original, require_price=False)
        _warehouse(row.warehouse, doc.company)
        quantities[key] += _number(row.qty)
    held = reserved(order, exclude=doc.name, lock=True)
    for key, qty in quantities.items():
        row = next(r for r in source.items if r.name == key)
        if qty > _number(row.qty) - _number(row.received_qty or 0) - held.get(key, 0):
            frappe.throw('Lượng chờ định giá vượt phần còn được nhận của đơn mua')


def native_receipt(doc, method=None):
    """Cả PR chuẩn và PI cập nhật kho phải nhường phần đã nhận chờ giá."""
    if not installed() or (doc.doctype == 'Purchase Invoice' and not cint(doc.get('update_stock'))):
        return
    from kh_aph.factory_receiving import _number
    is_pr = doc.doctype == 'Purchase Receipt'
    field = 'purchase_order_item' if is_pr else 'po_detail'
    rows = [r for r in doc.items if r.get('purchase_order') and r.get(field)]
    if not rows:
        return
    orders = lock_orders(doc.company, [r.purchase_order for r in rows])
    if method == 'before_cancel':
        return
    own = FINALIZING.get() if is_pr else None
    if own != doc.get('kh_aph_pending_receipt'):
        # Không được loại trừ giữ chỗ bằng dữ liệu client.
        own = None
    for name, source in orders.items():
        held = reserved(name, exclude=own, lock=True)
        if not held:
            continue
        totals = defaultdict(lambda: _number(0))
        for r in rows:
            if r.purchase_order != name:
                continue
            if cint(doc.get('is_return')):
                continue
            original = next((v for v in source.items if v.name == r.get(field)), None)
            if not original:
                frappe.throw('Dòng nhập không còn trên đơn mua')
            if not held.get(original.name, 0):
                continue
            qty = _number(r.received_qty or r.qty) * _number(r.conversion_factor) / _number(original.conversion_factor)
            totals[original.name] += qty
        for key, qty in totals.items():
            original = next(v for v in source.items if v.name == key)
            if held.get(key, 0) and qty > _number(original.qty) - _number(original.received_qty or 0) - held[key]:
                frappe.throw('Lượng nhập vượt phần còn lại sau khi giữ hàng đang chờ định giá')


def protect_order(doc, method=None):
    if not installed():
        return
    from kh_aph.factory_receiving import _number
    source = lock_orders(doc.company, [doc.name])[doc.name]
    held = reserved(doc.name, lock=True)
    if not held:
        return
    if method in ('before_cancel', 'on_trash'):
        frappe.throw('Đơn mua còn hàng chờ định giá; xử lý phiếu nhận trước')
    for name, qty in held.items():
        pending_items = frappe.db.sql('''SELECT i.item_code FROM `tabAPH Pending Receipt Item` i
            INNER JOIN `tabAPH Pending Receipt` p ON p.name=i.parent
            WHERE p.kh_aph_receiving_purchase_order=%s AND p.docstatus=1
            AND i.kh_aph_receiving_source_row=%s FOR UPDATE''', (doc.name, name))
        row = next((r for r in doc.items if r.name == name), None)
        original = next((r for r in source.items if r.name == name), None)
        if (not row or not original or row.item_code != original.item_code
                or row.uom != 'Kg' or _number(row.conversion_factor) != 1
                or any(item[0] != row.item_code for item in pending_items)
                or _number(row.qty) < _number(original.received_qty or 0) + qty):
            frappe.throw('Không đổi nguồn hoặc giảm đơn mua dưới lượng đã nhận và chờ định giá')


def cancelled_source(doc):
    """Chỉ nhận đúng hồ sơ chờ do service đã chuyển, không tin Link client."""
    name = doc.get('kh_aph_pending_receipt')
    if not name or not doc.get('kh_aph_receiving_request'):
        return None
    pending = frappe.get_doc('APH Pending Receipt', name, for_update=True)
    pending.check_permission('read')
    pending.check_permission('write')
    if (pending.docstatus != 1 or pending.purchase_receipt != doc.name
            or not pending.get(PO_FIELD)
            or pending.get('kh_aph_receiving_request') != doc.get('kh_aph_receiving_request')
            or pending.get('kh_aph_receiving_payload') != doc.get('kh_aph_receiving_payload')):
        frappe.throw('Quan hệ phiếu chờ và phiếu nhập không khớp để hủy')
    return pending


class PendingReceiptLinks:
    def check_no_back_links_exist(self):
        if self.docstatus != 2 or not self.get('kh_aph_receiving_request') or not self.get('kh_aph_pending_receipt'):
            return super().check_no_back_links_exist()
        pending = cancelled_source(self)
        if not pending:
            return super().check_no_back_links_exist()
        # Chỉ miễn đúng hồ sơ nguồn để giữ Link lịch sử, kiểm mọi backlink khác.
        from frappe.model.delete_doc import get_linked_docs, get_dynamic_linked_docs, raise_link_exists_exception
        for ref in get_linked_docs(self, method='Cancel') + get_dynamic_linked_docs(self, method='Cancel'):
            if (ref['reference_doctype'], ref['reference_docname']) != ('APH Pending Receipt', pending.name):
                raise_link_exists_exception(self, ref['reference_doctype'], ref['reference_docname'])


def receipt_cancelled(doc, method=None):
    if doc.get('kh_aph_pending_receipt') and doc.get('kh_aph_receiving_request'):
        pending = cancelled_source(doc)
        pending.db_set('status', 'Chờ định giá', update_modified=True)
