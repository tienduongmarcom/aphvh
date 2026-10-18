"""Một mã giao dịch trên một quỹ/ngân hàng chỉ thuộc một chứng từ tiền đang hiệu lực."""
import frappe
from frappe.utils import cint


def check(account, reference, exclude=None):
    from kh_aph.tien_vay import ma_da_ghi
    frappe.db.sql("SELECT name FROM `tabAccount` WHERE name=%s FOR UPDATE", account)
    if ma_da_ghi(account, reference, bo_qua=exclude, lock=True):
        frappe.throw("Mã giao dịch đã được dùng trên quỹ/ngân hàng này; kiểm chứng từ cũ trước khi ghi thêm")


def validate(doc, method=None):
    if not (cint(frappe.conf.get("kh_aph_tien_vay")) or cint(frappe.conf.get("kh_aph_funds_workflow"))):
        return
    if frappe.flags.get("funds_internal"):
        # Phiếu tiền/cọc đã khóa và kiểm mã trước khi tạo JE của chính nó.
        return
    reference = (doc.get("reference_no") if doc.doctype == "Payment Entry" else doc.get("cheque_no")) or ""
    reference = reference.strip()
    if not reference or cint(doc.docstatus) == 2:
        return
    doc.set("reference_no" if doc.doctype == "Payment Entry" else "cheque_no", reference)
    names = ({doc.get("paid_from"), doc.get("paid_to")} if doc.doctype == "Payment Entry"
             else {d.account for d in doc.get("accounts") or []}) - {None, ""}
    banks = frappe.get_all("Account", filters={"name": ["in", list(names)], "account_type": ["in", ["Cash", "Bank"]]}, pluck="name") if names else []
    for account in sorted(banks):
        check(account, reference, doc.name)
