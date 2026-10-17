# Bán hàng nhanh — trạng thái để agent khác tiếp quản

Ứng viên 0.15.0, chưa phát hành/triển khai. Nguồn yêu cầu anh Tiến 16/10: tự tạo dữ liệu giả, làm lần lượt nghiệp vụ, chú ý UI, kèm bản dịch. Cờ `kh_aph_trung_tam_ban` hiện có; không sửa core.

## Luồng đã viết

1. Lập và xác nhận đơn chung bằng form chuẩn (giá sàn/hạn mức/thuế giữ nguyên).
2. Bấm **Lập phiếu xuất & In**. Dialog hiển thị lượng còn lập phiếu, kho, quy cách; mở dòng xem lượng đặt/đã giao/nháp. Điền lượng kg đợt này hoặc “Điền toàn bộ phần còn lại”. Bao phải nguyên theo snapshot.
3. Server kiểm quyền đơn chung, Customer, SO con, Company, Warehouse, Item và quyền tạo DN. Khóa đơn chung rồi nguồn SO; kiểm lại lượng, gồm mọi DN nháp chưa hủy từ cùng dòng nguồn. Tạo một DN nháp cho từng SO × kho trong cùng transaction. Không ghi GL/SLE/SI.
4. Mã yêu cầu giữ trong Dialog khi mạng lỗi. Cùng mã/cùng nội dung trả đúng phiếu cũ; cùng mã/nội dung khác bị từ chối. Không nuốt lỗi/commit giữa các kho. Mở lại Dialog sẽ đọc lượng đã lập, tránh hiểu nhầm là chưa có phiếu.
5. In một trang mỗi DN: chỉ lượng, kho, bao/kg, mã DN/đơn chung, chữ ký thực giao/thực nhận; nháp ghi **CHỜ XUẤT — CHƯA GHI SỔ KHO/CÔNG NỢ**. Không thay Print Settings toàn hệ thống để cho phép in nháp. In không tự submit; kho tiếp tục dùng luồng xác nhận đã có.

Không coi lượng trên phiếu nháp là giữ tồn vật lý. API chuẩn khác vẫn có thể lập nháp; khi xác nhận xuất tiếp tục qua kiểm native và khóa nguồn hiện có. Đã có ca hai request cùng mã và kiểm chỉ một phiếu; chưa đo tải lớn/phối hợp nhiều cửa sổ. Chưa tạo nhóm điều phối giao có trạng thái riêng.

## Vị trí code

- `kh_aph/ban_nhanh.py`: facade, schema 3 liên kết DN, kiểm quyền, tạo nháp/in.
- `kh_aph/dispatch_plan.py`: quy tắc thuần lượng còn lại/bao nguyên/không nhận NaN/Inf/dòng trùng hoặc ngoài nguồn.
- JS form đơn chung: Dialog chuẩn Frappe, không Page/SPA, không thêm bước build. Sinh token bằng `crypto.getRandomValues` chạy được cả HTTP; không dùng `randomUUID` bắt buộc secure context.
- Schema gọi qua `trung_tam_ban.schema` trong bộ cài rõ ràng. Kế toán bán hàng thêm DN create/write để lập nháp, không thêm submit/cancel/delete; không reset quyền đang có.
- Mẫu in `templates/ban_nhanh/phieu_dot_xuat.html`: facade truyền allowlist, escape tên người/hàng/kho; không truyền nguyên chứng từ có giá.

## Kiểm độc lập

```
(cd apps/lab9x && python3 -m unittest discover -s lab9x/tests -t .)
PYTHONPATH=apps/lab9x python3 -m unittest discover -s kh_aph/tests -t .
node --check kh_aph/kh_aph/doctype/aph_shared_sales_order/aph_shared_sales_order.js
```

Image có Jinja2; máy cục bộ cần Jinja2 để chạy đủ các ca mẫu in. Không đánh đồng unit với UAT.

UAT Actions chạy b014: kế toán bán hàng tạo/xác nhận đơn, lập 5/20 kg, kiểm nháp không đổi GL/SLE/SI; lặp cùng request không thêm phiếu, đổi nội dung token cũ bị chặn, lập vượt 15kg còn lại bị chặn. Dũng có role cộng thêm bị từ chối. In số lượng không ghi sổ. Chrome mở form thật, bấm nút, kiểm Dialog lượng nháp/còn lại, lưu ảnh `ban-nhanh-dialog.png`. Khôi phục cùng baseline do runner b014 đảm nhiệm. Mong 14 PASS cả b014 cũ và restore; chưa kết luận đạt cho tới run đúng SHA xanh.

Đã bổ sung ngày 17/10 (chờ CI SHA mới): `b014_ban_nhanh_scope.py` kiểm 3 kho/2 pháp nhân qua facade, sửa nháp bằng endpoint chuẩn cập nhật lượng còn lại, tài khoản chỉ Company APH và tài khoản chỉ kho chính (có đối chứng dương cùng endpoint), chặn preview/tạo mới/thử lại mã cũ/in ngoài phạm vi; Item VH bị ngừng sau xác nhận SO gây lỗi native ở nhóm sau, không để lại DN/GL/SLE/SI. b014 nay mong 19 PASS cả restore. `_note_scope` kiểm lại Company/Warehouse/Item khi thử lại và in, không chỉ dựa quyền DN. Phiếu hủy không được trả như đợt còn dùng được.

Mất kết nối sau commit được mô phỏng bằng gọi lại cùng mã và kiểm phiếu giữ nguyên; chưa cắt mạng thật. Sửa nháp sau khi in vẫn theo quyền native và lịch sử chứng từ; hồ sơ bản ký chưa thuộc luồng này. Chưa quan sát hình UI thật; ảnh CI cần được xem lại.

## Bản dịch

Đã sửa 7 chuỗi sai nghĩa rõ: Base Total Billed Amount, Tax Withholding, chênh lệch làm tròn hóa đơn đầu kỳ, diễn giải quyền, Chart of Accounts, lấy bút toán, số kỳ khấu hao. Giữ placeholder/HTML và mọi dòng không đổi. Audit 15/10 có 326 đề xuất, không phải 326 lỗi đã xác nhận. 182 diễn đạt và 137 phụ thuộc ngữ cảnh chưa được áp toàn bộ.

## Kiểm riêng bản vá nền

`deploy/uat/native_16511.py` chạy trước HTTP trên site CI trắng: ngày tương lai/thiếu Company/phiếu chốt nháp bị chặn, số dư đầu kỳ lọc đúng mã–kho và khớp cách bỏ chốt, phiếu chốt sau chặn hủy/tái tạo phiếu trước, phiếu hủy không sinh lại số dư; rollback số đếm và series. Bốn ca kỳ vọng, chưa PASS trước run đúng SHA. Image nền đã đo trong CI: ERPNext 16.51.1 + Frappe 16.52.0. UAT nền cũ đạt nhưng Cổng 3 bắt lỗi ô default_warehouse không còn trong Stock Settings; helper mới kiểm meta, nền cũ vẫn đọc cấu hình bình thường. Số dư chốt chứa giá/FIFO nên thêm hook quyền cho cả Stock Closing Entry/Balance; ca HTTP Dũng được cộng Stock User vẫn bị chặn đọc/query, kế toán trưởng vẫn đọc được. Lớp che JSON cũng bỏ fifo_queue/stock_queue.

## Phần tiếp theo

Hồ sơ ký nhận (tải bản ký, người đối chiếu/thời gian, thiếu hồ sơ/chênh lệch); ca giữ tiền/bàn giao/đối soát chuyển khoản/cọc/thu hộ; nhà máy; tổng hợp tài chính. Bản in có ô ký chưa phải bằng chứng hồ sơ đã ký. Giữ dữ liệu nguồn ERPNext, không xây sổ tiền/kho/công nợ thứ hai.
