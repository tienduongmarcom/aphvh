# APH-VH trên NocoBase (dùng tạm ~1 năm, từ 26/10/2026)

Lý do: chưa tách được hàng hóa theo từng đơn vị → tồn kho tính **tổng theo kho**, đơn bán **chọn đơn vị bán**,
công nợ theo **khách × đơn vị**. Khi tách xong sẽ quay lại ERPNext (repo này, thư mục gốc).
MISA vẫn là sổ kế toán/thuế chính thức; NocoBase chỉ là sổ vận hành (kho, bán, giao, thu tiền).

## Thành phần
| Thư mục | Nội dung |
|---|---|
| `plugin-kho/` | Plugin NocoBase `@aphvh/plugin-kho`: nghiệp vụ trên máy chủ (sổ kho có khóa, chốt/giao/hủy đơn, ghi/hủy phiếu thu) + 5 màn hình (Bán hàng, Kho vận, Thu chi và công nợ, Danh mục, Báo cáo) + trang in A5 `/in/don_ban|luot_giao|phieu_thu|phieu_chi|phieu_kho/<id>` |
| `schema/tao_bang.py` | Tạo 12 bảng qua API quản lý bảng (vẫn sửa được trong NocoBase) |
| `schema/cai_dat.py` | Menu, 6 nhóm quyền (bán hàng / kho / nhà máy / thu chi / kế toán / quản lý), 4 đơn vị APH, VH, MK, TL |
| `trien-khai/` | `docker-compose.yml` (NocoBase 2.2.31 + Postgres 16), `cai-dat.sh`, `sao-luu.sh`, gói plugin `.tgz` |
| `kiem/` | `kiem_api.py` (53 ca nghiệp vụ), `kiem_quyen.py` (10 ca quyền), kịch bản trình duyệt |

## Quy tắc nghiệp vụ đã làm (không tự suy diễn thêm)
- Tồn chỉ thay đổi qua **Sổ kho**; không sửa tay tồn. Hai người cùng xuất một mặt hàng/kho: khóa dòng, không âm kho.
- Đơn: Nháp → **Chốt** (tạo lượt giao, giữ hàng) → lượt **Khách đã nhận / Đã bàn giao xe** (trừ kho, ghi nợ) — xem bản 0.3.0. Bấm nhiều lần chỉ ghi một lần.
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
`python3 kiem/kiem_api.py --email … --password …` (53/53 đạt), `python3 kiem/kiem_quyen.py …` (10/10 đạt) — chạy trên CSDL thử, tạo dữ liệu tiền tố `KT-`.

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

## Bản 0.3.0 (24/10/2026) — theo bản rà soát, cài một lần để thử toàn bộ
**Thay đổi cách làm việc (cần báo nhân viên):**
- **Giao hàng theo lượt.** Chốt đơn → hệ thống tạo sẵn 1 lượt giao toàn bộ và in phiếu xuất của lượt đó (giữ hàng, chưa trừ kho).
  Kho bấm **Khách đã nhận** (khách đến lấy) hoặc **Đã bàn giao xe** (vận chuyển) → trừ kho, ghi công nợ phần đã giao.
  Giao nhiều đợt: hủy lượt mặc định, bấm **+ Tạo lượt giao** nhập lượng từng đợt. Màn Kho vận → **Lượt chờ xuất**.
- **Đơn đã giao không hủy được.** Hàng khách trả: **Khách trả hàng** (chọn kho nhận, hàng hỏng → kho chờ xử lý, trả lẻ được 5 kg từ bao 25 kg).
  Khách giữ hàng chỉ giảm tiền: **Giảm giá sau bán** (nhân viên lập, kế toán ghi). Giao thiếu và không giao nữa: **Đóng phần chưa giao**.
- **Hàng nhập chưa có giá** = **chờ định giá**: có trong kho nhưng **không bán được**, không vào giá vốn. Thủ kho nhập luôn là chờ định giá
  (giá gõ vào bị bỏ); kế toán định giá ở Kho vận → **Chờ định giá**.
- **Khả dụng bán = tồn − đang giữ cho lượt chưa giao − chờ định giá.** Hai người cùng giữ hàng: một người bị chặn.

**Nghiệp vụ thêm:** ĐVT tồn theo mặt hàng (Kg / Cái / Gói…; vỏ thùng tính Cái, đóng gói chỉ cân kg giữa hàng kg) ·
giá vốn bình quân **theo mặt hàng × kho** (chuyển kho mang giá trị) · nhà cung cấp, phải trả theo phiếu nhập, phiếu chi trả NCC (không trả quá) ·
phiếu thu **Đặt cọc** / **Chưa rõ người nộp** (vào đúng tài khoản, nằm ở chưa phân bổ; nhận diện khách rồi phân bổ sau) ·
**Thu hộ**: tiền vào đơn vị A trả nợ đơn đơn vị B — chỉ kế toán, ghi căn cứ, tiền vẫn ở A, sinh khoản "đang giữ hộ" chờ tất toán ·
hạn mức công nợ khách (vượt → chờ duyệt) · đánh dấu xuất hóa đơn MISA + hàng đợi nhập ký hiệu/số HĐ (chặn trùng) ·
báo cáo lãi gộp theo đơn vị / khách / mặt hàng / ngày · chống bấm trùng (mã yêu cầu).

**Quyền:** thêm nhóm **Nhà máy** (phiếu sản xuất / đóng gói, không thấy giá) và **Kế toán**. Giá vốn, giá thành, giá nhập, phải trả NCC
bị **cắt ở máy chủ** với bán hàng / kho / nhà máy / thu chi (gọi API trực tiếp cũng không thấy; bảng giá vốn trả 403).

**Kiểm (CSDL thử, dữ liệu tiền tố `KT-`):** `kiem_api.py` 53/53 đạt (gồm: 2 đơn vị bán chung kho, 2 người tranh 400 kg, giao 3 đợt,
bàn giao xe rồi khách nhận chỉ trừ 1 lần, hủy đơn đã giao bị chặn, trả 5 kg, giảm giá, đóng gói Cái, APH thu hộ TL, tiền chưa rõ người nộp,
cọc, hàng chờ giá không bán được, sản xuất 1.000 → 820 + 150 + hao 30, nhà máy gọi API giá vốn bị chặn, bấm trùng) ·
`kiem_quyen.py` 10/10 · quét 15 màn + 4 mẫu in không lỗi · kịch bản trình duyệt lập đơn → chốt → in lượt → khách nhận đạt
(`NB_EMAIL=… NB_PASSWORD=… node kiem/e2e-trinh-duyet.mjs`).

## Nâng cấp từ 0.2.0
Cấu trúc dữ liệu đổi nhiều (lượt giao, giá vốn theo kho). Chưa có dữ liệu thật nên **cài mới**: xóa thư mục cài cũ (hoặc `docker compose down -v`) rồi `bash cai-dat.sh`.

## Chưa làm
Hồ sơ bản ký (ảnh phiếu đã ký); báo cáo lãi gộp chưa trừ hàng trả / giảm giá; tuổi nợ.
