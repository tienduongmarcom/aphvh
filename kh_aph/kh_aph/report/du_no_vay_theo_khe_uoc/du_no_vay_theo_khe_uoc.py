"""Dư nợ vay theo khế ước và lịch đến hạn 7 / 30 / 90 ngày (lượt 0.14, cờ kh_aph_tien_vay)."""

import frappe


def execute(filters=None):
    from kh_aph import tien_vay as K
    f = frappe._dict(filters or {})
    K._can_bat()
    K._vai_tro()
    cols = [{"fieldname": "name", "label": "Khế ước", "fieldtype": "Link", "options": "APH Khe uoc vay", "width": 150},
            {"fieldname": "company", "label": "Đơn vị", "fieldtype": "Link", "options": "Company", "width": 160},
            {"fieldname": "ben_cho_vay", "label": "Bên cho vay", "fieldtype": "Data", "width": 160},
            {"fieldname": "lai_suat", "label": "Lãi suất %/năm", "fieldtype": "Float", "width": 100},
            {"fieldname": "ngay_den_han", "label": "Đến hạn", "fieldtype": "Date", "width": 100},
            {"fieldname": "nhom_han", "label": "Nhóm hạn", "fieldtype": "Data", "width": 110},
            {"fieldname": "goc_nhan", "label": "Gốc đã nhận", "fieldtype": "Currency", "width": 140},
            {"fieldname": "da_tra", "label": "Gốc đã trả", "fieldtype": "Currency", "width": 140},
            {"fieldname": "du_no", "label": "Dư nợ gốc", "fieldtype": "Currency", "width": 140},
            {"fieldname": "lai_chi_phi", "label": "Lãi đã ghi chi phí", "fieldtype": "Currency", "width": 140},
            {"fieldname": "lai_phai_tra", "label": "Lãi còn phải trả", "fieldtype": "Currency", "width": 140},
            {"fieldname": "ky_han", "label": "Kỳ hạn", "fieldtype": "Data", "width": 90}]
    rows = K.du_no_vay(f.company, f.ngay, chi_dang_vay=not f.ca_da_tat_toan)
    if f.nhom_han:
        rows = [r for r in rows if r["nhom_han"] == f.nhom_han]
    return cols, rows
