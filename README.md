# aphvh — tùy biến ERPNext cho An Phú Hưng và Vĩnh Hưng

App riêng chạy trên ERPNext v16.

- **0.1** — chia giá thành phẩm theo kg cho phiếu sản xuất có nhiều đầu ra.
- **0.2** — vai trò kế toán nhà máy, ẩn giá nguyên phụ liệu với vai trò này, phiếu nhập
  nguyên phụ liệu bắt buộc lấy từ đơn mua, báo cáo tồn kho số lượng, mẫu in phiếu nhập/xuất
  kho Việt Nam (01-VT, 02-VT theo TT133).
- **0.3** — luồng bán hàng kho Hà Nội: cảnh báo công nợ và giá (không chặn), hóa đơn nháp tự tạo
  khi xác nhận phiếu giao hàng, phiếu xuất kho và biên bản giao nhận 2 liên, vai trò nhân viên bán
  hàng và thủ kho Hà Nội (thấy giá bán, không thấy giá vốn).

## Bản 0.1 làm gì

| Thành phần | Nội dung |
|---|---|
| Loại phiếu kho **"Đóng gói theo kg"** | Mục đích Repack. Một phiếu được có nhiều thành phẩm. |
| Chia giá theo kg | Tổng giá đầu vào (theo sổ kho, bình quân) chia cho các dòng thành phẩm theo số kg. Phần lẻ làm tròn dồn vào dòng nhiều kg nhất. |
| Quy đổi kg | Mã tồn kho bằng **Kg**: hệ số 1. Mã tồn kho bằng đơn vị khác (Thùng…): lấy **Trọng lượng/đơn vị** và **Đơn vị trọng lượng = Kg** trên mã hàng. |
| Lưu trên chứng từ | Phiếu lưu mã quy tắc `kg-v1`; mỗi dòng lưu `Kg / ĐVT tồn kho` và `Số kg tính giá` lúc lưu/gửi. |
| Tính lại giá (repost) | Khi chi phí nhập khẩu đổi hoặc có chứng từ lùi ngày, ERPNext tính lại phiếu theo quy tắc và số kg **đã lưu**, không đọc lại trọng lượng hiện tại trên mã hàng. |

Phiếu kho loại khác, và công ty không dùng loại phiếu này, giữ nguyên hành vi chuẩn của ERPNext.

**Chưa hỗ trợ ở bản 0.1** (phiếu sẽ báo lỗi): phụ phẩm định giá riêng, chi phí cộng thêm
trên phiếu, dòng vừa có kho nguồn vừa có kho đích.

## Bản 0.2 làm gì (ghi chú phát hành — duyệt trước khi cài)

### Vai trò mới "Kế toán nhà máy APH"

Gán cho kế toán nhà máy **thay cho** Stock User (Stock User xem được toàn bộ giá). Quyền app tạo
khi cài (chỉ tạo khi chưa có; đã chỉnh tay trong Role Permission Manager thì giữ nguyên):

| Loại chứng từ | Quyền |
|---|---|
| Phiếu nhập mua hàng (Purchase Receipt), Phiếu kho (Stock Entry) | đọc, sửa, tạo, gửi, hủy, sửa đổi, xóa nháp, in |
| Gói lô/serial (Serial and Batch Bundle) | đọc, sửa, tạo, gửi, hủy, xóa |
| Lô (Batch), hồ sơ Lô nhập khẩu | đọc, sửa, tạo |
| Đơn mua hàng | chỉ đọc (để lấy hàng vào phiếu nhập; không in) |
| Mã hàng, Kho, Nhà cung cấp, Loại phiếu kho, ĐVT, Nhóm hàng, Thương hiệu, Công ty, Điều khoản | chỉ đọc |
| Kho | thêm quyền báo cáo (để mở báo cáo Tồn kho số lượng APH) |
| Tài khoản, Trung tâm chi phí, Dự án | chỉ chọn trong ô liên kết |
| Cài đặt kho, Cài đặt mua hàng | chỉ đọc (màn hình phiếu cần đọc; không có giá) |

**Không có:** xem dạng bảng/xuất Excel phiếu, sổ kho (Stock Ledger Entry), Bin, sổ cái, báo cáo
có giá trị (Stock Balance, Stock Ledger…), tạo mã hàng, tạo nhà cung cấp, phiếu kiểm kê, phân bổ
chi phí mua hàng. Lần đầu thêm quyền cho một loại chứng từ, Frappe chép quyền chuẩn sang quyền
tùy chỉnh (như khi bấm trong Role Permission Manager): quyền các vai trò khác giữ nguyên, nhưng
bản cập nhật ERPNext sau này đổi quyền chuẩn của các loại chứng từ đó sẽ không tự áp dụng.

### Ẩn giá (mức màn hình + báo cáo, đã chốt 29/09/2026)

Người có vai trò trên mà **không** có vai trò xem giá (Stock Manager, Accounts User/Manager,
Purchase User/Manager, System Manager, Auditor):
- Không thấy đơn giá, thành tiền, tổng tiền, thuế trên phiếu nhập (trừ phiếu vật tư vận hành),
  đơn mua, phiếu kho, gói lô; không thấy giá trên mã hàng; cột tổng tiền bị bỏ khỏi danh sách.
- Bản in (mọi mẫu, kể cả mẫu Standard) để trống đơn giá, thành tiền, tổng tiền, thuế: app xóa
  các trường này trong bộ nhớ ngay trước khi dựng bản in (`before_print`), không lưu vào phiếu.
- Giới hạn: người rành kỹ thuật vẫn đọc được giá qua API. Muốn khóa ở máy chủ thì dùng che
  trường (mask) của Frappe v16 — khi đó phiếu vật tư vận hành phải tách sang loại phiếu khác.

Bản 0.2.1 sửa: dòng quyền mới của Frappe mặc định có "xuất" (export) và "đọc" — bản 0.2.0 để lọt
quyền xuất Excel và đọc Tài khoản/Trung tâm chi phí/Dự án. Bản vá `normalize_factory_role_perms`
đặt lại đúng bảng trên cho site đã cài 0.2.0.

### Phiếu nhập

- Ô **"Phiếu nhập vật tư vận hành"**: tích thì hiện giá để kế toán nhà máy tự nhập, và chỉ
  nhận mã thuộc nhóm hàng tích **"Nhà máy tự nhập giá"** (cài sẵn cho nhóm "Vật tư tiêu hao";
  kế toán trưởng tích thêm nhóm khác trên Nhóm hàng).
- Không tích: người bị ẩn giá phải lấy hàng từ đơn mua (giá do kế toán trưởng đặt trên đơn;
  Buying Settings đang để "Maintain same rate" = Stop nên giá không đổi được).

### Báo cáo và mẫu in

- **Tồn kho số lượng APH** (tên gốc `Ton kho so luong APH`): tồn thực tế và số đặt mua chưa
  nhận theo mã, kho — không có giá trị.
- **Phiếu nhập kho APH** (Purchase Receipt) và **Phiếu kho APH** (Stock Entry) đặt làm mẫu in
  mặc định. Phiếu kho tự chọn mẫu: nhập khác → 01-VT, xuất/chuyển kho → 02-VT, sản xuất/đóng
  gói → Phiếu sản xuất (xuất dùng + nhập kho, có số kg). Nợ/Có lấy từ sổ cái của phiếu đã gửi.
  Sửa mẫu: sửa `.html`/`phieu_in_aph.css` rồi chạy `python tools/build_print_formats.py`.

## Mở rộng về sau

- Quy tắc mới (ví dụ phụ phẩm tính theo giá trị thuần có thể thực hiện được) = mã quy tắc mới
  trong `constants.py` + hàm mới trong `costing_rules.py`. Phiếu cũ giữ `kg-v1`.
- Báo cáo (đối chiếu 1381, giá về kho theo lô, tỷ lệ thu hồi) đọc dữ liệu đã có, không cần
  sửa chứng từ cũ, miễn là chứng từ đã gắn chiều phân tích "Lô nhập khẩu".

## Cấu trúc

```
aphvh/
  hooks.py            khai báo extend_doctype_class, after_install, after_migrate
  constants.py        tên loại phiếu, mã quy tắc, đơn vị Kg
  costing_rules.py    phép chia thuần (kiểm thử không cần Frappe)
  stock_entry_kg.py   lớp mở rộng Stock Entry
  install.py          custom field, loại phiếu, vai trò + quyền, mẫu in mặc định (chạy lại được)
  price_visibility.py ai bị ẩn giá, quy tắc phiếu nhập nguyên phụ liệu / vật tư vận hành
  print_utils.py      hàm dùng trong mẫu in (Nợ/Có, số tiền bằng chữ, định dạng số, lô, địa chỉ)
  sales_rules.py      0.3: so giá với bảng giá, chọn hạn mức, câu cảnh báo (thuần Python)
  sales_warnings.py   0.3: cảnh báo công nợ/giá trên đơn bán hàng
  sales_flow.py       0.3: hóa đơn nháp tự tạo từ phiếu giao hàng, thủ kho chỉ giao theo đơn
  vn_words.py         đọc số tiền bằng chữ, định dạng số kiểu Việt Nam (thuần Python)
  public/js/          ẩn cột giá trên màn hình (nạp qua doctype_js, không cần build)
  aph_vh/print_format mẫu in 01-VT, 02-VT, phiếu sản xuất, phiếu xuất kho bán hàng, biên bản giao nhận
  aph_vh/report       báo cáo Tồn kho số lượng APH
  tests/              kiểm thử đơn vị
tools/build_print_formats.py   ghép .html/.css vào .json mẫu in
Dockerfile            dựng bản cài ERPNext kèm app
```

## Dựng và cài (Docker, theo cấu hình pwd.yml)

```bash
# 1. Lấy mã nguồn đúng phiên bản đã nghiệm thu
git clone git@github.com:<chu-so-huu>/aphvh.git && cd aphvh && git checkout v0.1.0

# 2. Dựng bản cài (tự chạy kiểm thử đơn vị trong lúc dựng)
docker build -t aphvh-erpnext:0.1.0 .

# 3. Trong tệp compose, đổi mọi dòng "image: frappe/erpnext:v16.36.1" thành
#    "image: aphvh-erpnext:0.1.0", rồi khởi động lại (configurator tự cập nhật apps.txt)
docker compose -p <du-an> -f <tep-compose> up -d

# 4. Cài app vào site
docker exec <du-an>-backend-1 bench --site frontend install-app aphvh
```

Sao lưu site trước bước 3. Gỡ app: `bench --site frontend uninstall-app aphvh`
(phiếu đã gửi vẫn giữ nguyên giá trị trên sổ).

## 0.2.2–0.2.3 – bản dịch chốt cho màn hình kế toán trưởng

- `aphvh/translations/vi.csv`: 686 chuỗi (0.2.3 thêm 7 nút bấm, trong đó "Update Rate and Availability" đang dịch sai là tỷ giá) (Frappe nạp sau ERPNext nên đè bản dịch chính thức), sinh từ
  `tools/translation/export_csv.py` theo bảng đã rà 3 vòng và anh Tiến chốt 29/09. Không ghi bản ghi Translation vào CSDL;
  gỡ app là về bản dịch gốc.
- Sau khi cài: migrate (xóa bộ nhớ đệm bản dịch), mỗi người bấm Ctrl+Shift+R.

## 0.2.4 – dịch báo cáo kho, thông báo, màn hình nhà máy (30/09/2026)

- `vi.csv` thêm 678 chuỗi (tổng 1.364): cột và bộ lọc báo cáo kho (Tổng hợp nhập – xuất – tồn: SL đầu kỳ / SL nhập /
  SL xuất / SL tồn cuối…), thông báo lỗi, cảnh báo, hộp thoại trong mã Python/JS của kho và mua hàng (tồn kho âm, lô,
  phiếu kho, phiếu nhập, đơn mua), mô tả trường, màn hình kế toán nhà máy.
- Sửa lỗi phát hiện khi quay video: Lead "Chì" → Khách hàng tiềm năng; Subcontracting "Ký gửi" → Gia công; cột số thứ tự
  "Không." → STT (dòng có ngữ cảnh, cột thứ 3 của CSV).
- Công cụ: `tools/translation/v024/` (extract.py gom chuỗi bằng AST cho Python để lấy đủ chuỗi viết nhiều dòng; BRIEF.md;
  final_rows_024.json). Giữ nguyên bản dịch của "Stores", "Standard Selling", "after" vì mã dùng chúng để tra tên.
- Sau khi cài: migrate, Ctrl+Shift+R; báo cáo chạy nền (Tổng hợp nhập – xuất – tồn) bấm "Xây dựng lại" để cột lấy tên mới.

## 0.3 – luồng bán hàng kho Hà Nội (30/09/2026, duyệt trước khi cài)

Theo thiết kế "Thiết kế luồng bán hàng APH – kho Hà Nội" và các quyết định của anh Tiến ngày 30/09.
Chạy thử đủ chuỗi trên ERPNext 16.36.1 riêng (đơn → giao thiếu → giao nốt → hóa đơn → thu một phần →
trả lại → hủy phiếu giao), số dư 131, 5111, 33311, 632, 156 khớp tính tay.

| Phần | Làm gì |
|---|---|
| Cảnh báo công nợ | Khi lưu và xác nhận đơn bán hàng: công nợ (sổ 131 + đơn chưa lập hóa đơn) cộng đơn này vượt **Hạn mức cảnh báo**, hoặc khách có nợ quá hạn → hiện hộp "Cảnh báo", **vẫn lưu, vẫn xác nhận**. Hạn mức đặt ở bảng hạn mức tín dụng của nhóm khách, sửa riêng được cho từng khách, theo từng công ty; khách không đặt thì lấy nhóm, rồi nhóm cha. Cột hạn mức chuẩn của ERPNext (chặn) bị ẩn. |
| Cảnh báo giá | Dòng có giá thấp hơn giá trong bảng giá → cảnh báo. Nhân viên bán hàng sửa giá tự do. |
| Đánh dấu đơn | Đơn bị cảnh báo có ô "Vượt hạn mức hoặc có nợ quá hạn" / "Có dòng giá thấp hơn bảng giá" và nội dung cảnh báo; lọc được trên danh sách đơn. |
| Hóa đơn nháp tự tạo | Xác nhận phiếu giao hàng → hóa đơn bán hàng **nháp** đúng số lượng đã giao, giá và thuế theo đơn, ngày hóa đơn = ngày giao, hạn thanh toán tính từ ngày giao. Kế toán kiểm tra rồi xác nhận. Phiếu nhận hàng trả lại: hóa đơn gốc **còn nháp** → trừ số trả lại thẳng vào hóa đơn nháp đó (trả hết thì xóa), không lập hóa đơn trả lại; hóa đơn gốc **đã xác nhận** → hóa đơn trả lại nháp gắn hóa đơn gốc (từng dòng, giảm công nợ của hóa đơn gốc). Đơn đã lập hóa đơn một phần trước khi giao, hoặc phiếu giao có dòng lập từ hóa đơn → không tự tạo (tránh trùng), báo kế toán. Tạo lỗi thì phiếu giao vẫn xác nhận, có Nhật ký lỗi và thông báo để kế toán lập tay. Hủy phiếu giao → xóa hóa đơn nháp app đã tạo từ phiếu đó. Hóa đơn có ô "Tự tạo từ phiếu giao hàng" để lọc. |
| Phiếu xuất kho bán hàng APH | Mẫu 02-VT, thủ kho và người nhận ký. Giá bán theo đơn (chưa thuế), không có giá vốn; cột số lượng theo đơn và thực xuất; lô. Phiếu nhận hàng trả lại in thành phiếu nhập kho 01-VT. Mẫu in mặc định của phiếu giao hàng. |
| Biên bản giao nhận APH | 2 liên trong một lần in (liên 1 giao khách, liên 2 công ty lưu): bên giao, người vận chuyển (khi thuê xe), bên nhận, đơn giá, thành tiền, thuế GTGT, tổng thanh toán, bằng chữ. |
| Ô giao nhận trên phiếu giao hàng | Hình thức giao (Khách tự lấy / Thuê xe, nhà xe), người nhận hàng bên khách, nhà xe, lái xe, biển số, SĐT lái xe. Sửa được sau khi xác nhận. Nút **In → Phiếu xuất kho / Biên bản giao nhận (2 liên)**. |
| Vai trò "Nhân viên bán hàng APH" | Lập, xác nhận đơn bán hàng; đọc khách, mã hàng, bảng giá **bán** (không thấy bảng giá mua), phiếu giao hàng; không tạo khách, không xem hóa đơn, không xuất Excel. |
| Vai trò "Thủ kho Hà Nội APH" | Lập, in, xác nhận phiếu giao hàng **từ đơn** (không có đơn thì không lưu được), phiếu trả lại; không sửa giá (khóa trên màn hình và chặn ở máy chủ); đọc đơn, phiếu kho chuyển về; không xem hóa đơn. |
| Ẩn giá vốn | Với hai vai trò trên (và kế toán nhà máy): giá tồn kho, lãi gộp trên dòng đơn; giá vào trên phiếu giao (cả hàng bộ); giá tồn kho, giá mua trên mã hàng; giá trên gói lô và phiếu kho — ẩn trên màn hình và xóa khỏi bản in. Nút "Xem trước → Sổ cái / Sổ kho" trên phiếu nháp bị chặn. Bảng giá chỉ thấy bảng giá chỉ dùng để bán. Báo cáo Tồn kho số lượng APH mở cho hai vai trò. |
| Cài đặt bán hàng | Mục "An Phú Hưng – luồng bán hàng": bật/tắt tự tạo hóa đơn, cảnh báo công nợ, cảnh báo giá (bật sẵn). |

Kế toán dùng vai trò chuẩn (Accounts User, Sales Manager…): thấy giá vốn, xác nhận hóa đơn.

Công ty APH đã bật tài khoản kho theo nhóm hàng (8080 và bản chính thức, kiểm 30/09): Kho Hà Nội chứa
được cả thành phẩm (155) và hàng hóa (156), tài khoản lấy theo nhóm hàng, không theo kho.

Lưu ý:
- Hạn mức tín dụng chuẩn của ERPNext (chặn) bị ẩn; nếu khách/nhóm khách nào đang có số ở cột đó thì
  app KHÔNG ẩn và in cảnh báo khi migrate — xóa số đó để chỉ còn cảnh báo.
- Trả lại khi hóa đơn gốc còn nháp: phiếu giao gốc hiện "Partially Billed" (hóa đơn = số giữ lại), giống
  luồng chuẩn của ERPNext khi trả hàng trước khi lập hóa đơn.
- Cài đặt bán hàng dùng chung mọi công ty (khi thêm Vĩnh Hưng sẽ xem lại). Không bật "Validate Selling
  Price" (thông báo lỗi của nó nêu giá vốn).

**Chưa làm ở bản này (bước cài nền, làm sau khi chị Dung trả lời):** nhóm khách, loại thuế, mẫu thuế,
quy tắc thuế; 5 kho vệ tinh;
Selling Settings "giữ đúng giá từ đơn sang hóa đơn"; giới hạn kho cho thủ kho (User Permission).

Cài: dựng bản mới, migrate, Ctrl+Shift+R. Không có bản vá dữ liệu; `after_migrate` tạo ô, vai trò,
quyền (chỉ khi chưa có), đặt mẫu in mặc định của phiếu giao hàng (trừ khi đã chọn mẫu khác
"with Item Image").

## 0.3.2 – mẫu in theo kế toán trưởng, chặn bán có hóa đơn khi chưa có thuế suất (30/09/2026)

- **Phiếu xuất kho** (và phiếu nhập kho hàng trả lại): chỉ số lượng, không in đơn giá, thành tiền.
- **Biên bản giao nhận**: đơn giá, thành tiền đã gồm thuế GTGT, một dòng tổng thanh toán; không tách
  tiền hàng và thuế. Thuế lấy theo từng dòng hàng (bảng thuế theo dòng của ERPNext); phần lệch do làm
  tròn dồn vào dòng lớn nhất để cộng đúng tổng thanh toán.
- Bán **Có** hóa đơn mà mặt hàng chưa có mẫu thuế mặt hàng: lưu nháp thì cảnh báo, xác nhận thì chặn
  (không tự coi là 0%).

## 0.3.1 – có / không xuất hóa đơn GTGT (30/09/2026)

ERPNext ghi mọi lần bán thật; MISA chỉ ghi lần bán có hóa đơn để kê khai thuế.

- Ô **Xuất hóa đơn GTGT** (Có/Không) trên Đơn bán hàng, Phiếu giao hàng, Hóa đơn bán hàng; mặc định
  theo ô cùng tên trên Khách hàng (kế toán đặt). Khách chưa đặt thì người lập phải chọn. Đơn → phiếu
  giao → hóa đơn → hóa đơn trả lại tự mang theo. Thủ kho không đổi được (phải giống đơn).
- **Không**: máy chủ bỏ dòng thuế, mẫu thuế mặt hàng khi lưu; khách nợ đúng tiền hàng, không ghi 33311.
  Biên bản giao nhận không in dòng thuế; phiếu xuất kho không ghi "chưa thuế".
- **Có**: tính thuế như chuẩn; chứng từ đổi từ Không sang Có thì nạp lại mẫu thuế bán hàng mặc định
  của công ty (phải có một mẫu "Mặc định" cho công ty).
- Hóa đơn bán hàng có ô ký hiệu, số, ngày hóa đơn điện tử (ghi được sau khi xác nhận); chỉ ghi khi Có;
  báo trùng ký hiệu + số.
- Báo cáo **Bán hàng có hóa đơn APH** (kế toán): hóa đơn Có đã xác nhận theo kỳ, lọc đã/chưa ghi số,
  để đối chiếu bảng kê đầu ra MISA.
- Bỏ qua với khách nội bộ và hóa đơn đầu kỳ (Is Opening).

## Nâng cấp bản đã cài (0.1 → 0.2.x)

```bash
# Sao lưu site trước
docker exec <du-an>-backend-1 bench --site frontend backup
# Dựng bản mới (tự chạy kiểm thử đơn vị)
docker build -t aphvh-erpnext:0.2.1 .
# Đổi image trong tệp compose sang bản mới, khởi động lại, rồi migrate để nạp mẫu in,
# báo cáo, vai trò, quyền và custom field
docker compose -p <du-an> -f <tep-compose> up -d
docker exec <du-an>-backend-1 bench --site frontend migrate
```

## Kiểm thử

```bash
python -m unittest aphvh.tests.test_costing_rules aphvh.tests.test_vn_words aphvh.tests.test_print_formats aphvh.tests.test_translations aphvh.tests.test_sales_rules -v
```
