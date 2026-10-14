# Đặc tả lượt 0.12 (gộp 0.12.0 + 0.12.1) — Trung tâm dữ liệu và số dư đầu kỳ

Ngày 14/10/2026. Gộp hai bản vào một lượt phát hành và triển khai (anh Tiến, 14/10 22:13).
Production đang chạy 0.11.4 (15 cờ). Bản dịch 0.11.5 (không cờ) đi cùng lượt này.

Nguồn:
- Đặc tả 0.11.2 mục 5 (K5): số liệu nhân viên nhập, quy tắc kiểm, người duyệt.
- BA 0.11.1 nguyên tắc 1 và mục 16: không chặn cứng dữ liệu đầu kỳ; cảnh báo mềm và danh sách cần rà soát.
- Hồ sơ phân loại sổ MISA: số dư đầu kỳ lấy theo thực tế (kiểm kê kho, quỹ đếm, sổ phụ ngân hàng, công nợ khách xác nhận); MISA chỉ tham khảo.

## 1. Quyết định chung

| # | Nội dung | Đề xuất |
|---|---|---|
| H1 | Cờ | Hai cờ mới, mặc định tắt: **`kh_aph_du_lieu`** (cờ 16, Trung tâm dữ liệu) và **`kh_aph_dau_ky`** (cờ 17, số dư đầu kỳ). Bật riêng được. |
| H2 | Ai nạp dữ liệu thật | **Anh Tiến nạp** bằng công cụ của app (chốt 14/10 22:40). Nhân viên kiểm, đối chiếu và tự xử lý dòng thiếu/sai. Tác tử lập trình không nạp dữ liệu thật. |
| H3 | Chặn hay cảnh báo | Lỗi **cấu trúc** chặn (sai mã, sai công ty, thiếu cột bắt buộc, nợ ≠ có). Lỗi **số liệu** chỉ cảnh báo và đưa vào danh sách cần rà soát (thiếu giá, lệch định mức, nghi trùng). |
| H4 | Công cụ nạp | Dùng **Data Import của ERPNext 16.50** (trình hướng dẫn mới, có xem trước và báo lỗi từng dòng) và các công cụ chuẩn (Opening Invoice Creation Tool, Stock Reconciliation, Journal Entry loại Opening Entry). Không viết bộ nạp riêng. |
| H5 | Giao diện | Workspace chuẩn "Trung tâm dữ liệu" (không Native Page, không Vue), theo `docs/kien-truc-giao-dien.md`. |

## 2. Bản 0.12.0 — Trung tâm dữ liệu (cờ `kh_aph_du_lieu`)

### 2.1 Workspace "Trung tâm dữ liệu"
Một màn hình gồm:
- **Mẫu nhập** (Excel tải về, đã có sẵn tên cột tiếng Việt và một dòng ví dụ): khách hàng, nhà cung cấp, mặt hàng, quy đổi ĐVT, định mức.
- **Nạp**: nút mở Data Import đúng DocType, đúng mẫu.
- **Đề nghị sửa số liệu chờ duyệt** (mục 2.2).
- **Danh sách cần rà soát** (báo cáo `Du lieu can ra soat` đã có, mở rộng ở mục 2.3).
- Số đếm nhanh: số đề nghị chờ duyệt, số dòng cần rà soát theo nhóm.

### 2.2 Đề nghị sửa số liệu có người duyệt (K5)
Số liệu nhà máy (sản lượng mẻ, kg tịnh, gram mỗi gói, bao bì mỗi quy cách, tỷ lệ hao hụt, định mức hiệu lực) không sửa thẳng trên mã hàng / định mức mà qua **"Đề nghị cập nhật số liệu"**:

| Bước | Ai | Việc |
|---|---|---|
| Lập | Dũng / anh Hùng | Nhập nhiều dòng một lần (tay hoặc dán từ Excel): đối tượng, trường, giá trị mới, lý do. App tự điền giá trị hiện tại. |
| Kiểm | App | Chạy quy tắc của mục 2.4 cho từng dòng: lỗi cấu trúc thì không cho gửi; cảnh báo thì hiện cạnh dòng. |
| Duyệt | Chị Dung (định mức hiệu lực: Giám đốc hoặc chị Dung) | Duyệt hoặc trả lại từng phiếu, bắt buộc lý do khi trả. |
| Áp dụng | App | Khi duyệt: ghi vào mã hàng / định mức. Định mức đã dùng thì **tạo bản định mức mới** (ERPNext không cho sửa định mức đã xác nhận), đặt mặc định, giữ bản cũ. Lưu nhật ký trước/sau. |

Dùng **Workflow chuẩn của Frappe** cho trạng thái (Nháp → Chờ duyệt → Đã áp dụng / Trả lại). Không tạo DocType "Nhiệm vụ".

### 2.3 Mở rộng danh sách cần rà soát
Thêm vào báo cáo `Du lieu can ra soat` (đang có từ 0.11.1):
- Khách / nhà cung cấp **trùng MST** trong cùng công ty; khách thiếu MST mà có "lấy hóa đơn".
- Mặt hàng: thiếu kg tịnh (khi bán theo bao/thùng), thiếu quy đổi ĐVT, giá vốn 0 mà còn tồn.
- Một mã bao bì nằm ở hai định mức với hai quy cách khác nhau.
- Mặt hàng có nhiều hơn một định mức mặc định, hoặc không có định mức mặc định mà đã có lệnh sản xuất.
- Sản lượng mẻ thực tế 30 ngày gần nhất lệch quá **20%** so với định mức.

### 2.4 Quy tắc kiểm (thuần, nằm ở `lab9x` để khách sau dùng lại)
- kg tịnh mỗi thùng = số gói × gram mỗi gói (sai số 0,5%).
- Sản lượng mẻ > 0; tỷ lệ hao hụt ≥ 0, mặc định 0.
- Mã bao bì phải thuộc nhóm "Bao bì đóng gói".
- MST: 10 hoặc 13 số (dạng 10-3), không trùng trong công ty.
- Mỗi mã thành phẩm tại mỗi thời điểm có đúng một định mức mặc định.

## 3. Bản 0.12.1 — Số dư đầu kỳ (cờ `kh_aph_dau_ky`)

### 3.1 Phạm vi và mốc
- **Ngày đầu kỳ theo từng công ty**, khai trong `khach.json` (`ngay_chot` hiện là 30/09/2026). Bút toán đầu kỳ ghi vào ngày chốt.
- Bảy loại số dư, mỗi loại một mẫu và một công cụ chuẩn:

| Loại | Công cụ chuẩn ERPNext | Nguồn số liệu | Ghi chú |
|---|---|---|---|
| Tồn kho | Stock Reconciliation (mục đích Nhập số dư đầu kỳ) | Kiểm kê kho | Thiếu giá → cảnh báo, vào danh sách rà soát; nhập giá tạm được. |
| Tiền mặt, ngân hàng | Journal Entry loại Opening Entry | Quỹ đếm, sổ phụ ngân hàng | Tài khoản ngoại tệ nhập cả nguyên tệ và tỷ giá. |
| Công nợ khách | Opening Invoice Creation Tool | Công nợ đã xác nhận với khách | **Từng hóa đơn còn nợ** (giữ hạn thanh toán để báo cáo tuổi nợ và dòng tiền 0.11.4 đúng). Khách chỉ có số tổng thì một dòng, hạn = ngày chốt. |
| Công nợ nhà cung cấp | Opening Invoice Creation Tool | Đối chiếu với NCC | Như trên. |
| Tài sản cố định | Asset loại Existing Asset + Journal Entry 211/214 | Bảng tài sản của chị Dung | Existing Asset không tự ghi sổ cái nên phải kèm bút toán. |
| CCDC chờ phân bổ | Journal Entry 242 | Bảng CCDC | Phân bổ tháng theo bảng chị Dung duyệt. |
| Vay, vốn, khác | Journal Entry | Khế ước vay, sổ sách | Vay gắn đối tượng (ngân hàng) để theo dõi từng khế ước. |

### 3.2 Tài khoản đối ứng đầu kỳ
- Mọi số dư đối ứng một **tài khoản tạm**, khai trong `khach.json` (`tk_doi_ung_dau_ky`). Mặc định **9990** (tài khoản tạm app đang dựng).
- **Chờ chị Dung chốt 3389 hay 9990** (mục mở từ 0.11.2). Đổi sau khi đã nhập thì phải nhập lại, nên cần chốt trước khi Dung nạp.
- Khi nạp đủ 7 loại, tài khoản tạm của mỗi công ty phải về **0**. Còn số dư thì báo cáo chỉ ra loại nào lệch.

### 3.3 Báo cáo "Doi chieu so du dau ky"
Theo từng công ty:
- Cột: loại số dư, số theo bảng nguồn (nhân viên nhập tổng), số trên sổ ERP, chênh lệch, trạng thái (Chưa nạp / Lệch / Khớp).
- Dòng cuối: số dư tài khoản tạm đối ứng.
- Kiểm thêm: sổ kho = sổ cái theo từng tài khoản kho; tổng công nợ chi tiết = số dư 131 / 331.

### 3.4 Khóa sau khi chốt
Chị Dung bấm **"Chốt số dư đầu kỳ"** khi báo cáo khớp: app khóa kỳ đến ngày đầu kỳ bằng công cụ khóa kỳ của 0.11.4. Sau đó muốn sửa phải mở khóa có lý do.

## 4. Kiểm thử

- **Cờ:** 17 cờ ở mọi danh sách. Cổng 3 nâng cấp từ 0.11.4 (digest `54bf5a99…`, 15 cờ), bật 2 cờ mới.
- **Bộ UAT `b0120`** (dữ liệu giả):
  1. Mẫu tải về đúng cột; nạp khách trùng MST bị báo.
  2. Đề nghị sửa kg tịnh sai công thức không gửi được; đúng thì gửi, chị Dung duyệt, mã hàng đổi, có nhật ký.
  3. Đề nghị đổi định mức đã dùng → tạo bản mới, bản cũ giữ nguyên.
  4. Dũng không duyệt được; người không phải chủ dữ liệu không áp dụng được.
  5. Danh sách rà soát hiện đủ các nhóm của mục 2.3.
- **Bộ UAT `b0121`** (dữ liệu giả, hai công ty):
  1. Nạp đủ 7 loại → tài khoản tạm về 0, báo cáo "Khớp".
  2. Bỏ một loại → báo cáo chỉ đúng loại "Chưa nạp" và số dư tài khoản tạm bằng đúng phần đó.
  3. Công nợ đầu kỳ từng hóa đơn có hạn → hiện đúng trong báo cáo dòng tiền 7/30 ngày.
  4. Tồn kho thiếu giá → vẫn nạp được, vào danh sách rà soát.
  5. Chốt số dư → chứng từ ngày đầu kỳ bị chặn; mở khóa cần lý do.

## 5. Đã chốt (anh Tiến, 14/10 22:40)

1. Anh Tiến nạp; nhân viên kiểm và xử lý phần thiếu/sai.
2. Ngày đầu kỳ **30/09/2026** cho cả 4 đơn vị (cuối tháng, cuối quý gần nhất; tháng 9 đã kết thúc nên khóa kỳ được).
   Tồn kho đầu kỳ phải là tồn **ngày 30/09** (kiểm kê 01/09 cộng trừ phát sinh tháng 9), không phải tồn 01/09.
   Chứng từ từ 01/10 nhập bù sau khi nạp đầu kỳ.
3. Tài khoản đối ứng: **9990 "Tài khoản tạm nhập số dư đầu kỳ"**, ngoài hệ thống tài khoản của thông tư.
   Lý do: TT133 và TT99 không quy định tài khoản đối ứng cho số dư đầu kỳ (sổ được chuyển số dư, không ghi bút toán);
   TT133 không có 3389; dùng một tài khoản 338x thật sẽ trộn với nợ phải trả thật trên báo cáo tình hình tài chính.
   9990 phải về 0 khi đã nạp đủ mọi số dư (kể cả vốn 411, lợi nhuận chưa phân phối 421); không lên báo cáo tài chính.
   Ghi vào `docs/bang-ra-soat-phap-ly-APH-VH.md` để chị Dung xác nhận.
4. Công nợ theo từng hóa đơn còn nợ.
5. Tài sản cố định, CCDC, vay, vốn: **lượt sau**. Lượt này: tồn kho, tiền mặt + ngân hàng, công nợ khách, công nợ NCC.
   Vì vậy sau lượt này 9990 **chưa về 0**: số dư còn lại phải bằng đúng phần chưa nạp (TSCĐ, CCDC, vay, vốn, các khoản khác);
   báo cáo đối chiếu hiện dòng "phần chưa nạp (lượt sau)".

**Nạp từ 15/10 trước khi có 0.12.1:** dùng ngay công cụ chuẩn (Stock Reconciliation mục đích Nhập số dư đầu kỳ, Opening Invoice
Creation Tool, Journal Entry loại Opening Entry), ngày 30/09/2026, đối ứng 9990. Dữ liệu này dùng tiếp được với 0.12.1:
báo cáo đối chiếu và nút chốt đọc thẳng các chứng từ đó.
