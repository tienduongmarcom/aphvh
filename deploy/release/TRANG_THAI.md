# Trạng thái phát hành APH-VH (một nơi duy nhất — cập nhật mỗi lần phát hành / triển khai)

## 17/10/2026 — Khép luồng tiền và phạm vi báo cáo (đang kiểm)

Tiếp tục PR #4 theo xác nhận của anh Tiến: rà thu/cọc–phân bổ–bàn giao–sao kê, nhà máy và tài chính bằng dữ liệu giả; gom nghiệm thu thật sau khi có danh mục/tồn kho. Production vẫn0.15.1.

Bản sửa: xác nhận nhận tiền nhà máy kiểm quyền phiếu/Company, chặn sửa tay kết quả ghi sổ và gắn JE có sẵn, kiểm số tiền hữu hạn/tối đa2 số lẻ. Sao kê kiểm quyền File/Account; lưu mẫu dùng quyền write Bank và save chuẩn. Phiếu tiền/cọc ghi đúng tham chiếu thực thu/chi vào JE; mã giao dịch chung theo Account áp PE/JE/FundsReceipt/FundsAction, khóa tài khoản và đọc hiện tại để chặn nhập đồng thời qua các lối khác nhau. Xác minh khách/tạo kế hoạch chỉ POST.

Báo cáo lãi gộp/dòng tiền/công nợ giới hạn Company được cấp; lọc ngoài phạm vi bị chặn. Phân loại đối tác nội bộ vẫn xét đủ đơn vị để không tính nhầm dự thu/chi. Người chỉ xem một phần không được ghi xác nhận công nợ chung toàn khách; báo cáo không so số dư một phần với số xác nhận chung. Hồ sơ Dũng vẫn chặn dù cộng Accounts Manager.

Kiểm cục bộ trước mở rộng phạm vi sổ quỹ/vay:264 kh_aph +107 lab9x=371 ca đạt. Đã bổ sung kiểm Company cho sổ quỹ, công nợ giám đốc, khế ước và khóa/mở khóa kỳ; lấy danh sách khế ước qua quyền native thay get_all. Có ca HTTP scope APH cùng đối chứng ngoài phạm vi VH. UAT mở rộng: funds20, b0111=15, b0114=8, b014=23 (gồm restore); thêm tài khoản giới hạn Company, tệp riêng không chia sẻ, chặn sửa mẫu Bank không có quyền và hai phiên tạo JE cùng mã. Giữ các ca nghiệp vụ cũ, không nới assertion. Cần đọc CI trên SHA mới; mốc7827add không nghiệm thu cho thay đổi này.

ĐANG DỞ: đẩy bản sửa và chạy UAT/Cổng2/2b/3, sửa nguyên nhân nếu lỗi; đọc artifact đối chiếu/khôi phục. Không tag/merge/triển khai. Các nghiệp vụ giá thành/nhà máy và tài chính có sẵn được hồi quy trong cùng bộ UAT; chưa coi nghiệm thu người dùng thật hoặc toàn bộ202 quyết định hoàn tất.

## Mốc kiểm ngày 17/10/2026 — hồ sơ giao nhận và hàng đợi tiền

Mã nguồn ứng viên `7827add608f7cee8af59c62f69df506660c8cbc3`, PR #4, nhánh `feat/ho-so-giao-nhan-20261017`. Chưa phát hành hoặc triển khai; production vẫn 0.15.1. Người dùng yêu cầu tiếp tục bằng dữ liệu giả và gom nghiệm thu thực tế sau khi có danh mục hàng/tồn kho.

Đã có bản ký riêng tư gắn đúng Delivery Note, ghi chú chênh lệch, người/thời điểm đối chiếu. Kiểm quyền đọc/ghi và modified; thay tệp/ghi chú làm mất dấu đối chiếu. Chặn xóa blob trước native File.on_trash bằng extend_doctype_class; chặn công khai/đổi liên kết tệp đang tham chiếu. Có nút gỡ bản ký trên phiếu, không bắt đính kèm khi giao/nhận. Không ghi sổ lần hai. Workspace Bán hàng và Tiền/vay gom phiếu thiếu hồ sơ, chờ đối chiếu, tiền chưa rõ khách, phân bổ nháp, bàn giao tiền chờ nhận/chênh lệch.

Cổng 1: 254 kh_aph + 107 lab9x = 361 ca đạt (Python 3.12/Jinja2). UAT run 39011438406: 209 kết quả PASS/0 FAIL trong artifact, gồm 21/21 b014 và khôi phục; có ảnh Desk, kiểm tải lại blob sau yêu cầu xóa bị chặn. Cổng 2 run39011440839 đạt; Cổng 2b39011438502 đạt. Cổng 3 run39011438376 đạt: so schema, quay lui chủ động và nâng lỗi tự quay lui/giữ bảo trì, dấu vân dữ liệu khớp. Đủ bốn cổng trên SHA7827add. Các bằng chứng này thuộc SHA7827add; cập nhật tài liệu sau đó không được gọi là kiểm lại mã nguồn mới.

ĐANG DỞ: không coi toàn dự án hoàn tất. Theo `docs/nghiem-thu-tong-the.md` tiếp tục rà các khoảng trống thực sự trong luồng giữ tiền/nhà máy/tài chính; nhiều mục trong bảng 202 ngày14/10 đã được làm ở0.11.x–0.14, không xây lại theo bảng lịch sử. Nghiệm thu bằng nhân sự/máy in/dữ liệu thật còn chờ danh mục/tồn kho/số dư và cấu hình khách. Không tự tag, merge hoặc triển khai production.


## 17/10/2026 — Phát triển tiếp, gom nghiệm thu thực tế sau khi có dữ liệu

Anh Tiến xác nhận chưa có danh mục hàng/tồn kho nên chưa thử thực tế; yêu cầu tiếp tục hoàn thiện và nghiệm thu tổng thể sau. Không chặn phát triển vì thiếu dữ liệu thật. Nhánh `feat/ho-so-giao-nhan-20261017` từ mốc bàn giao 6fe0cd7; production vẫn 0.15.1, chưa tag/triển khai mới.

Đã viết hồ sơ bản ký trên Delivery Note, dùng cờ Trung tâm Bán hàng hiện có: tệp riêng gắn đúng phiếu, ghi chú chênh lệch, người/thời điểm đối chiếu có kiểm quyền write và chống phiếu cũ. Thay tệp/ghi chú làm mất dấu đối chiếu; không bắt buộc đính kèm khi giao/nhận, không ghi GL/SLE. Workspace có phiếu đã nhận thiếu bản ký / bản ký chưa đối chiếu. Chặn xóa tệp đang là bản ký. Có 13 ca unit và ca HTTP/Chrome mới trong b014 (mong 21 PASS gồm restore). Cổng 3 nâng baseline lên digest production 0.15.1 đúng mốc VM.

Bổ sung lối vào Tiền và vay cho tiền thực nhận/chưa rõ khách, phân bổ nháp, tuyến đã duyệt, bàn giao nhà máy chờ nhận/chênh lệch; dùng nguyên quyền và chứng từ nguồn. Kịch bản gom nghiệm thu: `docs/nghiem-thu-tong-the.md`. Kiểm cục bộ: 252 ca kh_aph và 107 ca lab9x đạt (Python 3.12, Jinja2).

ĐANG DỞ: chạy UAT/Cổng 2/2b/3 trên SHA mới, xử lý lỗi thực nếu có; kiểm UI hồ sơ. Tiếp theo hoàn thiện tiền/đối soát, nhà máy, tổng hợp tài chính theo thứ tự đã chốt. Nghiệm thu nhân sự và máy in thật chưa làm; không tuyên bố toàn dự án hoàn tất.

## Mốc hiện tại — 17/10/2026 13:22 (Việt Nam): frontend 0.15.1

| Mục | Giá trị |
|---|---|
| Production | Site `frontend`, VM `erpnext-prod`; kh_aph 0.15.1, lab9x 0.2.10, ERPNext 16.51.1/Frappe 16.52.0 |
| Nguồn | Tag `v0.15.1` → `b803c7a95e13c57af3a0f58da6e0c8ea48079db2` |
| Image | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.1` |
| Digest | `sha256:c4b61eb4b2924d50f64bbeaf83623da3e7259f9484b28d6f3e228939912edf47` |
| CI/phát hành | [Run 39005035290](https://github.com/tienduongmarcom/aphvh/actions/runs/39005035290), attempt 1: UAT/Cổng 2/Cổng 2b/Cổng 3 và đẩy image đạt, đúng SHA |
| Diễn tập VM | Lượt `10170555e7bc7c`: tong/dem/chi_tiet khớp, `DIỄN TẬP 0.15.1: ĐẠT`, theo log anh Tiến gửi |
| Triển khai VM | Anh Tiến gửi log digest khớp và `=== XONG 0.15.1: ĐẠT ===` lúc 13:22; Codex không trực tiếp SSH/kiểm Desk production |
| Quay lui khi cần | Theo `quay-lui.sh` và đúng sao lưu ngay trước nâng trong `~/erp/aph-vh/sao-luu/`, kiểm `phien-ban-truoc.txt` = `0.14.3` và checksum; không tự chọn sao lưu cũ |
| Việc còn mở | Kiểm vận hành giao diện/quyền với nhân sự thật; hồ sơ bản ký/ca tiền/nhà máy/tài chính mới. Không tuyên bố toàn dự án hoàn tất |

Các mốc bên dưới được giữ nguyên làm lịch sử; thông tin production/ứng viên cũ không còn là trạng thái hiện tại. Giữ nguyên tag đã phát hành.

## 17/10/2026 11:25 — 0.15.0 chưa phát hành, chuẩn bị 0.15.1

v0.15.0=c236b27 giữ nguyên. Run phát hành38998723309 attempt1/2: UAT/Cổng2/Cổng3 đạt, Cổng2b503 sau nâng B rồi kéo image thiếu; job đẩy image chưa chạy. Ứng viên0.15.1 sửa phép kiểm: xác nhận B HTTP-ready trước thử kéo image lỗi, sau đó vẫn đòi200 ngay sau thao tác; probe có deadline và kiểm body pong, có3 ca HTTP thật. Cổng2b nay tự chạy trên nhánh PR #3. ĐANG DỞ: CI SHA mới phải đủ4 cổng xanh trước tag mới. Chưa có tag0.15.1, chưa merge/phát hành/triển khai; production không đổi.

## 17/10/2026 09:20 — Sửa fixture Warehouse User Permission

SHA 76f6bde: Cổng 2 38987997088 / Cổng 3 38987993537 xanh, UAT 38987993529 lỗi đối chứng dương scope_wh do Company có kho chuyển tiếp mặc định ngoài kho chính. Sửa tài khoản UAT áp Warehouse permission vào đúng 4 DocType Warehouse/SO/DN/đơn chung; không mở thêm kho, không bỏ kiểm quyền. Ba ca nhiều kho/sửa nháp/Company đã đạt, restore đạt; Warehouse và rollback nhóm sau còn chờ. ĐANG DỞ: CI SHA mới, chưa tag/phát hành/triển khai.

## 17/10/2026 — PR #3 mở rộng nghiệm thu nhiều kho/phạm vi quyền

PR #2 a271099 đã xanh đủ UAT/Cổng 2/Cổng 3 (38925577491 / 38925582784 / 38925578136). PR #3 mốc 8705848 đã xanh đủ (38925615925 / 38925623196 / 38925615939), có quay lui và nâng lỗi. Nay bổ sung 5 ca HTTP nhiều kho, native lỗi nhóm sau, sửa nháp, User Permission Company/Warehouse, kiểm scope khi in/thử lại. ĐANG DỞ: chờ CI SHA mới; kết quả mốc cũ không nghiệm thu thay đổi mới. Production vẫn 0.14.3/digest bên dưới; chưa tag/phát hành/triển khai.

## 16/10/2026 22:40 — Sửa vị trí ca kiểm workflow

CI SHA 25974b9 / bd66e95 dừng build: test mới đọc `.github/workflows` nhưng Docker loại `.github` khỏi image. Chuyển nguyên ca kiểm ranh giới sang `deploy/release/test_print_defaults_gate.py`, chạy bắt buộc ngay sau checkout Cổng 3; test bộ cài vẫn chạy trong image. Không skip ca, không nới assertion, không thêm workflow vào image production. ĐANG DỞ: kiểm cục bộ rồi đẩy hai PR, đọc CI SHA mới; frontend không đổi.

## 16/10/2026 22:20 — Ứng viên đang sửa Cổng 3, chưa phát hành

PR #2 3b01cc7 / PR #3 8952265: UAT và Cổng 2 đạt; Cổng 3 (38897717545 / 38897741846) lỗi so schema mẫu in bước 5. Chưa chạy các bước quay lui phía sau. Sửa nhận mẫu Classic trong lab9x 0.2.10 và thu hẹp ngoại lệ schema chỉ 6 chứng từ native, giữ so nghiêm 5 mẫu app. Test mới: bộ cài mới/nâng cấp/mẫu riêng/idempotent và phạm vi ngoại lệ. ĐANG DỞ: chờ CI SHA sau sửa; chưa kết luận đủ cổng. Production vẫn mốc 0.14.3/digest bên dưới; không tag/merge/phát hành/triển khai.

| Mục | Giá trị |
|---|---|
| Production (site `frontend`, VM `erpnext-prod`) | **kh_aph 0.14.3**, lab9x 0.2.9, ERPNext 16.50.0 + Frappe 16.51.0 |
| Image production | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.14.3` — digest `sha256:706bf959addeca5bcb255fee0437ae7aeb355d910d1fc0625ae93fe66367ebc8` |
| Lên production lúc | 16/10/2026 ~16:29 (diễn tập tách biệt ĐẠT 16:23: tong + dem + chi_tiet khớp), 21 cờ bật |
| Nguồn | commit `b14ad8d` (tag `v0.14.3`); CI xanh trên đúng commit (UAT 38840547684, Cổng 3 38840547719) |
| Quay lui về | bản sao lưu trước nâng cấp trong `~/erp/aph-vh/sao-luu/` (thư mục có `phien-ban-truoc.txt` = `0.14.2`, có `sha256.txt`): `./quay-lui.sh <thư mục>` |
| Ứng viên | Nền **0.14.4** `thu/erpnext-v16.51.1` (PR #2); tính năng **0.15.0** `feat/ban-hang-nhanh-20261016` dựa trên nền đó; chưa phát hành/triển khai, chờ CI |
| CI bắt buộc trước khi gắn tag | UAT candidate, Cổng 2, Cổng 3 xanh trên đúng commit |
| Thủ tục | `bash deploy/release/dien_tap_ban_sao.sh <PB>` → `bash deploy/release/trien_khai_frontend.sh <PB>` (≤ 12 giờ sau) |
| Lịch người dùng | Bắt đầu dùng thử 18/10/2026 |

Lịch sử: 0.14.2 (15/10 ~22:44, `0f528c3c…`), 0.14.0 (15/10 ~15:45, `3a259c9b…`), 0.13.0 (`e3136592…`), 0.12.1 (`897f81c2…`), 0.11.4 (`54bf5a99…`), 0.11.3 (`716f1401…`),
0.11.2 (`f2417393…`), 0.11.1 (`9335dfa1…`).
