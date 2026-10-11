"""Tổng hợp bán hàng theo khách — APH, VH, HKD Minh Khang trên một bảng (chỉ xem, in cho khách)."""

import frappe
from frappe.utils import flt

from lab9x.tong_hop_khach_rules import LOAI, dong_bao_cao


def _so_du(customer, company, before):
    return flt(
        frappe.db.sql(
            """select ifnull(sum(debit - credit), 0) from `tabGL Entry`
               where party_type='Customer' and party=%s and company=%s and is_cancelled=0 and posting_date < %s""",
            (customer, company, before),
        )[0][0]
    )


def _chung_tu(customer, company, f, t):
    gl = frappe.db.sql(
        """select posting_date ngay, voucher_type, voucher_no, sum(debit) no_, sum(credit) co_, min(creation) c
           from `tabGL Entry` where party_type='Customer' and party=%s and company=%s and is_cancelled=0
             and posting_date between %s and %s
           group by posting_date, voucher_type, voucher_no order by posting_date, c""",
        (customer, company, f, t),
        as_dict=True,
    )
    out = []
    for g in gl:
        ct = {"ngay": g.ngay, "loai": LOAI.get(g.voucher_type, g.voucher_type), "voucher_type": g.voucher_type,
              "so": g.voucher_no, "no": flt(g.no_), "co": flt(g.co_), "dien_giai": "", "xuat_hd": "", "so_hd": "",
              "tien_hang": 0.0, "thue": 0.0}
        if g.voucher_type == "Sales Invoice":
            si = frappe.db.get_value(
                "Sales Invoice", g.voucher_no,
                ["is_return", "kh_aph_xuat_hoa_don", "kh_aph_hd_so", "kh_aph_hd_ky_hieu", "net_total", "total_taxes_and_charges"],
                as_dict=True,
            )
            ct.update(
                loai="Trả hàng" if si.is_return else "Hóa đơn",
                xuat_hd=si.kh_aph_xuat_hoa_don or "",
                so_hd=" ".join(x for x in (si.kh_aph_hd_ky_hieu, si.kh_aph_hd_so) if x),
                tien_hang=flt(si.net_total),
                thue=flt(si.total_taxes_and_charges),
                dien_giai=", ".join(
                    frappe.get_all("Sales Invoice Item", {"parent": g.voucher_no}, pluck="item_name", order_by="idx", limit=3)
                ),
            )
        elif g.voucher_type == "Payment Entry":
            pe = frappe.db.get_value("Payment Entry", g.voucher_no, ["payment_type", "paid_to", "paid_from", "reference_no"], as_dict=True)
            acc = pe.paid_to if pe.payment_type == "Receive" else pe.paid_from
            ct.update(loai="Phiếu thu" if pe.payment_type == "Receive" else "Phiếu chi",
                      dien_giai=frappe.get_cached_value("Account", acc, "account_name") or "")
        elif g.voucher_type == "Journal Entry":
            ct["dien_giai"] = (frappe.db.get_value("Journal Entry", g.voucher_no, "user_remark") or "").strip()[:160]
        out.append(ct)
    return out


def execute(filters=None):
    f = frappe._dict(filters or {})
    cols = [
        {"fieldname": "don_vi", "label": "Đơn vị", "fieldtype": "Data", "width": 70},
        {"fieldname": "ngay", "label": "Ngày", "fieldtype": "Date", "width": 95},
        {"fieldname": "loai", "label": "Loại", "fieldtype": "Data", "width": 90},
        {"fieldname": "so", "label": "Số chứng từ", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 160},
        {"fieldname": "dien_giai", "label": "Diễn giải", "fieldtype": "Data", "width": 260},
        {"fieldname": "xuat_hd", "label": "Xuất HĐ", "fieldtype": "Data", "width": 70},
        {"fieldname": "so_hd", "label": "Số HĐ điện tử", "fieldtype": "Data", "width": 110},
        {"fieldname": "tien_hang", "label": "Tiền hàng", "fieldtype": "Currency", "width": 120},
        {"fieldname": "thue", "label": "Thuế GTGT", "fieldtype": "Currency", "width": 100},
        {"fieldname": "no", "label": "Phát sinh nợ (bán)", "fieldtype": "Currency", "width": 130},
        {"fieldname": "co", "label": "Phát sinh có (thu, trả hàng)", "fieldtype": "Currency", "width": 130},
        {"fieldname": "so_du", "label": "Còn nợ", "fieldtype": "Currency", "width": 130},
        {"fieldname": "voucher_type", "label": "Loại chứng từ", "fieldtype": "Data", "hidden": 1},
    ]
    if not f.customer:
        return cols, []
    frappe.get_doc("Customer", f.customer).check_permission("read")
    don_vi = []
    for c in frappe.get_list("Company", fields=["name", "abbr", "company_name"], order_by="creation", limit_page_length=0):
        if f.company and f.company != c.name:
            continue
        don_vi.append({"don_vi": c.abbr, "ten": c.company_name, "dau_ky": _so_du(f.customer, c.name, f.from_date),
                       "chung_tu": _chung_tu(f.customer, c.name, f.from_date, f.to_date)})
    rows = dong_bao_cao(don_vi)
    if rows:
        # Dòng tổng mang tên khách, MST cho đầu bản in (bản in chỉ nhận filters và data).
        ten, mst = frappe.db.get_value("Customer", f.customer, ["customer_name", "tax_id"]) or (f.customer, "")
        rows[-1].update(ten_khach=ten, mst=mst or "")
    return cols, rows
