# UX-0 / UX-4 — phiếu đo với người thật

Số đo máy (DESK_UX0_BASELINE trong UAT) chỉ đếm thao tác/màn hình/thời gian chạy máy cho cùng một đường đi. Phiếu này để đo
**người thật** ở nghiệm thu cuối, mỗi người làm 3 việc trên site UAT/dữ liệu thật, mỗi việc 2 lần: A = Desk hiện tại (tắt cờ
`kh_aph_ux_task_first` hoặc dùng Workspace cũ), B = giao diện mới.

| Việc | Bắt đầu | Kết thúc |
|---|---|---|
| T01 | Màn hình đầu sau đăng nhập, có đơn đã xác nhận | Đã in phiếu xuất nháp |
| T02 | Màn hình đầu, khách báo đã chuyển X đồng, chưa rõ trả hóa đơn nào | Phiếu thu đã ghi, phần chưa rõ để chưa phân bổ |
| T03 | Màn hình đầu, khách gọi hỏi còn nợ bao nhiêu | Đọc được số nợ theo từng đơn vị |

Ghi cho mỗi lần: người (tuổi, mức quen máy), việc, A/B, thời gian (giây), số lần hỏi người hướng dẫn, số lần bấm nhầm/làm lại,
hoàn thành đúng (có/không), ghi chú. Không điền số ước tính. Mục tiêu tham khảo: B nhanh hơn A ≥ 30% hoặc ít lỗi hơn rõ rệt;
không đạt thì xem lại UX trước khi nghĩ tới Native Page (UX-5).
