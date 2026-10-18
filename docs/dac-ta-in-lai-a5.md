# Mở lại phiếu xuất A5 từ DN đã lưu

1. **Mục tiêu/phạm vi:** mở lại mẫu A5 hai liên từ Delivery Note hiện có; không cần lập đợt mới. Áp dụng phiếu nháp/đã xuất, cả phiếu lập chuẩn không có đơn chung. Không dùng cho phiếu hủy/trả hàng.
2. **Hiện trạng:** production0.15.3 chỉ có A5 từ Dialog lập đợt; in lại chuẩn dùng mẫu khác. Ứng viên thêm `ban_nhanh.print_note`, nút “Phiếu xuất kho A5 (2 liên)” trong nhóm In trên form DN.
3. **Quy trình:** người có quyền mở phiếu đã lưu → In → Phiếu xuất kho A5 (2 liên). Phiếu có thay đổi chưa lưu phải lưu trước. Cửa sổ bị chặn thì hướng dẫn cho phép mở; lỗi server đóng cửa sổ trống.
4. **Quy tắc:** chỉ đọc; in lặp không tạo/sửa DN, không xác nhận xuất hoặc ghi kho/nợ. Nháp có dấu Chờ xuất, đã xuất có dấu bản sao. Không cộng tổng số lượng khi các dòng khác đơn vị tính.
5. **Dữ liệu:** lấy giá bán thuần, lượng, quy cách và metadata từ DN đã lưu. Dùng chung renderer với print_batch; snapshot mới/fallback ô cũ theo print_snapshot. Không có đơn chung thì bỏ dòng tham chiếu, không tự dựng liên kết.
6. **Quyền:** dùng cờ Trung tâm Bán hàng/đơn chung hiện có và guard giá. Server kiểm read/print DN, read Company/Customer/Item/Warehouse và địa chỉ theo scope cũ; kho phải thuộc đúng company. Không đòi quyền create/submit để in lại, không bypass quyền.
7. **Tác động:** không ghi GL/SLE/SI/tiền, không đổi kho/công nợ/giá vốn/sản xuất/MISA. Không thêm schema/cờ, không đổi bộ đếm in lại chuẩn.
8. **Kiểm thử:** unit quyền/scope, status hủy/trả, phiếu không có đơn chung, giá0/net và tổng khác ĐVT; HTTP in lặp cùng HTML, snapshot nghiệp vụ/counts không đổi, scope/giá bị chặn; Chrome bấm nút thật hai lần. UAT chỉ dữ liệu giả; nghiệm thu người dùng/máy in gom cuối theo chủ dự án.
9. **Đóng gói/khôi phục:** Python và JS theo hook hiện có, template nhanh không phải Print Format chuẩn. Không sửa core/schema; image mới và reload/clear-cache theo runbook khi đến lượt phát hành. Lượt phát triển này chưa tăng version/tag hoặc triển khai. Quay lui theo snapshot/image đúng cửa sổ bảo trì, không restore mù sau mở nhập liệu.
