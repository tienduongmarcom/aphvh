# AGENTS.md — hướng dẫn cho tác tử lập trình (Codex, Claude…) làm việc trên repo này

> Cập nhật nguồn 18/10/2026: PR #4 đã gộp vào `main` bằng merge commit
> `f05c8a181c269d2075b6d822addb571f26b7bef6`; lịch sử PR #1–#3 và tag0.15.2 đã nằm trong main.
> Nguồn0.15.3 thuộc PR #5 (`feat/thong-tin-giao-nhan-20261017`) → main;
> mã đóng gói `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c` đã đủ bốn cổng.
> Các dòng dưới nói main còn cũ hoặc production0.14.x là lịch sử; trạng thái production mới nhất
> phải đọc `deploy/release/TRANG_THAI.md` và `khach/aph-vh/phien-ban.yaml`.
> Production0.15.3 đã được người vận hành xác nhận ĐẠT ngày18/10/2026, digest khớp image phát hành.

Đọc tệp này trước, rồi `docs/ban-giao.md` (trạng thái, việc còn mở), `docs/quyet-dinh-nghiep-vu.md` (13 quyết định
nghiệp vụ đã chốt — không hỏi lại), `deploy/release/RELEASE_GATES.md` + `deploy/release/TRIEN_KHAI_FRONTEND.md`
(đưa bản mới lên production) và `docs/quy-trinh-trien-khai-khach.md`. Ngôn ngữ trao đổi với chủ dự án (anh Tiến, 9xLab): **tiếng Việt**. Thông điệp commit, chú thích,
thông báo lỗi trên giao diện: tiếng Việt có dấu.

## Dự án là gì

Đơn vị tư vấn ERPNext **9xLab** đóng gói ERPNext **16.50.0 + Frappe 16.51.0** (ghim theo digest, từ 0.11.0) cho doanh nghiệp Việt Nam, mỗi khách một máy ảo chạy Docker.
Khách đầu tiên: **An Phú Hưng - Vĩnh Hưng (APH-VH)**, 4 đơn vị trên một site: APH (TT133), VH (TT99), HKD Minh Khang (TT152),
TL (đơn vị nội bộ = XB, hàng không hóa đơn; không tạo company thứ năm). MISA chỉ lập hóa đơn thuế; ERP ghi tồn kho/công nợ
vận hành. Production là site **`frontend`** trên VM GCloud `erpnext-prod` (Compose `~/erp/aph-vh`, project `erp-aph-vh`).
Không dùng `erpnext.local` hay cấu hình cũ của nó.

Nghiệp vụ lớn từ bản 0.10.0 (PR #1, đã kiểm UAT trên CI, bật bằng cờ site_config): đơn bán chung nhiều công ty theo
chủ kho, ghi nợ lúc giao, trạng thái giao/nhận, bao + kg (giá/kg × kg/bao), nhập chờ định giá, chi phí chuyến theo kg,
sản xuất/phụ phẩm theo kg, tiền thực thu/cọc/phân bổ theo kế hoạch (không FIFO), APH nhận hộ TL, đổi nguồn phần chưa
giao, hạn mức chung + duyệt khách rủi ro cao, chặn người dùng "APH Không xem giá vốn" (Dũng) xem giá vốn ở mọi lối.

## Nhận bàn giao / kiểm độc lập (đọc trước khi làm gì)

Mọi agent (Claude, Codex, …) phải tiếp tục được việc tại bất kỳ thời điểm nào mà không cần lịch sử hội thoại:

1. **Đang ở đâu:** `deploy/release/TRANG_THAI.md` (production đang chạy bản nào, digest, ứng viên, CI, quay lui về đâu) và mục
   đầu tiên của `docs/ban-giao.md` (việc vừa làm, việc còn mở). Cập nhật CẢ HAI mỗi khi phát hành / triển khai / dừng giữa chừng.
2. **Kiểm không cần máy chủ:** Cổng 1 (unit test, lệnh ở dưới) chạy được ngay. Cổng 2 / 2b / 3 / UAT chạy trên GitHub Actions;
   bằng chứng = artifact `cong-3-bang-chung`, log `http-*-evidence.txt`, chú thích `::error::` của run. Không tin lời tuyên bố,
   đọc run trên đúng SHA.
3. **Kiểm script triển khai:** `deploy/release/dien_tap_ban_sao.sh` và `trien_khai_frontend.sh` nhận biến môi trường (`BE`,
   `ERP_DIR`, `TAG`, `IMG`, `SAO_LUU_CLOUD=0`, `DAU_RA`, `LOG_RA`) để chạy trên máy CI / máy thử y như trên VM — xem Cổng 3.
4. **Quyết định đã chốt** nằm trong `docs/` (không hỏi lại); điểm pháp lý chưa chắc ghi `docs/bang-ra-soat-phap-ly-APH-VH.md`.
5. Dừng giữa chừng thì commit phần đã xong (CI không cần xanh) và ghi "ĐANG DỞ: …, bước tiếp theo: …" vào `docs/ban-giao.md`.

## Cấu trúc repo

| Đường dẫn | Nội dung |
|---|---|
| `apps/lab9x/` | App **lõi 9xLab** (`lab9x`, bản 0.2.8) dùng chung mọi khách: hệ thống tài khoản TT133/TT99, HKD TT152, quy tắc thuế GTGT, mẫu in, kiểm soát kế toán, nhóm hàng/tài khoản kho, đọc số bằng chữ. |
| `kh_aph/` (gốc repo là app) | App **riêng khách APH-VH** (`kh_aph`, bản 0.14.3; production đang 0.14.3 (từ 16/10/2026 ~16:29)), `required_apps = ["erpnext", "lab9x"]`. Hook vào chứng từ, custom field, mẫu in, báo cáo, JS màn hình, cài bản trắng, bộ kiểm triển khai. |
| `khach/<ten>/khach.json` | Cấu hình khách (một nguồn sự thật). `phien-ban.yaml`: image đang chạy + môi trường. |
| `deploy/khach-hang/` | `dung.sh` (dựng mới), `nang-cap.sh` (nâng cấp, tự quay lui khi lỗi), `quay-lui.sh`, `compose.yaml`, `erpctl`. |
| `deploy/cloud/` | Sao lưu 2 lần/ngày lên Google Cloud Storage (systemd timer). |
| `.github/workflows/` | UAT candidate (ca nghiệp vụ HTTP/Chrome trên site `aphvh-web-uat`, gồm bộ 0.11.1 `deploy/uat/http/b0111*.py`, 0.11.2 `b0112*.py`, 0.11.3 `b0113*.py`, 0.11.4 `b0114*.py`, lượt 0.12 `b012*.py`, lượt 0.13 `b013*.py`, lượt 0.14 `b014*.py`), Cổng 2 (site trắng mỗi khách), Cổng 2b (diễn tập dung/nang-cap/quay-lui), **Cổng 3** (nâng cấp từ image production 0.14.3 theo digest, đã bật 21 cờ + bộ cài + cây kho + quay lui), Phát hành image (tag `v*`, cần tất cả). |
| `deploy/release/` | Kiểm kê chỉ đọc VM (`collect_frontend_inventory.py`), dấu vân site (`dau_van_site.py` có phần `chi_tiet` theo công ty/tài khoản/đối tượng, mã hàng/kho, bao; `so_dau_van.py`), diễn tập bản sao tách biệt (`dien_tap_ban_sao.sh`, dấu `dau_dien_tap.py`), triển khai một lệnh có bảo trì xuyên suốt (`trien_khai_frontend.sh`), bảng `TRANG_THAI.md`. |
| `deploy/uat/`, `uat/` | Bộ chạy UAT HTTP/Desk của CI và biên bản UAT của Codex (lịch sử 11–13/10). |
| `tools/` | `kiem_ban_trang.py`, `build_print_formats.py`, công cụ dịch. |
| `docs/` | Quy trình, rà soát pháp lý, đối chiếu tài khoản thông tư, thu hộ. |
| `Dockerfile` | Image = `frappe/erpnext@sha256:ac5b4591…` (ERPNext 16.50.0 + Frappe 16.51.0) + lab9x + kh_aph (qua tệp `.pth`, thêm vào `sites/apps.txt`, chạy unit test lúc build). |

### Đặt code ở đâu

- Quy tắc **dùng được cho nhiều khách** → `apps/lab9x/lab9x/`. Viết phần **thuần** (không import frappe) ở đầu tệp để unit test;
  phần gắn Frappe import `frappe` bên trong hàm. Xem mẫu `apps/lab9x/lab9x/nhom_hang.py`.
- Chỉ riêng khách này → `kh_aph/`. Khách sau sẽ có app `kh_<ten>` riêng; đừng nhét chữ "APH" vào tên vai trò/mẫu in/báo cáo.
- Tính năng mới: **luôn sau cờ site_config** (mặc định tắt, hook phải `return` sớm khi cờ tắt) và schema cài bằng hàm
  `schema()` gọi từ bộ cài rõ ràng (`kh_aph.cai_dat_tinh_nang` cho production, `uat_candidate_setup.setup_uat` cho UAT).
  **Không** gắn cài đặt tính năng vào after_install/after_migrate (có test chặn). Thêm cờ mới phải cập nhật cả
  `cai_dat_tinh_nang.FLAGS`, `quay-lui.sh`, `dau_van_site.py`, `handoff_preflight.py`, Cổng 3 (test kiểm nhất quán).
- Đang dang dở: phần gắn ERPNext dùng chung (controls, vat, mẫu in, báo cáo, custom field) còn nằm ở `kh_aph`, sẽ chuyển dần
  sang `lab9x`. Khi chuyển phải giữ đường dẫn cũ hoạt động hoặc đổi hook cùng lúc, và cập nhật test.

## Chạy kiểm thử

```bash
# Cổng 1 — unit test (không cần ERPNext; Python 3.11+)
(cd apps/lab9x && python3 -m unittest discover -s lab9x/tests -t .)          # 103 test
PYTHONPATH=apps/lab9x python3 -m unittest discover -s kh_aph/tests -t .      # 219 test
# Dựng image như CI
docker build -t kh-aph-erpnext:dev .
```

Cổng chạy trên GitHub Actions (Linux amd64): Cổng 2 tự chạy theo pull request đụng `kh_aph/**`, `apps/**`, `khach/**`,
`Dockerfile`; UAT candidate và Cổng 3 tự chạy khi push nhánh PR; Cổng 2b chạy bằng tay hoặc khi phát hành. Số ca PASS kỳ
vọng của UAT ghi cứng trong `uat-candidate.yml` (inventory 33, funds 19, cost 16, dispatch 48, b0111 14, b0112 13, b0113 13, b0114 7, b012 9, b013 10, b014 9). **Không tuyên bố PASS khi
chưa có run xanh trên đúng SHA**; run FAIL giữ nguyên làm bằng chứng, không sửa assertion để che lỗi. Lỗi được in thành chú thích
`::error::` — đọc qua `check-runs/<id>/annotations` của GitHub API.

Thử trên site thật (tùy chọn): một bench Frappe v16 với `apps/kh_aph` là symlink tới repo và tệp `.pth` cho `apps/lab9x`;
tạo site rồi `bench --site X execute kh_aph.khach_hang.ap_dung --kwargs '{"duong_dan": "khach/aph-vh/khach.json"}'`, sau đó
`kh_aph.kiem_trien_khai.chay`. Đổi hook thì phải xóa cache redis (`bench --site X clear-cache`).

## Phát hành

1. Tăng `__version__` trong `kh_aph/__init__.py` (và `apps/lab9x/lab9x/__init__.py` nếu lõi đổi); commit, push nhánh.
2. **Chủ dự án tự gắn tag** từ máy mình: `git tag vX.Y.Z && git push origin vX.Y.Z`. Workflow "Phát hành image" chạy
   Cổng 2 + 2b, kiểm tag khớp `__version__`, rồi đẩy `ghcr.io/tienduongmarcom/kh-aph-erpnext:X.Y.Z`.
3. Đổi `khach/aph-vh/phien-ban.yaml` → nâng cấp UAT bằng `deploy/khach-hang/nang-cap.sh` → khách ký UAT → production.

Nhánh làm việc hiện tại: `fix/p0-uat-v091-20261010` (PR #1 draft → `main`; `main` còn rất cũ, đừng dựa vào nó).
Không đẩy đè `main`, không ghi đè tag/image `0.9.1` (workflow phát hành từ chối).

## Quy tắc bắt buộc

1. **Theo thông tư** (TT133/2016, TT99/2025, TT152/2025 cho HKD; NĐ 123/2020, NĐ 70/2025, NĐ 310/2025…). Không chắc
   điều khoản thì **chưa làm** — ghi vào `docs/bang-ra-soat-phap-ly-APH-VH.md` và hỏi.
2. **Không bao giờ chạm dữ liệu thật của khách.** Thử trên site trắng / dữ liệu giả / UAT. Trên VM chỉ chạy lệnh chỉ đọc
   hoặc thủ tục đã ghi trong `TRIEN_KHAI_FRONTEND.md`; xác định đúng site/VM trước mọi thao tác.
3. **Cây kho do app dựng theo cây chuẩn** (đổi 14/10/2026, xem `docs/dac-ta-0.11.2.md` mục 2): khai địa điểm và kho vệ tinh
   trong `khach.json` (`dia_diem`); tên kho do app sinh. Bộ dựng chỉ THÊM kho thiếu, không đổi tên/xóa/đổi pháp nhân kho có
   tồn; kho ngoài cây chỉ báo. Khóa cũ `nha_may`, `kho_them`, `ten_nha_may` vẫn báo lỗi. App vẫn dựng tài khoản chuẩn,
   nhóm hàng cấp 1 gắn tài khoản kho, mẫu thuế, tài khoản mặc định, và **xóa** kho/nhóm/tài khoản mẫu của ERPNext.
4. **Giao diện theo `docs/kien-truc-giao-dien.md` (Hybrid Native, chốt 14/10/2026)**: Workspace chuẩn để điều hướng,
   Dialog cho thao tác ngắn, **Native Frappe Page** chỉ khi đạt 6 tiêu chí trong tài liệu đó (có cờ, có số đo A/B, chỉ
   Page API chính thức, gọi API facade trả trường tối thiểu). Chưa dùng Vue/SPA/bước build frontend. Không DocType
   "Nhiệm vụ" trạng thái riêng. Phần dưới vẫn áp dụng cho form chuẩn:
   Customize Form, Workspace, Dashboard, Client Script; JS qua `doctype_js` (không build
   asset). Giữ kiểu Frappe, nhận diện thương hiệu 9xLab; không bắt chước MISA AMIS. Không ghi đè tệp lõi Frappe/ERPNext.
5. Mọi bước cài đặt (`after_install`, `after_migrate`, `ap_dung`) phải **chạy lại nhiều lần không hỏng** (idempotent).
6. Không đưa mật khẩu/token vào repo, log hay lệnh. Máy chủ chỉ giữ token `read:packages`.
7. Không xóa dữ liệu/máy/container ngoài phạm vi được yêu cầu.

## Bẫy đã gặp (đừng lặp lại)

- **Triển khai (0.14.3):** container tạm chạy image mới KHÔNG được dùng chung ổ `sites`/mạng/Redis với production (entrypoint
  image chép tệp giao diện vào ổ, worker production nhận việc của site tạm). Diễn tập dùng tài nguyên riêng gắn nhãn
  `vn.9xlab.dien-tap=<mã lượt>`. Nâng cấp luôn trong chế độ bảo trì từ trước sao lưu tới khi kiểm xong; lỗi thì giữ bảo trì.

- **Frappe16.52.0 cache site_config trong RAM từng web worker TTL60:** đổi maintenance bằng CLI không xóa cache đó. Sau bật/tắt phải restart backend trước sao lưu/mở site; không chỉ chờ một ping200 (worker khác có thể503). Cổng2b39192414323 đã bắt lỗi này, giữ20 probe nghiêm sau readiness.

- **Frappe16.52.0 `frappe.call` trả jqXHR:** dùng `.always(...)` để mở lại nút cả thành công/lỗi; không gọi trực tiếp `.finally(...)`. Đã gặp ở Chrome mất phản hồi thu quầy (UAT39190026643), đối chiếu `frappe/public/js/frappe/request.js` đúng tag. Nếu cần Promise native phải chuyển rõ ràng; kiểm bằng trình duyệt thật, không chỉ kiểm cú pháp.

- **Phiên UAT HTTP/Desk:** mở Desk khởi tạo CSRF trong session. Không truyền cookie của caller urllib không có CSRF header sang Chrome rồi dùng lại để POST; dùng phiên trình duyệt riêng cùng nhân sự giả, vẫn kiểm principal server. Không tắt CSRF để chữa bộ thử. Đã gặp ở UAT39224149992 sau khi ca Chrome PASS.

- **Frappe16.52.0 Currency chỉ đọc:** `BaseControl.get_value()` dùng `value || undefined`, nên số0 trả undefined dù ô vẫn hiển thị0. Ca trình duyệt phải kiểm cả `control.value === 0` và vùng hiển thị; không đổi undefined thành0 để che lỗi. Native `frappe.client.delete` thành công có thể không có khóa `message`; cleanup quyền UAT dùng phản hồi raw, không suy xóa thất bại từ khóa thiếu.

- **Frappe16.52.0 lỗi đã bắt trong report:** `frappe.throw` vẫn đưa thông báo vào `frappe.local.message_log`. Khi bắt ValidationError để hiển thị thành dòng cần xử lý, chỉ gỡ các thông báo mới của chính lần gọi đó; giữ thông báo trước và không nuốt PermissionError. Kiểm Chrome không còn popup che bảng. Native cancel còn kiểm backlink sau `on_cancel`: nếu nguồn gương cần giữ lịch sử, chỉ ngoại lệ đúng nguồn dưới capability và vẫn kiểm mọi liên kết tĩnh/động khác; không dùng `ignore_links`.

- Frappe `BaseDocument.update` nhận mapping, không nhận kwargs. Update-after-submit không gọi `before_validate`: giá trị
  dẫn xuất (giá/bao) phải tính lại ở server.
- Phiếu nhập lùi ngày phải `set_posting_time` và chờ repost hoàn tất trước khi đọc giá vốn MA.
- Không monkeypatch class tạm trong `__main__` (pickle cache lỗi); dùng module thật.
- Trong workflow: `! grep …` không làm bước lỗi dưới `set -e`; dùng `if grep …; then exit 1; fi`. Không khai báo
  `shell: bash` thì không có pipefail (lỗi trước `| tee` bị nuốt).
- Test đọc tệp ngoài app (`.github`, `deploy/khach-hang`) phải tự bỏ qua trong image (`.dockerignore` loại chúng).

- ERPNext để `default_warehouse` ở **3 nơi**: Stock Settings, Item Default (của nhóm/mã), và `tabDefaultValue`. Muốn xóa
  kho mẫu phải gỡ hết (xem `kh_aph/cai_ban_trang.py::_bo_kho_mau`).
- Accounts Settings `add_taxes_from_item_tax_template` mặc định 1 → thuế tính **hai lần** khi mẫu thuế mặt hàng có 2 dòng
  (33311 + 1331). Đã đặt 0 (`kh_aph/vat.py`), bộ kiểm có kiểm mục này.
- Thuế mua vào: app chỉ gắn mẫu "Thuế GTGT mua vào - <viết tắt>" (1331) khi phiếu chưa có thuế; **kế toán tự chọn thuế suất**.
  Không tự chọn thuế suất (chủ dự án đã chốt).
- `.dockerignore` chỉ được loại `deploy/khach-hang` và `deploy/cloud` (test cần phần còn lại).
- Script triển khai phải chạy được trên Linux và macOS: không dùng `hostname -I` không dự phòng, `sed -i` phải có hậu tố
  (`sed -i.bak … && rm -f *.bak`), truyền tệp vào container qua stdin thay vì `docker cp`.
- Python package không được bắt đầu bằng chữ số → lõi tên `lab9x`, tiêu đề "9xLab".
- **Frappe 16: hook `has_permission` trả giá trị falsy (kể cả `None`) là TỪ CHỐI.** Hook chỉ được trả `True` (không ý kiến)
  hoặc `False` (chặn). Lỗi này từng chặn kế toán mở GL/Purchase Invoice/kiểm kê (sửa 0.11.1). Ca HTTP phải chạy bằng người
  dùng thật, không chỉ Administrator (Administrator bỏ qua hook).
- Phản hồi `frappe.client.insert`/`savedocs` trả nguyên chứng từ, không qua lớp che khi đọc: trường nhạy cảm phải che ở
  `after_request` (xem `dung_cost_policy.mask_cost_response`).
- Mẫu in: sửa `.html` rồi chạy `python tools/build_print_formats.py` (tăng `MODIFIED`); hàm jinja mới phải nằm ở
  `kh_aph.print_utils` (có test).
- 21 cờ (0.11.1 thêm `kh_aph_factory_costing`, `kh_aph_factory_cash`, `kh_aph_sales_adjust`, `kh_aph_data_review`;
  0.11.2 thêm `kh_aph_kho_chuan`; 0.11.3 thêm `kh_aph_sales_p1`; 0.11.4 thêm `kh_aph_quan_tri`; 0.12 thêm `kh_aph_du_lieu`, `kh_aph_dau_ky`; 0.13 thêm `kh_aph_kho_van_hanh`, `kh_aph_gia_san`; 0.14 thêm `kh_aph_trung_tam_ban`, `kh_aph_tien_vay`).
- Accounting Period (khóa kỳ): ERPNext thêm " - <viết tắt>" vào cả `name` và `period_name`, chỉ cho khóa tháng đã
  kết thúc, và chặn cả lưu nháp chứng từ trong kỳ (ClosedAccountingPeriod). `bootstrap_doctypes_for_closing` lỗi với dict:
  tự dựng `closed_documents` từ hook `period_closing_doctypes`.
- Bench cục bộ 16.36 không kiểm kiểu như 16.50 (`get_payment_terms` đòi ngày dạng chuỗi): ngày truyền cho hàm
  whitelisted của ERPNext luôn `str(getdate(...))`.
- Hóa đơn trả lại tự sinh trừ thẳng vào hóa đơn gốc (`update_outstanding_for_self = 0`), nên tự nó không có "nợ":
  `get_payment_entry` trên nó báo "Paid Amount is mandatory". Phiếu chi hoàn tiền phải lập theo số tiền, không theo hóa đơn.
- Danh sách DocType của app được ghi cứng trong `test_tong_hop_khach.test_wired`: thêm DocType mới phải sửa test đó.
- Đổi cấu trúc Custom Field (vd thêm `allow_on_submit`) thì chạy lại `schema()` trên site thử: `create_custom_fields` cập nhật
  ô đã có. Báo cáo mới cần migrate (hoặc `frappe.reload_doc`) mới chạy được trên site cũ.
- Kho dở dang nhận biết bằng Loại kho = "Dở dang dây chuyền" (0.11.2); ô "Kho bồn dở dang" 0.11.1 đã gỡ.
- Hóa đơn đầu kỳ của Opening Invoice Creation Tool có dòng **không mã hàng**: hook duyệt `items` phải bỏ qua dòng thiếu
  `item_code` (lỗi "Item None not found" ở `bag_stock.validate`, sửa ở lượt 0.12). Công cụ này chuẩn chỉ cấp cho System Manager.
- Frappe kiểm ô Link/Dynamic Link (`_validate_links`) **trước** `before_insert`/`validate`: không điền loại của Dynamic Link
  trong hook; dùng hai ô Link riêng (xem `APH Dong de nghi so lieu`).
- Từ 0.11.5 `ap_dung` đặt ngôn ngữ hệ thống = vi: thông báo ERPNext ra tiếng Việt. UAT giữ Administrator tiếng Anh
  (`uat_candidate_setup.setup_uat`); ca kiểm thông báo bằng người dùng khác phải so chuỗi tiếng Việt hoặc so mã lỗi.
- Đầu kỳ: đối ứng 9990 (không 3388/3389), ngày 30/09/2026; báo cáo `Doi chieu so du dau ky` xếp loại theo loại chứng từ
  có dòng 9990 (Stock Reconciliation, Sales/Purchase Invoice, Journal Entry tiền/khác).
- ERPNext tự kiểm quyền Payment Entry bên trong `get_account_details` (cả khi `ignore_permissions`): vai trò lập phiếu thu
  phải có DocPerm Payment Entry (`ban_quay._quyen_ktbh`).
- Accounting Period không được chồng nhau: khóa / chốt mới phải nới kỳ đã có (`dau_ky.khoa_den_ngay`).
- Giá tạm (0.11.1) chỉ cho nhóm hàng có cờ, TRỪ phiếu tồn đầu kỳ (Opening Stock) — rà soát dòng 15/20.
- Khế ước vay gắn bằng ô `kh_aph_khe_uoc` trên dòng bút toán (không dùng Accounting Dimension: thêm ô vào ~40 DocType).
  Tạo Accounting Dimension thì ERPNext đẩy việc dựng ô vào hàng đợi `long` (không chạy ngay khi không có worker).
- Tài khoản 1388 / 3388 không có loại (account_type) nên nhận đối tượng Nhân viên; tài khoản có loại khác Receivable / Payable /
  Equity thì ERPNext chặn đối tượng (`validate_account_party_type`).
- ERPNext16.51.1 `accounts_controller.update_child_qty_rate` bỏ qua dòng thiếu `item_code`, kể cả có `docname`;
  thao tác thành công có thể trả phản hồi không có `message`. Fixture phải gửi đủ mã/dòng, lượng/giá, UOM/hệ số,
  ngày và mô tả như màn chuẩn, rồi kiểm trạng thái đã lưu. Quyền sửa PO (Purchase User/Manager) độc lập quyền
  Accounts Manager chốt giá; không cấp quyền mua ngầm hoặc coi phản hồi rỗng là lỗi nghiệp vụ.
- PO mới cho mã đã mua có thể tự điền giá mua gần nhất khi payload gửi rate0. Ca “chưa có giá” phải dùng mã chưa
  có lịch sử giá và kiểm lại `PO.items[].rate==0` sau lưu; không suy rate0 từ payload, không bỏ assert để cho PASS.

## Quy ước chữ hiển thị (chủ dự án, 20/10/2026)

Chữ người dùng thấy **không dùng "APH" làm tên chung** cho hệ thống/đơn chung nhiều đơn vị (dễ hiểu nhầm là của riêng An Phú Hưng);
chỉ dùng khi đúng là nói về công ty APH (vd. "Kho … - APH", "APH: TT133"). Tên kỹ thuật DocType giữ nguyên, hiển thị qua `translations/vi.csv`.
Tên dễ hiểu, không gây áp lực ("Bàn …", không "Việc …"), không lộ mã nội bộ (R0xx, bước n) trên nhãn.
