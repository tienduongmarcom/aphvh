"""Công nợ với người thu / chi hộ qua tài khoản cá nhân (lượt 0.14): 1388 (giám đốc còn giữ tiền thu hộ) − 3388 (công ty
còn phải trả tiền chi hộ), theo người và đơn vị. Cờ kh_aph_tien_vay."""

import frappe


def execute(filters=None):
    from kh_aph import tien_vay as K
    f = frappe._dict(filters or {})
    K._can_bat()
    K._vai_tro()
    cols = [{"fieldname": "nhan_vien", "label": "Người", "fieldtype": "Link", "options": "Employee", "width": 120},
            {"fieldname": "ten", "label": "Họ tên", "fieldtype": "Data", "width": 180},
            {"fieldname": "company", "label": "Đơn vị", "fieldtype": "Link", "options": "Company", "width": 200},
            {"fieldname": "phai_thu", "label": "Giữ tiền thu hộ (1388)", "fieldtype": "Currency", "width": 160},
            {"fieldname": "phai_tra", "label": "Công ty còn nợ chi hộ (3388)", "fieldtype": "Currency", "width": 180},
            {"fieldname": "chenh", "label": "Chênh (+ giám đốc phải nộp lại)", "fieldtype": "Currency", "width": 200}]
    return cols, K.cong_no_giam_doc(f.company, f.nhan_vien, f.den_ngay)
