"""Dòng tiền 7 / 30 ngày (0.11.4, cờ kh_aph_quan_tri, R102–R103). Loại đối tác nội bộ giữa các đơn vị."""

import frappe
from frappe.utils import getdate, nowdate
from lab9x import quan_tri as Q

KHOA = ("so_du", "thu_7", "chi_7", "rong_7", "thu_30", "chi_30", "rong_30", "qua_han_thu", "qua_han_chi")
NHAN = {"so_du": "Tiền + ngân hàng hiện có", "thu_7": "Dự thu 7 ngày", "chi_7": "Dự chi 7 ngày", "rong_7": "Ròng 7 ngày",
        "thu_30": "Dự thu 30 ngày", "chi_30": "Dự chi 30 ngày", "rong_30": "Ròng 30 ngày",
        "qua_han_thu": "Phải thu quá hạn", "qua_han_chi": "Phải trả quá hạn"}


def execute(filters=None):
    from kh_aph import quan_tri as K
    filters = frappe._dict(filters or {})
    from kh_aph.executive_access import guard
    guard()
    ngay = getdate(filters.ngay or nowdate())
    cols = [{"fieldname": "don_vi", "label": "Đơn vị", "fieldtype": "Data", "width": 220}] + \
        [{"fieldname": k, "label": NHAN[k], "fieldtype": "Currency", "width": 140} for k in KHOA]
    rows, tong = [], dict.fromkeys(KHOA, 0.0)
    for a, ten in K.cac_cong_ty():
        kq, _thu, _chi = K.dong_tien_cong_ty(ten, ngay)
        rows.append({"don_vi": f"{a} — {ten}", **kq})
        for k in KHOA:
            tong[k] += kq[k]
    rows.append({"don_vi": "Cộng ngang", **tong, "bold": 1})
    return cols, rows, Q.GHI_CHU_CONG_NGANG + ". Đã loại phải thu / phải trả giữa các đơn vị nội bộ; quá hạn không cộng vào ròng."
