from frappe.model.document import Document


class APHSodudaukynguon(Document):
    def validate(self):
        from kh_aph.dau_ky import validate_nguon
        validate_nguon(self)
