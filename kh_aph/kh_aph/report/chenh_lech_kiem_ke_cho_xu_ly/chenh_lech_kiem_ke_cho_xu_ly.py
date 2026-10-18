"""Chênh lệch kiểm kê chờ xử lý theo vụ (lượt 0.13, cờ kh_aph_kho_van_hanh, rà soát pháp lý dòng 16)."""

import frappe


def execute(filters=None):
    from kh_aph import kho_van_hanh as K
    filters = frappe._dict(filters or {})
    K._can_bat()
    K._vai_tro({"Accounts User", "Accounts Manager", "Stock Manager", "System Manager"})
    cols = [{"fieldname": "bien_ban", "label": "Vụ (biên bản kiểm kê)", "fieldtype": "Data", "width": 320},
            {"fieldname": "company", "label": "Đơn vị", "fieldtype": "Link", "options": "Company", "width": 200},
            {"fieldname": "thieu", "label": "Thiếu chờ xử lý (1381)", "fieldtype": "Currency", "width": 160},
            {"fieldname": "thua", "label": "Thừa chờ xử lý (3381)", "fieldtype": "Currency", "width": 160},
            {"fieldname": "but_toan_nhap", "label": "Bút toán xử lý đang nháp", "fieldtype": "Data", "width": 220}]
    return cols, K.cac_vu(filters.company)
