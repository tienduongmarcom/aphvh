"""Khách chưa xác nhận công nợ (0.11.4, cờ kh_aph_quan_tri, R039)."""

import frappe
from frappe.utils import cint, flt, nowdate
from lab9x import quan_tri as Q


def execute(filters=None):
    from kh_aph import quan_tri as K
    filters = frappe._dict(filters or {})
    K.can_quyen({"Accounts User", "Accounts Manager", "System Manager"})
    so_ngay = cint(filters.so_ngay or frappe.db.get_single_value("Selling Settings", K.F_SO_NGAY) or 30)
    cols = [{"fieldname": "customer", "label": "Khách", "fieldtype": "Link", "options": "Customer", "width": 220},
            {"fieldname": "so_du", "label": "Số dư sổ", "fieldtype": "Currency", "width": 140},
            {"fieldname": "ngay_xn", "label": "Xác nhận lần cuối", "fieldtype": "Date", "width": 120},
            {"fieldname": "so_du_xn", "label": "Số dư khách xác nhận", "fieldtype": "Currency", "width": 150},
            {"fieldname": "chenh", "label": "Chênh lệch (xác nhận − sổ hiện tại)", "fieldtype": "Currency", "width": 170}]
    rows = []
    for r in frappe.db.sql("""SELECT party AS customer, SUM(amount) AS so_du FROM `tabPayment Ledger Entry`
            WHERE party_type='Customer' AND delinked=0 GROUP BY party HAVING SUM(amount) > 0.5""", as_dict=True):
        kh = frappe.db.get_value("Customer", r.customer, [K.F_XN_NGAY, K.F_XN_SO_DU], as_dict=True) or {}
        if not Q.qua_han_xac_nhan(kh.get(K.F_XN_NGAY), nowdate(), so_ngay):
            continue
        rows.append({"customer": r.customer, "so_du": flt(r.so_du), "ngay_xn": kh.get(K.F_XN_NGAY),
                     "so_du_xn": kh.get(K.F_XN_SO_DU),
                     "chenh": flt(kh.get(K.F_XN_SO_DU)) - flt(r.so_du) if kh.get(K.F_XN_NGAY) else None})
    return cols, sorted(rows, key=lambda x: -x["so_du"])
