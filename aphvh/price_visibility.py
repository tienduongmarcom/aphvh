"""Ẩn giá với kế toán nhà máy (mức màn hình + báo cáo) và quy tắc phiếu nhập nguyên phụ liệu.

Mức bảo vệ đã chốt (29/09/2026): ẩn cột giá trên phiếu và bản in, không cho mở báo cáo có giá
trị, không có quyền xem dạng bảng/xuất Excel. Không phải khóa ở máy chủ: người rành kỹ thuật
vẫn đọc được giá qua API. Muốn khóa hẳn thì dùng che trường (mask) của Frappe v16 — xem README.

Quy tắc phiếu nhập mua hàng:
- Phiếu tích "Phiếu nhập vật tư vận hành": chỉ nhận mã thuộc nhóm hàng được tích
  "Nhà máy tự nhập giá"; kế toán nhà máy xem và nhập giá được.
- Phiếu còn lại, do người bị ẩn giá lập: mọi dòng phải lấy từ đơn mua (giá do kế toán trưởng
  đặt trên đơn; Buying Settings "Maintain same rate" = Stop giữ giá không đổi).
"""

import frappe
from frappe import _
from frappe.utils import cint

from aphvh.constants import IG_FACTORY_CAN_PRICE, PR_OPEX, PRICE_ROLES, ROLE_FACTORY


def is_price_restricted(user: str | None = None) -> bool:
    user = user or frappe.session.user
    if user == "Administrator":
        return False
    roles = set(frappe.get_roles(user))
    return ROLE_FACTORY in roles and not roles.intersection(PRICE_ROLES)


def factory_price_groups() -> list[str]:
    """Nhóm hàng (kể cả nhóm con) mà kế toán nhà máy được tự nhập giá."""
    if not frappe.db.has_column("Item Group", IG_FACTORY_CAN_PRICE):
        return []
    flagged = frappe.get_all("Item Group", filters={IG_FACTORY_CAN_PRICE: 1}, pluck="name")
    groups: set[str] = set()
    for name in flagged:
        groups.add(name)
        groups.update(frappe.db.get_descendants("Item Group", name) or [])
    return sorted(groups)


def boot_session(bootinfo):
    bootinfo.aphvh = {
        "price_restricted": is_price_restricted(),
        "factory_price_groups": factory_price_groups(),
    }


def _item_group(row) -> str | None:
    return row.get("item_group") or frappe.get_cached_value("Item", row.item_code, "item_group")


def validate_purchase_receipt(doc, method=None):
    if cint(doc.get("is_return")):
        return

    rows = doc.get("items") or []

    if cint(doc.get(PR_OPEX)):
        allowed = set(factory_price_groups())
        bad = [r for r in rows if _item_group(r) not in allowed]
        if bad:
            frappe.throw(
                _(
                    "Phiếu nhập vật tư vận hành chỉ nhận mã thuộc nhóm hàng được tích "
                    "'Nhà máy tự nhập giá'. Dòng không hợp lệ: {0}. Bỏ tích ô này nếu là nguyên phụ liệu."
                ).format(", ".join(f"#{r.idx} {r.item_code} ({_item_group(r)})" for r in bad)),
                title=_("Sai loại phiếu nhập"),
            )
        return

    if is_price_restricted():
        bad = [r for r in rows if not r.get("purchase_order_item")]
        if bad:
            frappe.throw(
                _(
                    "Nguyên phụ liệu phải nhận từ đơn mua do kế toán trưởng lập (nút Lấy hàng từ → "
                    "Đơn mua hàng). Dòng chưa gắn đơn mua: {0}. Nếu là vật tư vận hành thì tích "
                    "'Phiếu nhập vật tư vận hành' và lập phiếu riêng."
                ).format(", ".join(f"#{r.idx} {r.item_code}" for r in bad)),
                title=_("Thiếu đơn mua"),
            )


# Trường giá xóa trên bản in (chỉ trong bộ nhớ, không lưu) với người bị ẩn giá — áp dụng cho
# MỌI mẫu in kể cả mẫu Standard, vì Frappe gọi before_print trước khi dựng bản in.
_BUYING_PARENT = (
    "total", "net_total", "base_total", "base_net_total",
    "total_taxes_and_charges", "base_total_taxes_and_charges", "taxes_and_charges_added",
    "taxes_and_charges_deducted", "base_taxes_and_charges_added", "base_taxes_and_charges_deducted",
    "grand_total", "rounded_total", "base_grand_total", "base_rounded_total", "rounding_adjustment",
    "base_rounding_adjustment", "in_words", "base_in_words", "discount_amount", "base_discount_amount",
    "additional_discount_percentage", "advance_paid", "other_charges_calculation",
)
_BUYING_ITEM = (
    "price_list_rate", "base_price_list_rate", "margin_rate_or_amount", "rate_with_margin",
    "base_rate_with_margin", "discount_percentage", "discount_amount", "distributed_discount_amount",
    "rate", "amount", "base_rate", "base_amount", "stock_uom_rate", "net_rate", "net_amount",
    "base_net_rate", "base_net_amount", "valuation_rate", "landed_cost_voucher_amount",
    "amount_difference_with_purchase_invoice", "rate_difference_with_purchase_invoice", "item_tax_amount",
    "rm_supp_cost", "sales_incoming_rate", "billed_amt", "last_purchase_rate", "blanket_order_rate",
)
PRINT_MASK = {
    "Purchase Receipt": {"parent": _BUYING_PARENT, "tables": {"items": _BUYING_ITEM}, "clear": ("taxes",)},
    "Purchase Order": {
        "parent": _BUYING_PARENT,
        "tables": {"items": _BUYING_ITEM},
        "clear": ("taxes", "payment_schedule"),
    },
    "Stock Entry": {
        "parent": ("total_outgoing_value", "total_incoming_value", "value_difference",
                   "total_additional_costs", "total_amount"),
        "tables": {"items": ("basic_rate", "basic_amount", "additional_cost", "valuation_rate", "amount",
                             "customer_provided_item_cost", "landed_cost_voucher_amount")},
        "clear": ("additional_costs",),
    },
    "Serial and Batch Bundle": {
        "parent": ("avg_rate", "total_amount"),
        "tables": {"entries": ("incoming_rate", "outgoing_rate", "stock_value_difference")},
        "clear": (),
    },
    "Item": {"parent": ("standard_rate", "valuation_rate", "last_purchase_rate"), "tables": {}, "clear": ()},
}


def blank_prices_for_print(doc, method=None, *args, **kwargs):
    if not is_price_restricted():
        return
    if doc.doctype == "Purchase Receipt" and cint(doc.get(PR_OPEX)):
        return
    spec = PRINT_MASK.get(doc.doctype)
    if not spec:
        return
    for field in spec["parent"]:
        if doc.meta.has_field(field):
            doc.set(field, None)
    for table, fields in spec["tables"].items():
        for row in doc.get(table) or []:
            for field in fields:
                if row.meta.has_field(field):
                    row.set(field, None)
    for table in spec["clear"]:
        if doc.meta.has_field(table):
            doc.set(table, [])
