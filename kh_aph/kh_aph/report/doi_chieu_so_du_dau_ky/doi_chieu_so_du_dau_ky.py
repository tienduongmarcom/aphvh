"""Đối chiếu số dư đầu kỳ (0.12.1, cờ kh_aph_dau_ky). Chỉ đọc sổ."""

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
    cols = [{"fieldname": "loai", "label": "Loại số dư", "fieldtype": "Data", "width": 320},
            {"fieldname": "so_nguon", "label": "Số theo bảng nguồn", "fieldtype": "Currency", "width": 170},
            {"fieldname": "so_so", "label": "Số trên sổ ERP", "fieldtype": "Currency", "width": 170},
            {"fieldname": "chenh", "label": "Chênh lệch", "fieldtype": "Currency", "width": 150},
            {"fieldname": "trang_thai", "label": "Trạng thái", "fieldtype": "Data", "width": 200}]
    return cols, K.doi_chieu(filters.company, ngay)
