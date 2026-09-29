# aphvh — tùy biến ERPNext cho An Phú Hưng và Vĩnh Hưng

App riêng chạy trên ERPNext v16.

- **0.1** — chia giá thành phẩm theo kg cho phiếu sản xuất có nhiều đầu ra.
- **0.2** — vai trò kế toán nhà máy, ẩn giá nguyên phụ liệu với vai trò này, phiếu nhập
  nguyên phụ liệu bắt buộc lấy từ đơn mua, báo cáo tồn kho số lượng, mẫu in phiếu nhập/xuất
  kho Việt Nam (01-VT, 02-VT theo TT133).

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
  print_utils.py      hàm dùng trong mẫu in (Nợ/Có, số tiền bằng chữ, định dạng số)
  vn_words.py         đọc số tiền bằng chữ, định dạng số kiểu Việt Nam (thuần Python)
  public/js/          ẩn cột giá trên màn hình (nạp qua doctype_js, không cần build)
  aph_vh/print_format mẫu in 01-VT, 02-VT, phiếu sản xuất
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
python -m unittest aphvh.tests.test_costing_rules aphvh.tests.test_vn_words aphvh.tests.test_print_formats aphvh.tests.test_translations -v
```
