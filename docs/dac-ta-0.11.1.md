# Đặc tả bản 0.11.1 (và phần dời sang 0.11.2)

Nguồn: đánh giá BA ngày 14/10/2026 (`docs/ba/danh-gia-BA-0.11.1.md`, gọi tắt "BA") và các quyết định anh Tiến chốt ngày 14/10
(mục 1). Mã R/Q theo `docs/quyet-dinh-202-khoi-phuc.md`. Tài liệu này có hiệu lực **thay BA** ở những chỗ hai bên khác nhau. Mọi
khác biệt đều ghi rõ ở mục 2.

## 1. Quyết định chốt 14/10/2026 (không hỏi lại)

| # | Nội dung | Chốt |
|---|---|---|
| D1 | Tài khoản chi phí sản xuất của APH (TT133 không có 621/622/627) | Mở **tài khoản chi tiết dưới 154** theo yếu tố chi phí (1548x); xưởng tách bằng trung tâm chi phí (mục 3.3). Không mở 622/627 cho APH. |
| D2 | Chi phí "Nhà máy chung" | **Ghi vào 632 hằng tháng** dưới dạng "chi phí sản xuất chung cố định không phân bổ"; không đưa vào giá thành đậu/phồng tôm, không ghi vào 642. **Chị Dung (kế toán trưởng) hoặc kiểm toán xác nhận** trước khi dùng trên sổ thật (bảng rà soát pháp lý, dòng 12). |
| D3 | Phạm vi | **0.11.1** gồm các mục P0 của BA: 1–9, 12, 16. **0.11.2** gồm các mục P1: 10, 11, 13, 14, 15. |
| BA-II.1 | Tiền mặt và chi phí nhỏ của Dũng | Phương án A: cổng riêng, chỉ phiếu mình lập, không mở giá vốn. |
| BA-II.2 | Ghi nợ khi shipper nhận | Giữ nguyên (R016). Khách nhận thiếu thì lập chứng từ điều chỉnh có phân loại R024. |
| BA-II.3 | Cảnh báo dưới giá vốn | Chỉ kế toán và Admin thấy. Người khác chỉ thấy cảnh báo "thấp hơn bảng giá". |
| BA-II.4 | Chờ định giá và giá tạm | Hàng thương mại theo R063 (chờ định giá). Nguyên vật liệu, bán thành phẩm, bao bì, vật tư nhà máy theo R064 (giá tạm > 0). |
| BA-II.6 | Dữ liệu đầu kỳ còn lệch | Không chặn cứng; đưa vào danh sách "Cần rà soát" để sửa dần. |

## 2. Chỗ đặc tả này khác BA (và lý do)

1. **622, 6272, 6274 không dùng cho APH.** TT133 không có các tài khoản này (bộ kiểm `loi_cau_truc` của lab9x đã chặn). Cách thay
   thế xem mục 3.3. Tài khoản chi tiết 642 (64211, 64214, 64221, 64224), 2141/2143 và 3319 là chi tiết doanh nghiệp tự mở,
   không trái TT133. Kế toán tự mở qua cây tài khoản; app không bắt buộc.
2. **Nhà máy chung ghi 632, không ghi chi phí kỳ (642).** TT133, TK 154, nguyên tắc 1(đ): chi phí sản xuất chung cố định không
   phân bổ thì không tính vào giá trị hàng tồn kho mà phải tính vào giá vốn hàng bán của kỳ.
3. **Trung tâm chi phí không phải căn cứ phân bổ.** App phân bổ theo **tài khoản chi tiết của xưởng** (mục 3.3), vì tài khoản đã
   có sẵn và kiểm được. Trung tâm chi phí vẫn dùng để báo cáo. App không cần Sheet 4 (5 trung tâm chi phí) để chạy.
4. **App không tạo kho bồn.** Quy tắc số 3 của AGENTS: khách tự tạo kho. App chỉ thêm ô "Kho bồn dở dang" trên Warehouse để kế
   toán đánh dấu kho bồn.
5. **Dữ liệu đầu kỳ "không giá" vẫn không nhận giá 0** (quyết định 10). Hàng chưa có giá thì nhập bằng **giá tạm > 0** có cờ
   "giá tạm", rồi hiện trong danh sách "Cần rà soát" để sửa dần. Như vậy đúng tinh thần "không chặn đứng việc" mà không tạo giá
   vốn 0.
6. **Tách "chuyển kho" và "đóng gói lại"** (BA mục 6) dùng phiếu chuẩn của ERPNext: Material Transfer cho chuyển kho, loại phiếu
   "Đóng gói theo kg" (Repack) cho đổi bao. Phần app thêm chỉ là xử lý lệch kg khi đóng gói lại: thay vì chặn, yêu cầu xác nhận
   kèm lý do (Q103: không tạo hao hụt giả).
7. **Xác nhận công nợ (R039), khóa kỳ (R105), báo cáo quản trị, hàng đợi hóa đơn MISA, trả hàng 5 tình trạng** chuyển sang
   0.11.2 theo D3.

## 3. Phạm vi 0.11.1: thiết kế

Bản 0.11.1 có bốn cờ mới, đều mặc định tắt. Hook nào cũng phải `return` ngay khi cờ tắt. Thêm cờ thì cập nhật cả
`cai_dat_tinh_nang.FLAGS`, `quay-lui.sh`, `dau_van_site.py`, `handoff_preflight.py` và Cổng 3.

| Cờ | Phạm vi |
|---|---|
| `kh_aph_factory_costing` | Giá tạm R064, hệ số phẩm cấp R078, kho bồn và vét bồn R075/R076, phân bổ chi phí cuối tháng R079/R088, lệch kg khi đóng gói lại Q103 |
| `kh_aph_factory_cash` | Phiếu quỹ nhà máy của Dũng (R046–R048, R085–R087), khóa giá bán thành phẩm chính tại nhà máy (R090, R091, Q138) |
| `kh_aph_sales_adjust` | Cảnh báo dưới giá vốn (R011), điều chỉnh giao thiếu và xe quay về (R022, R024), mã khách KH- (Q175, Q176), đóng phần chưa giao (Q181, Q182), in có giá / không giá / in lại (Q192, Q197–Q199, R053) |
| `kh_aph_data_review` | Báo cáo "Dữ liệu cần rà soát" (BA mục 16) |

### 3.1 Giá tạm cho hàng nhà máy (R064)

- **Nhóm hàng:** thêm ô `kh_aph_gia_tam` ("Cho nhập giá tạm"). Kế toán tích cho nhóm nguyên vật liệu, bán thành phẩm, bao bì,
  vật tư nhà máy. Nhóm hàng thương mại không tích và tiếp tục đi luồng chờ định giá R063.
- **Phiếu nhập mua (Purchase Receipt) và đơn mua (Purchase Order):** thêm ô `kh_aph_gia_tam` ("Giá tạm").
  - Khi tích, mọi dòng phải thuộc nhóm có `kh_aph_gia_tam` và có đơn giá > 0.
  - Dòng thuộc nhóm không cho giá tạm thì báo lỗi, hướng dẫn dùng "Chờ định giá".
  - Phiếu nhập lập từ đơn mua thì lấy cờ giá tạm của đơn mua.
- **Phiếu kho (Stock Reconciliation) đầu kỳ:** ô `kh_aph_gia_tam` cũng có trên phiếu này. Dùng cho 42 mã đang 0 đồng: nhập bằng
  giá tạm > 0, không nhập giá 0.
- **Chốt giá chính thức** dùng lối chuẩn của ERPNext:
  - Lập Purchase Invoice từ phiếu nhập với giá chính thức. App đảm bảo Buying Settings
    `set_landed_cost_based_on_purchase_invoice_rate = 1` khi cờ bật, để ERPNext tự điều chỉnh giá trị phiếu nhập và chạy lại giá
    vốn (repost).
  - Với phiếu kho đầu kỳ: kế toán lập Stock Reconciliation mới bằng giá đúng. ERPNext tự repost.
- **Danh sách giá tạm:** một mục trong báo cáo "Dữ liệu cần rà soát" (3.6). Phiếu nhập giá tạm chưa có Purchase Invoice nào đã
  ghi sổ, và phiếu kho giá tạm chưa có phiếu sau thay thế.

### 3.2 Hệ số phẩm cấp khi chia giá thành (R078), quy tắc `kg-v4`

- **Item:** thêm ô `kh_aph_he_so_gia_thanh` (mặc định 1, phải > 0).
- **Phiếu "Sản xuất theo kg" / "Đóng gói theo kg":** khi cờ bật, phiếu mới dùng quy tắc `kg-v4`.
  - Giống `kg-v3`, khác ở trọng số: mỗi dòng thành phẩm chia giá theo `kg × hệ số`.
  - Hệ số được **lưu lên dòng** (`kh_aph_he_so`) lúc lưu phiếu, sửa được trên dòng. Repost đọc hệ số đã lưu, không đọc lại Item.
  - Phụ phẩm giá cố định giữ nguyên: trừ trước, phần còn lại mới chia theo trọng số.
  - Chi phí cộng thêm trên phiếu cũng chia theo `kg × hệ số`.
- **Phiếu cũ** giữ nguyên mã quy tắc đã lưu (`kg-v1` đến `kg-v3`), kết quả không đổi.

### 3.3 Tài khoản chi phí sản xuất và phân bổ cuối tháng (R079, R088, D1, D2)

Cập nhật 14/10 sau khi nhận file "Mẫu nhập tài sản APH 31/08". Xưởng được xác định bằng **trung tâm chi phí** (Sheet 4, mỗi tài
sản và mỗi khoản CCDC đã có cột này). Tài khoản chi tiết chỉ còn theo **yếu tố chi phí**, đánh số cuối giống 627x mà chị Dung đã
duyệt (6272, 6274). Số ở đây là 1548x, vì TT133 không có 627.

**Tài khoản (lab9x, chỉ cho công ty TT133).** Chi tiết doanh nghiệp mở dưới 154. Các tài khoản đều không phải tài khoản kho, nên
ghi bút toán tay được.

| Số | Tên | Thay cho đề xuất cũ |
|---|---|---|
| 15481 | Chi phí nhân công trực tiếp sản xuất | 622 |
| 15482 | Chi phí vật liệu, công cụ dụng cụ sản xuất | 6272 |
| 15484 | Chi phí khấu hao TSCĐ sản xuất | 6274 |
| 15487 | Chi phí dịch vụ mua ngoài sản xuất (điện, nước…) | 6277 |
| 15488 | Chi phí sản xuất bằng tiền khác, hao hụt tự nhiên | 6278 |
| 6323 | Chi phí sản xuất chung cố định không phân bổ (chi tiết 632) | |

15411 và 15421 (dở dang, tài khoản kho) giữ nguyên. Công ty TT99 không nhận các tài khoản này, vì TT99 đã có 621/622/627.

**Cài đặt `APH Cài đặt giá thành`** (Single, kế toán trưởng đặt):
- Công ty.
- Bảng xưởng: trung tâm chi phí và tên hiển thị. Ví dụ "Xưởng sơ chế đậu", "Xưởng phồng tôm".
- Trung tâm chi phí "Nhà máy chung".
- Danh sách tài khoản yếu tố. Mặc định là 15481, 15482, 15484, 15487, 15488.

Khách tự tạo trung tâm chi phí theo Sheet 4; app không tạo.

**Ghi nhận trong tháng (kế toán làm, app không tự ghi):**
- Mọi bút toán chi phí sản xuất ghi Nợ 1548x, **kèm trung tâm chi phí** của xưởng hoặc của nhà máy chung.
- Khấu hao: nhóm tài sản sản xuất dùng tài khoản chi phí khấu hao 15484. Trung tâm chi phí trên thẻ tài sản quyết định xưởng.
- CCDC 242: bút toán phân bổ Nợ 15482 kèm trung tâm chi phí, theo Sheet 7.

**Phiếu sản xuất:** thêm ô `kh_aph_xuong` (Link Cost Center, phải nằm trong bảng xưởng). Phiếu theo quy tắc kg-v4 bắt buộc có ô
này. Khi lưu, app gán trung tâm chi phí đó cho các dòng thành phẩm.

**Công cụ "Phân bổ chi phí sản xuất cuối tháng"** (`kh_aph.factory_costing.phan_bo_thang`, chỉ kế toán):
1. Với từng xưởng: lấy số dư đến cuối tháng của từng tài khoản 1548x theo trung tâm chi phí của xưởng đó.
2. Tạo **Landed Cost Voucher nháp** (lối chuẩn ERPNext, có hỗ trợ Stock Entry):
   - Phiếu nhận chi phí: các phiếu sản xuất kg-v4 của xưởng trong tháng.
   - Dòng nhận chi phí: các dòng thành phẩm chia giá (không gồm phụ phẩm giá cố định), chia theo `kg × hệ số` đã lưu.
   - Dòng chi phí: mỗi tài khoản một dòng.
3. Kế toán xem lại rồi tự ghi sổ. ERPNext ghi Nợ kho thành phẩm, Có 1548x theo trung tâm chi phí của xưởng, rồi repost giá vốn.
4. **Nhà máy chung (D2):** tạo **bút toán nháp** Nợ 6323, Có từng tài khoản 1548x, bằng số dư theo trung tâm chi phí "Nhà máy
   chung". Diễn giải "CPSXC cố định không phân bổ". Kế toán duyệt rồi ghi sổ.
5. Xưởng có chi phí mà trong tháng không có phiếu sản xuất: không phân bổ, báo cho kế toán. Số dư để lại tháng sau.
6. Chạy lại trong cùng tháng không tạo trùng: nếu đã có chứng từ nháp hoặc đã ghi sổ của cùng tháng và xưởng thì trả chứng từ đó.
7. R079 (ước tính rồi điều chỉnh): chi phí ghi bổ sung sau làm số dư tháng sau thay đổi, phần chênh được phân bổ ở lần chạy tháng
   đó. Điều chỉnh lùi tháng cũ thì kế toán tự lập Landed Cost Voucher.

### 3.4 Kho bồn dở dang và vét bồn (R075, R076, R068)

- **Warehouse:** thêm ô `kh_aph_kho_bon` ("Kho bồn dở dang"). Kế toán tự tạo kho bồn (Bồn hạt + xay, Bồn bóc vỏ) và gắn tài
  khoản kho (15411 hoặc chi tiết).
- **Vận hành:**
  - Đưa nguyên liệu vào bồn bằng chuyển kho (Material Transfer), bồn là kho đích.
  - Phiếu sản xuất lấy đầu vào từ kho bồn.
  - Điều chỉnh tồn bồn dần dần bằng Stock Reconciliation chuẩn (có cờ giá tạm nếu cần).
- **Thao tác "Quyết toán vét bồn"** (`kh_aph.factory_costing.vet_bon`, chỉ kế toán):
  - Đầu vào: kho bồn, ngày, loại hao hụt cho phần còn trên sổ ("Hao hụt tự nhiên" hoặc "Hao hụt bất thường"), lý do.
  - Tạo **phiếu xuất kho nháp** (Material Issue) toàn bộ lượng còn trên sổ của bồn, theo từng mã.
  - Tài khoản đối ứng:
    - Hao hụt tự nhiên: **15488 kèm trung tâm chi phí của xưởng**, để lần phân bổ cuối tháng đưa vào giá thành thành phẩm (R068:
      hao hụt tự nhiên nằm trong giá trị hàng còn lại).
    - Hao hụt bất thường: **6322** "Tổn thất hàng tồn kho ghi nhận vào giá vốn".
  - Phiếu lưu loại hao hụt, lý do, người làm và thời điểm.
  - Ghi sổ xong thì bồn về 0.
- **Báo cáo tồn bồn:** báo cáo "Tồn kho số lượng" có sẵn lọc theo kho bồn. Không thêm báo cáo mới.

### 3.5 Đóng gói lại lệch kg (Q103, R080)

Với phiếu "Đóng gói theo kg" (mục đích Repack) khi cờ `kh_aph_factory_costing` bật:
- Kg đầu ra phải bằng kg đầu vào (sai số 0,001 kg).
- Nếu lệch: không ghi hao hụt. Phiếu chỉ lưu được khi người lập tích `kh_aph_xac_nhan_lech_kg` và ghi lý do. Bản thân phiếu
  không đổi cách chia giá.
- Phiếu "Sản xuất theo kg" giữ quy tắc hao hụt hiện có.

### 3.6 Báo cáo "Dữ liệu cần rà soát" (BA mục 16, cờ `kh_aph_data_review`)

Báo cáo dạng Script Report, chỉ kế toán (Accounts User / Accounts Manager / System Manager) xem được. Dũng **không** xem được,
vì báo cáo có giá trị.

| Mã | Nội dung |
|---|---|
| (a) | Tài sản (Asset) có một trong các dấu hiệu sau. Ví dụ từ Sheet 5: dòng 1 Máy cắt phồng tôm, dòng 30 xe nâng, dòng 37 máy sấy 150KW, dòng 18 máy phồng tôm |
| (a1) | Hao mòn lũy kế đầu kỳ ≥ nguyên giá mà vẫn còn kỳ khấu hao |
| (a2) | Hao mòn lũy kế > nguyên giá |
| (a3) | Khấu hao tháng dự kiến lớn gấp hơn 3 lần mức đường thẳng (nguyên giá / tổng số tháng) |
| (a4) | Trung tâm chi phí khác vị trí. Ví dụ tài sản ở "Xưởng phồng tôm" nhưng trung tâm chi phí là "Xưởng sơ chế đậu" |
| (a5) | Tài khoản chi phí khấu hao của nhóm tài sản không hợp với trung tâm chi phí. Ví dụ tài sản của xưởng hoặc nhà máy chung mà nhóm tài sản ghi vào 642x |
| (b) | Phiếu nhập hoặc phiếu kho giá tạm chưa chốt (3.1) |
| (c) | Tồn kho theo kho và mã có số lượng 0 mà giá trị khác 0, hoặc số lượng âm |
| (d) | Mã hàng nằm ở kho có tài khoản kho khác tài khoản kho của nhóm hàng cấp 1 (ví dụ thành phẩm 155x nằm ở kho nguyên liệu 152x) |
| (e) | Bồn dở dang còn tồn quá 31 ngày chưa vét |

Báo cáo không sửa dữ liệu. Mỗi dòng có liên kết tới chứng từ để sửa.

### 3.7 Phiếu quỹ nhà máy của Dũng (R046–R048, R085–R087)

- **DocType mới `APH Phiếu quỹ nhà máy`** (submittable):
  - Loại phiếu: "Thu tiền khách", "Chi phí nhỏ", "Bàn giao tiền".
  - Các ô: ngày, công ty, khách (khi thu tiền khách), bảng dòng (diễn giải, khoản mục, số tiền), người nhận (khi bàn giao),
    trạng thái xác nhận.
- **Cài đặt `APH Cài đặt quỹ nhà máy`** (Single, kế toán trưởng đặt):
  - Công ty, quỹ tiền mặt nhà máy (tài khoản tiền chi tiết, ví dụ 11111, do kế toán mở).
  - Trung tâm chi phí nhà máy.
  - Bảng khoản mục: tên khoản mục và tài khoản chi phí, ví dụ "Bốc xếp" ứng với 15488.
  - Tài khoản tiền nhận bàn giao.
- **Ghi sổ** bằng Journal Entry do server tạo:
  - Thu tiền khách: Nợ quỹ nhà máy, Có 131 theo khách. Không cấn hóa đơn (quyết định 5).
  - Chi phí nhỏ: Nợ tài khoản theo khoản mục, Có quỹ nhà máy. Được nhập gộp nhiều dòng (R086, R087), không bắt buộc chứng từ đính
    kèm.
  - Bàn giao tiền: khi Dũng gửi, phiếu ở trạng thái "Chờ nhận". Người nhận (kế toán) xác nhận số thực nhận thì mới tạo bút toán
    Nợ tài khoản nhận, Có quỹ nhà máy theo **số thực nhận**. Phần chênh ghi "Chờ điều tra", không tự quy trách nhiệm (R048).
    Nhận từng phần được.
- **Quyền:**
  - Vai trò "Kế toán nhà máy" tạo, gửi và xem **chỉ phiếu mình lập** (if_owner).
  - Kế toán xem tất cả.
  - Dũng không được mở Journal Entry hay GL. Phiếu chỉ hiện số tiền do chính Dũng lập (R085).
  - `dung_cost_policy` cho phép đúng DocType này trong lối danh sách (reportview) và vẫn chặn mọi thứ khác như cũ.

### 3.8 Khóa giá bán thành phẩm chính tại nhà máy (R090, R091, Q138)

- **Nhóm hàng:** thêm ô `kh_aph_khoa_gia_nha_may` ("Thành phẩm chính: giá Hà Nội chốt").
- Người dùng có vai trò "Kế toán nhà máy" hoặc "APH Không xem giá vốn", và không có vai trò kế toán, lập Sales Order, Sales
  Invoice, Delivery Note hoặc đơn bán chung:
  - Dòng thuộc nhóm khóa giá: `rate` phải bằng `price_list_rate` của bảng giá trên chứng từ. Server kiểm, không tin trình duyệt.
  - Dòng thuộc nhóm khác (phụ phẩm, R090): được nhập giá bán thực tế.

### 3.9 Cảnh báo dưới giá vốn chỉ cho kế toán (R011, R084)

Khi lưu Sales Order hoặc đơn bán chung:
- Người có vai trò kế toán (Accounts User / Accounts Manager / System Manager / Administrator) nhận thêm cảnh báo "dòng X: giá
  bán thấp hơn giá vốn bình quân hiện tại". Giá vốn bình quân đọc từ Bin theo mã và kho của dòng. Chỉ là cảnh báo, không chặn.
- Người khác không nhận bất kỳ thông báo, cờ hay trường nào liên quan đến giá vốn.
- Cảnh báo "thấp hơn bảng giá" hiện có giữ nguyên cho mọi người.

### 3.10 Giao thiếu, xe quay về, chuyển khách (R016, R022, R024)

- **Delivery Note trả lại và Sales Invoice trả lại / giảm:** thêm ô `kh_aph_loai_dieu_chinh` (Chọn). Chứng từ trả lại hoặc giảm
  phải chọn một loại khi cờ bật.
  - "Khách trả hàng (R025)"
  - "Giao thiếu - hàng chở về kho (R022/R024)": trả lại theo **lượng thực chở về**, nhập lại kho, bảo toàn bao và kg qua
    `bag_stock`.
  - "Giao thiếu - mất trên đường (R024)": Sales Invoice giảm, không nhập kho.
  - "Sửa sai số lượng (R024)": dùng khi nhập nhầm số lượng.
- **Thao tác "Xe quay về"** trên phiếu giao đang ở trạng thái "Đang giao": tạo Delivery Note trả lại **nháp** với loại "Giao thiếu
  - hàng chở về kho". Người dùng nhập lượng thực chở về.
- **Thao tác "Chuyển sang khách khác"** (R022): tạo phiếu trả lại nháp như trên, kèm phiếu giao nháp mới cho khách mới từ đơn của
  khách mới (người dùng chọn đơn). Không có phiếu nào tự ghi sổ.
- Ghi nợ lúc shipper nhận giữ nguyên (R016, cờ `kh_aph_post_receivable_on_delivery`).

### 3.11 Mã khách KH- và đóng phần chưa giao (Q175, Q176, Q181, Q182)

- **Mã khách:** khi cờ bật, bộ cài đặt Selling Settings `cust_master_name = "Naming Series"`, và Customer `naming_series` có
  `KH-.#####` làm mặc định. App không thêm trường mã MISA cũ.
- **Đơn bán chung:** thao tác "Đóng phần chưa giao" (kế toán bán hàng, Accounts User):
  - Đóng các Sales Order con bằng trạng thái Closed chuẩn của ERPNext. Phần đã giao, công nợ, cọc giữ nguyên.
  - Lưu người, thời điểm, lý do trên đơn chung.
  - Không cần phê duyệt (Q182).
  - Mở lại theo lối chuẩn: Sales Order "Re-open".

### 3.12 In có giá / không giá và in lại (Q192, Q197–Q199, R053)

- **Mẫu in phiếu giao hàng và biên bản giao nhận:**
  - Mặc định **không giá**.
  - Bản có giá là mẫu in riêng "… (có giá)". Mẫu này chỉ in được khi người in có vai trò kế toán hoặc "Sales Manager". Kiểm
    trong `before_print`, áp cho mọi lối in.
- **In lại kèm số hóa đơn MISA (Q197):** mẫu in đọc số hóa đơn MISA đã lưu trên Sales Invoice, nếu có.
- **In theo lượng thực nhận (Q198):** mẫu "Phiếu giao (lượng thực nhận)" lấy lượng giao trừ các phiếu trả lại loại "Giao thiếu".
  Mẫu chỉ in, không tạo chứng từ.
- **Đơn vị tính (R053, Q199):** hàng có bao thì in "bao + kg". Hàng theo thùng hoặc hộp in đơn vị tính bán của dòng (UOM) và quy
  đổi.

## 4. Kiểm thử

**Unit test thuần cho phần tính toán:**
- Trọng số `kg × hệ số`, chia có phụ phẩm cố định.
- Tính số dư cần phân bổ, tính số tiền vét bồn.
- Khóa giá, ai được xem cảnh báo giá vốn.
- Phân loại điều chỉnh, kiểm lệch kg khi đóng gói lại.
- Quyền phiếu quỹ.

**Ca UAT HTTP trên CI** (thêm vào bộ chạy hiện có, cập nhật số ca PASS kỳ vọng):
- Phiếu SX kg-v4 với hệ số 1,0 và 1,4. Kiểm số chia đúng, và repost không đổi.
- Phân bổ cuối tháng:
  - Landed Cost Voucher nháp đúng số tiền theo trọng số.
  - Ghi sổ xong thì giá thành phẩm tăng đúng.
  - Chi phí trung tâm "Nhà máy chung" không vào LCV; JE 6323 có số đúng.
- Vét bồn tự nhiên và bất thường: tài khoản đúng, bồn về 0.
- Giá tạm:
  - Nhóm không cho giá tạm thì bị chặn.
  - Lập Purchase Invoice giá khác thì giá trị phiếu nhập đổi.
- Dũng:
  - Lập chi phí nhỏ và bàn giao: chỉ thấy phiếu của mình; người khác không xem được.
  - Mọi lối giá vốn vẫn 403.
  - Không sửa được giá thành phẩm chính; sửa được giá phụ phẩm.
- Cảnh báo giá vốn: kế toán thấy, nhân viên bán hàng không thấy chữ "giá vốn" trong phản hồi.
- Xe quay về: trả lại nháp, ghi sổ xong thì kho, bao và kg về đúng. Công nợ giảm theo hóa đơn điều chỉnh.
- Đóng phần chưa giao: Sales Order chuyển Closed, phần đã giao giữ nguyên.
- In: người không quyền in mẫu có giá thì 403; mẫu không giá không chứa giá.
- Báo cáo rà soát: dữ liệu giả có đủ năm loại (a)–(e) thì ra đủ dòng; Dũng bị 403.

**Cổng 3:** nâng cấp từ image production 0.11.0 lên bản ứng viên, chạy bộ cài với các cờ mới, rồi quay lui.

## 5. Dời sang 0.11.2 (D3)

| BA mục | Nội dung |
|---|---|
| 10 | Trả hàng 5 tình trạng, kho cách ly (R025); giảm giá sau giao phân bổ theo tỷ trọng dòng (R026, Q169–Q170) |
| 11 | Hạn thanh toán chung và lịch sử gia hạn (R044, R045, Q166–Q168); giao nhiều địa chỉ, đổi địa chỉ khi đang giao (Q178, Q180); lọc đơn quá hạn giao (Q189, Q190) |
| 13 | Cảnh báo lệch BOM (R073); kiểm kê trong lúc giao dịch, hàng thiếu/thừa chờ xử lý (R054–R056). R057 sang 0.12+ |
| 14 | Hồ sơ hóa đơn MISA gốc / điều chỉnh / thay thế / hủy và hàng đợi chống trùng (R093–R098, Q148) |
| 15 | Báo cáo quản trị lãi gộp, cộng ngang 4 đơn vị, lãi tạm tính, dòng tiền 7/30 ngày (R099–R104); xác nhận công nợ (R039); khóa kỳ (R105) |

## 6. Dữ liệu khách cần trước khi nghiệm thu (không chặn việc viết code)

1. ~~File mẫu tài sản 31/08~~: đã nhận 14/10. Sheet 1 dòng 6 (6272/6274) đổi thành 15482/15484 theo D1. Sheet 7 có khoản CCDC ghi 811 và 632 cần chị Dung xem lại. Hướng dẫn "khấu hao không cộng vào giá thành" ở sheet "Đọc trước" **hết hiệu lực** (thay bằng 3.3).
2. Cây nhóm hàng thật: nhóm nào tích "Cho nhập giá tạm", nhóm nào tích "Thành phẩm chính: giá Hà Nội chốt".
3. Hệ số phẩm cấp từng thành phẩm đậu. Ví dụ BA: 24.000 đ/kg đến 35.000 đ/kg, tức hệ số khoảng 0,69–1,0.
4. Danh sách khoản mục chi phí nhỏ của nhà máy và tài khoản tương ứng.
5. Tài khoản người dùng thật của chị Dung và Dũng.
6. Chị Dung xác nhận D2 (6323) trước khi ghi sổ thật.
