# Đợt 2 — rà nguồn trước khi xây người giữ tiền, chốt ca và bàn giao

Ngày 18/10/2026. Đây là bản rà code và ràng buộc thiết kế, **chưa phải đặc tả đủ để code toàn đợt**, chưa áp schema hoặc thay đổi site. Nguồn nghiệp vụ: `ke-hoach-van-hanh-tiep-noi.md` T01–T07 và các quyết định đã chốt. Nghiệm thu thực tế gom cuối; kiểm UAT dữ liệu giả vẫn bắt buộc từng phần.
Cập nhật triển khai2A: `dac-ta-nguoi-giu-tien-2a.md` và PR #10 đã có mã metadata/báo cáo nguồn, đang kiểm CI; các nhận xét hiện trạng dưới đây là baseline trước2A. Thiết kế tiếp nối chốt ca/bàn giao ở `thiet-ke-chot-ca-ban-giao-2b.md`, chưa có mã2B. Không suy rằng toàn đợt2 đã xong.


## 1. Mục tiêu và phạm vi

Biết tiền mặt đang do ai giữ; đối chiếu số phải có với số đếm; người nhận xác nhận bàn giao; giữ lịch sử thiếu/thừa. Bao phủ cả màn hình mới lẫn các đường thu cũ. Không làm lại thu/cọc/phân bổ/thu hộ; không tự cấn nợ cũ, không tạo bank TL giả hoặc thay đổi nơi thực nhận. Đợt này không giải quyết hóa đơn một phần.

## 2. Hiện trạng đã đọc trong nguồn

| Điểm vào | Cách ghi sổ hiện có | Khoảng cần nối |
|---|---|---|
| `ban_quay.thu_tien` | Tách tiền mặt/chuyển khoản thành Payment Entry, phân bổ các hóa đơn được chọn | Chưa nhận thông tin người giữ tiền; đường này có thể tạo hai phiếu trong một lần gọi |
| Payment Entry chuẩn | Controller ERPNext, `controls.validate_payment_entry`, `money_reference.validate` | Cần phân loại thu/chi/chuyển nội bộ theo từng phía tài khoản Cash; không chỉ kiểm màn bán hàng |
| `controls.sales_invoice_on_submit` | Tự tạo Payment Entry khi chọn thu ngay | Đây là một đường thu bổ sung cần bao phủ, không chỉ phiếu người dùng lập tay |
| `funds.FundsReceipt.on_submit` | Journal Entry ghi tiền thực nhận vào quỹ/bank và tài khoản giữ; Funds Action xử lý cọc/phân bổ/hoàn | Receipt có tuyến và mã chống trùng nhưng chưa có người thực giữ. JE liên kết là cùng một khoản, không được đếm thêm lần nữa |
| Journal Entry chuẩn | Hook kiểm tài khoản, thu hộ, mã giao dịch; controller chuẩn ghi GL | Một JE có thể có nhiều dòng Cash; phải định danh dòng, company, tài khoản và chiều tăng/giảm, không coi cả JE là một khoản thu khách |
| `factory_cash.ghi_so` | Phiếu thu/chi sinh JE; bàn giao chờ người nhận, chưa ghi ngay | Có cơ chế nhà máy để tái dùng, chưa có chốt ca chung |
| `factory_cash.xac_nhan_nhan` | Khóa phiếu; người nhận hoặc quản lý xác nhận số đếm; JE chuyển giữa quỹ/bank cùng company | Chưa có guard rõ cấm cùng người thực giao/thực nhận kể cả cộng quyền; không được bê nguyên quyền ngoại lệ này sang cơ chế mới |

Đây là danh sách điểm vào đã xác minh, **chưa khẳng định bao phủ mọi chứng từ Cash**. Trước code phải rà thêm POS, Purchase Invoice thanh toán ngay, Expense Claim, nhập đầu kỳ, chuyển tiền và chứng từ tự sinh khác đang được bật. Ngân hàng là tiền vào tài khoản, không tự gán người lập làm người giữ tiền mặt.

## 3. Quy trình và trách nhiệm đã chốt

Kế toán bán hàng ghi thu tại quầy và người thực giữ. Kế toán tổng hợp 2 nhận bàn giao, đối chiếu ngân hàng/công nợ; tổng hợp 1 kiểm độc lập theo phân công. Kế toán trưởng xử lý ngoại lệ/chênh lệch. Chủ dự án xem báo cáo và quyết định vượt quyền. Không ai xác nhận nhận từ chính mình. Tên nhân sự/tài khoản thật đối chiếu ở đợt nghiệm thu cuối; không coi role giả lập là bằng chứng đã giao quyền thực tế.

## 4. Quy tắc không được phá

- Khoản thu khách và bàn giao nội bộ có định danh riêng; bàn giao không ghi Có 131/doanh thu thêm lần nữa.
- Cùng tài khoản Cash và company: đổi người giữ có thể chỉ thay trách nhiệm quản lý; không tự tạo bút toán giả tăng/giảm tiền. Khác tài khoản chỉ dùng một chứng từ chuyển tiền chuẩn, liên kết với bàn giao.
- Khóa nguồn và yêu cầu chống trùng khi xác nhận; bấm lại/mất phản hồi trả đúng kết quả cũ. Không chỉ chống trùng trên trình duyệt.
- Tiền chờ nhận không đồng thời khả dụng cho hai người. Chênh lệch giữ riêng, không tự sửa phiếu thu hoặc tự quy trách nhiệm/bù trừ sổ.
- Khoản lịch sử chưa rõ người giữ phải hiện “Chưa xác minh”; không suy từ owner. Không ép số thực đếm bằng số phải có.
- Số tiền hữu hạn, tối đa hai chữ số thập phân; company/quỹ/người nhận phải trong quyền trên server.

## 5. Dữ liệu và trạng thái cần chốt trong đặc tả kế tiếp

Phải có bảng field cụ thể và nguồn cho: người giữ, company, tài khoản Cash, chứng từ/dòng nguồn, số tăng/giảm thực tế, ngày giờ, ca, số phải có/thực đếm, người giao/nhận, số đề nghị/thực nhận, bằng chứng, người xử lý và thời hạn. Bản ghi phát sinh từ Receipt và JE của Receipt phải có một khóa nguồn duy nhất để không đếm hai lần.

Chốt ca và bàn giao có vòng đời riêng, không dùng DocType “Nhiệm vụ” thay chứng từ. Đặc tả tiếp theo cần xác định chính xác khi nào chuyển trách nhiệm tiền, cách xử lý nhận thiếu/thừa, ca qua ngày, hủy nguồn sau chốt, chuyển lại và mở lại ca. Chưa chọn field/DocType chỉ dựa vào tên màn hình.

## 6. Quyền và kiểm soát

Tận dụng vai trò hiện có, native DocPerm/User Permission và Company; API trả đúng trường được phép. Người lập không mặc nhiên có quyền nhận thay; quyền quản lý không vượt guard cấm tự nhận. Dũng giữ chính sách không xem giá vốn kể cả cộng role. Kết quả xác nhận không sửa tay sau submit; sửa/hủy/thay bằng chứng phải có actor/time/lý do và lịch sử. Cần ma trận quyền cụ thể ở đặc tả trước triển khai.

## 7. Tác động hệ thống

Không tác động kho/giá vốn/sản xuất/MISA. Thu/chi và chuyển giữa tài khoản tiếp tục qua chứng từ native; dữ liệu trách nhiệm giữ tiền không thay GL/PLE. Bảng chốt ngày đọc từ nguồn có quyền, không tạo bộ công nợ thứ hai. Đầu kỳ người giữ cần thủ tục xác nhận riêng, không sửa số dư GL đã nhập để khớp.

## 8. Tiêu chí kiểm cần đưa vào bộ UAT

| Ca | Đầu vào/thao tác | Kết quả bắt buộc |
|---|---|---|
| T-U01 | Thu mặt + chuyển khoản một lần tại quầy | Hai phiếu đúng số/company; chỉ phần mặt vào người giữ; nợ giảm đúng một lần |
| T-U02 | Receipt mặt và JE tự sinh; lập phân bổ cọc | Tiền thực chỉ đếm một lần; phân bổ không làm tăng tiền mặt |
| T-U03 | Thu qua PE chuẩn/thu ngay trên SI/JE tay/quỹ nhà máy | Mỗi đường thuộc phạm vi đều có người giữ hoặc trạng thái chưa xác minh theo chính sách đã chốt |
| T-U04 | Chốt ca có thiếu/thừa và ca qua ngày | Giữ nguyên số phải có, số thực đếm và chênh lệch; không sửa sổ cho bằng |
| T-U05 | Hai phiên nhận cùng nguồn, thử lại sau mất phản hồi | Chỉ một bàn giao có hiệu lực; không chiếm nguồn hoặc ghi GL hai lần |
| T-U06 | Người giao tự nhận, kể cả cộng quyền quản lý | Server từ chối |
| T-U07 | Bàn giao cùng tài khoản; khác tài khoản; nộp bank | Không giảm nợ khách lần nữa; chỉ chuyển tài khoản khi có chứng từ tiền thật |
| T-U08 | Hủy thu đã chốt/đã bàn giao; đổi tệp bằng chứng | Chặn hoặc đảo theo quy trình có liên kết; không để số người giữ sai mà không có ngoại lệ |
| T-U09 | Bị giới hạn Company; Dũng cộng vai trò; gọi API trực tiếp | Không vượt phạm vi/không lộ giá vốn |
| T-U10 | Nâng bản sao có số dư và quay lui | Không tự gán lịch sử; tổng tiền/sổ/quyền/schema khớp trước–sau theo runbook |

Chưa có ca nào ở bảng này được tuyên bố PASS cho tính năng mới.

## 9. Triển khai và bước tiếp

Chưa thêm cờ/schema/migration. Trước code: hoàn thiện danh sách nguồn Cash, bảng field/khóa chống trùng, công thức tồn tiền theo người, trạng thái chuyển trách nhiệm và ma trận quyền. Tính năng mới phải có cờ mặc định tắt, bộ cài idempotent rõ ràng; nếu thêm cờ phải cập nhật toàn bộ bộ kiểm/nâng/quay lui theo AGENTS. Sau đó mới triển khai phần nhỏ đầu tiên và kiểm dữ liệu giả; nghiệm thu nhân sự/dữ liệu thật gom cuối. Không triển khai hoặc thay đổi production từ bản rà này.
