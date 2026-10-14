# AGENTS.md — hướng dẫn cho tác tử lập trình (Codex, Claude…) làm việc trên repo này

Đọc tệp này trước, rồi `docs/ban-giao.md` (trạng thái, việc còn mở), `docs/quyet-dinh-nghiep-vu.md` (13 quyết định
nghiệp vụ đã chốt — không hỏi lại), `deploy/release/RELEASE_GATES.md` + `deploy/release/TRIEN_KHAI_FRONTEND.md`
(đưa bản mới lên production) và `docs/quy-trinh-trien-khai-khach.md`. Ngôn ngữ trao đổi với chủ dự án (anh Tiến, 9xLab): **tiếng Việt**. Thông điệp commit, chú thích,
thông báo lỗi trên giao diện: tiếng Việt có dấu.

## Dự án là gì

Đơn vị tư vấn ERPNext **9xLab** đóng gói ERPNext **v16.36.1** cho doanh nghiệp Việt Nam, mỗi khách một máy ảo chạy Docker.
Khách đầu tiên: **An Phú Hưng - Vĩnh Hưng (APH-VH)**, 4 đơn vị trên một site: APH (TT133), VH (TT99), HKD Minh Khang (TT152),
TL (đơn vị nội bộ = XB, hàng không hóa đơn; không tạo company thứ năm). MISA chỉ lập hóa đơn thuế; ERP ghi tồn kho/công nợ
vận hành. Production là site **`frontend`** trên VM GCloud `erpnext-prod` (Compose `~/erp/aph-vh`, project `erp-aph-vh`).
Không dùng `erpnext.local` hay cấu hình cũ của nó.

Nghiệp vụ lớn từ bản 0.10.0 (PR #1, đã kiểm UAT trên CI, bật bằng cờ site_config): đơn bán chung nhiều công ty theo
chủ kho, ghi nợ lúc giao, trạng thái giao/nhận, bao + kg (giá/kg × kg/bao), nhập chờ định giá, chi phí chuyến theo kg,
sản xuất/phụ phẩm theo kg, tiền thực thu/cọc/phân bổ theo kế hoạch (không FIFO), APH nhận hộ TL, đổi nguồn phần chưa
giao, hạn mức chung + duyệt khách rủi ro cao, chặn người dùng "APH Không xem giá vốn" (Dũng) xem giá vốn ở mọi lối.

## Cấu trúc repo

| Đường dẫn | Nội dung |
|---|---|
| `apps/lab9x/` | App **lõi 9xLab** (`lab9x`, bản 0.2.2) dùng chung mọi khách: hệ thống tài khoản TT133/TT99, HKD TT152, quy tắc thuế GTGT, mẫu in, kiểm soát kế toán, nhóm hàng/tài khoản kho, đọc số bằng chữ. |
| `kh_aph/` (gốc repo là app) | App **riêng khách APH-VH** (`kh_aph`, bản 0.11.1 đang kiểm; production đang 0.11.0), `required_apps = ["erpnext", "lab9x"]`. Hook vào chứng từ, custom field, mẫu in, báo cáo, JS màn hình, cài bản trắng, bộ kiểm triển khai. |
| `khach/<ten>/khach.json` | Cấu hình khách (một nguồn sự thật). `phien-ban.yaml`: image đang chạy + môi trường. |
| `deploy/khach-hang/` | `dung.sh` (dựng mới), `nang-cap.sh` (nâng cấp, tự quay lui khi lỗi), `quay-lui.sh`, `compose.yaml`, `erpctl`. |
| `deploy/cloud/` | Sao lưu 2 lần/ngày lên Google Cloud Storage (systemd timer). |
| `.github/workflows/` | UAT candidate (ca nghiệp vụ HTTP/Chrome trên site `aphvh-web-uat`, gồm bộ 0.11.1 `deploy/uat/http/b0111*.py`), Cổng 2 (site trắng mỗi khách), Cổng 2b (diễn tập dung/nang-cap/quay-lui), **Cổng 3** (nâng cấp từ image production 0.11.0 đã bật 8 cờ + bộ cài + quay lui), Phát hành image (tag `v*`, cần tất cả). |
| `deploy/release/` | Kiểm kê chỉ đọc VM (`collect_frontend_inventory.py`), dấu vân site (`dau_van_site.py`, `so_dau_van.py`), cổng phát hành, thủ tục triển khai frontend. |
| `deploy/uat/`, `uat/` | Bộ chạy UAT HTTP/Desk của CI và biên bản UAT của Codex (lịch sử 11–13/10). |
| `tools/` | `kiem_ban_trang.py`, `build_print_formats.py`, công cụ dịch. |
| `docs/` | Quy trình, rà soát pháp lý, đối chiếu tài khoản thông tư, thu hộ. |
| `Dockerfile` | Image = `frappe/erpnext:v16.36.1` + lab9x + kh_aph (qua tệp `.pth`, thêm vào `sites/apps.txt`, chạy unit test lúc build). |

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
(cd apps/lab9x && python3 -m unittest discover -s lab9x/tests -t .)          # 58 test
PYTHONPATH=apps/lab9x python3 -m unittest discover -s kh_aph/tests -t .      # 213 test
# Dựng image như CI
docker build -t kh-aph-erpnext:dev .
```

Cổng chạy trên GitHub Actions (Linux amd64): Cổng 2 tự chạy theo pull request đụng `kh_aph/**`, `apps/**`, `khach/**`,
`Dockerfile`; UAT candidate và Cổng 3 tự chạy khi push nhánh PR; Cổng 2b chạy bằng tay hoặc khi phát hành. Số ca PASS kỳ
vọng của UAT ghi cứng trong `uat-candidate.yml` (inventory 33, funds 19, cost 16, dispatch 48, b0111 14). **Không tuyên bố PASS khi
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
3. **Không tạo kho** trong app: khách tự tạo cây kho. `khach.json` không có mục kho (`nha_may`, `kho_them`, `ten_nha_may`
   sẽ báo lỗi). App vẫn dựng tài khoản chuẩn, nhóm hàng cấp 1 gắn tài khoản kho, mẫu thuế, tài khoản mặc định, và **xóa**
   kho/nhóm/tài khoản mẫu của ERPNext.
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
- 12 cờ (0.11.1 thêm `kh_aph_factory_costing`, `kh_aph_factory_cash`, `kh_aph_sales_adjust`, `kh_aph_data_review`).
