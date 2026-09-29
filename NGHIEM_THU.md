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
