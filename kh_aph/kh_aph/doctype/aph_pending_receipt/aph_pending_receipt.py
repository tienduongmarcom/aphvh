"""Quantity recorded outside available inventory until the price is approved."""
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, flt
from kh_aph.bag_stock import enabled, validate as validate_bags


class APHPendingReceipt(Document):
    def validate(self):
        if not enabled():
            frappe.throw("Chưa bật quy trình nhập chờ định giá")
        if getdate(self.received_date) > getdate(today()):
            frappe.throw("Ngày nhận hàng không được ở tương lai")
        if not self.items:
            frappe.throw("Thiếu hàng nhập")
        for dt, name in (("Company", self.company), ("Supplier", self.supplier)):
            frappe.get_doc(dt, name).check_permission("read")
        if self.is_new():
            if self.get("purchase_receipt") or self.get("valued_by") or self.get("valued_at"):
                frappe.throw("Không được gán trước kết quả định giá")
            self.status = "Chờ định giá"
        for row in self.items:
            item = frappe.get_doc("Item", row.item_code)
            item.check_permission("read")
            warehouse = frappe.get_doc("Warehouse", row.warehouse)
            warehouse.check_permission("read")
            if (warehouse.company != self.company or warehouse.is_group or warehouse.disabled
                    or item.disabled or not item.is_stock_item or item.stock_uom != "Kg" or flt(row.qty) <= 0):
                frappe.throw("Hàng chờ định giá phải là hàng tồn Kg và kho lá đúng company")
        validate_bags(self)
        if not self.is_new():
            old = self.get_doc_before_save()
            if old and any(old.get(f) != self.get(f) for f in
                    ("status", "purchase_receipt", "valued_by", "valued_at", "valuation_reason")):
                frappe.throw("Trạng thái định giá chỉ đổi qua thao tác chốt giá")

    def before_cancel(self):
        if self.purchase_receipt and frappe.db.get_value("Purchase Receipt", self.purchase_receipt, "docstatus") != 2:
            frappe.throw("Đã có phiếu nhập được định giá; xử lý phiếu nhập trước")
