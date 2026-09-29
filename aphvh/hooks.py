app_name = "aphvh"
app_title = "APH VH"
app_publisher = "An Phú Hưng - Vĩnh Hưng"
app_description = "Tùy biến nghiệp vụ ERPNext cho An Phú Hưng và Vĩnh Hưng"
app_email = "tienduongmarcom@gmail.com"
app_license = "Proprietary"

required_apps = ["erpnext"]

# Cài đặt cấu hình (custom field, loại phiếu kho) — chạy lại được nhiều lần
after_install = "aphvh.install.after_install"
after_migrate = ["aphvh.install.after_migrate"]

# Mở rộng lớp Stock Entry: chia giá thành phẩm theo kg cho loại phiếu "Đóng gói theo kg".
# Cơ chế extend_doctype_class của Frappe v16 ghép lớp này TRƯỚC lớp chuẩn trong MRO;
# repost nạp phiếu qua cùng lớp đã ghép nên quy tắc vẫn chạy khi tính lại giá.
extend_doctype_class = {
    "Stock Entry": ["aphvh.stock_entry_kg.StockEntryKgCosting"],
}
