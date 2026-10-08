app_name = "lab9x"
app_title = "9xLab"
app_publisher = "9xLab"
app_description = "Lõi ERPNext cho doanh nghiệp Việt Nam: hệ thống tài khoản theo thông tư, thuế GTGT, hộ kinh doanh, mẫu in, kiểm soát kế toán"
app_email = "tienduongmarcom@gmail.com"
app_license = "Proprietary"

required_apps = ["erpnext"]

# 0.1.0: lõi mới chỉ chứa quy tắc thuần (không móc vào ERPNext). Các hook (doc_events, mẫu in,
# báo cáo, custom field) sẽ chuyển dần từ app khách sang đây ở các đợt sau, kèm patch chuyển dữ liệu.
