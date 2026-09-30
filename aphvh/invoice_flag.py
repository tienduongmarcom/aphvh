"""Có / không xuất hóa đơn GTGT trên đơn bán hàng, phiếu giao hàng, hóa đơn bán hàng (0.3.1).

ERPNext ghi mọi lần bán thật; MISA chỉ ghi lần bán có hóa đơn để kê khai thuế.
- "Không": không tính thuế GTGT — bỏ dòng thuế và mẫu thuế mặt hàng, khách nợ đúng tiền hàng.
- "Có": tính thuế như chuẩn (mẫu thuế mặt hàng theo loại thuế của khách). Chứng từ trước đó để
  "Không" rồi đổi sang "Có" thì nạp lại mẫu thuế mặc định của công ty.
Chứng từ trống ô này thì lấy mặc định của khách; khách chưa đặt thì người lập phải chọn.
Bỏ qua với khách nội bộ và hóa đơn đầu kỳ.
"""

import frappe
from frappe.utils import cint, cstr

from aphvh.constants import (
    EINV_FIELDS,
    INV_FLAG,
    INV_NO,
    INV_YES,
    SI_EINV_DATE,
    SI_EINV_NO,
    SI_EINV_SERIES,
)


def _applies(doc) -> bool:
    if not doc.meta.has_field(INV_FLAG) or not doc.get("customer"):
        return False
    if cint(doc.get("is_internal_customer")) or doc.get("is_opening") == "Yes":
        return False
    return True


def customer_default(customer: str) -> str:
    return cstr(frappe.get_cached_value("Customer", customer, INV_FLAG)) if customer else ""


def strip_taxes(doc) -> bool:
    """Bỏ thuế GTGT khỏi chứng từ. Trả về True nếu có thay đổi."""
    changed = bool(doc.get("taxes")) or bool(doc.get("taxes_and_charges"))
    doc.set("taxes", [])
    if doc.meta.has_field("taxes_and_charges"):
        doc.taxes_and_charges = None
    for row in doc.get("items") or []:
        if row.get("item_tax_template") or (row.get("item_tax_rate") not in (None, "", "{}")):
            changed = True
        row.item_tax_template = None
        row.item_tax_rate = "{}"
    return changed


def restore_taxes(doc) -> bool:
    """Chứng từ "Có" mà chưa có dòng thuế: nạp mẫu thuế bán hàng (đã chọn, hoặc mặc định của công ty)."""
    if doc.get("taxes") or not doc.meta.has_field("taxes_and_charges"):
        return False
    master = doc.meta.get_field("taxes_and_charges").options
    if not doc.get("taxes_and_charges") and doc.get("company"):
        doc.taxes_and_charges = frappe.db.get_value(master, {"is_default": 1, "company": doc.company, "disabled": 0})
    if not doc.get("taxes_and_charges"):
        return False
    doc.append_taxes_from_master(master)
    return bool(doc.get("taxes"))


def apply_invoice_flag(doc, method=None):
    """validate của Sales Order, Delivery Note, Sales Invoice."""
    if not _applies(doc):
        return
    if not doc.get(INV_FLAG):
        doc.set(INV_FLAG, customer_default(doc.customer))
    flag = doc.get(INV_FLAG)
    if flag not in (INV_YES, INV_NO):
        frappe.throw(
            f"Chọn ô <b>Xuất hóa đơn GTGT</b> (Có / Không). Khách {frappe.bold(doc.customer)} chưa đặt mặc định; "
            "kế toán đặt mặc định trên hồ sơ khách để lần sau tự điền.",
            title="Thiếu Xuất hóa đơn GTGT",
        )

    changed = strip_taxes(doc) if flag == INV_NO else restore_taxes(doc)
    if changed:
        doc.calculate_taxes_and_totals()
    if flag == INV_YES:
        check_tax_rates(doc)


def check_tax_rates(doc):
    """Bán có hóa đơn mà mặt hàng chưa có thuế suất (chưa có mẫu thuế mặt hàng): không tự coi là 0%.

    Lưu nháp thì cảnh báo; xác nhận thì chặn. Thuế suất từng mặt hàng do kế toán trưởng xác định.
    """
    missing = [r for r in doc.get("items") or [] if r.get("item_code") and not r.get("item_tax_template")]
    if not missing:
        return
    rows = ", ".join(f"#{r.idx} {r.item_code}" for r in missing)
    msg = (
        f"Mặt hàng chưa có thuế suất GTGT: {rows}. Kế toán trưởng gán thuế suất cho mặt hàng (Mẫu thuế mặt hàng) "
        "trước khi bán có xuất hóa đơn; hoặc chọn Xuất hóa đơn GTGT = Không nếu lần bán này không xuất hóa đơn."
    )
    if doc.get("_action") == "submit":
        frappe.throw(msg, title="Chưa có thuế suất")
    frappe.msgprint(msg, title="Chưa có thuế suất", indicator="orange")


def validate_einvoice(doc, method=None):
    """Sales Invoice: validate và before_update_after_submit — số hóa đơn điện tử đã xuất trên MISA."""
    if not doc.meta.has_field(SI_EINV_NO):
        return
    for f in EINV_FIELDS:
        if isinstance(doc.get(f), str):
            doc.set(f, doc.get(f).strip() or None)
    if not any(doc.get(f) for f in EINV_FIELDS):
        return
    if doc.get(INV_FLAG) != INV_YES:
        frappe.throw(
            "Hóa đơn này để Xuất hóa đơn GTGT = Không nên không ghi ký hiệu, số, ngày hóa đơn điện tử. "
            "Nếu thực tế đã xuất hóa đơn thì hủy, sửa thành Có rồi xác nhận lại.",
            title="Không ghi số hóa đơn",
        )
    if not doc.get(SI_EINV_NO):
        return
    dup = frappe.get_all(
        "Sales Invoice",
        filters={
            "company": doc.company,
            SI_EINV_NO: doc.get(SI_EINV_NO),
            SI_EINV_SERIES: doc.get(SI_EINV_SERIES) or ["is", "not set"],
            "docstatus": ["<", 2],
            "name": ["!=", doc.name],
        },
        pluck="name",
        limit=3,
    )
    if dup:
        frappe.throw(
            f"Ký hiệu {frappe.bold(doc.get(SI_EINV_SERIES) or '(trống)')}, số {frappe.bold(doc.get(SI_EINV_NO))} "
            f"đã ghi trên hóa đơn {', '.join(dup)}.",
            title="Trùng số hóa đơn điện tử",
        )
    if doc.get(SI_EINV_DATE) is None and doc.docstatus == 1:
        frappe.msgprint("Nhớ ghi ngày hóa đơn điện tử.", indicator="orange", alert=True)
