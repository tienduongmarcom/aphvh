# Đối chiếu quyết định nghiệp vụ ↔ code/UAT (14/10/2026)

## Cập nhật trạng thái 17/10/2026 — đọc trước bảng lịch sử

Các mục 1–8 bên dưới ghi trạng thái ngày 14/10, KHÔNG phải danh sách việc chưa làm hiện tại. Code và đặc tả mới đã khép nhiều mục trong bảng; không hỏi lại các quyết định đã chốt hoặc xây lại chức năng theo dấu ⬜ cũ.

| Nhóm đã bổ sung | Code / bằng chứng trong bộ UAT hiện tại |
|---|---|
| Quỹ nhà máy, chi nhỏ, bàn giao, khóa giá Dũng | `factory_cash`, `HTTP_0111_QUY_NHA_MAY`, `HTTP_0111_KHOA_GIA_THANH_PHAM` |
| Giá tạm theo nhóm, phân bổ tháng, vét bồn | `factory_costing`, `HTTP_0111_GIA_TAM_THEO_NHOM`, `HTTP_0111_PHAN_BO_CUOI_THANG`, `HTTP_0111_VET_BON` |
| Dở dang/định mức, kiểm kê có mốc | `kho_chuan`, `HTTP_0112_PHONG_TOM_DINH_MUC`, `HTTP_0112_KIEM_KE_MOC` |
| Hạn chung/gia hạn, địa chỉ, hàng trả, giảm giá, MISA | `sales_p1`, bộ `b0113_cases` |
| Lãi gộp, dòng tiền, khóa kỳ, xác nhận nợ | `quan_tri`, bộ `b0114_cases` |
| Dữ liệu/đầu kỳ, kho vận hành, giá sàn | `du_lieu`, `dau_ky`, `kho_van_hanh`, `ban_quay`, bộ `b012_cases` / `b013_cases` |
| Tiền/ngân hàng, vay, sao kê, in lại kèm MISA | `tien_vay`, `trung_tam_ban`, bộ `b014_cases` |
| Phiếu xuất nháp và in nhanh, nhiều kho/pháp nhân/quyền | `ban_nhanh`, `b014_ban_nhanh_cases`, `b014_ban_nhanh_scope` |
| Hồ sơ bản ký/đối chiếu (ứng viên PR #4, chưa triển khai) | `ho_so_giao_nhan`, `HTTP_014_HO_SO_BAN_KY`, `NATIVE_DESK_HO_SO_GIAO_NHAN` |

Mốc mã nguồn `7827add`: UAT [39011438406](https://github.com/tienduongmarcom/aphvh/actions/runs/39011438406) đạt, artifact có 209 kết quả PASS/0 FAIL (gồm restore và chuẩn bị), đủ 21 kết quả b014. Đây là kiểm tự động bằng dữ liệu giả, chưa phải nghiệm thu nhân sự/máy in hoặc xác nhận đủ nguyên văn 202 câu. Kịch bản gom nghiệm thu: `docs/nghiem-thu-tong-the.md`; việc tiếp quản xem `docs/ban-giao.md`.

---

Nguồn quyết định: `docs/quyet-dinh-202-khoi-phuc.md` (bản khôi phục — R001–R105 theo chủ đề, Q172–Q202 có số câu;
**không** phải nguyên văn 202 câu). Bằng chứng: tên ca UAT HTTP/Desk trong `deploy/uat/http/*` (run xanh trên SHA
`55b4491`, 110 ca) và code `kh_aph`. Bảng này **không** tuyên bố nghiệm thu; chỉ cho biết đã có gì để kiểm.

Ký hiệu: ✅ có ca UAT trên CI · 🟡 có code hoặc ERPNext chuẩn đáp ứng, chưa có ca UAT · ⬜ chưa làm · ⚠️ cần xác nhận /
có thể mâu thuẫn với code · — không làm theo đúng quyết định.

## 1. Phạm vi, đơn bán, giá (R001–R014, Q172–Q182)

| Mã | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| R001 site `frontend`, không dùng erpnext.local | ✅ | Kiểm kê chỉ đọc 13/10; Cổng 3 |
| R002 4 đơn vị, TL=XB | ✅ | `khach.json`, Cổng 2/3 |
| R003 MISA cho hóa đơn | 🟡 | Trường "Hóa đơn điện tử đã xuất (MISA)" (`invoice_flag`) |
| R004 một danh mục khách chung | ✅ | Ca 4 công ty dùng một khách (`HTTP_FOUR_COMPANY_EMPLOYEE_STOCK_DEBT`) |
| R005 không giao dịch nội bộ giả | ✅ | `HTTP_FUNDS_APH_RECEIVES_TL_PLANNED`, `HTTP_FUNDS_CROSS_COMPANY_NEEDS_ROUTE` |
| R006–R007 đơn tổng hợp, dòng theo chủ kho | ✅ | APH Shared Sales Order; `HTTP_FOUR_COMPANY_*`, `HTTP_SLIP_FOUR_COMPANY_EMPLOYEE` |
| R008 giao từng phần, nhiều kho | ✅ / ⬜ | `HTTP_DISPATCH_SECOND_BATCH`; **nhiều địa chỉ giao trên một đơn (Q178) chưa có ca** |
| R009 đặt/đã giao/còn/hủy | ✅ | Ca đổi nguồn giữ lịch sử (`HTTP_SOURCE_REVERSE_HISTORY_CONSERVATION`) |
| R010 đổi nguồn phần chưa giao | ✅ | `HTTP_SOURCE_*`, `NATIVE_DESK_SOURCE_CHANGE_FULL` |
| R011 giá gợi ý, cảnh báo dưới ngưỡng/dưới giá vốn | 🟡 ⚠️ | Cảnh báo dưới bảng giá có (`sales_warnings`). Cảnh báo **dưới giá vốn** chưa rõ — và nếu hiện cho nhân viên bán hàng thì lộ giá vốn gián tiếp: cần quyết ai thấy cảnh báo này |
| R012 giá có thể gồm VAT, không cộng 2 lần | 🟡 | `kh_aph_gia_gom_thue`; chưa có ca UAT |
| R013–R014, Q172 không hoa hồng, ghi người nhập | 🟡 | Trường owner chuẩn ERPNext |
| Q173 CSKH | — | Hoãn đúng quyết định |
| Q174 KT bán hàng tạo khách, trường tài chính hạn chế | ✅ | Hạn mức permlevel 9; `HTTP_SECURITY_CUSTOMER_*` |
| Q175 không giữ trường mã MISA của khách | 🟡 | Không thấy trường mã MISA trên Customer trong app — cần xác nhận khi import |
| Q176 tự cấp mã `KH…` | ⬜ | Chưa cấu hình naming series Customer |
| Q177, Q179 nhiều địa chỉ, người nhận không bắt buộc | 🟡 | ERPNext chuẩn |
| Q180 đổi địa chỉ khi đang giao, lưu lịch sử | ⬜ | Chưa có ca |
| Q181 sửa phần chưa giao | 🟡 | `update_child_qty_rate` gốc + đổi nguồn; chưa có ca riêng |
| Q182 KT tự hủy phần chưa giao, không cần duyệt | ⬜ | Chưa có ca (đóng/hủy phần còn lại) |

## 2. Giao hàng, trả hàng (R015–R027, Q183–Q191)

| Mã | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| R015–R017 3 trạng thái, shipper/khách lấy | ✅ | `HTTP_DELIVERY_HANDOFF_STATE`, `HTTP_DELIVERY_PICKUP_STATE`, `HTTP_DELIVERY_RECEIPT_NO_REPOST` |
| R018 mỗi đợt/kho xác nhận phần mình | ✅ | `HTTP_DISPATCH_SECOND_BATCH`, `HTTP_EMPLOYEE_FOUR_COMPANY_HANDOFF_PICKUP` |
| R019 lưu người/thời gian | ✅ | `HTTP_DELIVERY_RECEIPT_HISTORY` |
| R020 không bắt buộc ảnh | ✅ | Không có ràng buộc đính kèm |
| R021 giao thiếu, hủy phần còn lại, đổi khách nhận | ✅ / ⬜ | Trả một phần ✅ (`HTTP_PARTIAL_RETURN`); hủy phần còn lại và đổi khách nhận ⬜ |
| R022, Q183–Q184 xe quay về / chuyển khách khác / chuyển kho | ⬜ | Chưa có luồng; hiện chỉ có trả hàng chuẩn |
| R023 hàng đang vận chuyển không cộng lại tồn | 🟡 | Xuất kho tại "Đang giao" nên không còn trong tồn; hàng quay về chưa có luồng |
| R024, Q186 chênh lệch số lượng → chứng từ điều chỉnh hợp lệ | ⬜ | Chưa có ca |
| R025 hàng trả theo tình trạng (bán được/cách ly/…) | ⬜ | Chưa có kho/trạng thái cách ly |
| R026 giảm giá sau giao, phân bổ theo tỷ trọng | ⬜ | Chưa |
| R027 cước khách trả thẳng lái xe | — | Ngoài sổ, đúng quyết định |
| Q185 KT xác nhận số khách thực nhận | ✅ | `HTTP_DELIVERY_RECEIPT_*` |
| Q187 ngày ghi nhận = ngày KT xác nhận, không backdate | ⚠️ | Cần đối chiếu với cách hóa đơn bán lấy ngày theo phiếu giao (`set_posting_time`) và ca COGS lùi ngày |
| Q188 đơn tự hoàn tất khi giao đủ | 🟡 | ERPNext chuẩn |
| Q189–Q190 đánh dấu quá ngày giao dự kiến | ⬜ | Chưa |
| Q191 một loại phiếu xuất kiêm giao | ✅ | Delivery Note + phiếu in |

## 3. Thu tiền, cọc, công nợ (R028–R049, Q165–Q170)

| Mã | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| R028 ba con số | ✅ | `NATIVE_FUNDS_IDENTIFY_AND_FIGURES`, `HTTP_FUNDS_TRANSFER_RELEASE_REFUND_THREE_FIGURES` |
| R029–R030 đúng quỹ/bank thực nhận; APH nhận APH+TL | ✅ | `HTTP_FUNDS_OWNER_ACTUAL_SETTLEMENT`, `HTTP_FUNDS_APH_RECEIVES_TL_PLANNED` |
| R031–R032 tiền chưa rõ đơn/người | ✅ | `HTTP_FUNDS_UNKNOWN_ACTUAL_CASH`, `HTTP_FUNDS_IDENTIFY_NO_OLD_DEBT_ALLOCATION` |
| R033–R035 cọc giữ riêng/chung/nguồn, hủy đơn có cọc | ✅ | `HTTP_FUNDS_COMMON_AND_SOURCE_DEPOSIT`, `…TRANSFER_RELEASE_REFUND…` |
| R036 trả gộp nhiều đơn, phân bổ tay | ✅ | `HTTP_FUNDS_PARTIAL_OWN_COMPANY_ALLOCATION` |
| R037 đối soát sao kê CSV/Excel, chống trùng | 🟡 | Chống trùng ✅ (`HTTP_FUNDS_RECEIPT_DUPLICATE`); đọc sao kê mới ở dạng chuẩn hóa (`…BANK_RECONCILIATION_READ_ONLY`), **chưa có bộ đọc theo từng ngân hàng** |
| R038 phiếu thu, đối chiếu công nợ định kỳ | 🟡 | Mẫu in Phiếu thu chi có; quy trình đối chiếu/xác nhận chưa |
| R039 chưa xác nhận nợ chỉ cảnh báo | ⬜ | Chưa có trạng thái "đã xác nhận công nợ" |
| R040–R041, R043 hạn mức chung 4 đơn vị, trừ tiền chưa phân bổ đã xác minh | 🟡 | `global_credit` + unit test; chưa có ca UAT cảnh báo hạn mức chung riêng |
| R042 khách rủi ro cao cần duyệt | ✅ | `HTTP_HIGH_RISK_*` (8 ca) |
| R044–R045, Q166–Q168 hạn thanh toán theo khách, chung theo ngày xác nhận đơn, gia hạn lưu ngày gốc | ⬜ | Chưa có ca; gia hạn lưu lịch sử chưa làm |
| Q169–Q170 = R026 | ⬜ | |
| R046–R048 tiền mặt Dũng thu tại nhà máy, bàn giao từng phần | ⚠️ ⬜ | **Mâu thuẫn tiềm ẩn**: quy tắc hiện tại cấm vai trò "APH Không xem giá vốn" mở mọi phiếu quỹ/cọc (`funds.has_permission`). Cần thiết kế luồng thu tiền mặt + bàn giao cho Dũng |
| R049 báo chuyển khoản ≠ tiền vào; KT HN xác minh | ✅ | Xác minh trên Desk có người/thời gian (`NATIVE_FUNDS_IDENTIFY_AND_FIGURES`) |

## 4. Kho, mua hàng, định giá (R050–R069)

| Mã | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| R050, R052 SKU/kho/chủ/ĐVT, bao nguyên | ✅ | `HTTP_PARTIAL_DISPATCH_BAG_LEDGER`, `HTTP_BAG_HISTORY_AND_CANCEL_GUARDS` |
| R051 MA theo SKU × kho | ✅ | `HTTP_MOVING_AVERAGE_PER_WAREHOUSE` |
| R053, Q199 phiếu hiện bao/kg; thùng/hộp | ✅ / 🟡 | Bao/kg ✅ (phiếu PDF); thùng/hộp chưa có ca |
| R054–R056 kiểm kê, chênh lệch lớn, thiếu/thừa chờ xử lý | 🟡 / ⬜ | Kiểm kê chuẩn ERPNext + kiểm bao; cảnh báo chênh lệch lớn và trạng thái chờ xử lý ⬜ |
| R057 đề nghị bổ sung theo ngưỡng | ⬜ | Có thể dùng reorder chuẩn — chưa cấu hình |
| R058–R059, Q79 yêu cầu chuyển không giữ hàng, nhiều kho nguồn | 🟡 | Material Request chuẩn không giữ hàng; chưa có ca |
| R060 chuyển kho không đổi chủ | 🟡 | Kho thuộc một công ty theo thiết kế ERPNext |
| R061 vượt tồn, nhiều nguồn | ✅ | Đơn chung + đổi nguồn |
| R062 KT HN quản lý giá mua; nhà máy xác nhận lượng | ✅ | Ca ẩn giá Dũng/nhà máy (`HTTP_DUNG_*`, `HTTP_PENDING_PRICE_AND_ROLE_GUARDS`) |
| R063 hàng thương mại chưa giá: chờ định giá, không giá 0 | ✅ | `HTTP_PENDING_EXCLUDED_FROM_AVAILABLE`, `HTTP_ZERO_VALUED_RECEIPT_REJECTED` |
| R064 nguyên liệu vào sản xuất bằng giá tạm, repost sau | ⚠️ | Repost ✅ (`HTTP_PRODUCTION_INPUT_COST_REPOST`); **ranh giới R063/R064** (nhóm hàng nào được giá tạm) chưa cấu hình — chính bản khôi phục cũng ghi cần đối chiếu |
| R065–R067 chi phí chuyến theo kg, chi phí sau nhập | ✅ | `HTTP_LANDED_COST_KG_AND_REPOST`, `HTTP_LATE_LANDED_COST_REPOSTS_DISPATCH_COGS` |
| R068–R069 hao hụt tự nhiên/bất thường | ✅ | `HTTP_ABNORMAL_LOSS_EXPENSE_SEPARATE` (+ tự nhiên trong ca sản xuất) |

## 5. Sản xuất, nhà máy, Dũng (R070–R092)

| Mã | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| R070–R071 nhà máy APH, chỉ Dũng đăng nhập | 🟡 | Cấu hình người dùng thật chưa có (site trắng) |
| R072, R078 nhiều thành phẩm/phụ phẩm, phân bổ theo kg | ✅ | `HTTP_PRODUCTION_KG_BYPRODUCT_ADDITIONAL_COST`, `HTTP_BOM_WORK_ORDER_MANUFACTURE` |
| R073 BOM dự kiến, cảnh báo chênh lệch | ⬜ | Cảnh báo chênh lệch thực xuất/BOM chưa |
| R074, R077, R081 | 🟡 | Theo thiết kế (kho chung, không truy vết mẻ) |
| R075–R076 kết thúc lệnh theo thực tế, WIP ước tính về 0 | ⬜ | Chưa |
| R079 chi phí cuối tháng ước tính rồi điều chỉnh | 🟡 | Repost ✅; quy trình ước tính/điều chỉnh chưa |
| R080, Q103 repack bảo toàn khối lượng | ✅ | "Đóng gói theo kg" (nghiệm thu 0.1) + ca sản xuất |
| R082 sấy hỗ trợ VH/MK theo số bao | ✅ | `HTTP_DRYING_FULL_BAGS_*` |
| R083–R084 Dũng chỉ số lượng, không xem giá vốn mọi lối | ✅ ⚠️ | `HTTP_DUNG_*`, `HTTP_COST_*` (14 ca). **Lối in PDF qua bộ dựng mới (`weasyprint.download_pdf`) có từ 16.35 chưa chặn**; thêm lối mới ở 16.50 — vá ở 0.11.0 |
| R085–R087 Dũng thấy chi phí mình chi, nhập chi phí nhỏ gộp | ⚠️ ⬜ | Quy tắc hiện tại cấm Dũng mở Purchase Invoice/Journal liên quan giá; **chưa có luồng nhập chi phí nhỏ cho Dũng** |
| R088–R089 | — | HN quản lý; không làm bảo dưỡng |
| R090 Dũng bán phụ phẩm, khách lẻ trả đủ | 🟡 | Quy tắc khách vãng lai chỉ bán thu tiền ngay có từ 0.3.4 (`controls.validate_sales_invoice`); chưa có ca UAT |
| R091, Q138 Dũng bán thành phẩm chính theo giá HN, không sửa giá | ⬜ | Chưa có khóa giá theo vai trò |
| R092 bán chịu theo hạn mức | 🟡 | Theo hạn mức chung + duyệt rủi ro cao |

## 6. Hóa đơn, báo cáo, quyền (R093–R105, Q192–Q202)

| Mã | Trạng thái | Bằng chứng / ghi chú |
|---|---|---|
| R093–R098 hồ sơ hóa đơn ngoài (số, ngày, đơn vị, trạng thái, điều chỉnh/thay thế), hàng đợi, khóa người xử lý | 🟡 / ⬜ | Hiện chỉ có cờ + số hóa đơn MISA; hồ sơ đầy đủ và hàng đợi là phạm vi 0.14.0 |
| R099–R104 báo cáo quản trị, lãi gộp/lãi sau chi phí trực tiếp, cộng lãi 4 đơn vị, dòng tiền 7/30 ngày, lãi tạm tính | ⬜ | Chưa (có "Tổng hợp bán hàng theo khách", tồn kho số lượng) |
| R105 quyền theo kho/đơn vị/vai trò; khóa kỳ | ✅ / ⬜ | Phạm vi công ty ✅ (`HTTP_COMPANY_SCOPE_*`); khóa kỳ chưa cấu hình |
| Q192 phiếu có/không giá, mặc định không giá | ⬜ | Chưa có chế độ in chọn có/không giá theo quyền |
| Q193–Q196 phiếu tổng hợp/riêng, đầu phiếu trung lập | ✅ / 🟡 | `HTTP_SLIP_CONSOLIDATED`, `…SINGLE_SELECTION`, `…SELECT_BATCHES`; đầu phiếu trung lập mặc định chưa có ca |
| Q197–Q198 in lại kèm số hóa đơn / theo lượng thực nhận, giữ bản gốc | ⬜ | Chưa |
| Q200–Q202 kg = bao × quy cách, bán theo kg hoặc bao, giá/bao = giá/kg × kg/bao | ✅ | `HTTP_SHARED_BAG_PRICE_PER_KG`, phiếu PDF |

## 7. Cần chủ dự án / khách xác nhận trước khi làm tiếp

1. **Tiền mặt và chi phí nhỏ của Dũng** (R046–R048, R085–R087): vai trò "APH Không xem giá vốn" hiện bị cấm toàn bộ
   phiếu quỹ/cọc và hóa đơn mua. Cần một luồng riêng chỉ hiện số tiền Dũng thu/chi, không hiện giá vốn.
2. **Cảnh báo bán dưới giá vốn** (R011): ai nhận cảnh báo? Hiện cho nhân viên bán hàng sẽ lộ ngưỡng giá vốn.
3. **Ranh giới giá tạm** (R063 vs R064): nhóm hàng nào là nguyên liệu nhà máy được dùng giá tạm.
4. **Ngày ghi nhận** (Q187) so với hóa đơn bán lấy ngày phiếu giao.
5. **Ghi nợ khi shipper nhận (R016) và báo cáo theo lượng khách thực nhận** — bản khôi phục ghi cần đối chiếu.
6. Q1–Q171 và Q158–Q160, Q162–Q163 vẫn thiếu nguyên văn; bảng này chỉ đối chiếu được với bản tóm lược.

## 8. Xếp việc chưa làm vào lộ trình (đề xuất)

| Bản | Việc từ bảng này |
|---|---|
| 0.11.0 | R084 vá lối in/xem trước (bảo mật, kèm nâng nền) |
| 0.12.0 Kho | R022/Q183–184 xe quay về/chuyển khách/chuyển kho, R024/Q186 điều chỉnh, R025 hàng trả theo tình trạng, R054–R057 kiểm kê/chênh lệch/bổ sung, R058–R059 |
| 0.13.0 Bán hàng | Q176 mã KH, Q178/Q180 nhiều địa chỉ/đổi địa chỉ, Q182 hủy phần còn lại, R026 giảm giá sau giao, R039/R044–R045 hạn thanh toán/xác nhận nợ, Q189–Q190, Q192/Q197–Q198 chế độ in, R091 khóa giá Dũng, R046–R048 tiền mặt Dũng |
| 0.14.0 KT tổng hợp–Thuế | R093–R098 hồ sơ + hàng đợi hóa đơn, R037 đọc sao kê theo ngân hàng, R038, R105 khóa kỳ, R099–R104 báo cáo |
| 0.15.0 Nhà máy | R073, R075–R076, R079, R085–R087 chi phí nhỏ của Dũng |
