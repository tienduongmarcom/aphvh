"""Đề nghị bổ sung hàng (lượt 0.13, cờ kh_aph_kho_van_hanh, R057). Chỉ số lượng, không giá."""

import frappe


def execute(filters=None):
    from kh_aph import kho_van_hanh as K
    filters = frappe._dict(filters or {})
    K._can_bat()
    K._vai_tro(K.VAI_TRO_KHO)
    cols = [{"fieldname": "item_code", "label": "Mặt hàng", "fieldtype": "Link", "options": "Item", "width": 200},
            {"fieldname": "warehouse", "label": "Kho nhận", "fieldtype": "Link", "options": "Warehouse", "width": 200},
            {"fieldname": "ton", "label": "Tồn", "fieldtype": "Float", "width": 90},
            {"fieldname": "da_giu", "label": "Đã giữ cho đơn", "fieldtype": "Float", "width": 110},
            {"fieldname": "thieu_cho", "label": "Thiếu chờ xử lý", "fieldtype": "Float", "width": 110},
            {"fieldname": "kha_dung", "label": "Khả dụng", "fieldtype": "Float", "width": 90},
            {"fieldname": "dang_ve", "label": "Đang về / đã yêu cầu", "fieldtype": "Float", "width": 130},
            {"fieldname": "nguong", "label": "Ngưỡng", "fieldtype": "Float", "width": 90},
            {"fieldname": "de_nghi", "label": "Đề nghị", "fieldtype": "Float", "width": 90}]
    return cols, K.de_nghi(filters.company, filters.warehouse)
