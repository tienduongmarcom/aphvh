# Quy trình triển khai cho khách (hướng A: mỗi khách một máy + Docker image)

## Vai trò từng phần
| Phần | Ở đâu | Việc |
|---|---|---|
| App `aphvh` + bộ cài | repo GitHub, nhánh phát hành | chuẩn thông tư, kho, thu hộ, in ấn, bộ cài bản trắng |
| Phát hành image | `.github/workflows/phat-hanh.yml` | tag `v0.6.0` -> test -> dựng image -> `ghcr.io/<chủ>/aphvh-erpnext:0.6.0` |
| Cấu hình khách | `deploy/khach/<khach>.json` (mẫu: `mau-aph-vh.json`) | công ty, thông tư 133/99, nhà máy, kho thêm |
| Khuôn máy chủ | `deploy/khach-hang/` | compose, `dung.sh`, `nang-cap.sh`, `quay-lui.sh`, `erpctl` |
| Sao lưu tự động | `deploy/cloud/erpnext-backup.*` | 2 lần/ngày lên bucket, giữ 90 ngày |

## Khách mới (khoảng 20–30 phút, phần lớn là chờ)
1. Sao `deploy/khach/mau-aph-vh.json` thành `deploy/khach/<khach>.json`, sửa tên công ty, viết tắt, `thong_tu` (133 hoặc 99), `nha_may`, `kho_them`. Commit.
2. Tạo máy ảo (Ubuntu 22.04/24.04, amd64, 4 GB RAM trở lên, ổ 50 GB, mở cổng 80/443), cài Docker, `docker login ghcr.io` bằng token chỉ đọc gói.
3. Chép thư mục `deploy/khach-hang/` và file cấu hình lên máy, rồi chạy:
   `./dung.sh <khach> <phien-ban> ./<khach>.json [ten-mien]`
   Script tự: tạo `.env` (mật khẩu CSDL ngẫu nhiên), dựng dịch vụ, tạo site, cài `erpnext` + `aphvh`, nạp cấu hình khách, chạy bộ kiểm, in `== XONG` hoặc `== CHƯA ĐẠT`.
4. Cài sao lưu tự động (xem `deploy/cloud/README.md`), thêm tên miền (truyền tham số tên miền để bật HTTPS tự động).
5. Gửi khách báo cáo `sao-luu/kiem-trien-khai.txt`; nhập dữ liệu thật (số dư đầu kỳ, danh mục), đối chiếu với sổ cũ.

## Phát hành phiên bản mới
1. Sửa code, `python3 -m unittest discover -s aphvh/tests -t .`.
2. Tăng `__version__` trong `aphvh/__init__.py`, commit, `git tag v<phiên bản>`, `git push --tags`.
3. GitHub Actions dựng và đẩy image. Không dùng nhãn `latest` để triển khai.

## Nâng cấp một khách
`./nang-cap.sh <phien-ban-moi>` (trong thư mục khách): sao lưu -> đổi phiên bản -> kéo image -> `migrate` -> bộ kiểm.
Lỗi ở bước nào thì script dừng và in lệnh quay lui. Nên nâng cấp ngoài giờ làm việc; thử trên máy thử trước.

## Quay lui
`./quay-lui.sh <thư-mục-sao-lưu>`: đổi lại phiên bản cũ và khôi phục CSDL + tệp từ bản sao lưu trước nâng cấp (hỏi xác nhận; dữ liệu phát sinh sau nâng cấp sẽ mất).

## Quy tắc an toàn
- Một khách một máy, một `.env` (quyền 600, không đưa vào Git). `site_config_backup.json` có `encryption_key`: giữ bucket sao lưu riêng tư.
- Không chạy lệnh dọn Docker tổng quát trên máy có khách.
- Bộ cài bản trắng chỉ bỏ tài khoản mẫu khi công ty chưa có bút toán nào.

## Trạng thái kiểm chứng (06/10/2026)
- Đã chạy thật trên site trắng: cấu hình khách -> `ap_dung` -> `kiem_trien_khai` (30/30 đạt, chạy lại không tạo thêm).
- **Chưa chạy thật**: workflow GitHub Actions, `dung.sh`, `nang-cap.sh`, `quay-lui.sh`, HTTPS Caddy (máy phát triển không có Docker daemon). Phải diễn tập trên máy thử trước khi dùng cho khách thật (xem mục dưới).

## Diễn tập (làm một lần, trên MacBook 8081 hoặc máy thử)
`HTTP_BIND=127.0.0.1 HTTP_PORT=18090 ERP_HOME=$HOME/erp-thu ./dung.sh thu <phien-ban> ./khach.json` rồi `./nang-cap.sh` lên một phiên bản kế tiếp và `./quay-lui.sh`. Chỉ khi cả ba chạy đạt mới dùng cho khách thật.
