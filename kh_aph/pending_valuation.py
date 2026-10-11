"""Locked and idempotent conversion into a native valued Purchase Receipt."""
import frappe
from frappe.utils import flt, today, now_datetime
from kh_aph.quantity_rules import number
from kh_aph.bag_stock import enabled


@frappe.whitelist()
def finalize(name, rates, reason):
    if not enabled():
        frappe.throw("Chưa bật nhập chờ định giá")
    if frappe.session.user != "Administrator" and "Accounts Manager" not in frappe.get_roles():
        frappe.throw("Kế toán trưởng mới được chốt giá", frappe.PermissionError)
    from kh_aph.price_visibility import is_cost_restricted
    if is_cost_restricted():
        frappe.throw("Hồ sơ không xem giá vốn không được chốt giá nhập", frappe.PermissionError)
    doc = frappe.get_doc("APH Pending Receipt", name)
    doc.check_permission("write")
    frappe.db.sql("SELECT name FROM `tabAPH Pending Receipt` WHERE name=%s FOR UPDATE", name)
    doc.reload()
    if doc.docstatus != 1:
        frappe.throw("Cần xác nhận phiếu nhận hàng trước khi định giá")
    if doc.purchase_receipt:
        receipt = frappe.get_doc("Purchase Receipt", doc.purchase_receipt)
        receipt.check_permission("read")
        if receipt.docstatus != 1:
            frappe.throw("Phiếu nhập liên kết đã thay đổi; cần đối soát")
        return receipt.name
    rates = frappe.parse_json(rates)
    if not isinstance(rates, dict) or set(rates) != {r.name for r in doc.items} or not str(reason or "").strip():
        frappe.throw("Cần giá/kg cho đúng từng dòng và lý do chốt giá")
    co = frappe.get_doc("Company", doc.company)
    rows = []
    for row in doc.items:
        try:
            rate = number(rates[row.name])
            if rate <= 0:
                raise ValueError("Giá/kg phải lớn hơn 0; không nhập giá 0")
        except ValueError as exc:
            frappe.throw(str(exc))
        rows.append({"item_code": row.item_code, "warehouse": row.warehouse,
            "qty": row.qty, "rate": float(rate), "uom": "Kg", "conversion_factor": 1,
            "kh_aph_bags": row.kh_aph_bags, "kh_aph_kg_per_bag": row.kh_aph_kg_per_bag,
            "cost_center": co.cost_center})
    receipt = frappe.get_doc({"doctype": "Purchase Receipt", "company": doc.company,
        "supplier": doc.supplier, "posting_date": today(), "currency": "VND", "conversion_rate": 1,
        "kh_aph_pending_receipt": doc.name, "items": rows})
    frappe.flags.pending_internal_process = True
    try:
        receipt.insert()
        receipt.submit()
    finally:
        frappe.flags.pending_internal_process = False
    doc.db_set({"purchase_receipt": receipt.name, "status": "Đã định giá",
        "valued_by": frappe.session.user, "valued_at": now_datetime(), "valuation_reason": reason},
        update_modified=True)
    return receipt.name


def validate_link(doc, method=None):
    if enabled() and doc.get("kh_aph_pending_receipt") and not frappe.flags.pending_internal_process:
        frappe.throw("Phiếu chờ định giá phải được chốt qua thao tác định giá; không gán liên kết tay")
