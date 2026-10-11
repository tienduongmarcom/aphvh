# Rà bản dịch ERPNext → tiếng Việt, đợt 0.2.4 (thông báo, báo cáo kho, màn hình kế toán nhà máy)

## Bối cảnh
Công ty sản xuất – thương mại Việt Nam (APH, TT133). ERPNext v16 làm sổ quản trị kho, mua hàng, sản xuất đóng gói theo kg.
Người dùng: kế toán trưởng (Dung, quen MISA) và kế toán nhà máy (Dũng: nhận hàng từ đơn mua, chuyển kho, cấp liệu, đóng gói,
phiếu thiếu/thừa; KHÔNG thấy giá). Đợt này gồm: cột/bộ lọc báo cáo kho, thông báo lỗi/cảnh báo/hộp thoại trong mã Python/JS
của kho và mua hàng, mô tả trường (description), vài nhãn còn sót.
Mỗi dòng chunk: id, en (chuỗi gốc), ctx (ngữ cảnh msgctxt nếu có), cur (bản đang hiện; rỗng = đang hiện tiếng Anh),
where (tệp nguồn), kind. Một chuỗi dùng chung mọi nơi nó xuất hiện.

## Thuật ngữ ĐÃ CHỐT (bắt buộc dùng, kể cả trong câu ghép)
Submit=Xác nhận · Submitted=Đã xác nhận · Cancel=Hủy · Cancelled=Đã hủy · Amend=Sửa đổi · Draft=Nháp · Row=Dòng (Row #{0}=Dòng #{0}) ·
Item/Items=Mặt hàng (khi là "mặt hàng" chung; Item Code=Mã hàng, Item Name=Tên hàng, Item Group=Nhóm hàng) ·
Warehouse=Kho · Stock Entry=Phiếu kho · Purchase Receipt=Phiếu nhập mua hàng · Purchase Order=Đơn mua hàng · Purchase Invoice=Hóa đơn mua hàng ·
Stock Reconciliation=Điều chỉnh theo kiểm kê · Opening Stock=Nhập số dư đầu kỳ · Landed Cost Voucher=Phiếu phân bổ chi phí vào giá trị tồn kho ·
Landed Cost=Chi phí nhập hàng · Valuation Rate=Đơn giá vốn · Stock UOM=ĐVT tồn kho · UOM=ĐVT · Conversion Factor=Hệ số quy đổi ·
Posting Date/Time=Ngày/Giờ hạch toán · Batch=Lô · Batch No=Số lô · Serial No=Số serial · Serial and Batch Bundle=Gói serial/lô ·
Material Receipt=Nhập kho khác · Material Issue=Xuất kho khác · Material Transfer=Chuyển kho · Repack=Đóng gói lại · Manufacture=Sản xuất ·
Stock Ledger=Sổ chi tiết vật tư hàng hóa · Stock Ledger Entry=Dòng sổ kho · Stock Balance=Tổng hợp nhập – xuất – tồn ·
Stock and Account Value Comparison=So sánh giá trị tồn kho và sổ cái · General Ledger=Sổ cái · Accounts Frozen Till Date=Khóa sổ đến ngày ·
Debit=Nợ · Credit=Có · Party=Đối tượng · Supplier=Nhà cung cấp · Accepted/Rejected Qty=SL nhận đạt/SL không đạt ·
Accepted/Rejected Warehouse=Kho hàng đạt/Kho hàng không đạt · Source/Target Warehouse=Kho xuất/Kho nhập · Get Items From=Lấy hàng từ ·
Billing/Billed=lập hóa đơn (không phải thanh toán) · Stock Received But Not Billed=Hàng đã nhận chưa nhận hóa đơn · Repost=Tính lại giá vốn
(repost item valuation = tính lại giá vốn) · Series/Naming Series=Ký hiệu chứng từ · BOM=Định mức nguyên vật liệu · Work Order=Lệnh sản xuất.

## Cột báo cáo kho (chốt đợt này)
Opening Qty=SL đầu kỳ · Opening Value=Giá trị đầu kỳ · In Qty=SL nhập · In Value=Giá trị nhập · Out Qty=SL xuất · Out Value=Giá trị xuất ·
Balance Qty=SL tồn cuối · Balance Value=Giá trị tồn cuối · Actual Qty=SL thực tế · Projected Qty=SL dự kiến · Reserved Stock=Tồn đã giữ chỗ ·
Stock Ageing=Tuổi tồn kho · Average Age=Tuổi tồn bình quân · Stock Value=Giá trị tồn kho · Account Value=Giá trị trên sổ cái · Difference Value=Chênh lệch.

## Quy ước
- "Stock" = tồn kho/kho, TUYỆT ĐỐI không "cổ phiếu/chứng khoán". "Rate" = đơn giá (chỉ Exchange/Conversion Rate = tỷ giá). "Ageing"=tuổi tồn.
  "Negative stock"=tồn kho âm. "Frozen"=khóa (sổ khóa). "Valuation"=giá vốn/tính giá.
- Viết hoa chữ đầu câu; dấu kiểu mới (hóa, hòa, thủy). Giữ nguyên placeholder {0} {1} %s %(name)s, thẻ HTML (<b>, <br>, <a …>), ký hiệu, dấu chấm cuối
  câu như bản gốc. Không đổi thứ tự placeholder nếu ngữ pháp không cần; đổi thì vẫn đủ từng placeholder.
- Thông báo lỗi: văn phong ngắn, rõ, nói người dùng phải làm gì; không dịch word-by-word kiểu máy.
- Tên lớp/trường kỹ thuật (fieldname, DocType nội bộ như "Stock Ledger Entry" khi là tên bảng) → dùng tên Việt đã chốt nếu có.
- Từ thông dụng giữ: Serial, Email, Excel, FIFO, LIFO, UOM chỉ khi là mã.

## Việc cần làm
Với MỖI dòng, quyết định bản dịch cuối `final` (kể cả khi `cur` đã đúng thì final = cur). Ghi ra file JSON (mảng) TẤT CẢ các dòng:
{"id": <id>, "final": "...", "changed": true|false, "loai": "Sai nghiệp vụ"|"Khó hiểu"|"Chưa dịch"|"Chính tả/trình bày"|"Nhất quán"|"", "ly_do": "ngắn, chỉ khi changed"}
changed = final khác cur. Không bỏ sót dòng nào. Kiểm tra placeholder/thẻ HTML trước khi ghi.
Cuối cùng trả lời 2–3 câu: số dòng đã sửa theo loại và 3 lỗi đáng chú ý nhất.
