# Bàn giao dự án APH-VH

## 17/10/2026 — Đang kiểm đợt1A: thông tin giao nhận và bản in nhanh

Nhánh mới `feat/thong-tin-giao-nhan-20261017` từ mốc0c1e104 đã giữ kế hoạch5 đợt. Viết thông tin theo đợt trong Dialog lập phiếu: cách giao, người nhận, số liên hệ, lái xe/biển số/địa chỉ; dùng trường native đã kiểm meta16.51.1 và thêm6 ô thật sự thiếu. Kiểm Address theo quyền và Customer; đưa thông tin mới vào hash request, giữ hash cũ nếu không truyền thông tin mới. Kho ghi người giao thực tế (server kiểm submit quyền), xác nhận đúng cách giao. Phiếu đã xuất không sửa đè thông tin; cập nhật hồ sơ ký không tính lại địa chỉ đã lưu. Bản in nhanh có2 liên, escape dữ liệu và dấu bản sao sau xuất. Không thay sổ/tài chính/quyền cơ bản hoặc trạng thái giao hàng.

Cục bộ278 kh_aph +107 lab9x=385 ca đạt; cú phápPython/JS và diff kiểm được. Bộ sinh Print Format chạy không đổiJSON chuẩn (template nhanh render riêng). HTTP b014 thêm ca thông tin giao nhận và kiểm chuỗi VAT cũ trên phiếu mới; mong25 PASS gồm restore, tổng artifact dự kiến216. Cổng3 đổi baseline từ0.15.1 sang đúng0.15.2/digest production đã xác nhận. Các kết quả CI cũ không xác nhận mã mới.

ĐANG DỞ: chờ CI trên đúngSHA, sửa nguyên nhân nếu lỗi; đọc artifact/ảnhDialog và bằng chứng nâng cấp. Chi tiết9 nhóm tại `docs/dac-ta-giao-nhan-dot-1.md`. Chưa hoàn tất GN09 xử lý chênh lệch hoặc GN10 xuất ngay trongDialog; chốt ca/người giữ tiền/nhà máy vẫn ở kế hoạch tiếp theo. Production giữ0.15.2, chưa tăngversion/tag/merge/phát hành/triển khai.

## 17/10/2026 — Khôi phục mạch kế hoạch vận hành, đọc lại quy tắc GitHub

Theo yêu cầu anh Tiến, đã đọc lại AGENTS.md trên origin/feat/ho-so-giao-nhan-20261017 và đối chiếu bàn giao, quyết định nghiệp vụ, kiến trúc, quy trình khách/release. Local khớp remote d622abc trước lượt này. Production giữ 0.15.2; các phiên bản cũ trong thân AGENTS/runbook là mô tả lịch sử, không dùng thay mốc TRANG_THAI/manifest/log đã xác nhận.

Đã ghi `docs/ke-hoach-van-hanh-tiep-noi.md`: thứ tự 5 đợt, bảngGN01–GN12 với code/ca hiện có và phần thiếu, thiết kế thông tin giao nhận/chênh lệch, điểm nốiT01–T07 và phạm viNM/TC/HD. Đây là hồ sơ tiếp nối chính thức theo các tệp yêu cầu người dùng cung cấp lại; không phải tuyên bố đã hoàn thành tính năng. Không sửa mã/core/quyền/dữ liệu, chưa chạy lại test cho thayđổi tài liệu.

ĐANG DỞ: đợt 1 còn thông tin giao nhận, bản in 2 liên và vòng xử lý chênh lệch. Bước tiếp: xác minh meta native16.51.1 trước chọnfield, triển khaiGN03–GN04 + token GN01, kiểm hồi quy và server quyền, sau đó GN06/GN09. Đợt 2 chốt ca/người giữ chưa viết; nhà máy/chốt ngày chưa có màn thống nhất; hóa đơnmột phần vẫn cần chốt riêng. Không tag/merge/phát hành/triển khai trong lượt này.

## 17/10/2026 — Production 0.15.2 đã triển khai theo log anh Tiến

Anh Tiến chạy trên `erpnext-prod`, site `frontend`, trong `~/trien-khai` ở tag `v0.15.2`. Diễn tập bản sao tách biệt lượt `10171255a25ef6` báo `tong`, `dem`, `chi_tiet` khớp và ghi dấu `/home/tienduongmarcom/dien-tap-0.15.2.ok`. Sau đó bộ triển khai báo **`=== XONG 0.15.2: ĐẠT ===`**. Image VM `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.2` có digest **`sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333`**, khớp workflow phát hành39030251134. Nguồn `24b795cc28f47ca2f31aef8edbbd8e5984c12ee3`; nền ERPNext16.51.1/Frappe16.52.0, lab9x0.2.10, giữ21 cờ.

Đã cập nhật manifest khách về0.15.2. Bằng chứng là log người vận hành gửi trong chat; Codex không có SSH và chưa kiểm độc lập giao diện production. Không chạy lại nâng cấp hoặc dùng backup cũ để phục hồi sau khi mở nhập liệu. Nếu phát sinh lỗi sau mở nhập liệu, cần đối soát giao dịch mới trước khi chọn cách khắc phục.

Bước tiếp: tải lại Desk, kiểm mở danh mục/phiếu hiện có; tiếp tục nhập hàng hóa, tồn kho/số dư, người dùng và cấu hình thực tế. Gom nghiệm thu toàn chuỗi theo `docs/nghiem-thu-tong-the.md` khi dữ liệu sẵn sàng. Chưa ký nghiệm thu nghiệp vụ thật hoặc toàn bộ202 quyết định. Các mục “chưa triển khai” phía dưới là lịch sử trước mốc này. Bản trước0.15.1/digest `sha256:c4b61eb4b2924d50f64bbeaf83623da3e7259f9484b28d6f3e228939912edf47` chỉ là mốc quay lui có điều kiện, không tự restore làm mất dữ liệu mới.

## 17/10/2026 — Image 0.15.2 đã phát hành, chưa triển khai VM

[Workflow phát hành39030251134](https://github.com/tienduongmarcom/aphvh/actions/runs/39030251134) hoàn tất thành công, đủ mọi job UAT/Cổng2/2b/3/phát hành, trên tag `v0.15.2` = `24b795cc28f47ca2f31aef8edbbd8e5984c12ee3`. Log build/push xác nhận image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.2` có manifest digest `sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333` (kết thúc12:19 UTC). Không đổi tag đã phát hành.

Bước tiếp: người vận hành SSH vào `erpnext-prod`, checkout đúng tag trong `~/trien-khai`, chạy `dien_tap_ban_sao.sh 0.15.2` trên dữ liệu hiện tại. Chỉ sau diễn tập ĐẠT mới chạy `trien_khai_frontend.sh 0.15.2`; không thêm cờ. Chưa có log VM mới nên production vẫn0.15.1, manifest khách giữ nguyên. Codex không có phiên SSH; không coi phát hành image là đã triển khai/ nghiệm thu dữ liệu thật.

## 17/10/2026 — Ứng viên 0.15.2 sẵn sàng gắn tag

Mã đóng gói **`24b795cc28f47ca2f31aef8edbbd8e5984c12ee3`** đủ bốn cổng xanh: [UAT39028411357](https://github.com/tienduongmarcom/aphvh/actions/runs/39028411357), [Cổng239028414365](https://github.com/tienduongmarcom/aphvh/actions/runs/39028414365), [Cổng2b39028411350](https://github.com/tienduongmarcom/aphvh/actions/runs/39028411350), [Cổng339028411353](https://github.com/tienduongmarcom/aphvh/actions/runs/39028411353). Đã đọc artifact: UAT215 PASS/0 FAIL; Cổng3 số lượng/tổng/chi tiết khớp trước-sau nâng cấp và sau ca lỗi tự quay lui; schema khớp site mới. Unit268+107=375 đạt. PR #4 chuyển sang sẵn sàng duyệt, chưa merge.

**Bước tiếp theo:** chủ dự án gắn tag `v0.15.2` vào đúng SHA trên theo AGENTS.md; workflow phát hành chạy lại các cổng trước khi đẩy image. Chưa có image/digest 0.15.2 được phát hành, chưa chạy VM. Khi image đạt, theo `docs/phat-hanh-0.15.2.md`: diễn tập trên bản sao dữ liệu thật hiện tại rồi triển khai (21 cờ hiện có, không thêm cờ). Production vẫn0.15.1. Codex không có phiên SSH. Commit sau SHA trên chỉ chốt tài liệu/bằng chứng, không đổi mã đã kiểm; chọn SHA trên khi gắn tag để có đúng mốc đủ cổng.

## 17/10/2026 — Chuẩn bị ứng viên phát hành 0.15.2

Theo yêu cầu tiếp tục của anh Tiến: nâng nhãn app lên 0.15.2 cho phạm vi PR #4, giữ nền và 21 cờ. Sửa `khach/aph-vh/phien-ban.yaml` từ thông tin cũ 0.14.3 về production 0.15.1 theo log đã xác nhận; không ghi ứng viên thành bản đã triển khai. Hướng dẫn cụ thể ở `docs/phat-hanh-0.15.2.md` gồm phạm vi, migrate/bộ cài, diễn tập bắt buộc khi đã có dữ liệu, triển khai và quay lui. Chưa tag/merge/đẩy image/đổi production.

ĐANG DỞ: chờ bốn cổng trên SHA đóng gói 0.15.2. Sau khi xanh, chốt SHA cho chủ dự án gắn tag theo AGENTS.md. Sau workflow phát hành đạt mới chạy diễn tập trên VM rồi triển khai; Codex hiện không có phiên SSH. Nghiệm thu thực tế vẫn gom sau khi dữ liệu sẵn sàng.

## 17/10/2026 — Chốt kiểm luồng tiền, nhà máy, phạm vi tài chính và chuỗi VAT

Mã đã kiểm: `96ce98d6784fc9fd26818306bbe0a1fc54c5fd4a`, PR [#4](https://github.com/tienduongmarcom/aphvh/pull/4). Đủ bốn cổng trên cùng SHA: [UAT 39018390715](https://github.com/tienduongmarcom/aphvh/actions/runs/39018390715), [Cổng 2 39018394462](https://github.com/tienduongmarcom/aphvh/actions/runs/39018394462), [Cổng 2b 39018390706](https://github.com/tienduongmarcom/aphvh/actions/runs/39018390706), [Cổng 3 39018390742](https://github.com/tienduongmarcom/aphvh/actions/runs/39018390742) đều đạt. Cục bộ: 268 kh_aph + 107 lab9x = 375 ca đạt.

Đã đọc artifact UAT: 215 PASS, 0 FAIL; funds 20, b0111 15, b0114 8, b014 24 gồm phục hồi. Ca xuyên suốt cùng đơn xác nhận tổng có VAT 770.000 → cọc 100.000 → giao 5/20 kg/hóa đơn 192.500 → cấn cọc → nhận hàng/lưu bản ký/đối chiếu không ghi sổ lần hai → thu nốt 92.500; nợ đã giao 0, phần chưa giao 577.500, nợ cũ giữ nguyên, lãi gộp 75.000. Các ca chặn trùng mã PE/JE/phiếu thực thu và nhập đồng thời, quyền File/Bank, giới hạn Company, sửa tay kết quả quỹ nhà máy, hồ sơ không xem giá vốn cộng vai trò kế toán đều đạt trong bộ hồi quy.

Artifact Cổng 3: số lượng, tổng và chi tiết sổ trước/sau nâng cấp khớp; cấu trúc site nâng cấp khớp site cài mới; cố ý làm lỗi nâng cấp đã tự quay lui, giữ bảo trì và khôi phục số lượng/tổng/chi tiết. Lượt UAT trước `39017622574` dừng do helper đòi trường message khi xóa nháp (API trả rỗng); đã sửa đúng hai lối xóa nháp, giữ nguyên assertion nghiệp vụ và chạy lại toàn bộ.

Mốc này hoàn tất vòng phát triển/kiểm giả lập nêu dưới, không xác nhận toàn bộ 202 quyết định hoặc nghiệm thu người dùng thật. Bước tiếp theo: gom nghiệm thu thực tế theo `docs/nghiem-thu-tong-the.md` khi có danh mục hàng, tồn kho/số dư và nhân sự/máy in; xử lý chênh lệch thực tế nếu có. Production vẫn **0.15.1** theo digest đã ghi, chưa tag/merge/phát hành/triển khai. Commit bàn giao sau SHA trên chỉ cập nhật hai tài liệu trạng thái, không đổi mã đã kiểm.

## 17/10/2026 — Thêm chuỗi xuyên suốt và sửa ba số thanh toán có VAT

Trong cùng PR #4: thêm ca trên một đơn chung có VAT10%: tổng770000 → cọc100000 → giao5/20kg, hóa đơn192500 → cấn cọc, còn92500 → nhận hàng/bản ký (không ghi sổ lần hai) → thu nốt, nợ phần đã giao0, phần chưa giao577500. Kiểm nợ cũ không tự bị cấn và lãi gộp của phần đã giao75000 (doanh thu chưa thuế175000 − giá vốn100000).

Sửa `funds.shared_financials`: trước dùng net_total đơn chung chưa thuế với grand_total hóa đơn có thuế; nay tổng phải thanh toán lấy grand_total của SO nguồn chuẩn. Nguồn Closed không cộng lại phần chưa giao đã chuyển/hủy: chỉ giữ hóa đơn đã ghi của nguồn đóng. Hóa đơn trộn nguồn mở/đóng phải đối soát, không tự đoán phân bổ. Không sửa sổ hoặc giá trên chứng từ. Thêm chặn hồ sơ Dũng cộng Accounts Manager ở ba thao tác giá thành. Kiểm cục bộ268 kh_aph +107 lab9x=375 ca đạt. B014 nay mong24 PASS gồm restore, toàn artifact dự kiến215 kết quả PASS.

ĐANG DỞ: CI phải xanh trên SHA mới; các mốc cũ bên dưới là lịch sử. Chưa phát hành/triển khai, production0.15.1. Nghiệm thu dữ liệu/người dùng/máy in thật vẫn gom sau khi khách sẵn sàng danh mục/tồn kho.

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

## 17/10/2026 13:22 (Việt Nam) — Production 0.15.1 đã triển khai theo log anh Tiến

Anh Tiến trực tiếp chạy thủ tục trên VM `erpnext-prod`, site `frontend`; Codex không có phiên SSH. Diễn tập lượt `10170555e7bc7c` báo tong/dem/chi_tiet khớp, dấu `~/dien-tap-0.15.1.ok`, sau đó triển khai báo `=== XONG 0.15.1: ĐẠT ===`. Đây là bằng chứng log người vận hành gửi, chưa phải Codex kiểm độc lập giao diện production.

Nguồn bất biến: tag `v0.15.1`, commit `b803c7a95e13c57af3a0f58da6e0c8ea48079db2`; image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.1`, digest `sha256:c4b61eb4b2924d50f64bbeaf83623da3e7259f9484b28d6f3e228939912edf47` khớp log VM. Nền ERPNext 16.51.1/Frappe 16.52.0, kh_aph 0.15.1/lab9x 0.2.10. Phát hành [39005035290](https://github.com/tienduongmarcom/aphvh/actions/runs/39005035290) đạt UAT/Cổng 2/Cổng 2b/Cổng 3 và job đẩy image trên đúng SHA. Không di chuyển tag 0.15.0/0.15.1.

Bản này gồm nâng nền, lập phiếu xuất nháp/in nhanh và sửa dịch đã ghi bên dưới; không đồng nghĩa hoàn thành toàn bộ dự án. Tiếp theo: nhân sự mở lại Desk, kiểm phiên bản/hiển thị và sử dụng theo quyền; không tạo chứng từ giả trên production. Click primary/in giấy thực tế với nhân sự thật chưa được nghiệm thu bởi Codex. Hồ sơ bản ký, ca tiền, nhà máy/tài chính mới vẫn còn mở. Quay lui chỉ theo thủ tục và bản sao lưu ngay trước nâng 0.15.1 (phiên bản trước 0.14.3), không dùng thư mục sao lưu cũ tùy ý. Các mục ĐANG DỞ/phát hành chưa xong bên dưới là lịch sử.

## 17/10/2026 11:25 — Ứng viên 0.15.1, sửa ranh giới readiness của Cổng 2b

Tag v0.15.0 do anh Tiến đẩy = c236b27; KHÔNG di chuyển hoặc ghi đè. Phát hành run 38998723309: attempt 1 và 2 UAT/Cổng 2/Cổng 3 đạt, Cổng 2b lỗi HTTP503 bước 3 nên job đẩy image bị skip. Logs: mã thoát kéo image không tồn tại=2 và CUSTOM_TAG=ci-b đã đúng, backend/frontend vẫn health starting ~50 giây sau nâng. Rerun một lần tái hiện; không tiếp tục rerun cùng tag.

Sửa Cổng 2b: sau nâng B phải đợi HTTP200 đúng JSON message=pong (hạn chót 180 giây) TRƯỚC khi thử kéo image không tồn tại. Sau thử lỗi vẫn kiểm HTTP ngay, không retry để che downtime do chính hành động thử. Probe có 3 test HTTP localhost thật:503→200,503 vĩnh viễn và200 sai body. Thêm trigger Cổng 2b khi push nhánh tính năng để đóng cổng này trước khi nhờ anh gắn tag. Không thay bộ kiểm nghiệp vụ, không sửa core. App ứng viên 0.15.1; chưa có tag mới và không tự phát hành.

ĐANG DỞ: đẩy sửa vào PR #3 và chạy đủ UAT/Cổng2/Cổng2b/Cổng3 trên SHA mới; nếu readiness vẫn503 phải đọc log thêm, không kết luận đã sửa. Production frontend vẫn0.14.3 theo mốc bàn giao, phiên này không chạm VM.

## 17/10/2026 09:20 — UAT phạm vi kho: chỉnh cấu hình tài khoản thử

SHA 76f6bde: Cổng 2 38987997088 và Cổng 3 38987993537 đạt; UAT 38987993529 lỗi tại đối chứng dương của scope_wh. Native Frappe chặn đọc Company do Warehouse User Permission áp mọi DocType, gồm trường Company.default_in_transit_warehouse. Ba ca mới trước đó đạt: 3 kho/2 pháp nhân không ghi sổ, sửa nháp cập nhật lượng, Company scope; restore đạt. Ca lỗi nhóm sau chưa chạy, không tuyên bố đủ 19 ca.

Sửa fixture để Warehouse User Permission áp đúng Warehouse/Sales Order/Delivery Note/APH Shared Sales Order, không áp lên cấu hình Company có kho chuyển tiếp chung. Không thêm kho được phép, không bypass quyền server và không nới assertion đối chứng dương/âm. Company scope giữ apply_all. ĐANG DỞ: chạy lại CI SHA mới; production không đổi.

## 17/10/2026 — Hoàn thiện kiểm nhiều kho và quyền bán hàng nhanh

Mốc CI đã xác minh 16/10 23:40: PR #2 a271099 đủ ba cổng xanh (UAT 38925577491, Cổng 2 38925582784, Cổng 3 38925578136); PR #3 8705848 cũng đủ (38925615925 / 38925623196 / 38925615939), cả bước quay lui và cố ý nâng lỗi đều chạy đạt. Production chưa đổi. Các mục ĐANG DỞ cũ bên dưới là lịch sử.

Theo yêu cầu anh Tiến 17/10, mở rộng PR #3: b014 thêm 5 ca (3 kho/2 pháp nhân; sửa DN nháp; User Permission Company và Warehouse có đối chứng dương; lỗi native ở nhóm sau rollback cả đợt). Kiểm lại quyền liên kết trên phiếu khi in/thử lại và chặn dùng lại đợt có phiếu hủy. Mong 19 PASS b014 gồm restore; bổ sung User Permission vào snapshot. Tài khoản/dữ liệu giả, giữ framework native, không sửa core.

ĐANG DỞ: chạy CI trên SHA mới; chưa dùng kết quả mốc 8705848 để kết luận thay đổi này đạt. Sau CI rà ảnh Dialog và chốt phạm vi phát hành; hồ sơ chữ ký số hóa/ca tiền/nhà máy/tài chính mới còn là việc tiếp theo, không tuyên bố cả dự án xong. Không tag, phát hành image hay chạm frontend.

## 16/10/2026 22:40 — Sửa vị trí ca kiểm workflow

CI SHA 25974b9 / bd66e95 dừng build: test mới đọc `.github/workflows` nhưng Docker loại `.github` khỏi image. Chuyển nguyên ca kiểm ranh giới sang `deploy/release/test_print_defaults_gate.py`, chạy bắt buộc ngay sau checkout Cổng 3; test bộ cài vẫn chạy trong image. Không skip ca, không nới assertion, không thêm workflow vào image production. ĐANG DỞ: kiểm cục bộ rồi đẩy hai PR, đọc CI SHA mới; frontend không đổi.

## 16/10/2026 22:20 — Sửa lỗi Cổng 3 mẫu in Classic trên ERPNext 16.51.1

PR #2 tại 3b01cc7 và PR #3 tại 8952265: UAT/Cổng 2 đạt, Cổng 3 lỗi bước 5 (runs 38897717545 / 38897741846). So sổ khớp trong CI; bước quay lui phía sau chưa chạy. Không lấy run SHA cũ làm nghiệm thu SHA mới.

Nguyên nhân: bộ cài chưa nhận mẫu native `<DocType> Classic`; site mới giữ Classic thay vì mẫu tiếng Việt của app. Sửa lab9x 0.2.10 nhận đúng tên Classic của chính DocType, giữ mẫu khách chọn khác và idempotent. Cổng 3 chỉ cho phép khác biệt tên native của 6 DocType không có mẫu app; bỏ regex rộng cũ, bắt buộc tên mẫu khớp DocType. 5 DocType app quản lý vẫn so nghiêm ngặt, không bỏ qua. Kiểm cục bộ: kh_aph 237 ca + lab9x 107 ca đạt (có Jinja2). Thêm test chạy hàm bộ cài trên trạng thái cài mới/nâng cấp/mẫu khách + test ranh giới ngoại lệ schema.

ĐANG DỞ: đưa sửa vào cả hai nhánh và chờ CI mới. Chưa tag, phát hành, diễn tập VM hay thay frontend. Bước tiếp: đọc Cổng 3 đúng SHA, xử lý lỗi thực nếu còn; sau đó mở rộng ca nhiều kho/scope trước phát hành bán hàng nhanh. Thời gian ghi mục này là thời gian làm việc, không phải thời gian triển khai.

## 16/10/2026 — Ứng viên 0.15.0, bước bán hàng/lập phiếu xuất nhanh

Nhánh `feat/ban-hang-nhanh-20261016` dựa trên nhánh nâng nền `thu/erpnext-v16.51.1` (PR #2). Không phát hành/triển khai. Cờ hiện có `kh_aph_trung_tam_ban` (mặc định tắt); schema mới chỉ qua bộ cài rõ ràng, không after_migrate.

Đã viết: Dialog “Lập phiếu xuất & In” trên đơn chung đã xác nhận; facade `ban_nhanh.preview/create_drafts/print_batch`; phiếu nháp theo đơn nguồn × kho, chống lặp theo mã yêu cầu/nội dung, trừ lượng đã lập nháp khi chọn giao đợt tiếp; giữ bao nguyên theo snapshot. Không submit/commit/ghi sổ trong facade. Mẫu in số lượng có ô ký thực giao/thực nhận và nhãn CHỜ XUẤT. Bổ sung quyền lập nháp Delivery Note cho Kế toán bán hàng, không thêm quyền submit/hủy/xóa. Sửa 7 bản dịch sai nghĩa rõ từ audit 15/10; không áp bừa 137 đề xuất phụ thuộc ngữ cảnh.

Kiểm cục bộ: lab9x 107 ca; kh_aph 235 ca khi có Jinja2. HTTP/Chrome mới nằm trong `deploy/uat/http/b014_ban_nhanh_cases.py` + `ban-nhanh-desk.mjs`; chạy chung b014, mong 14 PASS gồm restore. Chưa kết luận HTTP/Chrome PASS trước Actions đúng SHA. Chi tiết `docs/ban-hang-nhanh-tiep-quan.md`.

Nền 3112ff0: UAT 38893496163 và Cổng 2 38893496202 đạt; core 63.508 tệp khớp, phiên bản thực ERPNext 16.51.1 + Frappe 16.52.0. Cổng 3 38893460847 FAIL vì kiểm kho mặc định đọc ô không tồn tại; đã sửa nhận biết meta, thêm 2 ca tái hiện và nhập thay đổi từ nhánh nền b409d34. Giữ run FAIL làm bằng chứng. ĐANG DỞ: đợi CI SHA mới và xử lý lỗi thực. Chưa làm hồ sơ bản ký/đối chiếu, ca tiền mặt/custodian, phần nhà máy/tài chính mới, phần lớn bản dịch còn lại. Thứ tự người dùng chốt: bán hàng → xuất kho/ký nhận → tiền mặt/chuyển khoản/công nợ → nhà máy → tổng hợp tài chính. Tiếp theo mở rộng ký nhận và cảnh báo phiếu thiếu hồ sơ; không coi bản in có ô ký là đã có chữ ký.

## 16/10/2026 — Codex tiếp nhận, ứng viên nâng nền 0.14.4

Anh Tiến đã cho phép phát triển tiếp: bán hàng → xuất kho/ký nhận → tiền mặt/chuyển khoản/công nợ → nhà máy → tổng hợp tài chính; cải thiện UI, bản dịch, tự tạo dữ liệu giả lập. Chỉ dẫn này thay quyết định tạm dừng tính năng ở bản bàn giao cũ bên dưới. Không chạm production.

Ứng viên nền tách riêng tại `thu/erpnext-v16.51.1`: ghim image ERPNext 16.51.1, app 0.14.4, Ubuntu CI 24.04; thêm gate so checksum toàn bộ tệp core image nền/ứng viên. Giữ mốc production 0.14.3 và digest quay lui. Cổng 3 vẫn diễn tập nâng từ đúng production 0.14.3.

ĐANG DỞ: chờ CI trên SHA ứng viên. Chưa phát hành, chưa triển khai; chưa xác nhận phiên bản Frappe thực trong image (CI in bench version). Sau nền: làm nút lập phiếu xuất nháp/in từ đơn chung, rồi hồ sơ ký nhận và thanh toán. Xem `docs/nang-nen-16.51.1.md`.

## 000000000000000. BÀN GIAO 16/10/2026 17:50 — Claude → Codex (kiểm chéo, phát triển tiếp)

Trạng thái: production `frontend` chạy **0.14.3** (digest `706bf959…`, commit `b14ad8d`), CI xanh trên đúng commit; HEAD nhánh
`fix/p0-uat-v091-20261010` = commit ghi nhận triển khai (chỉ tài liệu + mốc Cổng 3). Không có việc dở dang trong code.
Người dùng bắt đầu dùng thử **18/10/2026**; chủ dự án đã chốt **tạm dừng tính năng mới**, chỉ vá lỗi phát sinh.

Việc mở (theo thứ tự ưu tiên):
1. **ubuntu-latest chuyển sang Ubuntu 26 từ 19/10/2026** (thông báo trên mọi run): CI có thể đổi hành vi (docker, python, bash).
   Nên ghim `runs-on: ubuntu-24.04` trong mọi workflow trước 19/10, rồi mới thử nâng có kiểm soát.
2. Cảnh báo Node.js 20 của actions (checkout@v4, upload-artifact@v4, docker/*): nâng phiên bản action khi rảnh, không gấp.
3. ERPNext **16.51.1** (sửa Stock Closing Entry + Stock Balance; app chưa dùng Stock Closing Entry): CHƯA nâng. Gộp vào bản vá
   sau đợt dùng thử; nhảy 16.50.0 → 16.51.1 kéo theo cả 16.51.0 — đổi digest nền ở Dockerfile + Cổng 2/3, chạy đủ CI, diễn tập.
4. Lỗi người dùng báo từ 18/10: mỗi lỗi → ca kiểm (UAT HTTP / unit) tái hiện TRƯỚC khi sửa; bản vá theo thủ tục
   `dien_tap_ban_sao.sh` → `trien_khai_frontend.sh` (xem TRANG_THAI.md).
5. Pháp lý: dòng 12–23 `docs/bang-ra-soat-phap-ly-APH-VH.md` chờ chị Dung (kế toán trưởng) xác nhận.
6. Đề xuất chưa làm: kịch bản nghiệm thu theo vai trò (bán hàng → kho → Dũng → kế toán trưởng: đơn → cọc → giao từng phần →
   đổi nguồn → trả hàng → thu tiền → đối chiếu) chạy trên production bằng người dùng thật.

Cách kiểm chéo nhanh: đọc `AGENTS.md` mục "Nhận bàn giao / kiểm độc lập"; chạy Cổng 1; đọc run CI trên SHA `b14ad8d`
(UAT 38840547684, Cổng 2 38840552352, Cổng 3 38840547719) và 4 run FAIL trước đó (bằng chứng các lỗi đã sửa ở 0.14.3).

## 00000000000000. Bản 0.14.3 — 16/10/2026 (ĐÃ TRIỂN KHAI LÊN FRONTEND ~16:29, ĐẠT, digest `706bf959…`; diễn tập tách biệt ĐẠT 16:23, tong + dem + chi_tiet khớp) — an toàn nâng cấp khi production có dữ liệu

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
- Bảng trạng thái phát hành một nơi: `deploy/release/TRANG_THAI.md`; AGENTS.md có mục "Nhận bàn giao / kiểm độc lập".
- CI: 4 lần FAIL giữ làm bằng chứng (bắt được: mã container đổi sau nâng cấp, quyền 600 làm quay lui hỏng); xanh trên b14ad8d.
- Bước tiếp theo: người dùng thử từ 18/10, gom lỗi; không thêm tính năng mới.

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
- CI xanh trên `dc6aa1b`: UAT candidate `38567486172` (đủ các bộ, gồm b0113 14 PASS), Cổng 3 `38567486151` (nâng cấp từ 0.11.2), Cổng 2 `38567493935`.
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

Bổ sung dấu thời điểm/người xác nhận xuất tại kho do server ghi; giữ nguyên khi khách nhận và lưu bản ký. Cục bộ278+107=385 ca đạt, CI mới chưa kết luận.
