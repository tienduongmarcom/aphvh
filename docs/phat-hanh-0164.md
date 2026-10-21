# Phát hành bản sửa địa chỉ và số điện thoại0.16.4

Production vẫn0.16.3, digest `sha256:a252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95`. PR #30 đã gộp **1dffa623dc28d239321b7c9cd249968def402123**, mã app giữ nguyên c9433f3 đã đạt bốn cổng (xem đầu docs/ban-giao.md). Chưa có tag/image0.16.4 khi lập hồ sơ. Không đổi schema, quyền,28cờ, core hoặc logic ghi sổ.

## 1. Mac: chủ dự án gắn tag

Theo AGENTS.md, chủ dự án tự gắn tag đúng mã đã gộp:

```bash
cd /Users/macbook/Documents/Codex/2026-10-17/ghcr-io-tienduongmarcom-kh-aph-erpnext/work/aphvh &&
git fetch origin main &&
git tag v0.16.4 1dffa623dc28d239321b7c9cd249968def402123 &&
git push origin v0.16.4
```

Tag đã tồn tại thì đối chiếu nguồn, không xóa/ghi đè. Chờ workflow Phát hành image thành công toàn bộ, xác minh image0.16.4 và digest. Chỉ sau đó làm bước máy chủ; run kiểm ứng viên không thay run phát hành.

## 2. SSH máy chủ: vào tmux, diễn tập bản sao

Đúng tài khoản `tienduongmarcom@erpnext-prod`, site frontend, Compose `~/erp/aph-vh`. Nếu đang ngoài tmux:

```bash
tmux new -A -s nang-cap-0164
```

Đã ở trong tmux thì không tạo phiên lồng. SSH rớt: đăng nhập lại rồi `tmux attach -t nang-cap-0164`, không chạy thêm lượt song song. Trong phiên đó:

```bash
cd ~/trien-khai &&
git fetch -q https://github.com/tienduongmarcom/aphvh.git tag v0.16.4 &&
git checkout -q --detach v0.16.4 &&
bash deploy/release/dien_tap_ban_sao.sh 0.16.4
```

Thư mục này ở VM, không ở Mac. Chỉ tiếp tục sau DIỄN TẬP0.16.4: ĐẠT, so sổ khớp, dấu còn hạn12giờ/đúng image–commit–khach.json–cờ. Không cờ mới, không setup_uat trên production. Lỗi thì giữ log và xử lý nguyên nhân theo runbook.

## 3. Trong tmux: nâng sau diễn tập đạt

Thông báo ngừng nhập liệu trước khi chạy, cùng checkout/image đã diễn tập:

```bash
cd ~/trien-khai &&
bash deploy/release/trien_khai_frontend.sh 0.16.4
```

Chỉ xác nhận khi dòng cuối `=== XONG 0.16.4: ĐẠT ===`; lưu digest/log. Thủ tục bảo trì, sao lưu, so sổ, tự quay lui theo `deploy/release/TRIEN_KHAI_FRONTEND.md`. Không tự mở bảo trì sau lỗi hoặc chạy bỏ qua dấu.

Sau nâng, tải lại giao diện và kiểm chỉ đọc tên/mã/địa chỉ/SĐT của khách đã có liên kết. Không nhập lại địa chỉ chỉ để chữa lỗi này, không ghi giao dịch giả trên production. Thêm/sửa số trong nghiệp vụ thật rồi tải lại đơn sẽ đọc hồ sơ hiện tại; chứng từ lịch sử giữ nguyên. Nghiệm thu nhân sự/hàng/tồn/máy in thật vẫn để cuối.

Cập nhật docs/ban-giao.md, deploy/release/TRANG_THAI.md và khach/aph-vh/phien-ban.yaml chỉ sau log/digest triển khai thực. Quay lui về image0.16.3 với snapshot database/public/private ngay trước nâng; không restore snapshot cũ sau giao dịch mới khi chưa xử lý phần phát sinh.
