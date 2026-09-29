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
