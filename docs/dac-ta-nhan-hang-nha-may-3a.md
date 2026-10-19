# Đợt3A — nhận nhanh nhà máy theo đơn mua

## 1. Mục tiêu và phạm vi

Bắt đầu NM01: nhập lượng một lần theo đơn mua đã xác nhận, không nhập hoặc xem giá vốn; tạo và xác nhận một Purchase Receipt chuẩn. Dùng Dialog trên PO và lối vào từ báo cáo Tồn kho số lượng, không Page/SPA/sổ kho hay DocType nhiệm vụ mới.

Lát này chỉ nhận hàng tồn Kg/hệ số1, có giá dương hợp lệ, không lô/sê-ri/gia công/giao thẳng/đơn giá đơn vị. Các loại còn lại dùng chứng từ chuẩn. Gom nhập chờ định giá, nhận chuyến chuyển đến, sản xuất/dở dang/đóng gói/xuất và bảng ngày nhà máy còn tiếp. Không gọi NM01 hoặc đợt3 hoàn tất.

## 2. Hiện trạng và bằng chứng

Base PR #16/565910a; mã nghiệp vụ trước d0c1f16 đủ4 cổng,280 HTTP/Desk,394+108 unit. Production theo xác nhận người vận hành vẫn0.15.3/21 cờ; nền ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11.

Đã có pending_valuation.finalize/APH Pending Receipt (ngoài tồn khả dụng đến chốt giá), factory_costing.validate_gia_tam (nhóm được phép), price_visibility.validate_purchase_receipt (nhân sự ẩn giá lấy từ PO), bag_stock (bao/kg/sổ bao). Native Purchase Order.make_purchase_receipt được đối chiếu tag16.51.1 và mapper tag16.52.0: kiểm quyền create/read và map dòng PO/thuế; không sửa core.

Khoảng thiếu được bổ sung tại factory_receiving.py, public/js/factory_receiving.js: chọn đơn có quyền, xem lượng, nhận nguyên tử, chống trùng và lưu hồ sơ thực nhận.

## 3. Quy trình và trách nhiệm

Người vận hành cân/đếm và ký giấy; kế toán nhà máy nhập. Từ Tồn kho số lượng chọn Company → Nhận hàng nhà máy → chọn PO; hoặc mở đúng PO → Nhận hàng nhà máy. Nhập tổng kg/bao thực nhận, trong đó kg có vấn đề, người thực nhận/ký, ngày, tệp cân và ghi chú. Xác nhận ghi nhập kho thực theo quyền native, không là in nháp. Mất phản hồi thì gửi lại cùng cửa sổ mở phiếu cũ.

Chủ dự án chốt19/10/2026: hàng có vấn đề thường giữ lại, vẫn dùng ngay và đàm phán giảm giá sau. Vì vậy nhập đủ lượng thực giữ/dùng theo giá PO; kg có vấn đề nằm TRONG tổng kg, không trừ tồn/ghi rejected_qty/tự tạo trả hàng. Có vấn đề phải ghi nội dung chất lượng/đàm phán. Dấu “Có hàng đàm phán giảm giá lúc nhận” lưu tình trạng lịch sử lúc nhận, không phải trạng thái hiện tại đã/chưa xử lý. Kế toán mua xử lý giá theo chuỗi hóa đơn mua/đối chiếu/repost hiện có; bản này không tự giảm giá hoặc chốt giá cuối cùng.

## 4. Quy tắc và ngoại lệ

Kg dương/tối đa6 số lẻ; bao nguyên không âm, khớp kg×quy cách. Kg có vấn đề không âm/không vượt tổng kg; không sửa kg/bao cho khớp sai lệch. Không nhận vượt phần còn lại qua facade. Đơn đóng/tạm dừng hoặc hàng cần lô/sê-ri/gia công/giao thẳng dùng quy trình chuẩn. Giá0 bị chặn, hướng chờ định giá. Giá tạm giữ dấu của PO và kiểm nhóm sẵn có; không lấy giá từ client/chọn thuế suất tự động.

Mã lượt theo actor+PO+nonce; payload gồm dòng/kho/lượng/ngày/người/tệp/ghi chú. Khóa Company→PO rồi đọc lại PO và children bằng get_doc(for_update=True); lookup mã lượt cũng SELECT FOR UPDATE, File đọc for_update sau khóa. Không dùng consistent read cũ để tính phần còn lại sau chờ phiên khác. Retry đúng nội dung trả PR cũ, không thêm sổ; đổi nội dung hoặc PR đã hủy bị chặn. PO đóng sau đó vẫn cho đọc kết quả cũ khi còn quyền. Đóng/tải lại cửa sổ tạo nonce mới: phải kiểm phiếu đã nhận trước khi nhận tiếp.

Phiếu cân phải là File riêng tư do caller tải, chưa gắn hồ sơ khác, có read/write; URL /private/files/. Khóa File rồi gắn vào PR cùng transaction, lỗi rollback toàn chuỗi. Hủy theo native và kiểm hàng đã dùng; PR có dấu không xóa kể cả hủy. Dấu/quan sát không sửa tay sau lưu; sửa nghiệp vụ đi chuỗi sửa/hủy có lịch sử.

## 5. Dữ liệu và trạng thái

PR thêm các trường readonly/no_copy:

| Field | Nguồn/quy tắc |
|---|---|
| kh_aph_receiving_request | SHA actor+PO+nonce, unique/hidden; phiếu native không có dấu dùng NULL |
| kh_aph_receiving_payload | SHA nội dung chuẩn hóa, hidden, không chứa giá |
| kh_aph_receiving_actor / at | Session và thời điểm server |
| kh_aph_receiving_receiver | Tên người thực nhận/ký; không suy owner |
| kh_aph_receiving_ticket | URL tệp cân riêng tư; sidebar File gắn đúng PR |
| kh_aph_receiving_note | Ghi chú thực nhận/chất lượng/đàm phán |
| kh_aph_receiving_price_review | Snapshot có hàng cần đàm phán lúc nhận |

PR Item thêm Float readonly/no_copy kh_aph_receiving_quality_qty là phần trong qty. qty/received_qty/stock_qty/PO links/kh_aph_bags dùng trường hiện có; rejected_qty=0 trong lát này. PR0→1 nguyên tử, sau đó hủy theo native; không trạng thái nhiệm vụ riêng.

## 6. Quyền và kiểm soát

Cờ26 factory_receiving cần quantity_valuation_mvp và server_cost_guard; user đang hoạt động, vai trò Kế toán nhà máy/Stock User/Stock Manager/Accounts Manager/System Manager. Role không thay quyền chứng từ: PO/Company/Supplier/Item/Warehouse kiểm read; PR insert/submit/read native, không ignore_permissions. Các guard giá/quỹ/tài chính cũ giữ nguyên.

orders dùng get_list có quyền, chỉ name/supplier trong Company được đọc, tối đa200 đơn; vượt giới hạn báo lỗi. preview chỉ nguồn/Company/Supplier/price_mode và dòng/hàng/kho/lượng/quy cách; không doc.as_dict/giá/tổng/thuế. receive chỉ name/doctype/docstatus. Native đọc PR vẫn qua bảo vệ giá; NoCost cộng quản lý là đối chứng bắt buộc.

Dấu và lượng chất lượng chỉ tạo dưới ContextVar actor/key/payload, không whitelist context. Lối native giả/đổi/gỡ dấu hoặc xóa lịch sử chặn kể cả cờ tắt. Không mở generic list/export/GL/Bin/report giá cho nhà máy; lối vào từ báo cáo lượng hiện có.

## 7. Tác động hệ thống

Một PR chuẩn sở hữu tồn/giá/SLE/GL/sổ bao và lượng PO đã nhận; không sổ kho hoặc phiếu nhập thứ hai. Không thu khách/PE/PLE/doanh thu; công nợ mua theo hóa đơn native. Hàng có vấn đề vẫn dùng ngay theo xác nhận; điều chỉnh giá/chi phí sau đi quy trình kế toán và repost hiện có. Không thêm sản xuất/MISA.

## 8. Tiêu chí nghiệm thu

Unit: cờ/guest/role trước đọc; số hữu hạn/6 số lẻ/bao nguyên; từ chối giá giả/dòng trùng/kho sai Company; preview chỉ lượng; giả/đổi dấu kể cả cờ tắt và update-after-submit; datetime/số qua JSON giữ nguyên nghĩa; NULL key phiếu native; tệp riêng tư/ownership/hồ sơ khác.

HTTP giả: PO10kg×20.000; NoCost preview chỉ lượng; Company/role sai chặn. Nhận4kg gồm1kg có vấn đề tạo PR4kg theo giá20.000, không tự trả/giảm giá, còn6. Retry không tăng PR/SLE/GL/PLE, đổi nội dung chặn; giá client/kho khác Company/sửa dấu chặn. Hai phiên nhận4kg khi còn6: chỉ một thành công, còn2. Chrome từ báo cáo lượng, phiên nhà máy riêng, nhận1kg/bỏ200 sau commit/retry cùng Dialog: một PR/một SLE, còn1, form không có giá vốn; phải xem ảnh đúng SHA.

Năm case mới: HTTP_3A_RECEIVING_SCOPE_PREVIEW, HTTP_3A_RECEIVING_PARTIAL_REPLAY, HTTP_3A_RECEIVING_TAMPER, HTTP_3A_RECEIVING_RACE, DESK_3A_RECEIVING_RETRY. Dự kiến b01494/toàn HTTP285; chưa PASS trước run xanh và đọc artifact. Nghiệm thu nhân sự/dữ liệu/máy in thật vẫn gom cuối.

## 9. Triển khai và khôi phục

Không version/tag/merge/deploy. Cờ26 kh_aph_factory_receiving mặc định tắt, schema qua bộ cài rõ ràng, không after_migrate tự bật. Đồng bộ FLAGS/handoff/dấu vân/quay lui/Cổng3. UAT bật26 từ setup, giữ25 tắt cho hồi quy quỹ cũ rồi bật riêng như trước. Cổng3 nâng với5 cờ mới và kiểm trả0 khi rollback về production21 cờ. Cần4 cổng cùng SHA, đọc artifact/ảnh trước đóng lát. Khi phát hành vẫn diễn tập bản sao production có dữ liệu; rollback image+DB/files+cờ đồng thời, không tắt cờ để xóa dấu/hồ sơ đã phát sinh.
