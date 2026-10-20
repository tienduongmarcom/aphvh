# Phát hành 0.16.2 — mã và tên hàng, điện thoại/địa chỉ khách trên đơn bán chung

Production 0.16.1 (mốc quay lui). Không thêm cờ.

- 0.16.1 bật hiện tên trong ô Mã hàng: sai ý chủ dự án. 0.16.2 tắt lại cho Mặt hàng (ô Mã hàng hiện mã) và thêm cột "Tên hàng"
  trên dòng đơn bán chung. Khách hàng / nhà cung cấp vẫn hiện tên.
- Đơn bán chung: chọn khách xong hiện "Điện thoại khách" (mobile_no) và "Địa chỉ khách" (địa chỉ chính) — chỉ đọc, lấy từ hồ sơ khách.
  Khách chưa có địa chỉ chính / số điện thoại thì ô để trống: bổ sung trên hồ sơ khách.
- Danh sách gợi ý khi chọn khách có thêm số điện thoại để phân biệt khách trùng tên.

Không đổi logic ghi kho, công nợ, tiền.

## Triển khai (chạy trong tmux)
```bash
tmux new -s trienkhai
git fetch origin && git tag v0.16.2 <SHA_DONG_GOI> && git push origin v0.16.2   # máy anh, sau 4 cổng
cd ~/trien-khai && git fetch https://github.com/tienduongmarcom/aphvh.git tag v0.16.2 && git checkout --detach v0.16.2 &&
bash deploy/release/dien_tap_ban_sao.sh 0.16.2 kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving kh_aph_factory_production kh_aph_ux_task_first &&
bash deploy/release/trien_khai_frontend.sh 0.16.2 kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving kh_aph_factory_production kh_aph_ux_task_first
```
