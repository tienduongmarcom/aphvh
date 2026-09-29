# Rà soát bản dịch ERPNext → tiếng Việt cho kế toán APH (chuỗi trên màn hình kế toán trưởng)

## Bối cảnh
- Công ty sản xuất – thương mại Việt Nam (APH), kế toán theo Thông tư 133, người dùng là kế toán trưởng quen MISA.
- ERPNext v16 dùng làm sổ quản trị: mua nguyên phụ liệu (trong nước + nhập khẩu), nhận hàng, phân bổ chi phí nhập hàng
  vào giá vốn, sản xuất đóng gói theo kg, kho, kiểm kê, tài sản cố định/CCDC, khóa sổ tháng.
- Mỗi dòng trong chunk: `en` (chuỗi gốc), `cur` (bản đang hiện, rỗng = đang hiện tiếng Anh), `prop` (đề xuất vòng 1),
  `origin` (nguồn đề xuất), `donor` (bản ERPNext2VI), `screens`, `ctx` (doctype, fieldname, fieldtype, mô tả gốc).
  Một chuỗi dùng chung ở mọi nơi trong hệ thống (không có ngữ cảnh riêng), nên bản dịch phải đúng ở mọi chỗ nó xuất hiện.

## Thuật ngữ ĐÃ CHỐT (không đổi, dùng nhất quán trong chuỗi ghép)
Submit=Xác nhận · Submitted=Đã xác nhận · Cancel=Hủy · Cancelled=Đã hủy · Amend=Sửa đổi · Draft=Nháp · Row=Dòng ·
Party=Đối tượng · Party Type=Loại đối tượng · Valuation Rate=Đơn giá vốn · Net Total=Cộng tiền hàng ·
Grand Total=Tổng tiền thanh toán · BOM=Định mức nguyên vật liệu · Raw Material=Nguyên vật liệu ·
Naming Series / Series=Ký hiệu chứng từ · Stock Reconciliation=Điều chỉnh theo kiểm kê · Opening Stock=Nhập số dư đầu kỳ ·
Purchase Receipt=Phiếu nhập mua hàng · Item/Items (tên danh mục)=Mặt hàng · Add Row=Thêm dòng ·
Balance Sheet=Báo cáo tình hình tài chính.
Từ file ERPNext2VI 2.9 (đã kiểm toán): Billing/Billed = "lập hóa đơn" (KHÔNG phải thanh toán) · Credit To=Tài khoản ghi có ·
Debit To=Tài khoản ghi nợ · Credit Note=Phiếu ghi có · Debit Note=Phiếu ghi nợ · Write Off=Xóa sổ ·
Landed Cost=Chi phí nhập hàng · Landed Cost Voucher=Phiếu phân bổ chi phí vào giá trị tồn kho · Work Order=Lệnh sản xuất ·
Job Card=Phiếu công đoạn · Workstation=Trạm làm việc · Stock Frozen Up To=Khóa giao dịch kho đến ngày ·
Against Account=Tài khoản đối ứng · Per Received=Tỷ lệ đã nhận hàng.

## Thuật ngữ đề xuất vòng 1 (giữ trừ khi thấy sai rõ ràng – nếu sửa, ghi lý do)
Stock Entry=Phiếu kho · Item Code=Mã hàng · Item Name=Tên hàng · Item Group=Nhóm hàng · UOM=ĐVT ·
Stock UOM=ĐVT tồn kho · Conversion Factor=Hệ số quy đổi · Posting Date=Ngày hạch toán · Posting Time=Giờ hạch toán ·
Rate=Đơn giá · Amount=Thành tiền (dòng hàng) · Source/Target Warehouse=Kho xuất/Kho nhập ·
Accepted/Rejected=đạt/không đạt · Asset Category=Nhóm tài sản · Accumulated Depreciation=Hao mòn lũy kế ·
Gross Purchase Amount=Nguyên giá · Journal Entry=Bút toán · Debit/Credit=Nợ/Có · Accounts Frozen Till Date=Khóa sổ đến ngày ·
Material Receipt/Issue/Transfer=Nhập kho khác/Xuất kho khác/Chuyển kho · Repack=Đóng gói lại ·
Stock Ledger=Sổ chi tiết vật tư hàng hóa · Stock Balance=Tổng hợp nhập – xuất – tồn · General Ledger=Sổ cái ·
Trial Balance=Bảng cân đối số phát sinh · Cost Center=Trung tâm chi phí · Price List=Bảng giá · Pricing Rule=Chính sách giá.

## Quy ước trình bày
- Viết hoa chữ đầu câu, còn lại thường (giữ viết hoa: TK, ĐVT, SL, TSCĐ, XDCB, NVL, FIFO, Nợ, Có, VND, USD, tên riêng).
- Dấu kiểu mới: hóa, hòa, thủy (không hoá, hoà, thuỷ).
- Giữ nguyên placeholder {0}, {1}, %s, thẻ HTML, ký hiệu %, #, dấu ngoặc.
- Ngắn gọn, đúng từ kế toán Việt Nam (MISA, TT133). Không để tiếng Anh nếu có từ Việt thông dụng; từ đã phổ biến
  (Serial, Incoterm, Email, Website) được giữ.
- "Rate" hầu như là ĐƠN GIÁ; chỉ "Exchange Rate/Conversion Rate" mới là tỷ giá; "Tax Rate" = thuế suất.
- "Stock" = tồn kho/kho (không bao giờ là cổ phiếu). "Commission" = hoa hồng. "Subcontract" = gia công ngoài (không phải ký gửi/ký hợp đồng phụ).
- "Receipt" tùy chỗ: trạng thái di chuyển tài sản = Tiếp nhận; chứng từ nhận hàng = phiếu nhập.

## Việc cần làm
Với MỖI dòng trong chunk của bạn, quyết định bản dịch cuối (`final`). Kiểm tra:
1. Sai nghiệp vụ (nghĩa kế toán/kho sai, đảo Nợ/Có, Billing thành thanh toán, Rate thành tỷ giá, Stock thành cổ phiếu…).
2. Khó hiểu / dịch máy / tối nghĩa / sai chính tả / thiếu dịch.
3. Không nhất quán với thuật ngữ đã chốt ở trên (kể cả khi thuật ngữ nằm trong chuỗi ghép).
4. `prop` vòng 1 có làm hỏng gì không (ví dụ viết thường tên riêng, thay thế máy móc tạo câu kỳ cục).

Ghi kết quả ra file JSON (mảng) CHỈ các dòng mà `final` khác `prop`, mỗi phần tử:
{"id": <id>, "en": "...", "prop": "...", "final": "...", "loai": "Sai nghiệp vụ" | "Khó hiểu" | "Chính tả/trình bày" | "Nhất quán",
 "ly_do": "một câu ngắn tiếng Việt"}
Dòng nào `prop` đã đúng thì không ghi. Không bỏ sót: đọc hết mọi dòng. Cuối cùng trả lời bằng 2–3 câu: số dòng đã sửa theo từng loại và 3 lỗi đáng chú ý nhất.

## Chốt thêm 29/09 22:34 (anh Tiến, đối chiếu tài liệu ERPNext)
- "Received But Not Billed" xét từ phía bên mua = "đã nhận chưa nhận hóa đơn" (Stock/Asset Received But Not Billed).
- Tax Withholding Category = Danh mục thuế khấu trừ tại nguồn (Category = Danh mục; Group = Nhóm).
- Excise Entry = Bút toán Excise (không quy về thuế TTĐB Việt Nam). Clearance Date = Ngày ngân hàng ghi nhận.
- Target Incoming Rate (vốn hóa tài sản) = Giá trị vốn hóa của tài sản đích. Grant Commission = Cho phép tính hoa hồng.
- Contra Entry = Bút toán chuyển tiền giữa quỹ/ngân hàng (tránh "nội bộ" = liên công ty).
