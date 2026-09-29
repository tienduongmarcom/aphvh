"""Cài đặt cấu hình của app. Chạy lại được nhiều lần (after_install và after_migrate).

Không dùng fixtures cho các mục này: create_custom_fields và kiểm tra tồn tại giúp mỗi lần
cập nhật app chỉ bổ sung phần thiếu, không ghi đè dữ liệu vận hành hay chỉnh sửa tay.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from aphvh.constants import (
    DEFAULT_FACTORY_PRICE_GROUPS,
    IG_FACTORY_CAN_PRICE,
    KG_ENTRY_TYPE,
    PR_OPEX,
    PRINT_PURCHASE_RECEIPT,
    PRINT_STOCK_ENTRY,
    REPORT_QTY,
    REPORT_QTY_LABEL,
    ROLE_FACTORY,
)

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
    "Item Group": [
        {
            "fieldname": IG_FACTORY_CAN_PRICE,
            "label": "Nhà máy tự nhập giá",
            "fieldtype": "Check",
            "insert_after": "is_group",
            "description": "Tích cho nhóm vật tư vận hành (than, củi, phụ tùng…): kế toán nhà máy "
            "được xem và nhập giá khi nhận hàng. Nhóm con được áp dụng theo.",
        },
    ],
    "Purchase Receipt": [
        {
            "fieldname": PR_OPEX,
            "label": "Phiếu nhập vật tư vận hành",
            "fieldtype": "Check",
            "insert_after": "supplier",
            "print_hide": 1,
            "description": "Tích khi nhập vật tư vận hành (nhóm hàng được tích 'Nhà máy tự nhập giá'). "
            "Không tích: nguyên phụ liệu, nhận từ đơn mua do kế toán trưởng lập.",
        },
    ],
}

# Quyền của vai trò kế toán nhà máy. Không có "report"/"export" trên phiếu (không xem dạng bảng,
# không xuất Excel); không có quyền trên Stock Ledger Entry, Bin, sổ cái, báo cáo giá trị kho.
_DOC = {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "delete": 1, "print": 1}
ROLE_FACTORY_PERMS = {
    "Purchase Receipt": _DOC,
    "Stock Entry": _DOC,
    "Serial and Batch Bundle": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "delete": 1},
    "Batch": {"read": 1, "write": 1, "create": 1},
    "Lo Nhap Khau": {"read": 1, "write": 1, "create": 1},
    "Purchase Order": {"read": 1},
    "Item": {"read": 1},
    "Warehouse": {"read": 1, "report": 1},
    "Supplier": {"read": 1},
    "Stock Entry Type": {"read": 1},
    "UOM": {"read": 1},
    "Item Group": {"read": 1},
    "Brand": {"read": 1},
    "Company": {"read": 1},
    "Terms and Conditions": {"read": 1},
    "Account": {"select": 1},
    "Cost Center": {"select": 1},
    "Project": {"select": 1},
    # Màn hình phiếu nhập, phiếu kho đọc các cài đặt này (không chứa giá)
    "Stock Settings": {"read": 1},
    "Buying Settings": {"read": 1},
}

# Mọi loại quyền của một dòng Custom DocPerm. Dòng mới mặc định read=1, export=1 nên phải đặt
# rõ từng loại, không để giá trị mặc định.
PTYPES = (
    "select", "read", "write", "create", "delete", "submit", "cancel", "amend",
    "report", "export", "import", "share", "print", "email",
)

DEFAULT_PRINT_FORMATS = {
    "Purchase Receipt": PRINT_PURCHASE_RECEIPT,
    "Stock Entry": PRINT_STOCK_ENTRY,
}

TRANSLATIONS = {REPORT_QTY: REPORT_QTY_LABEL}


def after_install():
    setup()


def after_migrate():
    setup()


def before_migrate():
    ensure_role()


def setup():
    ensure_role()
    new_ig_field = not frappe.db.exists("Custom Field", {"dt": "Item Group", "fieldname": IG_FACTORY_CAN_PRICE})
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
    if new_ig_field:
        flag_default_factory_price_groups()
    ensure_kg_stock_entry_type()
    ensure_role_permissions()
    ensure_default_print_formats()
    ensure_translations()


def ensure_role():
    if frappe.db.exists("Role", ROLE_FACTORY):
        return
    role = frappe.new_doc("Role")
    role.role_name = ROLE_FACTORY
    role.desk_access = 1
    role.insert(ignore_permissions=True)


def flag_default_factory_price_groups():
    for group in DEFAULT_FACTORY_PRICE_GROUPS:
        if frappe.db.exists("Item Group", group):
            frappe.db.set_value("Item Group", group, IG_FACTORY_CAN_PRICE, 1, update_modified=False)


def ensure_kg_stock_entry_type():
    if frappe.db.exists("Stock Entry Type", KG_ENTRY_TYPE):
        return
    doc = frappe.new_doc("Stock Entry Type")
    doc.purpose = "Repack"
    doc.insert(set_name=KG_ENTRY_TYPE, ignore_permissions=True)


def ensure_role_permissions():
    """Tạo quyền cho vai trò nhà máy trên từng loại chứng từ, chỉ khi chưa có.

    Đã có dòng quyền (kể cả đã được chỉnh tay trong Role Permission Manager) thì giữ nguyên.
    Lần đầu thêm quyền cho một loại chứng từ, Frappe chép quyền chuẩn sang quyền tùy chỉnh
    (giống thao tác trong Role Permission Manager); quyền của các vai trò khác không đổi.
    """
    from frappe.permissions import add_permission

    for doctype, rights in ROLE_FACTORY_PERMS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": ROLE_FACTORY, "permlevel": 0}):
            continue
        add_permission(doctype, ROLE_FACTORY, 0, next(iter(rights)))
        set_factory_role_rights(doctype, rights)


def set_factory_role_rights(doctype: str, rights: dict):
    """Đặt đúng từng loại quyền của vai trò nhà máy trên một loại chứng từ (quyền không nêu = 0)."""
    from frappe.permissions import update_permission_property

    for ptype in PTYPES:
        update_permission_property(doctype, ROLE_FACTORY, 0, ptype, rights.get(ptype, 0), validate=False)
    frappe.clear_cache(doctype=doctype)


def ensure_default_print_formats():
    for doctype, print_format in DEFAULT_PRINT_FORMATS.items():
        if not frappe.db.exists("Print Format", print_format):
            continue
        if frappe.db.exists(
            "Property Setter",
            {"doc_type": doctype, "property": "default_print_format", "doctype_or_field": "DocType"},
        ):
            continue
        frappe.make_property_setter(
            {
                "doctype": doctype,
                "doctype_or_field": "DocType",
                "property": "default_print_format",
                "value": print_format,
                "property_type": "Data",
            },
            validate_fields_for_doctype=False,
        )


def ensure_translations():
    for source, target in TRANSLATIONS.items():
        if frappe.db.exists("Translation", {"language": "vi", "source_text": source}):
            continue
        frappe.get_doc(
            {"doctype": "Translation", "language": "vi", "source_text": source, "translated_text": target}
        ).insert(ignore_permissions=True)
