"""Explicit UAT setup only; no after_migrate/production installation."""
import frappe


def setup_uat():
    if frappe.local.site != "aphvh-web-uat" or frappe.session.user != "Administrator":
        frappe.throw("Thiết lập candidate chỉ cho Administrator trên aphvh-web-uat")
    if not frappe.conf.get("kh_aph_shared_sales_order"):
        frappe.throw("Chưa bật candidate đơn chung trên UAT")
    for name in ("aph_shared_sales_order_item", "aph_shared_sales_order"):
        frappe.reload_doc("kh_aph", "doctype", name)
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({
        "Sales Order": [
            {"fieldname": "kh_aph_shared_order", "label": "Đơn bán chung", "fieldtype": "Link",
             "options": "APH Shared Sales Order", "insert_after": "company", "read_only": 1, "no_copy": 1},
            {"fieldname": "kh_aph_shared_fingerprint", "label": "Dấu vết đơn chung", "fieldtype": "Data",
             "insert_after": "kh_aph_shared_order", "read_only": 1, "hidden": 1, "no_copy": 1}],
        "Sales Order Item": [{"fieldname": "kh_aph_shared_line", "label": "Dòng đơn chung",
                              "fieldtype": "Data", "insert_after": "item_code", "read_only": 1,
                              "hidden": 1, "no_copy": 1}]
    })
