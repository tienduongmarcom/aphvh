"""Đơn tổng APH (0.3.9): một đơn của khách, nhiều đơn vị bán, dòng có / không xuất hóa đơn.

Xác nhận: tách thành Đơn bán hàng chuẩn — mỗi (đơn vị × có/không hóa đơn) một đơn, gắn ô aphvh_don_tong
(ô này đi theo sang phiếu giao, hóa đơn khi lập từ đơn). Hủy: hủy các đơn con chưa giao, chưa lập hóa đơn.
Tình hình (tinh_hinh): tiền đơn, đã lập hóa đơn, đã thu, còn phải thu — từng đơn con và cả đơn.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt

from aphvh import don_tong_rules as R

F_DON_TONG = "aphvh_don_tong"  # Sales Order / Delivery Note / Sales Invoice / Payment Entry


class DonTongAPH(Document):
    def validate(self):
        for r in self.items:
            if not r.xuat_hoa_don and self.xuat_hd_mac_dinh:
                r.xuat_hoa_don = self.xuat_hd_mac_dinh
            r.amount = flt(r.qty) * flt(r.rate)
            if r.warehouse and frappe.get_cached_value("Warehouse", r.warehouse, "company") != r.cong_ty:
                frappe.throw(f"Dòng {r.idx}: kho {frappe.bold(r.warehouse)} không thuộc đơn vị {frappe.bold(r.cong_ty)}.")
        self.tong_tien_hang = sum(flt(r.amount) for r in self.items)
        if not self.ap_thue and self.customer:
            self.ap_thue = frappe.get_cached_value("Customer", self.customer, "tax_category")
        loi = R.row_problems(self.items)
        if loi:
            frappe.throw("<br>".join(loi), title="Đơn tổng chưa đủ thông tin")

    def on_submit(self):
        made = []
        for (cong_ty, xuat_hd), rows in R.group_rows(self.items):
            so = frappe.get_doc(
                {
                    "doctype": "Sales Order",
                    "company": cong_ty,
                    "customer": self.customer,
                    "transaction_date": self.transaction_date,
                    "delivery_date": self.delivery_date,
                    "aphvh_xuat_hoa_don": xuat_hd,
                    "aphvh_ap_thue": self.ap_thue if xuat_hd == "Có" else None,
                    F_DON_TONG: self.name,
                    "items": [
                        {
                            "item_code": r.item_code,
                            "qty": r.qty,
                            "uom": r.uom,
                            "rate": r.rate,
                            "warehouse": r.warehouse,
                            "delivery_date": self.delivery_date,
                        }
                        for r in rows
                    ],
                }
            )
            if self.ghi_chu and so.meta.has_field("terms"):
                so.terms = self.ghi_chu
            so.insert()
            so.submit()
            for r in rows:
                r.db_set("sales_order", so.name, update_modified=False)
            made.append(so.name)
        frappe.msgprint(
            "Đã tách thành đơn bán hàng: " + ", ".join(frappe.bold(n) for n in made),
            title="Đơn tổng đã xác nhận",
            indicator="green",
        )

    def on_cancel(self):
        names = sorted({r.sales_order for r in self.items if r.sales_order})
        for n in names:
            so = frappe.get_doc("Sales Order", n)
            if so.docstatus != 1:
                continue
            if flt(so.per_delivered) or flt(so.per_billed):
                frappe.throw(
                    f"Đơn bán {frappe.bold(n)} đã giao hoặc đã lập hóa đơn. Hủy phiếu giao / hóa đơn trước, rồi hủy đơn tổng.",
                    title="Không hủy được đơn tổng",
                )
            so.cancel()

    def onload(self):
        if self.docstatus > 0:
            self.set_onload("tinh_hinh", tinh_hinh(self.name))


def _so_names(don_tong: str) -> list:
    return frappe.get_all("Sales Order", {F_DON_TONG: don_tong, "docstatus": 1}, pluck="name", order_by="company, name")


@frappe.whitelist()
def tinh_hinh(name: str) -> dict:
    """Tình hình đơn tổng: từng đơn con (đơn vị × có/không HĐ) và tổng."""
    frappe.has_permission("Don Tong APH", "read", name, throw=True)
    rows = []
    for so_name in _so_names(name):
        so = frappe.db.get_value(
            "Sales Order",
            so_name,
            ["name", "company", "aphvh_xuat_hoa_don", "grand_total", "rounded_total", "per_delivered", "per_billed", "status"],
            as_dict=True,
        )
        sis = frappe.db.sql(
            """select distinct si.name, si.grand_total, si.rounded_total, si.outstanding_amount, si.docstatus
               from `tabSales Invoice` si join `tabSales Invoice Item` i on i.parent = si.name
               where i.sales_order = %s and si.docstatus < 2 and si.is_return = 0""",
            so_name,
            as_dict=True,
        )
        lap = sum(flt(s.rounded_total or s.grand_total) for s in sis if s.docstatus == 1)
        refs = [so_name] + [s.name for s in sis if s.docstatus == 1]
        thu = flt(
            frappe.db.sql(
                """select ifnull(sum(r.allocated_amount), 0) from `tabPayment Entry Reference` r
                   join `tabPayment Entry` p on p.name = r.parent
                   where p.docstatus = 1 and r.reference_name in %s""",
                (tuple(refs),),
            )[0][0]
        )
        tong = flt(so.rounded_total or so.grand_total)
        rows.append(
            {
                "don_ban": so.name,
                "cong_ty": frappe.get_cached_value("Company", so.company, "abbr") or so.company,
                "xuat_hd": cstr(so.aphvh_xuat_hoa_don),
                "tong": tong,
                "da_giao_pt": flt(so.per_delivered),
                "hoa_don": [s.name + ("" if s.docstatus == 1 else " (nháp)") for s in sis],
                "da_lap_hd": lap,
                "da_thu": thu,
                "con_phai_thu": tong - thu,
            }
        )
    return {"don_con": rows, "tong": R.tong_hop(rows)}
