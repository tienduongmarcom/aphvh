# Lát bàn giao tiền: giữ chỗ và xác nhận thực nhận

18/10/2026, tiếp PR #11. Tính năng ứng viên, chưa phát hành. Không đổi các quyết định trong docs/quyet-dinh-nghiep-vu.md.

## 1. Mục tiêu và phạm vi

Bàn giao Cash/VND cùng company cho người nhận khác: cùng quỹ chuyển trách nhiệm, khác Cash hoặc nộp Bank tạo một JE chuyển tiền native. Không có 131/doanh thu/thu khách mới, không đổi kho/giá vốn/MISA. Cờ24 `kh_aph_cash_handover` mặc định tắt, cần custody22/closing23. Luồng kế toán có quyền đọc sổ/nguồn; chưa là adapter cho người bán/nhà máy không đọc GL.

## 2. Hiện trạng và nguồn

Kế thừa `cash_custody` (người trên nguồn), `cash_closing` (xác minh/ca), GL chuẩn ERPNext16.51.1/Frappe16.52.0. `APH Ban giao tien` mới có lifecycle riêng. Quỹ đã xác minh mới làm nguồn; khoản chưa rõ không được phân bổ theo owner. Công thức GL ở PR #11 giữ nguyên, thêm delta trách nhiệm chỉ cho cùng quỹ. Các luồng thu quầy và nhận nhà máy cũ giữ như trước, chưa nối adapter ở lát này; không coi toàn bộ đợt2B hoàn tất.

## 3. Quy trình và trách nhiệm

Người thực giao lập nháp của mình, chọn quỹ nguồn/đích, người nhận, số dự kiến và căn cứ. Gửi mới giữ chỗ. Đúng người nhận đăng nhập đếm và xác nhận. Quản lý xem trong phạm vi nhưng không nhận thay, không có ngoại lệ tự nhận cho Administrator. Màn hình native và Dialog nhận, Workspace Tiền và vay có danh sách chờ/ngoại lệ. Người giao hủy đề nghị chưa chuyển để giải phóng nguồn.

## 4. Quy tắc và ngoại lệ

- Gửi không chuyển trách nhiệm/GL. Phải có trừ giữ chỗ đang chờ là khả dụng; khóa nguồn trước khi kiểm, không hai đề nghị chiếm cùng tiền.
- Nhận thực100/95 chuyển95, giữ lệch-5. Nhận0 vẫn lưu thiếu toàn bộ, không tạo JE0. Nhận lớn hơn dự kiến được chuyển theo thực nhận nếu đủ nguồn và có giải trình/người/hạn xử lý.
- Nếu số thực nhận vượt nguồn còn có hoặc ví nguồn đang có lệch, lưu số đếm và trạng thái Vượt nguồn cần xử lý, giữ chỗ; không chuyển GL/trách nhiệm. Retry trả cùng kết quả, không đổi số cũ. Người giao có thể hủy hồ sơ chưa chuyển, giữ nguyên quan sát đã lưu.
- Lát này chặn giao ra trên toàn ví có ca/bàn giao lệch chưa xử lý, cách bảo thủ để không dùng lại tiền tranh lệch; không cộng các khoản thiếu qua nhiều ca. Luồng nhận thêm/chốt số vẫn giữ. **Chưa có nút đóng vụ lệch/mở lại**; không bật vận hành toàn bộ quỹ trước khi nối vòng xử lý này.
- Cùng Cash: delta người giao âm/người nhận dương đúng thực nhận, tổng0, GL/PLE không đổi. Khác Cash/Bank: chỉ JE debit đích/credit nguồn, người giữ trên đúng dòng Cash; không cộng thêm delta cùng-quỹ. JE liên kết không lập tay/gỡ link/sửa/hủy riêng.
- Bản xác minh mới không được tạo khi còn đề nghị chờ ở một trong hai phía. Sau xác minh mới, phân bổ mới là mốc trách nhiệm, các bàn giao cũ vẫn lưu lịch sử và không cộng lại. Ca nháp có dấu trách nhiệm, bàn giao mới sau lúc lưu yêu cầu kiểm lại ca.
- Đã nhận không hủy/sửa tay. Nghiệp vụ đảo có hai phía và kiểm nguồn đã dùng tiếp **chưa triển khai**, nên server chặn; không tự đảo JE hoặc hồi phục backup để sửa hồ sơ.

## 5. Dữ liệu và trạng thái

`APH Ban giao tien`: company, from_account/to_account, from_holder/to_holder, requested_amount, reason, evidence riêng tư đúng hồ sơ; from_verification/to_verification do server lấy; status; sent_by/at, received_by/at; received_amount/difference, receive_reason/assignee/due_date, receive_hash, journal_entry. Track Changes. Kết quả server read_only/no_copy/allow_on_submit, chỉ cập nhật trong service có guard.

Nháp(docstatus0) → Chờ nhận(docstatus1) → Đã nhận/Có chênh lệch; hoặc Vượt nguồn cần xử lý (chưa chuyển). Chờ/Vượt nguồn → Đã hủy(docstatus2), chỉ người giao. Hash nội dung nhận gồm số chuẩn hóa hai số lẻ/giải trình/người/hạn; cùng tên hồ sơ+cùng nội dung trả cũ, đổi nội dung bị từ chối. Snapshot ca thêm transfer_hash. JE thêm Custom Field kh_aph_ban_giao_tien.

Tệp chọn trên hồ sơ phải private/đúng parent; sau gửi không sửa/xóa blob, bảo vệ trước File.on_trash. Nhận sau đó chỉ ghi kết quả, không thay căn cứ ban đầu.

## 6. Phân quyền và kiểm soát

Accounts User chỉ hồ sơ có mình là người giao/nhận; Accounts Manager/System Manager xem theo Company User Permission. Mỗi API kiểm native DocPerm, Company/Account, GL và từng nguồn, user nội bộ hoạt động đúng đơn vị. Người nhận phải có quyền native tạo/submit JE khi chuyển khác quỹ, không ignore_permissions. NoCost/nhà máy bị chặn kể cả cộng role; không cấp thêm GL. Administrator được chuẩn hóa role quản lý vì Frappe tự trả mọi role (kể cả NoCost), nhưng guard actor/tự nhận luôn áp dụng.

Khóa các Cash account theo company/name, current read GL/nguồn và hồ sơ; khóa ngân hàng theo native JE. Gửi/nhận/hủy trong một transaction, không commit giữa JE và nhận. Status doc được cập nhật qua flag server có phạm vi đúng hồ sơ, client không sửa trực tiếp. Các bản nháp khác/nguồn mới được đọc lại khi khóa; retry theo tên hồ sơ không sinh JE lần hai.

## 7. Tác động hệ thống

Không sửa sổ tài chính khi chuyển trách nhiệm cùng quỹ. Khác quỹ chỉ hai dòng tiền; native controller giữ kiểm tài khoản/kỳ/tiền. Kho/công nợ/doanh thu/giá vốn/sản xuất/MISA giữ luồng hiện có. Báo cáo tiền cá nhân thêm giữ chỗ/khả dụng và cờ tranh lệch, không trả toàn bộ sổ hoặc người khác.

## 8. Tiêu chí nghiệm thu

- Quỹ giả1000 phân700/200/chưa rõ100; gửi50 giữ chỗ, nhận50 →650/250, GL/PLE không đổi; hủy trước nhận trả khả dụng.
- Bàn giao sau lưu ca làm ca nháp lỗi thời. Còn chờ nhận không đổi mốc xác minh.
- Dự kiến100/thực95 → chuyển95, lưu-5, retry cùng trả cũ/đổi nội dung bị chặn. Giao ra khi ví tranh lệch bị chặn.
- Khác Cash100/nộp Bank500 mỗi lần một JE/hai GL, không PLE/131/doanh thu, trách nhiệm giảm/tăng đúng một lần; JE không gỡ link/hủy tay.
- Hai đề nghị300 trên nguồn400 chỉ một gửi được; hai phiên nhận chỉ một JE. Chrome chặn phản hồi200 sau commit rồi nhận lại cùng Dialog không tạo thêm JE/GL/PLE.
- Sau gửi50, nguồn chi90/100 còn10: số đếm50 được lưu, không tạo tiền mới; scope/NoCost/nhận thay/tự nhận bị chặn, kể cả Admin.
- Kiểm cờ tắt, cài lặp, nâng/site mới và rollback. Không dùng unit hoặc kết quả PR #11 làm bằng chứng toàn bộ mã mới.

## 9. Triển khai và khôi phục

Schema qua bộ cài rõ ràng; không hook after_migrate, không tạo dữ liệu trách nhiệm lịch sử. Thêm cờ vào installer/preflight/dấu vân/rollback/C3/UAT, FLAGS_MOI hiện ba cờ mới so production0.15.3. Chưa tăng version/tag/deploy; chủ dự án tự gắn tag khi bản đủ điều kiện. Diễn tập bản sao dữ liệu hiện tại theo runbook trước nâng thật; quay lui snapshot/image/cờ trong bảo trì, không restore mất giao dịch sau mở nhập liệu. Nghiệm thu người dùng thật gom cuối; còn adapter nhà máy/thu cũ, đóng vụ lệch, đảo và quyền tiền cá nhân không GL trước khi gọi toàn bộ2B hoàn tất.
