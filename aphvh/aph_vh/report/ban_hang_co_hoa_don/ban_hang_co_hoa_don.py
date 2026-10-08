"""Bán hàng có hóa đơn (0.3.1): các hóa đơn bán hàng đã xác nhận có Xuất hóa đơn GTGT = Có.

Dùng để đối chiếu với bảng kê hóa đơn đầu ra trên MISA theo từng số hóa đơn, và tìm các lần bán
chọn "Có" mà kế toán chưa ghi số hóa đơn điện tử. Lần bán không xuất hóa đơn không có ở đây.
"""

import frappe
from frappe import _

from aphvh.constants import INV_FLAG, INV_YES, SI_EINV_DATE, SI_EINV_NO, SI_EINV_SERIES

BY_EINV_DATE = "Ngày hóa đơn điện tử"
WITH_NO = "Đã ghi số hóa đơn"
WITHOUT_NO = "Chưa ghi số hóa đơn"


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Ngày hạch toán"), "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
        {"label": _("Hóa đơn ERPNext"), "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 170},
        {"label": _("Trả lại"), "fieldname": "is_return", "fieldtype": "Check", "width": 60},
        {"label": _("Ký hiệu"), "fieldname": SI_EINV_SERIES, "fieldtype": "Data", "width": 100},
        {"label": _("Số hóa đơn"), "fieldname": SI_EINV_NO, "fieldtype": "Data", "width": 100},
        {"label": _("Ngày hóa đơn"), "fieldname": SI_EINV_DATE, "fieldtype": "Date", "width": 105},
        {"label": _("Mã khách"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
        {"label": _("Tên khách"), "fieldname": "customer_name", "fieldtype": "Data", "width": 220},
        {"label": _("Mã số thuế"), "fieldname": "tax_id", "fieldtype": "Data", "width": 120},
        {"label": _("Tiền hàng"), "fieldname": "net_total", "fieldtype": "Currency", "width": 130},
        {"label": _("Thuế GTGT"), "fieldname": "tax", "fieldtype": "Currency", "width": 110},
        {"label": _("Tổng thanh toán"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    si = frappe.qb.DocType("Sales Invoice")
    date_col = si[SI_EINV_DATE] if filters.date_basis == BY_EINV_DATE else si.posting_date
    q = (
        frappe.qb.from_(si)
        .select(
            si.posting_date,
            si.name,
            si.is_return,
            si[SI_EINV_SERIES],
            si[SI_EINV_NO],
            si[SI_EINV_DATE],
            si.customer,
            si.customer_name,
            si.tax_id,
            si.base_net_total.as_("net_total"),
            si.base_total_taxes_and_charges.as_("tax"),
            si.base_grand_total.as_("grand_total"),
        )
        .where(si.docstatus == 1)
        .where(si[INV_FLAG] == INV_YES)
        .orderby(date_col)
        .orderby(si[SI_EINV_SERIES])
        .orderby(si[SI_EINV_NO])
        .orderby(si.name)
    )
    if filters.company:
        q = q.where(si.company == filters.company)
    if filters.from_date:
        q = q.where(date_col >= filters.from_date)
    if filters.to_date:
        q = q.where(date_col <= filters.to_date)
    if filters.customer:
        q = q.where(si.customer == filters.customer)
    if filters.status == WITH_NO:
        q = q.where(si[SI_EINV_NO].isnotnull() & (si[SI_EINV_NO] != ""))
    elif filters.status == WITHOUT_NO:
        q = q.where(si[SI_EINV_NO].isnull() | (si[SI_EINV_NO] == ""))
    return q.run(as_dict=True)
