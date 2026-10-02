"""Cài đặt cấu hình của app. Chạy lại được nhiều lần (after_install và after_migrate).

Không dùng fixtures cho các mục này: create_custom_fields và kiểm tra tồn tại giúp mỗi lần
cập nhật app chỉ bổ sung phần thiếu, không ghi đè dữ liệu vận hành hay chỉnh sửa tay.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from aphvh.constants import (
    CCL_WARN_LIMIT,
    DEFAULT_FACTORY_PRICE_GROUPS,
    DN_CARRIER,
    DN_DRIVER,
    DN_DRIVER_PHONE,
    DN_MODE,
    DN_MODE_HIRED,
    DN_MODE_PICKUP,
    DN_PLATE,
    DN_RECEIVER,
    IG_FACTORY_CAN_PRICE,
    IG_FIXED_RATE,
    INV_FLAG,
    INV_NO,
    INV_YES,
    KG_ENTRY_TYPE,
    PR_OPEX,
    PRINT_DN_ISSUE,
    PRINT_PAYMENT,
    PRINT_SALES_INVOICE,
    PE_PERSON,
    PRINT_PURCHASE_RECEIPT,
    PRINT_STOCK_ENTRY,
    REPORT_INVOICED,
    REPORT_INVOICED_LABEL,
    REPORT_QTY,
    REPORT_QTY_LABEL,
    ROLE_FACTORY,
    ROLE_HN_STOCK,
    ROLE_SALES,
    SI_AUTO,
    SI_EINV_DATE,
    SI_EINV_NO,
    SED_FIXED_RATE,
    SI_EINV_SERIES,
    SO_BELOW_PRICE,
    SO_OVER_LIMIT,
    SO_WARNING,
    SS_AUTO_INVOICE,
    SS_WARN_CREDIT,
    SS_WARN_PRICE,
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
        {
            "fieldname": SED_FIXED_RATE,
            "label": "Giá cố định (phế, dở dang)",
            "fieldtype": "Check",
            "insert_after": "aphvh_kg",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "description": "App tự đánh dấu theo nhóm hàng khi lưu phiếu Đóng gói theo kg (quy tắc kg-v2).",
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
        {
            "fieldname": IG_FIXED_RATE,
            "label": "Giá cố định trên phiếu chia theo kg",
            "fieldtype": "Check",
            "insert_after": IG_FACTORY_CAN_PRICE,
            "description": "Tích cho nhóm phế phẩm, dở dang: trên phiếu Đóng gói theo kg, dòng đầu ra thuộc nhóm "
            "này lấy đơn giá kế toán nhập; phần giá trị còn lại chia theo kg cho thành phẩm. Nhóm con áp dụng theo.",
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

# --- 0.3.1: có / không xuất hóa đơn GTGT ---------------------------------------------------

_INV_OPTIONS = f"\n{INV_YES}\n{INV_NO}"
_INV_DOC_FIELD = {
    "fieldname": INV_FLAG,
    "label": "Xuất hóa đơn GTGT",
    "fieldtype": "Select",
    "options": _INV_OPTIONS,
    "insert_after": "customer_name",
    # Bắt buộc với khách thường; bỏ qua với khách nội bộ và hóa đơn đầu kỳ (công nợ đầu kỳ).
    "mandatory_depends_on": "eval:!doc.is_internal_customer && doc.is_opening!='Yes'",
    "in_list_view": 1,
    "in_standard_filter": 1,
    "print_hide": 1,
    "description": "Có: tính thuế GTGT theo mặt hàng, kế toán xuất hóa đơn trên MISA. "
    "Không: không tính thuế, khách trả đúng tiền hàng. Lấy theo mặc định của khách, sửa được trên từng chứng từ.",
}

INVOICE_CUSTOM_FIELDS = {
    "Customer": [
        {
            "fieldname": INV_FLAG,
            "label": "Xuất hóa đơn GTGT (mặc định)",
            "fieldtype": "Select",
            "options": _INV_OPTIONS,
            "insert_after": "tax_category",
            "in_standard_filter": 1,
            "description": "Mặc định cho đơn mới của khách. Để trống thì người lập đơn chọn trên từng đơn.",
        },
    ],
    "Sales Order": [dict(_INV_DOC_FIELD)],
    "Delivery Note": [dict(_INV_DOC_FIELD)],
    "Sales Invoice": [
        dict(_INV_DOC_FIELD),
        {
            "fieldname": "aphvh_hddt_section",
            "label": "Hóa đơn điện tử đã xuất (MISA)",
            "fieldtype": "Section Break",
            "insert_after": "amended_from",
            "depends_on": f"eval:doc.{INV_FLAG}=='{INV_YES}'",
            "collapsible": 0,
        },
        {
            "fieldname": SI_EINV_SERIES,
            "label": "Ký hiệu hóa đơn",
            "fieldtype": "Data",
            "insert_after": "aphvh_hddt_section",
            "allow_on_submit": 1,
            "no_copy": 1,
            "print_hide": 1,
        },
        {"fieldname": "aphvh_hddt_col", "fieldtype": "Column Break", "insert_after": SI_EINV_SERIES},
        {
            "fieldname": SI_EINV_NO,
            "label": "Số hóa đơn",
            "fieldtype": "Data",
            "insert_after": "aphvh_hddt_col",
            "allow_on_submit": 1,
            "no_copy": 1,
            "print_hide": 1,
            "in_standard_filter": 1,
            "search_index": 1,
        },
        {"fieldname": "aphvh_hddt_col2", "fieldtype": "Column Break", "insert_after": SI_EINV_NO},
        {
            "fieldname": SI_EINV_DATE,
            "label": "Ngày hóa đơn",
            "fieldtype": "Date",
            "insert_after": "aphvh_hddt_col2",
            "allow_on_submit": 1,
            "no_copy": 1,
            "print_hide": 1,
            "description": "Kế toán ghi sau khi xuất hóa đơn điện tử trên MISA (ghi được cả khi hóa đơn đã xác nhận).",
        },
    ],
}

# --- 0.3: luồng bán hàng kho Hà Nội ------------------------------------------------------

_DN_HIRED = f"eval:doc.{DN_MODE}=='{DN_MODE_HIRED}'"
_TRANSPORT = {"allow_on_submit": 1, "print_hide": 1, "no_copy": 1}

SALES_CUSTOM_FIELDS = {
    "Customer Credit Limit": [
        {
            "fieldname": CCL_WARN_LIMIT,
            "label": "Hạn mức cảnh báo",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "insert_after": "company",
            "in_list_view": 1,
            "columns": 3,
            "description": "Công nợ tính cả đơn mới vượt mức này thì cảnh báo khi lập đơn, không chặn. "
            "Khách không đặt thì theo nhóm khách.",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "aphvh_canh_bao_section",
            "label": "Cảnh báo khi lập đơn",
            "fieldtype": "Section Break",
            "insert_after": "amended_from",
            "depends_on": f"eval:doc.{SO_OVER_LIMIT} || doc.{SO_BELOW_PRICE}",
        },
        {
            "fieldname": SO_OVER_LIMIT,
            "label": "Vượt hạn mức hoặc có nợ quá hạn",
            "fieldtype": "Check",
            "insert_after": "aphvh_canh_bao_section",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "in_standard_filter": 1,
        },
        {
            "fieldname": SO_BELOW_PRICE,
            "label": "Có dòng giá thấp hơn bảng giá",
            "fieldtype": "Check",
            "insert_after": SO_OVER_LIMIT,
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "in_standard_filter": 1,
        },
        {"fieldname": "aphvh_canh_bao_col", "fieldtype": "Column Break", "insert_after": SO_BELOW_PRICE},
        {
            "fieldname": SO_WARNING,
            "label": "Nội dung cảnh báo",
            "fieldtype": "Small Text",
            "insert_after": "aphvh_canh_bao_col",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
        },
    ],
    "Delivery Note": [
        {
            "fieldname": "aphvh_giao_nhan_section",
            "label": "Giao nhận",
            "fieldtype": "Section Break",
            "insert_after": "return_against",
        },
        {
            "fieldname": DN_MODE,
            "label": "Hình thức giao",
            "fieldtype": "Select",
            "options": f"\n{DN_MODE_PICKUP}\n{DN_MODE_HIRED}",
            "insert_after": "aphvh_giao_nhan_section",
            **_TRANSPORT,
        },
        {
            "fieldname": DN_RECEIVER,
            "label": "Người nhận hàng bên khách",
            "fieldtype": "Data",
            "insert_after": DN_MODE,
            "description": "In lên phiếu xuất kho và biên bản giao nhận. Phiếu nhận hàng trả lại: người mang hàng trả.",
            **_TRANSPORT,
        },
        {"fieldname": "aphvh_giao_nhan_col", "fieldtype": "Column Break", "insert_after": DN_RECEIVER},
        {
            "fieldname": DN_CARRIER,
            "label": "Nhà xe",
            "fieldtype": "Data",
            "insert_after": "aphvh_giao_nhan_col",
            "depends_on": _DN_HIRED,
            **_TRANSPORT,
        },
        {
            "fieldname": DN_DRIVER,
            "label": "Lái xe",
            "fieldtype": "Data",
            "insert_after": DN_CARRIER,
            "depends_on": _DN_HIRED,
            **_TRANSPORT,
        },
        {"fieldname": "aphvh_giao_nhan_col2", "fieldtype": "Column Break", "insert_after": DN_DRIVER},
        {
            "fieldname": DN_PLATE,
            "label": "Biển số xe",
            "fieldtype": "Data",
            "insert_after": "aphvh_giao_nhan_col2",
            "depends_on": _DN_HIRED,
            **_TRANSPORT,
        },
        {
            "fieldname": DN_DRIVER_PHONE,
            "label": "SĐT lái xe",
            "fieldtype": "Data",
            "insert_after": DN_PLATE,
            "depends_on": _DN_HIRED,
            **_TRANSPORT,
        },
    ],
    "Sales Invoice": [
        {
            "fieldname": SI_AUTO,
            "label": "Tự tạo từ phiếu giao hàng",
            "fieldtype": "Check",
            "insert_after": "is_return",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "in_standard_filter": 1,
        },
    ],
    "Selling Settings": [
        {
            "fieldname": "aphvh_ban_hang_section",
            "label": "An Phú Hưng – luồng bán hàng",
            "fieldtype": "Section Break",
            "insert_after": "blanket_order_allowance",
        },
        {
            "fieldname": SS_AUTO_INVOICE,
            "label": "Tự tạo hóa đơn nháp khi xác nhận phiếu giao hàng",
            "fieldtype": "Check",
            "insert_after": "aphvh_ban_hang_section",
            "description": "Cả hóa đơn trả lại khi nhận hàng trả lại. Kế toán kiểm tra rồi xác nhận hóa đơn.",
        },
        {
            "fieldname": SS_WARN_CREDIT,
            "label": "Cảnh báo công nợ trên đơn bán hàng",
            "fieldtype": "Check",
            "insert_after": SS_AUTO_INVOICE,
            "description": "Vượt hạn mức cảnh báo (của khách hoặc nhóm khách) hoặc có nợ quá hạn. Không chặn.",
        },
        {
            "fieldname": SS_WARN_PRICE,
            "label": "Cảnh báo giá bán thấp hơn bảng giá",
            "fieldtype": "Check",
            "insert_after": SS_WARN_CREDIT,
            "description": "Nhân viên bán hàng vẫn sửa giá tự do; chỉ cảnh báo và đánh dấu đơn.",
        },
    ],
}

# Bật sẵn lần đầu tạo ô (Frappe không lấy giá trị mặc định cho ô của Single).
SELLING_SETTINGS_ON = (SS_AUTO_INVOICE, SS_WARN_CREDIT, SS_WARN_PRICE)

# Hạn mức tín dụng chuẩn của ERPNext CHẶN xác nhận đơn/hóa đơn khi vượt; công ty chỉ muốn cảnh báo,
# nên ẩn các cột chuẩn trên bảng hạn mức (Customize Form mở lại được).
HIDDEN_STANDARD_FIELDS = {
    "Customer Credit Limit": ("credit_limit", "overdue_billing_threshold", "bypass_credit_limit_check"),
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

# Quyền 0.3. Vai trò bán hàng và thủ kho chỉ đọc danh mục; không có "report"/"export" (không xem
# dạng bảng, không xuất Excel); không có quyền trên sổ cái, báo cáo giá trị kho, hóa đơn.
_READ = {"read": 1}
_SALES_MASTERS = {
    "Customer": _READ,
    "Item": _READ,
    "Price List": _READ,
    "UOM": _READ,
    "Item Group": _READ,
    "Brand": _READ,
    "Company": _READ,
    "Currency": _READ,
    "Territory": _READ,
    "Customer Group": _READ,
    "Address": _READ,
    "Contact": _READ,
    "Sales Taxes and Charges Template": _READ,
    "Item Tax Template": _READ,
    "Tax Category": _READ,
    "Payment Terms Template": _READ,
    "Terms and Conditions": _READ,
    "Batch": _READ,
    "Letter Head": _READ,
    "Print Heading": _READ,
    "Warehouse": {"read": 1, "report": 1},
    "Selling Settings": _READ,
    "Stock Settings": _READ,
    "Accounts Settings": _READ,
    "Account": {"select": 1},
    "Cost Center": {"select": 1},
    "Project": {"select": 1},
}
ROLE_SALES_PERMS = {
    **_SALES_MASTERS,
    "Sales Order": _DOC,
    "Delivery Note": {"read": 1, "print": 1},
    "Item Price": _READ,  # chỉ bảng giá bán (price_visibility.item_price_query_conditions)
    "Sales Person": _READ,
    "Serial and Batch Bundle": _READ,
}
ROLE_HN_STOCK_PERMS = {
    **_SALES_MASTERS,
    "Delivery Note": _DOC,
    "Sales Order": {"read": 1, "print": 1},
    "Serial and Batch Bundle": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "delete": 1},
    "Stock Entry": {"read": 1, "print": 1},
    "Stock Entry Type": _READ,
}
ROLE_PERMS = {
    ROLE_FACTORY: ROLE_FACTORY_PERMS,
    ROLE_SALES: ROLE_SALES_PERMS,
    ROLE_HN_STOCK: ROLE_HN_STOCK_PERMS,
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
    "Delivery Note": PRINT_DN_ISSUE,
    "Payment Entry": PRINT_PAYMENT,
    "Sales Invoice": PRINT_SALES_INVOICE,
}

TRANSLATIONS = {
    REPORT_QTY: REPORT_QTY_LABEL,
    REPORT_INVOICED: REPORT_INVOICED_LABEL,
    "Tong hop ban hang theo khach APH": "Tổng hợp bán hàng theo khách (3 đơn vị)",
    # 0.4.3: hộp Cài đặt in — bản dịch sẵn có của ERPNext dịch máy ("Phong cảnh", "Định hướng").
    "So doanh thu HKD": "Sổ doanh thu hộ kinh doanh (S1a, S2a, S2b)",
    "So ke toan HKD": "Sổ kế toán hộ kinh doanh (S2c, S2d, S2e)",
    "Orientation": "Hướng giấy",
    "Landscape": "Ngang",
    "Portrait": "Dọc",
    "With Letter Head": "Kèm tiêu đề công ty",
    "Print Format": "Mẫu in",
}


# --- 0.3.4: kiểm soát sau đợt kiểm thử 8086 ------------------------------------------------

_BUYER_FIELDS = [
    {"fieldname": "aphvh_ten_nguoi_mua", "label": "Tên người mua (khách lẻ)", "fieldtype": "Data", "insert_after": "customer_name",
     "description": "Ghi khi bán cho khách vãng lai chung: tên người mua thực tế. Không thay tên khách trên hóa đơn."},
    {"fieldname": "aphvh_sdt_nguoi_mua", "label": "SĐT người mua", "fieldtype": "Data", "options": "Phone", "insert_after": "aphvh_ten_nguoi_mua"},
]
# 0.3.5: lý do app phân loại loại thuế của khách (kế toán xem để rà soát).
_AP_THUE_FIELD = {
    "fieldname": "aphvh_ap_thue",
    "label": "Áp thuế theo",
    "fieldtype": "Select",
    "options": "\nDoanh nghiệp/HTX\nHộ KD/cá nhân",
    "insert_after": INV_FLAG,
    "depends_on": f"eval:doc.{INV_FLAG}=='{INV_YES}'",
    "in_standard_filter": 1,
    "print_hide": 1,
    "description": "Bán cho công ty/HTX: nông sản Không kê khai tính nộp. Bán cho hộ KD/cá nhân: 5%. "
    "Tự lấy theo loại của khách; kế toán bán hàng đổi được trên từng chứng từ (theo người mua ghi trên hóa đơn).",
}

VAT_CUSTOM_FIELDS = {
    # 0.3.7: tên người nộp / nhận tiền in trên phiếu thu, phiếu chi (trống thì in tên đối tượng).
    "Payment Entry": [
        {
            "fieldname": PE_PERSON,
            "label": "Người nộp / nhận tiền",
            "fieldtype": "Data",
            "insert_after": "party_name",
            "description": "Người thực tế nộp hoặc nhận tiền, in trên phiếu thu / phiếu chi. Trống thì in tên khách / nhà cung cấp.",
        },
    ],
    "Sales Order": [dict(_AP_THUE_FIELD)],
    "Delivery Note": [dict(_AP_THUE_FIELD)],
    "Sales Invoice": [dict(_AP_THUE_FIELD)],
    "Customer": [
        {
            "fieldname": "aphvh_ly_do_loai_thue",
            "label": "Lý do phân loại loại thuế",
            "fieldtype": "Data",
            "insert_after": "tax_category",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
            "description": "App tự ghi khi tự phân loại Doanh nghiệp/HTX hay Hộ KD/cá nhân theo MST và tên. "
            "Kế toán đổi Loại thuế nếu sai; app không ghi đè.",
        },
    ],
}

# 0.4.5: ngành nghề hộ kinh doanh theo nhóm hàng (sổ S2a/S2b-HKD, tỷ lệ thuế theo NĐ 68/2026).
def _nganh_options():
    from aphvh.so_hkd_rules import NGANH

    return "\n" + "\n".join(n for n, _, _ in NGANH)


HKD_CUSTOM_FIELDS = {
    "Item Group": [
        {
            "fieldname": "aphvh_nganh_hkd",
            "label": "Ngành nghề (sổ hộ kinh doanh)",
            "fieldtype": "Select",
            "options": _nganh_options(),
            "insert_after": "parent_item_group",
            "description": "Dùng cho sổ doanh thu S2a/S2b-HKD của hộ kinh doanh. Trống: theo nhóm cha; "
            "không nhóm nào đặt thì là Phân phối, cung cấp hàng hóa (1% GTGT, 0,5% TNCN).",
        }
    ],
}

# 0.4.8: chi phí không hợp lý — vẫn ghi sổ đầy đủ, kế toán tích để loại khỏi mục (2) sổ S2c-HKD.
# Sửa được cả khi chứng từ đã xác nhận (allow_on_submit). Đặt trên cả chứng từ: chứng từ lẫn khoản hợp lệ
# và không hợp lệ thì tách thành hai chứng từ.
F_CP_KHL = "aphvh_cp_khong_hop_ly"
F_CP_KHL_LY_DO = "aphvh_ly_do_cp_khl"
CP_KHL_DOCTYPES = {"Journal Entry": "user_remark", "Purchase Invoice": "remarks", "Payment Entry": "remarks",
                   "Expense Claim": "remark"}


def _cp_khl_fields(after):
    return [
        {"fieldname": F_CP_KHL, "label": "Chi phí không hợp lý (loại khỏi sổ S2c-HKD)", "fieldtype": "Check",
         "insert_after": after, "allow_on_submit": 1, "no_copy": 1,
         "description": "Chỉ dùng cho hộ kinh doanh nộp thuế theo thu nhập. Chi phí vẫn ghi sổ; sổ S2c không trừ khoản này khi tính thuế TNCN."},
        {"fieldname": F_CP_KHL_LY_DO, "label": "Lý do không hợp lý", "fieldtype": "Small Text", "insert_after": F_CP_KHL,
         "allow_on_submit": 1, "no_copy": 1, "depends_on": f"eval:doc.{F_CP_KHL}", "mandatory_depends_on": f"eval:doc.{F_CP_KHL}"},
    ]


def cp_khl_custom_fields() -> dict:
    return {dt: _cp_khl_fields(after) for dt, after in CP_KHL_DOCTYPES.items() if frappe.db.exists("DocType", dt)}


CONTROL_CUSTOM_FIELDS = {
    "Customer": [
        {"fieldname": "aphvh_khach_chung", "label": "Khách vãng lai chung", "fieldtype": "Check", "insert_after": "customer_type",
         "description": "Mã dùng chung cho khách lẻ không để lại thông tin. Chỉ được bán thu tiền ngay; khách mua nợ phải có mã riêng."},
    ],
    "Sales Invoice": [
        *[dict(f) for f in _BUYER_FIELDS],
        {"fieldname": "aphvh_thu_ngay_tk", "label": "Thu tiền ngay vào tài khoản", "fieldtype": "Link", "options": "Account",
         "insert_after": "aphvh_sdt_nguoi_mua",
         "description": "Chọn tiền mặt hoặc ngân hàng: khi xác nhận hóa đơn, hệ thống tự lập phiếu thu đủ tiền. Bắt buộc với khách vãng lai chung."},
    ],
    "Sales Order": [dict(f) for f in _BUYER_FIELDS],
    "Delivery Note": [dict(f) for f in _BUYER_FIELDS],
}


def ensure_frozen_party_modifier():
    """Kế toán trưởng (Accounts Manager) được ghi sổ với khách/NCC đã khóa và vào kỳ đã khóa sổ — để xóa nợ (J14).

    ERPNext v16 đọc vai trò này ở Company.role_allowed_for_frozen_entries. Chỉ đặt khi công ty chưa đặt.
    """
    if not frappe.get_meta("Company").has_field("role_allowed_for_frozen_entries"):
        return
    for co in frappe.get_all("Company", filters={"role_allowed_for_frozen_entries": ["in", ["", None]]}, pluck="name"):
        frappe.db.set_value("Company", co, "role_allowed_for_frozen_entries", "Accounts Manager")


def after_install():
    setup()


def after_migrate():
    setup()


def before_migrate():
    ensure_role()


def setup():
    ensure_role()
    new_ig_field = not frappe.db.exists("Custom Field", {"dt": "Item Group", "fieldname": IG_FACTORY_CAN_PRICE})
    new_ss_fields = [
        f for f in SELLING_SETTINGS_ON if not frappe.db.exists("Custom Field", {"dt": "Selling Settings", "fieldname": f})
    ]
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
    create_custom_fields(SALES_CUSTOM_FIELDS, ignore_validate=True, update=True)
    create_custom_fields(INVOICE_CUSTOM_FIELDS, ignore_validate=True, update=True)
    create_custom_fields(CONTROL_CUSTOM_FIELDS, ignore_validate=True, update=True)
    create_custom_fields(VAT_CUSTOM_FIELDS, ignore_validate=True, update=True)
    create_custom_fields(HKD_CUSTOM_FIELDS, ignore_validate=True, update=True)
    create_custom_fields(cp_khl_custom_fields(), ignore_validate=True, update=True)
    ensure_frozen_party_modifier()
    from aphvh.vat import setup_defaults

    setup_defaults()
    if new_ig_field:
        flag_default_factory_price_groups()
    for fieldname in new_ss_fields:
        frappe.db.set_single_value("Selling Settings", fieldname, 1)
    ensure_kg_stock_entry_type()
    ensure_role_permissions()
    hide_standard_fields()
    ensure_default_print_formats()
    ensure_translations()


def ensure_role():
    """Tạo các vai trò của app (chạy cả trước migrate để báo cáo chuẩn nạp được danh sách vai trò)."""
    for name in ROLE_PERMS:
        if frappe.db.exists("Role", name):
            continue
        role = frappe.new_doc("Role")
        role.role_name = name
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
    """Tạo quyền cho các vai trò của app trên từng loại chứng từ, chỉ khi chưa có.

    Đã có dòng quyền (kể cả đã được chỉnh tay trong Role Permission Manager) thì giữ nguyên.
    Lần đầu thêm quyền cho một loại chứng từ, Frappe chép quyền chuẩn sang quyền tùy chỉnh
    (giống thao tác trong Role Permission Manager); quyền của các vai trò khác không đổi.
    """
    from frappe.permissions import add_permission

    for role, perms in ROLE_PERMS.items():
        for doctype, rights in perms.items():
            if not frappe.db.exists("DocType", doctype):
                continue
            if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
                continue
            add_permission(doctype, role, 0, next(iter(rights)))
            set_role_rights(doctype, role, rights)


def set_role_rights(doctype: str, role: str, rights: dict):
    """Đặt đúng từng loại quyền của một vai trò trên một loại chứng từ (quyền không nêu = 0)."""
    from frappe.permissions import update_permission_property

    for ptype in PTYPES:
        update_permission_property(doctype, role, 0, ptype, rights.get(ptype, 0), validate=False)
    frappe.clear_cache(doctype=doctype)


def set_factory_role_rights(doctype: str, rights: dict):
    """Giữ cho bản vá 0.2.1 (normalize_factory_role_perms)."""
    set_role_rights(doctype, ROLE_FACTORY, rights)


def hide_standard_fields():
    """Ẩn cột chuẩn không dùng (chỉ lần đầu; đã có tùy chỉnh thì giữ nguyên).

    Cột nào đang có số liệu (vd. đã đặt hạn mức tín dụng chuẩn — ERPNext vẫn chặn theo số đó) thì
    KHÔNG ẩn, để người dùng thấy và xóa; in cảnh báo khi migrate.
    """
    for doctype, fields in HIDDEN_STANDARD_FIELDS.items():
        for fieldname in fields:
            if not frappe.get_meta(doctype).has_field(fieldname):
                continue
            in_use = frappe.get_all(doctype, filters={fieldname: [">", 0]}, fields=["parenttype", "parent"], limit=20)
            if in_use:
                print(
                    f"aphvh: KHÔNG ẩn {doctype}.{fieldname} vì đang có số liệu (ERPNext vẫn chặn theo số này): "
                    + ", ".join(f"{r.parenttype} {r.parent}" for r in in_use)
                )
                continue
            if frappe.db.exists(
                "Property Setter", {"doc_type": doctype, "field_name": fieldname, "property": "hidden"}
            ):
                continue
            for prop, value in (("hidden", "1"), ("in_list_view", "0")):
                frappe.make_property_setter(
                    {
                        "doctype": doctype,
                        "doctype_or_field": "DocField",
                        "fieldname": fieldname,
                        "property": prop,
                        "value": value,
                        "property_type": "Check",
                    },
                    validate_fields_for_doctype=False,
                )


def reload_print_formats():
    """Nạp lại mọi mẫu in của app từ mã nguồn (force): Frappe chỉ tự nạp khi "modified" mới hơn,
    sửa mẫu mà quên tăng mốc thì site giữ bản cũ (lỗi gặp ở 0.3.7)."""
    import os

    base = os.path.join(os.path.dirname(__file__), "aph_vh", "print_format")
    for folder in sorted(os.listdir(base)):
        if os.path.isfile(os.path.join(base, folder, f"{folder}.json")):
            frappe.reload_doc("aph_vh", "print_format", folder, force=True)


def ensure_default_print_formats():
    """Đặt mẫu in mặc định của app, trừ khi đã có người chọn mẫu khác.

    Mẫu "<chứng từ> with Item Image" do ERPNext tự đặt lúc cài thì coi như chưa chọn.
    """
    reload_print_formats()
    for doctype, print_format in DEFAULT_PRINT_FORMATS.items():
        if not frappe.db.exists("Print Format", print_format):
            continue
        current = frappe.db.get_value(
            "Property Setter",
            {"doc_type": doctype, "property": "default_print_format", "doctype_or_field": "DocType"},
            "value",
        )
        if current and current != f"{doctype} with Item Image":
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

# Bản dịch cũ được phép thay bằng bản trong TRANSLATIONS (nếu site đang lưu đúng chữ cũ này).
OLD_TRANSLATIONS = {"Orientation": ("Định hướng",), "Landscape": ("Phong cảnh",), "Portrait": ("Chân dung",)}


def ensure_translations():
    for source, target in TRANSLATIONS.items():
        name = frappe.db.get_value("Translation", {"language": "vi", "source_text": source})
        if name:
            # Bản dịch app đặt mà còn giữ bản cũ (sai) thì sửa; người dùng tự sửa khác thì giữ.
            if frappe.db.get_value("Translation", name, "translated_text") in OLD_TRANSLATIONS.get(source, ()):
                frappe.db.set_value("Translation", name, "translated_text", target)
            continue
        frappe.get_doc(
            {"doctype": "Translation", "language": "vi", "source_text": source, "translated_text": target}
        ).insert(ignore_permissions=True)
