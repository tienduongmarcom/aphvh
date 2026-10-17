"""Lập phiếu giao NHÁP từ đơn chung. Dùng cờ Trung tâm Bán hàng, không ghi sổ."""
import hashlib
import json
import re

import frappe
from frappe.utils import cint, flt

from kh_aph.dispatch_plan import plan
from kh_aph import delivery_info

F_ORDER = "kh_aph_don_chung_xuat"
F_BATCH = "kh_aph_dot_xuat"
F_HASH = "kh_aph_dot_xuat_hash"


def _guard():
    from kh_aph.trung_tam_ban import _can_bat
    _can_bat()
    if not cint(frappe.conf.get("kh_aph_shared_sales_order")):
        frappe.throw("Đơn chung chưa được bật")
    from kh_aph.price_visibility import is_price_restricted
    if is_price_restricted():
        frappe.throw("Không có quyền lập phiếu từ màn hình bán hàng", frappe.PermissionError)


def fields():
    return {"Delivery Note": [
        {"fieldname": F_ORDER, "label": "Đơn chung lập phiếu xuất", "fieldtype": "Link",
         "options": "APH Shared Sales Order", "insert_after": "customer", "read_only": 1, "no_copy": 1},
        {"fieldname": F_BATCH, "label": "Mã đợt lập phiếu", "fieldtype": "Data", "insert_after": F_ORDER,
         "read_only": 1, "no_copy": 1},
        {"fieldname": F_HASH, "label": "Dấu nội dung đợt lập phiếu", "fieldtype": "Data", "insert_after": F_BATCH,
         "hidden": 1, "read_only": 1, "no_copy": 1}]}


def schema():
    from kh_aph.trung_tam_ban import _can_bat
    _can_bat()
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(fields())
    # Kế toán bán hàng lập nháp; quyền xác nhận xuất vẫn theo luồng kho hiện có.
    from frappe.permissions import add_permission, update_permission_property
    for dt, rights in (("Delivery Note", ("read", "create", "write", "print")),
                       ("APH Shared Sales Order", ("read", "create", "write", "submit", "print"))):
        add_permission(dt, "Kế toán bán hàng", 0)
        for right in rights:
            update_permission_property(dt, "Kế toán bán hàng", 0, right, 1, validate=False)


def _order(name, lock=False):
    if lock:
        frappe.db.sql("SELECT name FROM `tabAPH Shared Sales Order` WHERE name=%s FOR UPDATE", name)
    doc = frappe.get_doc("APH Shared Sales Order", name, for_update=lock)
    doc.check_permission("read")
    if doc.docstatus != 1:
        frappe.throw("Xác nhận đơn chung trước khi lập phiếu xuất")
    frappe.get_doc("Customer", doc.customer).check_permission("read")
    return doc


def _rows(doc, lock=False):
    result = []
    orders = frappe.db.sql_list("""SELECT name FROM `tabSales Order`
        WHERE kh_aph_shared_order=%s AND docstatus=1 ORDER BY name""" + (" FOR UPDATE" if lock else ""), doc.name)
    for name in orders:
        if lock:
            frappe.db.sql("SELECT name FROM `tabSales Order` WHERE name=%s FOR UPDATE", name)
        so = frappe.get_doc("Sales Order", name, for_update=lock)
        so.check_permission("read")
        frappe.get_doc("Company", so.company).check_permission("read")
        if so.status in ("Closed", "Cancelled", "On Hold"):
            continue
        if so.customer != doc.customer:
            frappe.throw("Khách trên đơn nguồn không khớp đơn chung")
        for row in so.items:
            frappe.get_doc("Item", row.item_code).check_permission("read")
            wh = frappe.get_doc("Warehouse", row.warehouse)
            wh.check_permission("read")
            if wh.company != so.company or wh.is_group or wh.disabled:
                frappe.throw("Kho nguồn không còn hợp lệ: " + row.warehouse)
            # Đếm tất cả phiếu nháp, gồm phiếu lập thủ công. Đây là lượng đã lập phiếu, không phải giữ tồn vật lý.
            drafts = frappe.db.sql("""SELECT i.qty FROM `tabDelivery Note Item` i
                JOIN `tabDelivery Note` d ON d.name=i.parent
                WHERE i.so_detail=%s AND d.docstatus=0 AND IFNULL(d.is_return,0)=0
                ORDER BY d.name, i.idx""" + (" FOR UPDATE" if lock else ""), row.name)
            draft_qty = sum(flt(d[0]) for d in drafts)
            if row.get("delivered_by_supplier"):
                continue
            if row.uom != "Kg" or flt(row.conversion_factor) != 1:
                frappe.throw("Luồng nhanh chỉ nhận dòng Kg của đơn chung")
            result.append({"source_order": so.name, "source_row": row.name,
                           "company": so.company, "warehouse": row.warehouse, "item_code": row.item_code,
                           "item_name": row.item_name, "ordered_qty": flt(row.qty),
                           "delivered_qty": flt(row.delivered_qty), "draft_qty": draft_qty,
                           "remaining_qty": max(0, flt(row.qty) - flt(row.delivered_qty) - draft_qty),
                           "kg_per_bag": flt(row.get("kh_aph_kg_per_bag"))})
    return result


@frappe.whitelist()
def preview(shared_order):
    _guard()
    doc = _order(shared_order)
    if not frappe.has_permission("Delivery Note", "create"):
        frappe.throw("Bạn chưa có quyền lập phiếu giao nháp", frappe.PermissionError)
    return {"shared_order": doc.name, "customer": doc.customer, "rows": _rows(doc)}


def _summaries(notes):
    result = []
    for dn in notes:
        _note_scope(dn)
        if dn.docstatus == 2:
            frappe.throw("Đợt có phiếu đã hủy; mở lại để lập đợt mới")
        result.append({"name": dn.name, "company": dn.company, "warehouse": dn.items[0].warehouse,
                       "docstatus": dn.docstatus})
    return result


def _note_scope(dn):
    """Kiểm lại liên kết trên phiếu cũ khi in/thử lại, kể cả quyền vừa bị thu hẹp."""
    dn.check_permission("read")
    if dn.get(delivery_info.METHOD):
        delivery_info.check_address(dn.customer, dn.get("shipping_address_name"))
    frappe.get_doc("Company", dn.company).check_permission("read")
    for row in dn.items:
        frappe.get_doc("Item", row.item_code).check_permission("read")
        wh = frappe.get_doc("Warehouse", row.warehouse)
        wh.check_permission("read")
        if wh.company != dn.company:
            frappe.throw("Kho trên phiếu không thuộc đơn vị xuất hàng")


@frappe.whitelist(methods=["POST"])
def create_drafts(shared_order, selections, request_id, delivery=None):
    _guard()
    if not re.fullmatch(r"[a-zA-Z0-9-]{16,64}", request_id or ""):
        frappe.throw("Mã yêu cầu không hợp lệ; mở lại hộp thoại lập phiếu")
    choices = frappe.parse_json(selections) if isinstance(selections, str) else selections
    try:
        canonical = sorted([{"source_row": c["source_row"], "qty": str(c["qty"])} for c in choices],
                           key=lambda c: c["source_row"])
    except (TypeError, KeyError):
        frappe.throw("Dữ liệu dòng giao không hợp lệ")
    doc = _order(shared_order, lock=True)
    info = delivery_info.parse(delivery, doc.customer)
    # Giữ hash cũ khi không truyền thông tin giao nhận để retry phiếu trước nâng cấp vẫn hợp lệ.
    content = {"rows": canonical, "delivery": info} if info else canonical
    signature = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    # Current read: không dùng snapshot SELECT thường sau khi đã chờ khóa ở request khác.
    existing = frappe.db.sql_list(f"""SELECT name FROM `tabDelivery Note`
        WHERE {F_ORDER}=%s AND {F_BATCH}=%s ORDER BY name FOR UPDATE""", (doc.name, request_id))
    if existing:
        notes = [frappe.get_doc("Delivery Note", name, for_update=True) for name in existing]
        if any(n.get(F_HASH) != signature for n in notes):
            frappe.throw("Đợt này đã lập phiếu với nội dung khác; mở lại để lập đợt mới")
        return {"delivery_notes": _summaries(notes), "reused": True}
    if not frappe.has_permission("Delivery Note", "create"):
        frappe.throw("Bạn chưa có quyền lập phiếu giao nháp", frappe.PermissionError)
    try:
        selected = plan(_rows(doc, lock=True), choices)
    except ValueError as exc:
        frappe.throw(str(exc))
    groups = {}
    for row in selected:
        groups.setdefault((row["source_order"], row["warehouse"]), []).append(row)
    from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
    notes = []
    for (source, _warehouse), rows in sorted(groups.items()):
        wanted = {r["source_row"]: r for r in rows}
        dn = make_delivery_note(source, kwargs={"filtered_children": list(wanted)})
        if {r.so_detail for r in dn.items} != set(wanted):
            frappe.throw("Nguồn đã thay đổi; tải lại lượng còn giao")
        for row in dn.items:
            choice = wanted[row.so_detail]
            row.qty = choice["qty"]
            row.kh_aph_bags = choice["bags"]
            row.kh_aph_kg_per_bag = choice["kg_per_bag"]
        delivery_info.apply(dn, info)
        dn.set(F_ORDER, doc.name)
        dn.set(F_BATCH, request_id)
        dn.set(F_HASH, signature)
        dn.insert()  # Quyền chuẩn, validation chuẩn, không ignore_permissions / submit / commit.
        notes.append(dn)
    return {"delivery_notes": _summaries(notes), "reused": False}


@frappe.whitelist()
def print_batch(shared_order, request_id):
    """In một đợt đã lập; không tăng số lượng, không xác nhận xuất, không trả giá."""
    _guard()
    doc = _order(shared_order)
    names = frappe.get_all("Delivery Note", {F_ORDER: doc.name, F_BATCH: request_id}, pluck="name", order_by="name")
    if not names:
        frappe.throw("Đợt chưa có phiếu xuất")
    notes = []
    for name in names:
        dn = frappe.get_doc("Delivery Note", name)
        _note_scope(dn)
        dn.check_permission("print")
        if dn.docstatus == 2:
            frappe.throw("Đợt có phiếu đã hủy; không in làm căn cứ xuất hàng")
        notes.append({"name": dn.name, "company": dn.company, "posting_date": dn.posting_date,
                      "customer_name": dn.customer_name, "docstatus": dn.docstatus,
                      "delivery_method": dn.get(delivery_info.METHOD), "recipient": dn.get(delivery_info.RECIPIENT),
                      "phone": dn.get(delivery_info.PHONE), "dispatcher": dn.get(delivery_info.DISPATCHER),
                      "driver_name": dn.get("driver_name"), "vehicle_no": dn.get("vehicle_no"),
                      "address": frappe.utils.strip_html(dn.get("shipping_address") or ""),
                      "created_by": frappe.utils.get_fullname(dn.owner),
                      "items": [{"item_code": r.item_code, "item_name": r.item_name, "warehouse": r.warehouse,
                                 "qty": r.qty, "bags": r.get("kh_aph_bags"),
                                 "kg_per_bag": r.get("kh_aph_kg_per_bag")} for r in dn.items]})
    return {"html": frappe.render_template("templates/ban_nhanh/phieu_dot_xuat.html",
                                           {"shared_order": doc.name, "notes": notes})}
