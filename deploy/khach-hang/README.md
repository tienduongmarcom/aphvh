# Quy trình triển khai cho khách (hướng A: mỗi khách một máy + Docker image)

Khách đầu tiên: **An Phú Hưng - Vĩnh Hưng** (`khach/aph-vh/`). Nguyên tắc: **mình không bao giờ chạm dữ liệu thật của khách**; mình giao hệ thống đúng cùng công cụ để khách tự nhập và tự kiểm.

## Vai trò từng phần
| Phần | Ở đâu | Việc |
|---|---|---|
| App `aphvh` + bộ cài | repo GitHub | chuẩn thông tư, kho, thu hộ, in ấn, bộ cài bản trắng |
| Cấu hình + phiên bản của khách | `khach/<khach>/khach.json`, `phien-ban.yaml` | công ty, thông tư 133/99, kho, `che_do_du_lieu`, `ngay_chot`; image tag đang chạy |
| Cổng 2 | `.github/workflows/cong-2-site-trang.yml` | với MỌI thư mục khách: dựng site trắng theo config rồi chạy bộ kiểm |
| Phát hành image | `.github/workflows/phat-hanh.yml` | tag `v0.6.1` -> unit test -> **Cổng 2 phải đạt** -> image `ghcr.io/<chủ>/aphvh-erpnext:0.6.1` |
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

## Quy tắc an toàn
- Một khách một máy, một `.env` (quyền 600, không đưa vào Git). `site_config_backup.json` có `encryption_key`: giữ bucket sao lưu riêng tư.
- Không chạy lệnh dọn Docker tổng quát trên máy có khách.
- Bộ cài bản trắng chỉ bỏ tài khoản mẫu khi công ty chưa có bút toán nào.

## Trạng thái kiểm chứng (06/10/2026)
- **Đã chạy thật** (sandbox, site trắng): cấu hình khách -> `ap_dung` -> `kiem_trien_khai` 30/30; kiểm cấu hình có chế độ dữ liệu và ngày chốt (unit test).
- **Chưa chạy thật**: Cổng 2 và workflow phát hành trên GitHub Actions, `dung.sh`, `nang-cap.sh` (kể cả tự quay lui), `quay-lui.sh`, HTTPS Caddy (không có Docker daemon). Diễn tập trước khi dùng cho khách thật.
- **Chưa xây**: bộ file mẫu nhập, công cụ import có chế độ thử + báo cáo đối chiếu, công cụ "Kiểm tra dữ liệu" cho khách, bộ sinh dữ liệu giả cho UAT, lệnh `khach-moi`, restore thử hằng tuần, cảnh báo.
- **Cần anh chốt cho khách đầu tiên**: `che_do_du_lieu` (hiện đặt `tu_nhap`), `ngay_chot`, tên miền, nhà cung cấp cloud.

## Diễn tập (làm một lần, trên MacBook hoặc máy thử)
`HTTP_BIND=127.0.0.1 HTTP_PORT=18090 ERP_HOME=$HOME/erp-thu ./dung.sh thu <phien-ban> ./khach.json`, rồi `./nang-cap.sh` lên phiên bản kế tiếp (thử cả ca lỗi: đặt phiên bản không tồn tại để xem tự quay lui), và `./quay-lui.sh`. Cả ba đạt mới dùng cho khách thật.
