from frappe.model.document import Document
from kh_aph import cash_closing as C


class APHChotcatien(Document):
    def validate(self):
        C.validate(self)

    def before_submit(self):
        C.before_submit(self)

    def before_cancel(self):
        C.prevent_change(self)

    def before_update_after_submit(self):
        C.prevent_change(self)
