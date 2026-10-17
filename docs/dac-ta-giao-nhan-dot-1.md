# Đợt 1A — Thông tin giao nhận theo đợt và bản in nhanh

## 1. Mục tiêu và phạm vi

Tiếp nối GN01/GN03/GN04 và một phần GN06 trong `ke-hoach-van-hanh-tiep-noi.md`. Người bán điền cách giao, người nhận tại kho, số liên hệ, lái xe, biển số và địa chỉ ngay khi lập phiếu đợt. Kho ghi người trực tiếp giao trước xác nhận. Không thay đổi tài chính, trạng thái giao hàng hoặc quy trình điều chỉnh số lượng đang có. Vòng xử lý chênh lệch GN09, xuất ngay trong Dialog GN10 và các đợt tiền/nhà máy chưa thuộc lát thay đổi này.

## 2. Hiện trạng và nguồn

Production0.15.2; thay đổi chưa phát hành. Đã kiểm meta chính thức Delivery Note của ERPNext16.51.1: dùng lại `shipping_address_name`, `shipping_address`, `driver_name`, `vehicle_no`. Không tạo bảng địa chỉ/lái xe hoặc sổ giao hàng riêng. API cũ cho phép retry với hash cũ khi không truyền thông tin mới.

## 3. Quy trình và trách nhiệm

Kế toán bán hàng mở đơn chung → Lập phiếu xuất & In → chọn lượng và nhập thông tin giao → tạo các DN nháp theo SO/kho → in2 liên. Kho kiểm lượng, cập nhật nháp trong quyền, ghi tên người giao thực tế trên DN → lưu → xác nhận đúng Vận chuyển hoặc Khách đến lấy. Người nhận/lái xe và người xuất trực tiếp không bắt buộc có tài khoản. Actor/time trên hệ thống tiếp tục do `delivery_status` ghi, không lấy từ tên tự nhập.

## 4. Quy tắc và ngoại lệ

- Thông tin nhập mới có cách giao và người nhận bắt buộc. Điện thoại/lái xe/biển số/địa chỉ có thể trống nếu chưa có; không ép điền giả.
- Địa chỉ phải có quyền đọc, đang sử dụng và liên kết Customer của đơn. Bộ lọcLink chỉ là gợi ý, server kiểm lại.
- Tên/số liên hệ chỉ nhận chuỗi, có giới hạn độ dài; chặn ký tự điều khiển và field ngoài allowlist.
- Cùng request_id nhưng khác lượng hoặc thông tin giao nhận bị từ chối. Dữ liệu chuẩn hóa trước tính hash. Khi không truyền thông tin mới, giữ nguyên cách tính hash0.15.2 cho tương thích retry.
- Kho phải ghi người thực giao trước xuất phiếu có cách giao mới. Người chỉ có quyền lập/sửa nháp không được giả tên người thực giao; server đòi quyền submit khi thay tên đó.
- Phiếu ghi Vận chuyển không được xác nhận bằng Khách đến lấy và ngược lại. Luồng native submit vẫn qua kiểm này.
- Phiếu đã xuất không sửa đè thông tin bằng save. Luồng đổi địa chỉ khi đang giao0.11.3 vẫn dùng endpoint có lý do/lịch sử riêng; không sửa core hoặc bypass endpoint này.
- Không bổ sung yêu cầu bắt buộc cho phiếu cũ chưa có cách giao, không chuyển trạng thái hay tự điền dữ liệu lịch sử.

## 5. Dữ liệu và trạng thái

Custom Field trên Delivery Note: `kh_aph_cach_giao` (Select), `kh_aph_nguoi_nhan_tai_kho` (Data), `kh_aph_dien_thoai_nhan` (Data), `kh_aph_nguoi_thuc_giao` (Data), `kh_aph_ban_giao_luc` (Datetime), `kh_aph_ban_giao_boi` (Link User). Hai dấu bàn giao do server ghi lúc xuất, không thay khi khách nhận hàng; không sửa tay. `no_copy=1`, không cho cập nhật tùy ý sau submit. Giữ ba trạng thái Chờ xuất → Đang giao → Khách đã nhận. Cách giao là thông tin của đợt, không phải trạng thái thứ tư. Dấu đối chiếu bản ký vẫn là hồ sơ độc lập.

Địa chỉ hiển thị lấy bằng renderer chuẩn Frappe từ Address đã kiểm quyền, không nhận HTML địa chỉ từ client. Khi cập nhật hồ sơ trên phiếu đã xuất, không tái tạo địa chỉ theo danh mục mới (giữ snapshot của phiếu).

## 6. Phân quyền và lịch sử

Giữ quyền đơn chung, Customer, SO, Company/Warehouse/Item, DN create/read/print/submit đã có. Kiểm Address khi tạo và khi dùng phiếu qua facade. Chỉ nhận allowlist trả về, bản in không có giá. Guard bật sau cờ `kh_aph_trung_tam_ban`; tắt cờ không sửa chứng từ. Form chuẩn giữ Version/audit của native; endpoint nhận hàng/bản ký vẫn ghi actor/time và comment như trước.

## 7. Tác động hệ thống

Tạo nháp và in không ghi GL/SLE/PLE/SI. Xác nhận kho đi qua `delivery_status.confirm` và controller native, chỉ ghi một lần như trước. Không phân bổ cọc, không sửa nợ, giá vốn, MISA hoặc quỹ. Tên người giao là người làm thực tế, không tự cấp quyền phần mềm.

## 8. Kiểm thử

Unit: chuẩn hóa/kiểu dữ liệu/field thừa, địa chỉ theo khách/quyền, người giao cần submit, chặn sửa đè và không render lại địa chỉ đã xuất; kiểm escape và hai liên/dấu bản sao. HTTP b014 thêm `HTTP_014_GIAO_NHAN_METADATA`: tạo đúng địa chỉ, chặn sai khách và User Permission, mã lặp khác nội dung, người thiếu quyền submit giả tên người giao, thiếu người giao, xác nhận sai cách giao; số phiếu/sổ không đổi khi bị chặn. Chuỗi VAT/cọc/giao/bản ký/thu nốt cũ tiếp tục chạy trên phiếu có thông tin mới. b014 mong25 PASS gồm restore, toàn artifact dự kiến216 PASS. Chỉ xác nhận khi run đúngSHA đạt, chưa ký nghiệm thu máy in thật.

## 9. Cài đặt và khôi phục

Schema thêm sáu ô qua `trung_tam_ban.schema`, dùng cờ hiện có, không after_migrate. JS qua hook, không build frontend. Template in nhanh render trực tiếp theo image; bộ sinh JSON Print Format chuẩn được chạy kiểm và không có diff vì không sửa mẫu chuẩn. Cổng3 baseline cập nhật đúng digest production0.15.2 đã có log xác nhận. Chưa tăng version/tag/image, chưa đổi VM. Trước phát hành cần đủ cổng; trên VM phải diễn tập bản sao dữ liệu hiện tại và giữ bảo trì khi nâng, quay lui theo snapshot tương ứng; không restore tùy ý sau khi đã mở nhập liệu.
