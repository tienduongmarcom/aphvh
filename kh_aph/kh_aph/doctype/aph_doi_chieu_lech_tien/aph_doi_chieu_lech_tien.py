from frappe.model.document import Document
from kh_aph import cash_issue as I


class APHDoichieulechtien(Document):
    def get_invalid_links(self, is_submittable=False):
        invalid, cancelled = super().get_invalid_links(is_submittable=is_submittable)
        return invalid, I.cancelled_links(self, cancelled)

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

    def on_trash(self):
        I.prevent_delete(self)
