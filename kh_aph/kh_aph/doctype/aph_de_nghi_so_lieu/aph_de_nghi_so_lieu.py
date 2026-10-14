from frappe.model.document import Document


class APHDenghisolieu(Document):
    def _dat_loai(self):
        # Đối tượng lấy từ ô Mặt hàng hoặc ô Định mức tùy số liệu.
        from kh_aph.du_lieu import TRUONG
        for d in self.dong:
            if d.truong in TRUONG:
                d.loai_doi_tuong = TRUONG[d.truong][0]
                d.doi_tuong = d.mat_hang if d.loai_doi_tuong == "Item" else d.dinh_muc

    def before_validate(self):
        self._dat_loai()

    def validate(self):
        from kh_aph.du_lieu import validate
        validate(self)
