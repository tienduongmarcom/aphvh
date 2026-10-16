import frappe
from frappe.model.document import Document


class APHGiasan(Document):
    def validate(self):
        trung = frappe.db.get_value("APH Gia san", {"item_code": self.item_code, "company": self.company or ["in", ["", None]],
                                                   "name": ["!=", self.name]})
        if trung:
            frappe.throw(f"Mặt hàng {self.item_code} đã có giá sàn cho đơn vị này ({trung})")
        if self.gia_san is None or self.gia_san <= 0:
            frappe.throw("Giá sàn phải lớn hơn 0")
