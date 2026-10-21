# Phát hành bản tối ưu giao diện0.16.3

**Đã triển khai21/10/2026 theo log người vận hành:** diễn tập10210126238079 so sổ KHỚP, sau đó `=== XONG 0.16.3: ĐẠT ===`; digest khớp image nêu dưới. Các bước phát hành/nâng cấp trong tài liệu này đã hoàn tất, giữ làm hồ sơ, không chạy lại chỉ để kiểm. Nghiệm thu nghiệp vụ thực tế vẫn để cuối.

**Mốc21/10/2026:** chủ dự án đã gắn tag, workflow39518896902 success; image0.16.3 đã có, digest `sha256:a252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95` (log phát hành và registry khớp). Bước1 dưới đây đã xong, không gắn lại tag. Tiếp tục bước2 trên SSH máy chủ. Production chưa được xác nhận nâng0.16.3.

PR #26 đã gộp vào main, commit `a1f95b062f2ff7334ed36c176dfb742bf828974a`. Mã app giữ nguyên so với12d9d24 đã đạt bốn cổng; phần sau chỉ hồ sơ. Bản đang chạy theo xác nhận vẫn0.16.2, digest34a32f71…,28cờ. Không có cờ mới; không chạy setup_uat trên production. Nền ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11 giữ nguyên.

## 1. Trên Mac — chủ dự án gắn tag

AGENTS.md quy định: **Chủ dự án tự gắn tag**. Tag vào đúng commit đã gộp, không dùng HEAD của một nhánh khác:

```bash
cd /Users/macbook/Documents/Codex/2026-10-17/ghcr-io-tienduongmarcom-kh-aph-erpnext/work/aphvh &&
git fetch origin main &&
git tag v0.16.3 a1f95b062f2ff7334ed36c176dfb742bf828974a &&
git push origin v0.16.3
```

Nếu tag đã tồn tại thì dừng đối chiếu nguồn, không xóa hoặc ghi đè tag. Workflow “Phát hành image” tự chạy các cổng và đẩy image khi đạt. Chờ workflow thành công toàn bộ và có image0.16.3, ghi lại digest; chưa chạy lệnh nâng máy chủ khi image chưa có. Một run kiểm ứng viên xanh không thay kết quả phát hành từ tag.

## 2. Trên máy chủ — diễn tập bản sao dữ liệu thực

Đăng nhập SSH `tienduongmarcom@erpnext-prod`, site `frontend`, Compose `~/erp/aph-vh`. Kiểm đúng máy/tài khoản trước khi thao tác; thực hiện trong phiên tmux để tránh SSH rớt. Nếu đang ngoài tmux, chạy `tmux new -A -s nang-cap-0163`; khi đã ở trong phiên thì không tạo phiên lồng. Nếu SSH ngắt, kết nối lại rồi chạy `tmux attach -t nang-cap-0163`, không chạy thêm lượt song song. **Thư mục ~/trien-khai là trên máy chủ**, không phải thư mục Mac.

```bash
cd ~/trien-khai &&
git fetch -q https://github.com/tienduongmarcom/aphvh.git tag v0.16.3 &&
git checkout -q --detach v0.16.3 &&
bash deploy/release/dien_tap_ban_sao.sh 0.16.3
```

Chỉ tiếp tục khi báo `DIỄN TẬP 0.16.3: ĐẠT`, so sổ khớp và có dấu còn hạn12giờ, ràng buộc đúng image/commit/khach.json/cờ. Không truyền thêm cờ vì bản này không có cờ mới. Lỗi hoặc dữ liệu không khớp thì giữ log, dừng xử lý nguyên nhân.

## 3. Trên máy chủ — nâng trong cửa sổ bảo trì

Thông báo ngừng nhập liệu trước khi chạy. Dùng chính checkout/tag và image vừa diễn tập:

```bash
cd ~/trien-khai &&
bash deploy/release/trien_khai_frontend.sh 0.16.3
```

Bộ triển khai thực hiện bảo trì, sao lưu, nâng/bộ cài, so sổ và kiểm tra trước mở lại. Chỉ ghi nhận thành công khi dòng cuối `=== XONG 0.16.3: ĐẠT ===`; lưu log, digest và dấu diễn tập. Nếu lỗi, làm theo thông báo giữ bảo trì/quay lui và `deploy/release/TRIEN_KHAI_FRONTEND.md`; không tự mở site hoặc chạy lặp bỏ qua dấu.

## 4. Kiểm sau nâng và hồ sơ

- Kiểm app/backend/worker/scheduler đúng image0.16.3 và28cờ; ghi lại digest thực tế. Không suy version chỉ từ tag hoặc trang GitHub.
- Đăng xuất/đăng nhập lại: năm khu mới theo quyền, tên chung Vận hành; tài khoản có tùy chỉnh riêng có thể giữ bố trí riêng. Kiểm tên/mã/SĐT/địa chỉ khách và mã/tên hàng, lối thu tiền/in.
- Không dùng giao dịch giả để thử trên dữ liệu thật. Nghiệm thu nghiệp vụ với nhân sự, hàng/tồn và máy in thật vẫn gom cuối theo `docs/huong-dan-giao-dien-0163.md`.
- Cập nhật cả `docs/ban-giao.md`, `deploy/release/TRANG_THAI.md` và mốc image trong `khach/aph-vh/phien-ban.yaml` sau khi có bằng chứng thực tế. Không sửa trạng thái production trước xác nhận.

Rollback cần image0.16.2 và snapshot database/public/private tương ứng trước nâng. Không restore snapshot cũ sau khi có giao dịch mới nếu chưa có phương án xử lý các giao dịch đó. Tắt cờ UX không tự phục hồi mọi cấu hình Sidebar hoặc metadata.
