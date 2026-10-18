from frappe.model.document import Document
from kh_aph import cash_handover as H


class APHBangiaotien(Document):
    def validate(self):
        H.validate(self)

    def before_cancel(self):
        H.before_cancel(self)

    def before_update_after_submit(self):
        H.protect(self)
