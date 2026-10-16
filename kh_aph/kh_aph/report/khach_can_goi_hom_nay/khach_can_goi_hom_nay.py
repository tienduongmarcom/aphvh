"""Khách cần gọi thu nợ hôm nay (lượt 0.13, cờ kh_aph_gia_san)."""

import frappe


def execute(filters=None):
    from kh_aph import ban_quay as K
    filters = frappe._dict(filters or {})
    K._can_bat()
    K._vai_tro()
    cols = [{"fieldname": "customer", "label": "Khách", "fieldtype": "Link", "options": "Customer", "width": 130},
            {"fieldname": "ten", "label": "Tên", "fieldtype": "Data", "width": 200},
            {"fieldname": "dien_thoai", "label": "Điện thoại", "fieldtype": "Data", "width": 120},
            {"fieldname": "con_no", "label": "Còn nợ", "fieldtype": "Currency", "width": 130},
            {"fieldname": "qua_han", "label": "Quá hạn", "fieldtype": "Currency", "width": 130},
            {"fieldname": "hen_tra", "label": "Hẹn trả", "fieldtype": "Date", "width": 100},
            {"fieldname": "ly_do", "label": "Lý do gọi", "fieldtype": "Data", "width": 220},
            {"fieldname": "goi_cuoi", "label": "Gọi lần cuối", "fieldtype": "Datetime", "width": 150},
            {"fieldname": "ket_qua", "label": "Kết quả", "fieldtype": "Data", "width": 200}]
    return cols, K.khach_can_goi(filters.company)
