"""Khoản mục chi nhỏ tại nhà máy (0.11.1): kế toán trưởng gắn tài khoản và trung tâm chi phí; Dũng chỉ chọn tên."""
from frappe.model.document import Document


class APHKhoanmucchinhamay(Document):
    def validate(self):
        from kh_aph.factory_cash import validate_khoan_muc
        validate_khoan_muc(self)
