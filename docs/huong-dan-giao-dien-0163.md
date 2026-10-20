# Hướng dẫn bản tối ưu giao diện 0.16.3 — ứng viên

Chưa phát hành production. Nguồn và kết quả kiểm xem PR #26; không dùng tài liệu này làm bằng chứng đã triển khai.

## Nơi làm việc

- Bán hàng: lập đơn chung, khách, nguồn hàng, chuẩn bị giao và hồ sơ.
- Kho vận: tồn, nhận/chuyển, phiếu chờ xuất, kiểm kê, bản ký và chênh lệch.
- Nhà máy: nhận/chuyển, ghi sản xuất/đóng gói và tiêu hao. Giữ riêng với Kho vận, chung nguồn dữ liệu chuẩn.
- Tiền và kế toán: khách trả tiền, phiếu thu chi, quỹ/chốt ca/bàn giao, ngân hàng, công nợ, vay và MISA.
- Dữ liệu và cấu hình: nhập dữ liệu, đầu kỳ, quy cách/định mức, giá sàn và tuyến thu hộ, theo quyền.

Các màn Trung tâm/Việc/Bàn cũ được ẩn sau khi dựng đủ nơi thay thế. Liên kết cũ và chứng từ còn giữ. Tài khoản đặt mặc định cũ được chuyển đúng khu mới; không cấp thêm quyền bằng việc đổi màn hình.

## Lên đơn

1. Tìm khách: gợi ý có mã, tên, điện thoại và địa chỉ. Chọn đúng khách.
2. Đầu đơn luôn hiện thông tin nhận diện hiện tại. Thiếu thông tin thì hiển thị rõ; đây không phải thao tác sửa địa chỉ giao hoặc hồ sơ cũ.
3. Xem dòng công nợ hóa đơn và quá hạn trong quyền; bấm Xem chi tiết để đối chiếu theo công ty. Tiền chưa phân bổ giữ riêng. Lỗi tải hoặc thiếu quyền không có nghĩa khách hết nợ.
4. Chọn mã hàng: tên hàng là cột riêng, tự tải. Chọn đúng kho nguồn; công ty theo kho.
5. Lập phiếu xuất và in: cửa chuẩn bị giao có cả mã và tên, lượng còn lập, quy cách và lượng đợt này. In chưa ghi xuất; chỉ xác nhận khi giao thực tế.
6. Thông tin tiền của đơn nằm trong phần chi tiết; có cọc giữ cho đơn mới hiện dòng nổi bật. Số tiền không tự cấn nợ cũ.

## Giao và hồ sơ

- Phiếu theo thông tin giao mới chỉ hiện một bộ người nhận/người giao/xe. Phiếu cũ và phiếu trả tiếp tục đọc đúng bộ cũ, không đổi dữ liệu lịch sử.
- Nút bước tiếp theo gom tại một vị trí; việc chênh lệch được nhắc trước việc thiếu bản ký.
- In tập trung trong nhóm In; mẫu A5, mẫu chuẩn và mẫu biên bản khác mục đích vẫn giữ. Đường in lại chuẩn vẫn lưu dấu vết.
- Mẫu ba liên đang sửa là bản nháp, chưa thay mẫu in đang vận hành.

## Thu tiền

Các điểm thu nhanh dùng chung cửa xem trước và hàm ghi tiền đã có. Mở từ hóa đơn giữ công ty/hóa đơn nguồn; chọn đúng quỹ hoặc ngân hàng nhận. Có người giữ tiền mặt khi áp dụng. Phân bổ theo lựa chọn, tiền dư chưa phân bổ; gửi lại cùng cửa giữ mã lượt chống thu trùng. Khi tắt cờ giao diện vẫn có đường thao tác cũ.

Chốt ca không đồng nghĩa bàn giao tiền. Đúng người nhận bàn giao phải xác nhận số tiền thực nhận. Phiếu hoàn khác hủy đề nghị.

## Tên và giới hạn

Đơn bán chung tạo mới dùng số DBC-năm-dãy số. Số đơn đã cấp được giữ nguyên; tìm và mở lại theo số cũ như trước. Thanh bên chung có tên Vận hành, các lối chứng từ chi tiết nằm trong năm khu; tùy chỉnh riêng của từng người vẫn được giữ.

Tên chung trung lập, tên công ty chỉ xuất hiện khi thực sự là chủ hàng/nhận tiền/phát hành/chế độ kế toán. Mã kỹ thuật và định danh chứng từ cũ chưa đổi; không xóa hoặc đổi tên dữ liệu gốc. Tên dịch phụ thuộc ngôn ngữ ở các bề mặt native, phải xem bằng chứng UI từng vai trò trước nghiệm thu.

Chưa mở rộng UOM hoặc quy trình sản xuất khác Kg; chưa thêm giữ tồn vật lý từ khi in, giấy gốc/vị trí lưu mới, hóa đơn một phần, tuyến chuyển hàng khác công ty, parser mọi ngân hàng hoặc chính sách mới chưa chốt.

## Nghiệm thu thực tế sau khi có dữ liệu

1. Mỗi người đăng nhập bằng tài khoản được phân công, kiểm nơi làm việc và các lối cần dùng; kiểm cả trường hợp không được xem giá vốn.
2. Chọn hai khách trùng tên, đổi qua lại; điện thoại, địa chỉ và công nợ phải đi theo đúng khách. Khách thiếu thông tin phải được báo rõ.
3. Lập một đơn nhiều mã hàng, giao từng phần từ kho được giao; kiểm mã/tên, lượng còn lại, bản in A5 và người nhận. In trước không làm giảm tồn hoặc tăng nợ.
4. Thu tiền đúng công ty/quỹ thực nhận, kiểm số còn nợ và tiền chưa phân bổ; chốt ca và bàn giao không thu thêm lần nữa.
5. Mở lại đơn/phiếu cũ và bản ký, kiểm dữ liệu lịch sử, đường in lại và lối tra cứu. Đối chiếu sổ trước/sau cùng kế toán phụ trách.

Các bước này cần người, hàng, tồn và máy in thật; kết quả kiểm tự động trên dữ liệu giả không thay cho biên bản nghiệm thu thực tế.
