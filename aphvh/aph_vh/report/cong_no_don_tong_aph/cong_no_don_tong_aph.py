"""Công nợ theo đơn tổng (0.3.9): mỗi đơn tổng một dòng — tiền đơn gồm thuế, đã lập hóa đơn, đã thu,
còn phải thu, và còn phải thu tách theo đơn vị bán (APH / VH / HKD)."""

import frappe
from frappe.utils import flt

from aphvh.aph_vh.doctype.don_tong_aph.don_tong_aph import tinh_hinh


def execute(filters=None):
    filters = frappe._dict(filters or {})
    abbrs = frappe.get_all("Company", pluck="abbr", order_by="creation")
    cond = {"docstatus": 1}
    if filters.customer:
        cond["customer"] = filters.customer
    if filters.from_date and filters.to_date:
        cond["transaction_date"] = ["between", [filters.from_date, filters.to_date]]
    rows = []
    for d in frappe.get_all("Don Tong APH", cond, ["name", "transaction_date", "customer", "customer_name"], order_by="transaction_date desc, name desc"):
        th = tinh_hinh(d.name)
        t = th["tong"]
        if filters.chi_con_no and flt(t["con_phai_thu"]) < 1:
            continue
        row = {
            "don_tong": d.name,
            "ngay": d.transaction_date,
            "customer": d.customer,
            "customer_name": d.customer_name,
            "tong": t["tong"],
            "da_lap_hd": t["da_lap_hd"],
            "da_thu": t["da_thu"],
            "con_phai_thu": t["con_phai_thu"],
        }
        for a in abbrs:
            row["con_" + a] = sum(flt(x["con_phai_thu"]) for x in th["don_con"] if x["cong_ty"] == a)
        rows.append(row)
    cols = [
        {"fieldname": "don_tong", "label": "Đơn tổng", "fieldtype": "Link", "options": "Don Tong APH", "width": 140},
        {"fieldname": "ngay", "label": "Ngày", "fieldtype": "Date", "width": 95},
        {"fieldname": "customer", "label": "Mã khách", "fieldtype": "Link", "options": "Customer", "width": 110},
        {"fieldname": "customer_name", "label": "Tên khách", "fieldtype": "Data", "width": 220},
        {"fieldname": "tong", "label": "Tiền đơn (gồm thuế)", "fieldtype": "Currency", "width": 140},
        {"fieldname": "da_lap_hd", "label": "Đã lập hóa đơn", "fieldtype": "Currency", "width": 130},
        {"fieldname": "da_thu", "label": "Đã thu", "fieldtype": "Currency", "width": 130},
        {"fieldname": "con_phai_thu", "label": "Còn phải thu", "fieldtype": "Currency", "width": 130},
    ] + [{"fieldname": "con_" + a, "label": f"Còn phải thu {a}", "fieldtype": "Currency", "width": 120} for a in abbrs]
    return cols, rows
