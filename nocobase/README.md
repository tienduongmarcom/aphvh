# APH-VH trên NocoBase (dùng tạm ~1 năm, từ 26/10/2026)

Lý do: chưa tách được hàng hóa theo từng đơn vị → tồn kho tính **tổng theo kho**, đơn bán **chọn đơn vị bán**,
công nợ theo **khách × đơn vị**. Khi tách xong sẽ quay lại ERPNext (repo này, thư mục gốc).
MISA vẫn là sổ kế toán/thuế chính thức; NocoBase chỉ là sổ vận hành (kho, bán, giao, thu tiền).

## Thành phần
| Thư mục | Nội dung |
|---|---|
| `plugin-kho/` | Plugin NocoBase `@aphvh/plugin-kho`: nghiệp vụ trên máy chủ (sổ kho có khóa, chốt/giao/hủy đơn, ghi/hủy phiếu thu) + 4 màn hình (Bán hàng, Kho vận, Thu chi và công nợ, Danh mục) + trang in A5 `/in/don_ban/<id>`, `/in/phieu_thu/<id>` |
| `schema/tao_bang.py` | Tạo 12 bảng qua API quản lý bảng (vẫn sửa được trong NocoBase) |
| `schema/cai_dat.py` | Menu, 4 nhóm quyền (bán hàng / kho / thu chi / quản lý), 4 đơn vị APH, VH, MK, TL |
| `trien-khai/` | `docker-compose.yml` (NocoBase 2.2.31 + Postgres 16), `cai-dat.sh`, `sao-luu.sh`, gói plugin `.tgz` |
| `kiem/` | `kiem_api.py` (21 ca nghiệp vụ), `kiem_quyen.py` (10 ca quyền), kịch bản trình duyệt |

## Quy tắc nghiệp vụ đã làm (không tự suy diễn thêm)
- Tồn chỉ thay đổi qua **Sổ kho**; không sửa tay tồn. Hai người cùng xuất một mặt hàng/kho: khóa dòng, không âm kho.
- Đơn: Nháp → **Chốt & In** (Chờ xuất, chưa trừ kho) → **Đã giao** (trừ kho, ghi nợ). Bấm nhiều lần chỉ ghi một lần.
  Mặc định khách đến lấy, ngày giao = hôm nay; chọn khách hiện SĐT + địa chỉ; mặt hàng hiện "mã – tên".
- Thu tiền: chỉ trả vào đơn được tích, theo thứ tự tích, không quá số còn nợ; phần còn lại **chưa phân bổ**.
  Không tự trả nợ cũ nhất, **không cấn chéo đơn vị**. Hủy phiếu thu trả lại công nợ; đơn có tiền thu không hủy được.
- Số chứng từ `DB-` (đơn bán), `PK-` (phiếu kho), `PT-` (phiếu thu) theo năm — không dùng chữ "APH".

## Cài (Mac có Docker Desktop, hoặc VM)
```bash
cd nocobase/trien-khai && bash cai-dat.sh
```
Mật khẩu quản trị sinh ngẫu nhiên trong `trien-khai/.env` (không đưa lên git). Sao lưu: `bash sao-luu.sh` (đặt crontab hằng đêm).

## Kiểm
`python3 kiem/kiem_api.py --email … --password …` (21/21 đạt), `python3 kiem/kiem_quyen.py …` (10/10 đạt) — chạy trên CSDL thử, tạo dữ liệu tiền tố `KT-`.

## Bản 0.2.0 (24/10/2026)
- **Giá vốn bình quân gia quyền** theo mặt hàng (tồn tổng mọi kho): nhập có giá → bình quân lại; xuất/bán/chuyển/kiểm kê theo bình quân.
  Đơn đã giao lưu giá vốn. Chỉ nhóm quản lý xem giá vốn.
- **Nhà máy:** phiếu Sản xuất / Đóng gói: nguyên liệu vào (xuất theo bình quân) → thành phẩm + phụ phẩm ra (kho thành phẩm).
  **Giá thành = (giá trị nguyên liệu + chi phí sản xuất − phụ phẩm × đơn giá nhập tay) / kg thành phẩm.** Kg vào ≠ kg ra bắt buộc ghi lý do.
  Báo cáo "Giá thành sản xuất" (kg vào/ra, hao hụt %, NVL, chi phí, giá thành).
- **Giá sàn:** bán dưới giá sàn → đơn "Chờ duyệt giá", quản lý duyệt có lý do mới in / giao.
- **Tiền:** quỹ / tài khoản theo đơn vị; phiếu thu vào đúng quỹ (tiền mặt ↔ quỹ tiền mặt, CK ↔ ngân hàng); phiếu chi (quỹ tiền mặt không âm);
  bàn giao / nộp tiền giữa hai quỹ CÙNG đơn vị; sổ quỹ; chốt ca tiền (đếm so sổ, lệch phải ghi lý do, không tự sửa sổ).
- **In:** đơn "Vận chuyển" in 3 liên (kho / vận chuyển / khách ký); phiếu chuyển kho 3 liên (nguồn / vận chuyển / đích, có cột kg thực nhận);
  phiếu nhập / xuất / sản xuất 2 liên; phiếu chi 2 liên.
- Kiểm: API 39/39, quyền 10/10, quét giao diện + mẫu in không lỗi.

## Chưa làm
Hồ sơ bản ký (ảnh phiếu đã ký), nhận hàng nhà cung cấp chờ định giá, công nợ nhà cung cấp, báo cáo doanh số / lãi gộp theo đơn vị.
