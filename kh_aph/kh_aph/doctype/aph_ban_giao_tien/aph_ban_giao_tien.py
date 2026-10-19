from frappe.model.document import Document
from kh_aph import cash_handover as H


class APHBangiaotien(Document):
    def check_no_back_links_exist(self):
        from kh_aph import factory_handover
        if not factory_handover.checked_cancel_backlinks(self):
            return super().check_no_back_links_exist()

    def validate(self):
        H.validate(self)

    def before_cancel(self):
        H.before_cancel(self)

    def before_update_after_submit(self):
        H.protect(self)

    def on_trash(self):
        H.prevent_delete(self)
