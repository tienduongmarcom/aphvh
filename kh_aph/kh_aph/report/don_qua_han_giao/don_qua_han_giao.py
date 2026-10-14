"""Đơn quá hạn giao (0.11.3, cờ kh_aph_sales_p1, Q189–Q190): đơn đã xác nhận, chưa giao đủ, chưa đóng, ngày giao dự kiến
đã qua. Chỉ số lượng, không có giá trị."""

import frappe
from frappe.utils import cint, date_diff, flt, getdate, nowdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not cint(frappe.conf.get("kh_aph_sales_p1")):
        frappe.throw("Tính năng bán hàng 0.11.3 chưa được bật")
    hom_nay = getdate(filters.ngay or nowdate())
    dk = {"docstatus": 1, "per_delivered": ["<", 100], "status": ["not in", ["Closed", "Completed", "Cancelled", "On Hold"]],
          "delivery_date": ["<", hom_nay]}
    if filters.company:
        dk["company"] = filters.company
    if filters.customer:
        dk["customer"] = filters.customer
    cols = [
        {"fieldname": "name", "label": "Đơn bán", "fieldtype": "Link", "options": "Sales Order", "width": 160},
        {"fieldname": "customer", "label": "Khách", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"fieldname": "company", "label": "Đơn vị", "fieldtype": "Link", "options": "Company", "width": 160},
        {"fieldname": "delivery_date", "label": "Ngày giao dự kiến", "fieldtype": "Date", "width": 110},
        {"fieldname": "tre", "label": "Số ngày trễ", "fieldtype": "Int", "width": 90},
        {"fieldname": "per_delivered", "label": "% đã giao", "fieldtype": "Percent", "width": 90},
        {"fieldname": "con_lai", "label": "Còn phải giao (ĐVT tồn kho)", "fieldtype": "Float", "width": 150},
        {"fieldname": "status", "label": "Trạng thái", "fieldtype": "Data", "width": 120},
    ]
    rows = []
    for so in frappe.get_list("Sales Order", filters=dk, fields=["name", "customer", "company", "delivery_date",
                                                                   "per_delivered", "status"], order_by="delivery_date"):
        con = frappe.db.sql("""SELECT SUM(GREATEST(stock_qty - delivered_qty * conversion_factor, 0))
            FROM `tabSales Order Item` WHERE parent=%s""", so.name)[0][0]
        rows.append({**so, "tre": date_diff(hom_nay, so.delivery_date), "con_lai": flt(con)})
    return cols, rows
