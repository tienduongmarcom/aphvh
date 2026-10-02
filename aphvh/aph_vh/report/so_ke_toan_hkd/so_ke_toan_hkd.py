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
        """select g.voucher_type vt, g.voucher_no so, g.posting_date ngay, a.account_name tk, sum(g.debit - g.credit) st, max(g.remarks) ghi
           from `tabGL Entry` g join tabAccount a on a.name = g.account
           where g.company=%s and g.is_cancelled=0 and a.root_type='Expense' and g.posting_date between %s and %s
           group by g.voucher_type, g.voucher_no, g.posting_date, a.name order by g.posting_date, g.voucher_no""",
        (f.company, f.from_date, f.to_date),
        as_dict=True,
    )
    chi_phi = [{"so": c.so, "ngay": c.ngay, "so_tien": flt(c.st), **_khong_hop_ly(c.vt, c.so),
                "dien_giai": c.tk + (f" – {d}" if (d := _dien_giai(c.vt, c.so, None, c.ghi)) else "")} for c in cp if flt(c.st)]
    cols = [C_SO, C_NGAY, C_DG, _cur("so_tien", "Số tiền", 150), C_KIEU]
    return cols, dong_s2c(doanh_thu, chi_phi, flt(f.thue_suat_tncn or THUE_SUAT_TNCN_MAC_DINH))


def _khong_hop_ly(voucher_type, voucher_no) -> dict:
    """Cờ "Chi phí không hợp lý" kế toán tích trên chứng từ (0.4.8)."""
    from aphvh.install import CP_KHL_DOCTYPES, F_CP_KHL, F_CP_KHL_LY_DO

    if voucher_type not in CP_KHL_DOCTYPES or not frappe.get_meta(voucher_type).has_field(F_CP_KHL):
        return {}
    v = frappe.db.get_value(voucher_type, voucher_no, [F_CP_KHL, F_CP_KHL_LY_DO], as_dict=True) or {}
    return {"khong_hop_ly": 1, "ly_do": v.get(F_CP_KHL_LY_DO)} if v.get(F_CP_KHL) else {}


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
        # Số lượng theo "tồn sau giao dịch" từng kho: phiếu kiểm kê (cả tồn đầu kỳ) không ghi số lượng thay đổi.
        sles = frappe.db.sql(
            """select sle.voucher_type, sle.voucher_no, sle.posting_date, sle.warehouse, sle.qty_after_transaction qa,
                      sle.stock_value_difference v, sle.incoming_rate, sle.valuation_rate
               from `tabStock Ledger Entry` sle join tabWarehouse w on w.name = sle.warehouse
               where w.company=%s and sle.item_code=%s and sle.is_cancelled=0 and sle.posting_date <= %s
               order by sle.posting_date, sle.posting_time, sle.creation""",
            (f.company, it, f.to_date),
            as_dict=True,
        )
        truoc, dau_sl, dau_tt, rows = {}, 0.0, 0.0, []
        for p in sles:
            dq = flt(p.qa) - truoc.get(p.warehouse, 0.0)
            truoc[p.warehouse] = flt(p.qa)
            if str(p.posting_date) < str(f.from_date):
                dau_sl += dq
                dau_tt += flt(p.v)
                continue
            if not dq and not flt(p.v):
                continue
            nhap = dq > 0 or (dq == 0 and flt(p.v) > 0)
            rows.append({"so": p.voucher_no, "ngay": p.posting_date,
                         "dien_giai": ("Nhập – " if nhap else "Xuất – ") + _(p.voucher_type),
                         "don_gia": flt(p.incoming_rate if nhap and p.incoming_rate else p.valuation_rate),
                         "nhap_sl": dq if nhap else 0, "nhap_tt": flt(p.v) if nhap else 0,
                         "xuat_sl": -dq if not nhap else 0, "xuat_tt": -flt(p.v) if not nhap else 0})
        ten, dvt = frappe.db.get_value("Item", it, ["item_name", "stock_uom"])
        mh.append({"ma": it, "ten": ten, "dvt": dvt, "ton_sl": dau_sl, "ton_tt": dau_tt, "ps": rows})
    cols = [C_SO, C_NGAY, C_DG, {"fieldname": "dvt", "label": "ĐVT", "fieldtype": "Data", "width": 60},
            _cur("don_gia", "Đơn giá", 100), _flt("nhap_sl", "Nhập SL"), _cur("nhap_tt", "Nhập thành tiền"),
            _flt("xuat_sl", "Xuất SL"), _cur("xuat_tt", "Xuất thành tiền"), _flt("ton_sl", "Tồn SL"), _cur("ton_tt", "Tồn thành tiền"), C_KIEU]
    return cols, dong_s2d(mh)


def _dien_giai(voucher_type, voucher_no, party, ghi):
    """Diễn giải tiếng Việt: phiếu thu chi lấy lý do như bản in phiếu (ERPNext tự sinh câu tiếng Anh)."""
    if voucher_type == "Payment Entry":
        from aphvh.print_rules import ly_do

        pe = frappe.db.get_value("Payment Entry", voucher_no,
                                 ["payment_type", "party_type", "party_name", "custom_remarks", "remarks", "paid_from", "paid_to"], as_dict=True)
        if pe:
            refs = frappe.get_all("Payment Entry Reference", {"parent": voucher_no}, ["reference_doctype", "reference_name"], as_list=True)
            tf = frappe.get_cached_value("Account", pe.paid_from, "account_type") if pe.paid_from else None
            tt = frappe.get_cached_value("Account", pe.paid_to, "account_type") if pe.paid_to else None
            txt = ly_do(pe.payment_type, pe.party_type, refs, tf, tt, pe.remarks if pe.custom_remarks else None)
            return (f"{pe.party_name}: " if pe.party_name and pe.party_name not in txt else "") + txt
    ghi = "" if not ghi or ghi == "No Remarks" else ghi[:100]
    return " – ".join(x for x in (party or "", ghi) if x)


def _s2e(f):
    tks = frappe.get_all("Account", {"company": f.company, "account_type": ["in", ["Cash", "Bank"]], "is_group": 0},
                         ["name", "account_name", "account_number", "account_type"], order_by="account_type desc, account_number")
    tk = []
    for a in tks:
        dau = flt(frappe.db.sql("select ifnull(sum(debit-credit),0) from `tabGL Entry` where account=%s and is_cancelled=0 and posting_date < %s",
                                (a.name, f.from_date))[0][0])
        ps = frappe.db.sql(
            """select voucher_type vt, voucher_no so, posting_date ngay, sum(debit) thu, sum(credit) chi, max(remarks) ghi, max(party) dt
               from `tabGL Entry` where account=%s and is_cancelled=0 and posting_date between %s and %s
               group by voucher_type, voucher_no, posting_date order by posting_date, min(creation)""",
            (a.name, f.from_date, f.to_date),
            as_dict=True,
        )
        loai = "Tiền mặt" if a.account_type == "Cash" else "Tiền gửi ngân hàng"
        tk.append({"ten": f"{loai}: {a.account_number or ''} {a.account_name}".strip(), "dau_ky": dau,
                   "ps": [{"so": p.so, "ngay": p.ngay, "thu": flt(p.thu), "chi": flt(p.chi),
                           "dien_giai": _dien_giai(p.vt, p.so, p.dt, p.ghi)} for p in ps]})
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
