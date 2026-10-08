"""Cảnh báo trên đơn bán hàng (0.3): công nợ vượt hạn mức, nợ quá hạn, giá thấp hơn bảng giá.

Chạy khi lưu và khi xác nhận đơn (validate). Chỉ hiện cảnh báo trên màn hình và đánh dấu đơn để
kế toán lọc; không bao giờ chặn. Bật/tắt từng loại trong Cài đặt bán hàng.

Hạn mức cảnh báo đặt ở bảng hạn mức tín dụng của khách (riêng từng khách) hoặc của nhóm khách,
theo từng công ty. Khách không đặt thì lấy nhóm của khách, rồi đến các nhóm cha.
"""

import frappe
from frappe.utils import cint, escape_html, flt
from frappe.utils.nestedset import get_ancestors_of

from kh_aph.constants import (
    CCL_WARN_LIMIT,
    SO_BELOW_PRICE,
    SO_OVER_LIMIT,
    SO_WARNING,
    SS_WARN_CREDIT,
    SS_WARN_PRICE,
)
from lab9x.sales_rules import credit_lines, pick_limit, price_lines
from lab9x.vn_words import so_vn


def setting_on(fieldname: str) -> bool:
    if not frappe.get_meta("Selling Settings").has_field(fieldname):
        return False
    return bool(cint(frappe.db.get_single_value("Selling Settings", fieldname)))


def _limit_of(parenttype: str, parent: str, company: str) -> float:
    return flt(
        frappe.db.get_value(
            "Customer Credit Limit",
            {"parenttype": parenttype, "parent": parent, "company": company},
            CCL_WARN_LIMIT,
        )
    )


def warning_limit(customer: str, company: str) -> tuple[float, str | None]:
    group = frappe.get_cached_value("Customer", customer, "customer_group")
    groups = []
    if group:
        groups = [group, *(get_ancestors_of("Customer Group", group) or [])]
    return pick_limit(
        _limit_of("Customer", customer, company),
        [(g, _limit_of("Customer Group", g, company)) for g in groups],
    )


def overdue_amount(customer: str, company: str) -> float:
    try:
        from erpnext.selling.doctype.customer.customer import get_customer_overdue_amount
    except ImportError:  # bản ERPNext cũ chưa có hàm này
        return 0.0
    return flt(get_customer_overdue_amount(customer, company))


def credit_check(doc) -> tuple[bool, list[str]]:
    from erpnext.selling.doctype.customer.customer import get_customer_outstanding

    limit, source = warning_limit(doc.customer, doc.company)
    outstanding = flt(get_customer_outstanding(doc.customer, doc.company)) if limit else 0.0
    # Lúc validate đơn này chưa ở trạng thái đã xác nhận trong CSDL nên chưa nằm trong số đang nợ.
    return credit_lines(limit, source, outstanding, flt(doc.base_grand_total), overdue_amount(doc.customer, doc.company))


def validate_sales_order(doc, method=None):
    if not doc.meta.has_field(SO_WARNING) or not doc.customer or not doc.company:
        return

    over, credit, price = False, [], []
    # Cảnh báo không bao giờ được chặn lưu đơn: lỗi khi tính thì ghi Nhật ký lỗi và bỏ qua.
    try:
        if setting_on(SS_WARN_CREDIT):
            over, credit = credit_check(doc)
        if setting_on(SS_WARN_PRICE):
            price = price_lines(doc.get("items"))
            if price and flt(doc.get("discount_amount")):
                price.append(f"Đơn có thêm chiết khấu tổng {so_vn(doc.discount_amount, 0)} đ.")
    except Exception:
        doc.log_error("kh_aph: lỗi khi tính cảnh báo đơn bán hàng")
        return

    doc.set(SO_OVER_LIMIT, 1 if over else 0)
    doc.set(SO_BELOW_PRICE, 1 if price else 0)
    doc.set(SO_WARNING, "\n".join(credit + price))

    if not (credit or price) or frappe.flags.in_import or frappe.flags.in_patch:
        return
    parts = []
    if credit:
        parts.append("<b>Công nợ</b><ul>" + "".join(f"<li>{escape_html(x)}</li>" for x in credit) + "</ul>")
    if price:
        parts.append("<b>Giá bán</b><ul>" + "".join(f"<li>{escape_html(x)}</li>" for x in price) + "</ul>")
    parts.append("Đơn vẫn được lưu và xác nhận bình thường; đơn được đánh dấu để kế toán xem lại.")
    frappe.msgprint("".join(parts), title="Cảnh báo", indicator="orange")
