# Tiếp nhận và phạm vi tối ưu giao diện kế tiếp

## Mốc nguồn và bằng chứng tiếp nhận

Tiếp nhận PR #25, main `7dcff5a98801a032e0336c9adcde6741d97693b4`. Đã đối chiếu diff so `72e6a0b`: chỉ AGENTS, hai hồ sơ và hai bản nháp HTML; không thay mã nghiệp vụ. GitHub không có PR mở tại thời điểm nhận. Production theo hồ sơ người vận hành là0.16.2/digest34a32f71f10f20421405c0bd1155abb0570b1d48b564f1df6b8e25d6aa146917/28cờ, không trực tiếp kiểm VM trong lần này.

Đã đọc trạng thái GitHub: UAT39427294383, Cổng2 39427281958, Cổng2b39427285899, Cổng3 39427290220 đều success và headSha95a8b1e63358b190faccfa300010445ee799cac9. Phát hành39432250494 success đúng95a8b1e; Cổng3 mốc0.16.2 run39441058175 success đúnge062287. Không lấy các kết quả này làm PASS cho thay đổi mới.

Đã tải candidate-image-evidence từ UAT39427294383 về work/ci-handoff-0162/uat (ngoài repo), đọc13 tệp http-*-evidence.txt:308 bản ghi statusPASS,0FAIL, bao gồm kiểm kỹ thuật/chuẩn bị/khôi phục; b014117PASS. Đã xem ux-viec-ban-hang.png: có cả Trung tâm/Bàn và tên kỹ thuật ở thanh bên trong phiên Administrator tiếng Anh; không chứng minh mọi người dùng tiếng Việt cũng thấy như vậy. Ảnh đang trong trạng thái làm mờ/nạp, chưa dùng để kết luận khả năng đọc cuối cùng hoặc xác nhận cột mới.

Ca nhan-hang-nha-may chập chờn chưa rõ nguyên nhân vẫn mở. Ca quy-nha-may có sửa b23ca5f cần tiếp tục theo dõi; không coi việc nhận bàn giao là đã giải quyết hai ca.

## Yêu cầu mới nhất từ chủ dự án, thay cho mục chờ chốt cũ trong hồ sơ Claude

- Bốn khu vận hành: Bán hàng; Kho vận; Nhà máy; Tiền và kế toán. Một khu Dữ liệu và cấu hình theo quyền. Nhà máy tách riêng để mở rộng sản phẩm; tái dùng service/kho/mã hàng/chứng từ chuẩn, không nhân bản dữ liệu.
- Không dùng tên một công ty làm tên chung hệ thống. Tên hiển thị trung lập; chỉ giữ APH khi thật sự là công ty An Phú Hưng/chủ hàng/kho/chế độ kế toán. Tên kỹ thuật giữ nguyên theo AGENTS, không replace hàng loạt.
- Đầu đơn chọn khách phải luôn hiện tên/mã/điện thoại/địa chỉ; gợi ý tìm khách có thông tin phân biệt trùng tên. Không thu gọn điện thoại/địa chỉ sau khi chọn. Địa chỉ giao của đợt khác địa chỉ hồ sơ khách.
- Bảng hàng: mã hàng và tên hàng hai cột riêng; chọn mã tự tải tên chỉ đọc, đổi mã không giữ tên cũ; gợi ý tìm có mã và tên.
- Công nợ thường ngày chỉ dòng Còn phải thu / Trong đó quá hạn và xem chi tiết. Có cọc/tiền chưa phân bổ mới hiện dòng tương ứng; khi giao chọn rõ sử dụng, không FIFO/cấn nợ cũ tự động.
- Giảm nhập lại/chuyển trang/nút trùng, không nhồi hết thông tin lên đầu đơn. Phần kỹ thuật giữ dưới nền, nguồn/lịch sử không mất.
- Ưu tiên lấy tại kho (khách hoặc lái xe khách khoảng90%); phân biệt gom nội bộ, giao vệ tinh và gửi vận chuyển. Không tự đổi thời điểm ghi kho/nợ.

## Trình tự và ranh giới

1. Map đủ chức năng cũ vào khu mới và role/ngữ cảnh; đối chiếu28 đối tượng nguồn (27JSON và APH Credit Release tạo động),24báo cáo,7Print Format+A5. Không tạo menu bảng con.
2. Chuẩn tên/nhãn/dịch/điểm gọi; đồng bộ ux_buoc_tiep và ca Chrome còn tìm nút theo chữ. Không gọi mọi Xác nhận thực nhận là nhận hàng: bàn giao quỹ là nhận tiền.
3. Gọn form/bảng: giữ nhận diện khách/hàng; hiện vận chuyển/bao/ngoại lệ theo điều kiện; tự điền số dẫn xuất và actor/time.
4. Hợp nhất cửa thu tiền và nhóm in trên service có sẵn; đối chiếu hai bộ giao nhận và hai nơi tham chiếu MISA trước khi ngừng nhập ở một bên. Không sửa mù dữ liệu cũ.
5. Ẩn bộ Workspace/nút dư sau đủ lối thay thế, bảo toàn route/default user/module profile và fallback cờ tắt. Sửa bộ lọc chuyển kho không lẫn yêu cầu mua; phân chuyến đi/đến theo scope.
6. Kiểm idempotent/cờ bật-tắt/quyền/company/kho/NoCost, retry/concurrency, native links/search/import/export/print, tiếngViệt/Anh. Đủ cổng đúngSHA trước phát hành; không tự gắn tag hoặc triển khai production.

## Những nội dung chưa tự quyết

Không đổi số đơn, hash/series chứng từ cũ, định danh role/DocType, giữ tồn vật lý từ lúc in, chính sách vệ tinh offline/QR, chuyển hàng kháccompany, hao hụt vận chuyển hoặc hóa đơn một phần chỉ để làm gọn. Mẫu3liên tại docs/de-xuat-mau-3-lien là nháp chủ dự án đang sửa, chưa tích hợp/duyệt; không tự khôi phục phần ký/chân trang đã bỏ trong bản nháp. Thông tin vị trí giấy gốc và trạng thái nhận bản giấy là đề xuất chưa có, ghi thành phần triển khai riêng nếu chốt.

## Hiện trạng sau nhận

Đã nhận và xác minh hồ sơ/nguồn/trạng tháiCI, đã ghi yêu cầu hội thoại vào nguồn. Chưa sửa code/schema/quyền, chưa tăng version hoặc phát hành. Bước tiếp theo là thực hiện lượt chuẩn tên/điều hướng và đối chiếu lối nghiệp vụ trên nhánh feat/toi-uu-giao-dien-20261020; kiểm trên site thử, không tác động dữ liệu thật.
