# Bản cài trắng 0.5.2 và kết quả đối chiếu bổ sung (06/10/2026)
**Đã xác định (nhiều nguồn khớp):**
- TT99: BHTN là **3386** (không có 3385); 3387 là "Doanh thu chờ phân bổ"; 33311 và 33312 là tài khoản cấp 3; 111, 112, 154, 156 không có cấp 2 do thông tư quy định.
- TT133: 338 gồm 3381–3388 (3385 là BHTN, không có 3389); 154 không có cấp 2 (DN tự mở chi tiết); 156 không có cấp 2 theo đa số nguồn.
- TT99 Điều 11 và TT133 Điều 10 (sửa đổi bởi TT46/2025 từ 01/07/2025): DN được sửa đổi, bổ sung tài khoản qua quy chế hạch toán, không cần Bộ Tài chính chấp thuận. Vì vậy chi tiết DN (1521–1524, 1551/1552/1558, 15411/15421, 3311, 3318, 33880, 6321/6322, 6359) hợp lệ.

**Còn một nguồn / chưa có văn bản gốc (ghi nhận, sửa khi cần):** không truy cập được Phụ lục chính thức của hai thông tư (chỉ có nguồn thứ cấp; trang xcyber.vn chặn robots); tên một số tài khoản TT133 chỉ có một nguồn; 156 cấp 2 của TT133 nguồn mâu thuẫn (chưa tạo cấp 2); có dự thảo thay thế TT133 (22 tài khoản) chưa ban hành, chỉ một nguồn.

**Bản cài trắng (aphvh 0.5.2, nhánh v0.3-review):** `aphvh/bang_tai_khoan.py` (APH 138 tài khoản, VH 188) + `aphvh/cai_ban_trang.py`: bỏ tài khoản mẫu ERPNext (chỉ khi công ty chưa có bút toán), tạo cây chuẩn, đặt tài khoản mặc định, tài khoản tạm 9990 nhập số dư đầu kỳ (không dùng 3389), bật tồn kho vĩnh viễn và theo mặt hàng, kho (nhà máy chỉ APH), nhóm hàng cấp 1 gắn tài khoản kho (APH: HH 156, TP 1551, NL 1521, VT 1523, DD 15411, PTSC 1524, CCDC 153; VH: HH 1561, CCDC 153), mẫu thuế GTGT. Kiểm trên site trắng thật: 36/36 đạt (máy phát triển và site thử 8086). Chạy tay: `bench --site <site> execute aphvh.cai_ban_trang.cai_tat_ca`; chưa gắn tự động sau migrate để không đụng site có dữ liệu.

**Chưa làm:** mẫu thuế mua hàng 1331 theo thuế suất; chặn đổi tài khoản kho sau khi có phát sinh; công cụ chuyển số dư khi tách tài khoản.

## Đối chiếu với văn bản chính thức TT133 (anh Tiến cung cấp PDF "Hệ thống tài khoản kế toán TT133", 06/10/2026) — bản 0.5.3
- Danh mục số hiệu của APH khớp **100%** với bản chính thức (148 tài khoản cấp 1–3 từ 111 đến 821). Phần thêm ngoài thông tư chỉ là chi tiết DN: 1521–1524, 15411, 15421, 1551, 1552, 1558, 3311, 3318, 3351, 33880, 6321, 6322, 6359.
- Sửa tên theo bản chính thức: 228 "Đầu tư góp vào đơn vị khác", 3333 "Thuế xuất khẩu, nhập khẩu".
- Xác nhận từ văn bản gốc: 154 và 156 **không có cấp 2**; 3385 Bảo hiểm thất nghiệp; 3386 Nhận ký quỹ, ký cược; 3387 Doanh thu chưa thực hiện; 642 có 6421 Chi phí bán hàng, 6422 Chi phí quản lý doanh nghiệp; 338 không có 3389; không có 621/622/623/627/641.
- **911 (Xác định kết quả kinh doanh)** có trong thông tư nhưng cố ý không tạo: ERPNext xác định kết quả qua báo cáo và Period Closing Voucher (kết chuyển vào 4212), tài khoản 911 sẽ không dùng đến. Ghi nhận, thêm lại nếu kế toán muốn kết chuyển tay.
- Có test cố định danh mục chính thức (test_bang_tai_khoan.TestKhopBanChinhThucTT133) để sau này sửa bảng không lệch thông tư.
- Còn thiếu: bản chính thức TT99 cho VH (hiện dựa nguồn thứ cấp).

## Đối chiếu với văn bản chính thức TT99 (Phụ lục II Thông tư 99/2025/TT-BTC, PDF anh Tiến cung cấp) — bản 0.5.4
- 71 tài khoản cấp 1 chính thức; số hiệu của VH khớp **100%** (206 tài khoản trong thông tư, trừ 911 cố ý không tạo). Bản trước thiếu 20 tài khoản cấp 2–4 và đã bổ sung: 2151–2153 và 21511/21512/215121/215122 (tài sản sinh học), 3431/3432, 41111/41112, 6231–6238 (623), 82111/82112.
- Văn bản gốc xác nhận: 111, 112, 113, 154, 155, 156, 511 không có cấp 2 (vì vậy 1111/1112/1121/1122, 1551…, 1561, 5111–5113 là chi tiết do DN mở, đánh dấu "DN"); 338 gồm 3381–3384, 3386 (bảo hiểm thất nghiệp), 3387 (doanh thu chờ phân bổ), 3388 — không có 3385 và 3389; 155 tên chính thức là "Sản phẩm"; 242 "Chi phí chờ phân bổ"; có thêm 158, 171, 211–213 (cấp 1), 215, 221, 222, 243, 244, 332, 337, 343, 344, 347, 357, 412, 414, 521, 621–623, 627, 641.
- Văn bản chính thức viết "Chi phí thuế TNDN hoàn lại" cho 8212 (lỗi chính tả trong thông tư); bảng giữ "hoãn lại".
- Có test cố định danh mục TT99 chính thức (TestKhopBanChinhThucTT99).
- Kiểm trên site trắng thật: 36/36 đạt.
