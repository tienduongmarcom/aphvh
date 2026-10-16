# Đối chiếu hệ thống tài khoản với thông tư (06/10/2026) — làm căn cứ lọc bảng tài khoản bản cài trắng

Quy tắc lọc: giữ tài khoản có trong thông tư của đơn vị (APH: TT133, VH: TT99) và tài khoản chi tiết có lý do nghiệp vụ; tài khoản không dùng thì bỏ.

## Tài khoản cấp 1 — đã đối chiếu
- **TT99/2025** (hiệu lực 01/01/2026): 71 tài khoản cấp 1, 101 cấp 2. Cấp 1 gồm 111, 112, 113, 121, 128, 131, 133, 136, 138, 141, 151–158, 171, 211–215, 217, 221, 222, 228, 229, 241–244, 331–338, 341, 343, 344, 347, 352, 353, 356, 357, 411–414, 418, 419, 421, 511, 515, 521, **621, 622, 623, 627, 632, 635, 641, 642**, 711, 811, 821, 911. (Nguồn: ketoanthienung.net, luatvietnam.vn, thuvienphapluat.vn.)
- **TT133/2016**: cấp 1 gồm 111, 112, 121, 128, 131, 133, 136, 138, 141, 151–157, 211, 214, 217, 228, 229, 241, 242, 331, 333–336, 338, 341, 352, 353, 356, 411, 413, 418, 419, 421, 511, 515, 611, 631, 632, 635, **642**, 711, 811, 821, 911. **Không có 621, 622, 623, 627, 641** (chi phí sản xuất tập hợp thẳng vào 154; bán hàng và quản lý là 6421, 6422 dưới 642).

## Tài khoản cấp 2 — mức đối chiếu
| TK | Nội dung | Mức |
|---|---|---|
| TT133 6421 / 6422 | Chi phí bán hàng / Chi phí quản lý doanh nghiệp (dưới 642) | Đã đối chiếu, 2 nguồn khớp |
| TT133 154 | Thông tư không bắt buộc chi tiết cụ thể; hai nguồn lệch nhau về 1541–1547 (một nguồn: NVL, nhân công, máy, SXC; nguồn kia: xây lắp, sản phẩm khác, dịch vụ, bảo hành) | Chưa có văn bản gốc. **Không dùng cách chia 1541–1547 của em.** Dùng đúng chi tiết đã chốt trong lịch sử chat: theo dây chuyền (15411 sơ chế, 15421 phồng tôm), ghi là "chi tiết do DN mở" |
| TT99 6271–6278, 6411–6418, 6421–6428 | Chi tiết 627, 641, 642 | Đã đối chiếu (thuvienphapluat.vn) |
| TT99 1331, 1332, 1381, 1383, 1388, 3331, 3338, 3381–3388 | Chi tiết 133, 138, 333, 338 | Đã đối chiếu |
| TT99 154 | Không quy định cấp 2 cụ thể, DN tự mở chi tiết | Đã đối chiếu (amis.misa.vn) |
| TT99 còn lại (khoảng 70 tài khoản cấp 2) | | Chưa có danh mục đầy đủ; dùng danh mục MISA của APH/VH làm chi tiết, đánh dấu "chi tiết DN" |

## Hệ quả cho app (0.4.23)
- APH (TT133): bỏ yêu cầu 627, 641; thay bằng 6421, 6422. VH (TT99) giữ 627, 641.
- Bản trắng APH không có 627, 641; chi phí sản xuất chung của APH đi qua chi tiết của 154 (1547).
- Tài khoản "Tiền thu hộ đơn vị khác" (33880) là chi tiết DN dưới 3388, ghi nhận, bỏ khi về một sổ.

## Đối chiếu với lịch sử chat (06/10/2026)
- **Đã khớp:** sổ MISA của APH dùng 6422 (không có 641); VH dùng 6417, 6428 (kiểu TT99); VAT đầu ra 33311, TK 5111. APH theo TT133, VH theo TT99 đúng như đã chốt.
- **Lệch cần dọn trong bản trắng:**
  1. Ngày 28/09 đã dựng bảng tài khoản APH "TT133 92 tài khoản (+5113)" và đặt nhóm Vật tư tiêu hao dùng chi phí **627**. TT133 không có 627. Trong tài liệu có câu "kết chuyển 621/622/627 → 154 kiểu MISA" nhưng đó là suy đoán, sổ MISA mẫu không cho thấy APH dùng 627. Bản trắng APH bỏ 627; chi phí sản xuất chung đi vào chi tiết 154 do DN mở.
  2. Tồn đầu kỳ của APH được đối ứng bằng **3389**. TT133 chỉ có 3381–3388 (3385 là BHTN), không có 3389. Bản trắng dùng tài khoản tạm số dư đầu kỳ, không dùng 3389.
  3. Chi tiết 154 đã chốt theo dây chuyền (15411, 15421), không theo 1541–1547 kiểu thông tư.
- **Không phải sai:** 6321/6322 (chi tiết 632), 3311/3312/3318 (chi tiết 331), 3351, 6359 (trung gian tỷ giá) là tài khoản chi tiết do DN mở, giữ nếu app còn dùng, ghi rõ "chi tiết DN".
