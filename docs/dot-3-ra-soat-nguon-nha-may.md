# Rà nguồn đợt3 — gom thao tác nhà máy, giữ nghiệp vụ đã có

Baseline production0.15.3 theo người vận hành; nhánh phát triển nối PR #16 (quỹ/cá nhân/bảng quản lý đã đủ4 cổng). Không coi các nghiệp vụ thiếu màn nhập nhanh là chưa có backend. Nghiệm thu người dùng/dữ liệu/máy in thật gom cuối, không chặn phát triển trên UAT giả.

| Mã | Nguồn đã có, bằng chứng code | Phần bổ sung thực sự / giới hạn |
|---|---|---|
| NM01a nhận từ PO | price_visibility.validate_purchase_receipt, native PO.make_purchase_receipt, bag_stock, factory_costing.validate_gia_tam | PR #17 đang kiểm facade/Dialogue lượng và hồ sơ; giá từ PO, một PR/nonce/khóa, hàng có vấn đề vẫn nhập đủ lượng và ghi riêng phần cần đàm phán |
| NM01b chờ định giá | APH Pending Receipt.validate, pending_valuation.finalize, Ton kho so luong.pending_kg | Có nhập lượng ngoài khả dụng và chốt giá tạo PR duy nhất; chưa gom cửa sổ nhận. Nếu nối từ PO phải giữ đúng từng dòng PO qua phiếu chờ đến PR, tính phần còn/giữ chỗ giữa phiếu chờ và nhập có giá, không tạo thêm một nhập độc lập |
| NM01c chuyển đến | Stock Entry native/Material Request; kho_van_hanh.tao_yeu_cau_chuyen; cây kho Company | Chưa có cửa sổ nhận chuyến đến. Phải phân biệt chuyển cùng Company với mua/bán khác Company; không dùng PR mua để nhận mọi chuyến chuyển |
| NM02 sản xuất | stock_entry_kg.StockEntryKgCosting, validate_kg_entry, allocate_finished_cost_by_kg; loại Sản xuất theo kg, kg-v3/kg-v4; lab9x.costing_rules/gia_thanh | Backend chia kg/hệ số/phụ phẩm và snapshot khi repost đã có. Chưa có Dialog chọn lệnh/định mức/dây chuyền rồi ghi đầu vào–đầu ra–dở dang–chênh lệch một lần. Không ép thiếu đầu ra thành hao hụt hoặc tự đưa đầu vào chưa dùng ra khỏi kho |
| NM03 dở dang | Warehouse.kh_aph_loai_kho=Dở dang dây chuyền; factory_costing.quyet_toan_do_dang/vet_bon/so_lieu_ky; docs/dac-ta-0.11.2.md | Mỗi dây chuyền có kho dở dang, không dựng lại từng bồn. Chỉ gọi quyết toán khi kết thúc/dừng chuyền thật; màn ngày cần lượng vào–ra–còn, không tự vét0 mỗi ngày |
| NM04 đóng gói/đổi bao | stock_entry_kg.REPACK_TYPE/DONG_GOI_TYPE/BAO_TOAN_KG; hai công đoạn theo docs/dac-ta-0.11.2.md; kho_chuan.la_bao_bi | Đã có Đổi bao, đóng gói lại và Đóng gói thành phẩm; cân đối kg, bao bì không tính thành kg hàng. Chưa gom Dialog nhập ngắn. Không đổi quy cách để che thiếu hụt, không phân bổ lại chi phí tháng vào công đoạn2 |
| NM05 xuất/chuyển | ban_nhanh/delivery_status/ho_so_giao_nhan cho DN, kho_van_hanh và Stock Entry native cho chuyển | Luồng bán/giao/bản ký đã có. Hồ sơ DN không tự bao phủ Stock Entry; cửa sổ nhà máy phải chọn đúng nghiệp vụ bán/cùng Company/khác Company |
| NM06 tiền/ngày | PR #15–#16 personal_cash, factory_handover, cash_issue; báo cáo day_close quản lý | Tiền cá nhân/chốt tự thân/nhận-hoàn nhà máy đã kiểm. Report day_close là cho quản lý, chủ động chặn NoCost; bảng ngày cho Dũng cần facade lượng/tiền của mình riêng, không mở report tài chính hiện tại |
| NM07 quyền Dũng | dung_cost_policy/SENSITIVE, server_cost_guard, cost_query_api, print_guard, price_visibility | Không đổi generic guard để đọc BOM/Work Order/GL. Facade sản xuất kế tiếp phải đặc tả cách đọc metadata lượng tối thiểu của nguồn được phép và User Permission; không trả nguyên doc, không dùng ignore_permissions như cách chữa quyền |

## Quyết định chất lượng mới đã chốt19/10

Hàng có vấn đề thường giữ lại dùng ngay, đàm phán giảm giá sau. Nhận đủ tổng lượng thực giữ/dùng; lượng có vấn đề là phần trong tổng lượng, không rejected_qty/phiếu trả tự động. Giá hiện hành lấy từ PO; điều chỉnh sau theo chứng từ kế toán/repost. Snapshot ở PR #17 không là trạng thái xử lý giá hiện tại. Chưa có giá hợp lệ vẫn vào pending, không tồn giá0. Không suy mọi chuyến đều không được trả/cách ly.

## Thứ tự kỹ thuật kế tiếp

1. Đọc đủ4 cổng/ảnh PR #17 đúng mã; chỉ sửa khi có lỗi thực tế. Chưa phát hành production từ PR này.
2. Chốt đặc tả9 nhóm NM01b: nguồn PO hoặc nhận chưa có PO, chống trùng/giữ phần đã nhận giữa pending và PR, người nhận/tệp/chất lượng; giữ native finalize và quyền kế toán chốt giá.
3. Rà meta native Work Order/BOM/Stock Entry đúng nền, thiết kế facade NM02/03; nguồn không xem giá vốn phải có kiểm quyền độc lập, từng hành động/field/Company/Warehouse. Chọn mẻ/lệnh/dây chuyền và dữ liệu dở dang thật, không tạo “sổ sản xuất” nhập lần hai.
4. Gom NM04/05 bằng service đã có; phân biệt sản xuất/đóng gói/đổi bao, bán/chuyển, hồ sơ ký từng loại.
5. Sau khi các luồng đã nối, tạo Workspace nhà máy và bảng ngày lượng/việc tồn/tiền cá nhân. Dialog trước; chỉ Native Page nếu đủ6 tiêu chí kiến trúc và có đo A/B. Không dùng Page để bỏ qua lớp quyền.

Đây là rà nguồn và điểm nối, không phải kết quả PASS các chức năng còn thiếu. Đợt4 tài chính toàn chuỗi và đợt5 hóa đơn một phần vẫn ngoài phạm vi tài liệu này.
