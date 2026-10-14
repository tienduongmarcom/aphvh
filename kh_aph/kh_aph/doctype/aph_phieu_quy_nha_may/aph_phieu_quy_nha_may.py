"""Phiếu quỹ nhà máy (0.11.1, cờ kh_aph_factory_cash). Nghiệp vụ ở kh_aph/factory_cash.py."""
from frappe.model.document import Document

from kh_aph import factory_cash as F


class APHPhieuquynhamay(Document):
    def validate(self):
        F.validate_phieu(self)

    def on_submit(self):
        F.ghi_so(self)

    def before_cancel(self):
        F.truoc_huy(self)
