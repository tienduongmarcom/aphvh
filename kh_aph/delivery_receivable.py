"""Opt-in accounting at dispatch; no external MISA operation or historical backfill."""

import frappe
from frappe.utils import cint, flt

FLAG = "kh_aph_post_receivable_on_delivery"


def enabled():
    return bool(cint(frappe.conf.get(FLAG)))


def post_receivable(doc):
    from kh_aph.constants import SI_AUTO
    from kh_aph.sales_flow import _build_invoice, _original_invoices

    if cint(doc.get("is_internal_customer")):
        return
    if not frappe.get_meta("Sales Invoice").has_field(SI_AUTO):
        frappe.throw("Thiếu cấu hình đánh dấu chứng từ bán hàng tự tạo; chưa được xuất hàng.")

    # Serialise concurrent/repeated hook calls for this DN. The caller owns the transaction.
    frappe.db.sql("SELECT name FROM `tabDelivery Note` WHERE name=%s FOR UPDATE", doc.name)
    parents = frappe.get_all("Sales Invoice Item", filters={"delivery_note": doc.name}, pluck="parent")
    linked = [frappe.get_doc("Sales Invoice", n) for n in sorted(set(parents))]
    active = [si for si in linked if cint(si.docstatus) != 2]
    if active:
        if len(active) == 1 and cint(active[0].docstatus) == 1 and cint(active[0].get(SI_AUTO)):
            # Do not accept an unrelated/partial invoice as an idempotent retry.
            si = active[0]
            if all(r.delivery_note == doc.name for r in si.items) and abs(flt(si.grand_total) - flt(doc.grand_total)) < 0.01:
                return
        frappe.throw("Phiếu giao đã có chứng từ bán hàng: cần đối soát, không tự lập thêm hoặc tự xác nhận nháp cũ.")

    if not cint(doc.is_return):
        if flt(doc.per_billed) >= 100:
            return  # Already invoiced before dispatch; do not book the debt twice.
        if flt(doc.per_billed) > 0 or any(r.get("against_sales_invoice") for r in doc.items):
            frappe.throw("Phiếu giao có phần đã lập hóa đơn: cần đối soát trước khi xuất để không ghi công nợ trùng.")
        original = None
    else:
        originals = _original_invoices(doc)
        if len(originals) != 1:
            frappe.throw("Phiếu trả lại phải xác định duy nhất chứng từ bán hàng gốc đã xác nhận.")
        original = originals[0]

    si = _build_invoice(doc, original)
    si.update_stock = 0  # DN already posted stock. SI only posts receivable/revenue/tax.
    si.submit()
    if cint(si.docstatus) != 1:
        frappe.throw("Chưa ghi nhận được công nợ; không được hoàn tất xuất hàng.")
    # No catch/savepoint recovery: failures must abort the caller's dispatch transaction.

