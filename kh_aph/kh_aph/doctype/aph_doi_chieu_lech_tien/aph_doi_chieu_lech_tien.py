from frappe.model.document import Document
from kh_aph import cash_issue as I


class APHDoichieulechtien(Document):
    def validate(self):
        I.validate(self)

    def before_submit(self):
        I.before_submit(self)

    def on_submit(self):
        I.on_submit(self)

    def before_cancel(self):
        I.before_cancel(self)

    def before_update_after_submit(self):
        I.prevent_change(self)
