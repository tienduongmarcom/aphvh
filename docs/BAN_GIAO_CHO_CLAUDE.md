# Bàn giao Codex → Claude — 20/10/2026

Chủ dự án giao Claude tiếp tục phát triển và rà lỗi độc lập; sau khi hoàn thành, Claude bàn giao lại cho Codex kiểm tra. Đây là hồ sơ tiếp nối, không phải xác nhận toàn dự án đã hoàn tất.

## Điểm bắt đầu

- Repo: https://github.com/tienduongmarcom/aphvh
- Checkout hiện tại: `/Users/macbook/Documents/Codex/2026-10-17/ghcr-io-tienduongmarcom-kh-aph-erpnext/work/aphvh`.
- Nhánh: `feat/nhan-cho-gia-theo-don-mua-20261020`; PR #18 đang draft/open, base là nhánh PR #17. Chuỗi phát triển chưa phát hành; kiểm trạng thái GitHub thực tế trước sửa, không suy main/production đã có các PR này.
- HEAD hồ sơ trước bàn giao này: `e929498`; mã nghiệp vụ/kiểm cuối: **a75ced9b8b4613d71fe45117bc36b7215f85877d**. Các commit sau mã kiểm chỉ đổi tài liệu/AGENTS.
- Production theo xác nhận người vận hành vẫn **0.15.3**, digest `sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`,21 cờ. Không coi code trên nhánh là đã bật production.

Đọc theo thứ tự: `AGENTS.md` → đầu `docs/ban-giao.md` và `deploy/release/TRANG_THAI.md` → `docs/quyet-dinh-nghiep-vu.md` → `docs/ke-hoach-van-hanh-tiep-noi.md` → `docs/dot-3-ra-soat-nguon-nha-may.md`. Khi phát hành, đọc thêm RELEASE_GATES/TRIEN_KHAI_FRONTEND/quy trình triển khai khách. Quyết định đã chốt không hỏi lại.

## Đã làm và bằng chứng

Đợt1 bán/giao nhận và đợt2 tiền đã được phát triển/kiểm theo hồ sơ từng PR; nghiệm thu người thật/số dư thật còn chờ. PR #17 bổ sung nhận nhanh từ PO có giá. PR #18 nối nhận chờ giá vào cùng cửa sổ, giữ PO/dòng nguồn, nonce/payload, người nhận, tệp private và lượng có vấn đề; giữ chỗ áp cả PR chuẩn/PI update_stock khi tắt26. Chốt một PR native đúng giá PO; hủy PR trả giữ chỗ, hủy pending sau đó giải phóng nhưng giữ lịch sử.

Bằng chứng PR #18 đúng a75ced9:

| Cổng | Run đã success |
|---|---|
| Site trắng | https://github.com/tienduongmarcom/aphvh/actions/runs/39350330165 |
| Diễn tập triển khai | https://github.com/tienduongmarcom/aphvh/actions/runs/39350329373 |
| UAT HTTP/Desk | https://github.com/tienduongmarcom/aphvh/actions/runs/39350325419 |
| Nâng từ production/quay lui | https://github.com/tienduongmarcom/aphvh/actions/runs/39350333813 |

419 kh_aph +108 lab9x unit đạt; **293 HTTP/Desk PASS,0 FAIL**, b014102,8 ca mới. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Artifact đã tải/đọc và xem ảnh tại thư mục ngoài Git `work/ci-pending-a75ced9/`: uat/, cong3/, cong2b.log, uat-run.log, cong3-run.log. Có thể tải lại từ Actions nếu đổi máy. Cổng3 schema1.085/1.085; quay lui1.052/1.052; năm cờ mới về0,21 cờ cũ giữ1; ca cố ý lỗi giữ maintenance_mode=1. CI nền GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Đặc tả và truy nguyên ca: `docs/dac-ta-nhan-hang-nha-may-3a.md`, `docs/dac-ta-nhan-cho-gia-theo-don-mua-3b.md`; hướng dẫn: `docs/huong-dan-nhan-hang-nha-may.md`. Lát3B chỉ PO VND/tỷ giá1, hàng tồn Kg/hệ số1; không lô/sê-ri/gia công/giao thẳng. Pending cũ không backfill PO. Chưa thể gọi toàn NM01 hoặc đợt3 hoàn tất.

## Claude rà độc lập trước khi phát triển tiếp

Đọc diff/code và bằng chứng, không lấy tuyên bố PASS làm bằng chứng không còn lỗi. Ưu tiên các điểm sau; đây là vùng cần rà, không phải lỗi đã được xác nhận:

- Khóa/current-read và chống vượt lượng giữa pending, PR, PI cập nhật kho; nhiều dòng/cùng dòng nguồn, hai phiên, sửa lượng/UOM/mã hàng trên PO, đóng/mở/hủy nguồn.
- ContextVar/capability loại trừ giữ chỗ chỉ đúng phiếu đang chốt; nonce không đổi mode/nội dung, không tái tạo sau hủy; mọi lỗi rollback toàn chuỗi, không commit giữa chừng.
- Bảo vệ metadata/nguồn/lượng qua native API, update-after-submit, copy/amend/delete và khi tắt cờ. Không nới native guard hoặc ignore_permissions để làm ca kiểm qua.
- Hủy PR chỉ miễn đúng backlink pending gốc; liên kết tĩnh/động khác vẫn chặn, trạng thái pending và báo cáo lượng khớp sau hủy.
- Quyền theo Company/Item/Warehouse/Supplier/PO, NoCost kể cả thêm vai trò quản lý; phản hồi insert/submit, report, print, File và Version. Tệp private/ownership/đúng parent, giữ lịch sử.
- Finalize đúng PO/dòng/giá/thuế/UOM, không mất sổ bao/giá tạm; pending cũ không PO vẫn hoạt động. Quyền sửa PO khác quyền Accounts Manager chốt giá.

Code trọng tâm: `kh_aph/factory_receiving.py`, `kh_aph/pending_order.py`, `kh_aph/pending_valuation.py`, controller APH Pending Receipt, `hooks.py`, `public/js/factory_receiving.js`, report Ton kho so luong. Test tương ứng trong kh_aph/tests và deploy/uat/http/b014_{factory_receiving,pending_order}.py, ban-nhanh-desk.mjs.

Giữ bằng chứng FAIL đã có: UAT39346121476/38318ab (fixture thiếu item_code, native bỏ qua/trả rỗng); UAT39348470916/02d9 (native tự điền giá mua gần nhất, fixture không thật sự rate0). Cách sửa/đường dẫn log đã ghi ban-giao/AGENTS. Không bỏ assertion hoặc giảm số ca để giấu lỗi. Phát hiện lỗi mới phải ghi trigger, đầu vào, actor, ảnh hưởng, cách tái hiện và regression thích hợp.

## Phần làm tiếp theo kế hoạch

1. **Nhận chuyển đến NM01c:** đặc tả9 nhóm trước triển khai; tái dùng Material Request/Stock Entry. Phân biệt cùng Company với giao dịch khác Company; giữ nguồn, đang chuyển, nhận từng phần, lượng còn và hồ sơ. Không dùng PR mua cho mọi chuyến chuyển. Kiểm nhận lặp/đồng thời, thiếu/thừa, hủy và NoCost.
2. **Sản xuất/dở dang NM02–03:** gom nhập lượng một lần trên backend đã có (stock_entry_kg/factory_costing). Chọn lệnh/định mức/dây chuyền, nguyên liệu thực dùng, thành phẩm/phụ phẩm, phần còn dở và chênh lệch. Không ép mọi chênh lệch thành hao hụt, không vét về0 hằng ngày, không tạo sổ sản xuất nhập lại. Không mở generic BOM/Work Order/GL cho NoCost; thiết kế API lượng với kiểm quyền rõ ràng.
3. **Đóng gói/đổi bao/xuất NM04–05:** giữ các công đoạn hiện có, cân đối kg và bao bì, phân biệt xuất bán/chuyển cùng Company/khác Company, nối hồ sơ ký đúng chứng từ.
4. **Workspace/bảng ngày nhà máy NM06–07:** việc đang chờ, lượng/dở dang/hồ sơ thiếu và tiền cá nhân; dùng quỹ/chốt ca đã có. Không mở report tài chính quản lý cho NoCost. Dialog/Workspace trước; Native Page chỉ khi đạt tiêu chí kiến trúc trong dự án.
5. **Đợt4 tài chính:** đối chiếu toàn chuỗi, mua–nhận–hóa đơn–trả tiền, chi phí đến muộn/repost, dở dang/giá thành, chốt tháng và báo cáo. Rà nguồn đã có trước; không viết lại nghiệp vụ nền hoặc cộng ngang lợi nhuận nội bộ.
6. **Đợt5 hóa đơn một phần:** cần chốt nghiệp vụ/đặc tả riêng trước code. Không tự suy các quy tắc thuế/MISA hoặc mở rộng phạm vi từ các phần đã duyệt. Ghi rõ điểm cần chủ dự án quyết định nếu còn thiếu.

Mỗi phần phải phân biệt đã có backend/đã nối UI/đã kiểm kỹ thuật/đã nghiệm thu thật/đã phát hành. Không tự gán phần trăm hoàn thành hoặc gọi toàn dự án xong khi còn các lớp này.

## Các quyết định phải giữ

- Chủ dự án cho gom nghiệm thu người đại diện, hàng hóa/tồn kho/số dư và máy in thật vào cuối. Vẫn kiểm kỹ thuật trên dữ liệu giả đại diện trước; không tuyên bố nghiệm thu thật khi chưa làm.
- Hàng có vấn đề thường giữ lại dùng ngay, đàm phán giảm giá sau. Ghi đủ lượng thực giữ, phần có vấn đề nằm trong tổng; không tự tạo trả hàng/giảm giá. Hàng thực sự chưa có giá vẫn ngoài tồn khả dụng; giá tạm phải đi đúng luồng đã duyệt, không giá0.
- Dũng/kế toán nhà máy không xem giá vốn/giá thành qua UI/API/report/print; nhân viên vận hành có thể chỉ cân/đếm/ký giấy, không cần tài khoản.
- Không sửa core, không sổ kho/tiền/công nợ trùng, không phân bổ tiền FIFO/ngầm, không bàn giao tiền làm giảm nợ lần nữa; giữ native chứng từ/quyền và lịch sử.
- Cờ mới mặc định tắt, cài schema rõ ràng, đồng bộ preflight/dấu vân/quay lui/Cổng3; không tự bật qua after_migrate. Tôn trọng quyền phát hành/tag và quy trình production trong AGENTS.

## Kiểm thử và bàn giao ngược cho Codex

Unit theo AGENTS (Python3.11+); 4 cổng trên Actions đúng mã cuối. Môi trường máy này đã dùng Python tại `/Users/macbook/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`; nếu Python mặc định3.9 thì dùng runtime phù hợp. Dữ liệu CI chỉ site dùng một lần `aphvh-web-uat`, không thao tác dữ liệu thật để chạy ca giả.

Sau mỗi phần, cập nhật **cả docs/ban-giao.md và deploy/release/TRANG_THAI.md**, commit phần đã làm. Dừng dở phải ghi ĐANG DỞ và bước tiếp. Phân biệt mã nghiệp vụ/kiểm với commit tài liệu sau đó. Đọc artifact và xem ảnh thực, không chỉ nhìn màu xanh. Không lặp kiểm rộng nếu chỉ sửa tài liệu hoặc không có thay đổi/lỗi cần xác minh.

Khi Claude bàn giao lại, cần có:

- Nhánh/PR/base/HEAD và mã nghiệp vụ cuối đã kiểm; trạng thái merge/tag/deploy thực tế.
- Bảng yêu cầu → code → test → bằng chứng → phần còn mở, kể cả giới hạn chưa bao phủ.
- Danh sách lỗi phát hiện, mức ảnh hưởng, tái hiện, bản sửa và regression; giữ các run FAIL.
- Run4 cổng đúng mã, tổng PASS/FAIL thật, artifact/ảnh, migration/rollback và giới hạn dữ liệu thử.
- Thay đổi schema/cờ/quyền, ảnh hưởng kho–nợ–tiền–giá vốn, cách nâng/quay lui và việc chủ dự án còn phải chốt.
- Những gì Codex cần kiểm độc lập lần sau. Không đánh dấu UAT người thật hoàn tất nếu vẫn để cuối.
