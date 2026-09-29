"""Cài đặt cấu hình của app. Chạy lại được nhiều lần (after_install và after_migrate).

Không dùng fixtures cho các mục này: create_custom_fields và kiểm tra tồn tại giúp mỗi lần
cập nhật app chỉ bổ sung phần thiếu, không ghi đè dữ liệu vận hành.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from aphvh.constants import KG_ENTRY_TYPE

CUSTOM_FIELDS = {
    "Stock Entry": [
        {
            "fieldname": "aphvh_costing_rule",
            "label": "Quy tắc tính giá (APH)",
            "fieldtype": "Data",
            "insert_after": "stock_entry_type",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "description": "Do app tự điền với phiếu Đóng gói theo kg. Phiếu giữ quy tắc này khi tính lại giá.",
        },
    ],
    "Stock Entry Detail": [
        {
            "fieldname": "aphvh_kg_per_unit",
            "label": "Kg / ĐVT tồn kho",
            "fieldtype": "Float",
            "precision": "6",
            "insert_after": "transfer_qty",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
        },
        {
            "fieldname": "aphvh_kg",
            "label": "Số kg tính giá",
            "fieldtype": "Float",
            "precision": "3",
            "insert_after": "aphvh_kg_per_unit",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "in_list_view": 0,
        },
    ],
}


def after_install():
    setup()


def after_migrate():
    setup()


def setup():
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
    ensure_kg_stock_entry_type()


def ensure_kg_stock_entry_type():
    if frappe.db.exists("Stock Entry Type", KG_ENTRY_TYPE):
        return
    doc = frappe.new_doc("Stock Entry Type")
    doc.purpose = "Repack"
    doc.insert(set_name=KG_ENTRY_TYPE, ignore_permissions=True)
