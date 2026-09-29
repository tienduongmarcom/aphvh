"""Hàm dùng trong mẫu in (khai báo ở hooks.jinja). Tên hàm có tiền tố aphvh_ để không trùng."""

import frappe
from frappe.utils import cint, flt, getdate

from aphvh.constants import PR_OPEX
from aphvh.price_visibility import is_price_restricted
from aphvh.vn_words import so_tien_bang_chu, so_vn


def aphvh_an_gia(doc) -> bool:
    """True nếu bản in phải ẩn đơn giá, thành tiền với người đang in."""
    if not is_price_restricted():
        return False
    if doc.doctype == "Purchase Receipt" and cint(doc.get(PR_OPEX)):
        return False
    return True


def _account_number(account: str) -> str:
    number = frappe.get_cached_value("Account", account, "account_number")
    if number:
        return number
    return (account or "").split(" - ")[0]


def aphvh_no_co(doc) -> dict:
    """Tài khoản Nợ / Có của chứng từ theo sổ cái (chỉ phiếu đã gửi)."""
    if cint(doc.docstatus) != 1:
        return {"no": "", "co": ""}
    rows = frappe.get_all(
        "GL Entry",
        filters={"voucher_type": doc.doctype, "voucher_no": doc.name, "is_cancelled": 0},
        fields=["account", "debit", "credit"],
        order_by="creation asc",
    )
    no, co = [], []
    for r in rows:
        acc = _account_number(r.account)
        if flt(r.debit) and acc not in no:
            no.append(acc)
        if flt(r.credit) and acc not in co:
            co.append(acc)
    return {"no": ", ".join(no), "co": ", ".join(co)}


def aphvh_ngay(date) -> str:
    if not date:
        return "Ngày ... tháng ... năm ..."
    d = getdate(date)
    return f"Ngày {d.day:02d} tháng {d.month:02d} năm {d.year}"


def aphvh_so(value, precision: int = 3) -> str:
    """Định dạng số kiểu Việt Nam: 1.234.567,5."""
    return so_vn(value, precision)


def aphvh_bang_chu(amount) -> str:
    return so_tien_bang_chu(amount)


def aphvh_cong_ty(company: str) -> dict:
    """Tên và địa chỉ đơn vị cho đầu mẫu in."""
    name = frappe.get_cached_value("Company", company, "company_name") or company
    address = ""
    link = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Company", "link_name": company, "parenttype": "Address"},
        pluck="parent",
        limit=1,
    )
    if link:
        a = frappe.db.get_value("Address", link[0], ["address_line1", "address_line2", "city"], as_dict=True)
        if a:
            address = ", ".join(x for x in (a.address_line1, a.address_line2, a.city) if x)
    return {"ten": name, "dia_chi": address}


def aphvh_ten_nguoi(user: str) -> str:
    if not user:
        return ""
    return frappe.utils.get_fullname(user)


def aphvh_sl_chung_tu(row) -> float | None:
    """Số lượng theo chứng từ (đơn mua) của dòng phiếu nhập; None nếu không lấy từ đơn."""
    if not row.get("purchase_order_item"):
        return None
    return frappe.db.get_value("Purchase Order Item", row.purchase_order_item, "qty")


def aphvh_ten_kho(warehouse: str) -> str:
    """Tên kho bỏ đuôi viết tắt công ty (' - APH')."""
    if not warehouse:
        return ""
    return frappe.get_cached_value("Warehouse", warehouse, "warehouse_name") or warehouse
