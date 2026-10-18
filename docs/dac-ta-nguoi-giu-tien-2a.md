# Đợt 2A — Người giữ tiền trên nguồn và bảng rà phát sinh

Ngày18/10/2026. Thiết kế và mã ứng viên đã đạt bốn cổng trên929d16a:317+108 unit,236 UAT PASS/0 FAIL (b01445); chưa phát hành. Bằng chứng và giới hạn ở đầu `ban-giao.md`. Nguồn nghiệp vụ: kế hoạch5 đợt/T01–T07, quyết định không FIFO/không tráo company, yêu cầu người giữ trên cả đường thu cũ. Phần chốt ca/bàn giao chung thuộc2B, không coi đã hoàn thành từ2A.

## 1. Mục tiêu và phạm vi

Ghi được người thực giữ/nhận/chi tiền mặt ngay trên nguồn, có bảng rà nguồn thiếu thông tin. Không mặc định người lập là người giữ. Không có bút toán hoặc bộ số dư mới; báo cáo đọc GL. Nhập liệu bằng form/child table chuẩn và Dialog thu tiền hiện có, điều hướng Workspace Tiền và vay. Không tạo Page/SPA mới.

2A chưa trả lời “hiện mỗi người còn giữ bao nhiêu”: chưa có chuyển trách nhiệm cùng tài khoản, chốt ca, xử lý chênh lệch hoặc xác minh người giữ cho giao dịch lịch sử. Những việc này không được suy từ tổng phát sinh trong báo cáo.

## 2. Hiện trạng và bằng chứng nguồn

Baseline production0.15.3, tag96a7ef0, đã ghi nhận triển khai. PR #9 bổ sung in lại A5 chưa phát hành; nhánh2A dựa trên #9. Nguồn rà ở `dot-2-ra-soat-nguon-tien.md`.

| Nguồn Cash | Cách ghi người giữ ở2A | Giới hạn |
|---|---|---|
| Payment Entry chuẩn/quầy/thu ngay SI | Phía paid_to dùng người nhận, paid_from dùng người giao; quầy chỉ truyền vào phiếu tiền mặt | Không tự gán cho chuyển khoản hoặc phiếu lịch sử |
| Journal Entry chuẩn | Từng dòng Journal Entry Account | Cùng tài khoản Cash phải cùng người, kể cả không trộn dòng đã rõ với dòng chưa rõ; GL có thể gộp dòng |
| Funds Receipt | Ô người nhận truyền vào dòng Cash của JE tự sinh | Báo cáo đếm JE trên GL, không đếm thêm Receipt |
| Funds Action hoàn/chi thu hộ | Người giao truyền vào quỹ chi; người nhận truyền vào quỹ nhận của chủ hàng | Kiểm company theo từng phía; thao tác cấn/giữ cọc không tạo tiền mặt |
| Phiếu quỹ nhà máy | Ô người giữ cho quỹ nguồn; bàn giao cũ dùng người nhận đã chọn cho phía nhận Cash | Giữ cơ chế nhà máy hiện có; chưa thay bằng bàn giao chung/chốt ca |
| SI/Purchase Invoice/POS Invoice ghi Cash trực tiếp | Một người trên đầu phiếu cho các dòng Cash của phiếu đó | Nếu thực tế nhiều người thì tách nguồn; POS tổng hợp không được tự suy người giữ từ phiếu ca/POS gốc |
| Nguồn khác/nhập đầu kỳ/Expense Claim/JE cũ | Dòng GL vẫn có thể hiện nếu được quyền; thiếu metadata hiện Chưa xác minh | Chưa có adapter cho mọi nguồn; không coi là đã xác minh người giữ |

Đã đọc meta chuẩn PE/PI/GL từ kho chính thức ERPNext tagv16.51.1: PE dùng paid_from/paid_to, PI cash_bank_account; GL có account/company/is_cancelled/debit/credit. Việc cài thực tế và native UI phải được kiểm trên image CI.

## 3. Quy trình nghiệp vụ

Người lập chọn tài khoản và nhập người thực giữ phù hợp, lưu/submit như cũ. Có thể để trống trong2A; khi đó báo cáo ghi Chưa xác minh, không gán owner. Kế toán mở Tiền và vay → Rà người giữ tiền mặt → chọn company và tối đa31 ngày để đối chiếu với phiếu nguồn. Người có quyền sửa nguồn nháp bổ sung thông tin trước submit. Phiếu đã submit giữ nguyên, không có API cập nhật hàng loạt người giữ lịch sử trong2A.

Kế toán bán hàng ghi thu tại quầy; người dùng kế toán rà nguồn. Kế toán tổng hợp2 nhận bàn giao và tổng hợp1 kiểm độc lập là trách nhiệm vận hành đã chốt, nhưng thao tác bàn giao mới chỉ có ở2B. Kế toán trưởng xử lý ngoại lệ. Nhân sự thật đối chiếu cuối, không tạo tài khoản nhân viên thật từ fixture.

## 4. Quy tắc và ngoại lệ

- Tiền mặt xác định từ Account.account_type=Cash, không suy từ tên111 hoặc phương thức thanh toán.
- Không thay account/amount/reference/route/company vì chọn người giữ. Khoản chuyển khoản không cộng vào tiền mặt.
- Link User phải là tài khoản nội bộ đang hoạt động, không Guest, và có quyền Company tương ứng. Company của Funds Action phía chủ hàng kiểm riêng.
- Metadata trên nguồn submit không đổi/xóa; sửa thông tin phải theo quy trình nguồn/ngoại lệ sau, không ghi đè lịch sử. Cancel/amend chuẩn vẫn theo quyền/controller; bản amend không tự sao chép người giữ.
- Một accountCash trong một JE không có hai người khác nhau; không chia tùy tiện một dòng GL gộp cho nhiều người.
- Nguồn không đọc được hoặc không có adapter/metadata trả Chưa xác minh; không đọc vòng qua quyền để tìm tên người.
- Báo cáo loại GL is_cancelled, tối đa5.000 dòng; vượt thì yêu cầu thu hẹp ngày, không cắt âm thầm. Không cộng tổng thành số tiền đang giữ.

## 5. Dữ liệu, nguồn và trạng thái

| Field | Loại | Vị trí | Nguồn/quy tắc |
|---|---|---|---|
| kh_aph_nguoi_giu_tien | Link User, không mặc định, no_copy | PE/SI/PI/POS/Funds Receipt/Funds Action/Phiếu quỹ nhà máy | Người nhận ở PE; người giữ phía nguồn ở các phiếu khác; nhận thu hộ của chủ hàng ở Funds Action |
| kh_aph_nguoi_giao_tien | Link User, không mặc định, no_copy | PE/Funds Action | Người giao phía paid_from hoặc phía thực chi |
| kh_aph_nguoi_giu_tien | Link User, no_copy | Journal Entry Account | Một người/quỹ trên phiếu; truyền từ nguồn tự sinh hoặc nhập tay |
| holder/status | Chỉ trả từ API | Dòng báo cáo GL | Đã ghi người giữ trên nguồn / Chưa xác minh; không phải trạng thái bàn giao/kiểm đếm |
| gl_entry/voucher_type/voucher_no | ID gốc | Báo cáo | GL là nguồn định danh dòng; không tạo ID thu mới |

Không thêm DocType hoặc bảng số dư. Schema gọi rõ ràng khi cờ bật; không after_migrate. Trường ẩn khi cờ tắt qua boot/dependency. Ngày, account, debit/credit lấy trực tiếp GL trong scope, tên người chỉ lấy từ nguồn có quyền đọc.

## 6. Phân quyền và kiểm soát

| Hành động | Điều kiện |
|---|---|
| Ghi người giữ trên nháp | Quyền write/create native của nguồn, Link hợp lệ và quyền Company của người được chọn |
| Submit/cancel | Quyền native và kiểm controller cũ; metadata không cấp thêm quyền |
| Sửa người giữ sau submit | Server từ chối, không phụ thuộc nút UI |
| Rà báo cáo/API | Accounts User/Accounts Manager/System Manager + read Company/GL/Account theo native; từ chối tổ hợp có APH Không xem giá vốn hoặc Kế toán nhà máy |
| Đọc tên người từ nguồn | Chỉ khi đọc được nguồn đúng company; không trả items/giá vốn/as_dict |
| Cài schema | Qua bộ cài Administrator/site đúng và cờ; không endpoint cài công khai |

Form nguồn giữ lịch sử sửa nháp theo controller/native Version; không có sổ trách nhiệm bất biến riêng trong2A. Report chỉ đọc, không lưu lần xem/khóa nguồn/commit, không thay người giữ. Quyền print/export báo cáo theo native; API chỉ trả trường allowlist tiền mặt.

## 7. Tác động hệ thống

Không tạo GL/PLE/SLE/PE/JE khi rà. Thu/chi cũ giữ cách ghi sổ chuẩn; chỉ thêm metadata. Không tăng doanh thu/giảm nợ thêm lần nữa, không MISA, không ảnh hưởng giá vốn/sản xuất. Tắt cờ không xóa metadata; đường native vẫn hoạt động. Không biến người giữ trên một khoản thu lịch sử thành người hiện giữ khoản đó.

## 8. Tiêu chí kiểm

Unit: cờ tắt không query/ghi; không suy owner; người ngoài Company/bị vô hiệu/Website/Guest bị chặn; gộp cùngCash khác người bị chặn; bank không nhận người giữ trên dòng JE; hai phía PE độc lập; nguồn submit bất biến; report chặn role/scope/ngày/quá5.000, cache nguồn và không ghi.

HTTP/nativeUAT: thu quầy mặt+bank tách đúng; nguồn chuẩn/không rõ, chặn sửa sau submit; Receipt→JE và hoàn tiền→JE giữ người đúng phía, GL chỉ đếm một lần; Dũng cộng quyền/Company khác bị chặn; báo cáo chuẩn chạy và không tăng sổ; Chrome mở PE thấy người đã lưu và form sạch. Ca2A chỉ dùng dữ liệu giả và rollback bằng runner hiện có. Kết quả phải đọc đúng SHA, chưa có bằng chứng thì không ghi PASS.

## 9. Triển khai và khôi phục

Cờ thứ22 `kh_aph_cash_custody` mặc định tắt, cập nhật FLAGS bộ cài/preflight/dấu vân/quay lui; Cổng3 giữ21 cờ production cũ, FLAGS_MOI chứa đúng cờ mới. Cài thêm10 Custom Field và báo cáo, không tạo dữ liệu người giữ hoặc sửa sổ. Bộ cài chạy lặp phải không tăng field/quyền; schema nâng phải khớp site mới. Khi cờ tắt hook return sớm, form không dùng metadata và API báo chưa bật.

Không đổi version/tag/production trong lượt phát triển. Phát hành sau bốn cổng đúng SHA; khi nâng thật diễn tập bản sao production có dữ liệu, truyền cờ mới theo runbook. Quay lui trong bảo trì phải trả CSDL/tệp/image/cờ từ snapshot tương ứng; sau mở nhập liệu không restore mù. Nghiệm thu thực tế người dùng/số dư/máy in gom cuối theo quyết định chủ dự án.
