# Quy trình triển khai cho khách (hướng A: mỗi khách một máy + Docker image)

Khách đầu tiên: **An Phú Hưng - Vĩnh Hưng** (`khach/aph-vh/`). Nguyên tắc: **mình không bao giờ chạm dữ liệu thật của khách**; mình giao hệ thống đúng cùng công cụ để khách tự nhập và tự kiểm.

## PHƯƠNG ÁN FINAL (08/10/2026)
1. **Một nguồn sự thật:** repo GitHub giữ app, `khach/<ten>/khach.json` và `phien-ban.yaml`.
2. **Kiểm chứng tự động trên Linux amd64 của GitHub** (giống máy chủ khách): Cổng 1 unit test, Cổng 2 site trắng theo từng khách, **Cổng 2b diễn tập** `dung.sh` + `nang-cap.sh` (cả ca lỗi) + `quay-lui.sh`. Không đạt thì không gắn tag, không ra image.
3. **Triển khai một lệnh:** workflow "Triển khai khách" chọn một khách hoặc tất cả, chờ duyệt, SSH vào VM chạy `nang-cap.sh` (tự giữ bản cũ / tự quay lui khi lỗi).
4. **Mỗi khách hai máy Docker:** UAT (dữ liệu giả, nâng cấp trước, khách ký) và production (dữ liệu thật, nâng cấp sau, sao lưu 2 lần/ngày, mình không truy cập).
5. **Dữ liệu:** `tu_nhap` hoặc `import_mot_phan` + `ngay_chot` (như mục Hai chế độ dữ liệu).
6. **MacBook chỉ để xem giao diện**, không phải nơi kiểm chứng (khác kiến trúc chip và lệnh hệ thống so với máy chủ).

Lộ trình: tuần 1 Cổng 2b + workflow triển khai + dựng UAT khách đầu tiên; tuần 2 công cụ import/kiểm dữ liệu + dữ liệu giả, khách UAT và ký, mở production; sau đó theme, `khach-moi`, cảnh báo.
Cần anh chốt: nhà cung cấp máy ảo (UAT + production), `che_do_du_lieu` và `ngay_chot`, tên miền; anh tự thêm khóa SSH triển khai vào GitHub Secrets.

## Cấu trúc app từ 0.7.0
- **`lab9x` (9xLab)**: lõi dùng chung, nằm ở `apps/lab9x` của repo. Hiện chứa các quy tắc thuần: hệ thống tài khoản TT133/TT99, thuế GTGT, hộ kinh doanh TT152, mẫu in (quy tắc), kiểm soát kế toán, cảnh báo bán hàng, bên thứ ba, thu hộ, tồn kho theo tài khoản, đọc số bằng chữ.
- **`aphvh`**: app riêng của khách An Phú Hưng - Vĩnh Hưng (đóng vai trò `kh_aph`), phụ thuộc `lab9x`. Giữ tên `aphvh` vì đổi tên app đã cài trên site đang chạy rủi ro cao. Các đường dẫn cũ (`aphvh.vn_words`...) trỏ sang lõi nên site cũ không vỡ.
- **0.7.0 bỏ chữ "APH"** khỏi vai trò (Kế toán nhà máy, Nhân viên bán hàng, Thủ kho bán hàng), 6 mẫu in và 3 báo cáo. Patch `aphvh.patches.v0_7.doi_ten_bo_chu_aph` tự đổi trên site đang chạy khi migrate: người dùng giữ vai trò, quyền, mẫu in mặc định đi theo. Đã chạy thật trên site có dữ liệu cũ.
- **Đợt sau:** chuyển phần gắn vào ERPNext (doc_events, custom field, mẫu in, báo cáo) từ `aphvh` sang `lab9x`; đưa cây kho, nhóm hàng, viết tắt công ty vào `khach.json`; tách luồng chỉ APH có (đơn vị chuyển tiếp TL).
- Nâng cấp site cũ lên 0.7.0: `nang-cap.sh` tự cài `lab9x` vào site trước khi migrate.

## Vai trò từng phần
| Phần | Ở đâu | Việc |
|---|---|---|
| App `aphvh` + bộ cài | repo GitHub | chuẩn thông tư, kho, thu hộ, in ấn, bộ cài bản trắng |
| Cấu hình + phiên bản của khách | `khach/<khach>/khach.json`, `phien-ban.yaml` | công ty, thông tư 133/99, kho, `che_do_du_lieu`, `ngay_chot`; image tag đang chạy |
| Cổng 2 | `.github/workflows/cong-2-site-trang.yml` | với MỌI thư mục khách: dựng site trắng theo config rồi chạy bộ kiểm |
| Phát hành image | `.github/workflows/phat-hanh.yml` | tag `v0.6.2` -> unit test -> **Cổng 2 phải đạt** -> image `ghcr.io/<chủ>/aphvh-erpnext:0.6.2` |
| Khuôn máy chủ | `deploy/khach-hang/` | compose, `dung.sh`, `nang-cap.sh` (tự quay lui), `quay-lui.sh`, `erpctl` |
| Sao lưu tự động | `deploy/cloud/erpnext-backup.*` | 2 lần/ngày lên bucket, giữ 90 ngày |

## Hai chế độ dữ liệu (`che_do_du_lieu` trong khach.json)
| | `tu_nhap` | `import_mot_phan` |
|---|---|---|
| Khách đưa mình | chỉ yêu cầu nghiệp vụ | file mẫu danh mục + số dư đầu kỳ |
| Mình làm | giao site trắng + file mẫu + công cụ kiểm | import thử (không ghi) -> báo cáo đối chiếu -> import thật |
| Khách làm | nhập tất cả | nhập phiếu từ `ngay_chot` trở đi |

Chung cho cả hai: ngày chốt (`ngay_chot`, trước = số dư, sau = phiếu; bắt buộc ở chế độ import), khách tự chạy bộ "Kiểm tra dữ liệu" chỉ đọc, môi trường **UAT** (dữ liệu giả, khách thử và ký biên bản) rồi mới mở **production trắng**. Tài khoản của mình trên production tắt, chỉ bật khi khách cho phép. Dữ liệu gốc khách gửi (chế độ import) xóa theo thời hạn thỏa thuận, giữ báo cáo đối chiếu.

## Khách mới (khoảng 20–30 phút phần dựng, phần lớn là chờ)
1. Sao `khach/aph-vh/` thành `khach/<khach>/`, sửa `khach.json` (tên, viết tắt, `thong_tu`, `nha_may`, `kho_them`, `che_do_du_lieu`, `ngay_chot`) và `phien-ban.yaml`. Mở pull request: Cổng 2 tự chạy cho khách mới.
2. Tạo máy ảo (Ubuntu 22.04/24.04, amd64, 4 GB RAM+, ổ 50 GB, mở cổng 80/443), cài Docker, `docker login ghcr.io` bằng token chỉ đọc gói.
3. Chép `deploy/khach-hang/` và `khach.json` lên máy, chạy `./dung.sh <khach> <phien-ban> ./khach.json [ten-mien]` (tạo `.env` mật khẩu ngẫu nhiên, dựng dịch vụ, tạo site, cài `erpnext` + `aphvh`, nạp cấu hình, chạy bộ kiểm). Dựng **UAT** trước, production sau khi khách ký.
4. Cài sao lưu tự động (`deploy/cloud/README.md`), thêm tên miền (HTTPS tự động).
5. Gửi khách báo cáo `sao-luu/kiem-trien-khai.txt`.

## Phát hành phiên bản mới
1. Sửa code, `python3 -m unittest discover -s aphvh/tests -t .`.
2. Tăng `__version__`, commit, `git tag v<phiên bản>`, `git push --tags`.
3. GitHub Actions: unit test -> Cổng 2 (mọi khách) -> dựng và đẩy image. Không dùng nhãn `latest` khi triển khai.
4. Nâng cấp khách bằng cách sửa `image_tag` trong `khach/<khach>/phien-ban.yaml` (pull request), rồi chạy nâng cấp. Thứ tự: UAT của khách trước, production sau.

## Nâng cấp một khách (không dùng dữ liệu thật của khách để thử)
`./nang-cap.sh <phien-ban-moi>` (trong thư mục khách): (tùy chọn `SNAPSHOT_CMD` chụp snapshot ổ VM) -> sao lưu -> đổi phiên bản -> kéo image -> `migrate` -> bộ kiểm.
**Migrate lỗi hoặc kiểm không đạt thì tự quay lui** (khôi phục bản sao lưu vừa chụp) rồi báo mã lỗi 3 hoặc 4; tắt bằng `TU_QUAY_LUI=0`. Nên nâng cấp ngoài giờ làm việc.

## Quay lui bằng tay
`./quay-lui.sh <thư-mục-sao-lưu>`: đổi lại phiên bản cũ, khôi phục CSDL + tệp (hỏi gõ `CO`; dữ liệu phát sinh sau nâng cấp sẽ mất). `--tu-dong` bỏ hỏi (do `nang-cap.sh` dùng).

## Quy tắc tùy biến giao diện (để nâng cấp không lỗi)
Trên hệ thống của khách (UAT và production) chỉ can thiệp giao diện theo đúng hai nhóm dưới đây. Cả hai lưu trong cơ sở dữ liệu, không sửa mã nguồn, nên `migrate` giữ nguyên và bản sao lưu mang theo.

**Nhóm 1: Không lập trình (No-Code), an toàn nhất**
| Công cụ | Dùng để |
|---|---|
| Customize Form | ẩn/hiện trường, đổi nhãn, đổi vị trí, bắt buộc nhập / chỉ đọc |
| Workspace và Dashboard | đổi trang chủ phân hệ: biểu đồ, thẻ báo cáo, lối tắt |
| Giao diện (màu, logo, font, CSS nhỏ) | chủ đề giao diện cho cả hệ thống |

**Nhóm 2: Lập trình nhẹ (Low-Code)**
| Công cụ | Dùng để |
|---|---|
| Client Script (JavaScript, tạo trên giao diện) | nút tùy chỉnh, đổi màu trường, ẩn/hiện tab theo điều kiện, cảnh báo động |

**Ngoài hai nhóm này thì không làm trên giao diện:** không sửa mã ERPNext hay Frappe, không tạo Server Script, không tạo DocType mới. Nhu cầu cần mã phía máy chủ do mình làm trong app (`aphvh` hoặc `kh_<khach>`), đi qua phát hành image và Cổng 2.

**Ghi chú về "Frappe Theme":** bản ERPNext/Frappe v16 mà mình dùng không có DocType tên "Frappe Theme". Phần giao diện có sẵn là Website Theme (chỉ trang web công khai) và chọn sáng/tối cho từng người dùng. Muốn đổi màu, logo, font cho toàn bộ giao diện làm việc thì cần một app giao diện bổ sung hoặc CSS qua mã app; việc này cần thống nhất riêng, chưa đưa vào quy trình.

**Đưa tùy biến vào quy trình**
1. Khách (hoặc mình, khi khách cho phép) tùy biến trên **UAT** trước, khách thử rồi ký.
2. Tùy biến thuộc phạm vi mình giao cho khách (không phải tinh chỉnh riêng của khách) thì xuất thành fixtures vào app khách (`kh_<khach>`: Custom Field, Property Setter, Client Script, Workspace), commit và phát hành bằng image. Như vậy production, UAT và máy dựng mới đều có cùng một bộ, kiểm tra được ở Cổng 2.
3. Tinh chỉnh riêng của khách làm trực tiếp trên production được phép, không cần phát hành; chỉ nằm trong CSDL và sao lưu.
4. Trước mỗi nâng cấp, chạy trên UAT của khách để xem tùy biến có vỡ không (Client Script gọi trường bị đổi tên là nguyên nhân hay gặp nhất).

## Quyết định giao diện (06/10/2026)
- **Giữ kiểu Frappe**, không bắt chước bố cục MISA AMIS. Nhận diện bằng **bản sắc riêng** của công ty tư vấn.
- **Theme = app riêng `aphvh_theme`**, chỉ ghi đè biến CSS (màu, font, bo góc, mật độ). Không đè bộ chọn, không ghi đè hàm JS nội bộ của Frappe. Logo, tên, trang đăng nhập, mẫu in đặt bằng cấu hình trên giao diện.
- Hai tầng nhận diện: bản sắc chung của mình + lớp riêng từng khách (logo, màu nhấn) khai trong `khach.json`.
- **Cổng 2 kiểm theme:** mọi biến CSS theme dùng phải còn tồn tại trong bản Frappe đang đóng gói; chụp màn hình vài trang chính để so sánh. Lệch thì chặn phát hành.
- Theme là code trong app (đi qua phát hành image), là ngoại lệ có kiểm soát so với hai nhóm No-Code / Low-Code trên giao diện.
- Workspace theo vai trò (trang Tổng quan, lối tắt) làm theo nhu cầu từng khách, không áp thứ tự menu của phần mềm khác.
- **Chưa làm:** app theme, bước kiểm biến + chụp màn hình trong Cổng 2. Cần từ anh: màu chính, font, logo.

## Quy tắc an toàn
- Một khách một máy, một `.env` (quyền 600, không đưa vào Git). `site_config_backup.json` có `encryption_key`: giữ bucket sao lưu riêng tư.
- Không chạy lệnh dọn Docker tổng quát trên máy có khách.
- Bộ cài bản trắng chỉ bỏ tài khoản mẫu khi công ty chưa có bút toán nào.

## Trạng thái kiểm chứng (06/10/2026)
- **Đã chạy thật** (sandbox, site trắng): cấu hình khách -> `ap_dung` -> `kiem_trien_khai` 30/30; kiểm cấu hình có chế độ dữ liệu và ngày chốt (unit test).
- **Chưa chạy thật**: Cổng 2 và workflow phát hành trên GitHub Actions, `dung.sh`, `nang-cap.sh` (kể cả tự quay lui), `quay-lui.sh`, HTTPS Caddy (không có Docker daemon). Diễn tập trước khi dùng cho khách thật.
- **Chưa xây**: bộ kiểm tùy biến chỉ đọc (liệt kê Server Script, DocType mới, Client Script của khách để phát hiện vượt quy tắc), bộ file mẫu nhập, công cụ import có chế độ thử + báo cáo đối chiếu, công cụ "Kiểm tra dữ liệu" cho khách, bộ sinh dữ liệu giả cho UAT, lệnh `khach-moi`, restore thử hằng tuần, cảnh báo.
- **Cần anh chốt cho khách đầu tiên**: `che_do_du_lieu` (hiện đặt `tu_nhap`), `ngay_chot`, tên miền, nhà cung cấp cloud.

## Diễn tập (làm một lần, trên MacBook hoặc máy thử)
`HTTP_BIND=127.0.0.1 HTTP_PORT=18090 ERP_HOME=$HOME/erp-thu ./dung.sh thu <phien-ban> ./khach.json`, rồi `./nang-cap.sh` lên phiên bản kế tiếp (thử cả ca lỗi: đặt phiên bản không tồn tại để xem tự quay lui), và `./quay-lui.sh`. Cả ba đạt mới dùng cho khách thật.
