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

Không đổi số đã cấp, hash/series chứng từ cũ hoặc định danh role/DocType; đơn chung mới dùng DBC theo mục dưới. Không tự thêm giữ tồn vật lý từ lúc in, chính sách vệ tinh offline/QR, chuyển hàng kháccompany, hao hụt vận chuyển hoặc hóa đơn một phần chỉ để làm gọn. Mẫu3liên tại docs/de-xuat-mau-3-lien là nháp chủ dự án đang sửa, chưa tích hợp/duyệt; không tự khôi phục phần ký/chân trang đã bỏ trong bản nháp. Thông tin vị trí giấy gốc và trạng thái nhận bản giấy là đề xuất chưa có, ghi thành phần triển khai riêng nếu chốt.

## Hiện trạng sau nhận

Theo quy tắc không dùng tên một công ty cho đơn chung, đơn tạo mới dùng tiền tố DBC (Đơn bán chung), giữ năm và dãy số. Đây là lựa chọn triển khai trung lập, không đổi tên DocType, không rename/backfill số đơn đã tồn tại hoặc sửa liên kết lịch sử. Nội dung "chưa đổi số đơn" ở mốc tiếp nhận là lịch sử; cập nhật này chỉ đổi cách cấp số MỚI, không đổi số cũ.

Thanh bên dùng cấu hình `Custom Sidebar` chính thức trên nền16.52: nhãn chung Vận hành, năm Workspace, ẩn shortcut DocType/Report thuộc package thay vì xóa nguồn. Giữ các mục riêng và lớp người dùng, bộ cài idempotent. Nền không có DocType này giữ Workspace chuẩn; HTTP và ảnh trên nền ghim đã xác nhận cấu hình và ẩn màn cũ cho quản trị; xem mã kiểm12d9d24 trong hồ sơ bàn giao.

Sau tiếp nhận đã thực hiện mã đầu `cc616a3`/PR #26: danh mục dùng chung và năm khu, API nhận diện/gợi ý khách theo quyền, công nợ hóa đơn không cấn chéo, cửa thu tiền chung, giảm nút/in lặp và một bộ giao nhận theo thế hệ phiếu. Kiểm cục bộ454 test (14 skip) +108 lõi đạt; bốn cổng đạt trên12d9d24, đã tải/đọc ảnh và log; chưa phát hành. Không sửa snapshot đơn hoặc dữ liệu giao nhận cũ; không coi lỗi tải/quyền là số0. Mẫu3liên, giữ tồn lúc in, đổi số đã cấp/roleID và các chính sách chưa chốt vẫn ngoài lượt này.

Ứng viên mang phiên bản0.16.3 trên nhánh feat/toi-uu-giao-dien-20261020, PR #26. Đã sửa giao diện và cấu hình điều hướng; không thay quyền hay sổ tài chính. Chỉ thử trên môi trường cô lập, không tác động dữ liệu thật. Kết quả cuối và giới hạn nghiệm thu được ghi tại đầu docs/ban-giao.md và deploy/release/TRANG_THAI.md.

## Đối chiếu phạm vi triển khai

| Nhóm | Kết quả và ranh giới |
|---|---|
| Mục tiêu và phạm vi | Năm khu điều hướng, Nhà máy riêng; giảm nhập/trang/nút lặp. Không xây lại sổ hoặc quy trình giao hàng. |
| Hiện trạng | Nguồn nhận main7dcff5a, ứng viên0.16.3 tại PR #26; production0.16.2. Mã kiểm và bằng chứng cuối ghi tại đầu hồ sơ bàn giao. |
| Quy trình | Bán hàng lập đơn/chuẩn bị giao; Kho vận xác nhận và lưu hồ sơ; Nhà máy nhận/sản xuất; Tiền và kế toán thu–chi/đối chiếu; dữ liệu/cấu hình theo quyền. Các thao tác gọi service hiện có. |
| Quy tắc và ngoại lệ | In chưa ghi xuất/nợ; mất phản hồi thu tiền gửi lại cùng mã lượt; không cấn chéo công ty hoặc FIFO. Phiếu cũ/trả giữ bộ giao nhận cũ; thông tin khách thiếu hoặc không tải được phải báo rõ. |
| Dữ liệu và trạng thái | Giữ trường, Link, ID DocType/role và số đã cấp; đơn mới dùng DBC. Nhận diện khách là hồ sơ hiện tại chỉ đọc, không sửa snapshot giao. Mã/tên hàng riêng. Custom Sidebar là cấu hình native, không tạo bảng nghiệp vụ mới. |
| Phân quyền và kiểm soát | Giữ các hook/guard và quyền chứng từ gốc. API đọc theo quyền native; công nợ theo Company được xem. Menu không cấp quyền; người dùng có tùy chỉnh riêng vẫn giữ lớp cá nhân. |
| Tác động hệ thống | Không đổi thời điểm ghi kho/nợ/tiền, công thức giá vốn/sản xuất hay luồng MISA. Tái dùng bộ thu tiền chống trùng; mẫu ba liên chưa tích hợp. |
| Tiêu chí nghiệm thu | Cổng1/2/2b/UAT/3 trên đúng nguồn, kiểm metadata/API/Chrome và đọc ảnh. Nhân sự, hàng/tồn và máy in thật nghiệm thu cuối theo hướng dẫn. Không suy số đo máy thành tiết kiệm thời gian thực tế. |
| Triển khai và khôi phục | Chủ dự án gắn tag sau khi duyệt; phát hành kiểm lại các cổng. Diễn tập bản sao production và nâng theo runbook; rollback dùng đúng image và snapshot tương ứng. Tắt cờ không tự xóa metadata/khôi phục mọi cấu hình thanh bên. |

Dòng công nợ trên đơn cộng các hóa đơn có số còn phải thu dương trong quyền, không phải số dư công nợ ròng của sổ kế toán. Tiền chưa phân bổ giữ riêng; trả hàng/ghi giảm và việc chốt số đối chiếu ở báo cáo công nợ chuẩn. Không suy tổng này thành số khách phải nộp ngay hoặc tự phân bổ tiền.
