"""Kiểm soát 0.3.4 (móc vào doc_events trong hooks.py). Quy tắc thuần ở control_rules.py.

- Journal Entry: chặn ghi tay vào tài khoản loại Kho (K21).
- Item: chặn đổi nhóm hàng khi mã đã có giao dịch kho (I01) — tài khoản kho đi theo nhóm hàng.
- Chứng từ có ngày ghi sổ: chặn ngày tương lai, trừ kế toán trưởng (H05).
- Payment Entry / Purchase Invoice đã trả: cảnh báo tiền mặt từ 20 triệu (J16).
- Payment Entry thu trước không gắn đơn khi khách đang nợ quá hạn: cảnh báo (J24).
- Sales Invoice của khách vãng lai chung: bắt thu tiền ngay, tự lập phiếu thu khi xác nhận (J28).
"""

import frappe
from frappe.utils import flt, getdate, nowdate

from aphvh import control_rules as R

F_WALK_IN = "aphvh_khach_chung"  # Customer
F_PAY_NOW = "aphvh_thu_ngay_tk"  # Sales Invoice: tài khoản tiền thu ngay


def _account_type(acc: str) -> str:
    return frappe.get_cached_value("Account", acc, "account_type") or ""


def validate_journal_entry(doc, method=None):
    if doc.get("is_system_generated") or doc.flags.get("aphvh_allow_stock_account"):
        return
    bad = R.stock_account_rows(doc.get("accounts"), _account_type)
    if bad:
        frappe.throw(R.stock_account_message(bad), title="Không ghi tay vào tài khoản kho")


def validate_item(doc, method=None):
    if doc.is_new() or not doc.has_value_changed("item_group"):
        return
    if frappe.db.exists("Stock Ledger Entry", {"item_code": doc.name, "is_cancelled": 0}):
        old = doc.get_doc_before_save().item_group if doc.get_doc_before_save() else ""
        frappe.throw(
            f"Mã {frappe.bold(doc.name)} đã có giao dịch kho nên không đổi nhóm hàng ({old} → {doc.item_group}). "
            "Tài khoản kho lấy theo nhóm hàng: đổi nhóm sẽ làm số dư nằm ở tài khoản cũ. "
            "Muốn đổi: tạo mã mới ở nhóm đúng và chuyển tồn bằng Phiếu kho (đổi mã).",
            title="Không đổi nhóm hàng",
        )


def validate_posting_date(doc, method=None):
    if doc.doctype not in R.POSTING_DATE_DOCTYPES:
        return
    if R.is_future(getdate(doc.get("posting_date")), getdate(nowdate())) and not R.can_override(frappe.get_roles()):
        frappe.throw(
            f"Ngày ghi sổ {frappe.format(doc.posting_date, {'fieldtype': 'Date'})} là ngày tương lai. "
            "Kiểm tra lại ngày; nếu thật sự cần, nhờ kế toán trưởng lập.",
            title="Ngày chứng từ chưa tới",
        )


def _set_don_tong(doc):
    """Phiếu thu gắn với đơn bán / hóa đơn thuộc một Đơn tổng thì ghi số đơn tổng (để xem trên đơn tổng)."""
    if not doc.meta.has_field("aphvh_don_tong") or doc.get("aphvh_don_tong"):
        return
    for r in doc.get("references") or []:
        if r.reference_doctype in ("Sales Order", "Sales Invoice") and r.reference_name:
            dt = frappe.db.get_value(r.reference_doctype, r.reference_name, "aphvh_don_tong")
            if dt:
                doc.aphvh_don_tong = dt
                return


def validate_payment_entry(doc, method=None):
    validate_posting_date(doc)
    _set_don_tong(doc)
    cash_acc = doc.paid_to if doc.payment_type == "Receive" else doc.paid_from
    if cash_acc and _account_type(cash_acc) == "Cash":
        msg = R.cash_warning(doc.paid_amount)
        if msg:
            frappe.msgprint(msg, title="Tiền mặt lớn", indicator="orange")
    if doc.payment_type == "Receive" and doc.party_type == "Customer" and doc.party:
        overdue = frappe.db.sql(
            """select ifnull(sum(outstanding_amount),0) from `tabSales Invoice`
               where customer=%s and company=%s and docstatus=1 and outstanding_amount>0 and due_date<%s""",
            (doc.party, doc.company, doc.posting_date),
        )[0][0]
        msg = R.deposit_warning(bool(doc.get("references")), overdue)
        if msg:
            frappe.msgprint(msg, title="Tiền trả trước chưa gắn đơn", indicator="orange")


def validate_purchase_invoice(doc, method=None):
    validate_posting_date(doc)
    if doc.get("is_paid") and doc.get("cash_bank_account") and _account_type(doc.cash_bank_account) == "Cash":
        msg = R.cash_warning(doc.get("paid_amount") or doc.get("grand_total"))
        if msg:
            frappe.msgprint(msg, title="Tiền mặt lớn", indicator="orange")


def validate_sales_invoice(doc, method=None):
    validate_posting_date(doc)
    walk_in = bool(frappe.get_cached_value("Customer", doc.customer, F_WALK_IN)) if doc.customer else False
    if doc.get("_action") == "submit" or doc.docstatus == 1:
        msg = R.walk_in_problem(walk_in, doc.get(F_PAY_NOW), bool(doc.get("is_return")))
        if msg:
            frappe.throw(msg, title="Khách vãng lai chung")
    if doc.get(F_PAY_NOW):
        t = _account_type(doc.get(F_PAY_NOW))
        if t not in ("Cash", "Bank"):
            frappe.throw("Ô 'Thu tiền ngay vào tài khoản' phải là tài khoản tiền mặt hoặc ngân hàng.")


def sales_invoice_on_submit(doc, method=None):
    """Thu tiền ngay: tự lập và xác nhận phiếu thu cho toàn bộ số còn nợ."""
    acc = doc.get(F_PAY_NOW)
    if not acc or doc.get("is_return") or flt(doc.outstanding_amount) <= 0:
        return
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

    pe = get_payment_entry("Sales Invoice", doc.name, bank_account=acc)
    pe.posting_date = doc.posting_date
    if _account_type(acc) == "Bank":
        pe.reference_no = doc.name
        pe.reference_date = doc.posting_date
    pe.remarks = f"Thu tiền ngay theo hóa đơn {doc.name}"
    pe.insert()
    pe.submit()
    frappe.msgprint(f"Đã lập phiếu thu {frappe.bold(pe.name)} cho hóa đơn này.", indicator="green", alert=True)
