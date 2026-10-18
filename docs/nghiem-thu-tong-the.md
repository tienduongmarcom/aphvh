# Nghiệm thu tổng thể APH–VH–MK–TL

## Cách làm đã chốt ngày 17/10/2026

Anh Tiến chưa có danh mục hàng và tồn kho để thử thực tế. Tiếp tục phát triển và kiểm bằng dữ liệu giả trên site UAT tách biệt. Gom nghiệm thu nghiệp vụ thật sau khi có danh mục, tồn kho, số dư, người dùng và máy in. Không đánh đồng CI xanh với nghiệm thu nhân sự hoặc hoàn tất mọi nghiệp vụ.

Nguồn yêu cầu: `docs/quyet-dinh-nghiep-vu.md`, các đặc tả 0.11–0.14, `docs/ban-hang-nhanh-tiep-quan.md`. Bảng dưới là kịch bản nghiệm thu, chưa phải kết quả PASS và không thay nguyên văn 202 quyết định.

## Điều kiện bắt đầu nghiệm thu thực tế

- Kế toán duyệt mã hàng, đơn vị Kg, kg/bao, giá và chủ kho; thủ kho xác nhận tồn kg/bao theo kho, kế toán duyệt giá trị đầu kỳ.
- Cấu hình quỹ/ngân hàng và tuyến thu hộ được người có thẩm quyền duyệt. Không tự điền tài khoản thực nhận thay khách.
- Có tài khoản nhân sự theo vai trò, giới hạn công ty/kho và hồ sơ Dũng không xem giá vốn.
- Có phiên bản ứng viên đủ UAT/Cổng 2/2b/3 trên đúng SHA; triển khai theo thủ tục, có sao lưu/diễn tập.
- Thử chứng từ giả trên UAT; production chỉ dùng chứng từ nghiệp vụ thật được nhân sự xác nhận.

## Kịch bản theo một chuỗi nghiệp vụ

| Bước | Người thực hiện | Tình huống | Kết quả cần xác nhận |
|---|---|---|---|
| 1 | Kế toán + kho | Danh mục, kho, số dư đầu kỳ | Đúng công ty/chủ kho, kg/bao, giá trị; đối chiếu đầu kỳ khớp |
| 2 | Bán hàng | Đơn chung, hàng từ nhiều kho và pháp nhân | Đơn con đúng chủ hàng, lượng và giá; không ghi sổ khi mới lập đơn |
| 3 | Người duyệt | Giá dưới sàn / khách rủi ro | Đúng quyền duyệt; sửa nội dung làm duyệt cũ hết hiệu lực |
| 4 | Kế toán | Thu tiền/cọc, chưa rõ khách | Tiền vào đúng quỹ/bank thực nhận; chưa rõ khách không tự cấn nợ |
| 5 | Kế toán | Phân bổ cọc, thu hộ APH–TL | Theo kế hoạch duyệt, không FIFO; không tạo tiền giả ở ngân hàng TL |
| 6 | Bán hàng | Lập phiếu xuất & In từng phần | Nháp theo nguồn/kho; gọi lại không trùng; không giảm tồn/nợ khi in |
| 7 | Kho | Bàn giao cho người giao / khách tự lấy | Xuất kho và ghi nợ đúng thời điểm, đúng kg/bao; không ghi sổ hai lần |
| 8 | Người nhận | Khách nhận hàng | Đúng actor/thời gian, không phát sinh thêm GL/SLE |
| 9 | Kế toán/kho có quyền | Lưu bản ký, đối chiếu chênh lệch | Tệp riêng đúng phiếu; dấu đối chiếu; thay hồ sơ phải kiểm lại |
| 10 | Bán hàng/kế toán | Phiếu thiếu bản ký | Tìm được phiếu còn thiếu/chờ đối chiếu theo quyền; giao hàng không bị chặn vì thiếu ảnh |
| 11 | Điều phối | Đổi nguồn phần chưa giao | Không sửa phần đã giao, không vượt lượng còn lại hoặc quyền kho |
| 12 | Kế toán + kho | Thực nhận thiếu, trả hàng, giảm giá | Dùng chứng từ điều chỉnh hợp lệ; bảo toàn kg/bao, tồn, giá trị và công nợ |
| 13 | Kế toán | Thu nốt, đối chiếu sao kê | Đúng mã/tiền/ngày; báo trùng/lệch/chưa ghi; không tự ghi sổ từ sao kê |
| 14 | Dũng + người nhận tiền | Thu tiền nhà máy, chi nhỏ, bàn giao | Chỉ thấy phạm vi được phép; người nhận đếm thực; chênh lệch chờ điều tra |
| 15 | Nhà máy + kế toán | Nhập chờ định giá, chi phí chuyến | Không đưa giá 0 vào tồn khả dụng; chốt giá và phân bổ/repost đúng |
| 16 | Nhà máy | Sản xuất, phụ phẩm, hao hụt, repack | Cân đối kg/bao/giá trị; quy tắc phụ phẩm và dở dang đúng đặc tả |
| 17 | Kế toán trưởng | Công nợ, tồn kho, quỹ, tài chính | Báo cáo đối chiếu với sổ nguồn theo từng công ty; chỉ rõ lãi tạm/giá tạm |
| 18 | Kế toán thuế | Hồ sơ hóa đơn MISA, in lại | Tham chiếu đúng hóa đơn; không coi ERP tự phát hành hóa đơn thuế |
| 19 | Nhân sự thật | Quyền, giá vốn và máy in | Không lộ giá vốn qua API/in/export với hồ sơ bị chặn; bản in giấy đọc đủ, đúng liên |
| 20 | Kế toán trưởng | Chốt/khóa kỳ và tình huống lỗi | Không sửa trái kỳ; lỗi giao dịch không để chứng từ/sổ dở; phục hồi đúng thủ tục |

Ghi mỗi ca: phiên bản/SHA, ngày, người thao tác, mã chứng từ, số liệu kỳ vọng/thực tế, ảnh/bản in và người ký xác nhận. Có lỗi phải giữ bằng chứng, bổ sung ca hồi quy trước khi sửa; không ghi PASS thay nhân sự.

## Mốc phát triển hiện tại

Production theo log VM: 0.15.1. Nhánh hồ sơ giao nhận bổ sung bản ký/đối chiếu và lối vào các phiếu tiền còn chờ xử lý; chưa phát hành. Ca giữ tiền tổng quát, mở rộng nhà máy/tài chính và các khoảng trống trong bảng đối chiếu yêu cầu cần được rà lại theo code hiện có trước khi tuyên bố hoàn tất; nhiều ghi chú trong bảng 202 là lịch sử 13/10.
