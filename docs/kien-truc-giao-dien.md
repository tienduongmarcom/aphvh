# Quyết định kiến trúc giao diện — Hybrid Native ERPNext Workspace (chốt 14/10/2026)

Chủ dự án phê duyệt sau phản biện giữa nhóm BA + Senior Frappe Developer và Claude. Áp dụng từ bản 0.11.0.

## 1. Kiến trúc

| Thành phần | Quyết định |
|---|---|
| ERPNext Desk | Giữ nguyên, không thay thế khung (thanh trái, thanh trên, tìm kiếm, chọn công ty là của Desk) |
| Workspace chuẩn | Điều hướng theo nhóm nhân sự |
| Dialog | Thao tác ngắn, ít trường |
| Native Frappe Page | Luồng nghiệp vụ nhiều bước, tần suất cao, cần một màn hình tập trung |
| Vue / SPA / bước build frontend | Chưa dùng |
| API nghiệp vụ | Tập trung ở backend `kh_aph`; Workspace, Dialog, Page, form chuẩn gọi chung service |
| Dữ liệu | Một nguồn sự thật trong ERPNext; không tạo DocType "Nhiệm vụ" có trạng thái riêng — danh sách công việc là màn hình xem trên chứng từ nguồn (phiếu giao, phiếu chờ định giá, chuyển kho, kiểm kê) |
| Phân quyền | Kiểm ở server |
| Nâng cấp | CI (UAT candidate, Cổng 2, 2b, 3), image ghim theo digest, rollback = image cũ + snapshot CSDL/tệp tương ứng |
| Lõi ERPNext/Frappe | Không sửa |

Nhóm người dùng: kế toán trưởng và nhân sự khác dùng Desk mặc định; Nhóm 1 Kế toán tổng hợp–Thuế (hàng đợi hóa đơn:
nhận xử lý, xuất nháp, đã xuất, đối soát, khóa/tiếp quản có kiểm soát — hóa đơn điện tử vẫn lập trên MISA, ERP chỉ ghi số
tham chiếu); Nhóm 2 Kế toán bán hàng; Nhóm 3 Kho; Nhóm 4 Nhà máy. Ánh xạ vào vai trò đang có (Kế toán nhà máy, Nhân
viên bán hàng, Thủ kho bán hàng, APH Không xem giá vốn…), không tạo vai trò trùng.

## 2. Tiêu chí được dùng Native Page (thay cho phê duyệt từng màn hình)

1. Luồng tần suất cao, cần thao tác trên nhiều chứng từ ở một màn hình (danh sách + khung chi tiết).
2. Chỉ dùng Page API chính thức (`frappe.ui.make_app_page`, `page.set_primary_action`, `page.add_field`,
   `frappe.ui.Dialog`, control chuẩn); **không** phụ thuộc DOM/CSS nội bộ của Frappe, không đụng Sidebar/Workspace lõi.
3. Chỉ gọi API facade của `kh_aph`; API trả **đúng các trường đã cho phép** (không `doc.as_dict()`), kiểm Company/Warehouse
   theo quyền ở server.
4. Có cờ site_config riêng; tắt cờ thì quay về Desk chuẩn và **không** thay đổi chứng từ.
5. Có số đo A/B so với cách Workspace + form/Dialog (thời gian, số thao tác, tỷ lệ lỗi, khả năng sử dụng) trên nhiều
   phiếu độ phức tạp khác nhau. Mốc tham khảo ~30% cải thiện, không tuyệt đối; không cải thiện rõ thì bỏ Page.
6. Kiểm nạp asset của Page trên đúng image phát hành (Frappe đọc `page/<tên>/<tên>.js|css|html` trực tiếp từ thư mục app,
   không cần build — đã kiểm trong mã Frappe 16.51 `Page.load_assets`).

Nguyên tắc BA: không bắt nhân viên đổi quy trình đã chốt để hợp giao diện; chọn cách ít phức tạp nhất mà vẫn đạt mục tiêu.
Từ 0.12.0 có **bộ thành phần UI dùng chung 9xLab** cho bốn nhóm (bảng danh sách, bộ lọc, khung chi tiết, thông báo, nút
xác nhận, hiển thị trạng thái) dựng trên control chuẩn của Frappe.

## 3. Bảo mật — ba lớp

| Lớp | Cơ chế |
|---|---|
| Quyền gốc | Role, DocPerm, permlevel, User Permission, kiểm ở cấp chứng từ |
| API của `kh_aph` | Allowlist hành động + allowlist trường trả về + kiểm Company/Warehouse |
| Kiểm thử bảo mật | Mỗi lần nâng nền: API chuẩn, endpoint mới của Frappe/ERPNext, bản in, xem trước, export, tổ hợp vai trò; mỗi API mới có ca "người không xem giá vốn bị từ chối/bị che" |

Không chặn toàn bộ API Frappe theo URL (dễ làm hỏng Desk); lối mới của bản nền mới được rà và kiểm ở lớp 3.

## 4. Lộ trình

| Bản | Phạm vi |
|---|---|
| 0.10.0 | Backend đã kiểm, nền ERPNext 16.36.1 / Frappe 16.35.0 |
| 0.11.0 | Nâng ERPNext 16.50 (ghim digest); chỉ sửa tương thích, bảo mật, kiểm nâng cấp; chưa có UI mới |
| 0.12.0 | Trung tâm Kho: Workspace chuẩn + A/B một Native Page xuất kho |
| 0.13.0 | Trung tâm Bán hàng: đơn đa nguồn, giao hàng, công nợ, thu tiền |
| 0.14.0 | Kế toán tổng hợp–Thuế: hàng đợi hóa đơn, nhận xử lý, khóa, tiếp quản |
| 0.15.0 | Trung tâm Nhà máy: nguyên liệu, sản xuất, thành phẩm, hao hụt |

Mỗi bản chỉ hoàn thành khi nghiệm thu trên đúng mã nguồn và image. Kho chỉ go-live xuất kho thật khi tồn đầu kỳ được kế
toán và thủ kho xác nhận (thiết kế/kiểm thử bằng dữ liệu UAT không phải chờ).

## 5. Việc của 0.11.0 (từ kiểm tương thích 14/10)

- Ghim `frappe/erpnext:v16.50.0` theo digest; in phiên bản Frappe đi kèm vào bằng chứng CI.
- Cài mới trên 16.50 làm mất mẫu in mặc định của app (ERPNext đặt "… Modern with Images") — đặt lại sau bước cài.
- Che giá ở các lối mới: `print_format_generator.get_formatted_field_values`, `check_conditions`, `doc_preview.get_preview`
  (dòng con), in PDF qua `weasyprint.download_pdf`/`weasyprint_legacy.download_pdf` (lối này có từ 16.35 — vá trước khi
  tạo tài khoản thật bị hạn chế giá); áp cho cả "APH Không xem giá vốn" và vai trò bị ẩn giá (Kế toán nhà máy).
- Quyền `select` trên mẫu thuế mua vào cho vai trò nhà máy (ERPNext 16.50 kiểm quyền khi lấy thuế mặc định); kiểm trên Desk.
- `delivery_status.confirm` trả trường tối thiểu thay vì `doc.as_dict()`.
- Dọn đĩa runner CI (image 16.50 lớn hơn); kiểm dung lượng VM trước khi nâng.
- Cổng 3 tương đương production: chạy `dau_van_site.py` (chỉ đọc) trên frontend thật và so với ảnh "trước nâng cấp" của
  Cổng 3; mở rộng dấu vân thêm giá trị các Settings đơn (Stock/Accounts/Selling/Buying/System, không gồm bí mật) và các
  khóa site_config không bí mật. Phần không tái tạo được ghi rõ vào biên bản.
