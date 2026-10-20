# NM01c — nhận chuyến chuyển kho đến nhà máy (cùng đơn vị)

## 1. Mục tiêu và phạm vi

Kho nhà máy nhận hàng chuyển từ kho khác **cùng đơn vị** (vd Kho bán hàng Hà Nội - APH → Kho thành phẩm nhà máy - APH)
theo lượng thực nhận, nhận từng phần được, trên chứng từ native Stock Entry. Không dùng phiếu mua (PR) cho chuyến chuyển.
Tái dùng cờ `kh_aph_factory_receiving` (mặc định tắt), không thêm cờ. Chỉ hàng tồn Kg/hệ số 1, không lô/sê-ri.

Ngoài phạm vi, **chưa tự suy diễn** (cần chủ dự án chốt): chuyển **khác đơn vị** (APH ↔ VH/MK/TL) — code hiện có coi là mua
bán nội bộ (`kho_van_hanh.tao_yeu_cau_chuyen` chặn), chưa có quy tắc giá/hóa đơn nội bộ; cách **xử lý lượng thiếu** của chuyến
(hao hụt vận chuyển, ai chịu, tài khoản) — R023 chỉ chốt "đang vận chuyển không tự cộng lại tồn khả dụng".

## 2. Hiện trạng và phần thay đổi

Có sẵn: Material Request chuyển kho (`kho_van_hanh.tao_yeu_cau_chuyen`, R058/R059), Stock Entry chuyển qua kho đang vận
chuyển (`add_to_transit`), phiếu nhận native `make_stock_in_entry` cập nhật `transferred_qty`/`per_transferred`, kho
"Hàng đang vận chuyển - <đơn vị>" do cây kho dựng và đặt làm kho đang vận chuyển mặc định. Thiếu: cửa sổ nhận theo lượng thực
nhận, khóa chống hai phiên cùng nhận (kiểm vượt của ERPNext đọc tổng không khóa), dấu người nhận/ghi chú bất biến.

Thêm `kh_aph/factory_transfer.py` (incoming/preview/receive + hook), `public/js/factory_transfer.js` (nút trên phiếu chuyển
đi và trên báo cáo Tồn kho số lượng), 6 Custom Field `kh_aph_transfer_*` trên Stock Entry.

## 3. Quy trình và trách nhiệm

Kho nguồn lập và xác nhận phiếu chuyển đi qua kho đang vận chuyển như hiện nay. Khi xe tới, người nhập nhà máy mở
"Nhận chuyến về kho", nhập kg/bao thực nhận từng dòng, kho nhận, người ký, ghi chú. Một lần bấm tạo và xác nhận một phiếu
nhận native. Lượng chưa nhận nằm lại kho đang vận chuyển, hiện ở "còn trên đường" để đối soát.

## 4. Quy tắc và ngoại lệ

Còn trên đường = transfer_qty dòng chuyển − tổng transfer_qty các phiếu nhận đã xác nhận (đọc trực tiếp sau khóa). Không
nhận vượt; thừa xử lý bằng kiểm kê. Ngày nhận từ ngày chuyển đến hôm nay. Kho nhận cùng đơn vị, kho lá, không phải kho đang
vận chuyển. Bao/kg khớp quy cách nếu mã quản lý bao. Mã lượt (nonce) theo người + phiếu; gửi lại cùng nội dung mở đúng
phiếu cũ, khác nội dung bị chặn, phiếu đã hủy không tạo lại.

## 5. Dữ liệu và trạng thái

Stock Entry thêm `kh_aph_transfer_{request,payload,actor,at,receiver,note}` (readonly, no_copy; request unique/ẩn).
Trạng thái dùng native: phiếu chuyển `per_transferred`, dòng `transferred_qty`. Không DocType mới, không sổ riêng.

## 6. Quyền và kiểm soát

Guard nhà máy như NM01a (vai trò nhà máy/kho/kế toán, cờ bảo vệ giá vốn). Đọc phiếu chuyển, đơn vị, mã hàng, kho bằng quyền
native; tạo/xác nhận phiếu nhận bằng quyền native của người dùng (không ignore_permissions). API chỉ trả mã/kho/lượng, không
giá. Dấu chỉ do cửa sổ tạo (ContextVar), không sửa sau xác nhận, không xóa phiếu có mã lượt.

## 7. Tác động hệ thống

Phiếu nhận native chuyển lượng và giá trị từ kho đang vận chuyển sang kho nhận cùng đơn vị: không đổi chủ sở hữu (R060),
không công nợ/tiền. Hook `before_submit`/`before_cancel` trên mọi phiếu nhận có `outgoing_stock_entry` (kể cả màn chuẩn)
khóa Company → phiếu chuyển đi rồi kiểm lượng còn, khi cờ bật.

## 8. Tiêu chí kiểm

Unit `kh_aph/tests/test_factory_transfer.py` (10 ca). HTTP (`deploy/uat/http/b014_factory_transfer.py`, 6 ca):
HTTP_NM01C_SCOPE_PREVIEW (chỉ lượng, người ngoài quyền bị chặn); HTTP_NM01C_PARTIAL_REPLAY (nhận 4/10, gửi lại một phiếu,
đổi nội dung bị chặn, per_transferred 40); HTTP_NM01C_TAMPER (vượt lượng, kho đang vận chuyển, kho đơn vị khác, giá giả,
sửa dấu bị chặn); HTTP_NM01C_RACE (hai phiên cùng 4 khi còn 6 chỉ một thành công); HTTP_NM01C_NATIVE_CAP (màn chuẩn nhận vượt
bị chặn, nhận đủ phần còn → 100%); HTTP_NM01C_CANCEL_RESTORE (hủy phiếu nhận trả lượng về trên đường, không xóa hồ sơ).

## 9. Triển khai và khôi phục

Schema qua `factory_transfer.schema()` trong bộ cài rõ ràng (uat_candidate_setup.schema), không after_migrate. Tắt cờ: cửa sổ
và khóa thêm ngừng, phiếu đã có giữ nguyên; dấu vẫn bất biến. Quay lui theo image + DB như quy trình. Nghiệm thu người thật
gom cuối.
