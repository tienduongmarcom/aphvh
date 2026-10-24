# Bàn giao NocoBase 0.4.0 — Unified Operations (APH – VH – MK – TL)

Phiên bản: `@aphvh/plugin-kho` 0.4.0 · nền: 0.3.2 (`main` 1503e02) · nhánh: `feat/nocobase-040-unified-operations`.
Phát hành chính thức (tag) do chủ dự án quyết định sau UAT — tài liệu này là hồ sơ để quyết định.

## 1. Nguyên tắc giữ nguyên (không phá vỡ)
1. MISA vẫn là sổ kế toán / thuế chính thức; NocoBase là sổ vận hành. Không sửa ERPNext production.
2. Kho vật lý ≠ pháp nhân bán: một kho chung có thể bán bởi nhiều bên; quyền sở hữu không suy đoán.
3. Giá vốn **bình quân di động theo mặt hàng × kho**, không FIFO.
4. Không sổ song song: POS, đơn gộp, chuyển hàng, import đều ghi qua sổ kho / sổ giá trị / sổ quỹ / công nợ hiện có.
5. Tiền thực nhận ghi đúng quỹ / tài khoản và pháp nhân nhận; thu hộ có căn cứ, theo dõi riêng. Không FIFO tiền thu, không tự cấn.
6. Mọi nghiệp vụ ghi sổ là thao tác máy chủ có giao dịch + khóa dòng + chống bấm trùng (mã yêu cầu / trạng thái).
7. Không xóa / tạo lại CSDL khi nâng cấp. Không tự tạo PO/SO liên công ty, không tự xuất hóa đơn MISA.

## 2. Phạm vi đã làm theo đặc tả (B1–B7)
| Mục | Đã làm | Màn hình / thao tác máy chủ |
|---|---|---|
| B1 Dữ liệu & Go-Live | Nạp 2 nguồn (xlsx / csv / bản text "## Sheet name"), staging có nguồn + số dòng + khóa nội dung + SHA-256 tệp; ánh xạ kho / hàng / khách / công ty / quỹ / NCC (tự khớp mã, tên); phân loại theo mốc; ghép chuyến hai nguồn; ghi sổ theo nhóm có điểm lưu; nạp lại không nhân đôi; bản sửa của chứng từ đã ghi → "Có thể trùng"; lô tồn đầu kỳ từ 2 nguồn + bảng lệch cùng kho vật lý | Trung tâm dữ liệu · `nguon_tep:nap / goiYAnhXa / phanLoai / timTrung / ghiSo / taoLoTon / baoCao`, `anh_xa_ma:dat`, `khop_chung_tu:xacNhan / bacBo`, `nguon_ban_ghi:boQua` |
| B2 Đơn gộp | `don_gop` + dòng chọn bên bán / kho; chốt tách đơn con trong cùng giao dịch; tín dụng kiểm một lần trên tổng; chuyến giao gộp nhiều đơn con / kho; 4 trạng thái; in đơn tổng cho khách; hủy | Bán hàng → Đơn gộp · `don_gop:chot / duyet / taoGiao / huy`, `giao_gop:xacNhan / huy`, `don_gop:tongQuan` |
| B3 Kho & giao nhận | Giữ tồn khi duyệt (một số dư, chuyển giữ đơn → lượt không cộng trùng, nhật ký `dat_giu_ton`); giao theo cân thực + quy cách bao nguyên + dung sai; giao thiếu / giữ lại / nhả; chuyến hai đầu qua kho đang vận chuyển; chênh lệch chờ xử lý; hủy chuyến đã xuất (đảo sổ) | Kho vận → Chuyển hàng · `chuyen_hang:xacNhanXuat / xacNhanNhan / huy`, `chenh_lech_giao_nhan:xuLy` |
| B4 Nhà máy | Nhập nhanh phiếu SX (một giao dịch: mẻ + cấp NVL + thu hồi); hàng đợi rà soát; không chốt giá 0 / NVL giá 0; điều chỉnh giá trị theo vết bình quân (nhiều kho, chuyển, hủy chuyển, NVL đã cấp cho mẻ khác); báo cáo hiệu suất | Kho vận → Phiếu SX · `me_sx:nhapNhanh / hieuSuat`, `sx_ra_soat:boSung / boQua` |
| B5 Giá, VAT, tín dụng | Bảng giá theo nhóm khách / kênh / hiệu lực / bậc SL / ưu tiên; giá sàn; giá chốt lưu trên dòng (giá niêm yết, nguồn giá, lý do sửa); VAT theo dòng; quy đổi ĐVT; phơi nhiễm tín dụng không cộng trùng; khách rủi ro chờ duyệt; khách thường theo cấu hình; lịch sử duyệt | Danh mục → Bảng giá · `don_ban:chotDon / duyetGia` |
| B6 POS & tài chính | Ca bán (thu ngân + quỹ + kho); bán nhiều hình thức; CK chờ xác minh; khách lẻ trả đủ; chốt ca; nạp sao kê chống trùng; khớp / tạo thu / bỏ qua; phải hoàn (giữ / hoàn bằng phiếu chi) | Bán nhanh · Thu chi → CK chờ xác minh / Đối soát ngân hàng / Khoản phải hoàn · `ca_pos:mo / ban / chot`, `phieu_thu:baoChuyen / xacMinh / tuChoiXacMinh`, `sao_ke:nap / goiY`, `sao_ke_dong:khop / taoThu / boQua`, `don_ban:xuLyHoan` |
| B7 Quyền, báo cáo, MISA | Phạm vi kho / quỹ mặc định từ chối; NoCost phủ quyết; tổng quan vận hành; hàng đợi HĐ theo bên bán (nhận / ghi số / hủy / cần điều chỉnh); truy vết | Báo cáo → Tổng quan / Hàng đợi HĐ · `hoa_don_cho_xuat:nhan / ghiSo / huy`, `luot_giao:truyVet` |

Mã nguồn máy chủ tách module: `sales`, `pricing`, `inventory`, `logistics`, `manufacturing`, `finance`, `pos`, `import`, `reports`,
`security`, `migrations` (đăng ký trong `dang_ky_040.ts`); lõi sổ kho / giá vốn / quỹ / công nợ vẫn ở `plugin.ts` (không nhân bản).

## 3. Cấu hình vận hành (bảng `cau_hinh`, Danh mục → Cấu hình)
| Khóa | Mặc định 0.4.0 | Ý nghĩa |
|---|---|---|
| `giu_khi_duyet` | `co` | Giữ tồn ngay khi duyệt đơn |
| `vuot_han_muc_khach_thuong` | `canh_bao` | Khách thường vượt hạn mức: cảnh báo vẫn bán / `duyet` chờ duyệt (khách rủi ro luôn chờ duyệt) |
| `pham_vi_mac_dinh` | `tu_choi` | Người dùng nghiệp vụ chưa được cấp phạm vi kho / quỹ |
| `ck_can_xac_minh` | `khong` | `co`: phiếu thu CK của thủ quỹ chờ đối soát mới vào tài khoản (POS luôn chờ) |
| `gia_danh_muc_gom_vat` | `co` | Giá bán trên danh mục mặt hàng đã gồm VAT |
| `dung_sai_can_pct` | `2` | Dung sai cân mặc định (%) |
| `nguong_lech_sx_pct` | `0.5` | Ngưỡng lệch kg phiếu sản xuất (theo sheet nhà máy) |
| `ma_khach_le` | `KHACH-LE` | Khách lẻ cho bán nhanh (phải tạo trong danh mục khách) |
| `ngay_moc_golive` | (trống) | Mốc Go-Live cho Trung tâm dữ liệu |

Đổi cấu hình chỉ qua thao tác `cau_hinh:dat` (kế toán / quản lý; ghi người + ngày vào mô tả). Bản chưa chạy nâng cấp (không có dòng
cấu hình) giữ hành vi 0.3.2.

## 4. Ma trận phân quyền (máy chủ kiểm, không phụ thuộc giao diện)
| Chức năng | Bán hàng | Kho | Nhà máy (+NoCost) | Thu chi | Thu ngân | Kế toán | Quản lý |
|---|---|---|---|---|---|---|---|
| Lập / chốt đơn gộp, đơn bán | ✔ | xem | – | xem | – | ✔ | ✔ |
| Duyệt giá sàn / tín dụng | – | – | – | – | – | ✔ | ✔ |
| Lập / xác nhận chuyến giao gộp | – | ✔ (trong phạm vi kho) | – | – | – | ✔ | ✔ |
| Chuyển hàng: xuất / nhận | – | ✔ (kho được cấp) | ✔ (kho được cấp) | – | – | ✔ | ✔ |
| Xử lý chênh lệch giao – nhận, hủy chuyến đã xuất | – | – | – | – | – | ✔ | ✔ |
| Nhập nhanh phiếu SX, rà soát | – | – | ✔ | – | – | ✔ | ✔ |
| Chốt giá thành, chi phí mẻ, giá vốn, truy vết | – | – | – | – | – | ✔ | ✔ |
| Phiếu thu / báo CK | – | – | – | ✔ (quỹ được cấp) | (trong ca) | ✔ | ✔ |
| Xác minh CK, sao kê, phải hoàn, thu hộ | – | – | – | – | – | ✔ | ✔ |
| Ca bán nhanh (mở / bán / chốt) | – | – | – | xem | ✔ (kho + quỹ được cấp) | ✔ | ✔ |
| Hàng đợi hóa đơn MISA | xem | – | – | – | – | ✔ | ✔ |
| Trung tâm dữ liệu, cấu hình | – | – | – | – | – | ✔ | ✔ |
| Xem giá vốn / giá thành / giá nhập | – | – | **không** (kể cả quan hệ, in, xuất) | – | – | ✔ | ✔ |

- **NoCost** (`khong_xem_gia`) phủ quyết mọi vai trò khác (gán thêm cho người nhà máy kiêm việc).
- **Phạm vi**: người không có dòng phạm vi bị từ chối kho / quỹ (đọc: lọc rỗng; ghi: báo lỗi). Kế toán / quản lý / quản trị không bị chặn
  mặc định (nếu được cấp dòng phạm vi thì vẫn bị giới hạn theo dòng). Có lựa chọn "mọi kho" / "mọi quỹ".
- Bảng nguồn, sao kê, hàng đợi HĐ, nhật ký giữ tồn, chênh lệch: chỉ đổi qua thao tác nghiệp vụ (hook chặn tạo / sửa / xóa trực tiếp).

## 5. Mapping dữ liệu hai nguồn
| Nguồn / trang tính | Nghiệp vụ | Ghi thành |
|---|---|---|
| Nhà máy · Nhận hàng | `nhan_hang` | Phiếu nhập (giá trống → **chờ định giá**); loại "Từ Hà Nội" → ghép với chuyển "→ Kho nhà máy" của sổ bán hàng |
| Nhà máy · Sản xuất (nhiều dòng / Số phiếu SX) | `san_xuat` | Mẻ + cấp NVL + thu hồi (`me_sx:nhapNhanh`); thiếu / lệch → rà soát |
| Nhà máy · Chuyển kho → "Hàng đang vận chuyển" | `chuyen_kho` | Ghép với sổ bán hàng "Kho nhà máy → kho X" → **một** chuyến hai đầu (xuất theo NM, nhận theo BH, lệch → chênh lệch chờ xử lý) |
| Nhà máy · Bán tại NM / Sổ BH · Đơn bán | `ban_nm` / `don_ban` | Đơn bán (+ lượt khách nhận theo "SL thực xuất"); đơn giá sổ BH là giá **đã gồm thuế** |
| Sổ BH · Thu tiền | `thu_tien` | Phiếu thu vào quỹ ánh xạ theo "công ty + hình thức"; phân bổ cho phiếu XK ghi kèm; **"ghi nợ" không phải tiền thu → bỏ qua**; thiếu công ty mà có phiếu XK duy nhất → lấy công ty của phiếu đó |
| Sổ BH · Trả lại | `tra_lai` | Phiếu trả hàng theo đơn gốc (thiếu số XK gốc → chưa đủ căn cứ) |
| Sổ BH · Nhập kho | `nhap_kho` | Phiếu nhập (giá chưa thuế) |
| Sổ BH · Chuyển kho – xuất khác | `chuyen_kho` | Chuyển nội bộ (hai đầu cùng sổ) hoặc phiếu xuất khác |
| Nhà máy · tồn đầu kỳ / Sổ BH · DM hàng (tồn đầu theo kho) | `ton_dau` / `ton_dau_bh` | Lô tồn đầu kỳ (Go-Live) — cùng kho vật lý có ở 2 nguồn thì **không cộng**, lấy sổ nhà máy và đưa vào bảng lệch |

Quy tắc: mã "mã \| tên" lấy phần mã; số kiểu Việt (1.234,5); ngày dd/mm/yyyy; dòng ghi HỦY → bị chặn; trước mốc → nằm trong số dư.
"Kho nhà máy" của sổ bán hàng và "Kho thành phẩm nhà máy - APH" của sheet nhà máy phải ánh xạ về **cùng một kho**.

**Chạy thử với hai tệp thật (CSDL nháp, chỉ số tổng hợp, mốc 01/10/2026):** sheet nhà máy 510 dòng nghiệp vụ, sổ bán hàng 3.305 dòng;
phân loại toàn bộ ~3 giây. Kết quả trước khi ánh xạ thủ công: Đơn bán 1.425 nhập được / 45 chưa đủ / 2 bị chặn / 6 trước mốc; Sản xuất 92 / 16;
Nhập kho 83 / 1; Chuyển kho: 349 dòng liên quan nhà máy ↔ Hà Nội chờ ghép (77 cặp đề xuất tự động); Thu tiền: 370 dòng "ghi nợ" bỏ qua, 900
chưa đủ (chủ yếu **chưa ánh xạ quỹ theo hình thức** và **thiếu công ty**); tồn đầu nhà máy 202 dòng chờ ánh xạ **mã kho MISA** (BAO BI, NVL DO…).
Việc cần làm trước Go-Live: ánh xạ quỹ ("APH|tiền mặt", "APH|CK … MB"…), mã kho MISA của tồn đầu nhà máy, 48 dòng thiếu mã hàng, 32 phiếu
trả lại thiếu số XK gốc, ~300 phiếu thu thiếu công ty.

## 6. Bằng chứng kiểm thử (CSDL thử, không dùng dữ liệu vận hành)
| Hạng mục | Kết quả |
|---|---|
| `kiem_040.py` — 17 nhóm nghiệm thu + truy vết | **139/139 đạt**, mỗi nhóm kiểm số dư trước / sau |
| Bộ 0.3.2 nguyên vẹn (`chay_tat_ca.sh`, cấu hình tương thích) | api 53/53 · quyền 10/10 · golive 72/72 · toàn vẹn 47/47 |
| Đối chiếu bảo toàn (Σ sổ kho = tồn, Σ sổ giá trị = giá trị tồn, điều chỉnh cân) | CÂN sau mỗi nhóm và cuối cùng |
| Nâng cấp 0.3.2 → 0.4.0 trên bản sao CSDL 0.3.2 | Sổ kho 266 dòng / 46.699; giá trị tồn 1.039.156.000; sổ quỹ 2.764.501.000; công nợ còn 653.300.000; thu hộ 70.500.000; mẻ 224.550.000 — **trước = sau**. Chỉ thay đổi: giữ tồn cho 26 đơn đã duyệt đang chờ giao (12 dòng giữ thiếu được báo, không ép âm). Sau đó chạy lại toàn bộ bộ kiểm: đạt |
| Phục hồi bản sao lưu sau nâng cấp vào CSDL riêng | 35 bảng khớp số dòng, số dư khớp; app chạy trên bản phục hồi, đối chiếu CÂN |
| Giao diện | 13 màn mới + lập / chốt / in đơn gộp qua trình duyệt: không lỗi trang, không lỗi 5xx (`kiem/e2e-040.mjs`) |
| Bộ cài (docker giả) | checksum đúng → sao lưu + kiểm đọc được (166 bảng) → bảng / quyền → nâng cấp dữ liệu → đối chiếu CÂN; sai checksum → dừng |
| Kiểu (TypeScript) | máy chủ + giao diện: không lỗi |

17 nhóm điều kiện (mục 13 đặc tả) ↔ ca kiểm: Đơn gộp (3 đơn con đúng bên bán, chốt lại không tạo thêm) · Kho (một kho chung hai bên bán,
trừ đúng 294 kg) · Giữ hàng (2 người duyệt đồng thời, tổng giữ = ATP) · Giao hàng (đặt 500, xuất 485: kho −485, phải thu 485 × giá, 15 kg
chưa giao, nhả giữ) · Chuyển kho (3 lần xác nhận nhận đồng thời: HN +598 một lần, chênh −2 chờ xử lý) · Import (2 sheet một chuyến → 1
chứng từ; nạp lại / bản sửa không ghi lần hai) · Nhà máy (thiếu mã / lệch → rà soát, không ghi sổ; giá 0 không chốt) · Giá vốn (bán hết
rồi chốt lại: 500.000 vào giá vốn, lô mới giữ nguyên 3.000.000; chuyển 3 kho: chia theo vết, cân) · UOM (thùng → gói; bao bì Cái không vào
cân bằng kg) · Bảng giá (sỉ / bậc SL / hết hạn / lẻ POS gồm VAT / giá sàn / VAT 5 %) · Tín dụng (rủi ro chờ duyệt, nhân viên không duyệt;
khách thường cảnh báo, cam kết không cộng trùng) · POS (TM + CK, thối tiền, bấm lại không thêm tiền, khách lẻ trả thiếu bị chặn) · Thu hộ
(APH thu cho TL, nợ TL giảm đúng phần phân bổ có căn cứ) · Bank (nạp lại không thêm dòng / tiền, khớp 1 lần) · MISA (hàng đợi đúng bên
bán, chặn trùng số theo bên bán, trả hàng → cần điều chỉnh) · Quyền (NoCost qua API / nhúng quan hệ / xuất / truy vết; phạm vi mặc định từ
chối) · Migration (bản sao + phục hồi như trên).

**Truy vết xuyên suốt:** 1 bao bán qua đơn gộp tại kho Hà Nội → đúng một dòng sổ kho trừ 25 kg → nguồn tồn HN ← chuyến từ kho thành phẩm
nhà máy ← mẻ sản xuất ← NVL ← phiếu nhập; xuôi: đơn con bên bán APH thuộc đơn gộp → phiếu thu chuyển khoản vào tài khoản APH → hết nợ.

## 7. Checklist Go-Live
1. Sao lưu VM / máy đang chạy; `git pull`; `bash trien-khai/cai-dat.sh` (lưu báo cáo `sao-luu/nang-cap-0.4.0-*.json`).
2. Đọc báo cáo nâng cấp: danh sách người được cấp "mọi kho / mọi quỹ" → **thu hẹp phạm vi** từng người (Danh mục → Phạm vi).
3. Tạo khách `KHACH-LE`; khai kho "Hàng đang vận chuyển" (đánh dấu trung chuyển) nếu chưa có; tạo quỹ quầy bán nhanh; gán nhóm *Thu ngân*.
4. Khai bảng giá (sỉ theo nhóm khách, lẻ POS), nhóm giá + khách rủi ro + số ngày nợ trên danh mục khách; thuế suất / loại VAT, mã vạch,
   dung sai cân, "tính tiền theo" trên mặt hàng.
5. Trung tâm dữ liệu: đặt mốc → nạp 2 tệp (tải .xlsx từ Google Sheets) → ánh xạ đủ (kho, hàng, khách, công ty, quỹ) → phân loại → xác nhận
   cặp chuyến → ghi sổ theo nhóm (chuyến ghép, chuyển nội bộ, nhập, sản xuất, đơn bán, thu tiền, trả lại) → xử lý "Chưa đủ / Có thể trùng /
   Bị chặn" từng dòng (bổ sung hoặc bỏ qua có lý do).
6. Tồn đầu kỳ: "Tạo lô tồn đầu kỳ" → duyệt bảng lệch hai nguồn → Go-Live → kiểm / duyệt / ghi → khóa kỳ.
7. Chạy `kiem/doi_chieu.py` (CÂN) + Báo cáo → Tổng quan vận hành; đối chiếu tồn từng kho với kiểm kê thực tế, công nợ với sổ MISA.
8. Bật `ck_can_xac_minh = co` nếu muốn mọi CK của thủ quỹ chờ đối soát sao kê.

## 8. Sao lưu / quay lui
- `trien-khai/sao-luu.sh` (crontab hằng đêm): pg_dump + kiểm đọc được + tệp đính kèm, giữ 30 bản.
- `trien-khai/phuc-hoi.sh`: phục hồi THỬ vào CSDL riêng và so số dòng (không đụng CSDL đang chạy).
- `trien-khai/quay-lui.sh`: plugin cũ (`.cu-*`), tùy chọn kèm CSDL từ bản sao lưu trước nâng cấp (hỏi xác nhận).
  Nâng cấp dữ liệu 0.4.0 chỉ **thêm** bảng / trường / cấu hình / giữ tồn; quay lui plugin 0.3.2 trên CSDL đã nâng cấp vẫn chạy (bảng mới bị bỏ
  qua), nhưng để sạch hãy phục hồi CSDL từ bản sao lưu bước 1b.

## 9. Giới hạn còn lại (minh bạch)
- Cân điện tử / máy in nhiệt: chưa nối thiết bị (đặc tả cho phép 0.4.1). Quét mã vạch dạng bàn phím đã dùng được.
- Số lô / hạn dùng được lưu trên lượt giao / chuyến; chưa ép chọn lô (FEFO) khi xuất — giá vốn vẫn bình quân.
- Truy vết nguồn hình thành tồn theo bình quân: liệt kê chứng từ nhập theo tỷ trọng (không phải lô vật lý chính xác).
- Điều chỉnh giá trị theo vết đi tối đa 4 bậc chuyển kho; xa hơn coi là đã tiêu thụ (vào giá vốn) — kiểm cân vẫn bảo đảm.
- Import: đơn bán / thu tiền từ sổ nguồn được ghi như chứng từ đã thực hiện (đơn trước Go-Live không kiểm tín dụng); trả lại cần số XK gốc.
- Cặp chuyến chỉ đề xuất khi cùng mã hàng, cách ≤ 3 ngày, lệch ≤ 0,5 %; ngoài ngưỡng phải ghép tay / xử lý từng dòng.
- Thông báo qua Workflow NocoBase chưa cấu hình (hàng đợi đã có dữ liệu để gắn sau).
- Hóa đơn MISA: chỉ hàng đợi + ghi tham chiếu; không gọi API MISA.
