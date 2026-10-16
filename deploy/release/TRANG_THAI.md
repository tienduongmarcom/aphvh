# Trạng thái phát hành APH-VH (một nơi duy nhất — cập nhật mỗi lần phát hành / triển khai)

| Mục | Giá trị |
|---|---|
| Production (site `frontend`, VM `erpnext-prod`) | **kh_aph 0.14.2**, lab9x 0.2.9, ERPNext 16.50.0 + Frappe 16.51.0 |
| Image production | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.14.2` — digest `sha256:0f528c3c1f0e0021eb9d864ba03bd4581af51f9857b736f584d16b442c81a8a3` |
| Lên production lúc | 15/10/2026 ~22:44 (diễn tập bản sao ĐẠT 22:35), 21 cờ bật |
| Nguồn | commit `87509d2` (tag `v0.14.2`) |
| Quay lui về | bản sao lưu trước nâng cấp trong `~/erp/aph-vh/sao-luu/` (thư mục có `phien-ban-truoc.txt` = `0.14.0`): `./quay-lui.sh <thư mục>` |
| Ứng viên | **0.14.3** (an toàn nâng cấp + nhãn thẻ ngân hàng), nhánh `fix/p0-uat-v091-20261010` — ĐANG KIỂM TRÊN CI |
| CI bắt buộc trước khi gắn tag | UAT candidate, Cổng 2, Cổng 3 xanh trên đúng commit |
| Thủ tục | `bash deploy/release/dien_tap_ban_sao.sh <PB>` → `bash deploy/release/trien_khai_frontend.sh <PB>` (≤ 12 giờ sau) |
| Lịch người dùng | Bắt đầu dùng thử 18/10/2026 |

Lịch sử: 0.14.0 (15/10 ~15:45, `3a259c9b…`), 0.13.0 (`e3136592…`), 0.12.1 (`897f81c2…`), 0.11.4 (`54bf5a99…`), 0.11.3 (`716f1401…`),
0.11.2 (`f2417393…`), 0.11.1 (`9335dfa1…`).
