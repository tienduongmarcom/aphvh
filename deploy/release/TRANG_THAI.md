# Trạng thái phát hành APH-VH (một nơi duy nhất — cập nhật mỗi lần phát hành / triển khai)

| Mục | Giá trị |
|---|---|
| Production (site `frontend`, VM `erpnext-prod`) | **kh_aph 0.14.3**, lab9x 0.2.9, ERPNext 16.50.0 + Frappe 16.51.0 |
| Image production | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.14.3` — digest `sha256:706bf959addeca5bcb255fee0437ae7aeb355d910d1fc0625ae93fe66367ebc8` |
| Lên production lúc | 16/10/2026 ~16:29 (diễn tập tách biệt ĐẠT 16:23: tong + dem + chi_tiet khớp), 21 cờ bật |
| Nguồn | commit `b14ad8d` (tag `v0.14.3`); CI xanh trên đúng commit (UAT 38840547684, Cổng 3 38840547719) |
| Quay lui về | bản sao lưu trước nâng cấp trong `~/erp/aph-vh/sao-luu/` (thư mục có `phien-ban-truoc.txt` = `0.14.2`, có `sha256.txt`): `./quay-lui.sh <thư mục>` |
| Ứng viên | **0.14.4**, nhánh `thu/erpnext-v16.51.1`: ERPNext 16.51.1, chưa phát hành/triển khai; chờ CI |
| CI bắt buộc trước khi gắn tag | UAT candidate, Cổng 2, Cổng 3 xanh trên đúng commit |
| Thủ tục | `bash deploy/release/dien_tap_ban_sao.sh <PB>` → `bash deploy/release/trien_khai_frontend.sh <PB>` (≤ 12 giờ sau) |
| Lịch người dùng | Bắt đầu dùng thử 18/10/2026 |

Lịch sử: 0.14.2 (15/10 ~22:44, `0f528c3c…`), 0.14.0 (15/10 ~15:45, `3a259c9b…`), 0.13.0 (`e3136592…`), 0.12.1 (`897f81c2…`), 0.11.4 (`54bf5a99…`), 0.11.3 (`716f1401…`),
0.11.2 (`f2417393…`), 0.11.1 (`9335dfa1…`).
