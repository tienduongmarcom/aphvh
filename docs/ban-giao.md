# Bàn giao dự án APH-VH

## 00000000000000. Bản 0.14.3 — 16/10/2026 (ĐANG KIỂM TRÊN CI) — an toàn nâng cấp khi production có dữ liệu

Theo rà soát của Codex (16/10, 6 điểm P0/P1 về triển khai, đã đối chiếu code: đúng cả). Không thêm tính năng.
- **Diễn tập tách biệt:** `dien_tap_ban_sao.sh` dựng mạng, MariaDB (mật khẩu ngẫu nhiên), Redis, ổ sites RIÊNG cho từng lượt
  (mã lượt ngẫu nhiên, nhãn `vn.9xlab.dien-tap=<mã>`), site `dt-<mã>`; tắt lịch chạy + thư; chỉ dọn tài nguyên mang nhãn của lượt.
  Production chỉ bị đọc (dấu vân + `bench backup`).
- **Dấu diễn tập ràng buộc** phiên bản, image ID, commit nguồn, sha256 `khach.json`, cờ mới, site đích, 12 giờ
  (`deploy/release/dau_dien_tap.py`, có test).
- **Bảo trì xuyên suốt:** `nang-cap.sh` kéo trước image, bật `maintenance_mode` + dừng lịch chạy + dừng worker TRƯỚC khi sao lưu,
  chỉ dựng lại web khi đổi image, migrate + kiểm trong bảo trì; lỗi thì tự quay lui và GIỮ bảo trì. `trien_khai_frontend.sh`
  giữ bảo trì tới hết bước so sổ; lỗi ở bất kỳ bước nào in nơi lưu bằng chứng + lệnh quay lui / mở lại.
- **Sao lưu kiểm đủ:** 4 thành phần (CSDL, tệp, tệp riêng, site_config) phải có, không rỗng, `gzip -t` / `tar -t` / JSON đọc được,
  ghi `sha256.txt`; `quay-lui.sh` kiểm sha256 trước khi ghi đè. Thiếu thì dừng trước khi đổi phiên bản.
- **So sổ chi tiết:** dấu vân thêm `chi_tiet` (GL theo công ty–tài khoản–đối tượng, PLE, SLE/Bin theo mã hàng–kho, chứng từ theo
  loại–công ty, số bao theo mã hàng–kho). Diễn tập và triển khai chặn khi lệch `tong`, `dem`, `chi_tiet` (thay đổi được duyệt
  trước khai bằng `DUOC_DOI`).
- **Duyệt đồng thời:** `du_lieu.duyet/tra_lai/gui` khóa dòng đề nghị (`SELECT … FOR UPDATE`); UAT b012 thêm ca hai lần bấm
  duyệt cùng lúc (9 ca).
- **Nhãn thẻ ngân hàng** (Bank Account) dịch theo ngữ cảnh: "Tài khoản kế toán (112x)", "Số tài khoản ngân hàng", "Chi nhánh",
  "4 số cuối", "Loại TK ngân hàng (không bắt buộc)"…
- **Cổng 3** chạy đúng các script trên: diễn tập tách biệt (kiểm không sót tài nguyên, tệp giao diện production không đổi),
  dấu sai bị từ chối trước khi bật bảo trì, `trien_khai_frontend.sh` thật, và ca cố ý làm hỏng bước kiểm → tự quay lui, giữ
  bảo trì, dữ liệu như trước.
- Bảng trạng thái phát hành một nơi: `deploy/release/TRANG_THAI.md`.

## 0000000000000. Bản 0.14.2 — 15/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND 22:44, ĐẠT, digest `0f528c3c…`; diễn tập bản sao ĐẠT 22:35: kiểm triển khai đạt, tong + dem khớp) — diễn tập bản sao production

Production đã có dữ liệu (1963 khách nhập lại giữ mã) nên bộ triển khai 0.14.1 dừng ở bước 1 "site không TRẮNG" (đúng thiết kế).
Anh Tiến chọn làm quy trình diễn tập bản sao. Thêm `deploy/release/dien_tap_ban_sao.sh <PB> [cờ mới]`: sao lưu frontend, chạy
image bản mới trong container TẠM cùng mạng/ổ sites, khôi phục vào site `dien-tap` (tắt lịch chạy, chép cờ + khóa mã hóa),
migrate + bộ cài (`co_du_lieu=1`) + cây kho + `kiem_trien_khai`, so `tong` sổ với frontend, xóa site tạm, ghi dấu
`~/dien-tap-<PB>.ok`. `trien_khai_frontend.sh`: site có dữ liệu thì đòi dấu diễn tập đúng bản, dưới 12 giờ, rồi chạy bộ cài chế độ
có dữ liệu (`cai_dat_tinh_nang.cai/kiem(..., co_du_lieu=1)`; mặc định vẫn đòi site trắng). Cổng 3 có thêm khách + nhà cung
cấp trên site CI, chạy chính script diễn tập bằng image ứng viên, và kiểm bộ cài từ chối khi thiếu `co_du_lieu`. 0.14.2 gồm
luôn 0.14.1 (chưa lên production).
Lỗi phát hiện khi diễn tập thật: container tạm chạy entrypoint của image nên chép tệp giao diện bản mới vào ổ sites dùng chung
("Linking fresh assets to volume") — vô hại lần này vì triển khai ngay sau; đã sửa bằng `--entrypoint bash` (bản sau).

## 000000000000. Bản 0.14.1 — 15/10/2026 (CI xanh, tag v0.14.1 phát hành; KHÔNG triển khai — gộp vào 0.14.2)

Theo dữ liệu anh Tiến gửi 16:22: `khach.json` mục `ngan_hang` 15 tài khoản (VH 5, APH 7, MK 3; chỉ 4 số cuối, tệp gốc có số
đầy đủ KHÔNG đưa vào repo). Đối chiếu sao kê đọc được tệp .xls (VietinBank), có sẵn mẫu cột ACB / MB / VietinBank, tự dò dòng
tiêu đề, khớp được khi mã giao dịch (FT…) nằm trong nội dung sao kê (ACB). Sửa lỗi: tên thẻ Bank Account trùng giữa hai đơn vị
(APH và VH cùng MB đuôi 9999) → thêm viết tắt đơn vị. Người thu / chi hộ (Trang, Ninh, Ánh): kế toán tạo trong danh mục Nhân viên.

## 00000000000. Lượt 0.14 (bản 0.14.0) — 15/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND 15/10 ~15:45, ĐẠT, digest `3a259c9b…`, 21 cờ; CI xanh trên 9fd3b28)

Đặc tả `docs/dac-ta-0.14.md` (mục 7b tránh trùng, 7c khác đặc tả). Cờ 20 `kh_aph_trung_tam_ban` (Workspace "Trung tâm Bán hàng",
giá sàn trên đơn chung theo đơn vị từng dòng, in lại phiếu xuất kho kèm số hóa đơn MISA + "In lại lần n"), cờ 21 `kh_aph_tien_vay`
(tài khoản ngân hàng từ khach.json, sổ quỹ / sổ tiền gửi tồn sau từng phiếu, thu / chi hộ của giám đốc qua 1388 / 3388 đối tượng
Nhân viên, khế ước vay + trích lãi 6351 / 3352 + dư nợ / lịch đến hạn + dòng tiền, đối chiếu sao kê .xlsx / .csv; Workspace "Tiền và vay").
Mang theo sửa bản dịch sau 0.13.0 (Submit → xác nhận…). Thử cục bộ: bộ `b014` 8/8 ca. Chờ anh: danh sách tài khoản ngân hàng
(đơn vị, ngân hàng, 4 số cuối, loại tiền), tên người thu / chi hộ, tệp sao kê mẫu. Sau 0.14: tạm dừng tính năng, gom vấn đề khi dùng.

## 0000000000. Lượt 0.13 (bản 0.13.0) — 15/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND 15/10 ~11:45, ĐẠT, digest `e3136592…`, 19 cờ)

Đặc tả `docs/dac-ta-0.13.md` (anh Tiến ok 09:28). Cờ 18 `kh_aph_kho_van_hanh` (Trung tâm Kho, chuyển kho khác R022, sửa SL nhập
sai R024 bằng hủy-sửa, đề nghị bổ sung R057–R059, chênh lệch kiểm kê bước 2), cờ 19 `kh_aph_gia_san` (giá sàn có bảng người duyệt,
kế toán bán hàng tự duyệt trong mức; quầy bán hàng: thu nhanh TM + CK, in phiếu xuất 2 liên, biên bản đối soát, thu hồi nợ;
vai trò "Kế toán bán hàng"). Đầu kỳ: ngày theo cấu hình, chốt khóa đến hết ngày đầu kỳ, phiếu tồn giá tạm chặn chốt, báo cáo
khách chưa có công nợ đầu kỳ. Ngày đầu kỳ chưa chốt (anh Tiến báo sau): đặt `bench --site frontend set-config kh_aph_ngay_dau_ky YYYY-MM-DD`.
Thử cục bộ: bộ `b013` 9/9 ca.

## 000000000. Lượt 0.12 (phát hành 0.12.1 = 0.11.5 + 0.12.0 + 0.12.1) — 14–15/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND 15/10 ~08:25, ĐẠT, digest `897f81c2…`)

Đặc tả `docs/dac-ta-0.12.0-0.12.1.md` (anh Tiến chốt 14/10 22:40). Hai cờ mới (16, 17):

| Cờ | Nội dung |
|---|---|
| `kh_aph_du_lieu` | Workspace "Trung tâm dữ liệu"; "APH De nghi so lieu" (kg tịnh, sản lượng mẻ, hao hụt, định mức mặc định) Dũng lập → chị Dung duyệt → app ghi, định mức đã xác nhận thì tạo bản mới; báo cáo rà soát thêm nhóm "Danh mục" (MST sai/trùng, thiếu kg tịnh, giá vốn 0 còn tồn, định mức mặc định, sản lượng lệch 20%). |
| `kh_aph_dau_ky` | "APH So du dau ky nguon" (số theo bảng nguồn), báo cáo "Doi chieu so du dau ky" (4 loại, số dư 9990, sổ kho = sổ cái), nút "Chốt số dư đầu kỳ" (khóa tháng bằng khóa kỳ 0.11.4). |

Sửa lỗi production: Opening Invoice Creation Tool hỏng vì `bag_stock.validate` đọc dòng không mã hàng → bỏ qua dòng đó.
Thử cục bộ: kịch bản APH/MK đạt; bộ HTTP `b012` 7/7 ca. Lệnh triển khai: `trien_khai_frontend.sh 0.12.1 kh_aph_du_lieu kh_aph_dau_ky`.

## 00000000. Bản 0.11.5 — 14/10/2026 (gộp vào lượt 0.12; CI xanh 661f8ac)

Không thêm cờ. Dịch thêm 651 chuỗi ERPNext 16.50 (kế toán, bán, mua, kho, sản xuất), tự bật Language `vi` khi cài
(`khach_hang.bat_tieng_viet`), test tệp dịch. Cổng 3 nâng cấp từ 0.11.4 (digest `54bf5a99…`, 15 cờ).
Từ đây gộp 2–3 bản mỗi lượt phát hành/triển khai (anh Tiến, 14/10 22:13).

## 0000000. Bản 0.11.4 — 14/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND ~22:15, ĐẠT)

Phát hành run 38582677234 xanh. Digest `sha256:54bf5a99f0174b234429e8e4541dc587e13e509461fb53fe8d0d9caa1543a881`.

Đặc tả `docs/dac-ta-0.11.4.md` (anh Tiến đồng ý 21:08). Cờ thứ 15 `kh_aph_quan_tri`, gồm:

| Phần | Nội dung |
|---|---|
| Báo cáo "Lai gop quan tri" | Cộng ngang 4 đơn vị, không phải hợp nhất kế toán. Xem theo công ty / kho / mặt hàng / khách / đơn. Có trả hàng, giảm giá sau giao, chi phí trực tiếp của đơn (bút toán có chọn ô "Đơn bán"), cờ lãi tạm tính. |
| Báo cáo "Dong tien 7 30 ngay" | Loại khoản nội bộ; khoản quá hạn hiện riêng. |
| Khóa / mở khóa kỳ | Dùng Accounting Period chuẩn. Bắt buộc lý do, có nhật ký. Chỉ khóa được tháng đã kết thúc. |
| Xác nhận công nợ (R039) | Cảnh báo mềm trên đơn bán. Báo cáo "Khach chua xac nhan cong no". |
| Chặn xem | Dũng và nhân viên bán hàng không xem được ba báo cáo trên. |

Kiểm thử:
- Thử cục bộ: bộ b0114 đạt 6/6 ca.
- Cổng 3 chuyển sang nâng cấp từ 0.11.3 theo digest `716f1401…`.
- Chi phí chuyến đã vào giá vốn hàng nhập (Landed Cost theo kg), nên không trừ lại trong "lãi sau chi phí trực tiếp".

## 000000. Bản 0.11.3 — 14/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND ~21:00)

**Phát hành và triển khai:**
- Phát hành: run `38570867103` xanh đủ 6 job.
- Triển khai bằng `trien_khai_frontend.sh`, kết quả ĐẠT:
  - nâng cấp 0.11.2 → 0.11.3 kiểm đạt; bản sao lưu trước nâng cấp: `sao-luu/20261014-135331`;
  - bộ dựng cây kho chạy lại "tạo 0"; kiểm triển khai "KHÔNG ĐẠT: 0";
  - tổng sổ trước và sau KHỚP.
- Digest image 0.11.3: `sha256:716f1401…bd2d8` (bản sau: Cổng 3 nâng cấp từ 0.11.3, 14 cờ).

Đặc tả: `docs/dac-ta-0.11.3.md` (E1–E9, anh Tiến đồng ý 18:30). Cờ thứ 14 `kh_aph_sales_p1` gồm các phần:
- **Trả hàng 2 chiều.** Phiếu trả hỏi hai ô: hàng trả về đâu (bán lại được / cách ly vào "Hàng cách ly <địa điểm>") và xử lý tiền thế nào (bù trừ / hoàn tiền / đổi hàng).
  - Hoàn tiền: app lập phiếu chi nháp theo số tiền.
  - Đổi hàng: app lập phiếu giao nháp từ đơn gốc.
- **Giảm giá sau giao.** Bút toán nháp loại Credit Note, chia theo tỷ trọng từng dòng và tách phần thuế. VH ghi Nợ 521; APH, MK, TL ghi giảm thẳng 511. Dòng 13 của bảng rà soát pháp lý chờ chị Dung xác nhận cách ghi này.
- **Hạn thanh toán chung của đơn.** Các hóa đơn tự sinh lấy chung hạn của đơn. Gia hạn bắt buộc có lý do và lưu lịch sử; khi gia hạn, app cập nhật hạn trên hóa đơn, lịch thanh toán và sổ công nợ PLE.
- **Đổi địa chỉ khi đang giao**, có nhật ký.
- **Báo cáo** "Don qua han giao".
- **Hồ sơ hóa đơn MISA** (`APH Hoa don ngoai`): hàng đợi "Hoa don cho xuat", khóa người xử lý chống trùng, Gốc / Điều chỉnh / Thay thế / Hủy; chênh lệch với doanh thu quản trị chỉ hiển thị, không chặn (Q148).

Kiểm thử và triển khai:
- CI xanh trên `dc6aa1b`: UAT candidate `38567486172` (đủ các bộ, gồm b0113 13 PASS), Cổng 3 `38567486151` (nâng cấp từ 0.11.2), Cổng 2 `38567493935`.
- Ba lần đỏ trước đó được giữ làm bằng chứng:
  - Phiếu trả bắt buộc chọn hai ô làm hỏng bộ inventory → đổi sang điền mặc định.
  - ERPNext 16.50 đòi ngày dạng chuỗi ở `get_payment_terms`.
  - Hạn chung bị điều khoản của khách ghi đè → đặt sẵn lịch thanh toán một dòng.
- Cổng 3 chuyển sang nâng cấp từ 0.11.2 theo digest `f2417393…`, dựng cây kho ở bước 1 giống production.
- Script triển khai một lệnh: `deploy/release/trien_khai_frontend.sh <phiên bản> <cờ mới…>`.
- Mục BA 15 (báo cáo quản trị, R039, khóa kỳ) làm ở 0.11.4.

## 00000. Bản 0.11.2 — 14/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND ~17:10)

**Phát hành:** run "Phát hành image v0.11.2" `38543418851` xanh đủ 6 job. Image `kh-aph-erpnext:0.11.2`, nguồn `8201b87`.

**Triển khai** bằng một script gộp (`~/trien-khai-0112.sh` trên VM, cùng các bước như TRIEN_KHAI_FRONTEND.md):
- Nâng cấp: "XONG: 0.11.1 -> 0.11.2, kiểm đạt". Bản sao lưu trước nâng cấp: `sao-luu/20261014-100602` (dùng khi cần quay lui).
- Cây kho: lần 1 tạo 55 kho, cảnh báo 0; lần 2 tạo 0.
- Kiểm triển khai: "Cây kho chuẩn đủ (55 kho) ĐẠT", không có mục KHÔNG ĐẠT.
- Dấu vân: phần tong KHỚP.
- Digest: 0.11.1 `sha256:9335dfa1…f8424` (đã ghim vào Cổng 3), 0.11.2 `sha256:f2417393…09ca3` (ghi ở `phien-ban.yaml`; bản sau Cổng 3 nâng cấp từ 0.11.2).

**Chưa phải PASS nghiệp vụ:** khách chưa nhập dữ liệu thật. Cấu hình khách cần làm sau 0.11.2 được liệt kê trong TRIEN_KHAI_FRONTEND.md.


Đặc tả và bảng nơi đặt code: `docs/dac-ta-0.11.2.md` (mục 9). Quyết định K1–K6 chốt 14/10 — không hỏi lại.

- **Cờ thứ 13 `kh_aph_kho_chuan`** (mặc định tắt): cây kho chuẩn do app dựng từ `khach.json` mục `cay_kho`
  (`kh_aph.kho_chuan.dung`, chỉ thêm kho thiếu, 55 kho cho 4 pháp nhân), ô Loại kho / Dây chuyền, chặn bán từ kho không
  bán, loại phiếu "Đóng gói thành phẩm" (CĐ2), nhóm "Bao bì đóng gói" chỉ cộng tiền không cộng kg, kiểm kê có mốc (thiếu
  Nợ 1381, thừa vào kho "Hàng chờ xử lý <địa điểm>" Có 3381, ngưỡng % đòi lý do).
- **Quyết toán dở dang về 0** (`factory_costing.quyet_toan_do_dang`): có định mức → tự chia 15488 / 6322 theo TT133 TK154
  1(đ); không có định mức → kế toán chọn. Cảnh báo lệch định mức R073. Báo cáo "Tieu hao so voi dinh muc".
- Sửa lỗi 0.11.1: "Đổi bao, đóng gói lại" cộng cả kg túi PP vào cân đối kg. CĐ2 không nhận phân bổ chi phí tháng.
- Dấu vân: Property Setter cột danh sách (in_list_view/columns/in_preview) sang phần `giao_dien` — giải thích lệch 220/216.
- Thử cục bộ 15/10 (bench v16, dữ liệu giả): bộ b0112 đủ 12 ca, bộ b0111 đủ 13 ca khi bật cờ mới. CI: chờ run xanh.
- Cổng 3 nâng cấp từ tag 0.11.1; `PROD_DIGEST` để trống (kéo theo tag) — lấy digest ở bước 1 của thủ tục 0.11.2.
- Thủ tục lên production: `deploy/release/TRIEN_KHAI_FRONTEND.md` (đầu tệp).

Còn chờ chị Dung (không chặn code): bước 2 xử lý chênh lệch kiểm kê; 3389 hay 9990 cho số dư đầu kỳ; xác nhận 6323 (D2).
Tiếp theo: 0.11.3 (P1 bán hàng / hóa đơn / báo cáo) → 0.12.0 Trung tâm dữ liệu → 0.12.1 số dư đầu kỳ → 0.13.0 giao diện Kho.

## 0000. Bản 0.11.1 — 14/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND ~14:50)

- Phát hành: tag `v0.11.1` = `a2ab58c`; run phát hành 38526754413 xanh (UAT candidate có 14/14 ca 0.11.1, Cổng 2, 2b, 3
  nâng cấp từ image production 0.11.0 `sha256:6bc8f302…`). Repo chuyển công khai 14/10 để chạy Actions miễn phí.
- Trên VM theo `TRIEN_KHAI_FRONTEND.md` mục 0.11.1: nâng cấp 0.11.0 → 0.11.1, bật 4 cờ mới (12/12), bộ cài + kiểm; dấu vân
  sau: `tong` khớp. Sao lưu trước nâng cấp `~/erp/aph-vh/sao-luu/20261014-074331`, Cloud Storage `aph-vh/2026-10-14_1443`. Bộ cài: idempotent 2 lần, CF 147, Custom DocPerm 535, Property Setter 220 (CI cùng bản: 216, chênh 4 — xem lại khi làm 0.11.2, không chặn); `kiem_trien_khai` 53 dòng KHÔNG ĐẠT: 0. Quay lui trước khi nhập liệu: `cd ~/erp/aph-vh && ./quay-lui.sh 20261014-074331`. VM báo *System restart required* (cập nhật hệ điều hành): khởi động lại trong khung bảo trì.
- Việc tiếp: cấu hình khách sau 0.11.1 (TRIEN_KHAI_FRONTEND.md), chị Dung xác nhận D2 (6323), làm 0.11.2 (P1).

### Ghi chép lúc làm 0.11.1

- Nguồn yêu cầu: đánh giá BA (`docs/ba/danh-gia-BA-0.11.1.md`) và quyết định của anh Tiến ngày 14/10 (D1 chi tiết 154 cho
  APH; D2 nhà máy chung vào 6323, chờ chị Dung xác nhận; D3 chia 0.11.1 P0 / 0.11.2 P1). Đặc tả có hiệu lực:
  `docs/dac-ta-0.11.1.md`.
- Đã làm:
  - Giá thành nhà máy (kg-v4 hệ số, giá tạm, 1548x/6323, phân bổ cuối tháng, vét bồn, "Đổi bao, đóng gói lại").
  - Phiếu quỹ nhà máy của Dũng; khóa giá thành phẩm chính.
  - Bán hàng: cảnh báo giá vốn chỉ kế toán thấy; xe quay về / chuyển khách; mã khách KH-; đóng phần chưa giao; biên bản
    không giá, có cột thực nhận, in bao + kg.
  - Báo cáo "Dữ liệu cần rà soát".
- Sửa 2 lỗi có trên production 0.11.0 (đặc tả mục 3.13):
  - Hook quyền trả `None` chặn kế toán mở GL / Purchase Invoice / kiểm kê / LCV / BOM / Work Order.
  - Lộ giá vốn trong phản hồi lưu đơn của nhân viên bán hàng.
  - **Phải lên 0.11.1 trước khi khách nhập liệu.**
- Kiểm:
  - Unit test: lab9x 58 OK, kh_aph 213 OK.
  - 13 ca HTTP 0.11.1 PASS trên máy thử (16.36).
  - **CI commit `a843837` chưa chạy**: GitHub báo tài khoản hết hạn mức hoặc lỗi thanh toán Actions. Anh Tiến sửa Billing
    xong thì chạy lại.
- Cổng 3 đổi nền sang production 0.11.0 (8 cờ bật + bộ cài 0.11.0). `PROD_DIGEST` = `sha256:6bc8f302…19f4` (RepoDigests đọc trên VM 14/10 13:00).
- Triển khai: `deploy/release/TRIEN_KHAI_FRONTEND.md` phần 0.11.1 (bật thêm 4 cờ + bộ cài) và cấu hình khách sau triển khai.
- Việc chuyển 0.11.2 (P1): trả hàng 5 tình trạng, giảm giá sau giao, hạn thanh toán / gia hạn, giao nhiều địa chỉ, kiểm kê
  có mốc, hàng đợi hóa đơn MISA, báo cáo quản trị, xác nhận công nợ, khóa kỳ.

## 000. Triển khai 0.11.0 lên frontend — 14/10/2026 (ĐÃ XONG)

- Phát hành: tag `v0.11.0` = `96fad42`, run 38502150872 xanh (UAT candidate, Cổng 2, 2b, 3 trên nền ghim
  `frappe/erpnext@sha256:ac5b4591…` = ERPNext 16.50.0 + Frappe 16.51.0). Image id trên VM `sha256:6bc8f302…19f4`.
- Nội dung 0.11.0: chặn lối in/xem trước bỏ qua bước xóa giá (`print_guard`), vai trò nhà máy chọn được mẫu thuế mua vào,
  mẫu in mặc định của app trên cài mới 16.50, `confirm()` chỉ trả trường giao/nhận, ghim digest nền, dấu vân thêm Settings.
  Cổng 3 chứng minh dấu vân trước nâng cấp của CI trùng frontend thật (770 mục, sha `9d30afd41f4bbb71`).
- Trên VM: kiểm kê trước = TRẮNG, 8/8 cờ; sao lưu Cloud Storage; `nang-cap.sh 0.11.0` → kiểm đạt, sao lưu trước nâng cấp
  `~/erp/aph-vh/sao-luu/20261014-033739`; bộ cài + kiểm idempotent (CF 125, Custom DocPerm 519 = +27 quyền từ patch ERPNext
  16.50 và quyền chọn mẫu thuế, Property Setter 214); `kiem_trien_khai` KHÔNG ĐẠT: 0; tổng sổ và số bản ghi khớp; sao lưu sau.
- Quay lui trước khi nhập liệu: `cd ~/erp/aph-vh && ./quay-lui.sh 20261014-033739` (về 0.10.0 trên ERPNext 16.36).

## 00. Triển khai 0.10.0 lên frontend — 14/10/2026 (ĐÃ XONG)

- Phát hành: tag `v0.10.0` = `3233607`, run 38491147844 xanh (UAT candidate, Cổng 2, 2b, 3, đẩy image).
  Image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.10.0@sha256:ca7cebd73b4695b2370d564fa2830e048d3bfa6542a359fa91950c4cea915d31`.
- Trên VM `erpnext-prod` (theo `deploy/release/TRIEN_KHAI_FRONTEND.md`): kiểm kê trước = TRẮNG (schema 770 mục, mọi cờ tắt);
  sao lưu Cloud Storage; `nang-cap.sh 0.10.0` → "kiểm đạt", sao lưu trước nâng cấp `~/erp/aph-vh/sao-luu/20261014-010809`;
  6 service cùng image 0.10.0; bật 8 cờ; `cai_dat_tinh_nang.cai` + `kiem` → idempotent (CF 125, Custom DocPerm 492,
  Property Setter 214); `kiem_trien_khai` KHÔNG ĐẠT: 0; dấu vân sau: tổng sổ khớp, chỉ thêm 8 DocType mới (0 bản ghi);
  sao lưu Cloud Storage sau nâng cấp. Desk: danh sách APH Shared Sales Order và form Delivery Note (Trạng thái giao hàng) mở được.
- Quay lui trước khi nhập liệu: `cd ~/erp/aph-vh && ./quay-lui.sh 20261014-010809`. Sau khi đã nhập liệu: không khôi phục, sửa tiến.
- Chưa phải nghiệm thu nghiệp vụ: chưa có người dùng/kho/mặt hàng thật; xem `docs/doi-chieu-quyet-dinh-202.md` (nhánh 0.11).

## 0. Cập nhật 13/10/2026 (đọc trước — các mục 1–7 bên dưới là trạng thái 09/10, giữ làm lịch sử)

- **Production = site `frontend`** trên VM `erpnext-prod` (không phải "UAT" như ghi 09/10). Kiểm kê chỉ đọc 13/10: vẫn
  trắng (0 khách/mặt hàng/chứng từ/GL/SLE), image `0.9.1@sha256:ce755900…` cho cả 6 service, mọi cờ tắt.
- **Codex 10–13/10** (PR #1, nhánh `fix/p0-uat-v091-20261010`) thêm nghiệp vụ lớn sau cờ site_config: đơn chung nhiều
  công ty, nợ lúc giao, giao/nhận, bao+kg, nhập chờ định giá, chi phí chuyến theo kg, sản xuất kg, tiền thực thu/cọc,
  APH nhận hộ TL, đổi nguồn, hạn mức chung, chặn Dũng xem giá vốn. Bằng chứng: UAT candidate 110 ca HTTP/Chrome 0 FAIL
  trên SHA `3ef5cf0` (run 38337814455), Cổng 2 xanh (run 38337817607). Quyết định nghiệp vụ: `docs/quyet-dinh-nghiep-vu.md`.
- **Claude 13/10, bản 0.10.0**: bộ cài production `kh_aph.cai_dat_tinh_nang` (dùng chính schema UAT, khóa site/cờ/
  site trắng), Cổng 3 diễn tập nâng cấp từ đúng image production + quay lui có so dấu vân, `quay-lui.sh` trả lại cờ,
  thủ tục `deploy/release/TRIEN_KHAI_FRONTEND.md`. Gộp các commit 09/10 (dung.sh hỏi mật khẩu, sao lưu PREFIX).

**Việc còn mở (theo thứ tự)**
1. ~~CI xanh cùng SHA~~ — **đạt 13/10 trên `55b4491`**: UAT candidate run 38361750647 (110 ca), Cổng 2 run 38361758496,
   Cổng 3 run 38361750585 (nâng cấp từ digest production, bộ cài + ca từ chối, schema khớp site mới, quay lui khớp dấu vân).
   Ghi nhận: UAT candidate run 38359275943 trên `3baba2e` FAIL ở bước hồi quy HTTP, không đọc được log; app code giống hệt
   `b6ce8cf`/`55b4491` (đều SUCCESS) → lỗi không ổn định, chưa rõ nguyên nhân; theo dõi nếu lặp lại (nay có chú thích lỗi).
   Cổng 2b chạy khi phát hành.
2. Chủ dự án gắn tag `v0.10.0` → workflow Phát hành xanh → ghi digest image.
3. Cửa sổ triển khai theo `TRIEN_KHAI_FRONTEND.md` (kiểm kê lại trước: còn trắng mới làm; có dữ liệu thì đi quy trình
   bản sao trong `RELEASE_GATES.md`).
4. Sau triển khai, trước nhập giao dịch thật: người dùng thật (Dũng = "APH Không xem giá vốn", kế toán trưởng duyệt,
   người giao/nhận), cây kho lá đúng chủ, mặt hàng Kg/MA/kg-bao, số bao mở đầu theo kiểm kê vật lý, tài khoản
   ngân hàng/giữ hộ/phải thu nội bộ do kế toán trưởng duyệt. Chạy `handoff_preflight.inspect` để kiểm.
5. Chưa được ghi PASS (P1): stress đồng thời đổi nguồn/giao, mọi amendment, đọc sao kê mọi ngân hàng, máy in thật,
   xác nhận nợ từ xa, vai trò người thật, thuê ngoài/hóa đơn NCC thật, đủ 202 quyết định (cần bản gốc).
6. Từ 09/10 còn: tên đầy đủ MK/TL, cách lấy tồn đầu kỳ (kiểm kê 30/09 hay 01/09 cộng trừ), 4 mục pháp lý chưa đối chiếu.


Tài liệu cho người/tác tử tiếp nhận phát triển tiếp khách **An Phú Hưng - Vĩnh Hưng**. Đọc kèm `AGENTS.md` (quy tắc làm việc)
và `docs/quy-trinh-trien-khai-khach.md` (quy trình triển khai chi tiết).

## 1. Trạng thái tại ngày bàn giao

| Hạng mục | Trạng thái |
|---|---|
| Phiên bản | `kh_aph` **0.9.1**, `lab9x` **0.2.0**, ERPNext/Frappe **v16.36.1**. Commit cuối trên `v0.3-review`: sao lưu cloud cấu hình được. |
| Image | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.9.1` (repo GitHub private `tienduongmarcom/aphvh`). Cổng 2, Cổng 2b, Phát hành: xanh. |
| Unit test | lab9x 48, kh_aph 101 — đạt. |
| Máy UAT | GCloud VM `erpnext-prod` (asia-southeast1-a, 2 vCPU, 3,8 GB RAM, 38 GB đĩa, x86_64). Dựng bằng `dung.sh aph-vh 0.9.1 khach/aph-vh/khach.json` tại `~/erp/aph-vh` (repo clone ở `~/trien-khai`), compose project `erp-aph-vh`, site `frontend`, host_name `http://<IP máy chủ erpnext-prod>`. Bộ kiểm triển khai: đạt toàn bộ. |
| Sao lưu | `/usr/local/bin/erpnext-backup.sh` + `erpnext-backup.timer` (02:30 và 12:30 giờ VN) → `gs://project-5ffa5918-411e-4199-a40-erpnext-backup/aph-vh/<ngày_giờ>/`. Cấu hình `/etc/erpnext-backup.conf` (BUCKET, CONTAINER=erp-aph-vh-backend-1, VOLUME=erp-aph-vh_sites, PREFIX=aph-vh). Đã chạy thử đạt 09/10/2026. Thư mục `frontend/` trong bucket là bản sao lưu của hệ thống cũ đã xóa, để nguyên. |
| Đăng nhập GHCR trên máy chủ | Token chỉ có `read:packages`. |
| Dữ liệu | Site trắng (chế độ `tu_nhap`), chưa có dữ liệu của khách. Kế toán khách tự tạo cây kho, nhóm hàng, danh mục. |
| Production | Chưa dựng. Dựng sau khi khách ký UAT (máy riêng, cùng quy trình). |
| Hệ thống cũ | App `aphvh` cũ (cổng 8086, 8081 trên máy thử) **không** nâng cấp lên `kh_aph`; không đụng nếu chưa được chủ dự án cho phép. |

## 2. Cấu hình khách (`khach/aph-vh/khach.json`)

- `che_do_du_lieu: tu_nhap`, `ngay_chot: 2026-09-30` (số dư đến hết 30/09 mang sang; chứng từ từ 01/10 nhập từng phiếu).
- APH — "CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI VÀ XUẤT NHẬP KHẨU AN PHÚ HƯNG", `thong_tu: 133`, MST 2601002157.
- VH — "CÔNG TY CỔ PHẦN THƯƠNG MẠI VĨNH HƯNG", `thong_tu: 99`, MST 0500470349.
- MK — "HỘ KINH DOANH MINH KHANG", `thong_tu: 152` (**tên tạm**, chờ khách xác nhận).
- TL — "TL", `noi_bo: true` (không thông tư, không MST, không VAT; **tên tạm**).
- Mã thông tư → viết tắt: `133→aph`, `99→vh`, `152→mk`, nội bộ → `tl` (`kh_aph/khach_hang.py::THONG_TU`).
- `loai_hinh`: `thuong_mai` (nhóm Hàng hóa, CCDC, Dịch vụ, Tài sản) hoặc `san_xuat`. Không có mục kho.

## 3. Quyết định của chủ dự án (đã chốt — không hỏi lại)

1. Mỗi khách một VM Docker; image theo phiên bản; repo là nguồn sự thật; UAT trước production.
2. Phát hành phải qua Cổng 1, 2, 2b. Chủ dự án tự gắn tag (tác tử không push tag).
3. Hai chế độ dữ liệu `tu_nhap` / `import_mot_phan` + `ngay_chot`. Mình không chạm dữ liệu thật.
4. Không tạo kho trong app; dữ liệu trắng cho khách đầu tiên.
5. Thuế GTGT mua vào: tự gắn dòng 1331 nhưng **kế toán chọn thuế suất** (thuế suất đổi theo chính sách từng năm, 8% ↔ 10%).
   Chặn nhầm chiều: 33311 trên phiếu mua, 1331 trên phiếu bán.
6. Ô "Khách lấy hóa đơn": mở cho khách dùng trước, đóng khi khách hoàn thiện. **Hóa đơn điện tử vẫn lập trên MISA.**
7. Nhóm hàng: kế toán sửa linh hoạt, app giữ sổ không lệch (lõi `lab9x/nhom_hang.py`).
8. Giao diện: chỉ No-Code/Low-Code, giữ kiểu Frappe + nhận diện 9xLab. App theme `aphvh_theme` (chỉ biến CSS) **dự kiến, chưa làm**.
   Thử theme Aurora đã bỏ.
9. MacBook chỉ để xem giao diện, không dùng để kiểm chứng.

## 4. Tính năng hiện có

**Lõi `lab9x`** (quy tắc thuần + hook): bảng tài khoản chuẩn TT133/TT99 (`bang_tai_khoan`), tài khoản HKD TT152 (`hkd_accounts`),
sổ HKD (`so_hkd_rules`), thuế GTGT theo loại khách (`vat_rules`), mẫu in tiếng Việt (`print_rules`, `vn_words`), kiểm soát kế toán
(`control_rules`), cảnh báo bán hàng (`sales_rules`), thanh toán qua bên thứ ba, thu hộ, tồn kho theo tài khoản × địa điểm,
tổng hợp bán theo khách, chia giá theo kg (`costing_rules`), **nhóm hàng/tài khoản kho** (hook Item Group, Item).

**App `kh_aph`** (gắn ERPNext):
- Cài bản trắng (`cai_ban_trang.py`): hệ thống tài khoản chuẩn, nhóm hàng cấp 1 gắn tài khoản kho, nhóm mặc định "HH - Hàng hóa",
  mẫu thuế, tài khoản mặc định, gỡ kho/nhóm/tài khoản mẫu của ERPNext; hỗ trợ HKD và đơn vị nội bộ.
- Bộ nạp cấu hình khách (`khach_hang.ap_dung`) và bộ kiểm sau triển khai (`kiem_trien_khai.chay`, ~53 dòng ĐẠT/KHÔNG ĐẠT cho 4 công ty).
- Phiếu kho "Đóng gói theo kg" chia giá thành phẩm theo kg, giữ đúng khi repost (`stock_entry_kg.py`).
- Vai trò Kế toán nhà máy (ẩn giá màn hình + bản in + xem trước sổ), Nhân viên bán hàng, Thủ kho bán hàng (`price_visibility.py`).
- Luồng bán: cảnh báo công nợ/giá, hóa đơn nháp tự tạo từ phiếu giao hàng, cờ có/không xuất hóa đơn GTGT, khách vãng lai thu tiền ngay.
- Thuế GTGT bán theo loại khách, thuế mua vào 1331, chặn nhầm tài khoản thuế (`vat.py`).
- Kiểm soát: chặn ngày tương lai, không ghi tay vào tài khoản kho, cảnh báo tiền mặt lớn, thu hộ, đơn vị chuyển tiếp TL.
- 6 mẫu in (Phiếu nhập kho, Phiếu kho, Phiếu xuất kho bán hàng, Biên bản giao nhận, Phiếu thu chi, Phiếu bán hàng).
- 7 báo cáo (Tồn kho số lượng, Bán hàng có hóa đơn, Tổng hợp bán hàng theo khách, Sổ doanh thu HKD, Sổ kế toán HKD,
  Tiền thu hộ chưa xử lý, Tồn kho theo tài khoản và địa điểm). Bản dịch `kh_aph/translations/vi.csv`.

## 5. Việc còn mở (theo thứ tự ưu tiên)

**Chờ khách**
1. Tên đầy đủ của HKD Minh Khang và TL → sửa `khach/aph-vh/khach.json` (và `deploy/khach/mau-aph-vh.json`).
2. Tồn kho đầu kỳ: quyết định cũ là kiểm kê 01/09 (bút toán ngày 31/08), nay ngày chốt 30/09 — kế toán chọn **kiểm kê lại tại 30/09**
   hay **lấy số 01/09 cộng trừ phát sinh tháng 9**. Chưa chốt thì chưa làm công cụ nhập tồn đầu.
3. Bốn mục pháp lý "chưa đối chiếu điều khoản" trong `docs/bang-ra-soat-phap-ly-APH-VH.md` (#2 bán không hóa đơn ở TL, #6 hóa đơn
   bù/điều chỉnh, #10 HKD Minh Khang TT152/NĐ 68/2026, #11 mức phạt NĐ 310/2025) — cần đọc văn bản gốc / kế toán xác nhận.

**Phát triển**
4. `dung.sh`: lấy IP ngoài từ GCP metadata (`http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip`,
   header `Metadata-Flavor: Google`) cho host_name, thay vì `hostname -I` (ra IP nội bộ 10.148.0.2).
5. Workflow "Triển khai khách": chọn khách hoặc tất cả, chờ duyệt (environment), SSH vào VM chạy `nang-cap.sh`. Chủ dự án tự thêm
   khóa SSH vào GitHub Secrets.
6. Công cụ import dữ liệu một phần (`import_mot_phan`): mẫu import danh mục + số dư tại `ngay_chot`, công cụ kiểm dữ liệu trước import.
   Dữ liệu giả cho UAT.
7. Chuyển phần gắn ERPNext dùng chung (controls, vat, mẫu in, báo cáo, custom field) từ `kh_aph` sang `lab9x`; tách phần chỉ APH có
   (đơn vị chuyển tiếp TL). Mục tiêu: khách mới chỉ cần `kh_<ten>` mỏng.
8. Lệnh/skeleton `khach-moi` (tạo `khach/<ten>/`, app `kh_<ten>`).
9. App theme `aphvh_theme` (nhận diện 9xLab, chỉ biến CSS).
10. Tên miền + HTTPS cho UAT/production; dựng production sau khi khách ký UAT.
11. Dọn: `kh_aph/_thu*.py` (tệp thử cục bộ, đã gitignore); `README.md` gốc còn ghi lịch sử 0.1–0.3 với tên cũ "APH".

## 6. Lệnh vận hành thường dùng (trên máy chủ)

```bash
cd ~/erp/aph-vh
./erpctl ps                                     # trạng thái
./erpctl exec backend bench --site frontend migrate
./nang-cap.sh <phiên bản>                       # nâng cấp, tự sao lưu trước, tự quay lui khi lỗi
./quay-lui.sh <thư mục trong sao-luu/>          # quay lui bằng tay (vd 20261006-153000)
sudo systemctl start erpnext-backup.service && sudo journalctl -u erpnext-backup.service -n 30 --no-pager
```

Repo trên máy chủ là private; máy chủ không còn token `repo`, muốn `git pull` phải nhập token tạm (`read -s GH_TOKEN`) rồi bỏ.

## 7. Tài liệu liên quan

- `docs/quy-trinh-trien-khai-khach.md` (= `deploy/khach-hang/README.md`): phương án final, chế độ dữ liệu, quy tắc giao diện, an toàn.
- `docs/doi-chieu-tai-khoan-thong-tu.md`, `docs/thu-ho-tai-khoan-chuan-phap-ly.md`, `docs/ban-cai-trang-0-5-2.md`, `docs/bang-ra-soat-phap-ly-APH-VH.md`.
- `deploy/cloud/README.md`: sao lưu.
- `NGHIEM_THU.md`: biên bản nghiệm thu các bản 0.1–0.2.
- Dữ liệu sổ MISA mẫu của khách nằm trong Project claude.ai "Hơp nhất APH - VH" (không có trong repo; không dùng làm dữ liệu thử ngoài máy khách).
