# GN10/GN11 — Xuất ngay theo đợt và thử lại sau mất phản hồi

## 1. Mục tiêu và phạm vi

Thêm lựa chọn xuất ngay vào Dialog lập phiếu của đơn chung. Mặc định vẫn lập nháp và in, không ghi sổ. Người có quyền kho chỉ chọn xuất ngay sau khi đã kiểm thực giao. Dùng controller DN và `delivery_status.confirm`, không tạo sổ riêng hoặc quy trình duyệt mới. Không mở phạm vi quỹ/chốt ca/nhà máy/hóa đơn MISA một phần.

## 2. Hiện trạng và bằng chứng nguồn

Production vẫn 0.15.2. PR #5 đã có thông tin giao nhận, hai liên và GN09; mã GN09 đã kiểm `9c45e74` với 401 ca cục bộ/222 UAT. GN10 dùng `ban_nhanh._create`, `create_and_dispatch`, JS đơn chung và `b014_xuat_ngay_cases.py`. Mã/run nghiệm thu GN10 được ghi ở đầu tài liệu bàn giao, không lấy kết quả GN09 để xác nhận mã mới.

## 3. Người thực hiện và thao tác

Kế toán bán hàng chỉ có quyền lập nháp vẫn dùng nút cũ. Người có quyền submit DN thấy ô **Xuất ngay — đã kiểm thực giao tại kho**, mặc định bỏ chọn. Nhập cách giao, người nhận và người thực giao, chọn lượng rồi bấm **Xuất ngay & Mở bản in**. Tên người thực giao có thể là người ký giấy không có tài khoản; tài khoản xác nhận và thời điểm do server ghi riêng.

Cách giao Vận chuyển xác nhận Đang giao; Khách đến lấy xác nhận Khách đã nhận. Cả hai ghi kho/nợ đúng một lần qua nghiệp vụ chuẩn. In lỗi hoặc mất phản hồi: giữ nội dung và thử lại trong cùng Dialog với mã yêu cầu cũ, không đóng/mở để tạo mã mới khi chưa rõ kết quả.

## 4. Quy tắc và ngoại lệ

- Lập nháp và xuất ngay là hai ý định khác nhau trong hash; cùng token không được đổi chế độ hoặc đổi lượng/giao nhận/người giao. Token cũ của lối lập nháp vẫn tương thích.
- Một POST tạo toàn bộ DN rồi xác nhận toàn bộ. Không commit giữa nhóm; lỗi quyền/giá/khách/tồn ở bất kỳ nhóm nào hoàn tác DN/SI/GL/SLE của cả yêu cầu. Không bắt lỗi để giữ phần đã xuất.
- Kiểm lại quyền create/read/write/submit/print, Company/Customer/Item/Warehouse, Address và nguồn SO. UI chỉ gợi ý khả năng thao tác, không cấp quyền.
- Lượng/bao và phần còn lại qua planner/khóa đơn/SO hiện có; điều kiện xuất, duyệt giá/rủi ro/hạn mức/tồn vẫn qua controller native. Không mở quyền sửa giá hoặc cho tồn âm riêng.
- Retry thành công chỉ trả các DN đã submit có cùng hash, lượng thực trên DN, thông tin đợt/người giao và SO thuộc đúng đơn chung. DN hủy hoặc sai lượng/nguồn không được tự tạo thay hay tự xuất tiếp. Sau khách nhận vẫn dùng lại kết quả cũ, không ghi sổ lại.
- Bản in sau xác nhận giữ dấu bản sao, không làm căn cứ lấy hàng thêm lần nữa. Lỗi mở cửa sổ in không rollback giao dịch đã commit; dùng lại token để in.

## 5. Dữ liệu và trạng thái

Không thêm Custom Field/DocType/cờ. Dùng `kh_aph_don_chung_xuat`, `kh_aph_dot_xuat`, `kh_aph_dot_xuat_hash` và các trường giao nhận đã có. Nội dung hash của xuất ngay gồm rows, delivery, operation=dispatch, dispatcher. Endpoint `create_and_dispatch(shared_order, selections, request_id, delivery, dispatcher)` chỉ POST; `_create` là hàm nội bộ. `preview.can_dispatch` là boolean theo quyền submit chung; server kiểm lại trên từng DN thực tế.

Không thêm trạng thái giao hàng: Vận chuyển → Đang giao; tự lấy → Khách đã nhận. Mỗi đợt có các DN tách theo SO/kho/Company như cũ. Dấu xác nhận kho do server ghi và không thay lúc nhận hàng/lưu bản ký.

## 6. Phân quyền và kiểm soát

Không thêm vai trò hay DocPerm. Người thiếu submit hoặc bị chặn màn bán hàng không được gọi API xuất ngay. Native quyền/scope được kiểm cả lần đầu và retry sau khi thu hẹp quyền. API trả name/company/warehouse/docstatus và reused, không trả nguyên DN hoặc giá vốn. Hồ sơ, trạng thái và nhật ký native vẫn áp dụng; không ignore_permissions hoặc sửa core.

## 7. Tác động hệ thống

Nháp/in vẫn không ghi sổ. Chọn xuất ngay chủ động thực hiện xuất tồn và ghi công nợ qua DN/controller cùng transaction. Không thu tiền, cấn cọc tự động hoặc đổi nơi nhận tiền; MISA vẫn riêng. Nhận hàng sau handoff, mở bản in và retry không ghi nợ/kho lần nữa. Giá vốn và hoàn tác theo native, không tự tạo bút toán bù.

## 8. Nghiệm thu

- Thiếu submit, Dũng bị chặn, thiếu người giao/thông tin nhận: không thêm DN/SI/GL/SLE. Preview tài khoản không có submit trả can_dispatch=false.
- Hai cách giao cho đúng trạng thái, actor/time kho; retry sau commit/sau nhận và đổi ý định/token bị kiểm đúng; không tự nâng nháp cũ thành đã xuất.
- Đợt APH/VH: nhóm đầu có tồn, nhóm sau thiếu tồn thì cả đợt rollback; so counts và Bin. Bổ sung tồn giả đúng chuẩn rồi thử lại cùng token thành công hai Company. Người ngoài scope bị chặn cả retry.
- Hai phiên cùng token chỉ có một DN và một SI; retry không tăng sổ.
- Desk thật: chọn tự lấy và xuất ngay; dùng CDP Fetch chặn phản hồi HTTP200 sau server commit; kiểm DN đã submit rồi bấm lại nút trong đúng Dialog, so counts DN/SI/GL/SLE không tăng. Đây là mô phỏng mất phản hồi trình duyệt thật ở mốc commit, không chỉ gọi API lặp.
- Thêm 4 ca HTTP và 1 ca Desk; b014 kỳ vọng36 PASS gồm restore, toàn UAT227. Kiểm trên đúng SHA, đọc artifact/ảnh và giữ hồi quy cọc/GN09/giá vốn.

## 9. Triển khai và khôi phục

Tái dùng cờ Trung tâm Bán hàng và các cờ nguồn/giao hàng đã có; không thay inventory21 cờ hoặc bộ cài. JS qua doctype_js hiện có, không build frontend. Production/tag/version/manifest chưa đổi. Cần Cổng2/2b/UAT/3 đúng SHA; trước phát hành vẫn diễn tập bản sao production hiện tại theo runbook, không lấy CI thay nghiệm thu người thật/máy in. Quay lui bằng image và snapshot tương ứng trước mở nhập liệu; sau có giao dịch mới phải đối soát, không tự restore mất dữ liệu.
