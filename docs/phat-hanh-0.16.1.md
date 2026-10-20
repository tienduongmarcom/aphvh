# Phát hành 0.16.1 — dễ dùng hơn cho nhân viên (không đổi nghiệp vụ)

Production hiện 0.16.0 (digest `sha256:ce8db011…`), là mốc quay lui. Không thêm cờ; 28 cờ giữ nguyên.

## Thay đổi
- Đơn bán chung: ngày giao dự kiến mặc định hôm nay; Dialog lập phiếu xuất mặc định "Khách đến lấy".
- Màn hình chính "Việc …" → "Bàn bán hàng / Bàn kho / Bàn tiền và công nợ / Bàn nhà máy"; "Hôm nay cần xử lý"; "Bước tiếp theo".
  Workspace tên cũ ẩn (không xóa); Module Profile tên cũ chưa ai dùng thì xóa.
- 24 tên chứng từ tiếng Việt không có chữ APH; 23 tên báo cáo có dấu; nhãn Sổ xuất nhập bao tiếng Việt.
- Ngày nhận thực tế / ngày thực nhận tiền / ngày xử lý mặc định hôm nay.
- Ô chọn khách, mặt hàng, nhà cung cấp hiện tên sau khi chọn (show_title_field_in_link), vẫn lưu mã.

Không đổi logic ghi kho, công nợ, tiền. Cổng 3 kiểm nâng cấp từ 0.16.0.

## Triển khai
```bash
git fetch origin && git tag v0.16.1 <SHA_DONG_GOI> && git push origin v0.16.1
```
Sau khi "Phát hành image" đạt, trên erpnext-prod:
```bash
cd ~/trien-khai && git fetch https://github.com/tienduongmarcom/aphvh.git tag v0.16.1 && git checkout --detach v0.16.1 &&
bash deploy/release/dien_tap_ban_sao.sh 0.16.1 kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving kh_aph_factory_production kh_aph_ux_task_first &&
bash deploy/release/trien_khai_frontend.sh 0.16.1 kh_aph_cash_custody kh_aph_cash_closing kh_aph_cash_handover kh_aph_factory_handover kh_aph_factory_receiving kh_aph_factory_production kh_aph_ux_task_first
```
