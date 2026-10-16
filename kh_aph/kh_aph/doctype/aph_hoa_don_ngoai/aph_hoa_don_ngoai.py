from frappe.model.document import Document


class APHHoadonngoai(Document):
    def validate(self):
        from kh_aph.sales_p1 import validate_hoa_don_ngoai
        validate_hoa_don_ngoai(self)

    def on_submit(self):
        from kh_aph.sales_p1 import submit_hoa_don_ngoai
        submit_hoa_don_ngoai(self)

    def on_cancel(self):
        from kh_aph.sales_p1 import cancel_hoa_don_ngoai
        cancel_hoa_don_ngoai(self)
