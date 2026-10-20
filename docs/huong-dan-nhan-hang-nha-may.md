# Nhận hàng nhà máy — hướng dẫn cho đợt nghiệm thu cuối

Tài liệu cho bản đang phát triển PR #17–#18; chưa bật trên production0.15.3. Dùng dữ liệu thử và tài khoản đại diện trước khi nghiệm thu dữ liệu thật.

## Nhà máy nhận theo đơn mua đã có giá

1. Mở **Tồn kho số lượng**, chọn đúng đơn vị, bấm **Nhận hàng nhà máy**; hoặc mở đúng đơn mua đã xác nhận.
2. Chọn đơn mua và cách nhận **Nhận theo giá đơn mua**. Màn hình chỉ đưa phần còn được nhận sau khi trừ hàng đã nhập và hàng đang chờ định giá.
3. Nhập tổng kg, số bao thực nhận, kho nhận, ngày nhận và tên người thực nhận/ký giấy. Lượng có vấn đề là phần trong tổng kg, không cộng thêm vào tổng.
4. Nếu có vấn đề, ghi nội dung chất lượng/đàm phán giảm giá. Có thể tải tệp cân mới, riêng tư, của đúng lần nhận.
5. Xác nhận để lập và ghi nhận một phiếu nhập chuẩn. Nếu mất phản hồi, giữ cửa sổ đang mở và bấm lại; không mở cửa sổ khác để thay thế lần chưa kiểm tra kết quả.

Không nhập giá tại cửa sổ này. Tên người thực nhận có thể là nhân viên kho không có tài khoản; hệ thống lưu riêng người đang đăng nhập và thời điểm ghi nhận.

## Nhà máy nhận khi chưa chốt giá

1. Chọn cùng đơn mua nhưng cách nhận **Nhận chờ định giá (chưa vào tồn khả dụng)**; trên đơn mua có nút riêng **Nhận chờ định giá**.
2. Nhập lượng và hồ sơ thực nhận như trên, rồi xác nhận.
3. Kết quả là **APH Pending Receipt — Chờ định giá**, không phải phiếu nhập đã ghi kho. Hàng này chưa được xuất bằng tồn khả dụng; lượng đã nhận được giữ chỗ trên dòng đơn mua.

Luồng chờ định giá này chỉ hỗ trợ đơn mua VND/tỷ giá1. Cửa sổ không cho dùng giá0 để ghi kho. Nhận có giá và nhận chờ giá cùng trừ phần còn nhận trên đơn. Nếu báo vượt lượng, kiểm tra các phiếu nhận/chờ đã có; không đổi kho hoặc lập lại đơn để bỏ kiểm tra.

## Kế toán trưởng chốt giá

1. Đối chiếu chứng từ mua, lượng nhận, phiếu cân và ghi chú chất lượng.
2. Người phụ trách mua có quyền chỉnh đơn cập nhật giá hợp lệ trên đơn mua bằng thao tác chuẩn; vai trò chốt giá không tự cấp thêm quyền sửa đơn mua.
3. Mở phiếu chờ đã xác nhận, bấm **Chốt giá nhập**, nhập giá từng dòng đúng giá hiện hành trên đơn mua và lý do chốt.
4. Hệ thống lập một phiếu nhập chuẩn gắn đúng từng dòng đơn mua; giữ hồ sơ thực nhận và tham chiếu phiếu chờ. Phần giữ chỗ được chuyển thành lượng đã nhập, không tính hai lần.

Tệp cân vẫn gắn với phiếu chờ gốc; phiếu nhập giữ tham chiếu để truy lại hồ sơ. Người có hồ sơ không xem giá vốn không được dùng thao tác chốt giá, kể cả khi có thêm vai trò kế toán trưởng.

## Xử lý sai và hủy

Không sửa trực tiếp lượng/nguồn/người nhận/tệp của hồ sơ đã xác nhận. Nếu phiếu chờ đã sinh phiếu nhập, xử lý và hủy phiếu nhập theo quyền chuẩn trước; các chứng từ liên quan khác vẫn có thể chặn hủy. Phiếu chờ lúc này trở lại chờ giá và vẫn giữ chỗ. Sau khi kiểm tra hàng vật lý và xử lý đủ chứng từ, hủy phiếu chờ mới giải phóng lượng trên đơn. Không xóa hồ sơ đã có mã lượt; vẫn giữ dấu và tệp để đối soát.

Sau khi hủy phiếu nhập, không chốt lại chính phiếu chờ đã có liên kết phiếu nhập hủy. Đối chiếu và hủy hồ sơ cũ trước khi lập lượt mới. Nếu hàng thực tế vẫn tại kho, kế toán phải xử lý hồ sơ tiếp nhận thay thế phù hợp; không dùng thao tác hủy để làm mất dấu hàng.

## Ghi nhận nghiệm thu thật

Đại diện nhà máy kiểm cách nhập lượng và tên người nhận; kế toán trưởng kiểm giá và quyền chốt; người kiểm độc lập đối chiếu phiếu cân, phần còn trên đơn và tồn khả dụng. Kiểm một lần nhận đủ, nhận từng phần, hàng có vấn đề, nhận chờ giá, mất phản hồi, hai người cùng nhận và hủy theo lịch sử. Ghi tài khoản/ngày/mã đơn/mã phiếu/kết quả; dữ liệu đại diện thật và máy in kiểm ở đợt nghiệm thu cuối theo quyết định chủ dự án.
