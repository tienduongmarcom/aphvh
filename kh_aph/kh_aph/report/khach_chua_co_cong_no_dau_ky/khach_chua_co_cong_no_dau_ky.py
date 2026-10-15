"""Khách đã giao dịch sau ngày đầu kỳ mà chưa có công nợ đầu kỳ (lượt 0.13, cờ kh_aph_dau_ky)."""

import frappe


def execute(filters=None):
    from kh_aph import dau_ky as K
    filters = frappe._dict(filters or {})
    K.can_quyen()
    if not filters.company:
        frappe.throw("Chọn đơn vị")
    ngay = filters.ngay or K.ngay_mac_dinh()
    if not ngay:
        frappe.throw("Chọn ngày đầu kỳ")
    cols = [{"fieldname": "customer", "label": "Khách", "fieldtype": "Link", "options": "Customer", "width": 240},
            {"fieldname": "so_ct", "label": "Số chứng từ", "fieldtype": "Int", "width": 100},
            {"fieldname": "tong_ban", "label": "Tổng bán sau đầu kỳ", "fieldtype": "Currency", "width": 160},
            {"fieldname": "tong_thu", "label": "Tổng đã thu", "fieldtype": "Currency", "width": 140},
            {"fieldname": "lan_cuoi", "label": "Giao dịch cuối", "fieldtype": "Date", "width": 120}]
    return cols, K.khach_chua_co_cong_no(filters.company, ngay)
