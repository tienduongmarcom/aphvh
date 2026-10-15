"""Sổ quỹ tiền mặt (S07) / sổ tiền gửi ngân hàng (S08) — lượt 0.14, cờ kh_aph_tien_vay. Tồn sau từng phiếu."""

import frappe
from frappe.utils import getdate, nowdate


def execute(filters=None):
    from kh_aph import tien_vay as K
    f = frappe._dict(filters or {})
    K._can_bat()
    K._vai_tro()
    cols = [{"fieldname": "ngay", "label": "Ngày", "fieldtype": "Date", "width": 95},
            {"fieldname": "loai", "label": "Loại", "fieldtype": "Data", "width": 85},
            {"fieldname": "so", "label": "Số chứng từ", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 160},
            {"fieldname": "voucher_type", "label": "Loại chứng từ", "fieldtype": "Data", "hidden": 1},
            {"fieldname": "dien_giai", "label": "Diễn giải", "fieldtype": "Data", "width": 300},
            {"fieldname": "thu", "label": "Thu / gửi vào", "fieldtype": "Float", "width": 140},
            {"fieldname": "chi", "label": "Chi / rút ra", "fieldtype": "Float", "width": 140},
            {"fieldname": "ton", "label": "Tồn", "fieldtype": "Float", "width": 150}]
    if not (f.company and f.account):
        return cols, []
    hom_nay = getdate(nowdate())
    s = K.so_quy(f.company, f.account, f.tu_ngay or hom_nay.replace(day=1), f.den_ngay or hom_nay)
    rows = [{"dien_giai": "Số tồn đầu kỳ", "ton": s["dau_ky"], "bold": 1}] + s["dong"]
    rows.append({"dien_giai": "Cộng phát sinh trong kỳ", "thu": s["thu"], "chi": s["chi"], "bold": 1})
    rows.append({"dien_giai": "Số tồn cuối kỳ", "ton": s["cuoi_ky"], "bold": 1})
    return cols, rows
