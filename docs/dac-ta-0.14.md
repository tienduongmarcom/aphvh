# Đặc tả lượt 0.14 — Trung tâm Bán hàng + Tiền và vay

Ngày 15/10/2026. Gộp hai phần vào một lượt (anh Tiến, 15/10 11:35). Production đang 0.13.0 (19 cờ).

## 1. Cờ

| Cờ | Phạm vi |
|---|---|
| **`kh_aph_trung_tam_ban`** (cờ 20) | Mục 2: Trung tâm Bán hàng |
| **`kh_aph_tien_vay`** (cờ 21) | Mục 3–6: tài khoản ngân hàng, sổ quỹ / sổ tiền gửi, thu chi hộ qua tài khoản cá nhân giám đốc, khế ước vay, nhập sao kê |

## 2. Trung tâm Bán hàng (Workspace chuẩn, cờ `kh_aph_trung_tam_ban`)

Một màn hình cho kế toán bán hàng và trưởng phòng bán hàng, gom các việc hằng ngày đã có từ 0.10–0.13:

- **Lối vào nhanh:** lập đơn bán / đơn chung nhiều công ty; phiếu giao chờ xuất, đang giao; hóa đơn còn nợ; thu tiền; khách cần gọi
  hôm nay; khách chưa xác nhận công nợ; đơn quá hạn giao; hóa đơn chờ xuất MISA; đơn chờ duyệt giá dưới sàn.
- **Số đếm nhanh:** đơn chờ duyệt dưới sàn, phiếu đang giao, hóa đơn quá hạn, khách đến hẹn trả.
- **Giá sàn cho đơn chung nhiều công ty** (còn thiếu ở 0.13): kiểm và duyệt trên đơn chung, các đơn con sinh ra mang theo duyệt.
- **In lại phiếu xuất kho kèm số hóa đơn MISA / theo lượng thực nhận, giữ bản gốc** (Q197–Q198): mẫu in thêm dòng "Hóa đơn số …"
  lấy từ hồ sơ hóa đơn MISA (0.11.3); bản in lại ghi "In lại lần n".
- Chưa làm trang Native riêng (chưa có số đo A/B theo kiến trúc giao diện).

## 3. Tài khoản ngân hàng (cờ `kh_aph_tien_vay`)

- Khai danh sách trong `khach.json` (mục `ngan_hang`): đơn vị, ngân hàng, **4 số cuối** tài khoản, loại tiền (VND/USD).
  **Số tài khoản đầy đủ không đưa vào repo** (repo công khai): kế toán nhập trên thẻ Bank Account sau khi dựng.
- App dựng cho từng dòng: tài khoản chi tiết dưới 1121 (VND) / 1122 (USD), tên "<ngân hàng> <4 số cuối>", loại Bank, đúng loại tiền;
  thẻ Bank Account gắn tài khoản đó. Chỉ THÊM cái thiếu, không đổi tên / xóa tài khoản đã có phát sinh (giống bộ dựng cây kho).
- Tài khoản chung 1121 hiện có: giữ, không dùng cho phát sinh mới (báo trong danh sách rà soát nếu còn phát sinh).

## 4. Sổ quỹ tiền mặt và sổ tiền gửi ngân hàng

- Báo cáo + mẫu in **Sổ quỹ tiền mặt** (S07-DN / mẫu tương ứng TT133) và **Sổ tiền gửi ngân hàng** (S08-DN): theo đơn vị, tài khoản,
  khoảng ngày; số dư đầu, từng phiếu (ngày, số phiếu thu/chi, diễn giải, thu, chi), **tồn sau từng phiếu**, cộng phát sinh, số dư cuối;
  chữ ký người lập, kế toán trưởng, giám đốc.
- Mẫu theo thông tư của từng đơn vị (APH TT133, VH TT99, HKD TT152 dùng sổ tiền của hộ kinh doanh). Không chắc mẫu thì ghi bảng rà soát pháp lý.

## 5. Thu chi hộ qua tài khoản cá nhân giám đốc

- Không ghi vào 112 của công ty (không phải tiền của công ty). Ghi **công nợ với giám đốc**:
  - Giám đốc thu hộ tiền khách: Nợ 1388 (đối tượng giám đốc) / Có 131 (khách).
  - Giám đốc chi hộ cho công ty: Nợ chi phí / 331 (nhà cung cấp) / Có 3388 (đối tượng giám đốc).
  - Công ty hoàn / giám đốc nộp lại: bù trừ 1388 / 3388 với tiền mặt / ngân hàng.
- Hộp thoại nhanh "Thu hộ / chi hộ qua tài khoản cá nhân" (chọn người, khách hoặc nhà cung cấp, số tiền, nội dung) → bút toán nháp,
  kế toán xác nhận. Người thu / chi hộ khai trong danh mục (Nhân viên).
- Báo cáo "Công nợ với giám đốc": số dư 1388 − 3388 theo người, chi tiết từng lần thu / chi hộ.

## 6. Vay theo khế ước

- DocType **"Khế ước vay"**: đơn vị, bên cho vay (ngân hàng hoặc cá nhân), số khế ước, số tiền, lãi suất (%/năm), ngày vay, ngày đến hạn,
  kỳ trả lãi, tài khoản (3411; ngắn / dài hạn theo hạn), trạng thái.
- Mọi bút toán nhận vay / trả gốc / trả lãi gắn **chiều phân tích "Khế ước vay"** (bắt buộc trên 3411 và 635 lãi vay).
- Báo cáo **"Dư nợ vay theo khế ước"**: gốc nhận, đã trả, dư nợ, lãi đã trả, ngày đến hạn; **lịch đến hạn** 7 / 30 / 90 ngày.
  Báo cáo dòng tiền 7/30 ngày (0.11.4) cộng thêm khoản gốc + lãi vay đến hạn.
- **Trích lãi tháng:** cuối tháng, nút lập bút toán nháp Nợ 635 / Có 335 (hoặc 3388) theo dư nợ × lãi suất × số ngày; kế toán duyệt.
- **Số dư vay đầu kỳ:** bút toán đầu kỳ gắn khế ước (đối ứng 9990), hiện ở báo cáo đối chiếu đầu kỳ dòng "Khác".

## 7. Nhập sao kê ngân hàng (R037)

- Tải tệp sao kê Excel/CSV của từng ngân hàng (cột: ngày, số tham chiếu, nội dung, ghi nợ, ghi có). Ánh xạ cột theo ngân hàng
  (lưu mẫu để dùng lại).
- App so với phiếu thu / chi đã ghi (theo mã giao dịch, số tiền, ngày ±2): **khớp / chưa ghi sổ / trùng**. Dòng chưa ghi sổ: nút lập
  phiếu thu / chi nháp. Không tự ghi sổ. Dùng chung chống trùng mã giao dịch của 0.13.

## 7b. Tránh trùng — dùng lại cái đã có (rà soát 15/10)

| Việc 0.14 | Đã có ở đâu | Cách làm |
|---|---|---|
| Đối chiếu sao kê (R037) | `funds.reconcile_rows` (0.10) so dòng sao kê JSON với APH Funds Receipt theo `external_key` | **Mở rộng** hàm này: thêm bộ đọc Excel/CSV + ánh xạ cột, so thêm Payment Entry `reference_no`. Không viết bộ so thứ hai. |
| Chống trùng mã giao dịch | `ban_quay.thu_tien` (0.13) chỉ kiểm Payment Entry; Funds Receipt có `external_key` riêng | Một hàm chung kiểm **cả hai** nguồn; `thu_tien` và nhập sao kê cùng gọi. |
| Dựng tài khoản ngân hàng | `tai_khoan_chuan.setup(company)` dựng tài khoản chuẩn | Thêm bước con theo cùng mẫu (chỉ thêm cái thiếu), không bộ dựng riêng. |
| Dòng tiền có khoản vay | `quan_tri.dong_tien_cong_ty` (0.11.4) | Cộng thêm gốc + lãi đến hạn khi cờ `kh_aph_tien_vay` bật; không báo cáo dòng tiền mới. |
| Thu chi hộ của giám đốc | `thu_ho.py` (0.4.20) là thu hộ **giữa các đơn vị** (chủ hàng ↔ khách) | Khác bản chất (đối tượng Nhân viên trên 1388/3388); dùng trường riêng, báo cáo "Công nợ với giám đốc" lọc theo party Employee để không lẫn số thu hộ nội bộ. |
| Giá sàn đơn chung | `ban_quay` (0.13) kiểm SO/SI, bỏ qua SO sinh từ đơn chung | Gọi lại đúng hàm kiểm giá sàn theo từng dòng (dòng có `company` riêng) trên APH Shared Sales Order; đơn con mang dấu duyệt, không kiểm lại. |
| Số hóa đơn MISA khi in lại | Dòng APH Hoa don ngoai (0.11.3: `sales_invoice`, `so`, `ky_hieu`) | Mẫu in đọc từ đó qua hàm jinja trong `print_utils`; không thêm ô số hóa đơn lên phiếu giao. |
| Trung tâm Bán hàng | Báo cáo/lệnh đã có: khách cần gọi, xác nhận công nợ, quá hạn giao (Q189), hóa đơn chờ MISA | Workspace chỉ **gom lối vào**, không làm báo cáo mới trùng các báo cáo này. |

Đã xong ở 0.11.x, bỏ khỏi lộ trình cũ: Q176 mã khách, R091 khóa giá thành phẩm, R046–48 quỹ nhà máy, Q189 quá hạn giao, in có / không giá.

Sau 0.14: **tạm dừng làm tính năng**, khách dùng một thời gian, gom vấn đề rồi xử lý lượt sau.

## 8. Kiểm thử

- 21 cờ ở mọi danh sách; Cổng 3 nâng cấp từ 0.13.0, bật 2 cờ mới.
- Bộ UAT `b014` (dữ liệu giả): dựng tài khoản ngân hàng chạy lại không trùng; sổ quỹ tồn sau từng phiếu đúng; thu hộ / chi hộ ra
  đúng số dư với giám đốc; khế ước: vay → trả gốc → trích lãi → dư nợ và lịch đến hạn đúng, dòng tiền có khoản vay; sao kê khớp /
  chưa ghi / trùng; đơn chung dưới giá sàn phải duyệt; quyền Dũng và nhân viên bán hàng.

## 9. Cần anh cung cấp

- Danh sách tài khoản ngân hàng: **đơn vị, ngân hàng, 4 số cuối, loại tiền** (APH 7, VH 7, HKD 4). Số đầy đủ kế toán nhập trên hệ thống.
- Danh sách người thu / chi hộ qua tài khoản cá nhân (tên). Không cần số tài khoản.
- Mẫu tệp sao kê của từng ngân hàng (1 tệp mẫu đã xóa số dư / tên khách là đủ để ánh xạ cột).
