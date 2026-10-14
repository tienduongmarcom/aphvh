"""Hàng đợi hóa đơn chờ xuất trên MISA (0.11.3, cờ kh_aph_sales_p1, R093–R098).

Hóa đơn bán đã ghi sổ, khách lấy hóa đơn, chưa có hồ sơ Gốc/Thay thế còn hiệu lực — kèm các hóa đơn đang có người nhận xử lý
(hiện tên người) để không ai làm trùng.
"""

import frappe
from frappe.utils import cint

from kh_aph.constants import INV_FLAG, INV_YES


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not cint(frappe.conf.get("kh_aph_sales_p1")):
        frappe.throw("Tính năng bán hàng 0.11.3 chưa được bật")
    from kh_aph.sales_p1 import HD_HIEU_LUC
    dk = {"docstatus": 1, "is_return": 0, INV_FLAG: INV_YES}
    if filters.company:
        dk["company"] = filters.company
    cols = [
        {"fieldname": "name", "label": "Hóa đơn bán", "fieldtype": "Link", "options": "Sales Invoice", "width": 170},
        {"fieldname": "posting_date", "label": "Ngày", "fieldtype": "Date", "width": 100},
        {"fieldname": "customer", "label": "Khách", "fieldtype": "Link", "options": "Customer", "width": 170},
        {"fieldname": "company", "label": "Đơn vị", "fieldtype": "Link", "options": "Company", "width": 170},
        {"fieldname": "base_grand_total", "label": "Doanh thu quản trị (gồm thuế)", "fieldtype": "Currency", "width": 150},
        {"fieldname": "ho_so", "label": "Hồ sơ đang xử lý", "fieldtype": "Link", "options": "APH Hoa don ngoai", "width": 160},
        {"fieldname": "nguoi_xu_ly", "label": "Người đang xử lý", "fieldtype": "Link", "options": "User", "width": 170},
    ]
    giu = {r.sales_invoice: r for r in frappe.db.sql("""SELECT d.sales_invoice, h.name AS ho_so, h.nguoi_xu_ly,
            h.trang_thai FROM `tabAPH Hoa don ngoai` h JOIN `tabAPH Dong hoa don ngoai` d ON d.parent=h.name
            WHERE h.docstatus<2 AND h.loai IN ('Gốc','Thay thế') AND h.trang_thai IN %s""", (HD_HIEU_LUC,), as_dict=True)}
    rows = []
    for si in frappe.get_list("Sales Invoice", filters=dk, fields=["name", "posting_date", "customer", "company",
                                                                    "base_grand_total"], order_by="posting_date"):
        g = giu.get(si.name)
        if g and g.trang_thai != "Đang xử lý":
            continue  # đã xuất xong
        if g and filters.chi_chua_nhan:
            continue
        rows.append({**si, "ho_so": g.ho_so if g else None, "nguoi_xu_ly": g.nguoi_xu_ly if g else None})
    return cols, rows
