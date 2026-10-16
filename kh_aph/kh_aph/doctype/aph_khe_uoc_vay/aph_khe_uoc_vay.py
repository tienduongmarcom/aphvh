import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class APHKheuocvay(Document):
    def validate(self):
        from lab9x import tien_vay as T
        if flt(self.so_tien) <= 0:
            frappe.throw("Số tiền vay phải lớn hơn 0")
        if flt(self.lai_suat) < 0:
            frappe.throw("Lãi suất không âm")
        if getdate(self.ngay_den_han) <= getdate(self.ngay_vay):
            frappe.throw("Ngày đến hạn phải sau ngày vay")
        tk = frappe.db.get_value("Account", self.tai_khoan, ["company", "account_number", "is_group"], as_dict=True)
        if not tk or tk.company != self.company or tk.is_group or not str(tk.account_number or "").startswith("341"):
            frappe.throw("Tài khoản vay phải là tài khoản chi tiết 341x của đúng đơn vị")
        self.ky_han = T.tai_khoan_vay(self.ngay_vay, self.ngay_den_han)
