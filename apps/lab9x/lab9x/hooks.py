app_name = "lab9x"
app_title = "9xLab"
app_publisher = "9xLab"
app_description = "Lõi ERPNext cho doanh nghiệp Việt Nam: hệ thống tài khoản theo thông tư, thuế GTGT, hộ kinh doanh, mẫu in, kiểm soát kế toán"
app_email = "tienduongmarcom@gmail.com"
app_license = "Proprietary"

required_apps = ["erpnext"]

# Hook dùng chung cho mọi khách. Các hook còn ở app khách (kh_*) sẽ chuyển dần về đây.
doc_events = {
    # Nhóm hàng và tài khoản kho (lab9x/nhom_hang.py)
    "Item Group": {
        "after_insert": "lab9x.nhom_hang.item_group_after_insert",
        "validate": "lab9x.nhom_hang.item_group_validate",
    },
    "Item": {"validate": "lab9x.nhom_hang.item_validate"},
}
