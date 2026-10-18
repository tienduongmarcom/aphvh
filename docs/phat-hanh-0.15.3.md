# Ứng viên 0.15.3 — vận hành giao nhận và bộ mẫu chứng từ

Đích: site `frontend`, VM `erpnext-prod`, Compose `~/erp/aph-vh`, project `erp-aph-vh`. Production hiện đã xác nhận là 0.15.2, digest `sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333`. Chưa ghi nhận triển khai 0.15.3.

## Phạm vi

- Thông tin giao nhận theo đợt và dấu người/thời điểm xuất; in lại/tổng hợp dùng đúng dữ liệu từng phiếu, giữ tương thích phiếu cũ/phiếu trả.
- Xuất ngay trong Dialog khi có quyền: tạo và xác nhận cả đợt nguyên tử; retry sau mất phản hồi không xuất/ghi nợ lần hai.
- Vòng xử lý chênh lệch ngay trên phiếu nguồn, có người phụ trách, hạn, căn cứ và lịch sử; không tự tạo chứng từ điều chỉnh sổ.
- Phiếu nhanh A5 ngang hai liên theo mẫu chủ dự án, giá bán thuần, dấu nháp/bản sao và năm vị trí ký.
- Bảy mẫu chuẩn theo chế độ của từng đơn vị: APH–TT133, VH–TT99, Minh Khang–mẫu nội bộ theo TT152, TL–mẫu quản trị nội bộ. Quy chế tại `docs/quy-che-bieu-mau-chung-tu.md` còn là dự thảo để doanh nghiệp ban hành.

## Đóng gói và migration

kh_aph 0.15.3, lab9x 0.2.11; nền giữ ERPNext 16.51.1/Frappe 16.52.0 theo digest hiện có. Giữ 21 cờ, không truyền cờ mới khi triển khai. Migrate đồng bộ các Print Format theo modified mới; bộ cài chuẩn thêm/cập nhật ô thông tin giao nhận. Python/hook/JS mới nằm trong image; thay đồng bộ service và clear-cache theo script. Không sửa core, không tự thay số dư/sổ lịch sử hoặc chế độ kế toán của Company.

## Bằng chứng

Mã nghiệp vụ `7c2217e8737e96700fa050aac446bb3591a830a8` đã đạt bốn cổng, UAT227 PASS/0 FAIL và cục bộ302+108. Chi tiết ở đầu `docs/ban-giao.md`. Đổi nhãn phiên bản tạo SHA đóng gói mới; phải kiểm lại cả bốn cổng trên SHA đó trước gắn tag. Không dùng các cổng mã cũ làm bằng chứng SHA đóng gói mới.

## Phát hành

Theo AGENTS.md, chủ dự án tự gắn tag `v0.15.3` vào đúng SHA đóng gói đã đủ cổng. Workflow Phát hành image phải đạt và có digest image mới rồi mới chuyển sang bước VM. Không ghi đè tag/image 0.15.2, không dùng workflow_dispatch trên nhánh thay cho tag bất biến.

## Diễn tập và triển khai trên VM

Chỉ chạy trong phiên SSH của `tienduongmarcom@erpnext-prod`, sau khi image 0.15.3 đã phát hành đạt. Không chạy lệnh này trong terminal MacBook.

```bash
cd ~/trien-khai &&
git fetch https://github.com/tienduongmarcom/aphvh.git tag v0.15.3 &&
git checkout --detach v0.15.3 &&
bash deploy/release/dien_tap_ban_sao.sh 0.15.3 &&
bash deploy/release/trien_khai_frontend.sh 0.15.3
```

`&&` giữ điều kiện diễn tập phải đạt mới nâng thật. Diễn tập dùng bản sao dữ liệu hiện tại, tách ổ/mạng/Redis/MariaDB; không thay bằng kết quả CI nền chưa có phát sinh sổ. Triển khai bật bảo trì trước sao lưu, dừng worker/lịch chạy, thay image, migrate/bộ cài, so tổng/đếm/chi tiết và chỉ mở lại khi đạt. Cần dừng nhập liệu trong cửa sổ này.

Nếu lỗi, giữ bảo trì và đọc bằng chứng/lệnh quay lui do script in ra. Không tự mở site hoặc chạy lại mù. Sau khi đã mở nhập liệu thì không restore backup làm mất giao dịch mới; đối soát trước khi chọn cách khắc phục.

## Sau triển khai

Chỉ cập nhật `khach/aph-vh/phien-ban.yaml` khi có log `=== XONG 0.15.3: ĐẠT ===` và digest đúng image phát hành. Kiểm các phiếu/danh mục hiện có, tải lại Desk và nghiệm thu máy in A5/A4 theo `docs/nghiem-thu-mau-in-20261018.md`. Việc chủ dự án yêu cầu triển khai chưa phải bằng chứng nghiệm thu máy in hoặc toàn bộ nghiệp vụ thật.
