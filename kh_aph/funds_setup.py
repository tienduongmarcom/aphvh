"""Explicit schema configuration only; never runs from install/migrate hooks."""
import frappe


def setup():
    if frappe.session.user != "Administrator" or frappe.local.site != "aphvh-web-uat":
        frappe.throw("Cấu hình ứng viên chỉ trên UAT cô lập")
    schema()


def schema():
    """Phần schema dùng chung cho UAT và bộ cài production (kh_aph.cai_dat_tinh_nang); không tự kiểm site."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({"Journal Entry": [
        {"fieldname": "kh_aph_funds_receipt", "label": "Khoản tiền thực nhận",
         "fieldtype": "Link", "options": "APH Funds Receipt", "read_only": 1,
         "no_copy": 1, "insert_after": "user_remark"},
        {"fieldname": "kh_aph_funds_action", "label": "Kế hoạch cọc/phân bổ/hoàn",
         "fieldtype": "Link", "options": "APH Funds Action", "read_only": 1,
         "no_copy": 1, "insert_after": "kh_aph_funds_receipt"},
    ]})
