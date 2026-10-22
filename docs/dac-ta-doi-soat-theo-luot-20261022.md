# Đối soát công nợ và bộ giấy theo lượt

Phần tiếp nối PR38. Đã viết entity/API/JS/PDF trên ứng viên, đang kiểm native, **chưa phát hành hoặc tuyên bố đạt**. Giấy tay đã được thu gọn theo quyết định22/10: chỉ nhập bổ sung và lưu trên phiếu chuẩn; không tạo hệ thống offline riêng.

## Phạm vi triển khai

- Từ phiếu giao, phiếu thu/chi hoặc Khách hàng, người có quyền chọn các chứng từ đã ghi sổ thuộc cùng khách trong lượt cần ký. Có tăng và giảm bù nhau, ròng0 vẫn in đối soát. Không tự chọn mọi khoản thu trong ngày hoặc cấn nợ cũ.
- Một hồ sơ biên bản có mã riêng, ghi rõ khách, mốc lập, phạm vi các Company người lập được xem, nguồn chứng từ và các số đã chụp. Hồ sơ này là bằng chứng xác nhận, không sổ kho/nợ/tiền và không cấp duyệt giao dịch.
- Tại mốc chụp, tính công nợ ròng từ PLE theo từng Company. Trình bày riêng phát sinh tăng/giảm của các chứng từ được chọn và **khoản khác tại cùng mốc**, không gọi số suy ngược là số dư lịch sử trước khi khách đến. Cuối lượt ròng0 vẫn giữ các phát sinh tăng/giảm để ký.
- Cọc còn giữ và tiền chưa phân bổ hiển thị riêng theo đơn vị nhận; ghi rõ tiền đã nằm trong số dư công nợ không được trừ lần nữa. Không cấn chéo Company. Khoản trong luồng Funds và tiền chưa phân bổ native có nguồn riêng, không cộng trùng thành một lần đã thu.
- Số liệu chỉ bao gồm chứng từ đã ghi sổ trong phạm vi. Giấy chưa nhập/phiếu chưa ghi không được điền thành đã ghi hoặc số0 giả; sau nhập bổ sung lập bản mới khi cần.

## Bất biến và quyền

- Chụp dữ liệu và danh sách nguồn phía server sau khi kiểm Customer, Company, vai trò tài chính, quyền đọc nguồn; hồ sơ hạn chế giá vốn không được dùng API/list/print/File để vượt quyền.
- Phạm vi in là đúng các đơn vị người lập được phép. Người đọc hồ sơ phải còn quyền xem toàn phạm vi của hồ sơ đó; bản một phần ghi rõ phạm vi, không tự mang tên đã xác nhận toàn khách.
- Snapshot, nguồn, mốc và bản PDF đã cấp bất biến sau tạo. Reprint dùng PDF đã lưu, không render lại số mới từ bản Customer theo ngày. Hủy/backdate/nhập giấy sau đó không sửa bản cũ; lập bản mới có liên kết bản trước.
- Bộ PDF lưu riêng tư trên hồ sơ có quyền đọc phù hợp. Lưu bản in xuất kho và thu/chi của lượt cùng biên bản; bảo toàn trang A5/A4, không phát sinh DN/SI/PE/JE khi tạo/in/ký/lưu.
- Khách hoặc người có quyền ký nợ riêng được ký nợ. Lái xe chỉ định lấy hàng không mặc nhiên ký nợ. Lưu người ký, căn cứ ủy quyền khi có, ảnh/PDF ký, người nhập/thời điểm và vị trí gốc; lưu bằng chứng sau, không giữ khách chờ tải ảnh.
- Request tạo gửi lại mở hồ sơ đã tạo nếu cùng nội dung. Không tạo nguồn tài chính mới, không tự gửi tin/email cho khách.

## Kiểm bắt buộc

- Cùng khách, nhiều Company; khoản tăng/giảm bằng nhau vẫn có biên bản; nợ khác và phát sinh cộng đúng số tại mốc.
- Cọc, tiền chưa phân bổ và thu hộ không bị trừ hai lần hoặc tráo Company.
- Snapshot/PDF cũ không đổi sau phiếu mới/hủy/backdate; bản mới nối lịch sử, request lặp không thêm bản.
- Người chỉ có một Company, không xem giá vốn hoặc không có quyền đọc nguồn không lấy được hồ sơ nhiều Company qua API/list/print/privateFile.
- Bộ giấy ghi đúng DN/PE của lượt; không nhân phiếu thu do cùng nguồn được chọn hai lần; không lấy số mới để gắn vào bản khách từng ký.
- Có ảnh ký/nhận gốc/reprint vẫn không thêm SLE/GL/PLE hay chứng từ tiền/hàng.

## Cách tổ chức trong app

Tái dùng cờ quản trị/quầy bán hiện có (mặc định tắt), schema qua bộ cài rõ ràng. Thêm đúng entity hồ sơ biên bản có lifecycle bằng chứng; không thêm màn hình chính hoặc bảng nhiệm vụ. Chứng từ tiền/hàng vẫn native; mẫu đối soát Customer theo ngày cũ giữ tương thích lịch sử, cửa thao tác mới dùng snapshot. Nghiệm thu nhân sự/hàng/máy in thật giữ cuối như đã chốt.

Nguồn: `debt_statement.py`, `debt_statement_rules.py`, `statement_pdf.py`, DocType `Bien ban doi soat no`, JS `debt_statement.js`, mẫu `doi_soat_theo_luot`. Khi tạo yêu cầu khóa sổ tiền hiện có đang bật (`kh_aph_cash_closing`), rồi current-read khóa nguồn trước chụp để phát hiện nguồn vừa hủy. Bản theo ngày cũ đã được lọc phạm vi Company và giữ guard vai trò/Customer. Bộ014 thêm2HTTP +1Chrome, kỳ vọng132PASS; 545ca cục bộ có Jinja2 đạt, native/PDF thực tế còn phải đọc bằng chứng.
