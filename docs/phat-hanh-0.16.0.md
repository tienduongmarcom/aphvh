# Phát hành 0.16.0 — tiền (đợt 2), nhà máy (đợt 3), giao diện theo công việc (UX-01)

Chủ dự án yêu cầu đưa lên production ngày 20/10/2026. Đích: site `frontend`, VM `erpnext-prod`, Compose `~/erp/aph-vh`.
Production hiện 0.15.3 (digest `sha256:330607a2…`), là mốc quay lui.

## Phạm vi (chuỗi PR #9 → #19, chưa gộp main)

- Đợt 2 tiền (PR #9–#16): in lại A5, người giữ tiền, chốt ca tiền mặt, bàn giao tiền, xử lý lệch/hoàn tiền, thu quầy/quỹ nhà
  máy, tiền cá nhân, chốt ngày.
- Đợt 3 nhà máy: nhận theo đơn mua (PR #17), chờ định giá theo đơn mua (PR #18), nhận chuyến chuyển đến / chuyển đi (NM01c/NM05),
  ghi sản xuất / đóng gói / đổi bao một lần (NM02–04) — PR #19.
- UX-01: bốn Workspace "Việc …" song song Workspace cũ, việc tiếp theo trên chứng từ, tìm khách SĐT/MST, thu tiền 5 bước,
  Module Profile theo nhóm (chưa gán ai), thông báo có việc cần làm.

kh_aph 0.16.0, lab9x 0.2.11 (không đổi); nền ERPNext 16.51.1 / Frappe 16.52.0 giữ nguyên digest.

## Cờ

21 cờ đang bật giữ nguyên. Bảy cờ mới (mặc định tắt, đã kiểm bật trong Cổng 3):
`kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving
kh_aph_factory_production kh_aph_ux_task_first`. Lệnh dưới bật cả bảy; muốn bật dần thì bỏ bớt tên cờ ở CẢ hai lệnh.

## Bằng chứng

Điền SHA đóng gói và 4 run sau khi cổng đạt (mục "Trạng thái" bên dưới). Tag chỉ gắn vào SHA đã đủ 4 cổng.

## 1. Gắn tag (máy của anh, sau khi 4 cổng đạt)

```bash
git fetch origin && git tag v0.16.0 <SHA_DONG_GOI> && git push origin v0.16.0
```

Workflow "Phát hành image" phải đạt và có digest image 0.16.0 rồi mới sang bước 2.

## 2. Diễn tập rồi triển khai (SSH vào erpnext-prod, dừng nhập liệu trong lúc chạy)

```bash
cd ~/trien-khai &&
git fetch https://github.com/tienduongmarcom/aphvh.git tag v0.16.0 &&
git checkout --detach v0.16.0 &&
bash deploy/release/dien_tap_ban_sao.sh 0.16.0 kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving kh_aph_factory_production kh_aph_ux_task_first &&
bash deploy/release/trien_khai_frontend.sh 0.16.0 kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving kh_aph_factory_production kh_aph_ux_task_first
```

Danh sách cờ ở hai lệnh phải giống hệt (dấu diễn tập ràng buộc cờ). Lỗi thì script giữ bảo trì và in lệnh quay lui; không tự mở
site. Đã mở nhập liệu rồi thì không restore làm mất giao dịch mới.

## 3. Sau triển khai

Gửi log có `=== XONG 0.16.0: ĐẠT ===` và digest. Tải lại Desk. Workspace mới đã có nhưng **chưa ai được đặt mặc định**: áp cho
từng người bằng `kh_aph.ux_task.ap_dung_nguoi_dung` (chạy thử trước, quản trị hệ thống). Nghiệm thu người thật/máy in theo
`docs/nghiem-thu-tong-the.md`, `docs/ux-0-phieu-do.md`.
