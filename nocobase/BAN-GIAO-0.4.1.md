# Bàn giao NocoBase 0.4.1 — Factory MES Lite (Nhà máy Phú Thọ)

Nền: 0.4.0 (nhánh `feat/nocobase-040-unified-operations`, PR #45). Nhánh: `feat/nocobase-041-factory-mes`. Gói `plugin-kho-0.4.1.tgz`.
Không tạo mẻ / sổ song song: dùng lại `me_sx`, phiếu cấp NVL, phiếu thu hồi, chi phí mẻ, phiên bản giá thành và lõi sổ kho 0.4.0.

## 1. Vào đâu
**Kho vận → tab "Sản xuất (nhà máy)"**, gồm:
| Tab | Ai | Việc |
|---|---|---|
| Phiếu sản xuất | Nhà máy | Chọn mẫu → **Mở mẻ** (chưa ghi kho) → nhập kg NVL hoặc số thành phẩm để có **dự kiến** → nhập số **cân / đếm thực tế** ở 3 khu vực (A. nguyên liệu · B. thành phẩm, phụ phẩm, hao hụt đã đo, dở dang · C. bao bì / vật tư / nhiên liệu) → **Ghi thực tế** (nhiều lần, nhiều ngày) hoặc **Ghi & kết thúc mẻ** → bảng **cân đối khối lượng** cập nhật ngay → **Giải trình chênh lệch** |
| Mẫu & định mức | Nhà máy đề xuất, kế toán duyệt | Mẫu theo 4 công nghệ; phiên bản định mức (đề xuất → duyệt, có căn cứ, ngày hiệu lực); bản đã duyệt không sửa được |
| Giải trình chờ duyệt | Kế toán / quản lý | Duyệt / từ chối giải trình (cân sai, hao hụt bất thường, khác) |
| Đề xuất mã hàng | Nhà máy / kho đề xuất, kế toán duyệt | Tạo mã chính thức hoặc ghép mã có sẵn |
| Hàng gửi gia công | Kế toán | Hồ sơ bên gửi / bên nhận / kho hàng gửi / chủ sở hữu xác nhận; nhận hàng, trả hàng, báo cáo |
| Hiệu suất | Kế toán / quản lý | Tỷ lệ thu hồi, phụ phẩm, hao hụt, lệch cân bằng theo mẻ |
| Rà soát nhập nhanh / import | Nhà máy, kế toán | Phiếu nhập nhanh / import thiếu mã, lệch (giữ từ 0.4.0) |
Chốt giá thành vẫn ở tab **Mẻ sản xuất** (kế toán).

## 2. Quy tắc đã cài (theo đặc tả, có điều chỉnh A–C)
- **Mẫu chỉ gợi ý.** Mở mẻ lưu **snapshot** định mức (phiên bản đang hiệu lực đã duyệt); đổi định mức sau không ảnh hưởng mẻ đang chạy. Chỉ "Ghi thực tế" mới xuất / nhập kho.
- **Chênh lệch không tự thành hao hụt.** Hao hụt chỉ là lượng đã đo. Phần còn lại "còn chênh chưa giải trình"; nhà máy giải trình, kế toán duyệt.
  Hao bất thường đã duyệt thành phiếu thu hồi dòng hao bất thường (không vào giá thành), có lịch sử.
- **Cân đối theo công nghệ** (lũy kế cả mẻ, dở dang chỉ lấy số cuối — qua nhiều ngày không tính hai lần):
  `NVL vào + nước thêm + dở dang đầu = thành phẩm + phụ phẩm + hao đã đo + nước bay hơi + dở dang cuối + chênh`.
  - GRADING (đỗ): phép kg trực tiếp. BLENDING_COOKING (phồng tôm): bắt buộc số nước thêm / bay hơi, thiếu → *Chưa đủ căn cứ*.
  - REPACKING: thành phẩm thùng / gói quy kg theo "kg cho 1 ĐVT" có căn cứ. LIQUID_FILLING: lít → kg theo khối lượng riêng có căn cứ; thiếu → *Chưa đủ căn cứ*, không dùng hệ số tùy tiện.
  - **Bao bì, vật tư, nhiên liệu (củi, than) không vào cân bằng khối lượng** dù ĐVT là kg.
- **Ngưỡng** không cố định 5 %: ngưỡng hao theo dòng nguyên liệu × phiên bản định mức; ngưỡng chênh cho phép theo phiên bản (trống = phải giải trình mọi chênh). Vượt ngưỡng → chờ kế toán.
- **Bao bì**: gợi ý theo định mức; ghi lượng THỰC dùng + hỏng; khác định mức hoặc có hỏng phải ghi nguyên nhân; kho trừ đúng thực dùng + hỏng (không ép theo công thức).
  Dòng không chọn kho: hệ thống lấy kho của mẻ, không đủ thì kho nhà máy khác (trong phạm vi người dùng) còn đủ hàng.
- **Trạng thái vận hành riêng** (Đang sản xuất → Chờ cân đối → Hoàn thành thực tế) tách khỏi trạng thái giá thành. Chốt giá thành bị chặn khi mẻ chưa kết thúc / còn chênh
  (kế toán có thể "chấp nhận chênh" kèm lý do) và **luôn bị chặn khi mẻ thiếu phiếu cấp nguyên liệu**.
- **Giá thành theo mẫu**: phương pháp mặc định của mẫu (kế toán duyệt), hệ số thành phẩm và **giá tham chiếu phụ phẩm có nguồn** lấy từ snapshot; không tự đặt hệ số 0,5 / 0,2…
  Điều chỉnh giá thành vẫn theo vết bình quân (0.4.0): mẻ cũ bán hết rồi chốt lại không đội giá trị lô mới.
- **Hàng gửi gia công**: kho hàng gửi riêng (loại kho mới, không bán, không chuyển, không bán nhanh, không nhập thường); nhận hàng giá trị sở hữu 0;
  mẻ gia công lấy và trả về kho hàng gửi; chủ sở hữu "chưa xác định" cho tới khi kế toán xác nhận có căn cứ; phí gia công chỉ ghi nhận, không tạo doanh thu.
- **Quyền**: nhà máy không thấy giá (giá tham chiếu, snapshot giá, phí gia công bị cắt ở máy chủ, cả khi nhúng quan hệ / xuất); không duyệt định mức, giải trình, mã hàng; không chốt giá thành; không hủy phiếu đã ghi.
- **Hủy / điều chỉnh**: hủy phiếu cấp / thu hồi đã ghi (kế toán, có lý do) → dòng đảo, giữ dòng gốc, mẻ chuyển "cần chốt lại".
- **Chống ghi trùng**: mở mẻ, ghi thực tế, nhận hàng gửi đều có mã yêu cầu; nhập lại phiếu từ file cũ dùng khóa nguồn (0.4.0).

## 3. Dữ liệu mới
`mau_sx`, `mau_sx_phien_ban`, `mau_sx_dong`, `ca_sx`, `sx_doi_chieu` (mỗi lần ghi một bản cân đối), `sx_giai_trinh`, `de_xuat_mat_hang`, `sx_ho_so_gia_cong`, `sx_nguon_lo`;
mở rộng `me_sx` (mẫu, phiên bản, snapshot, ca, công nghệ, bên gửi, hồ sơ gia công, sản lượng kế hoạch, trạng thái vận hành), `phieu_kho_dong` (vai trò, số lô, số hỏng),
`mat_hang` (kg cho 1 ĐVT + căn cứ; thêm ĐVT Lít), `kho` (loại "hàng gửi gia công").
Nâng cấp dữ liệu ghi phiên bản `0.4.1`; các bước một lần của 0.4.0 (cấp phạm vi người cũ, giữ tồn đơn cũ) không chạy lại.

## 4. Kiểm thử (CSDL thử)
- `kiem_041.py` **60/60** — đủ 17 kịch bản mục 10 đặc tả (+ đề xuất mã, định mức đề xuất / duyệt / khóa sửa), mỗi ca kiểm tồn / giá trị trước–sau.
- Bộ cũ giữ nguyên: api 53/53 · quyền 10/10 · golive 72/72 · toàn vẹn 47/47 · 0.4.0 139/139 · đối chiếu bảo toàn CÂN.
- Nâng cấp bản sao CSDL **0.3.2 → 0.4.1** bằng đúng lệnh `nocobase upgrade` của bản docker: không lỗi; số dư trước = sau (chỉ thêm giữ tồn đơn đã duyệt); chạy lại toàn bộ bộ kiểm: đạt.
- Giao diện: 6 tab Sản xuất + mở mẻ / điền dự kiến / ghi / xem cân đối qua trình duyệt — không lỗi trang, không lỗi 5xx (`kiem/e2e-041.mjs`). TypeScript sạch.

## 5. Việc cần làm trước khi dùng
1. Kế toán khai **mẫu & định mức** cho từng dây chuyền (từ số liệu thực nghiệm, ghi căn cứ) rồi duyệt; khai giá tham chiếu phụ phẩm có nguồn.
2. Khai "kg cho 1 ĐVT" + căn cứ cho hàng thùng / gói / chai / lít (khối lượng riêng dầu).
3. Tạo kho "hàng gửi gia công" + hồ sơ cho hàng VH / MK gửi.
4. Các mã đang âm trong file cũ (TP.DO5, TP.DXTV13.CAM, TP.DXTV2.3SAPH25, TP.PT7…): đối chiếu qua Trung tâm dữ liệu — hệ thống không tạo phiếu nhập ảo cho hết âm.

## 6. Ngoài phạm vi (theo đặc tả mục 11)
Cân điện tử (0.4.2), QR toàn chuỗi, IoT, OEE / lịch máy, tự lập PO/SO liên công ty, tự xuất hóa đơn MISA, tự quyết giá phụ phẩm / hao hụt.
Thu tiền mặt tại nhà máy: dùng Bán nhanh với ca do người giữ quỹ nhà máy mở (không có sổ quỹ nhà máy riêng).
