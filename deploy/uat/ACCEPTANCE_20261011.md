# Kiểm kê và nghiệm thu UAT APH–VH–MK–TL — 11/10/2026

## Phạm vi

Đây là bản candidate trong draft PR #1, không phải bản production đã triển khai. Production là site `frontend`; UAT cô lập là `aphvh-web-uat`. Không dùng `erpnext.local`. Không merge, publish image, migrate hoặc ghi production trong đợt này.

Runtime được ghi nhận: Frappe **16.35.0**, ERPNext **16.36.1**, kh_aph **0.9.1**, lab9x **0.2.0**. Không ghi Frappe 16.36.1 theo phiên bản ERPNext. TL = XB, không tạo company thứ năm.

## Bằng chứng kiểm thử

Baseline ứng viên `3dfb324ef90286c38b672748b2fcebfeb450c18e` đã PASS **216 unit test, 0 skipped**, **79 ca HTTP nghiệp vụ, 0 FAIL**. [Candidate run 38152420145](https://github.com/tienduongmarcom/aphvh/actions/runs/38152420145) và [site trắng 38152420181](https://github.com/tienduongmarcom/aphvh/actions/runs/38152420181) đều SUCCESS. Tổng log 84 PASS gồm setup/login và 3 lần restore. Artifact candidate-image-evidence SHA256: `a475ba647f7564b95ff45a84a1ee4ef47b0aca35518c3f42c7b575c372699c4a`.

Restore counts + naming series giữ baseline: User 2; các master/giao dịch test, Bin, GL/SLE/PLE, Pending Receipt/Bag Movement/BOM/Work Order đều trở về 0. Schema UAT giữ Custom Field 123, Property Setter 214, Custom DocPerm 492, Version 13. Cleanup container và render PDF SUCCESS.

Dũng giả lập đã được thử role nhà máy và cộng dồn Sales Manager, Accounts User, Accounts Manager, Stock Manager với role APH Không xem giá vốn; API token, document/v2/child query/report/export/preview/print và thao tác kho đều có bằng chứng. Không suy ra cấu hình tài khoản Dũng thật đã đúng.

Bổ sung Desk cho bàn giao: nút Chốt giá nhập trên phiếu chờ và tự quy đổi bao/kg/giá bao. Runner `deploy/uat/http/desk.mjs` dùng Chrome thật trong CI; chỉ nghiệm thu khi case NATIVE_DESK_FINALIZE_AND_BAG_PREVIEW PASS trên commit đang bàn giao. Đây là một thao tác Desk và preview; không thay nghiệm thu mọi vai trò, luồng người dùng và máy in thật.

## Chức năng, code và mức nghiệm thu

| Yêu cầu đã chốt | Bằng chứng code | Kết luận / giới hạn |
|---|---|---|
| Một đơn APH/VH/MK/TL, source Item + kho | `kh_aph/kh_aph/doctype/aph_shared_sales_order/aph_shared_sales_order.py`: `_plan`, `on_submit`; `shared_order_rules.py`: `plan_orders` | Kho xác định company; tạo SO riêng có backlink/fingerprint. Fixture bốn company; lỗi một company rollback toàn request; gọi lặp không nhân SO. Chỉ Item tồn bằng Kg, tiền VND. |
| Stock/công nợ đúng company khi bàn giao | `delivery_receivable.py`; `sales_flow.py`; `hooks.py` | DN submit tạo SI đã submit, `update_stock=0`; native DN trừ stock một lần. Đã thử giao hai đợt, return, cancel, lỗi và submit đồng thời. |
| Ba trạng thái, pickup, nhật ký actor/time | `delivery_status.py`; `public/js/delivery_note.js` | Chờ xuất → Đang giao → Khách đã nhận; pickup đi thẳng đã nhận. Receive không repost sổ; server ghi actor/time. Sales read-only được receive qua endpoint riêng, không được generic write/submit. |
| Phiếu tổng hợp / từng đợt | `delivery_slip.py`; shared-order JS; các native Print Format | Phiếu quantity-only từ DN đã submit, giữ owner/kho, chọn batch, kiểm tra read/print từng DN. A4 mẫu tám batch/bốn company. Các mẫu native riêng có code nhưng chưa nghiệm thu máy in thật toàn bộ. |
| Giá vốn không lộ qua API | `server_cost_guard.py`; `cost_query_api.py`; `price_visibility.py` | Fixture factory và tổ hợp role đã thử document/v2/child-query, ledger/report/export. Admin/role hợp lệ vẫn xem được. Không suy ra Dũng thật đã đạt khi chưa có identity/roles thật. |
| Báo cáo theo company được cấp quyền | [Báo cáo nợ](../../kh_aph/kh_aph/report/tong_hop_ban_hang_theo_khach/tong_hop_ban_hang_theo_khach.py); [tồn số lượng](../../kh_aph/kh_aph/report/ton_kho_so_luong/ton_kho_so_luong.py) | Báo cáo nợ lọc Company bằng `get_list` và kiểm tra Customer read; báo cáo số lượng lọc Warehouse/Item được phép. Trước sửa, `get_all`/SQL/QB không tự áp quyền. Native read của đơn chung đa company bị chặn nếu người xem chỉ có APH: không nới quyền để in phần đã lọc. Phiếu APH riêng vẫn theo quyền native. Phạm vi test là hai báo cáo này; chưa kết luận tất cả báo cáo native/custom đều được nghiệm thu. |
| Hạn mức chung, tiền đã rõ khách chưa phân bổ | `global_credit.py`: `balance_for`, `evaluate`; `global_credit_rules.py` | Số dư Receivable GL ròng APH/VH/MK/TL; không trừ PE lần thứ hai. Cảnh báo khi lập đơn và kiểm tra giao. Fixture thu/phân bổ và hủy thu có bằng chứng ở các run UAT trước; chưa có UI ba số tổng đơn/nợ đã giao/chưa giao đầy đủ. |
| Khách rủi ro cao cần duyệt / thu hồi | `credit_release.py`; `credit_release_rules.py` | Accounts Manager/Administrator duyệt; fingerprint gắn nội dung DN; thay qty hoặc revoke làm mất hiệu lực. Direct SI bypass, giả duyệt và sửa cờ khách trái quyền bị chặn. Có ca revoke/dispatch đồng thời; không phải stress nhiều worker. |
| Lịch sử phê duyệt không được xóa | `credit_release.py`: `prevent_release_delete`; `hooks.py`: `APH Credit Release.on_trash` | Chặn delete độc lập feature flag để giữ lịch sử kể cả khi tắt guard. Thu hồi ghi user/time/reason; không tự đảo giao đã submit. Không cam kết chống can thiệp SQL/root ngoài ứng dụng. |
| Nhận tiền đúng company/account | Native Payment Entry; `controls.py`; `thu_ho.py` | Có fixture thu từng company, unallocated và hủy thu; APH PE trỏ VH SI bị native account guard chặn. Không đồng nghĩa đã làm cơ chế APH nhận phần TL theo kế hoạch, cọc chung/cọc nguồn hoặc tiền chưa biết khách. Hướng dẫn `thu_ho.py` đã sửa thành phân bổ được duyệt trong ERP, MISA chỉ hóa đơn thuế; thay lời hướng dẫn chưa phải hoàn thành workflow thu hộ/phân bổ. |
| MISA chỉ hóa đơn thuế | `invoice_flag.py`; `vat.py`; các trường SI số/ký hiệu/ngày hóa đơn | ERP ghi nợ độc lập MISA; không gọi MISA trong UAT. APH/VH yêu cầu tax template, TL nội bộ không VAT. Kết nối/đối soát MISA thật chưa test. |
| Giá cơ sở VNĐ/kg, bao = kg × quy cách | `quantity_rules.py`; `bag_stock.py`; `public/js/bag_quantity.js` | UAT nhập/giao/trả theo 2 lượng, snapshot quy cách và giá/bao PASS. 3 bao × 25 kg = 75 kg; 20.000/kg = 500.000/bao. Native Desk preview có gate riêng; chưa đối soát tồn bao vật lý production. |
| Sản xuất / phụ phẩm | `stock_entry_kg.py`; `landed_cost_kg.py`; inventory HTTP runner | kg-v3 Repack/Manufacture có BOM/Work Order, phụ phẩm giá cố định, chi phí thêm, hao hụt tự nhiên, giá nguyên liệu đến sau và cancel PASS. Giữ v1/v2 chứng từ cũ. VH/MK sấy đủ bao không Subcontracting có fixture PASS. |
| Hàng chờ định giá / MA / hao hụt / chi phí chuyến | `pending_valuation.py`; `bag_stock.py`; `landed_cost_kg.py` | Pending không khả dụng, không GL/SLE; zero-price/unauthorized/manual-link bị chặn; chốt một PR và gọi lặp PASS. MA theo kho, chi phí theo kg, repost đầu ra và hao hụt bất thường vào chi phí PASS. Chưa suy ra mọi ca COGS bán backdated đạt. |
| Đối chiếu nợ, sao kê, cọc và đổi nguồn | Báo cáo nợ/PE/JE native và code thu hộ hiện có | Chưa có nghiệm thu workflow xác nhận khách, import sao kê chống trùng, tiền chưa biết khách, cọc chuyển/hoàn theo thỏa thuận và đổi nguồn sau giao một phần. Không tự FIFO hoặc tự đổi bank/company nhận. |

## P0/P1 còn mở

P0 là điều kiện trước vận hành thật khi nghiệp vụ có trong pilot. Không đóng chỉ vì unit test xanh.

| Gate | Mức | Ca nghiệm thu bắt buộc |
|---|---|---|
| Tài khoản Dũng thật và role cộng dồn | P0 deployment | Document/API/child-query/report/export/print không lộ giá vốn; người có quyền vẫn xem được. |
| Bao/kg và số bao vật lý | UAT PASS; P0 migration | Kiểm kê số bao mở đầu theo item/kho; không suy số bao vật lý từ tồn kg cũ. |
| Nhập chờ giá, điều chỉnh MA/COGS | Pending/MA/repost UAT PASS; P0 còn lại | Backdated bán hàng và COGS downstream cần oracle GL/SLE riêng nếu có trong pilot. |
| Sản xuất/phụ phẩm/chi phí | UAT PASS | 19 ca inventory tại baseline gồm BOM/Work Order, late input cost, hao hụt, cancel và sấy; production chưa triển khai. |
| APH nhận TL, cọc chung/cọc nguồn, tiền chưa biết khách | P0 | Ghi đúng quỹ/bank thực nhận, kế hoạch phân bổ/hoàn/chuyển có lịch sử, không tự bù/FIFO/trả nợ company khác. |
| Đổi nguồn khi thiếu, ba số giá trị/nợ | P0 | Giao từng phần rồi đổi source; owner/sổ/backlink đúng; tổng đơn còn phải trả / nợ đã giao / chưa giao khớp chứng từ và thu. |
| Native Desk và dữ liệu/quyền site frontend hiện tại | P0 | Read-only inventory mới; thao tác người thật trong UAT; không suy ra runtime production từ CI. |
| Xác nhận công nợ, sao kê tránh trùng | P1, nâng P0 nếu dùng trong pilot | Biến động cập nhật đối chiếu, khách chưa ký được cảnh báo; import sao kê không tạo thu trùng, file/bằng chứng lưu được. |
| Stress nhiều worker, toàn bộ báo cáo, máy in | P1, nâng P0 theo phạm vi pilot | Stress retry/race, quyền company/warehouse trên các báo cáo còn lại, nhiều trang A4 và máy in thực tế. |
| Đối chiếu đủ 202 quyết định | Gate nghiệm thu toàn dự án | Bản nguyên văn chưa được tìm thấy. Personal Context chỉ tìm thêm câu 124/200/202; không tạo giả ma trận 202/202. |

## Thứ tự hoàn tất MVP

1. Giữ candidate đã kiểm thử và CI artifacts làm baseline; production tiếp tục nguyên trạng.
2. Dùng các ca bag/kg, pending valuation và sản xuất đã PASS làm baseline; chốt thao tác Desk được gate và kế hoạch tồn bao mở đầu.
3. Hoàn thiện phân bổ thực nhận APH/TL, cọc/tiền chưa biết khách, đổi source và ba số nợ; kiểm thử không tự bù/FIFO.
4. Nghiệm thu người thật, native Desk, quyền company/warehouse, toàn bộ báo cáo và bộ quyết định nguyên văn.
5. Chỉ sau các gate trên mới lập release có image digest, backup, migrate trên clone, rollback rehearsal và phê duyệt triển khai cụ thể. PR vẫn draft; không triển khai tự động.

Không gắn PASS cho phần chỉ có code, native capability hoặc chưa có fixture kiểm thử. Báo cáo này cập nhật kiểm kê ngày 10/10; không thay thế dữ liệu quyết định gốc.
