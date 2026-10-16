# Đặc tả bản 0.11.3 — trả hàng, giảm giá sau giao, hạn thanh toán, địa chỉ giao, hồ sơ hóa đơn MISA

Ngày 14/10/2026.
Nguồn:
- BA mục 10, 11, 14 (`docs/ba/danh-gia-BA-0.11.1.md`), đã dời từ 0.11.1 theo D3.
- Các quyết định R025, R026, R044, R045, R093–R098, Q148, Q166–Q170, Q178, Q180, Q189, Q190.

Production đang chạy 0.11.2 (13 cờ).

## 1. Phạm vi và quyết định

| # | Nội dung | Chốt |
|---|---|---|
| E1 | Phạm vi | **0.11.3:** BA mục 10, 11, 14. **0.11.4:** BA mục 15 (báo cáo quản trị, cộng ngang 4 đơn vị, dòng tiền 7/30 ngày, R039, khóa kỳ R105). Tách vì mục 15 chỉ đọc số liệu, cần dữ liệu bán hàng của 0.11.3 để kiểm. |
| E2 | Cờ | Một cờ mới **`kh_aph_sales_p1`** (cờ thứ 14) cho cả ba mục, mặc định tắt. |
| E3 | 5 tình trạng hàng trả (R025) | Tách làm **2 câu hỏi** trên phiếu trả. Không gộp vào một ô vì hàng và tiền là hai việc độc lập. (1) **Hàng về đâu:** Bán lại được (về kho bán) / Cách ly (kho "Hàng cách ly <địa điểm>", không bán được). (2) **Xử lý tiền:** Bù trừ công nợ (mặc định) / Hoàn tiền / Đổi hàng. Như vậy đủ 5 tình trạng của BA. Hàng vừa bán được vừa cách ly thì lập 2 phiếu trả. |
| E4 | Giảm giá sau giao (R026, Q169–Q170) | Kế toán nhập **tổng tiền khách được giảm**: gồm thuế nếu hóa đơn có thuế, chưa thuế nếu không. App chia theo tỷ trọng doanh thu từng dòng và tách thuế theo thuế suất dòng. Kết quả là **bút toán nháp** loại Credit Note, đối trừ thẳng vào hóa đơn: Nợ TK giảm trừ, Nợ 33311 (phần thuế), Có 131 khách. Không dùng hóa đơn trả lại, vì trả lại giá sẽ ăn mất số lượng được trả của hóa đơn gốc. |
| E5 | TK giảm trừ doanh thu | Công ty có TK **521** (TT99: VH) thì ghi **521**. TT133 không có 521 (APH, MK theo bộ của app, TL) nên ghi thẳng **giảm TK doanh thu của dòng** (Nợ 511). Ghi vào bảng rà soát pháp lý. |
| E6 | Hạn thanh toán (Q166–Q168, R044–R045) | **Hạn chung của đơn** = ngày xác nhận đơn + số ngày theo điều khoản của khách. Sửa được trước khi gửi đơn. Mọi hóa đơn sinh từ các đợt giao của đơn lấy chung hạn này, thay cho cách 0.11.0 tính từ ngày giao. **Gia hạn** sau khi gửi đơn qua nút "Gia hạn thanh toán": bắt buộc lý do, lưu bảng lịch sử (hạn cũ, hạn mới, lý do, người, lúc). Hạn mới cập nhật hạn của các hóa đơn còn nợ của đơn. |
| E7 | Địa chỉ giao (Q178, Q180) | Mỗi đợt giao (phiếu giao) chọn địa chỉ riêng trong danh sách địa chỉ của khách; ERPNext có sẵn. Thêm nút **"Đổi địa chỉ giao"** cho phiếu đang giao: bắt buộc lý do, lưu nhật ký trên phiếu. |
| E8 | Đơn quá hạn giao (Q189, Q190) | Báo cáo "Đơn quá hạn giao" gồm các đơn đã gửi, chưa giao đủ, chưa đóng, có ngày giao dự kiến < hôm nay. Có số ngày trễ và phần còn phải giao. |
| E9 | Hồ sơ hóa đơn MISA (R093–R098, Q148) | DocType mới **"Hoa don ngoai"** (hóa đơn lập ngoài ERP). Loại: Gốc / Điều chỉnh / Thay thế / Hủy. Số tiền trên hóa đơn **không bắt buộc bằng** doanh thu quản trị (Q148), chỉ hiện chênh lệch. **Hàng đợi:** hóa đơn bán có "Khách lấy hóa đơn = Có", đã ghi sổ, chưa có hồ sơ Gốc còn hiệu lực. **Khóa chống trùng:** một hóa đơn bán chỉ thuộc một hồ sơ Gốc còn hiệu lực. Kế toán bấm "Nhận xử lý" thì hồ sơ đứng tên người đó; người khác nhận cùng hóa đơn bị chặn. Ghi sổ hồ sơ thì chép ký hiệu, số, ngày sang 3 ô HĐĐT sẵn có trên hóa đơn bán (giữ tương thích 0.9). |

## 2. Trả hàng 5 tình trạng (R025)

- Phiếu giao trả lại (Delivery Note `is_return = 1`) có loại điều chỉnh "Khách trả hàng (R025)" có hai ô. Để trống thì app
  điền mặc định **Bán lại được + Bù trừ công nợ**, đúng cách làm trước 0.11.3. Lý do: CI 14/10 cho thấy bắt buộc chọn sẽ chặn
  các luồng trả hàng sẵn có (bộ inventory).
  - `kh_aph_hang_tra_ve`: Bán lại được / Cách ly.
  - `kh_aph_xu_ly_tien`: Bù trừ công nợ / Hoàn tiền / Đổi hàng.
- **Cách ly:**
  - App đặt kho đích của mọi dòng là "Hàng cách ly <địa điểm của kho xuất gốc>". Kho này tự tạo lần đầu cần, theo cây kho chuẩn 0.11.2.
  - Kho cách ly thuộc loại không bán, nên đơn bán chọn kho này đã bị chặn từ 0.11.2.
- **Bán lại được:** giữ kho của dòng (mặc định là kho xuất gốc).
- **Sau khi ghi sổ** phiếu trả, hóa đơn giảm tự sinh như 0.11.1. Sau đó:
  - Hoàn tiền: lập Payment Entry **nháp** loại Trả tiền cho khách, đúng số của hóa đơn giảm. Kế toán chọn quỹ hoặc ngân hàng rồi ghi sổ.
  - Đổi hàng: lập phiếu giao **nháp** mới từ đơn bán gốc, cùng mã và số lượng đã trả. Kế toán sửa nếu đổi sang mã khác.
  - Bù trừ: không làm thêm gì; hóa đơn giảm tự trừ công nợ.

## 3. Giảm giá sau giao (R026)

- Nút **"Giảm giá sau giao"** trên hóa đơn bán đã ghi sổ (không phải hóa đơn trả lại).
- Kế toán nhập số tiền và lý do. Số tiền không được vượt phần còn nợ của hóa đơn.
- Lần lượt từng dòng, theo tỷ trọng tiền dòng (`net_amount`):
  - phần chưa thuế: Nợ TK giảm trừ (E5);
  - phần thuế (nếu hóa đơn có thuế): Nợ 33311.
- Đối ứng: Có 131 khách, `reference` tới hóa đơn để trừ đúng hóa đơn.
- Chứng từ là bút toán **nháp**. Kế toán xem rồi ghi sổ. Chạy lại cùng hóa đơn khi còn nháp thì trả lại bút toán cũ.
- Hóa đơn điều chỉnh trên MISA: kế toán lập hồ sơ "Hoa don ngoai" loại Điều chỉnh, liên kết bút toán này.

## 4. Hạn thanh toán, gia hạn, địa chỉ, quá hạn giao

- **Đơn bán, ô "Hạn thanh toán chung" (`kh_aph_han_thanh_toan`):**
  - Tự điền = ngày đơn + số ngày theo điều khoản thanh toán của khách. Không có điều khoản thì để trống, hóa đơn tính như cũ.
- **Hóa đơn tự sinh từ phiếu giao:** có đơn mang hạn chung thì `due_date` = hạn chung. Nếu hạn chung sớm hơn ngày giao thì lấy ngày giao.
- **Gia hạn** (`gia_han_thanh_toan(sales_order, han_moi, ly_do)`, quyền Accounts Manager / Accounts User):
  - Thêm một dòng lịch sử (bảng con `kh_aph_lich_su_gia_han`).
  - Đổi hạn chung trên đơn.
  - Đổi `due_date` của các hóa đơn còn nợ thuộc đơn, gồm cả lịch thanh toán và Payment Ledger Entry. Không đổi số tiền nào.
- **Đổi địa chỉ giao** (`doi_dia_chi_giao(delivery_note, dia_chi, ly_do)`):
  - Chỉ phiếu đã ghi sổ và đang giao. Địa chỉ phải thuộc khách.
  - Đổi địa chỉ hiển thị và ghi Comment nhật ký "từ … sang …, lý do".
- **Báo cáo "Don qua han giao".**

## 5. Hồ sơ hóa đơn MISA (R093–R098)

- **DocType `Hoa don ngoai`** (submittable). Các ô:
  - company, customer;
  - loai (Gốc / Điều chỉnh / Thay thế / Hủy), hoa_don_lien_quan (Link chính nó; bắt buộc trừ loại Gốc);
  - ky_hieu, so, ngay (bắt buộc khi ghi sổ);
  - tien_truoc_thue, tien_thue, tong;
  - nguoi_xu_ly, nhan_luc, trang_thai (Đang xử lý / Đã xuất / Bị điều chỉnh / Bị thay thế / Đã hủy);
  - bảng con: hóa đơn bán (Link Sales Invoice, doanh thu quản trị tự điền);
  - chenh_lech (tổng hóa đơn − tổng doanh thu quản trị, chỉ hiển thị).
- **Hàng đợi:** báo cáo "Hoa don cho xuat". Mỗi dòng có nút "Nhận xử lý" (`nhan_xu_ly(sales_invoices)`):
  - Tạo hồ sơ nháp loại Gốc đứng tên người bấm.
  - Hóa đơn bán đã nằm trong hồ sơ Gốc khác chưa hủy thì báo "đang do X xử lý".
- **Ghi sổ hồ sơ:**
  - Gốc: chép ký hiệu, số, ngày sang ô HĐĐT của từng hóa đơn bán.
  - Thay thế: hồ sơ cũ → "Bị thay thế", ô HĐĐT chép theo hồ sơ mới.
  - Điều chỉnh: hồ sơ cũ → "Bị điều chỉnh", ô HĐĐT giữ nguyên.
  - Hủy: hồ sơ cũ → "Đã hủy", xóa ô HĐĐT để hóa đơn bán quay lại hàng đợi.
- **Quyền:** Accounts User / Accounts Manager. Dũng (không xem giá vốn) không thấy, vì hồ sơ có doanh thu.

## 6. Cờ, cài đặt, kiểm thử

- **Cờ `kh_aph_sales_p1`:** cập nhật FLAGS, `quay-lui.sh`, `dau_van_site.py`, `frontend_preflight.py`, `handoff_preflight.py`, Cổng 3 (lên 14 cờ).
- **Cổng 3** nâng cấp từ **0.11.2** (digest `sha256:f2417393…09ca3`, 13 cờ cũ).
- **Bộ UAT `b0113`:**
  - Trả hàng cách ly: tồn vào kho cách ly, đơn bán từ đó bị chặn.
  - Trả hàng hoàn tiền: Payment Entry nháp đúng số.
  - Đổi hàng: phiếu giao nháp mới.
  - Giảm giá sau giao 2 dòng có thuế: chia đúng tỷ trọng; APH ghi 511, VH ghi 521; công nợ hóa đơn giảm đúng.
  - Hạn chung: 2 đợt giao cùng hạn; gia hạn đổi hạn hóa đơn và PLE, có lịch sử; người không quyền bị chặn.
  - Đổi địa chỉ đang giao có nhật ký.
  - Báo cáo quá hạn giao.
  - Hồ sơ MISA: nhận xử lý, người thứ hai bị chặn; ghi sổ chép số sang hóa đơn; Thay thế, Hủy quay lại hàng đợi; Q148 chênh lệch không chặn; Dũng không xem được.

## 7. Chờ xác nhận (không chặn code)

- E5: TT133 ghi giảm trừ thẳng vào 511. Chị Dung xác nhận khi xem bút toán nháp đầu tiên.
