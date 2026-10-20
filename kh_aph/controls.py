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

from lab9x import control_rules as R
from kh_aph.constants import INV_FLAG, INV_YES

F_WALK_IN = "kh_aph_khach_chung"  # Customer
F_PAY_NOW = "kh_aph_thu_ngay_tk"  # Sales Invoice: tài khoản tiền thu ngay


def _account_type(acc: str) -> str:
    return frappe.get_cached_value("Account", acc, "account_type") or ""


def validate_journal_entry(doc, method=None):
    if doc.get("is_system_generated") or doc.flags.get("kh_aph_allow_stock_account"):
        return
    bad = R.stock_account_rows(doc.get("accounts"), _account_type)
    if bad:
        frappe.throw(R.stock_account_message(bad), title="Không ghi tay vào tài khoản kho")


def validate_posting_date(doc, method=None):
    if doc.doctype not in R.POSTING_DATE_DOCTYPES:
        return
    if R.is_future(getdate(doc.get("posting_date")), getdate(nowdate())) and not R.can_override(frappe.get_roles()):
        frappe.throw(
            f"Ngày ghi sổ {frappe.format(doc.posting_date, {'fieldtype': 'Date'})} là ngày tương lai. "
            "Kiểm tra lại ngày; nếu thật sự cần, nhờ kế toán trưởng lập.",
            title="Ngày chứng từ chưa tới",
        )


def _ben_thu_ba(doc, sau_xac_nhan=False):
    """0.4.11: thanh toán qua bên thứ ba — kiểm tra hồ sơ, đặt trạng thái rà soát, nhắc rủi ro thuế."""
    from lab9x import ben_thu_ba_rules as B
    from kh_aph.constants import PE_BTB, PE_BTB_CAN_CU, PE_BTB_FILE, PE_BTB_GIAY, PE_BTB_TEN, PE_BTB_TT, PE_PERSON

    if not doc.meta.has_field(PE_BTB):
        return
    cu = doc.get_doc_before_save().get(PE_BTB_TT) if doc.get_doc_before_save() else None
    if doc.get(PE_BTB_TT) == B.TT_DA_DUYET and cu != B.TT_DA_DUYET and "Accounts Manager" not in frappe.get_roles():
        frappe.throw("Chỉ Kế toán trưởng được chọn 'Kế toán trưởng đã duyệt'.")
    kq = B.kiem_tra(doc.get(PE_BTB), doc.get(PE_BTB_TEN), doc.get(PE_BTB_CAN_CU), bool(doc.get(PE_BTB_FILE)),
                    doc.get(PE_BTB_TT) if doc.get(PE_BTB_TT) == B.TT_DA_DUYET else cu)
    if kq["loi"]:
        frappe.throw("<br>".join(kq["loi"]), title="Thanh toán qua bên thứ ba")
    if not doc.get(PE_BTB):
        if doc.get(PE_BTB_TT):
            doc.set(PE_BTB_TT, None)
        return
    doc.set(PE_BTB_TT, kq["trang_thai"])
    if sau_xac_nhan:
        return
    if not doc.get(PE_PERSON):
        doc.set(PE_PERSON, doc.get(PE_BTB_TEN))
    if doc.party_type == "Customer" and doc.party:
        hd = [r.reference_name for r in doc.get("references") or [] if r.reference_doctype == "Sales Invoice"]
        co_hd = bool(hd) and bool(frappe.get_all("Sales Invoice", {"name": ["in", hd], INV_FLAG: INV_YES}, limit=1))
        msg = B.canh_bao_thue(True, doc.get(PE_BTB_GIAY), frappe.get_cached_value("Customer", doc.party, "tax_id"), co_hd)
        if msg:
            frappe.msgprint(msg, title="Thanh toán qua bên thứ ba", indicator="orange")
    if kq["trang_thai"] == B.TT_CAN_RA_SOAT:
        frappe.msgprint("Phiếu được ghi nhận nhưng ở trạng thái <b>Cần rà soát</b> (chưa có văn bản). "
                        "Đính kèm văn bản sau, hoặc Kế toán trưởng duyệt.", title="Thanh toán qua bên thứ ba", indicator="orange")


def before_update_after_submit_payment_entry(doc, method=None):
    _ben_thu_ba(doc, sau_xac_nhan=True)


def validate_payment_entry(doc, method=None):
    validate_posting_date(doc)
    _ben_thu_ba(doc)
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
    from kh_aph import cash_custody
    if cash_custody.enabled() and _account_type(acc) == "Cash":
        pe.set(cash_custody.HOLDER, doc.get(cash_custody.HOLDER))
    if _account_type(acc) == "Bank":
        pe.reference_no = doc.name
        pe.reference_date = doc.posting_date
    pe.remarks = f"Thu tiền ngay theo hóa đơn {doc.name}"
    pe.insert()
    pe.submit()
    frappe.msgprint(f"Đã lập phiếu thu {frappe.bold(pe.name)} cho hóa đơn này.", indicator="green", alert=True)
