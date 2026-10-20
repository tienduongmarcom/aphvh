# NM02–NM04 — ghi sản xuất / đóng gói thành phẩm / đổi bao một lần theo lượng

## 1. Mục tiêu và phạm vi

Một cửa sổ cho nhà máy ghi lượng một lần, tạo **một** Stock Entry native thuộc loại phiếu kg đã kiểm (0.11.1–0.11.2), không
sổ sản xuất riêng. Cờ mới `kh_aph_factory_production` (mặc định tắt; cần `kh_aph_factory_costing` và bảo vệ giá vốn).
Không dùng Work Order/BOM/GL cho người không xem giá vốn. Quyết toán dở dang về 0 vẫn là thao tác kế toán sẵn có
(`factory_costing.quyet_toan_do_dang`), không đưa vào cửa sổ này.

Chưa làm, cần chủ dự án chốt nếu muốn: chọn **lệnh sản xuất/mẻ** (dự án chưa dùng Work Order); tự đề xuất đầu vào theo
định mức (hiện chỉ cảnh báo R073 khi lưu).

## 2. Hiện trạng và phần thay đổi

Có sẵn: `Sản xuất theo kg` (Manufacture, kg-v4, bắt buộc xưởng), `Đóng gói theo kg` (Repack, nhiều đầu ra chia theo kg ×
hệ số), `Đóng gói thành phẩm` và `Đổi bao, đóng gói lại` (bảo toàn kg, lệch phải xác nhận + lý do, Q103), kho Dở dang dây
chuyền theo loại kho. Thiếu: nhập ngắn một lần, chống ghi lặp/đồng thời, dấu người ghi. Thêm `kh_aph/factory_production.py`,
`public/js/factory_production.js` (nút trên báo cáo Tồn kho số lượng), 5 Custom Field `kh_aph_production_*` trên Stock Entry.

## 3. Quy trình và trách nhiệm

Sản xuất: chọn dây chuyền (kho dở dang) → cửa sổ hiện lượng đang có ở dở dang → nhập **lượng thực dùng** từng mã và đầu ra
cân thực tế (kho Chờ đóng gói / Thành phẩm / Chờ xử lý), chọn xưởng. Phần chưa dùng ở lại dở dang. Đóng gói/đổi bao: nhập
đầu vào (hàng + bao bì) và đầu ra.

## 4. Quy tắc và ngoại lệ

Một đầu ra → `Sản xuất theo kg`; nhiều đầu ra (thành phẩm phẩm cấp khác, phụ phẩm) → `Đóng gói theo kg`. Đầu vào sản xuất
từ một kho dở dang, không vượt tồn hiện tại (khóa Bin, đọc hiện tại). Đầu vào > đầu ra: hao hụt tự nhiên theo quy tắc sẵn
có, bắt buộc lý do; bất thường phải xuất chi phí riêng (thông báo native). Không tự vét dở dang, không ép chênh lệch.
Đóng gói/đổi bao: lệch kg (không tính bao bì) bị lớp sẵn có chặn, chỉ qua khi xác nhận + lý do. Ngày không ở tương lai.
Mã lượt theo người + đơn vị; gửi lại cùng nội dung mở phiếu cũ, khác nội dung bị chặn.

## 5. Dữ liệu và trạng thái

Stock Entry thêm `kh_aph_production_{request,payload,actor,at,note}` readonly/no_copy, request unique ẩn. Trạng thái native.

## 6. Quyền và kiểm soát

Guard: cờ + vai trò nhà máy/kho/kế toán; quyền đọc Company/Warehouse/Item và tạo/xác nhận Stock Entry theo quyền native,
không ignore_permissions. Kho đúng đơn vị, kho lá, đúng loại kho. API trả mã/kho/lượng; giá thành do kg-v4 tính và bị che
với hồ sơ không xem giá vốn (lớp che sẵn có).

## 7. Tác động hệ thống

Ghi kho và giá trị như phiếu cùng loại nhập tay; không công nợ/tiền. Giá thành chia theo kg × hệ số như hiện có.

## 8. Tiêu chí kiểm

Unit `kh_aph/tests/test_factory_production.py` (9 ca). HTTP `deploy/uat/http/b014_factory_production.py` (5 ca):
HTTP_NM02_CONTEXT_WIP; HTTP_NM02_RECORD_REPLAY (dùng 60/100, ra 55, hao hụt 5 có lý do, dở dang còn 40, gửi lại một phiếu);
HTTP_NM02_TAMPER (vượt dở dang, thiếu xưởng/lý do, kho bán, giá giả, kho đơn vị khác, sửa dấu bị chặn);
HTTP_NM02_MULTI_OUTPUT (hai đầu ra → Đóng gói theo kg, dở dang 0); HTTP_NM04_PACK_BALANCE (bảo toàn; lệch cần xác nhận + lý do).

## 9. Triển khai và khôi phục

Cờ 27 đồng bộ FLAGS/quay-lui/dấu vân/preflight/Cổng 3. Schema qua `factory_production.schema()` trong bộ cài rõ ràng.
Tắt cờ: cửa sổ ngừng, phiếu đã ghi giữ nguyên. Nghiệm thu người thật gom cuối.
