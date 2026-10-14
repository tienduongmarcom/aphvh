# Đặc tả bản 0.11.2 — cây kho chuẩn, dở dang theo dây chuyền, đóng gói 2 công đoạn

Ngày 14/10/2026.
Nguồn:
- Trao đổi với anh Tiến chiều 14/10.
- File "ĐỊNH MỨC PHÒNG TÔM" năm 2026, có chữ ký anh Nguyễn Tiến Hùng và giám đốc Nguyễn Phi Ninh.
- Các quyết định R054–R057, R060, R068, R073–R082 trong `docs/quyet-dinh-202-khoi-phuc.md`.

## 1. Quyết định chốt 14/10/2026 (không hỏi lại)

| # | Nội dung | Chốt |
|---|---|---|
| K1 | Ai tạo cây kho | **App tạo cây kho chuẩn**, đúng thông tư, dễ vận hành; kế toán (chị Dung) làm theo. Bỏ quy tắc số 3 cũ "app không tạo kho", thay bằng quy tắc mới ở mục 2.3. |
| K2 | Kho bồn | Bỏ "kho bồn" theo từng bồn. **Mỗi dây chuyền có một kho dở dang**: đậu một kho, phồng tôm một kho. |
| K3 | Quyết toán dở dang | **Cả hai dây chuyền** quyết toán dở dang về 0 khi dừng chuyền (R076). Khác nhau: phồng tôm **có định mức**, nên hệ thống tự chia hao hụt trong định mức và vượt định mức. |
| K4 | Đóng gói | **Hai công đoạn.** Công đoạn 1, sản xuất: ra bán thành phẩm cân thực tế hàng ngày. Công đoạn 2, đóng gói: đóng thành phẩm hoặc chia nhỏ hàng thương mại. |
| K5 | Số liệu thực tế (sản lượng mẻ, kg tịnh, định mức, hệ số…) | **Nhân viên tự nhập qua Trung tâm dữ liệu** (0.12.0): có ô nhập, quy tắc kiểm và người duyệt. Không hỏi qua lại số liệu. Trước khi có 0.12.0 thì nhập trên form chuẩn (BOM, Item). |
| K6 | Lộ trình | 0.11.2 (bản này) → **0.11.3**: các mục P1 bán hàng / hóa đơn / báo cáo dời từ 0.11.1 → **0.12.0**: Trung tâm dữ liệu (danh mục và định mức) → **0.12.1**: dữ liệu tài chính đầu kỳ → **0.13.0**: giao diện Kho. |

## 2. Cây kho chuẩn (app tạo)

### 2.1 Nguyên tắc

1. **Kho cho biết hàng nằm ở đâu và thuộc pháp nhân nào.** Tài khoản 152/153/154/155/156 vẫn lấy theo **nhóm hàng**, đã bật tồn kho theo mặt hàng, như quyết định 27/09 và 03/10. Kho không quyết định tài khoản.
2. **Chỉ tách thành kho riêng** khi hàng được kiểm kê riêng, có người chịu trách nhiệm riêng, và phải tách khỏi lượng có thể bán.
3. Mỗi tình trạng đặc biệt (dở dang, chờ đóng gói, chờ xử lý, cách ly) **chỉ có một kho cho mỗi địa điểm**.
4. **Giữa các pháp nhân không dùng phiếu chuyển kho** (R060): bên giao lập hóa đơn bán, bên nhận lập hóa đơn mua. Chuyển kho trong cùng một pháp nhân đi qua "Hàng đang vận chuyển".

### 2.2 Cây chuẩn

Tên kho có hậu tố viết tắt của pháp nhân, theo cách ERPNext đặt tên.

```
<Pháp nhân> (nhóm gốc)
├── Nhà máy Phú Thọ (nhóm)                         [chỉ APH; VH/MK chỉ có kho Gửi]
│   ├── Kho nguyên liệu                    loại: Nguyên liệu
│   ├── Kho vật tư - bao bì - phụ tùng     loại: Nguyên liệu
│   ├── Dở dang dây chuyền đậu             loại: Dở dang dây chuyền   (dây chuyền: Đậu)
│   ├── Dở dang dây chuyền phồng tôm       loại: Dở dang dây chuyền   (dây chuyền: Phồng tôm)
│   ├── Kho chờ đóng gói                   loại: Chờ đóng gói
│   └── Kho thành phẩm nhà máy             loại: Thành phẩm
│   (VH, MK: "Gửi tại nhà máy Phú Thọ"    loại: Gửi — hàng của VH/MK sấy hoặc chia nhỏ tại nhà máy, R082)
├── Hà Nội (nhóm)
│   ├── Kho bán hàng Hà Nội                loại: Bán hàng
│   └── <các kho vệ tinh khai trong khach.json>   loại: Bán hàng
├── Đà Nẵng (nhóm) → Kho Đà Nẵng           loại: Bán hàng
├── Hồ Chí Minh (nhóm) → Kho Hồ Chí Minh   loại: Bán hàng
└── Hàng đang vận chuyển                   loại: Vận chuyển (warehouse_type Transit, đặt làm kho vận chuyển mặc định)
```

**Không tạo sẵn** các kho "Chờ xử lý" và "Cách ly". Thao tác trả hàng hoặc kiểm kê sẽ tạo đúng một kho cho mỗi địa điểm khi lần đầu cần dùng.

### 2.3 Quy tắc mới thay quy tắc số 3 (AGENTS.md)

- Cây kho khai trong `khach.json`, mục mới `dia_diem`, gồm: địa điểm nào có ở pháp nhân nào, và danh sách kho vệ tinh.
  - Các khóa cũ `nha_may`, `kho_them`, `ten_nha_may` vẫn báo lỗi.
  - Không ghi tên kho tùy ý: tên kho do app sinh theo cây chuẩn.
- Bộ dựng chạy lại nhiều lần không hỏng, theo các ràng buộc sau:
  - Chỉ **thêm** kho còn thiếu.
  - **Không đổi tên** kho đã có (ERPNext v16 không cho đổi tên kho).
  - **Không xóa** kho.
  - **Không đổi** pháp nhân hoặc loại của kho đã có tồn.
  - Kho cũ ngoài cây chuẩn thì **chỉ báo**, không tự tắt.
- Production chưa có dữ liệu: chạy bộ dựng xong thì `kiem_trien_khai` kiểm có đủ cây.

### 2.4 Ô "Loại kho" (thay "Kho bồn dở dang" của 0.11.1)

- **Ô `kh_aph_loai_kho` (Select)**, các giá trị: Bán hàng / Nguyên liệu / Thành phẩm / Dở dang dây chuyền / Chờ đóng gói / Chờ xử lý / Cách ly / Gửi / Vận chuyển.
- **Ô `kh_aph_day_chuyen` (Select)**: Đậu / Phồng tôm. Bắt buộc khi loại kho là Dở dang dây chuyền.
- **Lượng có thể bán** không tính các kho loại Dở dang, Chờ đóng gói, Chờ xử lý, Cách ly, Gửi. Đơn bán và đơn bán chung chọn các kho này thì bị chặn.
- **Bỏ ô `kh_aph_kho_bon`.** Production chưa có dữ liệu (đã kiểm 14/10), nên chỉ cần thủ tục gỡ ô trong bộ cài, không phải chuyển dữ liệu.

## 3. Dở dang dây chuyền và quyết toán về 0 (R075, R076, R068, R073)

Nút **"Quyết toán dở dang về 0"** nằm trên kho loại Dở dang dây chuyền. Nút tạo phiếu xuất **nháp**: toàn bộ lượng còn trên sổ của kho dở dang.

| | Đậu | Phồng tôm |
|---|---|---|
| Kỳ quyết toán | Từ lần quyết toán trước đến lần dừng chuyền này | Như đậu |
| Phân loại lượng còn trên sổ | Kế toán chọn tự nhiên hay bất thường, ghi lý do (như 0.11.1) | **Tự tính theo định mức công đoạn 1**: lượng lẽ ra phải dùng = sản lượng bán thành phẩm trong kỳ quy ra số mẻ × định mức mỗi mẻ |
| Phần trong định mức (cộng tỷ lệ hao hụt cho phép) | — | Hao hụt tự nhiên: 15488 theo trung tâm chi phí của xưởng, vào giá thành |
| Phần vượt định mức | — | Hao hụt bất thường: 6322, bắt buộc lý do |
| Dùng ít hơn định mức | — | Không ghi thêm; báo kế toán xem (có thể cấp thiếu hoặc cân sai) |

**Căn cứ pháp lý:** TT133, TK 154, nguyên tắc 1(đ): chi phí nguyên vật liệu vượt mức bình thường không tính vào giá thành. Định mức có chữ ký giám đốc là "mức bình thường".

**Cảnh báo lệch định mức khi cấp liệu (R073):** chỉ cảnh báo, không chặn, kèm số lệch theo từng nguyên liệu.

**Báo cáo "Tiêu hao so với định mức":** theo dây chuyền và kỳ quyết toán.

## 4. Đóng gói hai công đoạn

```
Nguyên liệu ─cấp liệu─▶ Dở dang dây chuyền ─(CĐ1) sản xuất, cân hàng ngày─▶ Chờ đóng gói ─(CĐ2) đóng gói─▶ Thành phẩm
Hàng thương mại xá ─chuyển kho─────────────────────────────────────────────▶ Chờ đóng gói ─(CĐ2) chia nhỏ─▶ Hàng hóa gói nhỏ
```

| Công đoạn | Loại phiếu | Đầu vào | Đầu ra | Định mức (BOM) |
|---|---|---|---|---|
| CĐ1 Sản xuất | "Sản xuất theo kg" (kg-v4, bắt buộc chọn xưởng) | Nguyên liệu từ kho dở dang | Bán thành phẩm cân thực tế (kg) vào kho Chờ đóng gói, kèm phụ phẩm (ví dụ bánh vụn) | **Một bảng cho mỗi loại bột hoặc loại hàng**, tính theo mẻ (ví dụ 160 kg bột ra x kg bánh khô) |
| CĐ2a Đóng gói thành phẩm | **"Đóng gói thành phẩm"** (mới, mục đích Repack) | Bán thành phẩm (kg) + bao bì | Thành phẩm theo quy cách (thùng / bao / gói) vào kho thành phẩm | **Một bảng cho mỗi quy cách**, tính cho 1 thùng (ví dụ 18 kg bánh + túi + 1 vỏ thùng…) |
| CĐ2b Chia nhỏ hàng thương mại | Cùng loại "Đóng gói thành phẩm" | Hàng xá + bao bì | Hàng hóa gói nhỏ | Một bảng cho mỗi quy cách gói |

**Quy tắc chung cho hai công đoạn:**

- **Nhóm hàng có thêm ô "Bao bì đóng gói" (`kh_aph_bao_bi`).** Dòng thuộc nhóm này **chỉ cộng tiền, không cộng kg**.
- **Cân đối kg** chỉ tính giữa hàng chính đầu vào và (hàng chính đầu ra theo kg tịnh + phụ phẩm). Kg tịnh của thành phẩm lấy từ ô trọng lượng tịnh trên mã hàng.
  - Lệch thì phải xác nhận kèm lý do (Q103), không ghi hao hụt giả.
  - **Sửa lỗi 0.11.1:** loại phiếu "Đổi bao, đóng gói lại" đang cộng cả kg túi PP vào cân đối.
- **Giá:**
  - Chi phí sản xuất cuối tháng phân bổ vào đầu ra CĐ1 (công cụ 0.11.1, giữ nguyên).
  - CĐ2 cộng giá bao bì vào giá thành phẩm. Chia nhỏ hàng thương mại thì cộng vào giá gốc hàng hóa (chi phí trực tiếp trước khi bán).
  - Giá vốn bình quân và repost do ERPNext tự lo.
- **Hàng của VH hoặc MK** đóng gói tại nhà máy:
  - Ghi trên sổ của **chủ hàng**, kho "Gửi tại nhà máy Phú Thọ" của pháp nhân đó.
  - Chỉ theo dõi số lượng, giống sấy hỗ trợ R082. Tiền công đóng gói để sau, khi chị Dung muốn tính.
- **Kiểm tiêu hao bao bì:** bao bì không có dở dang. Vượt định mức CĐ2 thì cảnh báo; chênh lệch thực tế xử lý bằng kiểm kê kho bao bì như bình thường.

## 5. Số liệu do nhân viên nhập (K5)

Trước 0.12.0 các số liệu này nhập trên form chuẩn. Từ 0.12.0 nhập theo lô qua Trung tâm dữ liệu.

| Số liệu | Nằm ở | Người nhập | Người duyệt | Kiểm |
|---|---|---|---|---|
| Sản lượng bán thành phẩm mỗi mẻ (kg) | BOM CĐ1 (số lượng thành phẩm của BOM) | Dũng / anh Hùng | Chị Dung | lớn hơn 0. Từ 0.12.0 thêm cảnh báo khi lệch quá 20% so với thực tế |
| Kg tịnh mỗi thùng, gram mỗi gói | Item: trọng lượng tịnh và quy đổi ĐVT | Dũng | Chị Dung | kg tịnh = số gói × gram mỗi gói |
| Bao bì mỗi quy cách | BOM CĐ2 | Dũng | Chị Dung | mã thuộc nhóm "Bao bì đóng gói" |
| Mã bao bì riêng theo quy cách | Item | Dũng | Chị Dung | một mã không mang hai quy cách (báo cáo rà soát kiểm: cùng mã xuất hiện ở hai BOM với hai mô tả khác nhau) |
| Tỷ lệ hao hụt cho phép | BOM, ô `kh_aph_hao_hut_cho_phep` (%) | Anh Hùng | Chị Dung | ≥ 0. **Mặc định 0**: đúng định mức là mức bình thường |
| Bản định mức hiệu lực | BOM: is_default và ngày hiệu lực | Anh Hùng | Giám đốc / chị Dung | mỗi thời điểm có đúng một bản mặc định cho mỗi mã |

Khi nhập phải sửa các lỗi trong file định mức hiện tại. Các lỗi này sẽ đưa vào danh sách rà soát:
- sheet "250 gói" ghi nhầm tên thành 100 gói;
- `VT.TUI43`, `VT.TUI48` và `VT.THUNG40` mỗi mã mang nhiều quy cách;
- bánh rau củ có hai cột định mức lệch nhau (titanium 0,07/0,08; chất tẩy 0,16/0,15);
- "Cao cấp 2025" chưa đủ: chưa có mã, phụ gia, túi và vỏ thùng bằng 0.

## 6. Kiểm kê có mốc thời gian và hàng thiếu/thừa chờ xử lý (R054–R056)

Chuyển từ 0.11.1 sang đây vì gắn với cây kho:

- **Kiểm kê có mốc thời gian (R054):** dùng Stock Reconciliation có ngày giờ. Giao dịch sau mốc không bị chặn.
- **Chênh lệch lớn (R055):** ngưỡng % do nhân viên nhập. Vượt ngưỡng thì cảnh báo, bắt buộc lý do, lưu nhật ký.
- **Thiếu chờ xử lý (R056):** chuyển ngay sang kho **Chờ xử lý** của địa điểm, nên lượng có thể bán giảm ngay. Hạch toán hai bước theo quyết định 05/10:
  1. Theo biên bản kiểm kê: thừa ghi Nợ 152/153/155/156, Có 3381; thiếu ghi Nợ 1381, Có 152/153/155/156.
  2. Bước xử lý **chờ chị Dung chốt tài khoản**.
- **Thừa chưa xác nhận (R056):** nhập vào kho Chờ xử lý, chưa bán được cho tới khi xác nhận.

## 7. Lệch Property Setter (220 production / 216 CI) — đã tìm ra, không phải lỗi app

Kết quả liệt kê trên production, chạy lệnh chỉ đọc lúc 15:20 ngày 14/10:
- **4 Property Setter `Company.*.in_list_view`** (default_currency, country, is_group, enable_perpetual_inventory) tạo lúc **12:47:49**.
  - Thời điểm này giữa hai lần triển khai: 0.11.0 lúc 10:58, 0.11.1 lúc 14:43.
  - Đây là dấu vết của thao tác **chỉnh cột danh sách Company trên giao diện** (List View Settings), không phải do bộ cài.
- Phần còn lại trùng với bộ cài 0.11.1 và CI:
  - Selling Settings sinh: `naming_series` hidden/reqd, `tax_id` ×6, Packed Item rate, discount account ×4.
  - Bộ cài tạo lại các permlevel cũ (ngày tạo mới, số lượng không đổi).
  - Customer `naming_series` options/default.

**Xử lý:**
- Không sửa app.
- Bổ sung vào dấu vân một mục **"tùy chỉnh giao diện của người dùng"**, tách riêng các Property Setter `in_list_view` / `columns` khỏi phần schema của app. Như vậy so sánh production với CI chỉ báo lệch thật.

## 8. Cờ, cài đặt, kiểm thử

- **Cờ mới `kh_aph_kho_chuan`:** cây kho, loại kho, dở dang theo dây chuyền, đóng gói 2 công đoạn, kiểm kê có mốc.
  - Cập nhật FLAGS, `quay-lui.sh`, `dau_van_site.py`, `handoff_preflight.py`, Cổng 3 (lên 13 cờ).
- **Quyết toán theo định mức** nằm trong cờ `kh_aph_factory_costing` sẵn có.
- **Ca HTTP mới (bộ `b0112`), dữ liệu giả:**
  - Dựng cây kho hai lần không trùng; kho cũ ngoài cây chỉ báo.
  - Đơn bán chọn kho Chờ đóng gói hoặc Dở dang thì bị chặn.
  - Phồng tôm: cấp 2 mẻ nguyên liệu, ra 1,8 mẻ bánh khô, quyết toán.
    - Phần trong định mức vào 15488; phần vượt vào 6322.
    - Tỷ lệ hao hụt cho phép 2% làm dịch ngưỡng.
  - Đậu: quyết toán với lựa chọn của kế toán.
  - Đóng gói thành phẩm: túi PP tính bằng kg không làm lệch cân đối; giá thùng = bánh khô + bao bì.
  - Chia nhỏ 50 kg hàng thương mại thành 100 gói 500 g.
  - Hàng VH đóng gói tại nhà máy ghi trên sổ VH.
  - Kiểm kê có mốc; thiếu chờ xử lý làm giảm lượng có thể bán.
- **Cổng 3** nâng cấp từ 0.11.1 (digest image 0.11.1 đọc trên máy chủ sau khi triển khai).

## 9. Còn chờ chị Dung (không chặn code)

1. Bước xử lý chênh lệch kiểm kê (mục 6).
2. Tài khoản đối ứng số dư đầu kỳ: **3389** (Sheet 8 file tài sản) hay **9990** (tài khoản tạm app đang dựng). Cần trước 0.12.1.
3. Xác nhận ghi chi phí nhà máy chung vào 6323 (D2 của 0.11.1) trước khi ghi sổ thật.
