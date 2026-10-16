# Ứng viên nâng nền ERPNext 16.51.1 — 16/10/2026

Chủ dự án yêu cầu gộp bản vá trong đợt phát triển tiếp. Nhánh nền riêng `thu/erpnext-v16.51.1`, app ứng viên 0.14.4.
Không thay `khach/aph-vh/phien-ban.yaml` vì đó là bản đang chạy; không gắn tag, không đẩy image, không truy cập VM.

## Nguồn và phạm vi

- Release: https://github.com/frappe/erpnext/releases/tag/v16.51.1
- Bản 16.51.1 sửa Stock Closing Entry (chỉ ghi số dư phiếu xác nhận, bỏ phiếu hủy, kiểm ngày/công ty) và lọc/tồn đầu kỳ/tuổi tồn trong Stock Balance; PR https://github.com/frappe/erpnext/pull/60793.
- Nâng từ 16.50.0 đi qua cả 16.51.0: https://github.com/frappe/erpnext/releases/tag/v16.51.0. Có thay đổi giá thành nhiều thành phẩm/repost, Manufacture/Repack với BOM, quyền Company, trả hàng/ứng trước, phiếu mua ngoại tệ, khóa kỳ. Không coi đây là thay duy nhất của 16.51.1.
- Docker Registry xác minh 16/10: index `sha256:a856e7f65c7bfc9cfa2e74f95b62e11d37190c380d958cbf3bea5d05e2ec9268`; Linux amd64 manifest `sha256:32a3bd423f77b8bb63c5df95129a5f69a0bb9cc27a6e117d2623789d3a4836be`.
- Không suy phiên bản Frappe từ tag ERPNext. CI kiểm `erpnext.__version__ == 16.51.1` và in `bench version` của đúng image.

## Kiểm và bằng chứng

1. Cổng 1: hai bộ unittest trong AGENTS.md; công cụ core có ca thêm/xóa/sửa, quyền tệp, symlink, cache, thư mục rỗng.
2. UAT: giữ toàn bộ bộ HTTP/Desk hiện có, đặc biệt cost/quantity/dispatch/funds/factory. Không hạ số PASS hoặc bỏ assertion.
3. Gate `CORE_IMAGE_INTEGRITY`: chạy script chỉ đọc trên image nền và ứng viên trước khi cài site; so tên tệp, SHA256, mode và đích symlink của `apps/frappe`, `apps/erpnext`. Chỉ bỏ metadata `.git`, Python `__pycache__`, `.pyc`, `.pyo`. Không bỏ source, node_modules hay public assets. Symlink không được theo ra ngoài.
4. Artifact UAT giữ `core-base.json`, `core-candidate.json`, `core-integrity-evidence.txt`, `base-versions-evidence.txt` cùng SHA nguồn.
5. Cổng 2 dựng mới; Cổng 3 nâng từ 0.14.3 digest production và phục hồi thật. Giữ nguồn production cũ trong Cổng 3.
6. Trước phát hành: thêm ca đặc hiệu Stock Closing Entry + Stock Balance (lọc kho/mã và phiếu hủy), kiểm thay đổi native tính giá nhiều thành phẩm với kg-v4. Chưa có bằng chứng những ca mới này ở thời điểm tạo nhánh.

Gate checksum chứng minh core ứng viên giống image nền, không chứng minh upstream không có lỗi hoặc core container production chưa bị sửa. Kiểm runtime production là bước riêng chỉ đọc.

## Tiếp quản

Đọc kết quả Actions trên SHA đầu nhánh; giữ run FAIL. Nếu CI lỗi do thay đổi native, thêm ca tái hiện rồi sửa extension, không sửa core. Chỉ chốt nâng nền sau khi các gate đạt. Khi phát hành theo AGENTS.md: chủ dự án gắn tag; diễn tập bản sao tách biệt rồi quy trình production có bảo trì/backup/so sổ/rollback.
