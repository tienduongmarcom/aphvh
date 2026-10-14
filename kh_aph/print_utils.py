"""Hàm dùng trong mẫu in (khai báo ở hooks.jinja). Tên hàm có tiền tố kh_aph_ để không trùng."""

import html
import re

import frappe
from frappe.utils import cint, flt, getdate

from kh_aph.constants import PR_OPEX
from kh_aph.price_visibility import is_price_restricted
from lab9x.vn_words import so_tien_bang_chu, so_vn


def kh_aph_an_gia(doc) -> bool:
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


def kh_aph_no_co(doc) -> dict:
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


def kh_aph_ngay(date) -> str:
    if not date:
        return "Ngày ... tháng ... năm ..."
    d = getdate(date)
    return f"Ngày {d.day:02d} tháng {d.month:02d} năm {d.year}"


def kh_aph_so(value, precision: int = 3) -> str:
    """Định dạng số kiểu Việt Nam: 1.234.567,5."""
    return so_vn(value, precision)


def kh_aph_bang_chu(amount) -> str:
    return so_tien_bang_chu(amount)


def kh_aph_cong_ty(company: str) -> dict:
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


def kh_aph_ten_nguoi(user: str) -> str:
    if not user:
        return ""
    return frappe.utils.get_fullname(user)


def kh_aph_sl_chung_tu(row) -> float | None:
    """Số lượng theo chứng từ (đơn mua) của dòng phiếu nhập; None nếu không lấy từ đơn."""
    if not row.get("purchase_order_item"):
        return None
    return frappe.db.get_value("Purchase Order Item", row.purchase_order_item, "qty")


def kh_aph_ten_kho(warehouse: str) -> str:
    """Tên kho bỏ đuôi viết tắt công ty (' - APH')."""
    if not warehouse:
        return ""
    return frappe.get_cached_value("Warehouse", warehouse, "warehouse_name") or warehouse


def kh_aph_sl_don_ban(row) -> float | None:
    """Số lượng trên đơn bán hàng của dòng phiếu giao hàng; None nếu dòng không lấy từ đơn."""
    if not row.get("so_detail"):
        return None
    return frappe.db.get_value("Sales Order Item", row.so_detail, "qty")


def kh_aph_dia_chi(text) -> str:
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


def kh_aph_lo(row) -> str:
    """Số lô của dòng phiếu (ô lô trên dòng, hoặc các lô trong gói serial/lô)."""
    if row.get("batch_no"):
        return row.batch_no
    bundle = row.get("serial_and_batch_bundle")
    if not bundle:
        return ""
    lots = frappe.get_all("Serial and Batch Entry", filters={"parent": bundle}, pluck="batch_no")
    return ", ".join(sorted({x for x in lots if x}))


def kh_aph_gia_gom_thue(doc) -> dict:
    """Biên bản giao nhận: đơn giá, thành tiền đã gồm thuế GTGT từng dòng (thuế lấy theo từng dòng hàng)."""
    from collections import defaultdict

    from lab9x.sales_rules import gia_gom_thue

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


# --- 0.3.7: phiếu thu/chi, phiếu bán hàng, tên loại phiếu kho, căn cứ mẫu theo công ty ------------

def kh_aph_mau(company) -> str:
    """Dòng căn cứ mẫu chứng từ theo chế độ kế toán của công ty (APH: TT133, VH: TT99, hộ KD: không ghi)."""
    from lab9x.print_rules import can_cu_mau

    return can_cu_mau(frappe.get_cached_value("Company", company, "abbr") if company else "")


def kh_aph_loai_phieu_kho(name) -> str:
    from lab9x.print_rules import ten_loai_phieu_kho

    return ten_loai_phieu_kho(name)


def _dia_chi_doi_tuong(party_type, party) -> str:
    if not party_type or not party or party_type not in ("Customer", "Supplier"):
        return ""
    field = "customer_primary_address" if party_type == "Customer" else "supplier_primary_address"
    addr = frappe.get_cached_value(party_type, party, field)
    if not addr:
        link = frappe.get_all(
            "Dynamic Link",
            filters={"link_doctype": party_type, "link_name": party, "parenttype": "Address"},
            pluck="parent",
            limit=1,
        )
        addr = link[0] if link else None
    if not addr:
        return ""
    a = frappe.db.get_value("Address", addr, ["address_line1", "address_line2", "city"], as_dict=True) or {}
    return html.escape(", ".join(x for x in (a.get("address_line1"), a.get("address_line2"), a.get("city")) if x), quote=False)


def kh_aph_thu_chi(doc) -> dict:
    """Thông tin in phiếu thu / phiếu chi từ Payment Entry."""
    from lab9x.print_rules import chu_tien_te, ly_do, loai_thu_chi, tieu_de_thu_chi
    from lab9x.vn_words import so_tien_bang_chu

    t_from = frappe.get_cached_value("Account", doc.paid_from, "account_type") if doc.get("paid_from") else ""
    t_to = frappe.get_cached_value("Account", doc.paid_to, "account_type") if doc.get("paid_to") else ""
    loai = loai_thu_chi(doc.payment_type, t_from, t_to)
    tieu_de, mau = tieu_de_thu_chi(loai["kieu"], loai["tien_mat"])
    if loai["kieu"] == "thu":
        tien, tt, tk = flt(doc.received_amount), doc.get("paid_to_account_currency"), doc.paid_to
        ty_gia = flt(doc.get("target_exchange_rate"))
    else:
        tien, tt, tk = flt(doc.paid_amount), doc.get("paid_from_account_currency"), doc.paid_from
        ty_gia = flt(doc.get("source_exchange_rate"))
    company_currency = frappe.get_cached_value("Company", doc.company, "default_currency") or "VND"
    ngoai_te = bool(tt) and tt != company_currency
    refs = [(r.reference_doctype, r.reference_name) for r in doc.get("references") or []]
    ghi_chu = doc.get("remarks") if doc.get("custom_remarks") else None
    from lab9x.ben_thu_ba_rules import nguoi_tren_phieu

    nguoi = (nguoi_tren_phieu(doc.get("kh_aph_ben_thu_ba"), doc.get("kh_aph_btb_ten"), doc.get("party_name"), loai["kieu"])
             or doc.get("kh_aph_nguoi_nop_nhan") or doc.get("party_name") or "")
    return {
        "kieu": loai["kieu"],
        "tien_mat": loai["tien_mat"],
        "tieu_de": tieu_de,
        "mau": mau,
        "can_cu": kh_aph_mau(doc.company) if mau else "",
        "nguoi": html.escape(nguoi, quote=False),
        "dia_chi": _dia_chi_doi_tuong(doc.get("party_type"), doc.get("party")),
        "ly_do": html.escape(ly_do(doc.payment_type, doc.get("party_type"), refs, t_from, t_to, ghi_chu), quote=False),
        "so_tien": so_vn(tien, 2 if ngoai_te else 0),
        "tien_te": tt or company_currency,
        "bang_chu": so_tien_bang_chu(tien, chu_tien_te(tt)),
        "ngoai_te": ngoai_te,
        "ty_gia": so_vn(ty_gia, 2) if ngoai_te else "",
        "quy_doi": so_vn(tien * ty_gia, 0) if ngoai_te else "",
        "tai_khoan": frappe.get_cached_value("Account", tk, "account_name") if tk else "",
        "tham_chieu": doc.get("reference_no") or "",
    }


def kh_aph_ban_hang(doc) -> dict:
    """Phiếu bán hàng (Sales Invoice): thuế suất, tiền thuế từng dòng, công nợ của khách."""
    import json as _json
    from collections import defaultdict

    from kh_aph.constants import INV_FLAG, INV_YES
    from lab9x.print_rules import nhan_thue_suat

    co_thue = doc.get(INV_FLAG) == INV_YES and bool(doc.get("taxes"))
    # 0.4.15: khách không lấy hóa đơn -> in đơn giá, thành tiền ĐÃ GỒM VAT, không dòng thuế
    gom_thue = doc.get(INV_FLAG) != INV_YES
    vat_acc = frappe.db.get_value("Account", {"company": doc.company, "account_number": "33311", "is_group": 0}, "name")
    tax_row = defaultdict(float)
    for d in doc.get("item_wise_tax_details") or []:
        tax_row[d.get("item_row")] += flt(d.get("amount"))
    dong = []
    for r in doc.get("items") or []:
        rate = None
        if r.get("item_tax_rate"):
            try:
                m = _json.loads(r.item_tax_rate) if isinstance(r.item_tax_rate, str) else r.item_tax_rate
                rate = (m or {}).get(vat_acc)
            except ValueError:
                rate = None
        if rate is None and co_thue:
            rate = next((flt(t.rate) for t in doc.taxes if t.account_head == vat_acc), None)
        title = frappe.get_cached_value("Item Tax Template", r.item_tax_template, "title") if r.get("item_tax_template") else ""
        thue = tax_row.get(r.name)
        if thue is None or (not thue and rate):
            thue = flt(r.get("net_amount")) * flt(rate) / 100
        dong.append(
            {
                "nhan": nhan_thue_suat(title, rate) if co_thue else "",
                "thue": thue if co_thue else 0,
            }
        )
    for r, d in zip(doc.get("items") or [], dong):
        d["don_gia"] = flt(r.get("rate")) if gom_thue else flt(r.get("net_rate"))
        d["thanh_tien"] = flt(r.get("amount")) if gom_thue else flt(r.get("net_amount"))
    walk_in = bool(frappe.get_cached_value("Customer", doc.customer, "kh_aph_khach_chung")) if doc.get("customer") else True
    no = None
    if not walk_in and not doc.get("is_return"):
        # Công nợ của khách tại công ty này, tính đến lúc in (gồm cả các phiếu thu sau ngày hóa đơn).
        so_du = flt(
            frappe.db.sql(
                """select ifnull(sum(debit - credit), 0) from `tabGL Entry`
                   where party_type='Customer' and party=%s and company=%s and is_cancelled=0""",
                (doc.customer, doc.company),
            )[0][0]
        )
        tong_hd = flt(doc.get("rounded_total") or doc.get("grand_total"))
        con_no_hd = flt(doc.get("outstanding_amount")) if doc.docstatus == 1 else tong_hd
        if doc.docstatus != 1:
            so_du += tong_hd
        no = {"cu": so_du - con_no_hd, "con_no_hd": con_no_hd, "tong": so_du}
    return {"co_thue": co_thue, "dong": dong, "no": no}



# 0.11.1 (cờ kh_aph_sales_adjust): biên bản giao nhận — xem kh_aph/sales_adjust.py
def kh_aph_bbgn_an_gia(doc):
    from kh_aph.sales_adjust import kh_aph_bbgn_an_gia as f
    return f(doc)


def kh_aph_sl_hien_thi(row):
    from kh_aph.sales_adjust import kh_aph_sl_hien_thi as f
    return f(row)


def kh_aph_thuc_nhan(doc):
    from kh_aph.sales_adjust import kh_aph_thuc_nhan as f
    return f(doc)
