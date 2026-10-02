"""0.4.1: bỏ Đơn tổng và thu tiền gộp (anh Tiến chốt 02/10/2026: tổng hợp nhiều đơn vị chỉ để xem và in
cho khách, không phải nghiệp vụ — giao hàng, thu tiền vẫn tách từng đơn vị). Gỡ cấu hình 0.3.9–0.4.0 khỏi site.

Đơn bán, phiếu giao, hóa đơn, phiếu thu đã lập từ Đơn tổng GIỮ NGUYÊN (là chứng từ chuẩn của từng đơn vị).
"""

import frappe


def execute():
    for dt in ("Sales Order", "Delivery Note", "Sales Invoice", "Payment Entry"):
        name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": "aphvh_don_tong"})
        if name:
            frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
    for doctype, name in (("Print Format", "Phiếu tổng APH"), ("Report", "Cong no don tong APH")):
        if frappe.db.exists(doctype, name):
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Property Setter", {"doc_type": "Don Tong APH"}, pluck="name"):
        frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=True)
    for name in frappe.get_all("Custom DocPerm", {"parent": "Don Tong APH"}, pluck="name"):
        frappe.delete_doc("Custom DocPerm", name, ignore_permissions=True, force=True)
    for src in ("Don Tong APH", "Don Tong APH Item", "Cong no don tong APH"):
        for name in frappe.get_all("Translation", {"source_text": src}, pluck="name"):
            frappe.delete_doc("Translation", name, ignore_permissions=True, force=True)
    for dt in ("Don Tong APH", "Don Tong APH Item"):
        if frappe.db.exists("DocType", dt):
            frappe.delete_doc("DocType", dt, ignore_permissions=True, force=True)
