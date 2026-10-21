"""Lập phiếu nhận trả nháp từ phiếu gốc, kể cả sau khi khách đã nhận. Không tự thu/chi."""
import hashlib
import json
import re

import frappe
from frappe.utils import cint, flt
from kh_aph.return_quantity import LOOSE, loose_return

REQUEST = "kh_aph_ma_nhan_tra"
SIGNATURE = "kh_aph_dau_nhan_tra"
REASON = "kh_aph_ly_do_nhan_tra"


def enabled():
    return bool(cint(frappe.conf.get("kh_aph_sales_adjust")) and cint(frappe.conf.get("kh_aph_sales_p1")))


def fields():
    return {
        "Delivery Note": [
            {"fieldname": REQUEST, "label": "Mã yêu cầu nhận trả", "fieldtype": "Data", "unique": 1,
             "read_only": 1, "no_copy": 1, "hidden": 1},
            {"fieldname": SIGNATURE, "label": "Dấu nội dung nhận trả", "fieldtype": "Data",
             "read_only": 1, "no_copy": 1, "hidden": 1},
            {"fieldname": REASON, "label": "Lý do nhận trả", "fieldtype": "Small Text",
             "depends_on": "eval:doc.is_return", "no_copy": 1, "insert_after": "return_against"}],
        "Delivery Note Item": [
            {"fieldname": LOOSE, "label": "Trả lẻ theo kg", "fieldtype": "Check", "default": "0",
             "no_copy": 1, "insert_after": "kh_aph_bags",
             "description": "Hàng trả một phần bao: kg thực nhận và số bao vật lý độc lập. Chỉ dùng phiếu trả theo dòng gốc."}],
    }


def _guard():
    if not enabled():
        frappe.throw("Chưa bật nghiệp vụ nhận hàng trả lại")


def _source(name, lock=False):
    if lock:
        frappe.db.sql("SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE", name)
    dn = frappe.get_doc("Delivery Note", name, for_update=lock)
    dn.check_permission("read")
    frappe.get_doc("Company", dn.company).check_permission("read")
    frappe.get_doc("Customer", dn.customer).check_permission("read")
    if cint(dn.docstatus) != 1 or cint(dn.is_return):
        frappe.throw("Chọn phiếu xuất gốc đã ghi sổ")
    return dn


def _reserved(dn, exclude=None, lock=True):
    # Đã kiểm phạm vi phiếu gốc; tổng mọi user để không cho hai người lập cùng lượng.
    rows = frappe.db.sql("""SELECT r.dn_detail, r.qty, r.kh_aph_bags AS bags
        FROM `tabDelivery Note Item` r JOIN `tabDelivery Note` p ON p.name=r.parent
        WHERE p.is_return=1 AND p.return_against=%s AND p.docstatus<2
        AND p.name!=%s ORDER BY p.name, r.idx""" + (" FOR UPDATE" if lock else ""), (dn.name, exclude or ""), as_dict=True)
    totals = {}
    for row in rows:
        value = totals.setdefault(row.dn_detail, frappe._dict(dn_detail=row.dn_detail, qty=0, bags=0))
        value.qty += abs(flt(row.qty))
        value.bags += abs(flt(row.bags))
    return list(totals.values())


@frappe.whitelist()
def preview(delivery_note):
    _guard()
    if not frappe.has_permission("Delivery Note", "create"):
        frappe.throw("Cần quyền lập phiếu nhận trả", frappe.PermissionError)
    dn = _source(delivery_note)
    reserved = {r.dn_detail: r for r in _reserved(dn, lock=False)}
    rows = []
    for d in dn.items:
        frappe.get_doc("Warehouse", d.warehouse).check_permission("read")
        used = reserved.get(d.name) or {}
        rows.append({"source_row": d.name, "item_code": d.item_code, "item_name": d.item_name,
                     "uom": d.uom, "warehouse": d.warehouse, "delivered_qty": flt(d.qty),
                     "remaining_qty": max(0, flt(d.qty) - flt(used.get("qty"))),
                     "remaining_bags": max(0, flt(d.get("kh_aph_bags")) - flt(used.get("bags"))),
                     "kg_per_bag": flt(d.get("kh_aph_kg_per_bag"))})
    return {"name": dn.name, "customer": dn.customer, "company": dn.company, "rows": rows}


@frappe.whitelist(methods=["POST"])
def create_draft(delivery_note, selections, request_id, reason, condition, settlement):
    _guard()
    from lab9x.ban_hang import HANG_TRA_VE, XU_LY_TIEN
    from kh_aph.sales_p1 import F_HANG, F_TIEN
    from kh_aph.sales_adjust_rules import DC_TRA_HANG
    if not re.fullmatch(r"[a-zA-Z0-9-]{16,64}", request_id or ""):
        frappe.throw("Mã yêu cầu không hợp lệ; mở lại thao tác nhận trả")
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 1000:
        frappe.throw("Ghi lý do nhận trả, tối đa 1000 ký tự")
    if condition not in HANG_TRA_VE or settlement not in XU_LY_TIEN:
        frappe.throw("Chọn tình trạng hàng và cách xử lý tiền")
    choices = frappe.parse_json(selections) if isinstance(selections, str) else selections
    if not isinstance(choices, list) or not choices or any(not isinstance(r, dict) for r in choices):
        frappe.throw("Chọn dòng và lượng thực nhận trả")
    try:
        canonical = sorted([{"source_row": r["source_row"], "qty": str(r["qty"]),
                             "bags": str(r.get("bags", 0))} for r in choices], key=lambda r: r["source_row"])
    except (KeyError, TypeError):
        frappe.throw("Dữ liệu nhận trả không hợp lệ")
    signature = hashlib.sha256(json.dumps({"rows": canonical, "reason": reason.strip(),
        "condition": condition, "settlement": settlement}, sort_keys=True).encode()).hexdigest()
    dn = _source(delivery_note, lock=True)
    matches = frappe.db.sql(f"SELECT name, {SIGNATURE}, return_against, docstatus FROM `tabDelivery Note` WHERE {REQUEST}=%s FOR UPDATE",
                            request_id, as_dict=True)
    found = matches[0] if matches else None
    if found:
        existing = frappe.get_doc("Delivery Note", found.name)
        existing.check_permission("read")
        if found.return_against != dn.name or found.get(SIGNATURE) != signature or cint(found.docstatus) == 2:
            frappe.throw("Yêu cầu đã dùng cho nội dung khác hoặc phiếu đã hủy; mở lại thao tác")
        return {"name": found.name, "reused": True}
    if not frappe.has_permission("Delivery Note", "create"):
        frappe.throw("Cần quyền lập phiếu nhận trả", frappe.PermissionError)
    sources = {r.name: r for r in dn.items}
    seen, planned = set(), {}
    reserved = {r.dn_detail: r for r in _reserved(dn)}
    for choice in canonical:
        key = choice["source_row"]
        if key in seen or key not in sources:
            frappe.throw("Dòng nhận trả bị trùng hoặc không thuộc phiếu gốc")
        seen.add(key)
        source = sources[key]
        if source.uom != "Kg" or flt(source.conversion_factor) != 1:
            frappe.throw("Thao tác trả lẻ hiện dùng cho hàng có đơn vị Kg")
        used = reserved.get(key) or {}
        try:
            from kh_aph.quantity_rules import number
            q, b = number(choice["qty"]), number(choice["bags"])
            if q <= 0 or b < 0:
                raise ValueError("Nhập lượng nhận trả dương và số bao không âm")
            weight = flt(source.get("kh_aph_kg_per_bag"))
            remaining = flt(flt(source.qty) - flt(used.get("qty")), 6)
            if weight:
                result = loose_return(-q, -b, weight, remaining,
                    flt(source.get("kh_aph_bags")) - flt(used.get("bags")))
                result["loose"] = 1
            else:
                if b or q > number(remaining):
                    raise ValueError("Hàng không quản lý bao: số bao bằng0 và kg không vượt lượng còn được trả")
                result = {"qty": -q, "bags": 0, "kg_per_bag": 0, "loose": 0}
        except ValueError as exc:
            frappe.throw(str(exc))
        frappe.get_doc("Warehouse", source.warehouse).check_permission("read")
        planned[key] = result
    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_return
    ret = make_sales_return(dn.name)
    ret.items = [r for r in ret.items if r.get("dn_detail") in planned]
    if len(ret.items) != len(planned):
        frappe.throw("Không đối chiếu được dòng phiếu trả với phiếu gốc")
    for r in ret.items:
        p = planned[r.dn_detail]
        r.qty, r.kh_aph_bags, r.kh_aph_kg_per_bag = map(float, (p["qty"], p["bags"], p["kg_per_bag"]))
        r.set(LOOSE, p["loose"])
    ret.set("kh_aph_loai_dieu_chinh", DC_TRA_HANG)
    ret.set(F_HANG, condition)
    ret.set(F_TIEN, settlement)
    ret.set(REQUEST, request_id)
    ret.set(SIGNATURE, signature)
    ret.set(REASON, reason.strip())
    ret.insert()  # Nháp; không tự nhập kho, giảm nợ hoặc chi tiền.
    return {"name": ret.name, "reused": False}


def validate(doc, method=None):
    """Khóa nguồn khi mọi đường native lưu/ghi phiếu trả, không chỉ cửa sổ mới."""
    if not enabled():
        return
    if not doc.get(REQUEST) and not any(cint(r.get(LOOSE)) for r in doc.get("items") or []):
        return
    if doc.doctype != "Delivery Note" or not cint(doc.is_return) or not doc.get("return_against"):
        frappe.throw("Trả lẻ kg chỉ dùng trên phiếu nhận trả theo phiếu xuất gốc")
    dn = _source(doc.return_against, lock=True)
    if dn.company != doc.company or dn.customer != doc.customer:
        frappe.throw("Phiếu nhận trả phải cùng khách và đơn vị với phiếu gốc")
    original = {r.name: r for r in dn.items}
    reserved = {r.dn_detail: r for r in _reserved(dn, exclude=doc.name)}
    seen = set()
    for r in doc.items:
        key = r.get("dn_detail")
        if key in seen or key not in original:
            frappe.throw("Phiếu trả có dòng trùng hoặc không thuộc phiếu gốc")
        seen.add(key)
        source, used = original[key], reserved.get(key) or {}
        if r.item_code != source.item_code or r.uom != source.uom or flt(r.conversion_factor) != flt(source.conversion_factor):
            frappe.throw("Mã hàng và đơn vị trả phải khớp dòng giao gốc")
        if flt(r.qty) >= 0 or abs(flt(r.qty)) + flt(used.get("qty")) > flt(source.qty) + 0.000001:
            frappe.throw("Lượng trả và chờ nhận trả vượt lượng đã giao")
        if abs(flt(r.get("kh_aph_bags"))) + flt(used.get("bags")) > flt(source.get("kh_aph_bags")) + 0.000001:
            frappe.throw("Số bao nhận trả vượt số bao đã giao")
