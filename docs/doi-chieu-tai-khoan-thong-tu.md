# Đối chiếu hệ thống tài khoản với thông tư (06/10/2026) — làm căn cứ lọc bảng tài khoản bản cài trắng

Quy tắc lọc: giữ tài khoản có trong thông tư của đơn vị (APH: TT133, VH: TT99) và tài khoản chi tiết có lý do nghiệp vụ; tài khoản không dùng thì bỏ.

## Tài khoản cấp 1 — đã đối chiếu
- **TT99/2025** (hiệu lực 01/01/2026): 71 tài khoản cấp 1, 101 cấp 2. Cấp 1 gồm 111, 112, 113, 121, 128, 131, 133, 136, 138, 141, 151–158, 171, 211–215, 217, 221, 222, 228, 229, 241–244, 331–338, 341, 343, 344, 347, 352, 353, 356, 357, 411–414, 418, 419, 421, 511, 515, 521, **621, 622, 623, 627, 632, 635, 641, 642**, 711, 811, 821, 911. (Nguồn: ketoanthienung.net, luatvietnam.vn, thuvienphapluat.vn.)
- **TT133/2016**: cấp 1 gồm 111, 112, 121, 128, 131, 133, 136, 138, 141, 151–157, 211, 214, 217, 228, 229, 241, 242, 331, 333–336, 338, 341, 352, 353, 356, 411, 413, 418, 419, 421, 511, 515, 611, 631, 632, 635, **642**, 711, 811, 821, 911. **Không có 621, 622, 623, 627, 641** (chi phí sản xuất tập hợp thẳng vào 154; bán hàng và quản lý là 6421, 6422 dưới 642).

## Tài khoản cấp 2 — mức đối chiếu
| TK | Nội dung | Mức |
|---|---|---|
| TT133 6421 / 6422 | Chi phí bán hàng / Chi phí quản lý doanh nghiệp (dưới 642) | Đã đối chiếu, 2 nguồn khớp |
| TT133 154 | 1541 NVL trực tiếp, 1542 nhân công trực tiếp, 1543 sử dụng máy thi công, 1547 sản xuất chung | 1 nguồn nêu rõ TT133 (bizzi.vn); 1 nguồn khác (ketoanthienung.net) ghi 1541 xây lắp, 1542 sản phẩm khác, 1543 dịch vụ, 1547 bảo hành xây lắp, giống kiểu TT200. Lệch nhau: chưa có văn bản gốc. DN được mở chi tiết 154 nên chọn theo nguồn đầu, ghi rõ "chi tiết do DN mở" |
| TT99 6271–6278, 6411–6418, 6421–6428 | Chi tiết 627, 641, 642 | Đã đối chiếu (thuvienphapluat.vn) |
| TT99 1331, 1332, 1381, 1383, 1388, 3331, 3338, 3381–3388 | Chi tiết 133, 138, 333, 338 | Đã đối chiếu |
| TT99 154 | Không quy định cấp 2 cụ thể, DN tự mở chi tiết | Đã đối chiếu (amis.misa.vn) |
| TT99 còn lại (khoảng 70 tài khoản cấp 2) | | Chưa có danh mục đầy đủ; dùng danh mục MISA của APH/VH làm chi tiết, đánh dấu "chi tiết DN" |

## Hệ quả cho app (0.4.23)
- APH (TT133): bỏ yêu cầu 627, 641; thay bằng 6421, 6422. VH (TT99) giữ 627, 641.
- Bản trắng APH không có 627, 641; chi phí sản xuất chung của APH đi qua chi tiết của 154 (1547).
- Tài khoản "Tiền thu hộ đơn vị khác" (33880) là chi tiết DN dưới 3388, ghi nhận, bỏ khi về một sổ.
