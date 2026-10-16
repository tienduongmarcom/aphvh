"""Có / không xuất hóa đơn GTGT trên đơn bán hàng, phiếu giao hàng, hóa đơn bán hàng (0.3.1).

ERPNext ghi mọi lần bán thật; MISA chỉ ghi lần bán có hóa đơn để kê khai thuế.
- "Không": không tính thuế GTGT — bỏ dòng thuế và mẫu thuế mặt hàng, khách nợ đúng tiền hàng.
- "Có": tính thuế như chuẩn — mẫu thuế mặt hàng theo Loại thuế của khách (0.3.5, xem vat.py).
  Chứng từ trước đó để "Không" rồi đổi sang "Có" thì nạp lại mẫu thuế.
Chứng từ trống ô này thì lấy mặc định của khách; khách chưa đặt thì người lập phải chọn.
Bỏ qua với khách nội bộ và hóa đơn đầu kỳ.
"""

import frappe
from frappe.utils import cint, cstr

from kh_aph.constants import (
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
    chuyen_tiep = is_chuyen_tiep(doc.get("company"))
    if chuyen_tiep:
        doc.set(INV_FLAG, INV_NO)
    if not doc.get(INV_FLAG):
        doc.set(INV_FLAG, customer_default(doc.customer))
    flag = doc.get(INV_FLAG)
    if flag not in (INV_YES, INV_NO):
        frappe.throw(
            f"Chọn ô <b>Khách lấy hóa đơn</b> (Có / Không). Khách {frappe.bold(doc.customer)} chưa đặt mặc định; "
            "kế toán đặt mặc định trên hồ sơ khách để lần sau tự điền.",
            title="Thiếu Khách lấy hóa đơn",
        )

    if chuyen_tiep:
        changed = strip_taxes(doc)  # đơn vị chuyển tiếp: không VAT
    else:
        # 0.4.15: pháp nhân luôn tính VAT; khách không lấy hóa đơn -> đơn giá đã gồm VAT (tách ngược)
        changed = restore_taxes(doc)
        gom = flag == INV_NO
        for t in doc.get("taxes") or []:
            if t.get("charge_type") == "On Net Total" and cint(t.get("included_in_print_rate")) != int(gom):
                t.included_in_print_rate = int(gom)
                changed = True
        _nhac_doi_cach_tinh_gia(doc, flag)
    if changed:
        doc.calculate_taxes_and_totals()
    if not chuyen_tiep:
        check_tax_rates(doc)


def is_chuyen_tiep(company) -> bool:
    if not company or not frappe.get_meta("Company").has_field("kh_aph_noi_bo"):
        return False
    return bool(cint(frappe.get_cached_value("Company", company, "kh_aph_noi_bo")))


def _nhac_doi_cach_tinh_gia(doc, flag):
    """Đổi ô Khách lấy hóa đơn trên chứng từ đã có giá: ý nghĩa đơn giá đổi theo (chưa thuế <-> đã gồm VAT)."""
    cu = doc.get_doc_before_save()
    if not cu or not cu.get(INV_FLAG) or cu.get(INV_FLAG) == flag or not any(r.get("rate") for r in doc.get("items") or []):
        return
    y = "đã gồm VAT (giá báo khách)" if flag == INV_NO else "chưa thuế (VAT cộng thêm)"
    frappe.msgprint(f"Đã đổi Khách lấy hóa đơn sang <b>{flag}</b>: đơn giá trên chứng từ giờ được hiểu là giá {y}. "
                    "Kiểm tra lại đơn giá.", title="Kiểm tra đơn giá", indicator="orange")


def check_tax_rates(doc):
    """Bán có hóa đơn mà mặt hàng chưa có thuế suất (chưa có mẫu thuế mặt hàng): không tự coi là 0%.

    Lưu nháp thì cảnh báo; xác nhận thì chặn. Thuế suất từng mặt hàng do kế toán trưởng xác định.
    """
    from kh_aph.vat import _vat_account, missing_category_message

    if not _vat_account(doc.get("company")):
        return  # hộ kinh doanh (không có TK 33311): hóa đơn bán hàng, không tách thuế GTGT
    cat_msg = missing_category_message(doc)
    if cat_msg:
        if doc.get("_action") == "submit":
            frappe.throw(cat_msg, title="Khách chưa có Loại thuế")
        frappe.msgprint(cat_msg, title="Khách chưa có Loại thuế", indicator="orange")
    missing = [r for r in doc.get("items") or [] if r.get("item_code") and not r.get("item_tax_template")]
    if not missing:
        return
    rows = ", ".join(f"#{r.idx} {r.item_code}" for r in missing)
    msg = (
        f"Mặt hàng chưa có thuế suất GTGT: {rows}. Kế toán trưởng gán thuế suất cho mặt hàng (Mẫu thuế mặt hàng) "
        "trước khi bán (mọi đơn của APH, VH đều xuất hóa đơn trên MISA, kể cả khách không lấy hóa đơn)."
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
    if is_chuyen_tiep(doc.get("company")):
        frappe.throw("Đơn vị chuyển tiếp không phát hành hóa đơn nên không ghi ký hiệu, số, ngày hóa đơn điện tử.",
                     title="Không ghi số hóa đơn")
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
