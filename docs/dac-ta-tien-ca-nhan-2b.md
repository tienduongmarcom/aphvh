# Tiền cá nhân không cấp GL — bước nền trước adapter nhà máy

## 1. Mục tiêu và phạm vi

Cho người bán/nhà máy xem số tiền theo trách nhiệm của chính mình. Chỉ đọc; chưa mở chốt ca, gửi/nhận/hoàn bàn giao cho nhà máy. Adapter phiếu quỹ cũ sang giữ chỗ/đối chiếu canonical và bảng chốt ngày vẫn còn tiếp. Không gọi đợt2B hoàn tất.

## 2. Hiện trạng và nguồn

Kế thừa PR #14/a50f5f1, production theo xác nhận vẫn0.15.3/21 cờ. Luồng cash_closing.current cần quyền GL/nguồn và từ chối NoCost/nhà máy. Facade mới kh_aph.personal_cash dùng chung cash_closing._state, position/fingerprint và delta bàn giao; giữ nguyên quyền luồng native. Không tạo sổ tiền hoặc DocType mới.

## 3. Quy trình và trách nhiệm

Mở form Khách hàng hoặc Phiếu quỹ nhà máy → Tiền tôi đang giữ → chọn đơn vị/quỹ → Xem số tiền. Kế toán quản lý phải xác minh số bắt đầu trước. Người giữ xem trách nhiệm, giữ chỗ, khả dụng và thời điểm kiểm tra. Đây không phải tiền thực đếm. Chênh lệch/mốc lỗi phải chuyển kế toán đối chiếu; không tự lấy số đếm làm số bắt đầu.

## 4. Quy tắc và ngoại lệ

Không nhận holder từ client; luôn lấy session.user, kể cả quản lý. Không suy owner. Chưa rõ người nằm ngoài số cá nhân. Sổ trước mốc thay đổi, sổ trước ca bị sửa hoặc ghi lùi ngày đều báo cần xác minh theo công thức hiện có. Giữ chỗ chỉ đề nghị của chính người tại Cash nguồn. Cùng Cash đã nhận chỉ chuyển trách nhiệm, khác Cash đã ghi GL thì không cộng delta lần hai. Nhóm bất kỳ âm hoặc vụ lệch của chính người chưa đóng: khả dụng0, vẫn giữ số trách nhiệm để giải thích. Ca lệch người khác không trả chi tiết. Mốc chưa có hoặc hơn10.000 dòng không trả số đoán/cắt bớt.

## 5. Dữ liệu và trạng thái

Hai RPC chỉ đọc: accounts(company) trả tên Cash hợp lệ; current(company, account) chỉ trả expected_amount, reserved_amount, available_amount, disputed, checked_at. Không trả GL, tên nguồn, đối ứng, chi phí, phân bổ người khác, người xử lý hay hash mốc. Projection nội bộ chỉ đọc các cột Cash cần cho fingerprint và metadata người giữ/giao của PE, dòng Cash JE, SI/PI/POS. Không tải chứng từ chi phí đầy đủ. Cùng khóa Cash theo Company và current read như luồng ghi sổ; không commit giữa chuỗi. Tái dùng kiểm mốc/ca và delta hiện có, không lưu snapshot thứ hai.

## 6. Phân quyền và kiểm soát

Yêu cầu custody+closing bật, tài khoản nội bộ đang hoạt động, vai trò Accounts User/Accounts Manager/System Manager/Kế toán bán hàng/Kế toán nhà máy và native Company read. Người thông thường cần Account read và User Permission native. NoCost hoặc nhà máy (kể cả cộng quản lý) chỉ được chọn đúng Company.kh_aph_quy_nha_may khi factory_cash bật; kiểm User Permission Account riêng, Cash chi tiết VND đang hoạt động. Capability này cố ý đọc nội bộ Cash/metadata sau scope mà không cần GL hoặc quyền chứng từ nguồn; tuyệt đối không mở các quyền ấy. Không set_user/Administrator, không thay guard native hoặc DocPerm. RPC raw/nested/invoice/GL vẫn theo chặn hiện có.

## 7. Tác động hệ thống

Chỉ đọc số từ nguồn GL + mốc trách nhiệm và bàn giao. Không sửa nguồn, không ghi thu, JE, GL, PLE, kho, giá vốn, sản xuất hoặc MISA. Nút readonly trên hai form native, dùng cờ closing hiện có; không Page/SPA mới. Khi đổi Company/quỹ xóa số cũ, bỏ phản hồi đã lỗi thời; mất mạng nhả nút để đọc lại.

## 8. Tiêu chí kiểm

Unit: cờ tắt/Guest/vai trò ngoài phạm vi, Company/Account, NoCost cộng quản lý, Cash/Bank/VND/disabled/group, Account rỗng, allowlist nguồn/cột, không cắt dữ liệu, giữ chỗ đúng người, nhóm chưa rõ âm và vụ lệch. HTTP trên quỹ riêng:1000 phân300 nhà máy/600 kế toán/100 chưa rõ; thu nhà máy25 và PE7 → nhà máy332; JE11 chưa rõ không cộng cho owner. Kế toán gửi40 cùng Cash → giữ chỗ40/khả dụng560, người khác giữ chỗ0; nhận chuyển560/40, không thêm sổ. Hủy PE7 → nhà máy325; ca kế toán lệch chỉ chặn người đó; hủy GL trước mốc phải báo xác minh. Native GL/mốc/JE vẫn bị chặn với nhà máy, Company/Account ngoài phạm vi bị chặn. Chrome dùng cookie tài khoản nhà máy giả qua stdin (không Administrator), Dialog readonly/chỉ đúng quỹ; cố ý bỏ200 rồi đọc lại, không thêm sổ. Bốn cổng phải đạt cùng SHA. Dữ liệu/nhân sự/máy in thật nghiệm thu cuối theo anh Tiến.

## 9. Triển khai và khôi phục

Không schema, cờ, version hoặc tag mới; candidate vẫn24 cờ mặc định tắt ba cờ tiền, production21. Boot bổ sung cash_closing để hiện nút; tắt cờ trả lỗi trước đọc. Cần asset app tương ứng và clear-cache theo runbook khi phát hành. Không after_migrate hoặc cấp thêm quyền native. Rollback vẫn image + DB/files/cờ đồng thời theo runbook; không tắt riêng bàn giao sau phát sinh để xóa trách nhiệm. Chưa phát hành/triển khai ở bước này. Nối adapter nhà máy sau khi facade chỉ đọc được kiểm, giữ tiền cũ chưa rõ ngoài tự động hóa.
