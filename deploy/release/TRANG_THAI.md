# Trạng thái phát hành APH-VH (một nơi duy nhất — cập nhật mỗi lần phát hành / triển khai)

## 18/10/2026 — Bộ mẫu theo thông tư đang chờ kiểm SHA cuối

Đã đồng bộ mẫu kho, thu/chi, bán hàng, giao nhận, đối soát và phiếu xuất nhanh A5 theo chế độ hiện hành của từng đơn vị; căn cứ và giới hạn được ghi tại `docs/bang-ra-soat-phap-ly-APH-VH.md`, quy chế nội bộ còn là dự thảo. Render cục bộ 19 tình huống giả lập đạt 21 trang; kiểm cục bộ 302 ca ứng dụng + 108 ca lõi đạt. Booklet xem trước: `outputs/bo-mau-phieu-thong-tu-2026.pdf`.

**Chưa phát hành:** thay đổi này chưa có CI trên SHA cuối, chưa in máy thật, chưa tag/merge và chưa triển khai. Production vẫn 0.15.2. Bước kế tiếp là chạy kiểm đúng SHA, nghiệm thu giấy A4/A5 với người dùng rồi mới quyết định phát hành theo runbook.

## 18/10/2026 — Phiếu xuất nhanh A5 theo mẫu chủ dự án, chưa kiểm CI

Anh Tiến cung cấp PDF phiếu đang dùng và yêu cầu chỉnh riêng phiếu xuất nhanh theo mẫu A5. Yêu cầu mới thay cách trình bày A4/không giá của phiếu nhanh: A5 ngang, Times New Roman, thông tin đơn vị/khách/người nhận/kho/địa chỉ, bảng hàng có mã/ĐVT/kg/bao × kg mỗi bao/đơn giá/thành tiền, tổng tiền hàng bằng chữ, chứng từ kèm theo và năm vị trí ký theo mẫu. Giữ hai liên Lưu kho/Giao nhận, thông tin xe/người thực giao/thời điểm/chênh lệch và dấu chờ xuất/bản sao.

Giá bán thuần lấy từ `Delivery Note Item.net_rate/net_amount` (giữ đúng cả giá0), tổng cộng các net_amount, ghi rõ chưa thuế; không cộng lại thuế, không biến phiếu thành hóa đơn hoặc biên bản bàn giao mới. Chỉ fallback rate/amount khi trường net là None. Tiền chữ dùng VND; ngoại tệ ghi tổng và mã tiền, không đọc thành đồng. Không truy vấn/đưa giá vốn vào ngữ cảnh in. Giữ guard/quyền/scope trên server và không ghi sổ khi in. Không thêm schema/cờ/version.

Đã kiểm cục bộ **300 ca kh_aph đạt**, gồm kiểm giá thuần/giá0/không đưa giá vốn vào ngữ cảnh, escape và trạng thái nháp/đã xuất; cú pháp và diff đạt. Bộ sinh Print Format đã chạy, JSON chuẩn không đổi vì đây là template nhanh riêng. PDF Chrome từ chính template với dữ liệu giả: mỗi liên một trang A5 ngang594,96×420pt; đã xem cả hai liên. Phiếu25 dòng tự sang trang, lặp tiêu đề bảng, giữ phần ký nguyên khối. File xem thử tại thư mục `outputs/phieu-xuat-nhanh-a5.pdf` của chat, không đưa dữ liệu khách vào repo. Đã cập nhật ca HTTP kiểm giá từ DN/A5 và bỏ tuyên bố quantity_only cũ theo yêu cầu mới; **chưa chạy ca HTTP/CI của thay đổi này**, không dùng các cổng xanh bdb91a8 để chứng minh mã mới.

**ĐANG DỞ: GN06 và nghiệm thu thực tế chưa đóng.** Bước tiếp: kiểm CI đúng SHA mới, đồng bộ các đường mẫu chuẩn/in lại/tổng hợp theo phạm vi đã chốt; nghiệm thu máy in A5 và nhân viên. Chỉ phiếu nhanh đổi có giá theo yêu cầu này; mẫu kho chuẩn vẫn theo quy tắc riêng cho tới khi có yêu cầu đổi. Production giữ **0.15.2**, chưa push/phát hành/triển khai thay đổi A5.

## 18/10/2026 — GN10/GN11 đã đạt: xuất ngay và mất phản hồi sau commit

Tiếp tục [PR #5](https://github.com/tienduongmarcom/aphvh/pull/5) trên `feat/thong-tin-giao-nhan-20261017` từ `e2369ab`. **Mã nghiệp vụ đã kiểm: `bdb91a826cb506d67870e14d1319cededc4a5008`**. Commit sau mốc này chỉ cập nhật hồ sơ, không phải lượt CI mới. Đã đọc lại AGENTS GitHub, bàn giao, quyết định, kiến trúc và runbook; giữ production 0.15.2.

Đã thêm lựa chọn Xuất ngay trong Dialog, mặc định vẫn nháp. Người có quyền submit mới thấy lựa chọn; cần người thực giao, cách giao và người nhận. API POST tạo+xác nhận trọn đợt trong một transaction qua controller native; lỗi nhóm sau rollback cả DN/SI/GL/SLE. Tách hash nháp/xuất ngay, kiểm cờ ghi nợ lúc xuất, quyền/scope và lượng/nguồn/thông tin/dấu xuất thực tế khi retry. Không nâng nháp cũ thành đã xuất. Vận chuyển tới Đang giao, tự lấy tới Khách đã nhận; không ghi sổ khi mở lại bản in/nhận hàng/retry. Sau thành công tải lại lượng và công nợ trên đơn. Không thêm schema/cờ/quyền hoặc sửa core.

Bằng chứng trên đúng SHA:

- Cục bộ **299 kh_aph +107 lab9x =406 ca đạt**; cú pháp Python/JS, diff đạt.
- [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39086136285) và [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39086133337): đạt site trắng và diễn tập dựng/nâng/quay lui.
- [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39086133438): **227 PASS, 0 FAIL**, b01436 gồm restore. Đã đọc cả 4 ca HTTP xuất ngay và 1 ca Desk. Thiếu submit/Dũng/thiếu người giao bị chặn không để nháp; hai cách giao và retry sau nhận đúng; APH đã xử lý rồi VH thiếu tồn thì cả đợt rollback và Bin không đổi, bổ sung tồn giả rồi retry cùng token thành công hai Company; scope bị chặn cả retry; gọi đồng thời chỉ một DN/một SI.
- Ca `NATIVE_DESK_XUAT_NGAY_LOST_RESPONSE`: Chrome thực dùng Fetch chặn phản hồi200 sau server commit, xác minh DN `MAT-DN-2026-00017` đã submit/Khách đã nhận rồi bấm lại đúng Dialog/token. Counts DN/SI/GL/SLE không tăng. Đã xem ảnh kết quả `xuat-ngay-retry.png` trong artifact.
- [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39086133314): đạt từ baseline production0.15.2 đúng digest. Đọc dấu vân: trước/sau nâng khớp `dem/tong/chi_tiet`; schema/cờ khớp site trắng; trước lỗi/sau tự quay lui khớp `dem/tong/chi_tiet/versions`.

Đặc tả9 nhóm: `docs/dac-ta-xuat-ngay.md`. Kế hoạch truy nguyên: `docs/ke-hoach-van-hanh-tiep-noi.md`.

**ĐANG DỞ: đợt 1 chưa đóng. Bước tiếp GN06:** đồng bộ dữ liệu giao nhận giữa bản in nhanh, mẫu in chuẩn/in lại và phiếu tổng hợp. `phieu_xuat_kho_ban_hang.html`/`bien_ban_giao_nhan.html` còn đọc ô cũ `kh_aph_nguoi_nhan`, `kh_aph_lai_xe`/biển số trong khi phiếu nhanh đã dùng ô đợt/native mới; `delivery_slip.render` còn ô ký trống chung. Cần chọn dữ liệu mới khi có cách giao đợt, fallback phiếu cũ/phiếu trả, escape và kiểm từng đường in/PDF; không gán một người nhận chung cho nhiều DN khác nhau. Sau đó nghiệm thu máy in/người dùng/dữ liệu thật. Chốt ca/tiền/nhà máy và hóa đơn một phần vẫn theo các đợt sau.

Production vẫn **0.15.2**; chưa tăng version/tag/merge/phát hành/triển khai PR #5. Phát hành phải kiểm SHA phiên bản cuối và diễn tập bản sao production hiện tại theo runbook.

## 18/10/2026 — GN09 đã đạt kiểm thử: xử lý chênh lệch giao nhận

Tiếp tục [PR #5](https://github.com/tienduongmarcom/aphvh/pull/5), nhánh `feat/thong-tin-giao-nhan-20261017`, từ mốc tài liệu `602b73e` / mã 1A đã kiểm `5155ca4`. **Mã nghiệp vụ GN09 đã kiểm: `9c45e7492e55797c48483d19004e52aecf6614ca`**. Các commit sau mốc này chỉ cập nhật tài liệu, không phải lượt CI mới. Đã đọc lại AGENTS trên GitHub và các quyết định/kiến trúc/bàn giao/runbook.

Đã có vòng báo chênh lệch → giao người/hạn → chốt kết quả hoặc mở lại có lý do trên DN nguồn. Quyền read/write và scope native vẫn áp dụng; thao tác giao/chốt/mở lại đòi Accounts Manager hoặc Administrator, người phụ trách phải có quyền trên đúng phiếu. Chốt cần bản ký hiện tại đã đối chiếu; không tự đóng vì chỉ có dấu đối chiếu. Căn cứ gồm kết luận không điều chỉnh sổ hoặc phiếu trả/hóa đơn giảm đã submit, đúng nguồn/Company/Customer. Thay tệp/ghi chú tự mở lại, giữ kết quả cũ trong Comment. Khóa đọc hiện hành bảo vệ khi chốt và hủy căn cứ đồng thời. Không tạo DocType Nhiệm vụ hoặc sổ lượng/tiền riêng.

Hủy phiếu nguồn có hồ sơ đòi trưởng và quyền cancel native. Hồ sơ kết thúc trong cùng transaction hủy; không buộc nhận hàng hoặc bản ký giả để thoát vòng. Nếu hóa đơn/liên kết native còn hiệu lực thì hủy bị chặn và dấu hồ sơ rollback. Phiếu đã hủy vẫn xem hồ sơ readonly; phiếu amend không sao chép trạng thái cũ. Không tự tạo/hủy chứng từ tài chính thay người dùng.

Bằng chứng trên đúng SHA:

- Cục bộ **294 kh_aph + 107 lab9x = 401 ca đạt**; cú pháp Python/JS và diff đạt.
- [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39083098771): đạt site trắng.
- [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39083095486): đạt dựng/nâng/quay lui.
- [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39083095506): **222 PASS, 0 FAIL**; b014 có 31 PASS gồm restore. Đã đọc artifact của cả 5 ca HTTP chênh lệch và 1 ca Desk; xem ảnh Dialog thật. Đã kiểm Dũng cộng vai trò, scope người phụ trách, phiên cũ/field giả, mở lại khi đổi bằng chứng, chứng từ nháp/sai nguồn, chốt không ghi sổ, chốt–hủy đồng thời, hủy nguồn không nhận hàng giả và hoàn tồn đúng.
- [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39083095503): đạt từ baseline 0.15.2 đúng digest. Đọc dấu vân: trước/sau nâng khớp `dem/tong/chi_tiet`; schema/cờ sau cài khớp site trắng; trước lỗi/sau tự quay lui khớp `dem/tong/chi_tiet/versions`.

Đặc tả 9 nhóm tại `docs/dac-ta-chenh-lech-giao-nhan.md`; kế hoạch truy nguyên cập nhật tại `docs/ke-hoach-van-hanh-tiep-noi.md`. Những chứng từ xử lý ngoài DN trả/SI giảm, hoặc hóa đơn gộp chưa truy được dòng nguồn phải giữ mở để đối soát, không chọn đại chứng từ hay tạo trả kho giả.

**ĐANG DỞ: đợt 1 chưa đóng. Bước tiếp theo GN10:** thao tác xuất ngay có quyền trong Dialog, một lần gọi tạo+xác nhận nguyên tử, kiểm quyền submit/lượng/tồn/duyệt và retry không ghi sổ hai lần. GN06 còn các đường in/máy in thật; GN11 còn cắt mạng đúng lúc server commit; nhân sự/dữ liệu thật chưa nghiệm thu. Chốt ca/người giữ tiền/nhà máy là đợt sau. Production vẫn **0.15.2**, chưa tăng version/tag/merge/phát hành/triển khai PR #5. Khi phát hành phải kiểm đúng SHA cuối và diễn tập bản sao production hiện tại theo runbook.

## 17/10/2026 — Đợt 1A đã đạt kiểm thử, chưa phát hành

PR [#5](https://github.com/tienduongmarcom/aphvh/pull/5), nhánh `feat/thong-tin-giao-nhan-20261017`, nền `0c1e104` của nhánh bàn giao. Mã nghiệp vụ đã kiểm: **`5155ca48f4a2039d164de419459fcde92a1bfdbb`**. Commit cập nhật hồ sơ sau mốc này chỉ thay tài liệu, không phải SHA đã chạy CI.

Đã thêm cách giao, người nhận, điện thoại, lái xe, biển số và địa chỉ trong Dialog lập phiếu theo đợt. Địa chỉ thay thế phải đúng Customer và quyền đọc; để trống giữ địa chỉ từng SO nguồn. Nội dung mới tham gia hash chống trùng, giữ hash cũ cho API không truyền thông tin giao nhận. Kho ghi riêng người trực tiếp giao; cần quyền submit và xác nhận đúng cách giao. Dấu người/thời điểm xuất do server ghi, giữ nguyên khi nhận hàng và lưu bản ký. Phiếu đã xuất không sửa đè thông tin. Bản in nhanh có hai liên Lưu kho/Giao nhận, không giá và có dấu bản sao khi in lại sau xuất. Dùng cờ Trung tâm Bán hàng hiện có; thêm sáu Custom Field qua bộ cài rõ ràng, không after_migrate, không sửa core/sổ tài chính.

Bằng chứng trên đúng SHA:

- Cục bộ: **278 kh_aph + 107 lab9x = 385 ca đạt**; cú pháp Python/JS và diff đạt. Bộ sinh Print Format chuẩn chạy không đổi JSON (template nhanh render riêng).
- [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39041879339): đạt site trắng.
- [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39041876332): đạt dựng/nâng/quay lui.
- [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39041876201): **216 PASS, 0 FAIL**, b014 có 25 PASS gồm restore. Đã đọc artifact, kiểm sáu trường Dialog và cả hai trang PDF A4. Chuỗi VAT/cọc/giao/thu: 770.000 / 192.500 / 100.000 / 92.500, chưa giao 577.500, nợ cũ không đổi, lãi gộp 75.000.
- [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39041876215): đạt từ đúng baseline production 0.15.2/digest đã xác nhận. Đọc dấu vân: trước/sau nâng khớp `dem/tong/chi_tiet`; schema/cờ sau cài khớp site trắng; trước lỗi/sau tự quay lui khớp `dem/tong/chi_tiet/versions`.

ĐANG DỞ: đợt 1 chưa đóng. Bước tiếp theo là thiết kế/triển khai GN09: người phụ trách, kết quả và liên kết chứng từ xử lý chênh lệch trên phiếu nguồn; không coi đối chiếu bản ký là xử lý xong. GN10 xuất ngay trong Dialog chưa có; GN06 còn các đường in khác và máy in thật; GN11 chưa cắt kết nối trình duyệt tại thời điểm server commit. Fallback địa chỉ SO có unit, chưa có ca HTTP riêng. Chi tiết 9 nhóm tại `docs/dac-ta-giao-nhan-dot-1.md`, thứ tự 5 đợt tại `docs/ke-hoach-van-hanh-tiep-noi.md`. Chốt ca/người giữ tiền/nhà máy vẫn thuộc đợt sau.

Production vẫn **0.15.2**, chưa tăng version/tag/merge/phát hành/triển khai PR #5, chưa nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật. Khi đến bước phát hành phải kiểm đúng SHA phiên bản cuối và diễn tập bản sao production hiện tại theo runbook.

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
