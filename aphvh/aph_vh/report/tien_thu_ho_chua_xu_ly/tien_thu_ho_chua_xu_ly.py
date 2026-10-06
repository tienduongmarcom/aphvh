"""Tiền thu hộ (0.4.20): liệt kê bút toán thu hộ theo trạng thái xử lý. Mặc định chỉ khoản 'Cần xử lý'."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from aphvh import thu_ho_rules as T


def execute(filters=None):
    f = frappe._dict(filters or {})
    cols = [
        {"label": _("Bút toán"), "fieldname": "name", "fieldtype": "Link", "options": "Journal Entry", "width": 150},
        {"label": _("Ngày ghi sổ"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Công ty"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 200},
        {"label": _("Chủ hàng"), "fieldname": "chu_hang", "fieldtype": "Data", "width": 90},
        {"label": _("Khách chuyển tiền"), "fieldname": "khach", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": _("Số phiếu bán / hóa đơn"), "fieldname": "tham_chieu", "fieldtype": "Data", "width": 150},
        {"label": _("Số tiền thu hộ"), "fieldname": "so_tien", "fieldtype": "Currency", "width": 140},
        {"label": _("Trạng thái"), "fieldname": "trang_thai", "fieldtype": "Data", "width": 100},
        {"label": _("Số ngày chờ"), "fieldname": "so_ngay", "fieldtype": "Int", "width": 90},
        {"label": _("Số chứng từ MISA / ghi chú"), "fieldname": "ghi_chu", "fieldtype": "Data", "width": 220},
        {"label": "", "fieldname": "kieu", "fieldtype": "Data", "hidden": 1},
    ]
    cond, val = ["je.docstatus = 1", "je.aphvh_thu_ho = 1", "a.account_name = %(ten_tk)s"], {"ten_tk": T.TEN_TK_THU_HO}
    for k, sql in (("company", "je.company = %(company)s"), ("trang_thai", "je.aphvh_th_trang_thai = %(trang_thai)s"),
                   ("chu_hang", "je.aphvh_th_chu_hang = %(chu_hang)s"), ("tu_ngay", "je.posting_date >= %(tu_ngay)s"),
                   ("den_ngay", "je.posting_date <= %(den_ngay)s")):
        if f.get(k):
            cond.append(sql)
            val[k] = f.get(k)
    rows = frappe.db.sql(
        f"""select je.name, je.posting_date, je.company, je.aphvh_th_chu_hang chu_hang, je.aphvh_th_khach khach,
                   je.aphvh_th_tham_chieu tham_chieu, je.aphvh_th_trang_thai trang_thai,
                   je.aphvh_th_ghi_chu_xu_ly ghi_chu, sum(jea.credit - jea.debit) so_tien
            from `tabJournal Entry` je
            join `tabJournal Entry Account` jea on jea.parent = je.name
            join `tabAccount` a on a.name = jea.account
            where {' and '.join(cond)}
            group by je.name order by je.posting_date, je.name""", val, as_dict=True)
    hom_nay = getdate(nowdate())
    data, tong = [], 0.0
    for r in rows:
        r["so_tien"] = flt(r.so_tien)
        r["so_ngay"] = T.so_ngay_cho(getdate(r.posting_date), hom_nay) if r.trang_thai != T.TT_DA_XU_LY else None
        tong += r["so_tien"]
        data.append(r)
    if data:
        data.append({"name": _("Tổng"), "so_tien": tong, "kieu": "tong"})
    return cols, data
