"""Lãi gộp quản trị (0.11.4, cờ kh_aph_quan_tri, R099–R101, R104). Cộng ngang 4 đơn vị — không phải hợp nhất kế toán."""

import frappe
from lab9x import quan_tri as Q

THEO = {"Công ty": "company", "Kho": "warehouse", "Mặt hàng": "item_code", "Khách": "customer", "Đơn": "sales_order"}
LINK = {"company": "Company", "warehouse": "Warehouse", "item_code": "Item", "customer": "Customer",
        "sales_order": "Sales Order"}


def execute(filters=None):
    from kh_aph import quan_tri as K
    filters = frappe._dict(filters or {})
    from kh_aph.executive_access import guard
    guard()
    tu, den = K.tu_ngay_den_ngay(filters)
    theo = THEO.get(filters.theo or "Công ty", "company")
    cty = K.cac_cong_ty()
    abbr = {n: a for a, n in cty}
    ly_do = {(c, t): K.ly_do_tam_tinh(c, t) for _a, c in cty for t in K.cac_thang(tu, den)}
    dong = []
    for r in K.dong_lai_gop(tu, den, filters.company):
        thang = f"{r['posting_date']:%Y-%m}" if hasattr(r["posting_date"], "strftime") else str(r["posting_date"])[:7]
        dong.append({"khoa": r.get(theo) or "(không có)", "abbr": abbr.get(r["company"]), "doanh_thu": r["doanh_thu"],
                     "gia_von": r["gia_von"], "cp_truc_tiep": r["cp_truc_tiep"],
                     "tam_tinh": {f"{r['company'] and abbr.get(r['company'])} {thang}: {x}"
                                  for x in ly_do.get((r["company"], thang), set())}})
    ds_abbr = [a for a, _n in cty]
    kq = Q.cong_ngang(dong, ds_abbr)
    cols = [{"fieldname": "khoa", "label": filters.theo or "Công ty", "fieldtype": "Link" if theo in LINK else "Data",
             "options": LINK.get(theo), "width": 200}]
    for a in ds_abbr:
        cols += [{"fieldname": f"{a}_dt", "label": f"{a}: doanh thu", "fieldtype": "Currency", "width": 120},
                 {"fieldname": f"{a}_gv", "label": f"{a}: giá vốn", "fieldtype": "Currency", "width": 120},
                 {"fieldname": f"{a}_lg", "label": f"{a}: lãi gộp", "fieldtype": "Currency", "width": 120}]
    cols += [{"fieldname": "dt", "label": "Cộng ngang: doanh thu thuần", "fieldtype": "Currency", "width": 150},
             {"fieldname": "gv", "label": "Cộng ngang: giá vốn", "fieldtype": "Currency", "width": 140},
             {"fieldname": "lg", "label": "Cộng ngang: lãi gộp", "fieldtype": "Currency", "width": 140},
             {"fieldname": "ty_le", "label": "% lãi gộp", "fieldtype": "Percent", "width": 90},
             {"fieldname": "cp", "label": "Chi phí trực tiếp của đơn", "fieldtype": "Currency", "width": 140},
             {"fieldname": "lai_sau_cp", "label": "Lãi sau chi phí trực tiếp", "fieldtype": "Currency", "width": 150},
             {"fieldname": "tam_tinh", "label": "Lãi tạm tính (lý do)", "fieldtype": "Data", "width": 260}]
    rows = [{"khoa": k, **v} for k, v in sorted(kq.items(), key=lambda x: -x[1]["dt"])]
    return cols, rows, Q.GHI_CHU_CONG_NGANG + ". Chi phí bán hàng chung (6421 / 641) không chia vào đơn."
