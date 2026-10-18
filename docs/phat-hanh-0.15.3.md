# Phát hành 0.15.3 — vận hành giao nhận và bộ mẫu chứng từ

## Trạng thái phát hành — 18/10/2026

Tag đã được chủ dự án đẩy; [workflow39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) **đạt toàn bộ**, image0.15.3 đã phát hành với manifest digest `sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`, nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Đã đọc log đẩy image và artifact UAT227 PASS/0 FAIL/Cổng3 khớp. Người vận hành đã gửi log **`=== XONG 0.15.3: ĐẠT ===`** từ VM cùng digest; production0.15.3 đã xác nhận. Các lệnh tag/triển khai phía dưới là quy trình tham chiếu đã hoàn thành, không chạy lại. Bước hiện tại là nghiệm thu mẫu in và nhân sự thực tế.

Đích: site `frontend`, VM `erpnext-prod`, Compose `~/erp/aph-vh`, project `erp-aph-vh`. Production hiện đã xác nhận là0.15.3 với digest nêu trên; bản trước0.15.2 là mốc quay lui có điều kiện. Codex không có SSH; bằng chứng triển khai là log người vận hành.

## Phạm vi

- Thông tin giao nhận theo đợt và dấu người/thời điểm xuất; in lại/tổng hợp dùng đúng dữ liệu từng phiếu, giữ tương thích phiếu cũ/phiếu trả.
- Xuất ngay trong Dialog khi có quyền: tạo và xác nhận cả đợt nguyên tử; retry sau mất phản hồi không xuất/ghi nợ lần hai.
- Vòng xử lý chênh lệch ngay trên phiếu nguồn, có người phụ trách, hạn, căn cứ và lịch sử; không tự tạo chứng từ điều chỉnh sổ.
- Phiếu nhanh A5 ngang hai liên theo mẫu chủ dự án, giá bán thuần, dấu nháp/bản sao và năm vị trí ký.
- Bảy mẫu chuẩn theo chế độ của từng đơn vị: APH–TT133, VH–TT99, Minh Khang–mẫu nội bộ theo TT152, TL–mẫu quản trị nội bộ. Quy chế tại `docs/quy-che-bieu-mau-chung-tu.md` còn là dự thảo để doanh nghiệp ban hành.

## Đóng gói và migration

kh_aph 0.15.3, lab9x 0.2.11; nền giữ ERPNext 16.51.1/Frappe 16.52.0 theo digest hiện có. Giữ 21 cờ, không truyền cờ mới khi triển khai. Migrate đồng bộ các Print Format theo modified mới; bộ cài chuẩn thêm/cập nhật ô thông tin giao nhận. Python/hook/JS mới nằm trong image; thay đồng bộ service và clear-cache theo script. Không sửa core, không tự thay số dư/sổ lịch sử hoặc chế độ kế toán của Company.

## Bằng chứng

Mã nghiệp vụ `7c2217e8737e96700fa050aac446bb3591a830a8` đã đạt bốn cổng, UAT227 PASS/0 FAIL và cục bộ302+108. SHA đóng gói0.15.3/lab9x0.2.11: `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`; cục bộ302+108 đạt. [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858) và [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872) đều đạt trên mã đóng gói, UAT227 PASS/0 FAIL. Đã đọc artifact xác nhận0.15.3/0.2.11; core63.508 tệp nguyên vẹn; xem PDF hai trang A5 và hai trang tổng hợp A4. Cổng3 so schema/cờ với site mới, nâng/quay lui và ca lỗi tự quay lui đều khớp, giữ bảo trì; nền CI chưa có phát sinh sổ nên vẫn bắt buộc diễn tập bản sao production hiện tại. Commit sau mã đóng gói chỉ chốt tài liệu, không thay SHA gắn tag.

## Phát hành

Theo AGENTS.md, chủ dự án tự gắn tag `v0.15.3` vào đúng SHA đóng gói đã đủ cổng. Workflow Phát hành image phải đạt và có digest image mới rồi mới chuyển sang bước VM. Không ghi đè tag/image 0.15.2, không dùng workflow_dispatch trên nhánh thay cho tag bất biến.

Sau khi cả bốn cổng trên đều đạt, chạy trên MacBook (checkout của chat):

```bash
cd /Users/macbook/Documents/Codex/2026-10-17/ghcr-io-tienduongmarcom-kh-aph-erpnext/work/aphvh &&
git tag v0.15.3 96a7ef0352b45c31b8d26428aad3ddbcafeeb37c &&
git push origin v0.15.3
```

Tag trỏ rõ SHA đã kiểm; không gắn theo HEAD tài liệu hoặc merge commit chưa chạy kiểm trên đúng SHA. Main phải chứa commit nguồn này để giữ nguồn phát hành nhất quán; kiểm bằng `git merge-base --is-ancestor 96a7ef0352b45c31b8d26428aad3ddbcafeeb37c origin/main` sau khi PR #5 được gộp.

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
