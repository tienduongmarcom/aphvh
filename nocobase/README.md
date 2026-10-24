# APH-VH trên NocoBase (dùng tạm ~1 năm, từ 26/10/2026)

Lý do: chưa tách được hàng hóa theo từng đơn vị → tồn kho tính **tổng theo kho**, đơn bán **chọn đơn vị bán**,
công nợ theo **khách × đơn vị**. Khi tách xong sẽ quay lại ERPNext (repo này, thư mục gốc).
MISA vẫn là sổ kế toán/thuế chính thức; NocoBase chỉ là sổ vận hành (kho, bán, giao, thu tiền).

## Thành phần
| Thư mục | Nội dung |
|---|---|
| `plugin-kho/` | Plugin NocoBase `@aphvh/plugin-kho`: nghiệp vụ trên máy chủ (sổ kho có khóa, chốt/giao/hủy đơn, ghi/hủy phiếu thu) + 7 màn hình (Bán hàng, Kho vận, Thu chi và công nợ, Danh mục, Báo cáo, Tài sản, Go-Live & số dư đầu kỳ) + trang in A5 `/in/don_ban|luot_giao|phieu_thu|phieu_chi|phieu_kho/<id>` |
| `schema/tao_bang.py` | Tạo 12 bảng qua API quản lý bảng (vẫn sửa được trong NocoBase) |
| `schema/cai_dat.py` | Menu, 6 nhóm quyền (bán hàng / kho / nhà máy / thu chi / kế toán / quản lý), 4 đơn vị APH, VH, MK, TL |
| `trien-khai/` | `docker-compose.yml` (NocoBase 2.2.31 + Postgres 16), `cai-dat.sh`, `sao-luu.sh`, `phuc-hoi.sh`, `quay-lui.sh`, gói plugin `.tgz` |
| `kiem/` | `kiem_032.py` (47 ca toàn vẹn), `doi_chieu.py`, `kiem_golive.py` (72 ca Go-Live / tài sản / mẻ), `kiem_api.py` (53 ca nghiệp vụ), `kiem_quyen.py` (10 ca quyền), kịch bản trình duyệt |

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

## Bản 0.3.1 (24/10/2026) — Go-Live & số dư đầu kỳ, tài sản, mẻ sản xuất
Theo bản rà soát bổ sung (import, đầu kỳ, tài sản, giá thành). **Nâng cấp tại chỗ, không xóa dữ liệu:** `git pull` rồi `bash cai-dat.sh`
(tự sao lưu trước khi nâng cấp nếu đã có dữ liệu; thêm bảng / trường, không đổi dữ liệu cũ).

**Menu mới "Go-Live & số dư đầu kỳ"** (chỉ kế toán / quản lý): Kỳ mở sổ → Lô nhập: dán từ Excel / Google Sheets (hoặc tệp CSV) →
**Kiểm tra** (từng dòng: tra mã, lỗi, trùng; tổng đối chiếu theo kho / đơn vị / quỹ: trong file, hệ thống trước) → **Duyệt** → **Ghi sổ**
(cả lô một giao dịch; hệ thống sau khi ghi) → **Khóa kỳ**. 13 loại: danh mục hàng / khách / NCC / kho / quỹ / tài sản; tồn đầu kỳ (số lượng,
số bao, giá trị, tình trạng giá Đã chốt / Tạm tính / Chưa xác định, tình trạng hàng Bán được / Chờ xử lý / Đang vận chuyển); nợ khách và
**nợ NCC đầu kỳ** (nhiều khoản / khách, chứng từ gốc, ngày, hạn, đối chiếu); **số dư quỹ / ngân hàng**; **tiền cọc / chưa rõ / chưa phân bổ**
(không cộng thêm vào số dư quỹ); **thu hộ còn giữ**; **đơn chưa giao / đang vận chuyển**.
- Chống trùng bằng khóa duy nhất ở máy chủ (`mo_so_khoa`): dán lại cùng file, lập tay phiếu tồn đầu kỳ trùng mã × kho đều bị chặn.
- Không ghi thẳng vào sổ kho / tồn / sổ quỹ / giá vốn: lô tạo chứng từ rồi ghi qua lõi nghiệp vụ. Danh mục: mã đã có mặc định **không ghi đè**.
- Quyền ở máy chủ: chỉ kế toán / quản lý tạo lô, kiểm, duyệt, ghi, khóa kỳ; nợ đầu kỳ / tiền đầu kỳ không tạo được ngoài Go-Live (kể cả quản trị);
  sau khóa kỳ không ai ghi thêm số dư đầu kỳ. Lô lưu nguồn (tên tệp / link Sheet), dữ liệu gốc, người nhập / duyệt / ghi, dòng → chứng từ.
- Trả nợ NCC đầu kỳ bằng phiếu chi (đúng đơn vị, không trả quá). Tiền chưa rõ đầu kỳ nhận diện rồi phân bổ vào nợ đầu kỳ như phiếu thu thường.
- **Giá tạm**: tồn đầu kỳ / định giá hàng nhập có thể ghi "giá tạm được duyệt"; định giá chính thức sau chỉ điều chỉnh phần chênh giá trị.
- Kho chờ xử lý / kho đang vận chuyển không xuất bán được.
- `trien-khai/phuc-hoi.sh`: phục hồi THỬ bản sao lưu vào CSDL riêng và so số dòng (không đụng CSDL đang chạy).

**Tài sản & CCDC** (menu "Tài sản"; MISA vẫn hạch toán, khấu hao chính thức): mã, serial, địa điểm, người giữ, tình trạng, ngày mua, nguyên giá
tham khảo, đơn vị đứng tên (tùy chọn). Người giữ / địa điểm / tình trạng chỉ đổi qua **sự kiện** (bàn giao, điều chuyển, cấp phát, thu hồi,
bảo trì, sửa chữa, báo hỏng, đề nghị thanh lý → **thanh lý do kế toán duyệt**, báo mất) — giữ lịch sử. Chi phí sử dụng **ước tính** theo tháng
(quản trị, không sinh bút toán). Nhà máy / kho không thấy nguyên giá.

**Mẻ sản xuất** (Kho vận → Mẻ sản xuất): mở mẻ → cấp NVL / bao bì (Cái) nhiều lần → thu hồi thành phẩm / phụ phẩm / hao hụt (tự nhiên /
bất thường, có lý do) nhiều lần qua nhiều ngày — thành phẩm vào kho với **giá tạm** → kế toán ghi chi phí (nhân công, điện, chung, khấu hao
ước tính, dở dang đầu kỳ…, kể cả chi phí đến sau) → **Chốt giá thành**: (NVL + bao bì + chi phí − phụ phẩm − dở dang cuối) − phần hao hụt
bất thường, phân bổ theo **kg / hệ số định mức / giá trị tương đối**, điều chỉnh đúng phần chênh giá trị kho. Có chi phí / sản lượng mới →
"Cần chốt lại"; mỗi lần chốt là một **phiên bản** (không ghi đè). Tái chế: mở mẻ gắn mẻ gốc. Nhà máy không thấy giá trị / chi phí / giá thành.
Phiếu "Sản xuất (một bước)" 0.2.0 vẫn dùng cho mẻ đủ số liệu.

**Báo cáo:** lãi gộp báo **TẠM TÍNH** khi còn mẻ chưa chốt / hàng giá tạm / chờ định giá; thêm **tuổi nợ khách** (theo hạn hoặc ngày giao).

**Kiểm (CSDL thử):** `kiem_golive.py` 71/71 — đủ 6 điều kiện nghiệm thu (dán lại không nhân đôi; tồn khớp kiểm kê theo kho × mã, không chia
đơn vị; nợ khách / NCC đúng đơn vị kể cả khoản chờ đối chiếu; quỹ 300tr không đếm đôi 40tr cọc / chưa rõ; người không có quyền không tạo
chứng từ đầu kỳ bằng API; truy nguồn + tổng trước / sau), tài sản, mẻ nhiều lần thu hồi + chi phí đến sau + dở dang + chỉnh giá phụ phẩm
(3 phiên bản) · `kiem_api.py` 53/53 · `kiem_quyen.py` 10/10 (không hồi quy) · quét 17 màn không lỗi · trình duyệt: mở kỳ → dán → kiểm
(1 lỗi) → sửa → duyệt → ghi sổ đạt · sao lưu → phục hồi vào CSDL riêng: 11 bảng chính khớp số dòng và mã băm.

## Bản 0.3.2 (24/10/2026) — toàn vẹn dữ liệu & an toàn (theo audit PR #43)
**Nâng cấp tại chỗ:** `git pull` rồi `bash cai-dat.sh`. Bộ cài mới: kiểm SHA-256 gói đích danh `plugin-kho-0.3.2.tgz` (bỏ qua gói cũ còn
trong thư mục) → dừng app (khóa ghi) → sao lưu + **kiểm bản sao lưu đọc được** → giải nén ra thư mục tạm, kiểm đúng phiên bản →
đổi plugin (giữ bản cũ `.cu-*`) → khởi động, lỗi thì **tự quay lui** plugin cũ → bảng / quyền → **đối chiếu bảo toàn**.
`quay-lui.sh` (plugin cũ, tùy chọn kèm CSDL từ bản sao lưu, hỏi xác nhận). Đã diễn tập: thư mục còn gói 0.3.0 → dùng đúng 0.3.2;
sai checksum → dừng; `pm enable` lỗi → tự quay lui về 0.3.0.

**P0 đã sửa**
- **Điều chỉnh giá trị thống nhất** (`dieu_chinh_gia_tri`): chốt / chốt lại giá thành, giá tạm → giá chính thức, giá phụ phẩm. Chênh lệch chia
  thành phần **còn tồn** (vào giá trị tồn), phần đã **chuyển kho mà kho nhận còn giữ** (vào tồn kho nhận), phần **đã bán / tiêu hao**
  (vào giá vốn kỳ, không đổi tồn). Kiểm cân: chênh = vào tồn + vào giá vốn, làm tròn = 0. Ví dụ đã kiểm: bán 600/1.000 kg rồi chốt
  +1 triệu → 400.000 vào tồn, 600.000 vào giá vốn, giá BQ tồn 21.000; bán hết rồi chốt lại → toàn bộ vào giá vốn, tồn 0 / 0 đ.
- Tồn về 0 còn giá trị lẻ: không xóa im lặng nữa — ghi sổ giá trị + điều chỉnh vào giá vốn.
- **Tồn đầu kỳ** bị chặn nếu mã × kho đã có phát sinh ngoài mở sổ; kỳ phải có ngày chốt.
- **Đơn đang vận chuyển chuyển tiếp**: nhập "Giá vốn" có căn cứ, hoặc lượt "giá vốn chưa xác định" — tách khỏi lãi gộp cho tới khi kế toán
  nhập (có căn cứ). Đối chiếu: hàng đã có trong tồn đầu kỳ ở kho đang vận chuyển → lỗi tính hai lần.
- **Tiền chưa phân bổ vượt số dư quỹ: CHẶN** duyệt và ghi (kiểm lại trong giao dịch ghi); chỉ **quản lý** duyệt ngoại lệ có căn cứ.
- **Chốt mẻ**: hệ số / giá phụ phẩm của dòng không thuộc mẻ (khác mẻ, chưa ghi, không phải thành phẩm) bị từ chối.
- **Vai trò "Không xem giá vốn (phủ quyết)"**: gán thêm thì dù có vai trò kế toán vẫn không lấy được giá vốn / lãi gộp / chốt giá thành.
- **Phạm vi kho / quỹ theo người dùng** (Danh mục → Phạm vi): kiểm ở máy chủ khi ghi phiếu kho, giao / nhận, trả hàng, mẻ, thu / chi /
  chuyển tiền / chốt ca; đọc tồn, sổ kho, phiếu kho, sổ quỹ, phiếu thu / chi bị lọc (cả in phiếu). Người chưa khai phạm vi: không giới hạn.
- Hai người cùng bấm ghi một lô: chỉ ghi một lần.

**P1 đã làm**: đọc **.xlsx thật** (chọn trang tính) và CSV chuẩn (dấu phẩy / ngoặc kép / xuống dòng trong ô); lưu **tệp gốc + SHA-256 +
thời điểm lấy + mã nguồn** (Google Sheet tải .xlsx = ảnh chụp, không tự ghi khi Sheet đổi) · **tách người nhập / người duyệt** cho lô tiền
và công nợ (cấu hình theo kỳ) · danh mục mặc định **không ghi đè**, ô trống không xóa dữ liệu cũ · **quy đổi ĐVT** theo mặt hàng (bao /
thùng / gói / cái; bán theo thùng, tồn theo kg) · **dở dang đầu kỳ** nhập theo lô (mở mẻ có kg + giá trị) · đơn chuyển tiếp **đang giữ hàng**
và **đã thu một phần** (tiền nằm trong số dư quỹ, không ghi sổ quỹ lại) · **số đối tác xác nhận** cho đối chiếu nợ đầu kỳ · **CCDC theo
người giữ** (kho / tổ A / tổ B; thu hồi kiểm đúng người đang giữ; tổng không đổi) · TSCĐ: ngày đưa vào sử dụng, bộ phận chịu chi phí,
số chứng từ sửa chữa / thanh lý · mẻ: **Tạm hoàn thành → Đã chốt → Cần điều chỉnh → Đã khóa kỳ** (khóa: không cấp / thu thêm; chi phí đến
muộn thành phiên bản điều chỉnh) · chi phí mẻ: số chứng từ + phiếu chi, **chống tính hai lần** · **lãi gộp thuần** (trừ trả hàng, giảm giá,
cộng điều chỉnh giá vốn) · **thu hộ tất toán một phần** có chứng từ · Go-Live → **Đối chiếu bảo toàn** (Σ sổ kho = tồn, Σ sổ giá trị =
giá trị tồn, mọi điều chỉnh cân) — cũng chạy cuối `cai-dat.sh` (`kiem/doi_chieu.py`).

**Kiểm (CSDL thử):** `kiem_032.py` 47/47 — đủ 13 ca bắt buộc của audit (trừ ca bộ cài, diễn tập riêng bằng docker giả: đạt) ·
`kiem_golive.py` 72/72 · `kiem_api.py` 53/53 · `kiem_quyen.py` 10/10 · đối chiếu bảo toàn toàn CSDL: CÂN · quét 16 màn không lỗi ·
trình duyệt: lập đơn → chốt → khách nhận; Go-Live dán → kiểm → duyệt → ghi; tải .xlsx → kiểm · sao lưu → phục hồi CSDL riêng:
23/23 bảng khớp số dòng và mã băm toàn bộ nội dung (gồm mở sổ, mẻ, phiên bản, tài sản, người giữ, điều chỉnh giá trị).

**Giới hạn còn lại (ghi rõ):** truy vết chênh lệch qua chuyển kho một bậc; hàng đã đi tiếp từ kho nhận được coi là đã tiêu thụ. Phân
bổ phần đã xuất theo tỷ trọng lượng ra (không theo từng lô) — đúng với bình quân gia quyền, không phải FIFO.

## Chưa làm
Hồ sơ bản ký (ảnh phiếu đã ký); đồng bộ trực tiếp Google Sheets bằng API (hiện tải .xlsx); đối soát MISA tự động.
