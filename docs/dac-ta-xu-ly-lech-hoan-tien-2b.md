# Xử lý lệch và hoàn bàn giao tiền — tiếp PR #12

19/10/2026. Ứng viên sau6431ec0, chưa phát hành. Dùng cờ24 kh_aph_cash_handover mặc định tắt (cần custody/closing); không thêm sổ tiền độc lập.

## 1. Mục tiêu và phạm vi

Khép vụ lệch của ca hoặc bàn giao bằng đối chiếu có căn cứ; cho hoàn toàn bộ số đã nhận bằng phiếu ngược chiều, kể cả Cash–Bank. Giữ nguyên số đếm, chênh lệch, JE và người/thời điểm nguồn. Chưa nối adapter nhà máy/thu quầy cũ, chưa là toàn bộ2B.

## 2. Hiện trạng

PR #12 đã kiểm giữ chỗ/nhận/chống tự nhận và retry (249 HTTP/Desk,338+108 unit,4 cổng đúng1787448). Chưa có đóng/mở lại vụ lệch hoặc hoàn; mã nguồn ở cash_closing.py/cash_handover.py. ERPNext16.51.1/Frappe16.52.0, production0.15.3 giữ nguyên.

## 3. Quy trình và trách nhiệm

Kế toán trưởng lập hồ sơ Đối chiếu lệch tiền trên ca/bàn giao. Người giữ kiểm đếm lại và tự chốt ca khớp sau xác minh quỹ mới. Kế toán trưởng liên kết đúng mốc xác minh/ca của từng phía Cash, ghi kết quả và tệp riêng tư, xác nhận hồ sơ. Hủy hồ sơ đối chiếu mở lại vụ lệch; giữ lịch sử hồ sơ/tệp đã hủy.

Người đã nhận lập phiếu hoàn từ bàn giao gốc; quỹ/người đảo đúng hai phía và số tiền bằng toàn bộ thực nhận. Phiếu hoàn gửi giữ chỗ; đúng người giao ban đầu xác nhận nhận lại. Không tự nhận hoặc quản lý nhận thay. Tiền đã dùng tiếp/đang giữ chỗ/đang tranh lệch không được hoàn vượt nguồn. Chỉ hoàn một lần toàn bộ; không hoàn từng phần hoặc hoàn tiếp phiếu hoàn.

## 4. Quy tắc và ngoại lệ

Đối chiếu không tự tạo JE, chi phí hoặc khoản phải thu nhân viên. Nếu cần sửa sổ, kế toán dùng chứng từ chuẩn theo quyền trước khi xác minh và kiểm đếm lại. Chốt vụ là ghi nhận kết quả điều tra/đối chiếu, không làm biến mất chênh lệch cũ hoặc coi số đếm mới là GL. Không chốt vụ bàn giao còn chờ nhận/vượt nguồn: nhận hoặc hủy đề nghị trước.

Mốc xác minh mới phải sau thời điểm ca/nhận gốc, còn là mốc hiện tại. Mỗi phía Cash có ca mới đúng người, khớp0, thuộc mốc này và còn khớp GL/dấu trách nhiệm tại lúc xác nhận đối chiếu. Hai hồ sơ cùng nguồn chỉ một được xác nhận. Hủy đối chiếu mở lại chặn giao ra ngay; không đảo tài chính. Bằng chứng cũ giữ nguyên.

Hoàn là giao dịch bù mới: cùng Cash hai delta ngược nhau; khác Cash/Bank một JE ngược chiều mới. Không cancel JE gốc. Bank chỉ làm nguồn cho phiếu hoàn đã liên kết đúng gốc, không mở luồng chi Bank tùy ý. Khóa quỹ theo company trước mọi đọc nguồn; Bank kiểm đủ số dư hiện tại trừ toàn bộ giữ chỗ, không dùng số riêng theo người. Nhận hoàn bắt buộc đủ đúng số, không thêm biến thể thiếu/thừa. Hủy đề nghị hoàn trước nhận có thể lập lại bằng yêu cầu mới; retry cùng mã yêu cầu trả đúng hồ sơ cũ kể cả đã hủy.

## 5. Dữ liệu và trạng thái

Hai DocType native: APH Doi chieu lech tien (nguồn ca/bàn giao, company server, kết quả, tệp, bảng căn cứ, actor/time server) và APH Can cu doi chieu quy (account/holder cố định theo nguồn, verification/shift). Nháp→đã xác nhận→hủy/mở lại. Nguồn lưu issue_state và issue_resolution chỉ server; source status/số tiền cũ không đổi. Track Changes và bình luận liên kết giữ audit.

Bàn giao thêm reversal_of/reversal_request và reversal_doc (read_only/no_copy). Yêu cầu hoàn có mã chống trùng và lý do, chỉ server tạo quan hệ; số/người/quỹ không sửa khỏi gốc. Phiếu hoàn chạy cùng lifecycle bàn giao. Bản gốc giữ liên kết phiếu hoàn mới nhất; các lần hủy trước vẫn truy theo reversal_of. Không tuyên bố đã hoàn khi phiếu ngược mới ở nháp/chờ nhận.

## 6. Phân quyền và kiểm soát

Đối chiếu: Accounts Manager/System Manager, native Company/Account/GL/nguồn và quyền nguồn; NoCost/nhà máy bị chặn kể cả cộng quyền. Không cấp thêm GL. Người giữ không chốt vụ của mình bằng Accounts User. Actor/timestamp do server; file riêng tư đúng parent, giữ blob sau submit/cancel. Không sửa tay kết quả nguồn hoặc quan hệ hoàn.

Hoàn: người đã nhận tự tạo/gửi, người giao ban đầu tự nhận lại; native quyền JE vẫn bắt buộc. Admin không nhận thay. Request/cancel/receive là transaction, retry nguyên RPC tối đa3 khi xung đột DB; không commit giữa nguồn/JE/kết quả.

## 7. Tác động hệ thống

Không đổi kho/doanh thu/131/PLE/MISA. Đối chiếu chỉ gỡ chặn sau đủ căn cứ. Hoàn khác quỹ ghi đúng hai dòng Cash/Bank và người thực giữ trên dòng Cash; Bank không gán người giữ tiền mặt. Native engine giữ kỳ/tài khoản/tiền. Ca nháp cũ mất hiệu lực khi hoàn cùng quỹ đổi trách nhiệm.

## 8. Tiêu chí kiểm

Đóng vụ thiếu/thừa, ca lệch, vụ vượt nguồn đã hủy; từ chối mốc cũ/ca lệch/sai người/sai quỹ/sổ đổi/thiếu tệp/cộng NoCost. Hai phiên xác nhận cùng nguồn chỉ một; hủy đối chiếu mở lại ví và giữ tệp. Không phát sinh GL/PLE khi đóng/mở.

Hoàn cùng Cash/khác Cash/Bank về Cash, số dư/giữ chỗ/đếm GL/PLE đối chiếu đúng. Chặn tự nhận/nhận thay, sửa liên kết, sai số, hoàn tiếp, hoàn trùng, nguồn đã dùng. Hai phiên tạo/nhận và mất phản hồi không sinh thêm phiếu/JE. Giữ toàn bộ249 ca cũ, bổ sung HTTP/Chrome và unit ranh giới; đủ4 cổng đúng mã cuối trước kết luận đạt.

## 9. Triển khai và khôi phục

Schema rõ trong bộ cài, không after_migrate; cài lại không tự xử lý lịch sử. Ca lệch cũ có issue_state trống vẫn bị chặn cho đến có hồ sơ đối chiếu hợp lệ. Cờ24/phiên bản giữ nguyên; không tag/merge/deploy. Diễn tập CI nâng/site mới/rollback và cố ý lỗi; khi phát hành còn cần bản sao production có dữ liệu. Không tắt riêng cờ sau phát sinh. Nghiệm thu người dùng/dữ liệu/máy in thật gom cuối theo anh Tiến.
