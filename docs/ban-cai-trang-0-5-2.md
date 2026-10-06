# Bản cài trắng 0.5.2 và kết quả đối chiếu bổ sung (06/10/2026)
**Đã xác định (nhiều nguồn khớp):**
- TT99: BHTN là **3386** (không có 3385); 3387 là "Doanh thu chờ phân bổ"; 33311 và 33312 là tài khoản cấp 3; 111, 112, 154, 156 không có cấp 2 do thông tư quy định.
- TT133: 338 gồm 3381–3388 (3385 là BHTN, không có 3389); 154 không có cấp 2 (DN tự mở chi tiết); 156 không có cấp 2 theo đa số nguồn.
- TT99 Điều 11 và TT133 Điều 10 (sửa đổi bởi TT46/2025 từ 01/07/2025): DN được sửa đổi, bổ sung tài khoản qua quy chế hạch toán, không cần Bộ Tài chính chấp thuận. Vì vậy chi tiết DN (1521–1524, 1551/1552/1558, 15411/15421, 3311, 3318, 33880, 6321/6322, 6359) hợp lệ.

**Còn một nguồn / chưa có văn bản gốc (ghi nhận, sửa khi cần):** không truy cập được Phụ lục chính thức của hai thông tư (chỉ có nguồn thứ cấp; trang xcyber.vn chặn robots); tên một số tài khoản TT133 chỉ có một nguồn; 156 cấp 2 của TT133 nguồn mâu thuẫn (chưa tạo cấp 2); có dự thảo thay thế TT133 (22 tài khoản) chưa ban hành, chỉ một nguồn.

**Bản cài trắng (aphvh 0.5.2, nhánh v0.3-review):** `aphvh/bang_tai_khoan.py` (APH 138 tài khoản, VH 188) + `aphvh/cai_ban_trang.py`: bỏ tài khoản mẫu ERPNext (chỉ khi công ty chưa có bút toán), tạo cây chuẩn, đặt tài khoản mặc định, tài khoản tạm 9990 nhập số dư đầu kỳ (không dùng 3389), bật tồn kho vĩnh viễn và theo mặt hàng, kho (nhà máy chỉ APH), nhóm hàng cấp 1 gắn tài khoản kho (APH: HH 156, TP 1551, NL 1521, VT 1523, DD 15411, PTSC 1524, CCDC 153; VH: HH 1561, CCDC 153), mẫu thuế GTGT. Kiểm trên site trắng thật: 36/36 đạt (máy phát triển và site thử 8086). Chạy tay: `bench --site <site> execute aphvh.cai_ban_trang.cai_tat_ca`; chưa gắn tự động sau migrate để không đụng site có dữ liệu.

**Chưa làm:** mẫu thuế mua hàng 1331 theo thuế suất; chặn đổi tài khoản kho sau khi có phát sinh; công cụ chuyển số dư khi tách tài khoản.
