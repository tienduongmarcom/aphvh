# Thu hộ, tài khoản chuẩn, pháp lý — APH, VH (bổ sung cho quyết định 02–03/10)
## THU HỘ, TÀI KHOẢN CHUẨN, PHÁP LÝ (chốt 06/10/2026, anh Tiến)
- **Thu hộ** (khách lấy hàng TL nhưng chuyển khoản vào TK của VH/APH): chỉ cần một bút toán Nợ tiền / Có tài khoản chi tiết "Tiền thu hộ đơn vị khác" (3388x, tự tạo, là tài khoản duy nhất được chấp nhận) và cờ "Cần xử lý". Phiếu có khách, chủ hàng (mặc định TL), tham chiếu; "Đã xử lý" bắt buộc có ghi chú tham chiếu MISA, tự ghi ngày xử lý. Báo cáo "Tien thu ho chua xu ly" (mặc định lọc Cần xử lý, số ngày chờ). Các bước sau do kế toán xử lý trên MISA; phía TL không tự động. (aphvh 0.4.20, 0.4.21)
- **Tài khoản chuẩn (0.4.21)**: ép đủ bộ tài khoản theo từng đơn vị (APH, VH, MK, TL) lúc cài đặt; không xóa hay đổi tên tài khoản có sẵn. Chạy lại không tạo trùng.
- **Hóa đơn**: hóa đơn do VH/APH xuất chỉ hợp lệ khi hàng thực sự thuộc VH/APH (TL bán trước bằng chứng từ hợp lệ). Hóa đơn đầu vào dư của các năm trước nằm ngoài hệ thống mới, là việc xử lý thuế của chị Dung, không làm quỹ xuất bù.
- **Quyết định về ghi chú pháp lý**: các lưu ý "cần xác nhận bằng văn bản" chỉ để ghi nhận, không chặn triển khai và sẽ bỏ khi về một sổ. Bảng rà soát đầy đủ: claude/bang-ra-soat-phap-ly-APH-VH.md (chốt 06/10/2026).
- **Kiểm thử**: 0.4.20 đạt H0–H9 trên 8086. 0.4.21 đã build, CHƯA chạy trên 8086 (chạy nang-cap-app-8086-v2.sh rồi kiem-full-8086.sh). 8081 chưa nâng lên 0.4.20/0.4.21.

## Nguyên tắc dữ liệu (chốt 06/10/2026, anh Tiến)
- Dữ liệu hiện tại chưa sạch (ví dụ chênh 400.000 ở 1551/156 do mặt hàng thử TEST.TK1 bị đổi nhóm sau khi ghi sổ; bút toán tay ACC-JV-2026-00005): không xử lý chạy theo dữ liệu thử cũ.
- Xây hệ thống chỉ theo các phần đã sạch và đã chốt, rồi cập nhật dần lên khi dữ liệu được làm sạch.
- Đã hoãn: chặn đổi tài khoản tồn kho nhóm hàng sau khi có chứng từ; phân loại đậu đỏ đóng gói (TP.DO: 1551 hay 156).
- aphvh 0.4.22 đạt 68/68 trên 8086 (06/10). Cây kho nhà máy APH đúng thiết kế (13 kho vật lý).
