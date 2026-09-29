# Nghiệm thu aphvh 0.1.0

Ngày 29/09/2026, trên bản thử (bản sao dữ liệu APH, ERPNext v16.36.0, công ty "THU NGHIEM APH").
Chuỗi: phiếu nhập 100 kg @ 90.000 → phân bổ chi phí nhập khẩu tạm tính → hai phiếu "Đóng gói theo kg"
→ sửa chi phí nhập khẩu tăng, giảm → tính lại giá.

| # | Ca thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|
| 1 | 90 kg đầu vào → 40 kg A + 20 kg B, chi phí tạm 1 tr | Đầu vào 9,0 tr; A 6,0 tr; B 3,0 tr (150.000/kg) | Đạt |
| 2 | 10 kg đầu vào → 1 kg A + 0,5 thùng (18 kg/thùng) | Chia 1 : 9 → A 100.000; thùng 900.000 (1.800.000/thùng) | Đạt |
| 3 | Chi phí nhập khẩu tăng lên 3 tr, tính lại giá | A 7,2 tr (180.000/kg); B 3,6 tr; thùng 1.080.000 | Đạt |
| 4 | Chi phí giảm còn 0,5 tr, tính lại giá | A 5,7 tr (142.500/kg); B 2,85 tr; thùng 855.000 | Đạt |
| 5 | Sửa trọng lượng mã thùng 18 → 20 kg rồi ép tính lại | Phiếu cũ giữ 9 kg đã lưu, số không đổi | Đạt |
| 6 | Tính lại lần nữa | Kết quả không đổi | Đạt |
| 7 | Mã thùng chưa khai trọng lượng | Báo lỗi "Chưa tính được số kg…" | Đạt |
| 8 | Có chi phí cộng thêm trên phiếu | Báo lỗi "chưa hỗ trợ" | Đạt |
| 9 | Phiếu Repack chuẩn, 2 thành phẩm, không giá tay | ERPNext chuẩn vẫn chặn như cũ | Đạt |
| 10 | Phiếu Repack chuẩn, 1 thành phẩm | Chạy như ERPNext chuẩn, không gắn quy tắc | Đạt |
| 11 | 700.000 chia 3 dòng bằng nhau | 233.333,34 + 233.333,33 + 233.333,33; chênh lệch phiếu = 0 | Đạt |
| 12 | Sổ kho so với sổ cái (báo cáo Stock and Account Value Comparison) | 0 dòng lệch | Đạt |

Ở mọi ca, giá trị trên sổ kho của từng dòng khớp bút toán sổ cái (152 → 155).

# Nghiệm thu aphvh 0.2.1

Ngày 29/09/2026, trên bản thử 8080 (ERPNext v16.36.0), công ty APH, bằng tài khoản thử chỉ có
vai trò "Kế toán nhà máy APH" (không có vai trò xem giá). Đơn mua PUR-ORD-2026-00001 do quản trị
lập (thay Dung): 1.000 kg NL.DXHAT7 @ 23.000 + 100 kg VT.BAO17 @ 3.000.

| # | Ca thử | Kết quả mong đợi | Kết quả |
|---|---|---|---|
| 1 | Tạo phiếu nhập từ đơn mua, sửa 980 kg theo cân, gửi | Giá giữ 23.000; Nợ 152 / Có 3318; đơn còn mở 20 kg | Đạt |
| 2 | Phiếu nhập NL.DXHAT7 không có đơn mua | Bị chặn, báo "Thiếu đơn mua" | Đạt |
| 3 | Phiếu vật tư vận hành nhưng chọn NL.DXHAT7 | Bị chặn, báo sai nhóm hàng | Đạt |
| 4 | Phiếu vật tư vận hành 500 kg than @ 3.500, gửi | Thấy và nhập được giá; Nợ 152 / Có 3318 | Đạt |
| 5 | Cấp liệu 500 kg sang kho dở dang đậu | Gửi được | Đạt |
| 6 | Đóng gói theo kg: 500 kg đậu + 10 kg bao → 450 kg TP + 40 kg tấm | kg-v1; 23.959,18/kg cả hai; Nợ 155 / Có 152 = 11.739.998,2 | Đạt |
| 7 | Thiếu 5 kg vào 1381 | Nợ 1381 / Có 152 theo bình quân 23.000 | Đạt |
| 8 | Thừa 2 kg, không nhập giá | Lấy bình quân 23.000; Nợ 152 / Có 3381 | Đạt |
| 9 | Màn hình phiếu nhập từ đơn, đơn mua, phiếu kho, mã hàng | Không có cột/ô giá, tổng tiền, thuế | Đạt |
| 10 | Màn hình phiếu vật tư vận hành | Có cột đơn giá, thành tiền | Đạt |
| 11 | Danh sách phiếu nhập, đơn mua | Không có cột tổng tiền | Đạt |
| 12 | Sổ kho, Bin, sổ cái, bảng giá; báo cáo Stock Balance, Stock Ledger, Stock Projected Qty | Bị từ chối (403) | Đạt |
| 13 | Báo cáo Tồn kho số lượng APH | Chạy, chỉ có số lượng | Đạt |
| 14 | Xuất Excel phiếu nhập | Bị từ chối (0.2.0 lọt, sửa ở 0.2.1) | Đạt |
| 15 | Mở phiếu mới, lấy hàng từ đơn mua | Không còn thông báo lỗi quyền Cài đặt kho / mua hàng (sửa ở 0.2.1) | Đạt |
| 16 | In mẫu Standard phiếu nhập, đơn mua, phiếu kho | Không có giá (sửa ở 0.2.1); phiếu vật tư vẫn có giá | Đạt |
| 17 | In Phiếu nhập kho APH, Phiếu kho APH | Đúng 01-VT / 02-VT / phiếu sản xuất, Nợ/Có theo sổ cái, giá trống | Đạt |
| 18 | Chọn tài khoản 1381 trong ô liên kết | Tìm được (quyền chọn) | Đạt |

Giới hạn đã biết (mức ẩn giá đã chốt): dữ liệu giá vẫn đọc được qua API /api/resource bởi người
rành kỹ thuật.

# Nâng ERPNext 16.36.0 → 16.36.1 (aphvh 0.2.1)

16.36.1 chỉ khác 16.36.0 ở số phiên bản và `erpnext/public/js/utils/crm_activities.js` (4 dòng,
bỏ tải hoạt động CRM trên phiếu chưa lưu); không có bản vá dữ liệu. Image
`aphvh-erpnext:0.2.1-v16.36.1` (Frappe 16.35.0). Thử trên 8080 ngày 29/09/2026 sau migrate:

| Ca thử | Kết quả |
|---|---|
| Phiên bản: frappe 16.35.0, erpnext 16.36.1, aphvh 0.2.1; không có lỗi hệ thống | Đạt |
| 20 dòng quyền vai trò nhà máy giữ nguyên | Đạt |
| Tài khoản nhà máy: phiếu nhập từ đơn mua PUR-ORD-2026-00002, sửa 195 kg, giá 24.000 giữ nguyên, cột giá ẩn | Đạt |
| Nhận nguyên phụ liệu không có đơn mua bị chặn | Đạt |
| Đóng gói theo kg 190 kg + 5 kg bao → 170 + 15 kg: kg-v1, cùng 24.233,76/kg, Nợ 155 / Có 152 | Đạt |
| In mẫu Standard và Phiếu nhập kho APH: không lộ giá | Đạt |
| Kho = sổ cái (chênh 0), không còn phiếu tính lại giá treo | Đạt |
