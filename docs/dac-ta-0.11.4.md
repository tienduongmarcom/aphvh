# Đặc tả bản 0.11.4 — báo cáo quản trị, dòng tiền, xác nhận công nợ, khóa kỳ

Ngày 14/10/2026.
Nguồn:
- BA mục 15 (`docs/ba/danh-gia-BA-0.11.1.md`): R099–R105, R039, Q157, Q161.

Production đang chạy 0.11.3 (14 cờ).

## 1. Quyết định

| # | Nội dung | Chốt |
|---|---|---|
| G1 | Cờ | Cờ mới **`kh_aph_quan_tri`** (cờ thứ 15), mặc định tắt. |
| G2 | Nguyên tắc | Báo cáo chỉ đọc sổ ERP, không ghi chứng từ. Tiêu đề và chân báo cáo ghi rõ **"Cộng ngang 4 đơn vị — không phải báo cáo hợp nhất kế toán"** (R100). Chỉ kế toán trưởng, Accounts Manager và anh Tiến (System Manager) xem; Dũng và nhân viên bán hàng bị chặn. |
| G3 | Lãi gộp (R099) | Doanh thu thuần lấy từ hóa đơn bán đã ghi sổ: tiền chưa thuế, trừ hóa đơn trả lại và bút toán giảm giá sau giao của 0.11.3. Giá vốn lấy từ sổ kho, là giá trị xuất của phiếu giao (hoặc hóa đơn xuất kho) tương ứng. Lãi gộp = doanh thu thuần − giá vốn. Xem theo Công ty / Kho / Mặt hàng / Khách / Đơn, có cột từng đơn vị và cột cộng ngang. |
| G4 | Lãi sau chi phí trực tiếp (R099) | Lãi gộp trừ hai khoản chi phí đã gắn được vào đơn: chi phí chuyến theo kg (tính năng sẵn có từ 0.10.0) và chiết khấu / hoa hồng ghi bằng bút toán có chọn ô "Đơn bán". Chi phí bán hàng chung (6421 / 641) **không chia** vào đơn. Báo cáo hiện riêng dòng "chi phí bán hàng chung chưa phân bổ" để người đọc không hiểu nhầm là lãi ròng. |
| G5 | Lãi tạm tính (R101, R104) | Một tháng **chưa khóa kỳ** (G7) hoặc **chưa phân bổ chi phí sản xuất** (công cụ của 0.11.1) thì mọi dòng của tháng đó gắn cờ "Lãi tạm tính" và ghi lý do. Lý do: giá vốn thành phẩm còn đổi khi phân bổ hoặc khi repost giá tạm. |
| G6 | Dòng tiền 7 / 30 ngày (R102–R103) | Số dư tiền và ngân hàng hiện tại cộng tiền dự thu (hóa đơn bán còn nợ, đến hạn trong cửa sổ) trừ tiền dự chi (hóa đơn mua còn nợ, đến hạn trong cửa sổ). Hai cửa sổ: 7 ngày và 30 ngày, theo từng đơn vị và cộng ngang. **Loại khoản nội bộ:** đối tác là một trong 4 đơn vị (khách/nhà cung cấp nội bộ, hoặc trùng tên công ty). Khoản quá hạn hiện riêng, không trộn vào "đến hạn". |
| G7 | Khóa kỳ (R105) | Dùng **Accounting Period chuẩn của ERPNext**: mỗi công ty, mỗi tháng, khóa các loại chứng từ có ghi sổ. Nút "Khóa kỳ" và "Mở khóa kỳ" chỉ dành cho Accounts Manager, bắt buộc lý do, lưu nhật ký. Chứng từ có ngày trong kỳ đã khóa bị ERPNext chặn ghi sổ, sửa và hủy. |
| G8 | Xác nhận công nợ (R039) | Trên Khách: ô "Đã xác nhận công nợ đến ngày" và ô "Người xác nhận". Kế toán bấm "Ghi nhận xác nhận công nợ" kèm số dư được khách xác nhận; app so với số dư sổ và ghi lịch sử. Khi đơn bán của khách có số dư mà lần xác nhận cuối quá **N ngày** (Selling Settings, mặc định 30) thì hiện **cảnh báo mềm** "Khách chưa xác nhận công nợ", không chặn. Có báo cáo danh sách khách chưa xác nhận. |

## 2. Báo cáo

| Báo cáo | Bộ lọc | Cột chính |
|---|---|---|
| **Lai gop quan tri** | Kỳ (từ–đến), xem theo (Công ty / Kho / Mặt hàng / Khách / Đơn), đơn vị | Doanh thu thuần, giá vốn, lãi gộp, % lãi gộp, chi phí trực tiếp, lãi sau chi phí trực tiếp, cờ tạm tính. Cột theo từng đơn vị (APH, VH, MK, TL) và cột cộng ngang. |
| **Dong tien 7 30 ngay** | Ngày tính | Số dư tiền; dự thu 7 / 30 ngày; dự chi 7 / 30 ngày; ròng 7 / 30 ngày; quá hạn phải thu / phải trả. Theo đơn vị và cộng ngang; dòng chi tiết đối tác có thể mở ra. |
| **Khach chua xac nhan cong no** | Số ngày | Khách, số dư sổ, ngày xác nhận cuối, số dư đã xác nhận, chênh lệch. |

## 3. Kiểm thử

- **Cờ:** cập nhật đủ 15 cờ ở mọi danh sách. **Cổng 3** nâng cấp từ **0.11.3** (digest `716f1401…`, 14 cờ).
- **Bộ UAT `b0114`, dữ liệu giả:**
  1. Bán ở APH và VH, có một lần trả hàng và một lần giảm giá. Lãi gộp từng đơn vị khớp số tính tay; cột cộng ngang bằng tổng các đơn vị.
  2. Tháng chưa khóa thì có cờ tạm tính; khóa kỳ xong thì hết cờ.
  3. Khóa kỳ chặn ghi sổ chứng từ có ngày trong kỳ. Mở khóa phải có lý do. Nhân viên không đủ quyền bị chặn.
  4. Dòng tiền: hóa đơn đến hạn ngày 5 nằm trong cửa sổ 7 ngày; hóa đơn đến hạn ngày 20 chỉ nằm trong cửa sổ 30 ngày; khoản nội bộ giữa hai đơn vị bị loại.
  5. Xác nhận công nợ: có lịch sử; số dư lệch thì hiện chênh lệch; đơn bán của khách quá hạn xác nhận chỉ cảnh báo, vẫn lưu được.
  6. Dũng và nhân viên bán hàng bị chặn ở cả 3 báo cáo.

## 4. Chờ xác nhận (không chặn code)

- **G4:** khoản nào tính là chi phí trực tiếp ngoài chi phí chuyến. Mặc định bản này: chỉ bút toán có chọn "Đơn bán". Chị Dung chọn thêm sau.
- **G7:** khóa kỳ theo tháng, mỗi công ty khóa riêng.
