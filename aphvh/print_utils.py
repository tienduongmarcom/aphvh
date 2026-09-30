"""Hàm dùng trong mẫu in (khai báo ở hooks.jinja). Tên hàm có tiền tố aphvh_ để không trùng."""

import html
import re

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
    """Tên, địa chỉ, mã số thuế đơn vị cho đầu mẫu in."""
    name = frappe.get_cached_value("Company", company, "company_name") or company
    mst = frappe.get_cached_value("Company", company, "tax_id") or ""
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
    return {"ten": name, "dia_chi": address, "mst": mst}


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


def aphvh_sl_don_ban(row) -> float | None:
    """Số lượng trên đơn bán hàng của dòng phiếu giao hàng; None nếu dòng không lấy từ đơn."""
    if not row.get("so_detail"):
        return None
    return frappe.db.get_value("Sales Order Item", row.so_detail, "qty")


def aphvh_dia_chi(text) -> str:
    """Địa chỉ dạng HTML nhiều dòng (address_display) thành một dòng để in."""
    return mot_dong(text)


def mot_dong(text) -> str:
    """Bỏ thẻ HTML, gộp các dòng bằng dấu phẩy; kết quả đã escape để in thẳng vào HTML."""
    if not text:
        return ""
    s = re.sub(r"<br\s*/?>|\n", ", ", str(text))
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    parts = [p.strip() for p in s.split(",")]
    return html.escape(", ".join(p for p in parts if p), quote=False)


def aphvh_lo(row) -> str:
    """Số lô của dòng phiếu (ô lô trên dòng, hoặc các lô trong gói serial/lô)."""
    if row.get("batch_no"):
        return row.batch_no
    bundle = row.get("serial_and_batch_bundle")
    if not bundle:
        return ""
    lots = frappe.get_all("Serial and Batch Entry", filters={"parent": bundle}, pluck="batch_no")
    return ", ".join(sorted({x for x in lots if x}))


def aphvh_gia_gom_thue(doc) -> dict:
    """Biên bản giao nhận: đơn giá, thành tiền đã gồm thuế GTGT từng dòng (thuế lấy theo từng dòng hàng)."""
    from collections import defaultdict

    from aphvh.sales_rules import gia_gom_thue

    items = doc.get("items") or []
    tax_row = defaultdict(float)
    for d in doc.get("item_wise_tax_details") or []:
        tax_row[d.get("item_row")] += flt(d.get("amount"))
    total_tax = abs(flt(doc.get("base_total_taxes_and_charges")))
    if total_tax and not tax_row:
        # Không có thuế theo dòng: chia tổng thuế theo tiền hàng.
        net = sum(abs(flt(r.get("base_net_amount"))) for r in items) or 1
        for r in items:
            tax_row[r.get("name")] = total_tax * abs(flt(r.get("base_net_amount"))) / net
    total = abs(flt(doc.get("base_rounded_total")) or flt(doc.get("base_grand_total")))
    lines = [(r.get("qty"), r.get("base_net_amount"), tax_row.get(r.get("name"), 0)) for r in items]
    return {"dong": gia_gom_thue(lines, total), "tong": total, "co_thue": bool(total_tax)}
