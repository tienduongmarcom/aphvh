# Đặc tả lượt 0.13 — kho vận hành, chênh lệch kiểm kê bước 2, giá sàn, hoàn thiện đầu kỳ

Ngày 15/10/2026. Production đang chạy 0.12.1 (17 cờ). Làm và kiểm trên site trắng / UAT; ngày đầu kỳ chưa chốt
(anh Tiến báo sau), nên mọi chỗ dùng ngày đầu kỳ đều đọc từ cấu hình, không ghi cứng.

Nguồn: quyết định 202 (R011, R022, R024, R057–R059), bảng rà soát pháp lý dòng 15, 16, 19, 20 (anh Tiến đồng ý 15/10),
kiến trúc giao diện (Hybrid Native).

## 1. Cờ

| Cờ | Phạm vi |
|---|---|
| `kh_aph_dau_ky` (đã có) | Mục 2: ngày đầu kỳ theo cấu hình, chốt chỉ khóa đến ngày đầu kỳ, danh sách khách chưa có công nợ đầu kỳ |
| **`kh_aph_kho_van_hanh`** (cờ 18) | Mục 3–6: Trung tâm Kho, hàng không giao được, sửa số lượng giao nhập sai, đề nghị bổ sung hàng, chênh lệch kiểm kê bước 2 |
| **`kh_aph_gia_san`** (cờ 19) | Mục 7: giá sàn thay cảnh báo dưới giá vốn |

## 2. Hoàn thiện số dư đầu kỳ (cờ `kh_aph_dau_ky`)

- **Ngày đầu kỳ** đọc từ site_config `kh_aph_ngay_dau_ky`, nếu trống thì từ `khach.json`. Báo cáo đối chiếu lấy mặc định từ máy
  chủ (bỏ ngày ghi cứng 30/09 trong JS). Đổi ngày chỉ cần một lệnh `set-config`, không cần bản mới.
- **Chốt** chỉ khóa từ đầu tháng đến **hết ngày đầu kỳ** (Accounting Period theo khoảng ngày), không khóa phần còn lại của tháng.
- **Tồn tạm (rà soát dòng 15):** dòng tồn đầu kỳ đánh dấu "Giá tạm" hiện trong báo cáo đối chiếu (số dòng, giá trị); còn dòng
  tạm thì nút Chốt từ chối. Sửa tồn đầu kỳ bằng hủy và sửa phiếu đầu kỳ hoặc thêm phiếu đầu kỳ cùng ngày; không có phiếu
  điều chỉnh ngày sau.
- **Báo cáo "Khach chua co cong no dau ky":** khách đã có đơn / giao / hóa đơn / phiếu thu sau ngày đầu kỳ mà chưa có hóa đơn
  đầu kỳ. Cột: khách, số chứng từ, tổng bán, tổng đã thu chưa phân bổ, lần giao dịch cuối. Xếp theo tổng bán giảm dần.

## 3. Trung tâm Kho (Workspace chuẩn)

Một màn hình cho thủ kho và kế toán kho: phiếu giao chờ xuất / đang giao, phiếu kho, kiểm kê, chênh lệch chờ xử lý, đề nghị
bổ sung, tồn kho số lượng. Có số đếm nhanh (đang giao, chênh lệch chờ xử lý, mã dưới ngưỡng). Chưa làm trang Native riêng:
lượt này chưa có số đo A/B theo kiến trúc giao diện.

## 4. Hàng không giao được (R022, Q183–Q184)

Trên phiếu giao **đã xuất, khách chưa nhận**, nút "Xử lý hàng không giao được" mở hộp thoại theo dòng (số lượng không giao):

| Lựa chọn | App làm |
|---|---|
| Xe quay về kho | Phiếu trả hàng (nháp) đúng số không giao, lý do "Xe quay về", vào kho gốc; giảm công nợ phần đó. |
| Chuyển khách khác | Phiếu trả hàng như trên + **đơn bán nháp** cho khách mới (chọn khách, giá), cùng kho. Hai chứng từ gắn nhau. |
| Chuyển kho khác | Phiếu trả hàng vào kho được chọn (cùng công ty). |

Thủ kho xác nhận phiếu trả; kế toán xác nhận đơn mới. Ghi nhật ký người, lý do, số lượng trên phiếu giao gốc.

## 5. Sửa số lượng giao nhập sai (R024, Q186)

Không tạo trả hàng giả cho lỗi nhập liệu. Nút "Sửa số lượng nhập sai" (Accounts Manager, bắt buộc lý do):
- Phiếu giao **chưa có hóa đơn**: hủy và sửa (Amend) phiếu giao.
- **Đã có hóa đơn nhưng chưa thu / chưa phân bổ tiền**: hủy hóa đơn rồi phiếu giao, sửa phiếu giao, lập lại hóa đơn nháp.
- Đã thu tiền, hoặc kỳ đã khóa: từ chối, hướng dẫn dùng trả hàng / điều chỉnh có chứng từ.
Lý do và người sửa lưu trên chứng từ mới.

## 6. Đề nghị bổ sung hàng (R057–R059) và chênh lệch kiểm kê bước 2

**Đề nghị bổ sung:** dùng mức đặt lại chuẩn của ERPNext (Item Reorder theo kho). Báo cáo "De nghi bo sung hang": mã × kho dưới
ngưỡng, tồn khả dụng (tồn − đã giữ − thiếu chờ xử lý, R056), đang vận chuyển, số đề nghị. Nút tạo Yêu cầu vật tư loại chuyển
kho; mỗi dòng chọn kho nguồn riêng (R059); yêu cầu chưa xuất **không giữ hàng** ở kho nguồn (R058, chuẩn ERPNext).

**Chênh lệch kiểm kê bước 2 (rà soát dòng 16):** trên mỗi vụ chênh lệch đang chờ xử lý (1381 / 3381 từ 0.11.2), hộp thoại
"Xử lý chênh lệch" chọn phương án theo dòng, app lập **bút toán nháp**, kế toán trưởng xác nhận:

| Phương án | Bút toán |
|---|---|
| Thiếu trong định mức / ngoài định mức không thu hồi | Nợ 632 (chi tiết hao hụt) / Có 1381 |
| Cá nhân bồi thường | Nợ 1388 (hoặc 334) / Có 1381 |
| Thừa trả lại người khác | Nợ 3381 / Có 331 hoặc 3388 |
| Thừa không rõ chủ | Nợ 3381 / Có 711 |
| Nhầm chứng từ | Không bút toán; hướng dẫn sửa chứng từ gốc |

Mỗi vụ được xử lý nhiều lần đến khi 1381 / 3381 của vụ về 0; báo cáo vụ chưa xử lý xong.

## 7. Giá sàn (R011, rà soát dòng 19; cờ `kh_aph_gia_san`)

- Bảng giá nội bộ "Giá sàn" (theo mặt hàng, công ty). Kế toán trưởng nhập hoặc nạp bằng Data Import; nhân viên bán không đọc được.
- Đơn bán / hóa đơn có dòng giá **dưới giá sàn**: nhân viên bán chỉ thấy "Dòng X dưới giá sàn, cần duyệt" (không hiện con số);
  không xác nhận được cho đến khi **trưởng phòng bán hàng hoặc kế toán trưởng** bấm "Duyệt giá dưới sàn" (bắt buộc lý do, nhật ký).
- Kế toán trưởng xem giá vốn và lãi gộp ở báo cáo 0.11.4; Dũng không thấy giá vốn (giữ nguyên).
- Cảnh báo "dưới bảng giá" hiện có giữ nguyên.

## 8. Kiểm thử

- 19 cờ ở mọi danh sách; Cổng 3 nâng cấp từ **0.12.1** (digest `897f81c2…`, 17 cờ), bật 2 cờ mới.
- Bộ UAT `b013` (dữ liệu giả): đổi ngày đầu kỳ bằng cấu hình; chốt chỉ khóa đến ngày đó, chứng từ sau ngày vẫn ghi được;
  dòng giá tạm chặn chốt; danh sách khách chưa có công nợ đầu kỳ; 3 lựa chọn hàng không giao được (tồn, công nợ đúng);
  sửa số lượng nhập sai 2 trường hợp + trường hợp bị từ chối; đề nghị bổ sung nhiều kho nguồn, không giữ hàng;
  xử lý chênh lệch về 0 theo vụ; giá sàn: nhân viên bị chặn, không lộ con số, quản lý duyệt được; quyền Dũng.
