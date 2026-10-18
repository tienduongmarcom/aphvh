# GN09 — Hồ sơ xử lý chênh lệch giao nhận

## 1. Mục tiêu và phạm vi

Tiếp nối đợt 1A của PR #5. Biết chênh lệch nào còn mở, ai phụ trách, hạn xử lý, căn cứ và kết quả. Hồ sơ nằm trên Delivery Note (DN) nguồn, không tạo DocType Nhiệm vụ hoặc sổ lượng/tiền riêng. Không đổi ba trạng thái giao hàng. GN10 xuất ngay, màn nhà máy/chốt ca và hóa đơn MISA một phần không thuộc thay đổi này.

## 2. Hiện trạng và nguồn

Production 0.15.2 chưa có vòng xử lý; `ho_so_giao_nhan` có tệp/ghi chú và dấu đối chiếu. Đợt 1A (mã đã kiểm `5155ca4`) thêm thông tin giao nhận và hai liên. GN09 chưa phát hành; SHA/run kiểm được ghi ở đầu `docs/ban-giao.md` và `deploy/release/TRANG_THAI.md`.

Tái dùng `sales_adjust`/`sales_adjust_rules`: hàng thực về kho dùng phiếu trả, mất trên đường không nhập kho giả, giảm nợ dùng hóa đơn giảm không cập nhật kho. GN09 chỉ kiểm và liên kết chứng từ đã được người có quyền ghi sổ, không thay bộ xử lý nghiệp vụ chuẩn.

## 3. Quy trình và trách nhiệm

1. Kế toán kho hoặc người có quyền đọc/sửa DN đã xuất chọn **Ghi nhận chênh lệch**, ghi lượng/bao, hiện tượng và việc cần xác minh. Không đòi tệp ký ngay khi báo.
2. Kế toán trưởng chọn **Giao người xử lý**, chỉ định User đang hoạt động, có quyền đọc/sửa đúng DN và hạn xử lý. Nhân viên kho ngoài phần mềm có thể cung cấp số thực tế, người nhập ghi rõ trong nội dung.
3. Người phụ trách xác minh qua quy trình vận hành. Kế toán trưởng kiểm bằng chứng, đối chiếu bản ký hiện tại, ghi kết quả và chọn căn cứ để **Chốt xử lý chênh lệch**. Không bắt mọi giao dịch bình thường phải duyệt; đây là kiểm soát ngoại lệ.
4. Nếu có bằng chứng mới, trưởng mở lại có lý do. Thay tệp/ghi chú bản ký tự mở lại hồ sơ đã chốt; kết quả cũ vẫn có trong Comment.

Workspace Trung tâm Bán hàng có lối **Chênh lệch giao nhận cần xử lý**, dùng danh sách DN chuẩn và quyền native. Lọc theo trạng thái, người phụ trách, hạn trên trường chuẩn của hồ sơ.

## 4. Quy tắc và ngoại lệ

- Trạng thái hồ sơ riêng: trống → Cần xử lý → Đang xử lý → Đã xử lý. Chỉ `assign` chuyển sang Đang xử lý; chỉ `resolve` từ Đang xử lý mới đóng. Dấu đối chiếu bản ký không đóng hồ sơ.
- Chốt phải có người phụ trách/hạn, bản ký riêng đúng DN đã đối chiếu và kết quả không rỗng. Bản ký không bắt buộc để xuất/nhận hàng hoặc báo vấn đề.
- **Đối chiếu, không điều chỉnh sổ:** trưởng chịu trách nhiệm kết luận, ghi đủ cách xác minh. Không tự sửa kho/nợ để làm khớp giấy.
- **Phiếu trả hàng:** DN trả đã submit, `is_return=1`, `return_against` đúng DN nguồn, đúng Company/Customer. Phải là hàng thực nhập lại theo quy trình hiện có; ghi nhận thiếu không mặc nhiên tạo trả hàng.
- **Hóa đơn giảm:** SI trả đã submit, không update_stock, có hóa đơn gốc cùng Company/Customer, truy được DN nguồn. Nếu hóa đơn gốc gộp nhiều DN thì dòng hóa đơn giảm phải chỉ rõ DN đang xử lý. Trường hợp chưa truy được nguồn phải giữ mở và đối soát, không chọn đại chứng từ.
- Không hỗ trợ đóng bằng JE/Stock Entry bất kỳ. Nếu cần quy trình khác, giữ hồ sơ mở và dùng đặc tả nghiệp vụ tương ứng; không lách bằng kết luận không điều chỉnh sổ.
- Chặn hủy chứng từ đang là căn cứ; trưởng mở lại và bỏ liên kết hiện hành trước khi hủy bằng nghiệp vụ native. Hủy source DN còn hồ sơ mở cũng bị chặn. Lịch sử không bị xóa khi bỏ liên kết.
- Thay tệp/ghi chú sau chốt xóa kết quả/căn cứ/dấu chốt hiện hành, giữ người phụ trách/hạn và mở Đang xử lý; đồng thời luồng hồ sơ ký xóa dấu đối chiếu. Phải xem lại bản ký trước khi chốt lần nữa.

## 5. Dữ liệu và chuyển trạng thái

Mười hai Custom Field trên DN: `kh_aph_chenh_lech_state` (Select), `_noi_dung` (Small Text), `_phu_trach` (Link User), `_han` (Date), `_ket_qua` (Small Text), `_cach_xu_ly` (Select), `_phieu_tra` (Link Delivery Note), `_hoa_don_giam` (Link Sales Invoice), `_bao_boi` (Link User), `_bao_luc` (Datetime), `_chot_boi` (Link User), `_chot_luc` (Datetime). Các hậu tố dùng cùng tiền tố `kh_aph_chenh_lech`.

Các trường readonly, allow_on_submit, no_copy; server chặn sửa tay qua API/save/import. Người/thời điểm báo và chốt do server ghi, không nhận từ client. Nội dung tối đa 2.000 ký tự; Link/Select tối đa 140, ngày ISO hợp lệ; chặn field thừa/kiểu sai/ký tự điều khiển. Endpoint POST `delivery_issue.cap_nhat(name, modified, action, values)` khóa DN và kiểm phiên sửa; cập nhật nguyên tử, không tự commit. Khi chốt khóa chứng từ căn cứ, kiểm lại trạng thái để không dùng chứng từ vừa hủy đồng thời.

## 6. Phân quyền và lịch sử

Báo vấn đề đòi native DN read/write. Giao người/chốt/mở lại thêm Accounts Manager (hoặc Administrator), vẫn giữ Company/Warehouse/Customer scope. Người chỉ có role trưởng nhưng ngoài scope không được xử lý. Người phụ trách phải có native read/write của DN tại lúc giao và chốt. Dialog không thay kiểm server.

API chỉ trả name/modified và 12 trường hồ sơ, không items/thuế/giá vốn hoặc toàn DN. Chuỗi JSON trước/sau được escape rồi lưu Comment cho từng thay đổi; bản ký và tệp vẫn qua cơ chế riêng tư/bảo vệ cũ. Tên, lý do và kết quả không được render thành HTML thực thi.

## 7. Tác động hệ thống

Báo/giao/chốt/mở lại không tạo GL/SLE/SI/PLE và không giảm công nợ lần nữa. Chứng từ căn cứ có tác động qua controller native khi người có quyền submit/cancel, độc lập thao tác hồ sơ. Không tự cấn cọc, không sửa MA, sản xuất hoặc MISA. Số lượng thực xuất/nhập vẫn thuộc DN và phiếu trả chuẩn.

## 8. Tiêu chí nghiệm thu

- Báo bằng tài khoản bán hàng; người thường không giao/chốt/mở lại; trưởng ngoài scope và người phụ trách ngoài scope bị chặn; phiên cũ/field giả bị từ chối, không đổi sổ.
- Đối chiếu bản ký không đổi Cần xử lý; giao người/hạn chuyển Đang xử lý. Chốt không điều chỉnh sổ lưu đúng actor/time, sổ giữ nguyên; bấm lặp không có lịch sử giả.
- Đổi ghi chú sau chốt tự mở lại, xóa dấu hiện hành, vẫn đọc được kết quả cũ; chốt lại trước đối chiếu mới bị chặn.
- DN trả nháp, source sai, Company/Customer sai, SI giảm ghi kho hoặc nguồn mơ hồ bị chặn. DN trả và SI giảm đúng nguồn đã submit được liên kết; chốt không ghi thêm sổ. Hủy căn cứ đang liên kết bị chặn; mở lại giữ lịch sử.
- Kiểm native Dialog và lối Workspace trên image thật. 4 ca HTTP và 1 ca Desk mới của b014; kỳ vọng b014 30 PASS gồm restore, tổng 221. Chỉ kết luận sau đọc run/artifact trên đúng SHA; không dùng kết quả 1A để nghiệm thu GN09.

## 9. Triển khai và khôi phục

Dùng cờ `kh_aph_trung_tam_ban` hiện có, mặc định tắt; hook return sớm khi tắt, UI ẩn trường/nút. Schema qua `trung_tam_ban.schema` trong bộ cài production/UAT rõ ràng, không after_migrate. Không đổi flag inventory, phiên bản hoặc manifest production trong lượt phát triển. Không backfill/đóng chênh lệch từ ghi chú lịch sử.

Kiểm Cổng 2/2b/UAT/3 trên mã mới; so schema site nâng từ 0.15.2 với site trắng, chạy lại installer và quay lui trên môi trường tách biệt. Trước phát hành/tag, áp runbook hiện hành và diễn tập bản sao dữ liệu production hiện tại. Rollback sau mở nhập liệu phải đối soát giao dịch mới; không tự restore snapshot cũ.
