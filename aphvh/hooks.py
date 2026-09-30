app_name = "aphvh"
app_title = "APH VH"
app_publisher = "An Phú Hưng - Vĩnh Hưng"
app_description = "Tùy biến nghiệp vụ ERPNext cho An Phú Hưng và Vĩnh Hưng"
app_email = "tienduongmarcom@gmail.com"
app_license = "Proprietary"

required_apps = ["erpnext"]

# Cài đặt cấu hình (custom field, loại phiếu kho) — chạy lại được nhiều lần
after_install = "aphvh.install.after_install"
before_migrate = ["aphvh.install.before_migrate"]
after_migrate = ["aphvh.install.after_migrate"]

# Mở rộng lớp Stock Entry: chia giá thành phẩm theo kg cho loại phiếu "Đóng gói theo kg".
# Cơ chế extend_doctype_class của Frappe v16 ghép lớp này TRƯỚC lớp chuẩn trong MRO;
# repost nạp phiếu qua cùng lớp đã ghép nên quy tắc vẫn chạy khi tính lại giá.
extend_doctype_class = {
    "Stock Entry": ["aphvh.stock_entry_kg.StockEntryKgCosting"],
}

# --- 0.2: phân quyền nhà máy, ẩn giá (mức màn hình + báo cáo), mẫu in Việt Nam ------------

# Cho trình duyệt biết người dùng có bị ẩn giá không và nhóm hàng nhà máy được tự nhập giá.
boot_session = ["aphvh.price_visibility.boot_session"]

# Phiếu nhập: vật tư vận hành chỉ nhận nhóm hàng được tích; người bị ẩn giá nhận nguyên phụ liệu
# phải lấy từ đơn mua.
# before_print: xóa giá trên bản in (mọi mẫu, kể cả Standard) với người bị ẩn giá.
_BLANK = "aphvh.price_visibility.blank_prices_for_print"
doc_events = {
    "Purchase Receipt": {
        "validate": "aphvh.price_visibility.validate_purchase_receipt",
        "before_print": _BLANK,
    },
    "Purchase Order": {"before_print": _BLANK},
    "Stock Entry": {"before_print": _BLANK},
    "Serial and Batch Bundle": {"before_print": _BLANK},
    "Item": {"before_print": _BLANK},
    # 0.3: cảnh báo công nợ/giá khi lưu và xác nhận đơn; hóa đơn nháp tự tạo từ phiếu giao hàng;
    # thủ kho chỉ giao theo đơn; ẩn giá vốn trên bản in với nhân viên bán hàng, thủ kho.
    # 0.3.1: có/không xuất hóa đơn GTGT (Không = bỏ thuế) chạy trước cảnh báo công nợ.
    "Sales Order": {
        "validate": ["aphvh.invoice_flag.apply_invoice_flag", "aphvh.sales_warnings.validate_sales_order"],
        "before_print": _BLANK,
    },
    "Delivery Note": {
        "validate": ["aphvh.invoice_flag.apply_invoice_flag", "aphvh.sales_flow.validate_delivery_note"],
        "on_submit": "aphvh.sales_flow.make_draft_invoice",
        "on_cancel": "aphvh.sales_flow.remove_draft_invoices",
        "before_print": _BLANK,
    },
    "Sales Invoice": {
        "validate": ["aphvh.invoice_flag.apply_invoice_flag", "aphvh.invoice_flag.validate_einvoice"],
        "before_update_after_submit": "aphvh.invoice_flag.validate_einvoice",
    },
}

# 0.3: nhân viên bán hàng chỉ thấy giá của bảng giá bán.
permission_query_conditions = {
    "Item Price": "aphvh.price_visibility.item_price_query_conditions",
}
has_permission = {
    "Item Price": "aphvh.price_visibility.item_price_has_permission",
}

# Xem trước sổ cái / sổ kho trên phiếu nháp lộ giá vốn: chặn với người bị ẩn giá vốn.
override_whitelisted_methods = {
    "erpnext.controllers.stock_controller.show_accounting_ledger_preview":
        "aphvh.price_visibility.show_accounting_ledger_preview",
    "erpnext.controllers.stock_controller.show_stock_ledger_preview":
        "aphvh.price_visibility.show_stock_ledger_preview",
}

# Ẩn cột giá trên màn hình với vai trò "Kế toán nhà máy APH" (không cần build asset).
doctype_js = {
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Item": "public/js/item.js",
    "Serial and Batch Bundle": "public/js/serial_and_batch_bundle.js",
    "Sales Order": "public/js/sales_order.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Sales Invoice": "public/js/sales_invoice.js",
}
doctype_list_js = {
    "Purchase Receipt": "public/js/purchase_receipt_list.js",
    "Purchase Order": "public/js/purchase_order_list.js",
}

# Hàm dùng trong mẫu in Phiếu nhập kho APH / Phiếu kho APH / phiếu xuất kho bán hàng, biên bản giao nhận.
jinja = {
    "methods": [
        "aphvh.print_utils.aphvh_an_gia",
        "aphvh.print_utils.aphvh_no_co",
        "aphvh.print_utils.aphvh_ngay",
        "aphvh.print_utils.aphvh_so",
        "aphvh.print_utils.aphvh_bang_chu",
        "aphvh.print_utils.aphvh_cong_ty",
        "aphvh.print_utils.aphvh_ten_nguoi",
        "aphvh.print_utils.aphvh_sl_chung_tu",
        "aphvh.print_utils.aphvh_ten_kho",
        "aphvh.print_utils.aphvh_sl_don_ban",
        "aphvh.print_utils.aphvh_dia_chi",
        "aphvh.print_utils.aphvh_lo",
        "aphvh.print_utils.aphvh_gia_gom_thue",
    ],
}
