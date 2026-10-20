# UX-01 — giao diện theo công việc (Task-Oriented ERPNext Desk)

Bản đặc tả đầy đủ do chủ dự án duyệt (18–19/10/2026, gồm phản biện ChatGPT và đặc tả 9 nhóm do Codex soạn). Tệp này ghi
**phần đã chốt để làm**, 6 điểm Claude sửa trước khi giao, và ánh xạ sang code. Nguyên tắc giữ nguyên: Desk → Workspace →
Form → Dialog → API; không Native Page/SPA đợt đầu; không sửa core; **không FIFO, không tự cấn nợ khác đơn vị**; mỗi ngữ cảnh
một việc chính; nhãn đúng hậu quả ("Lập phiếu & In" chỉ nháp; "Xác nhận bàn giao vận chuyển"/"Xác nhận khách đến lấy" mới
ghi kho/nợ).

## Sáu điểm sửa trước khi giao (Claude, 19/10)

1. Thu tiền: PR đầu chỉ dẫn tới luồng thu tiền **đang có** (nút "Thu tiền" của quầy bán hàng); Dialog thu tiền nhanh là PR
   riêng (UX-3) do rủi ro cao nhất. Ca U15–U17 kiểm luồng đang có.
2. Nút việc tiếp theo chỉ gọi hàm/nút server **đã kiểm** (GN04, GN10, ho_so_giao_nhan, chênh lệch); thiếu thì ghi chưa làm.
3. UX-0: số đo máy (số bấm/màn hình) ≠ nghiệm thu người thật (thời gian, hỏi, bấm nhầm) — người thật đo ở cuối.
4. Workspace là dữ liệu: dựng **song song** Workspace mới, giữ cũ; quay lui = đổi Workspace mặc định / tắt cờ.
5. Tìm khách theo SĐT là có viết mã (Contact/Address), không phải cấu hình — để UX-3.
6. Cấu hình theo từng người: bảng ánh xạ + lệnh áp có **chạy thử**; chủ dự án tự chạy thật trên production sau UAT.

## Ánh xạ code (cờ 28 `kh_aph_ux_task_first`, mặc định tắt)

| Nhóm | Đã làm | Code | Kiểm |
|---|---|---|---|
| UX-R01 vai trò | 4 nhóm → 4 Workspace; bán hàng/tiền không khóa đơn vị/kho; kho/nhà máy được giới hạn kho qua bảng | `ux_task.VAI_TRO`, `_ke_hoach` | unit `test_ux_task`; HTTP_UX01_WORKSPACE_APPLY |
| UX-R02 Workspace | "Việc bán hàng", "Việc kho", "Việc tiền và công nợ", "Việc nhà máy" (NM06): Việc cần làm (số đếm theo quyền danh sách native) / Thao tác nhanh / Tra cứu | `ux_task._workspace`, `schema()` | như trên |
| UX-R03 việc tiếp theo | Đơn chung, Phiếu giao, Hóa đơn: một dòng "Việc tiếp theo" + nút chính, bấm hộ nút nghiệp vụ có sẵn | `public/js/ux_buoc_tiep.js` | unit tĩnh; **chưa kiểm trên Chrome** |
| UX-R04 tìm kiếm | Tìm khách theo mã/tên/tên gọi tắt/MST/SĐT khách/SĐT liên hệ; nhiều kết quả thì liệt kê, không tự chọn | `ux_task.tim_khach`, `ux_customer_list.js` | unit; HTTP_UX03_TIM_KHACH_CONG_NO |
| UX-R05 Dialog bán/xuất | Giữ Dialog GN10 hiện có; nhãn việc tiếp theo tách nháp/xuất thật | — | — |
| UX-R06 thu tiền | Dialog 5 bước (khách → tiền thực nhận/đơn vị/tài khoản → hóa đơn được chọn theo thứ tự → xem trước phân bổ + chưa phân bổ → ghi). Ghi bằng `ban_quay.thu_tien` đã kiểm; công nợ tách từng đơn vị (`ux_task.cong_no_khach`) | `ux_thu_tien.js` | unit; DESK_UX0_BASELINE mở dialog; ghi tiền dùng ca thu quầy sẵn có |
| UX-R07 thông báo | Câu việc tiếp theo nói rõ hậu quả; thông báo thiếu hàng/vượt hạn mức viết lại có việc cần làm | `ux_buoc_tiep.js`, `translations/vi.csv` | test dịch |
| UX-R08 quy chuẩn | Khối có tiêu đề, ô to hơn (col 6/4/3), một nút chính màu | — | xem ảnh khi có Desk |
| UX-R09 đo/UAT | UX-0 số đo máy A (Desk cũ) / B (UX) cho T01–T03 trên Chrome thật, ảnh màn hình; Module Profile theo nhóm (gán bằng bảng, chạy thử mặc định) | `ux0-desk.mjs`, b014_ux.py | DESK_UX0_BASELINE |

## Còn mở

Phân bổ một phần theo số tiền tự nhập cho từng hóa đơn (hàm thu tiền hiện có trả theo thứ tự chọn, hóa đơn cuối nhận phần còn
lại) — cần sửa server, để sau khi người dùng thật xác nhận cần. UX-4 đo người thật (phiếu đo ở `docs/ux-0-phieu-do.md`).
UX-5 Native Page: chỉ xét khi số đo người thật cho thấy Dialog không đạt.
