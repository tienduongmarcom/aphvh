# Hồ sơ hệ thống ERPNext APH–VH–MK–TL để BA đánh giá thiếu sót (trước bản 0.11.1)

**Ngày lập:** 14/10/2026 · **Người lập:** Claude (đơn vị tư vấn 9xLab) · **Chủ dự án:** anh Tiến
**Repo:** `github.com/tienduongmarcom/aphvh` (private), nhánh `fix/p0-uat-v091-20261010` (PR #1), tag mới nhất `v0.11.0`.

---

## 0. Đọc trước: nhiệm vụ của BA và quy tắc

**Nhiệm vụ:** đối chiếu hệ thống đang có (mục 3–6) với nghiệp vụ đã chốt (mục 7) và thực tế vận hành của khách, để
liệt kê **mọi nghiệp vụ / chức năng / báo cáo / phân quyền / dữ liệu còn thiếu hoặc sai**, rồi xếp vào **0.11.1**
(bổ sung trước khi làm giao diện 0.12.0) hay để sau.

**Quy tắc bắt buộc khi đánh giá**

1. Không hỏi lại các quyết định đã chốt ở mục 7. Nếu thấy mâu thuẫn giữa hai quyết định, ghi rõ mã hai quyết định và
   để chủ dự án chọn — không tự chọn.
2. Không coi số ca kiểm thử là nghiệm thu. "Có ca UAT" nghĩa là đã chạy đúng trên dữ liệu giả lập trong CI, **chưa** nghiệm
   thu với người dùng thật.
3. Không tuyên bố đủ "202/202 quyết định": chỉ có bản khôi phục (R001–R105 theo chủ đề, Q172–Q202 có số câu); Q1–Q171 chưa
   có nguyên văn.
4. Theo thông tư/nghị định Việt Nam (TT133/2016, TT99/2025, TT152/2025, NĐ 123/2020, NĐ 70/2025, NĐ 181/2025,
   NĐ 310/2025, NĐ 68/2026). Điều gì chưa chắc về pháp lý thì ghi "cần đối chiếu điều khoản", không đề xuất làm ngay.
5. Ràng buộc kỹ thuật (mục 4.4) là cố định — đề xuất phải làm được trong ràng buộc đó.
6. Bản **0.11.1** chỉ nên chứa **backend / nghiệp vụ / quyền / báo cáo / mẫu in** còn thiếu. Giao diện theo nhóm người
   dùng (Workspace, Native Page) thuộc 0.12.0–0.15.0.

**Đầu ra mong muốn:** bảng ở mục 12.

---

## 1. Doanh nghiệp và con người

| Đơn vị | Loại | Chế độ kế toán | MST | Ghi chú |
|---|---|---|---|---|
| **APH** — CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI VÀ XUẤT NHẬP KHẨU AN PHÚ HƯNG | Công ty TNHH | TT133/2016 | 2601002157 | Có **nhà máy Phú Thọ** (sản xuất, sấy hỗ trợ VH/MK) |
| **VH** — CÔNG TY CỔ PHẦN THƯƠNG MẠI VĨNH HƯNG | Công ty CP | TT99/2025 | 0500470349 | Thương mại |
| **MK** — HỘ KINH DOANH MINH KHANG *(tên tạm, chờ khách xác nhận)* | Hộ kinh doanh | TT152/2025 | — | Sổ HKD |
| **TL** *(tên tạm)* — còn gọi **XB** | Đơn vị nội bộ | Không thông tư, không VAT | — | Hàng không hóa đơn; **không tạo công ty thứ 5** |

- Một site ERPNext chung cho cả 4 đơn vị; **một danh mục khách hàng chung**.
- **MISA** chỉ để lập **hóa đơn GTGT** và kế toán thuế; ERPNext ghi **tồn kho, công nợ, tiền vận hành**.
- Kho bán hàng ở **Hà Nội, Đà Nẵng, TP.HCM**; nhà máy **Phú Thọ** (APH).
- Người dùng dự kiến (chưa tạo tài khoản thật):
  - **Kế toán trưởng** — Desk ERPNext đầy đủ, phê duyệt (rủi ro cao, tuyến tiền APH nhận hộ TL).
  - **Kế toán Hà Nội** (bán hàng, mua hàng, tổng hợp–thuế, xác minh tiền vào).
  - **Thủ kho** các kho bán.
  - **Dũng** — người dùng duy nhất ở nhà máy (công nhân không đăng nhập): làm số lượng nhập/xuất/sản xuất/trả hàng, chi phí
    nhỏ, bán phụ phẩm; **tuyệt đối không xem giá mua, giá vốn, giá trị tồn, giá thành** qua mọi lối (màn hình, API, in, xuất).
- **Ngày chốt số dư: 30/09/2026.** Chế độ dữ liệu `tu_nhap`: khách tự nhập; chứng từ từ 01/10 nhập bù từng phiếu.

---

## 2. Trạng thái triển khai hiện tại (14/10/2026)

| Mục | Giá trị |
|---|---|
| Production | Site `frontend`, VM GCloud `erpnext-prod`, http://34.143.178.144 |
| Phiên bản | **kh_aph 0.11.0**, **lab9x 0.2.1** trên **ERPNext 16.50.0 + Frappe 16.51.0** (nền ghim digest) |
| Dữ liệu | **Trắng**: 0 khách, 0 mặt hàng, 0 chứng từ, 0 dòng sổ. Chỉ có 4 công ty, hệ thống tài khoản, 4 kho gốc, Administrator |
| Cờ tính năng | Bật đủ 8 (mục 5.4) |
| Sao lưu | 2 lần/ngày lên Google Cloud Storage + sao lưu trước mỗi lần nâng cấp; quay lui có kiểm |
| Kiểm thử | 232 unit test; **116 ca nghiệp vụ HTTP/Chrome** trên CI (kho 33, tiền 19, giá vốn 16, giao hàng 48); site trắng; diễn tập dựng/nâng cấp/quay lui; nâng cấp từ đúng image production |

---

## 3. Chức năng hiện có (theo nghiệp vụ)

Ký hiệu bằng chứng: **[UAT]** có ca CI (tên ca trong ngoặc) · **[Code]** có code, chưa có ca UAT · **[Chuẩn]** dùng
ERPNext chuẩn, chưa cấu hình/kiểm riêng.

### 3.1 Cài đặt nền (dựng site trắng một lệnh từ `khach.json`)
- Hệ thống tài khoản chuẩn **TT133** (APH), **TT99** (VH), **bộ HKD TT152** (MK), **bộ gọn nội bộ** (TL); tự tạo phần thiếu,
  không xóa/đổi tên tài khoản có sẵn; bỏ tài khoản/kho/nhóm mẫu của ERPNext. [UAT site trắng]
- Nhóm hàng cấp 1 gắn tài khoản kho theo loại hình (`thuong_mai`: Hàng hóa, CCDC, Dịch vụ, Tài sản; `san_xuat` có thêm NVL,
  thành phẩm…); mặt hàng mới mặc định nhóm "HH - Hàng hóa". [UAT]
- Quy tắc nhóm hàng (lõi `lab9x`): nhóm con tự lấy tài khoản kho của cha; cảnh báo nhóm chưa có tài khoản; cho đổi nhóm
  khi cùng tài khoản; **chặn** đổi tài khoản kho của nhóm đã có phát sinh. [Unit test]
- Mẫu thuế: thuế bán theo loại khách; mẫu "Thuế GTGT mua vào" (1331) mặc định; tắt tự thêm thuế theo mẫu mặt hàng (tránh
  tính 2 lần). [UAT site trắng]
- **Không tạo kho** — khách tự tạo cây kho. Bộ kiểm triển khai (~53 mục) chạy sau mỗi lần cài/nâng cấp.

### 3.2 Bán hàng
- **Đơn bán chung nhiều công ty** (APH Shared Sales Order): nhân viên lập một đơn, mỗi dòng chọn mặt hàng + kho nguồn;
  hệ thống tách Sales Order theo **công ty chủ kho**; lỗi một công ty thì hủy cả; gọi lặp không nhân đôi.
  [UAT `HTTP_FOUR_COMPANY_EMPLOYEE_STOCK_DEBT`]
- **Đổi nguồn phần chưa giao** (APH Source Change): chuyển số lượng còn lại sang kho/công ty khác, giữ nguyên phần đã giao;
  chặn phiếu giao cũ; đảo theo thứ tự; khôi phục dòng; chặn mở lại nguồn đã chuyển hết. [UAT 10 ca `HTTP_SOURCE_*`,
  `NATIVE_DESK_SOURCE_CHANGE_FULL`]
- Giá: bảng giá gợi ý, nhân viên sửa; **cảnh báo giá thấp hơn bảng giá**, công nợ vượt hạn mức, nợ quá hạn (cảnh báo,
  không chặn). [Code]
- **Bao/kg**: giá cơ sở theo kg; giá/bao = giá/kg × kg/bao; số bao nguyên; snapshot kg/bao trên chứng từ.
  [UAT `HTTP_SHARED_BAG_PRICE_PER_KG`]
- **Hạn mức công nợ chung** một khách qua 4 đơn vị; tiền chưa phân bổ đã xác minh trừ ròng một lần. [Code + unit test]
- **Khách rủi ro cao**: kế toán trưởng duyệt bán chịu; đổi lượng/nội dung làm duyệt hết hiệu lực; thu hồi duyệt.
  [UAT 8 ca `HTTP_HIGH_RISK_*`]
- **Có/không xuất hóa đơn GTGT** trên đơn/phiếu giao/hóa đơn (Không = giá đã gồm VAT, tách ngược, phiếu in không dòng thuế;
  kế toán vẫn xuất trên MISA). Ô "Khách lấy hóa đơn" đang **mở** cho khách dùng, sẽ đóng sau. [Code]
- Thuế bán theo loại khách (công ty/HTX: nông sản không kê khai tính nộp; hộ/cá nhân 5%); kế toán đổi được từng chứng từ. [Code]
- **Khách vãng lai chung**: chỉ bán thu tiền ngay; ghi tên/SĐT người mua thực tế. [Code]
- Hóa đơn bán nháp tự tạo khi xác nhận phiếu giao. [UAT]
- Chặn ngày tương lai; chặn hóa đơn bán trực tiếp né duyệt rủi ro cao. [UAT `HTTP_SECURITY_DIRECT_SI_BLOCKED`]

### 3.3 Giao hàng và trả hàng
- **3 trạng thái**: Chờ xuất → Đang giao → Khách đã nhận. Shipper nhận (Đang giao) thì **xuất kho + ghi nợ**; khách tự lấy
  thì xuất ngay; "Khách đã nhận" không ghi sổ lần 2. Lưu người/thời gian; không bắt buộc ảnh. [UAT `HTTP_DELIVERY_*` 9 ca]
- Hóa đơn bán submitted cùng giao dịch với phiếu giao; giao nhiều đợt; hai yêu cầu đồng thời cùng phiếu không ghi nợ 2 lần.
  [UAT `HTTP_DISPATCH_*`, `HTTP_CONCURRENT_SAME_DN`]
- Phiếu giao **tổng hợp** (nhiều công ty) và **riêng** từng công ty; chọn đợt giao; PDF. [UAT `HTTP_SLIP_*` 6 ca]
- Nhân viên bán hàng/thủ kho xác nhận "khách đã nhận" theo phạm vi; vai trò không liên quan bị từ chối. [UAT]
- **Trả hàng**: trả một phần khôi phục kg/bao/công nợ; hủy theo thứ tự. [UAT `HTTP_PARTIAL_RETURN`, `HTTP_RETURN_*`]

### 3.4 Kho, bao/kg, giá vốn, sản xuất
- Giá vốn **Moving Average theo mặt hàng × kho**. [UAT `HTTP_MOVING_AVERAGE_PER_WAREHOUSE`]
- Sổ bao (APH Bag Movement): số bao thực tế song song kg; giao/trả/hủy bảo toàn cả bao và kg. [UAT `HTTP_BAG_*`, `HTTP_PARTIAL_DISPATCH_BAG_LEDGER`]
- **Nhập chưa biết giá** (APH Pending Receipt): hàng chờ định giá **không vào tồn khả dụng/GL/SLE**; không cho giá 0; nút
  chốt giá tạo phiếu nhập, gọi lặp không nhập lại. [UAT `HTTP_PENDING_*` 4 ca, `NATIVE_DESK_FINALIZE_AND_BAG_PREVIEW`]
- **Chi phí chuyến phân bổ theo kg** (Landed Cost Voucher), repost giá vốn kể cả sau khi đã bán. [UAT `HTTP_LANDED_COST_KG_AND_REPOST`, `HTTP_LATE_LANDED_COST_REPOSTS_DISPATCH_COGS`]
- Bán lùi ngày: giá vốn GL/SLE khớp sau repost. [UAT `HTTP_BACKDATED_DISPATCH_COGS_GL_SLE`]
- **Hao hụt**: tự nhiên giữ chi phí trong tồn còn lại; bất thường ghi chi phí riêng đúng công ty, bắt buộc lý do. [UAT `HTTP_ABNORMAL_LOSS_EXPENSE_SEPARATE`]
- **Sản xuất theo kg**: phiếu "Đóng gói theo kg"/"Sản xuất theo kg" nhiều thành phẩm, chia giá theo kg (quy tắc lưu trên phiếu,
  repost không đổi), dòng giá cố định cho phụ phẩm; BOM/Work Order; hủy phục hồi. [UAT `HTTP_PRODUCTION_*`, `HTTP_BOM_WORK_ORDER_MANUFACTURE`, `HTTP_WORK_ORDER_MANUFACTURE_CANCEL`]
- **Sấy hỗ trợ VH/MK** theo số bao nguyên. [UAT `HTTP_DRYING_FULL_BAGS_*`]
- Báo cáo **Tồn kho số lượng** (không giá) và **Tồn kho theo tài khoản × địa điểm**.

### 3.5 Tiền, cọc, công nợ
- **Tiền thực thu** (APH Funds Receipt) vào đúng bank/quỹ của đơn vị thực nhận; khóa chống trùng; tiền chưa rõ khách/đơn ghi
  chưa phân bổ, xác minh trên Desk (người/thời gian). [UAT `HTTP_FUNDS_UNKNOWN_ACTUAL_CASH`, `HTTP_FUNDS_RECEIPT_DUPLICATE`, `NATIVE_FUNDS_IDENTIFY_AND_FIGURES`]
- **Kế hoạch tiền** (APH Funds Action): giữ cọc chung / cọc theo nguồn, chuyển, giải phóng, cấn hóa đơn một phần, hoàn tiền,
  trả tiền thu hộ; **không FIFO, không tự cấn nợ cũ**; chống chi quá (kể cả đồng thời). [UAT 9 ca]
- **APH nhận hộ TL** (APH Funds Route): tuyến bank/giữ hộ/phải thu nội bộ được duyệt; tiền TL chỉ phát sinh khi chuyển thật.
  [UAT `HTTP_FUNDS_APH_RECEIVES_TL_PLANNED`, `HTTP_FUNDS_CROSS_COMPANY_NEEDS_ROUTE`]
- **Ba con số** trên đơn chung: tổng đơn, công nợ phần đã giao, giá trị chưa giao. [UAT]
- Đối soát sao kê: **mới đọc dữ liệu đã chuẩn hóa**, chưa có bộ đọc file từng ngân hàng. [UAT chỉ đọc]
- **Thu hộ** (khách lấy hàng TL, chuyển khoản vào tài khoản APH/VH): 3388 chi tiết, cờ "Cần xử lý", báo cáo **Tiền thu hộ chưa xử lý**. [Code]
- Thanh toán qua bên thứ ba; cảnh báo tiền mặt lớn (NĐ 181/2025: từ 5 triệu cần thanh toán không dùng tiền mặt để khấu trừ). [Code]

### 3.6 Mua hàng và thuế mua vào
- Phiếu nhập tự gắn mẫu "Thuế GTGT mua vào" (1331) khi chưa có thuế; **kế toán tự chọn thuế suất** từng dòng (không tự chọn).
- Chặn nhầm chiều: 33311 trên phiếu mua, 1331 trên phiếu bán. [Code]
- Vai trò nhà máy: phiếu nhập nguyên phụ liệu **bắt buộc lấy từ đơn mua**; vật tư vận hành (nhóm được tích) được tự nhập giá.
- Vai trò nhà máy chọn được mẫu thuế mua vào (ERPNext 16.50). [UAT `HTTP_FACTORY_PURCHASE_TAX_DEFAULT`]

### 3.7 Phân quyền và bảo vệ giá
- Vai trò của app: **Kế toán nhà máy**, **Nhân viên bán hàng**, **Thủ kho bán hàng**, **APH Không xem giá vốn** (Dũng).
- Ẩn giá mua/giá vốn: trên màn hình, bản in (`before_print`), xem trước sổ, API (`frappe.client.*`, REST v1/v2, dòng con,
  query report, export, API token), phản hồi JSON được che. [UAT `HTTP_COST_*`, `HTTP_DUNG_*`]
- 0.11.0: chặn các lối in/xem trước mới của Frappe bỏ qua bước xóa giá. [UAT `HTTP_PRINT_BYPASS_DENIED`]
- Phạm vi công ty: người chỉ có quyền APH không thấy VH; phiếu tổng hợp nhiều công ty bị từ chối. [UAT `HTTP_COMPANY_SCOPE_*`]
- Nhân viên bán hàng chỉ thấy giá của bảng giá bán.

### 3.8 Hộ kinh doanh (MK)
- Báo cáo **Sổ doanh thu HKD**, **Sổ kế toán HKD** theo TT152/2025. [Code] — mẫu sổ **chưa đối chiếu** bản chính thức.

### 3.9 Mẫu in và báo cáo
- Mẫu in: Phiếu nhập kho (01-VT), Phiếu kho, Phiếu xuất kho bán hàng, Biên bản giao nhận (2 liên), Phiếu thu chi, Phiếu bán
  hàng; phiếu giao tổng hợp/riêng. Số tiền bằng chữ tiếng Việt.
- Báo cáo: Tồn kho số lượng; Tồn kho theo tài khoản và địa điểm; Bán hàng có hóa đơn; Tổng hợp bán hàng theo khách;
  Tiền thu hộ chưa xử lý; Sổ doanh thu HKD; Sổ kế toán HKD. Ngoài ra dùng báo cáo chuẩn ERPNext (sổ cái, công nợ, tồn kho…).

### 3.10 Kiểm soát kế toán
- Chặn ngày chứng từ tương lai; không bút toán tay vào tài khoản kho; cảnh báo tiền mặt lớn, tiền trả trước chưa gắn đơn;
  khóa sổ theo ngày (vai trò được sửa sổ đã khóa: Accounts Manager — **khóa kỳ chưa cấu hình**).

---

## 4. Kiến trúc kỹ thuật

### 4.1 Thành phần
- **`lab9x`** (lõi 9xLab, dùng chung mọi khách): tài khoản theo thông tư, HKD, quy tắc thuế, mẫu in, kiểm soát, nhóm hàng.
- **`kh_aph`** (riêng khách APH-VH): đơn chung, giao hàng, bao/kg, tiền/cọc, đổi nguồn, bảo vệ giá, mẫu in, báo cáo.
- Docker, mỗi khách một VM; image `ghcr.io/tienduongmarcom/kh-aph-erpnext:<phiên bản>`; nền ERPNext ghim theo digest.

### 4.2 Quy trình phát hành (cổng bắt buộc)
Unit test → **UAT candidate** (116 ca nghiệp vụ) → **Cổng 2** site trắng → **Cổng 2b** diễn tập dựng/nâng cấp/quay lui →
**Cổng 3** nâng cấp từ đúng image production + bộ cài + quay lui có so dấu vân → chủ dự án gắn tag → phát hành image →
cửa sổ triển khai (kiểm kê, sao lưu, nâng cấp, bộ cài, kiểm, sao lưu).

### 4.3 Cờ tính năng (site_config, bật/tắt từng cái, tắt thì app hành xử như bản cũ)
`kh_aph_server_cost_guard` (chặn giá vốn ở server), `kh_aph_post_receivable_on_delivery` (nợ lúc giao + trạng thái giao),
`kh_aph_shared_sales_order` (đơn chung), `kh_aph_global_credit_warning` (hạn mức chung), `kh_aph_high_risk_credit_guard`
(duyệt rủi ro cao), `kh_aph_quantity_valuation_mvp` (bao/kg, chờ định giá, hao hụt, LCV theo kg), `kh_aph_funds_workflow`
(tiền/cọc/tuyến), `kh_aph_source_change` (đổi nguồn).

### 4.4 Ràng buộc kỹ thuật (đề xuất phải tuân theo)
- Không sửa lõi ERPNext/Frappe; tính năng mới **sau cờ**, schema cài bằng bộ cài rõ ràng, chạy lại không hỏng.
- Giao diện: **Hybrid Native** (chốt 14/10) — Workspace chuẩn điều hướng, Dialog cho thao tác ngắn, Native Frappe Page
  cho luồng tần suất cao (có A/B), chưa dùng Vue/SPA. Không DocType "Nhiệm vụ" có trạng thái riêng.
- Không tạo kho trong app. Không đưa dữ liệu thật của khách ra ngoài máy khách.
- Hóa đơn điện tử **không** tích hợp — lập trên MISA, ERP chỉ lưu tham chiếu.

---

## 5. Đối tượng dữ liệu và API của app

### 5.1 DocType riêng
APH Shared Sales Order (+ Item) · APH Source Change · APH Pending Receipt (+ Item) · APH Bag Movement ·
APH Funds Receipt · APH Funds Action · APH Funds Route · APH Credit Release (tạo bởi bộ cài).

### 5.2 Trường tùy biến chính (125 Custom Field trên production)
Sales Order/Item (đơn chung, dòng chung), Delivery Note (trạng thái/người/thời điểm giao, vượt hạn mức), các dòng hàng
(số bao, kg/bao đã lưu, giá/bao), Item (quy cách kg/bao), Purchase Receipt (phiếu chờ định giá), Landed Cost Voucher
(phân bổ theo kg), Stock Entry (loại hao hụt, lý do, kg chênh lệch), Customer (hạn mức chung, rủi ro cao, vãng lai, loại
khách thuế), Journal Entry (liên kết tiền/kế hoạch, thu hộ), cờ có/không hóa đơn và số hóa đơn MISA.

### 5.3 API (whitelisted) của app
`delivery_status.confirm` · `delivery_slip.deliveries/consolidated` · `pending_valuation.finalize` ·
`funds.create_action/identify_receipt/receipt_position/reconcile_rows/shared_financials` ·
`credit_release.approve/revoke` · `cost_query_api.get_list/get_value` (thay lời gọi chuẩn cho dòng phiếu kho) ·
`price_visibility.show_*_ledger_preview`. (API facade cho giao diện 0.12+ chưa có.)

---

## 6. Giới hạn kiểm thử đã biết (chưa được ghi PASS)

- Chưa có người dùng thật; vai trò thật (Dũng, kế toán trưởng, thủ kho) chưa cấu hình/kiểm.
- Chưa stress đồng thời đổi nguồn + giao; chưa kiểm mọi kiểu sửa đổi (amendment) chứng từ.
- Chưa có bộ đọc sao kê theo từng ngân hàng (chỉ dữ liệu chuẩn hóa).
- Chưa in máy in thật (đã kiểm PDF).
- Chưa đủ quy trình xác nhận công nợ từ xa.
- Chưa kiểm thuê ngoài, hóa đơn nhà cung cấp thật.
- Giao diện ít dùng (Desk) chưa kiểm hết.

---

## 7. Quyết định nghiệp vụ đã chốt (nguồn chuẩn — không hỏi lại)

Tài liệu đầy đủ trong repo: `docs/quyet-dinh-nghiep-vu.md` (13 quyết định), `docs/quyet-dinh-202-khoi-phuc.md`
(R001–R105 theo chủ đề + Q172–Q202), `docs/kien-truc-giao-dien.md`. Tóm tắt các nhóm:

- **Phạm vi:** site `frontend`; 4 đơn vị, TL = XB; MISA chỉ hóa đơn thuế; một danh mục khách; không giao dịch nội bộ giả (R001–R005).
- **Đơn bán & giá:** một đơn tổng hợp, dòng theo chủ kho; giao từng phần/nhiều kho/nhiều địa chỉ; đổi nguồn phần chưa giao;
  giá gợi ý + cảnh báo; giá có thể gồm VAT; không hoa hồng; giữ mã `KH…`, không giữ mã MISA cũ (R006–R014, Q172–Q182).
- **Giao & trả:** 3 trạng thái; shipper nhận = xuất + ghi nợ; xe quay về / chuyển khách khác / chuyển kho; hàng trả theo
  tình trạng; giảm giá sau giao phân bổ theo tỷ trọng; ngày ghi nhận = ngày kế toán xác nhận; một loại phiếu xuất kiêm giao;
  in có/không giá (mặc định không giá); phiếu tổng hợp/riêng, đầu phiếu trung lập; in lại kèm số hóa đơn/lượng thực nhận
  (R015–R027, Q183–Q199).
- **Tiền & công nợ:** ba con số; đúng quỹ/bank thực nhận; APH nhận APH+TL; tiền chưa rõ khách/đơn; cọc không FIFO; đối soát
  sao kê; xác nhận công nợ (chưa xác nhận chỉ cảnh báo); hạn mức chung; rủi ro cao cần duyệt; hạn thanh toán theo khách,
  gia hạn lưu lịch sử; **tiền mặt Dũng thu tại nhà máy, bàn giao từng phần** (R028–R049, Q165–Q170).
- **Kho & giá vốn:** SKU × kho × chủ; bao nguyên; MA theo kho; kiểm kê toàn kho/xoay vòng/đột xuất; đề nghị bổ sung theo
  ngưỡng; chuyển kho không đổi chủ; hàng chờ định giá; nguyên liệu nhà máy có thể dùng giá tạm rồi repost; chi phí chuyến
  theo kg; hao hụt tự nhiên/bất thường (R050–R069, Q79, Q200–Q202).
- **Sản xuất:** nhiều lệnh đan xen, nhiều thành phẩm/phụ phẩm; BOM chỉ để dự kiến, cảnh báo chênh lệch; WIP ước tính, quyết
  toán về 0; chi phí cuối tháng ước tính rồi điều chỉnh; sấy hỗ trợ VH/MK theo bao (R070–R082, Q103, Q132).
- **Dũng / nhà máy:** chỉ số lượng; không xem giá vốn mọi lối; **thấy số tiền chi phí mình chi và giá bán/tiền khách phần
  mình làm**; nhập chi phí nhỏ gộp; bán phụ phẩm (khách lẻ trả đủ); bán thành phẩm chính **theo giá HN, không sửa giá**
  (R083–R092, Q138).
- **Hóa đơn & báo cáo:** MISA lập hóa đơn, ERP lưu số/ngày/đơn vị/trạng thái/liên kết; hàng đợi hóa đơn, chống xử lý trùng;
  báo cáo quản trị theo công ty/kho/SKU/khách/đơn; lãi gộp + lãi sau chi phí trực tiếp; cộng lãi 4 đơn vị (ghi rõ không phải
  hợp nhất); dòng tiền loại chuyển nội bộ, dự kiến 7/30 ngày; lãi tạm tính; quyền theo kho/đơn vị; khóa kỳ (R093–R105, Q148, Q157, Q161).
- **Đã chốt khác:** thuế mua vào kế toán tự chọn thuế suất; hóa đơn điện tử vẫn trên MISA; khách tự tạo cây kho; ngày chốt 30/09/2026.

---

## 8. Khoảng trống đã biết (từ bảng đối chiếu `docs/doi-chieu-quyet-dinh-202.md`)

### 8.1 Chưa làm (⬜)
| Mã | Nội dung |
|---|---|
| Q178, Q180 | Một đơn giao nhiều địa chỉ; đổi địa chỉ khi đang giao, lưu lịch sử |
| Q176 | Tự cấp mã khách `KH…` (naming series) |
| Q182 | Kế toán tự hủy phần chưa giao, không cần duyệt |
| R022, Q183–Q184 | Xe quay về nhập lại kho / chuyển cho khách khác / chuyển kho khác |
| R024, Q186 | Sai lệch số lượng giao → chứng từ điều chỉnh hợp lệ (kỳ mở / kỳ đã khóa) |
| R025 | Hàng trả theo tình trạng: bán được, cách ly, hoàn tiền, bù trừ, đổi hàng |
| R026, Q169–Q170 | Giảm giá sau giao, phân bổ theo tỷ trọng dòng |
| R039 | Trạng thái "khách đã xác nhận công nợ" |
| R044–R045, Q166–Q168 | Hạn thanh toán theo khách, chung theo ngày xác nhận đơn; gia hạn có lưu ngày gốc |
| Q189–Q190 | Đánh dấu/lọc đơn quá ngày giao dự kiến |
| Q192 | Chế độ in có/không giá theo quyền (mặc định không giá) |
| Q197–Q198 | In lại kèm số hóa đơn MISA; in lại theo lượng thực nhận giữ bản gốc |
| R054–R057 | Cảnh báo chênh lệch kiểm kê lớn; thiếu/thừa chờ xử lý; đề nghị bổ sung theo ngưỡng |
| R073, R075–R076 | Cảnh báo chênh lệch BOM; kết thúc lệnh theo thực tế; WIP ước tính về 0 |
| R091, Q138 | Khóa giá bán thành phẩm chính với Dũng |
| R093–R098 | Hồ sơ hóa đơn ngoài đầy đủ (điều chỉnh/thay thế/hủy), hàng đợi hóa đơn, khóa người xử lý |
| R099–R104 | Báo cáo quản trị: lãi gộp/lãi sau chi phí trực tiếp, cộng lãi 4 đơn vị, dòng tiền 7/30 ngày, lãi tạm tính |
| R105 | Khóa kỳ kế toán |

### 8.2 Cần xác nhận / có thể mâu thuẫn (⚠️)
1. **Tiền mặt & chi phí nhỏ của Dũng** (R046–R048, R085–R087): vai trò "APH Không xem giá vốn" hiện **bị cấm toàn bộ** phiếu
   quỹ/cọc và hóa đơn mua → Dũng chưa có đường ghi tiền thu/chi tại nhà máy.
2. **Cảnh báo bán dưới giá vốn** (R011): ai được nhận? Hiện cho nhân viên bán hàng sẽ lộ ngưỡng giá vốn.
3. **Ranh giới giá tạm** (R063 vs R064): nhóm hàng nào (nguyên liệu nhà máy) được giá tạm, nhóm nào phải chờ định giá.
4. **Ngày ghi nhận** (Q187) so với hóa đơn bán lấy ngày phiếu giao.
5. **Ghi nợ khi shipper nhận** (R016) so với báo cáo theo lượng khách thực nhận.
6. Q1–Q171, Q158–Q160, Q162–Q163 thiếu nguyên văn.

### 8.3 Có code nhưng chưa có ca UAT (🟡) — cần thêm ca kiểm
R003 hóa đơn MISA, R012 giá gồm VAT, R037 đối soát sao kê theo ngân hàng, R038 đối chiếu công nợ, R040–R043 hạn mức chung,
R058–R060 yêu cầu chuyển kho, R090 khách vãng lai, Q175 không giữ mã MISA, Q181 sửa phần chưa giao, Q188, Q193–Q196 đầu phiếu
trung lập, R053 thùng/hộp, R079 chi phí cuối tháng.

---

## 9. Pháp lý chưa đối chiếu điều khoản (`docs/bang-ra-soat-phap-ly-APH-VH.md`)
| # | Nghiệp vụ | Văn bản |
|---|---|---|
| 2 | Bán không hóa đơn ở TL (thanh lý hàng không hóa đơn đầu vào) | NĐ 123/2020, NĐ 310/2025 |
| 6 | Hóa đơn bù, lập muộn, điều chỉnh, thay thế | NĐ 123/2020 Đ19, NĐ 70/2025, NĐ 310/2025 |
| 10 | Mẫu sổ HKD Minh Khang (S1a/S2/S2c) | NĐ 68/2026, TT152/2025 |
| 11 | Mức phạt từng hành vi | NĐ 310/2025 |
Ngoài ra: 3388 chi tiết cho thu hộ đang theo thông lệ; mua từ cá nhân không hóa đơn cần bảng kê Mẫu 02/TNDN (lập ngoài app).

---

## 10. Dữ liệu / quyết định khách chưa cung cấp
- Tên đầy đủ HKD Minh Khang và TL.
- Cách lấy **tồn đầu kỳ**: kiểm kê lại tại 30/09 hay số kiểm kê 01/09 cộng trừ phát sinh tháng 9; **số bao vật lý** mở đầu.
- **Ngày bắt đầu nhập liệu thật.**
- Danh sách người dùng thật và vai trò; tài khoản ngân hàng/quỹ thực nhận; tài khoản giữ hộ/phải thu nội bộ cho tuyến APH–TL.
- Cây kho, danh mục mặt hàng (ĐVT kg, quy cách kg/bao), bảng giá, khách hàng (mã `KH…`), hạn mức, khách rủi ro cao.
- Mẫu sao kê ngân hàng (ACB, MB, VietinBank, USD) để làm bộ đọc.

---

## 11. Những gì KHÔNG nằm trong phạm vi (đã quyết)
Hóa đơn điện tử trong ERP · CSKH/hoa hồng/phân công khách (Q172–Q173) · bảo dưỡng máy định kỳ (Q132) · module gia công sấy
phức tạp (R082) · truy vết từng mẻ phụ phẩm (R077) · công nhân đăng nhập ERP (R071) · cước khách trả thẳng lái xe (R027).

---

## 12. Mẫu đầu ra BA cần trả về

Một bảng duy nhất, mỗi dòng một việc thiếu/sai:

| # | Mã quyết định liên quan (R/Q/khác) | Nghiệp vụ / chức năng thiếu hoặc sai | Ai dùng | Mức (P0 chặn go-live / P1 / P2) | Bản đề xuất (0.11.1 / 0.12+ / ngoài phạm vi) | Tiêu chí nghiệm thu (đo được) | Cần khách/chủ dự án xác nhận gì |
|---|---|---|---|---|---|---|---|

Kèm theo:
1. Danh sách **câu hỏi bắt buộc** cho khách (tối đa 10, xếp theo mức chặn go-live).
2. Các **mâu thuẫn** giữa quyết định (ghi cả hai mã) — không tự chọn.
3. Đề xuất **phạm vi 0.11.1** gọn: chỉ backend/nghiệp vụ/quyền/báo cáo/mẫu in cần trước khi khách nhập giao dịch thật.
