"""Sổ kế toán hộ kinh doanh nộp thuế theo thu nhập (TT152/2025): S2c-HKD doanh thu, chi phí; S2d-HKD vật liệu,
dụng cụ, sản phẩm, hàng hóa; S2e-HKD chi tiết tiền. Lập từ hóa đơn, sổ cái, sổ kho của đơn vị hộ kinh doanh."""

import frappe
from frappe.utils import flt

from aphvh.so_hkd_rules import THUE_SUAT_TNCN_MAC_DINH, dong_s2c, dong_s2d, dong_s2e

C_SO = {"fieldname": "so", "label": "Số hiệu chứng từ", "fieldtype": "Data", "width": 160}
C_NGAY = {"fieldname": "ngay", "label": "Ngày tháng", "fieldtype": "Date", "width": 95}
C_DG = {"fieldname": "dien_giai", "label": "Diễn giải", "fieldtype": "Data", "width": 360}
C_KIEU = {"fieldname": "kieu", "label": "Loại dòng", "fieldtype": "Data", "hidden": 1}


def _cur(fn, label, w=130):
    return {"fieldname": fn, "label": label, "fieldtype": "Currency", "width": w}


def _flt(fn, label):
    return {"fieldname": fn, "label": label, "fieldtype": "Float", "width": 95}


def _s2c(f):
    dt = frappe.db.sql(
        """select si.name so, si.posting_date ngay, si.aphvh_hd_so hd, si.customer_name kh, si.is_return, si.base_net_total st
           from `tabSales Invoice` si where si.company=%s and si.docstatus=1 and si.posting_date between %s and %s
           order by si.posting_date, si.name""",
        (f.company, f.from_date, f.to_date),
        as_dict=True,
    )
    doanh_thu = [{"so": d.hd or d.so, "ngay": d.ngay, "so_tien": flt(d.st),
                  "dien_giai": ("Hàng bán bị trả lại: " if d.is_return else "Bán hàng: ") + (d.kh or "")} for d in dt]
    cp = frappe.db.sql(
        """select g.voucher_no so, g.posting_date ngay, a.account_name tk, sum(g.debit - g.credit) st, max(g.remarks) ghi
           from `tabGL Entry` g join tabAccount a on a.name = g.account
           where g.company=%s and g.is_cancelled=0 and a.root_type='Expense' and g.posting_date between %s and %s
           group by g.voucher_no, g.posting_date, a.name order by g.posting_date, g.voucher_no""",
        (f.company, f.from_date, f.to_date),
        as_dict=True,
    )
    chi_phi = [{"so": c.so, "ngay": c.ngay, "so_tien": flt(c.st),
                "dien_giai": c.tk + (f" – {c.ghi[:80]}" if c.ghi and c.ghi != "No Remarks" else "")} for c in cp if flt(c.st)]
    cols = [C_SO, C_NGAY, C_DG, _cur("so_tien", "Số tiền", 150), C_KIEU]
    return cols, dong_s2c(doanh_thu, chi_phi, flt(f.thue_suat_tncn or THUE_SUAT_TNCN_MAC_DINH))


def _s2d(f):
    cond, args = "", [f.company]
    if f.item_code:
        cond, args = " and sle.item_code=%s", [f.company, f.item_code]
    items = frappe.db.sql(
        f"""select distinct sle.item_code from `tabStock Ledger Entry` sle join tabWarehouse w on w.name = sle.warehouse
            where w.company=%s and sle.is_cancelled=0 and sle.posting_date <= %s{cond} order by sle.item_code""",
        [args[0], f.to_date] + args[1:],
        pluck=True,
    )
    mh = []
    for it in items:
        dau = frappe.db.sql(
            """select ifnull(sum(sle.actual_qty),0), ifnull(sum(sle.stock_value_difference),0) from `tabStock Ledger Entry` sle
               join tabWarehouse w on w.name = sle.warehouse where w.company=%s and sle.item_code=%s and sle.is_cancelled=0
               and sle.posting_date < %s""",
            (f.company, it, f.from_date),
        )[0]
        ps = frappe.db.sql(
            """select sle.voucher_type, sle.voucher_no, sle.posting_date, sle.actual_qty q, sle.stock_value_difference v,
                      sle.incoming_rate, sle.valuation_rate
               from `tabStock Ledger Entry` sle join tabWarehouse w on w.name = sle.warehouse
               where w.company=%s and sle.item_code=%s and sle.is_cancelled=0 and sle.posting_date between %s and %s
               order by sle.posting_date, sle.posting_time, sle.creation""",
            (f.company, it, f.from_date, f.to_date),
            as_dict=True,
        )
        ten, dvt = frappe.db.get_value("Item", it, ["item_name", "stock_uom"])
        rows = []
        for p in ps:
            nhap = flt(p.q) > 0
            rows.append({"so": p.voucher_no, "ngay": p.posting_date,
                         "dien_giai": ("Nhập – " if nhap else "Xuất – ") + _(p.voucher_type),
                         "don_gia": flt(p.incoming_rate if nhap and p.incoming_rate else p.valuation_rate),
                         "nhap_sl": flt(p.q) if nhap else 0, "nhap_tt": flt(p.v) if nhap else 0,
                         "xuat_sl": -flt(p.q) if not nhap else 0, "xuat_tt": -flt(p.v) if not nhap else 0})
        mh.append({"ma": it, "ten": ten, "dvt": dvt, "ton_sl": flt(dau[0]), "ton_tt": flt(dau[1]), "ps": rows})
    cols = [C_SO, C_NGAY, C_DG, {"fieldname": "dvt", "label": "ĐVT", "fieldtype": "Data", "width": 60},
            _cur("don_gia", "Đơn giá", 100), _flt("nhap_sl", "Nhập SL"), _cur("nhap_tt", "Nhập thành tiền"),
            _flt("xuat_sl", "Xuất SL"), _cur("xuat_tt", "Xuất thành tiền"), _flt("ton_sl", "Tồn SL"), _cur("ton_tt", "Tồn thành tiền"), C_KIEU]
    return cols, dong_s2d(mh)


def _s2e(f):
    tks = frappe.get_all("Account", {"company": f.company, "account_type": ["in", ["Cash", "Bank"]], "is_group": 0},
                         ["name", "account_name", "account_number", "account_type"], order_by="account_type desc, account_number")
    tk = []
    for a in tks:
        dau = flt(frappe.db.sql("select ifnull(sum(debit-credit),0) from `tabGL Entry` where account=%s and is_cancelled=0 and posting_date < %s",
                                (a.name, f.from_date))[0][0])
        ps = frappe.db.sql(
            """select voucher_no so, posting_date ngay, sum(debit) thu, sum(credit) chi, max(remarks) ghi, max(party) dt
               from `tabGL Entry` where account=%s and is_cancelled=0 and posting_date between %s and %s
               group by voucher_no, posting_date order by posting_date, min(creation)""",
            (a.name, f.from_date, f.to_date),
            as_dict=True,
        )
        loai = "Tiền mặt" if a.account_type == "Cash" else "Tiền gửi ngân hàng"
        tk.append({"ten": f"{loai}: {a.account_number or ''} {a.account_name}".strip(), "dau_ky": dau,
                   "ps": [{"so": p.so, "ngay": p.ngay, "thu": flt(p.thu), "chi": flt(p.chi),
                           "dien_giai": " – ".join(x for x in ((p.dt or ""), (p.ghi or "")[:80] if p.ghi != "No Remarks" else "") if x)} for p in ps]})
    cols = [C_SO, C_NGAY, C_DG, _cur("thu", "Thu (gửi vào)"), _cur("chi", "Chi (rút ra)"), _cur("ton", "Tồn"), C_KIEU]
    return cols, dong_s2e(tk)


def _(s):
    return frappe._(s)


def execute(filters=None):
    f = frappe._dict(filters or {})
    f.mau_so = f.mau_so or "S2c-HKD"
    if not (f.company and f.from_date and f.to_date):
        return [C_SO, C_NGAY, C_DG], []
    cols, rows = {"S2c-HKD": _s2c, "S2d-HKD": _s2d, "S2e-HKD": _s2e}[f.mau_so](f)
    if rows:
        from aphvh.print_utils import aphvh_cong_ty

        c = aphvh_cong_ty(f.company)
        rows[-1].update(ten_ho=c.get("ten"), dia_chi=c.get("dia_chi"), mst=c.get("mst"))
    return cols, rows
