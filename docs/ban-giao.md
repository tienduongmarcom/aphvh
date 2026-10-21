# Bàn giao — trạng thái mới nhất

## 21/10/2026 — ĐANG KIỂM ứng viên0.16.4: nhận diện khách từ địa chỉ/liên hệ nhập riêng

Production vẫn0.16.3/digesta252478b… đã ĐẠT. Lỗi người dùng báo và kiểm chỉ đọc trên Customer/Address: Address đã liên kết Customer nhưng ô tóm tắt primary_address còn trống, đầu đơn0.16.3 đọc ô này nên báo thiếu. Không lưu mã/tên/địa chỉ thật vào ca thử, không sửa dữ liệu production.

Sửa customer_identity/customer_query/tim_khach dùng chung bộ đọc Address/Contact liên kết đúng Customer, theo get_list/quyền native; loại Address ngừng dùng, ưu tiên Link chính hợp lệ rồi hồ sơ được đánh dấu chính/thứ tự tạo. Đọc thông tin hiện tại mỗi lần tải, kể cả khi cache Customer còn giá trị cũ. SĐT ưu tiên Contact mobile/phone, rồi số trong bảng Contact Phone nếu chưa đánh dấu số chính; khi không có Contact dùng SĐT trực tiếp Customer, rồi Address. Thêm/sửa/xóa số Contact không làm sống lại cache cũ. Giữ dữ liệu Customer-only cũ nếu chưa có hồ sơ/Link thay thế; từ chối quyền có thông báo riêng. Không tự điền cache Customer, đổi địa chỉ giao hoặc snapshot chứng từ cũ. Không đổi schema, quyền,28cờ hoặc logic ghi sổ.

Cục bộ466ca (14skip) đạt. Đã mở rộng HTTP trên dữ liệu giả: import địa chỉ không chọn chính, loại địa chỉ ngừng dùng/khách khác, thêm–sửa–xóa–thêm SĐT, đối chiếu ba API và Customer không bị ghi lại. Chrome mở đơn chưa lưu, đổi sang khách rỗng rồi chọn lại, kiểm đúng địa chỉ/SĐT và ảnh khach-dia-chi-lien-ket.png; kiểm không tạo thêm đơn. Còn chờ bốn cổng trên đúng mã và xem ảnh thực tế CI, chưa tuyên bố PASS/tạo tag/phát hành.

Housekeeping trước đó đã xong: [PR #29](https://github.com/tienduongmarcom/aphvh/pull/29) gộp6bd06a0; [Cổng3 39529511187](https://github.com/tienduongmarcom/aphvh/actions/runs/39529511187) success mãeb22911, artifact cong-3-bang-chung đã đọc: diễn tập/nâng/quay lui/so chi tiết KHỚP; UAT39529591303 vàCổng239529591299 success commit15c6c08 chỉ sửa tài liệu saueb22911. Cổng3 nay lấy production0.16.3 đúngdigest. Không phát hành/tag cho housekeeping.

## 21/10/2026 — Production0.16.3 đã được người vận hành xác nhận ĐẠT

Anh Tiến gửi log tại `tienduongmarcom@erpnext-prod:~/trien-khai`: image **ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.3**, digest **sha256:a252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95**, dòng cuối **=== XONG 0.16.3: ĐẠT ===**. Digest khớp image phát hành39518896902 và registry đã kiểm; nguồn tag **v0.16.3 = a1f95b062f2ff7334ed36c176dfb742bf828974a** (PR #26 đã gộp main). Trước đó diễn tập thực **10210126238079**, dấu `/home/tienduongmarcom/dien-tap-0.16.3.ok`, tổng/đếm/chi tiết khớp, ĐẠT. Mốc khách đã cập nhật `khach/aph-vh/phien-ban.yaml`. Không cờ mới; bộ28cờ giữ nguyên theo thủ tục nâng. Đây là bằng chứng người vận hành gửi, không phải agent tự SSH kiểm lại VM.

ĐÃ TRIỂN KHAI bản làm gọn năm khu/nhận diện khách–hàng/thu tiền–in/chuẩn tên chung. Nghiệm thu với nhân sự đại diện, hàng/tồn và máy in thật vẫn để cuối theo yêu cầu, không coi log nâng cấp thành nghiệm thu toàn nghiệp vụ. Mẫu3liên vẫn nháp; công nợ ròng chốt qua báo cáo chuẩn. Vận hành trong tmux và nối lại đúng phiên khi SSH ngắt, không chạy lặp lượt đang chạy.

Quay lui có điều kiện về image0.16.2/digest34a32f71… với snapshot tương ứng lúc nâng0.16.3; không restore snapshot cũ sau giao dịch mới khi chưa xử lý phần phát sinh. ĐANG KIỂM housekeeping: chuyển mốc Cổng3 sang0.16.3/digest trên để lần sau diễn tập đúng production, chạy CI riêng, không sửa mã app hay triển khai lại. Bước tiếp ghi kết quả Cổng3 vào đây và gộp PR hồ sơ; không phát hành/tag mới cho việc ghi nhận này.

## 21/10/2026 — Image0.16.3 đã phát hành, CHƯA xác nhận triển khai production

Chủ dự án đã push tag **v0.16.3**, đã kiểm GitHub trỏ đúng merge commit **a1f95b062f2ff7334ed36c176dfb742bf828974a**. [Phát hành39518896902](https://github.com/tienduongmarcom/aphvh/actions/runs/39518896902) **success**: UAT, Cổng2,2b,3 và bước build/push đều success cùng nguồn tag. Image **ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.3**, digest **sha256:a252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95**; đã đối chiếu log pushing manifest/containerimage.digest với đọc registry bằng docker buildx imagetools inspect, khớp. Không tag lại hoặc ghi đè image.

Production vẫn theo xác nhận0.16.2/digest34a32f71…/28cờ; chưa nhận log diễn tập hoặc `XONG0.16.3:ĐẠT` trên erpnext-prod/frontend. Không đổi `khach/aph-vh/phien-ban.yaml` trước bằng chứng triển khai. Bước tiếp ở SSH máy chủ: đúng checkoutv0.16.3 → `bash deploy/release/dien_tap_ban_sao.sh 0.16.3`; chỉ sau ĐẠT/so sổ khớp/dấu hợp lệ mới `bash deploy/release/trien_khai_frontend.sh 0.16.3` trong cửa sổ bảo trì. Không thêm cờ. Hướng dẫn tách Mac/VM: `docs/phat-hanh-0163.md`. Không chạy các lệnh này trong thư mục Mac. Nghiệm thu nhân sự/hàng/tồn/máy in thật vẫn để cuối.

## 21/10/2026 — Đã gộp bản tối ưu0.16.3 vào main, chờ chủ dự án gắn tag

Theo yêu cầu tiếp tục, PR #26 đã gộp bằng merge commit **a1f95b062f2ff7334ed36c176dfb742bf828974a**, giữ lịch sử mã kiểm12d9d24 và commit hồ sơ54dfacc. Tree mã app giống mã đã đạt bốn cổng; không squash/đẩy đè main. Tag v0.16.3 chưa tồn tại khi kiểm trước gộp. Production vẫn0.16.2/digest34a32f71…/28cờ; chưa phát hành image, chưa chạy VM.

Đã chuẩn bị hướng dẫn cụ thể `docs/phat-hanh-0163.md`, tách Mac (chủ dự án gắn tag đúng merge commit trên) và SSH erpnext-prod (chỉ sau workflow phát hành success: diễn tập bản sao rồi nâng theo runbook, không cờ mới). AGENTS quy định chủ dự án tự gắn tag; agent chưa tạo/push tag. PR ghi nhận bước này chỉ tài liệu, không cần coi là mã app kiểm mới. Các run bốn cổng và giới hạn giữ ở mốc dưới. Bước chờ: chủ dự án gắn tag, chờ image và diễn tập production thực; không coi CI ĐẠT là production ĐẠT.

## 21/10/2026 — Bản tối ưu0.16.3 đã kiểm kỹ thuật, chưa phát hành

[PR #26](https://github.com/tienduongmarcom/aphvh/pull/26), nhánh `feat/toi-uu-giao-dien-20261020`; mã nghiệp vụ và kiểm cuối **`12d9d24a2ce613b354fc1e72ad815f984e4a217c`**. Commit hồ sơ theo sau chỉ đổi tài liệu, không phải mã nghiệp vụ được kiểm mới. Production vẫn **0.16.2**, digest `sha256:34a32f71f10f20421405c0bd1155abb0570b1d48b564f1df6b8e25d6aa146917`,28 cờ theo xác nhận bàn giao; không truy cập/sửa VM, không tag, gộp hoặc phát hành image trong lượt này.

Đã làm: năm khu Bán hàng / Kho vận / Tiền và kế toán / Nhà máy / Dữ liệu và cấu hình; Nhà máy riêng, tái dùng đủ lối cũ trước khi ẩn các thế hệ Việc/Bàn/Trung tâm. Custom Sidebar chuẩn mang tên Vận hành, ẩn tham chiếu cũ cho cả Workspace Manager, giữ tùy chỉnh riêng và nguồn/route. Đầu đơn hiện nhận diện khách hiện tại, SĐT/địa chỉ hoặc thông báo thiếu; gợi ý theo quyền; công nợ hóa đơn gọn và xem chi tiết. Mã/tên hàng riêng; cửa thu nhanh dùng chung service/mã lượt cũ; giảm nút/in lặp; chỉ một bộ nhập giao nhận theo thế hệ phiếu. Tên hiển thị chung trung lập; số đơn MỚI dùng DBC, số cũ/ID/Link giữ nguyên. Không thêm cờ/quyền, không đổi GL/SLE/PLE hoặc thời điểm ghi kho/nợ/tiền. Mẫu ba liên vẫn là bản nháp.

Bốn cổng **success cùng mã trên**:
- [Cổng2 / cài mới](https://github.com/tienduongmarcom/aphvh/actions/runs/39461537062).
- [Cổng2b / triển khai–quay lui](https://github.com/tienduongmarcom/aphvh/actions/runs/39461551570).
- [UAT HTTP/Chrome](https://github.com/tienduongmarcom/aphvh/actions/runs/39461545287): đã tải/đọc13 tệp, **308 bản ghi PASS,0 FAIL**, gồm kỹ thuật/chuẩn bị/khôi phục; b014117 PASS. Core63.508 tệp không đổi. Đã kiểm ca mất phản hồi thu tiền/gửi lại: một PE, không thêm GL/PLE; metadata năm khu/Sidebar và nhận diện khách theo quyền.
- [Cổng3 / nâng từ0.16.2, lượt2](https://github.com/tienduongmarcom/aphvh/actions/runs/39461556488/attempts/2): đã đọc đúng artifact12286420231 tại `work/ci-toi-uu-12d9d24/cong3-luot2-chinh-xac/`. Diễn tập tách biệt và triển khai0.16.3 ĐẠT; schema nâng/site mới1099/1099, lệch0, bỏ qua6/6 theo cấu hình; rollback1105/1105, đếm/tổng/cờ/phiên bản/cài đặt/giao diện khớp. Ca cố ý lỗi tự quay về0.16.2 và giữ bảo trì, đếm/tổng/chi tiết/phiên bản khớp. Nền CI sổ giao dịch0 không thay diễn tập bản sao production có dữ liệu lúc phát hành.

Cục bộ **454 ca kh_aph (14 bỏ qua theo môi trường),108 ca lõi đạt**; Python/JS/diff đạt. So tĩnh27 JSON giữ trường/kiểu/Link/quyền và5 nhóm hook kiểm soát; chỉ autoname cấp số mới thay đổi. Đã xem ux-viec-ban-hang.png, ux-buoc-tiep.png, xuat-ngay-retry.png: thanh bên quản trị còn năm khu, tên Vận hành/DBC và cột mã–tên có trong ảnh. Ảnh Workspace chụp khi nội dung còn mờ lúc chuyển trang, ảnh bước tiếp có hộp thoại; không dùng chúng khẳng định đã nghiệm thu độ dễ đọc/toàn bộ nhãn tiếng Việt. Số đo máy T01/T03 không giảm số thao tác, T02 từ5 xuống4; không suy thành tiết kiệm thời gian của nhân viên.

Giữ bằng chứng lỗi, không giảm assert: UAT39458034247/dba7604 FAIL vì ca Chrome tìm nút Thu tiền cũ trên Customer; đã cập nhật đúng tên Ghi nhận khách trả tiền, giữ kiểm mất phản hồi/retry/một PE. Xem ảnh lượt đó phát hiện quản trị vẫn thấy Workspace cũ; sửa tham chiếu hidden, có unit/HTTP và ảnh mới đối chiếu. Cổng3 [39461556488/lượt1](https://github.com/tienduongmarcom/aphvh/actions/runs/39461556488/attempts/1) FAIL vì MySQL1020 tại kho_chuan.dung cập nhật tabCompany trên IMAGE NỀN0.16.2, trước nâng ứng viên; giữ log/artifact lượt1 tại work/ci-toi-uu-12d9d24/cong3, chạy lại cùng SHA lượt2 đạt; không tuyên bố đã sửa gốc xung đột này. Các lượt hủy khi bổ sung mã không là PASS. Hai ca Chrome chập chờn từ hồ sơ Claude tiếp tục theo dõi, không kết luận đã chữa chỉ vì lượt này xanh.

Còn lại: duyệt/gộp PR và phát hành theo runbook khi chủ dự án chọn; chủ dự án tự gắn tag. Trước production phải diễn tập bản sao thực còn hạn, đúng image/commit/khach.json/cờ. Nghiệm thu với nhân sự, hàng/tồn và máy in thật để cuối theo yêu cầu. Công nợ trên đơn chỉ tổng hóa đơn số dư dương trong quyền, không phải số dư công nợ ròng; đối chiếu/chốt bằng báo cáo chuẩn. Tắt cờ không tự xóa metadata hoặc khôi phục mọi cấu hình Sidebar. Hướng dẫn và ca nghiệm thu: `docs/huong-dan-giao-dien-0163.md`; phạm vi9 nhóm: `docs/dac-ta-toi-uu-giao-dien-0163.md`.

### Nhật ký các mốc trước — không thay trạng thái mới nhất ở trên

## 20/10/2026 — ĐANG KIỂM: ẩn tường minh màn cũ cho cả quản trị

Đã xem ảnh xuat-ngay-retry.png của dba7604: nhãn Vận hành/DBC/thông tin khách/cột mã–tên đã có, nhưng Administrator vẫn thấy Trung tâm cũ. Nguồn Frappe16.52 cho Workspace Manager xem is_hidden, nên cấu hình Custom Sidebar bổ sung tham chiếu hidden cho đúng các Workspace cũ thuộc module; không sửa quyền/xóa trang hay ẩn trang riêng. Unit454 (14 skip) đạt, mở rộng HTTP giữ kiểm năm màn mới và tham chiếu cũ ẩn. Các lượt69131a7 hủy khi đang chuẩn bị image do bổ sung này; không là PASS. Cần bốn cổng/ảnh đúng mã mới trước kết luận; production0.16.2 giữ nguyên.

## 20/10/2026 — ĐANG KIỂM: đồng bộ ca Chrome với cửa thu tiền đã gom

UAT39458034247 tại dba7604 FAIL ở DESK_2B_CASHIER_LOST_RESPONSE: selector còn tìm nút Thu tiền cũ trên Customer, trong khi UX chỉ giữ Ghi nhận khách trả tiền. Sửa đúng hai điểm chọn nút, không đổi thao tác thu/gửi lại hoặc assert một PE/không thêm GL/PLE, không sửa mã nghiệp vụ để né lỗi. Log và artifact FAIL giữ tại work/ci-toi-uu-dba7604 và work/reports. Cổng2 39458030862 và2b39458019691 success dba7604; Cổng3 còn chạy, chưa kết luận toàn bộ. Thêm hướng dẫn docs/huong-dan-giao-dien-0163.md; production vẫn0.16.2, chưa tag/deploy. Bước tiếp: chạy lại bốn cổng đúng mã có selector mới, xem ảnh và đối chiếu bằng chứng.

## 20/10/2026 — Chuẩn tiền tố đơn bán chung mới

Ứng viên0.16.3 dùng `DBC-{YYYY}-{#####}` cho đơn mới theo quy tắc tên trung lập (Đơn bán chung). Chỉ đổi autoname của DocType nguồn; không rename/backfill đơn cũ, không sửa ID DocType/role hoặc liên kết. Các ghi chú trước "không đổi số đơn" chỉ còn đúng với số đã tồn tại; không coi tiền tố APH-SO là tên dùng chung cho đơn mới. Có kiểm metadata trong HTTP;4cổng đúng mã mới còn kiểm, chưa phát hành. Production vẫn0.16.2.

## 20/10/2026 — Bổ sung thanh bên chuẩn cho ứng viên0.16.3

PR #26: cấu hình `Custom Sidebar` chuẩn Frappe, nhãn chung Vận hành, giữ năm Workspace và ẩn lối DocType/Report tự sinh do app sở hữu. Dựa vào định nghĩa trong package + phiếu duyệt bán chịu tạo động; không ẩn chứng từ/báo cáo riêng người dùng, không xóa nguồn hoặc sửa lõi. Giữ lớp tùy chỉnh riêng của từng người. Bộ cài chạy lại chỉ ghi khi cần, dùng cờ UX hiện có. Có unit và mở rộng HTTP để kiểm cấu hình. Cục bộ **454 test (14 skip) +108 lõi đạt**. ĐANG DỞ:4cổng/ảnh trên mã có Sidebar; Cổng2 và2b đã success ở bản trước Sidebar `8a5e003`, không thay bằng chứng cho mã mới. Production vẫn0.16.2/28cờ, chưa tag/deploy.

## 20/10/2026 — Ứng viên tối ưu giao diện đang kiểm, chưa phát hành

PR #26, nhánh `feat/toi-uu-giao-dien-20261020`, mã nghiệp vụ đầu `cc616a3`: năm khu Bán hàng/Kho vận/Nhà máy/Tiền và kế toán/Dữ liệu và cấu hình; tái dùng đủ lối cũ, dựng xong mới ẩn tên cũ và map mặc định/profile. Đầu đơn nhận diện khách và công nợ hóa đơn chỉ đọc, không dùng số cũ khi đổi khách; mã/tên hàng riêng ở cửa chuẩn bị giao. Một cửa thu tiền dùng service cũ, giảm nút/in lặp, chọn bộ giao nhận theo thế hệ phiếu; nhãn chung trung lập, giữ ID kỹ thuật/role guard. Không đổi sổ, số đơn, giữ tồn lúc in hoặc mẫu3liên. Dùng cờ UX hiện có, không thêm quyền/cờ.

Cục bộ **453 test kh_aph (14 skip) +108 lab9x đạt**, Python/JS/diff đạt. ĐANG DỞ: kiểm4cổng và ảnh trình duyệt đúng nguồn; chưa PASS CI, không version/tag/deploy. Production vẫn0.16.2/28cờ. Bộ thử HTTP/Chrome đã mở rộng kiểm5khu, scope gợi ý khách, nhận diện và cột hàng. Hai ca Chrome chập chờn từ bàn giao vẫn giữ giới hạn, không coi là đã sửa.

## 20/10/2026 — Codex tiếp nhận PR #25 và ghi phạm vi tối ưu mới nhất

Nguồn nhận `7dcff5a`; đã đối chiếu diff chỉ tài liệu, GitHub không có PR mở. Bốn cổng và phát hành0.16.2 đều success đúng95a8b1e, Cổng3 mốc0.16.2 success e062287. Đã tải artifact UAT39427294383:13 tệp http,308 bản ghi PASS/0FAIL (gồm kỹ thuật/chuẩn bị/khôi phục), b014117PASS; xem ảnh ux-viec-ban-hang.png. Chi tiết, giới hạn và yêu cầu hội thoại mới tại `docs/dac-ta-toi-uu-giao-dien-0163.md`. Yêu cầu mới thay các đề xuất chờ chốt cũ của Claude về bố trí: Nhà máy riêng; khách luôn hiện SĐT/địa chỉ; mã và tên hàng riêng; công nợ gọn; tên chung trung lập. Không tự đổi series/số đơn/roleID/giữ tồn lúc in hoặc duyệt mẫu3liên.

**ĐANG DỞ:** mới hoàn tất tiếp nhận và ghi phạm vi; chưa sửa mã nghiệp vụ/schema/quyền. Nhánh tiếp nối `feat/toi-uu-giao-dien-20261020`; bước tiếp chuẩn tên/điều hướng, giữ đủ lối cũ trước ẩn. Không tăng version/tag/push/deploy. Production vẫn0.16.2 theo xác nhận hồ sơ; không kiểm VM trong lượt này. Hai ca Chrome mở theo hồ sơ vẫn giữ giới hạn, không tuyên bố đã sửa.

## 20/10/2026 ~22:45 — MỐC BÀN GIAO Claude → Codex (production 0.16.2 ĐẠT)

Chủ dự án yêu cầu bàn giao tập trung. **Claude dừng mọi chỉnh sửa trong cùng phạm vi kể từ mốc này** (kể cả bản đổi tên 0.16.3);
Codex kiểm lại bằng nguồn và bằng chứng dưới đây rồi tiếp tục. Không có mật khẩu/token trong hồ sơ.

### 1. Nguồn hiện tại
- Repo `tienduongmarcom/aphvh`, nhánh `main` = **`72e6a0b4f9cc44465f92bd023231b253e63b1237`** (merge PR #24). Hồ sơ này là PR riêng
  (`claude/ho-so-ban-giao-20261020`), chỉ đổi tài liệu + chép bản nháp mẫu in; không đổi code/schema.
- PR đã gộp hôm nay: #19 (chuỗi #9–#19: tiền đợt 2, nhà máy đợt 3, UX-01), #20 (0.16.1), #21 (Cổng 3 mốc 0.16.0), #22 (sửa
  `nang-cap.sh`), #23 (0.16.2), #24 (mốc 0.16.2). PR #9–#18 đã ĐÓNG KHÔNG GỘP vì nội dung đi qua chuỗi #19 (có bình luận trên từng PR).
  **Không còn PR mở** ngoài PR hồ sơ này.
- Tag do chủ dự án gắn: `v0.16.0`=457be4a, `v0.16.1`=cfdd5af, `v0.16.2`=95a8b1e.
- Nhánh cũ `claude/*`, `feat/*`, `docs/*`… còn trên remote (đã gộp hoặc thay thế), chưa xóa — không xóa ngoài phạm vi.

### 2. Thay đổi chưa lưu / việc đang dở
- Trong repo: **không có thay đổi chưa commit** (`git status` sạch trước khi tạo PR hồ sơ).
- **Bản đổi tên/làm sạch 0.16.3: CHƯA BẮT ĐẦU viết code**, chưa có nhánh. Mới có đề xuất trong hội thoại, chép ở mục 5. Chờ chủ dự án chốt.
- Bản nháp **mẫu phiếu 3 liên** (không phải code, chưa duyệt): trang thiết kế riêng của chủ dự án; chủ dự án ĐANG SỬA DỞ (đã bỏ phần
  ký và chân trang ở mẫu chuyển kho). Bản chụp lúc 22:40 lưu ở `docs/de-xuat-mau-3-lien/` (`chuyen-kho-noi-bo.dc.html`,
  `xuat-giao-van-chuyen.dc.html`) chỉ để tham khảo — mẫu in thật chưa làm.

### 3. Production
- `erpnext-prod` / site `frontend`, Compose `~/erp/aph-vh`. Image **`ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.2`**, digest
  **`sha256:34a32f71f10f20421405c0bd1155abb0570b1d48b564f1df6b8e25d6aa146917`** (theo `docker images --digests` người vận hành gửi;
  Cổng 3 kéo theo digest này đạt — run 39441058175). Nền ERPNext 16.51.1 / Frappe 16.52.0 / lab9x 0.2.11 / kh_aph 0.16.2,
  nền `frappe/erpnext@sha256:a856e7f6…`. Nguồn phát hành tag `v0.16.2` = `95a8b1e63358b190faccfa300010445ee799cac9`,
  workflow phát hành **39432250494** success.
- Bằng chứng: log người vận hành 20/10 ~21:35 `=== XONG 0.16.2: ĐẠT ===` (diễn tập bản sao rồi triển khai). Hồ sơ: `khach/aph-vh/phien-ban.yaml`.
- **28 cờ bật** (danh sách sau quay lui 0.16.1 do người vận hành gửi, không cờ mới từ đó): server_cost_guard, post_receivable_on_delivery,
  shared_sales_order, global_credit_warning, high_risk_credit_guard, quantity_valuation_mvp, funds_workflow, source_change,
  factory_costing, factory_cash, sales_adjust, data_review, kho_chuan, sales_p1, quan_tri, du_lieu, dau_ky, kho_van_hanh, gia_san,
  trung_tam_ban, tien_vay, cash_custody, cash_closing, cash_handover, factory_handover, factory_receiving, factory_production,
  ux_task_first (tiền tố `kh_aph_`).
- Lịch sử hôm nay: 0.15.3 → **0.16.0** (~13:20, digest ce8db011…) → **0.16.1** lần 1 TỰ QUAY LUI OAN (kiểm sau nâng cấp ghi
  `KHÔNG ĐẠT: 0` nhưng `| tee | grep -q` dưới pipefail làm tee chết SIGPIPE; tệp kiểm bị cắt giữa JSON) → sửa PR #22 → 0.16.1 lần 2
  ĐẠT (script 62668ab, image 0.16.1 không đổi; SSH rớt giữa chừng, script vẫn chạy xong, so sổ KHỚP; 3 container queue/scheduler phải
  `./erpctl up -d` lại) → **0.16.2** ĐẠT. Quay lui có điều kiện: 0.16.1 (digest không ghi lại được) hoặc 0.16.0 ce8db011… + bản sao lưu
  lúc nâng trong `sao-luu/`; không restore sau khi có giao dịch mới.
- Bài học vận hành: chạy triển khai trong `tmux`; chờ workflow "Phát hành image" đạt rồi mới chạy VM (lần đầu 0.16.2 chạy sớm → image
  not found, dừng ở bước 1, không đụng site).

### 4. Phần đã làm hôm nay (sau 0.16.0)
| Bản | Thay đổi | Code |
|---|---|---|
| 0.16.1 | Đơn bán chung: `delivery_date` mặc định Today; Dialog lập phiếu xuất mặc định "Khách đến lấy" | `aph_shared_sales_order.json`, `.js` (dòng ~22) |
| 0.16.1 | Workspace "Việc …" → "Bàn bán hàng / Bàn kho / Bàn tiền và công nợ / Bàn nhà máy"; khối "Hôm nay cần xử lý"; banner "Bước tiếp theo" | `ux_task.py` (`NHOM`, `_LAM`, `_an_ten_cu`, `TEN_CU`), `public/js/ux_buoc_tiep.js` |
| 0.16.1 | Workspace tên cũ do bộ cài tạo: `is_hidden=1`, người đặt mặc định chuyển sang tên mới; Module Profile "9xLab - Việc …" chưa ai dùng thì xóa | `ux_task._an_ten_cu` |
| 0.16.1 | 24 tên DocType APH dịch không có chữ APH (vd. Đơn bán chung, Phiếu nhận chờ định giá); 23 tên báo cáo có dấu; nhãn Sổ xuất nhập bao | `translations/vi.csv`, `aph_bag_movement.json` |
| 0.16.1 | Mặc định Today: received_date (Phiếu nhận chờ định giá), posting_date (Tiền thực nhận, Xử lý tiền) | 3 DocType JSON |
| 0.16.1 | `nang-cap.sh`: ghi kiểm ra tệp rồi grep (sửa SIGPIPE); `list-apps` cũng vậy | `deploy/khach-hang/nang-cap.sh` (PR #22) |
| 0.16.1 | Cổng 3 bỏ gắn cứng 0.15.3, kiểm theo `PROD_TAG` | `.github/workflows/cong-3-nang-cap-production.yml` |
| 0.16.2 | Customer/Supplier hiện tên trong ô Link (`show_title_field_in_link=1`, title_field); **Item tắt lại** (`0`) — ô Mã hàng hiện mã | `ux_task.HIEN_TEN`, `_hien_ten_khi_chon` |
| 0.16.2 | Dòng đơn chung thêm cột `item_name` "Tên hàng" (fetch_from item_code.item_name); đơn thêm `customer_phone` (customer.mobile_no), `customer_address` (customer.primary_address), chỉ đọc | `aph_shared_sales_order_item.json`, `aph_shared_sales_order.json` |
| 0.16.2 | Customer `search_fields` thêm `mobile_no` (gợi ý khách hiện SĐT) | `ux_task.TIM_KHACH` |
| 0.16.2 | Chốt ca tiền: ô Đơn vị không xóa quỹ khi onchange mà giá trị không đổi (gốc ca Chrome chập chờn) | `public/js/tien_ca_nhan.js` (~dòng 67) |

Cách dùng: không đổi thao tác nghiệp vụ; thay đổi hiện khi cờ `kh_aph_ux_task_first` bật (đã bật). Hướng dẫn phát hành:
`docs/phat-hanh-0.16.1.md`, `docs/phat-hanh-0.16.2.md`.

### 5. Phần chưa làm / câu hỏi chưa chốt (KHÔNG tự suy diễn)
**Đề xuất 0.16.3 đổi tên/làm sạch — chưa làm, chờ chốt:**
1. Năm Workspace: "Bàn bán hàng" (chủ dự án thấy ổn), "Kho vận" (chủ dự án chỉ định thay "Bàn kho"), "Thu chi và công nợ", "Nhà máy",
   "Dữ liệu"; có bỏ chữ "Bàn" cho đồng đều không — CHƯA CHỐT.
2. Gộp/ẩn bộ Workspace cũ "Trung tâm Bán hàng" (`trung_tam_ban.py`), "Trung tâm Kho" (`kho_van_hanh.py`), "Tiền và vay"
   (`tien_vay.py`), "Trung tâm dữ liệu" (`du_lieu.py`) — hiện 8 Workspace chồng nhau trên thanh bên — CHƯA CHỐT.
3. Thống nhất nhãn: Chốt ca tiền; Lập phiếu xuất & In; Xác nhận nhận hàng (5 biến thể); Mở lại/Chốt xử lý chênh lệch; Đề nghị chuyển
   kho; Phiếu xuất kho (thay "Phiếu giao hàng"); Đơn bán chung / Đơn bán từng đơn vị.
4. Bỏ mã nội bộ khỏi nhãn: "(R054–R056)", "(bước 2)", "(3 đơn vị)", "về 0".
5. Tên khó hiểu: Tuyến tài khoản tiền và thu hộ, Kế hoạch cọc và phân bổ, Số dư đầu kỳ nguồn, Đề nghị số liệu (chỉ định mức?),
   Hóa đơn ngoài (luôn là MISA?), "Hoàn toàn bộ bàn giao", "Trả lại".
6. **Quy tắc chủ dự án (20/10): chữ hiển thị KHÔNG dùng "APH" làm tên chung** (chỉ khi đúng là công ty An Phú Hưng). Còn: vai trò
   "APH Không xem giá vốn" (đổi tên thật bằng rename_doc — 31 tệp tham chiếu, cần cẩn thận), DocType "APH Credit Release" chưa dịch,
   nhãn "Quy tắc tính giá (APH)" (`install.py` ~58), số đơn `APH-SO-{YYYY}-{#####}`.
7. Mẫu số đơn bán chung: DBC- / DB- / DH- — CHƯA CHỐT; chỉ áp đơn mới.
8. Số chứng từ đang là hash (Chốt ca tiền, Bàn giao tiền, Phiếu nhận chờ định giá, Tiền thực nhận…) → số theo năm — CHƯA CHỐT.

**Kho / giao nhận (từ phương án chủ dự án gửi 20/10):**
- Hồ sơ bản ký có 3 trạng thái; thiếu "Đã nhận bản giấy gốc" + vị trí lưu (`ho_so_giao_nhan.py`) — đề xuất, chưa chốt.
- Bàn kho thêm: Đã giao chưa có bản ký / Có bản ký chưa đối chiếu / Bản ký có chênh lệch — đề xuất, chưa chốt.
- Mẫu 3 liên (chuyển kho nội bộ, xuất giao vận chuyển) — chủ dự án đang sửa nháp, kế toán chốt mẫu giấy + thời hạn lưu.
- "Giữ lượng cho lượt giao": hiện chỉ giữ theo đơn (không lập vượt còn lại), tồn chỉ trừ khi xác nhận giao — giữ tồn từ lúc in là đổi nghiệp vụ.
- Vệ tinh không có người dùng phần mềm: quy trình gọi đầu mối / QR — chưa chốt.

**Còn mở từ trước:** chuyển khác đơn vị; hao hụt vận chuyển; lệnh/mẻ sản xuất; TC03/TC05/TC07/TC08 và 5 câu hóa đơn một phần
(`docs/dot-4-5-ra-soat-tai-chinh-hoa-don.md`); phân bổ thu tiền theo số tự nhập từng hóa đơn (cần sửa server); áp Workspace cho từng
người (`ux_task.ap_dung_nguoi_dung`, chạy thử trước — chờ danh sách nhân viên); UX-4 đo người thật; nghiệm thu dữ liệu thật để cuối.
Ô "Kho nguồn" trên đơn thật của chủ dự án từng chọn "Hàng đang vận chuyển - APH" — đã nhắc, chưa chặn bằng code.

### 6. Kiểm thử (4 cổng = UAT, Cổng 2, Cổng 2b, Cổng 3)
| Mã | Phạm vi | Run | Kết quả |
|---|---|---|---|
| 1100619 / fe62ee5 | Cổng 3 mốc 0.16.0 | 39380485282 FAIL (gắn cứng 0.15.3) → 39382358810 | PASS |
| 139ec5f | 0.16.1 nhánh | UAT 39385003775, C3 39385000889, C2 39385000382, 2b 39384998213 | PASS |
| cfdd5af (v0.16.1) | main | UAT 39388098968, C3 39388096051, 2b 39388093768, C2 39388091434; phát hành 39394763705 | PASS |
| 1d1b0a1 | sửa nang-cap.sh | C3 39411790962, 2b 39411788597, C2 39411785874, UAT 39411793609 (39411787335 PR-trigger bị hủy do trùng) | PASS |
| e2ea993 | 0.16.2 nhánh | **UAT 39420392256 FAIL** (ca Chrome quy-nha-may: "missing values: Quỹ tiền mặt") | giữ làm bằng chứng |
| b23ca5f | 0.16.2 + sửa chập chờn | UAT 39423804066, C3 39423800283, 2b 39423796740, C2 39423793170 | PASS |
| 95a8b1e (v0.16.2) | main | UAT 39427294383, C3 39427290220, 2b 39427285899, C2 39427281958; phát hành 39432250494 | PASS |
| e062287 | Cổng 3 mốc 0.16.2 | 39441058175 | PASS |

Unit cục bộ: `test_ux_task` 11 OK, `test_ban_dich`, `test_shared_order_rules` OK. **Lưu ý:** `python3 -m unittest discover -s kh_aph/tests`
chạy cục bộ (không Frappe) báo 52 lỗi ở cả mã trước thay đổi — do môi trường, CI là bằng chứng. Artifact CI không tải được qua công cụ
của Claude (chuyển hướng blob); Codex nên tải ảnh UAT (ux-buoc-tiep.png, ux-viec-ban-hang.png) để xem nhãn mới.
Ca chập chờn: `quy-nha-may` đã tìm ra gốc và sửa ở b23ca5f (theo dõi tần suất); `nhan-hang-nha-may` (dialog không hiện) từng FAIL ở
39360250409/39362652605 — chưa có gốc. **Chưa kiểm bằng Chrome** các nhãn/cột mới 0.16.1–0.16.2 ngoài ảnh UAT; chủ dự án đã xác nhận trên
production: ngày giao tự điền, cột Mã hàng (sau 0.16.2 cần xác nhận lại hiện mã + cột Tên hàng + SĐT/địa chỉ khách).

### 7. Giao diện / quyền / tùy chỉnh trong DB
- Workspace (DB, bộ cài `ux_task.schema()` khi cờ 28 bật): tạo "Bàn …" ×4, ẩn "Việc …" ×4. **Chưa đặt mặc định cho người dùng nào.**
  Workspace cũ "Trung tâm …"/"Tiền và vay" vẫn hiện.
- Module Profile "9xLab - Bàn …" ×4 (chưa gán ai); "9xLab - Việc …" bị xóa nếu không ai dùng.
- Property Setter (DB): Customer & Supplier `title_field`, `show_title_field_in_link=1`; Item `show_title_field_in_link=0`
  (0.16.1 từng đặt Item title_field=item_name — vẫn còn, vô hại); Customer `search_fields` += mobile_no.
- Bản dịch: `translations/vi.csv` (+47 dòng hôm nay). Quyền: không đổi DocPerm/Role hôm nay.

### 8. Dữ liệu / schema
- Trường mới (DocType app, đồng bộ migrate theo hash JSON): `APH Shared Sales Order Item.item_name`; `APH Shared Sales Order.customer_phone`,
  `customer_address`; default Today cho 4 trường ngày. Không patch dữ liệu, không đổi sổ (GL/SLE/PLE): so sổ trước/sau 0.16.1 KHỚP.
- Đơn cũ: cột mới trống đến khi mở/lưu lại (fetch_from không tự điền ngược) — chỉ hiển thị.
- Khôi phục: quay lui image + `quay-lui.sh <thư mục sao-luu>` theo `docs/phat-hanh-*.md`; Property Setter/Workspace là dữ liệu, đi theo bản sao lưu.

### 9. Lưu ý tiếp nối
- **Phụ thuộc tên nút:** `ux_buoc_tiep.js` bấm hộ qua `frm.custom_buttons["<nhãn>"]`; ca Chrome (`ban-nhanh-desk.mjs`, `ux0-desk.mjs`)
  tìm nút/Workspace theo nhãn ("Chốt ca tiền của tôi", "Lập phiếu xuất & In", "Bàn bán hàng"…). Đổi nhãn ở 0.16.3 phải đổi đồng thời các chỗ này.
- **Hai bộ dữ liệu cũ–mới:** Workspace "Việc …"(ẩn) / "Bàn …" / "Trung tâm …"; Module Profile cũ/mới; Property Setter Item title_field.
  Đổi tên Workspace lần nữa phải thêm tên "Bàn …" vào `TEN_CU` để ẩn, không để 3 thế hệ cùng hiện.
- **Nguy cơ sửa chồng:** `ux_task.py`, `translations/vi.csv`, `aph_shared_sales_order*.json`, Cổng 3 workflow (PROD_TAG/DIGEST/FLAGS_CU)
  là điểm nóng. Claude không sửa thêm các tệp này sau mốc bàn giao.
- Thứ tự bắt buộc khi phát hành: 4 cổng trên đúng SHA → tag (chủ dự án) → "Phát hành image" đạt → VM trong tmux → cập nhật
  `phien-ban.yaml` + Cổng 3 mốc mới + hai hồ sơ này.


## 20/10/2026 ~13:20 — Production 0.16.0 ĐẠT (xem TRANG_THAI.md)

Digest `sha256:ce8db011338a7f6f521107999ee515a94366deeb7c96a50b2570376b903ccbf3`, nguồn `457be4a`, 28 cờ. ĐANG DỞ: gộp PR #9–#19 vào main;
baseline Cổng 3 vẫn 0.15.3 (đổi trong PR kế tiếp); Workspace mới chưa đặt mặc định cho ai; ca Chrome `quy-nha-may` chập chờn
(UAT nhánh 39374984958 FAIL, UAT trong workflow phát hành PASS) cần điều tra.

## 20/10/2026 — Claude: rà PR #17/#18, NM01c/NM02–05, UX-01 (đang làm, CHƯA bàn giao Codex)

PR [#19](https://github.com/tienduongmarcom/aphvh/pull/19) nháp, nhánh `claude/nm01c-nhan-chuyen-20261020`, base PR #18. Production vẫn
**0.15.3**; không tag/merge/phát hành. Chủ dự án dặn: làm hết UX, chỉ bàn giao Codex khi được bảo.

- Rà độc lập PR #17/#18 (factory_receiving, pending_order, pending_valuation): không thấy lỗi có bằng chứng. Ghi chú: hủy PR đã
  định giá thì pending về "Chờ định giá" nhưng không chốt lại được (đúng đặc tả 3B: phải hủy pending để nhận lại).
- Mã đã kiểm đủ 4 cổng trên **`eba12d036e667a9b2d2f4a30df20f15c4d307846`**: UAT 39356838490 (b014 đúng 115 PASS, 0 FAIL — gồm 7
  ca NM01c/NM05, 5 ca NM02–04, 1 ca UX-01), Cổng 2 39355987525, 2b 39355985890, Cổng 3 39355984116. Artifact không tải được qua
  công cụ của Claude (chuyển hướng blob) — bằng chứng là bước đếm PASS chính xác + không FAIL của workflow; Codex nên tải và xem ảnh.
- Lượt UAT 39354836759 (42f6796) FAIL ở ca Chrome `quy-nha-may` (PR #16, "No committed preview response intercepted"), không
  liên quan mã mới; lượt sau cùng ca PASS → coi là chập chờn, giữ run làm bằng chứng.
- Mới: `factory_transfer.py` (NM01c nhận chuyến + NM05 chuyển đi, cờ 26), `factory_production.py` (NM02–04, cờ 27),
  `ux_task.py` + `ux_*.js` (UX-01/UX-0/UX-3, cờ 28). Đặc tả: `docs/dac-ta-nhan-chuyen-den-nm01c.md`,
  `docs/dac-ta-ghi-san-xuat-nm02-04.md`, `docs/dac-ta-ux-01.md`, `docs/ux-0-phieu-do.md`, `docs/dot-4-5-ra-soat-tai-chinh-hoa-don.md`.
- Cần chủ dự án chốt (không tự suy diễn): chuyển khác đơn vị; hao hụt vận chuyển; lệnh/mẻ sản xuất; TC03/TC05/TC07/TC08; 5 câu hóa đơn một phần.

**Mã kiểm cuối `a3cfd6d5e3d07759321e4b2dd27243937bfbd5d7`: đủ 4 cổng** — UAT 39368636121 (b014 đúng 117 PASS, 0 FAIL, gồm
UX-0 DESK_UX0_BASELINE và UX-3 HTTP_UX03_TIM_KHACH_CONG_NO), Cổng 2 39368642320, 2b 39368640197, Cổng 3 39368638182.
Lỗi gặp và sửa (giữ run FAIL): Module Profile lưu lại khi đang khóa → DocumentLockedError (UAT 39358739479, Cổng 3 39358741700;
sửa + regression unit); UX-0 trùng tên biến `ws` (UAT 39364565012); dọn hồ sơ Chrome ENOTEMPTY (UAT 39366184701). Ca Chrome
cũ `quy-nha-may`/`nhan-hang-nha-may` FAIL chập chờn ở 39354836759, 39360250409, 39362652605; đã thêm in trạng thái hộp thoại khi
lỗi (không đổi điều kiện) và ba lượt sau đều PASS — Codex nên theo dõi tần suất.
Số đo máy UX-0 (A Desk cũ / B UX): T01 4/4 thao tác, 3/3 màn hình; T02 5/4, 3/3; T03 2/2, 2/2. Không thay số đo người thật.

ĐANG DỞ (theo lệnh chủ dự án, chưa bàn giao Codex): UX-4 đo người thật (`docs/ux-0-phieu-do.md`) để cuối; UX-5 chỉ khi số đo
người thật cho thấy Dialog không đạt. Phân bổ thu tiền theo số tự nhập từng hóa đơn chưa làm (cần sửa server, chờ xác nhận nhu cầu).


## 20/10/2026 — Bàn giao tiếp nối cho Claude theo yêu cầu chủ dự án

Chủ dự án chuyển phần việc tiếp theo và rà lỗi độc lập cho Claude; sau khi Claude hoàn thành sẽ bàn giao ngược cho Codex. Hồ sơ tập trung: `docs/BAN_GIAO_CHO_CLAUDE.md`, gồm baseline e929498/mã kiểm a75ced9, PR #18,4 cổng/293 HTTP và giới hạn, vùng cần rà độc lập, thứ tự phần còn lại và mẫu bằng chứng bàn giao ngược. Đây là commit hồ sơ, không thay code/quyền/schema/production. Production theo xác nhận vẫn0.15.3; nghiệm thu dữ liệu/nhân sự thật vẫn gom cuối. Codex dừng phát triển tại đây để Claude tiếp nối; không coi các vùng cần rà là lỗi đã xác nhận hoặc phần chưa làm là đã hoàn tất.

## 20/10/2026 — Nhận chờ định giá theo đơn mua 3B đã kiểm đủ bốn cổng

[PR #18](https://github.com/tienduongmarcom/aphvh/pull/18), nhánh `feat/nhan-cho-gia-theo-don-mua-20261020`, base PR #17/4b638b0. Mã nghiệp vụ/kiểm cuối **`a75ced9b8b4613d71fe45117bc36b7215f85877d`**. Cùng cửa sổ nhà máy chọn nhận có giá hoặc chờ giá; pending lưu đúng PO/dòng nguồn, người thực nhận, actor/thời điểm, tệp cân private và phần có vấn đề trong tổng lượng. Giữ chỗ lượng chờ trên cả PR chuẩn/PI update_stock, kể cả tắt26. Người có quyền mua cập nhật PO; KTT chốt đúng giá PO qua một PR native, không ghi kho giá0. Hủy PR trả giữ chỗ, hủy pending sau đó giải phóng nhưng giữ hồ sơ. Chỉ miễn đúng backlink pending nguồn khi native hủy PR; mọi backlink khác vẫn kiểm.

Cục bộ **419 kh_aph +108 lab9x** đạt, Python/JS/diff đạt. Bốn cổng success cùng mã cuối: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39350330165), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39350329373), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39350325419), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39350333813). Commit hồ sơ sau đó chỉ đổi tài liệu/AGENTS, không là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact tại `work/ci-pending-a75ced9/`: **293 HTTP/Desk PASS,0 FAIL**, b014102; core63.508 tệp không đổi, hai kiểm kỹ thuật core/site trắng PASS. ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Đủ8 ca mới: giữ chỗ/replay/tệp; PR và PI native khi26=0; chặn đổi mode/giả giá/gỡ nguồn/giảm hoặc hủy PO; hai phiên pending/có giá chỉ một nhận4kg khi còn6; finalize một PR4kg đúng dòng/giá PO; hủy giữ lịch sử; mã chưa có lịch sử giá/PO.rate0 chỉ nhận pending; Chrome bỏ200 sau commit rồi bấm lại một pending1kg/không thêm sổ. Luồng pending cũ không PO cũng PASS: ngoài khả dụng, chặn giá0/vai trò và gán Link native, finalize nguyên tử/retry.11 bản ghi khôi phục baseline đều PASS, gồm pending/child/PI/File/Series.

Đã xem `nha-may-nhan-cho-gia.png`: phiếu09k5kg7mr0 Submitted, PO PUR-ORD-2026-00004,1kg ở trạng thái Chờ định giá, người thực nhận/người nhập/thời điểm rõ; không hiện giá vốn hoặc nút chốt giá cho NoCost. Dữ liệu/tài khoản đều giả. Cổng2b đã đọc log:20 probe nghiêm sau mở bảo trì, kéo image lỗi giữ bản B/web pong, quay lui ci-b→ci-a, kiểm53 dòng/0 lỗi.

Cổng3 đã đọc artifact: schema nâng/site mới **1.085/1.085**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp. Năm cờ mới custody/closing/handover/factory_handover/factory_receiving về0,21 cờ cũ giữ1. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp, workflow kiểm maintenance_mode=1. Nền CI GL0 không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ FAIL [38318ab/UAT39346121476](https://github.com/tienduongmarcom/aphvh/actions/runs/39346121476):2 ca3B đầu PASS, fixture sửa PO thiếu item_code nên native bỏ qua/trả rỗng và helper lỗi KeyError. Sửa payload đủ mã/ngày/mô tả, đọc phản hồi rỗng đúng API, giữ assert giảm PO phải bị chặn/dữ liệu không đổi. Giữ FAIL [02d9a70/UAT39348470916](https://github.com/tienduongmarcom/aphvh/actions/runs/39348470916):6 ca đầu PASS; PO mới cho ItemA tự điền giá mua gần nhất, trái giả định fixture.rate0. Sửa dùng mã mới chưa có lịch sử giá; giữ assert PO.rate0/chặn nhập có giá/finalize0, không giảm assertion/số ca. Artifact/log hai FAIL giữ tại work/ci-pending-38318ab và work/ci-pending-02d9a70. Các lượt0c8d884/8e71fa4 hủy khi bổ sung current-read/capability/tiền tệ và đúng actor fixture, không dùng làm bằng chứng cuối.

Đặc tả9 nhóm và bảng truy nguyên8 ca: `docs/dac-ta-nhan-cho-gia-theo-don-mua-3b.md`; hướng dẫn nhân sự: `docs/huong-dan-nhan-hang-nha-may.md`. Lát3B chỉ PO VND/tỷ giá1, hàng tồn Kg/hệ số1, không lô/sê-ri/gia công/giao thẳng. Pending cũ không tự backfill PO; lượng chờ chưa khả dụng; dấu cần đàm phán là snapshot, không workflow giải quyết giá. Tái dùng26 mặc định tắt, không core patch/ignore_permissions/version/tag/merge/deploy. Production theo xác nhận vẫn0.15.3/21 cờ.

**ĐANG DỞ toàn đợt3:** nhận chuyển đến NM01c, sản xuất/dở dang/đóng gói/xuất và bảng ngày nhà máy còn tiếp theo `docs/dot-3-ra-soat-nguon-nha-may.md`. Bước tiếp: đặc tả9 nhóm nhận chuyến chuyển, phân biệt cùng Company với giao dịch khác Company, giữ nguồn/đang chuyển/đã nhận trên chứng từ chuẩn và chống nhận trùng. Chưa gọi toàn NM01 hoặc đợt3 hoàn tất; nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối.

## 20/10/2026 — Nhận nhanh nhà máy 3A đã kiểm đủ bốn cổng

[PR #17](https://github.com/tienduongmarcom/aphvh/pull/17), nhánh `feat/nhan-hang-nha-may-20261019`, base PR #16/565910a. Mã nghiệp vụ/kiểm cuối **`1fffcbaa9b40faf5b33fe246a6d4c7faf68c7b61`**. Nhận Kg từ đơn mua có giá qua Dialog trên PO hoặc Tồn kho số lượng; tạo một Purchase Receipt chuẩn, ghi người thực nhận, tệp cân riêng tư, ghi chú và phần hàng cần đàm phán trong tổng lượng nhận. Theo quyết định chủ dự án: hàng có vấn đề thường dùng ngay, giá điều chỉnh sau; không tự trả hàng/giảm giá. Cờ26 `kh_aph_factory_receiving` mặc định tắt; không bypass quyền hoặc mở giá vốn cho nhà máy.

Cục bộ **405 kh_aph +108 lab9x** đạt, JS/diff đạt. Cả bốn cổng success đúng mã trên: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39281475156), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39281543596), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39281539311), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39281548157). Commit hồ sơ tiếp theo chỉ đổi tài liệu; không coi đó là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact tại `work/ci-receiving-1fffcba/`: **285 HTTP/Desk PASS,0 FAIL**, b01494; hai kiểm kỹ thuật core/site trắng PASS. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Năm ca mới kiểm quyền/preview chỉ lượng, nhận4kg còn6 và retry một phiếu, chặn giá client/kho sai/sửa dấu, hai phiên chỉ một nhận4kg còn2, Chrome bỏ phản hồi200 sau commit rồi bấm lại cùng Dialog chỉ một PR/một SLE còn1. Tệp cân thật trong UAT giữ private và gắn đúng PR. Đã xem ảnh `nha-may-nhan-hang.png`: PR MAT-PRE-2026-00003 hoàn tất, lượng1kg, người thực nhận/người nhập/thời điểm được lưu, không hiện giá vốn trên form của vai trò bị hạn chế.

Cổng2b đã đọc log: kiểm ping nghiêm sau mở bảo trì, kéo image không tồn tại giữ bản B/web pong, quay lui ci-b→ci-a, kiểm53 dòng/0 lỗi. Cổng3 đã đọc artifact: schema nâng/site mới **1.074/1.074**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp. Năm cờ mới custody/closing/handover/factory_handover/factory_receiving trả0,21 cờ cũ giữ1. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Nền CI GL0 không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ lịch sử lỗi: [be6a44b UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39273247208) FAIL MariaDB1020 ở ca hai phiên; sửa bằng retry_rpc hiện có tại biên receive, rollback/thử lại toàn hàm có giới hạn, không retry lỗi nghiệp vụ. [a7bc040 UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39276735273) bốn HTTP mới PASS nhưng Chrome FAIL404 asset; sửa report dùng native render_include, chung nguồn JS với PO, không thêm build/core patch. Bản cuối kiểm cả script được include và File riêng tư; không giảm assertion/số ca. Các lượt b31c976 hủy khi bổ sung current-read/khóa và bảo vệ hồ sơ, không dùng làm bằng chứng bản cuối.

**ĐANG DỞ toàn đợt3:** lát3A mới nhận hàng Kg từ PO có giá hợp lệ, không lô/sê-ri/gia công/giao thẳng. Chưa hoàn tất NM01 hoặc toàn nhà máy. Bước tiếp: đặc tả rồi nối nhận chờ định giá theo từng dòng PO, giữ chỗ lượng giữa pending và PR; sau đó nhận chuyển đến, sản xuất/dở dang/đóng gói/xuất và bảng ngày theo `docs/dot-3-ra-soat-nguon-nha-may.md`. Nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối. Chưa tăng version/tag/merge/deploy; production theo xác nhận vẫn0.15.3/21 cờ.

## 19/10/2026 — Quỹ nhà máy, chốt ca cá nhân và bảng ngày đã kiểm đủ bốn cổng

Nhánh `feat/hoan-tat-quy-nha-may-20261019`, [PR #16](https://github.com/tienduongmarcom/aphvh/pull/16), base PR #15/35d7d42. Mã nghiệp vụ/kiểm cuối **`d0c1f16fb7287da84066f9142bc304be2f616918`**. Nối nguồn quỹ nhà máy với một bàn giao/giữ chỗ/đối chiếu/hoàn chung; chốt ca tự thân và bảng native Chốt ngày và cần xử lý. Không cấp GL/JE/H/snapshot native cho nhà máy hoặc sửa C.guard. Cờ25 `kh_aph_factory_handover` mặc định tắt. Không version/tag/merge/deploy; production theo xác nhận vận hành vẫn0.15.3/21 cờ.

Cục bộ **394 kh_aph +108 lab9x** đạt, Python/JS/diff đạt. Bốn cổng đúngd0c1f16: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39264983886), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39264983968), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39264977970), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39264989203). Cả bốn cổng đều success đúng mã nghiệp vụ/kiểm này; đã đọc artifact và xem ảnh. Commit hồ sơ sau đó chỉ đổi tài liệu/AGENTS, không là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact UAT đúngd0c1f16: **280 HTTP/Desk PASS,0 FAIL**, b01489; hai kiểm kỹ thuật core/site trắng cũng PASS. Core63.508 tệp không đổi, ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Đã xem `nha-may-chot-ca.png`: nguồn nhận25/30 ở trạng thái Chênh lệch đã đối chiếu, phiên nhà máy tự chốt và retry trả ca u5ig2j8g1g; chỉ một ca. Đã xem `chot-ngay.png`: report native đủ8 nhóm, dòng cần xác minh vẫn còn, không popup che bảng. Dữ liệu đều giả. Cổng2b đã đọc log:20 probe nghiêm sau mở bảo trì, kéo image không tồn tại không đổi bản B/web vẫn pong, quay lui ci-b→ci-a và kiểm53 dòng/0 lỗi.

Cổng3 đúngd0c1f16 đã tải/đọc artifact `cong-3-bang-chung`: schema nâng/site mới **1.065/1.065**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp. Bốn cờ custody/closing/handover/factory_handover từ1 trả về0,21 cờ cũ giữ1. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp, log giữ bảo trì và workflow kiểm maintenance_mode=1. Nền CI có GL0; không thay diễn tập bản sao production có dữ liệu khi phát hành.

Bản trước b375ff0 đã đủ4 cổng, **280 HTTP/Desk PASS,0 FAIL**, b01489; artifact UAT/Cổng3 đã tải/đọc, ảnh ca nhà máy và bảng ngày đã xem. QA ảnh phát hiện report hiện popup che bảng: ValidationError đã chuyển thành dòng cần xác minh vẫn còn trong message_log. d0c1f16 chỉ gỡ thông báo mới của lỗi đã xử lý, giữ thông báo trước và không nuốt PermissionError; thêm unit và Chrome assert không popup. Ảnh mới d0c1f16 đã kiểm như trên; không dùng ảnh b375 làm bằng chứng giao diện sạch.

12 ca mới kiểm: nguồn cũ đã nhận giữ nguyên/chờ phải chuyển tiếp; một H giữ chỗ; hai phiên qua lối cũ và native chỉ một JE/hai GL, không PE/PLE mới; cùng Cash thiếu5 không JE; hoàn Cash/Bank đúng người nhà máy không cấp GL; mốc mới+ca+tệp đóng vụ; hủy giữ chỗ giữ lịch sử; tự chốt/retry/đổi nội dung/nháp lỗi thời; Chrome bỏ200 sau lưu nháp và chốt rồi retry cùng cửa sổ; bảng ngày đúng quyền/tiền/ca/sao kê native/hàng/nợ và chỉ đọc. Đặc tả9 nhóm cùng bảng truy nguyên case tại `docs/dac-ta-hoan-tat-quy-nha-may-2b.md`.

Giữ FAIL [39234474071/28aad95](https://github.com/tienduongmarcom/aphvh/actions/runs/39234474071):77 ca cũ PASS, ConnectionResetError lúc chờ web sau bật cờ25; sửa chỉ readiness/luôn trả cờ finally và trace, không retry mù nghiệp vụ. Các lượt44e1bb hủy khi bổ sung User Permission nguồn và chặn phản hồi UI cũ; c53301d hủy khi bổ sung ngoại lệ đúng backlink nguồn khi cancel. Native Frappe16.52 kiểm backlink sau cancel: chỉ miễn đúng bản nguồn gương dưới capability, mọi backlink tĩnh/động khác vẫn kiểm. Không giảm assertion hoặc số ca.

Tiền/cọc/việc tồn theo hiện tại; thực đếm ghi thời điểm ca gần nhất, nợ đến ngày chọn. Sao kê chỉ từ Bank Transaction native đã lưu; kết quả đối chiếu tệp tạm chưa có lịch sử lưu, không tự coi đã khớp. Nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Khi phát hành vẫn diễn tập bản sao production có dữ liệu và rollback image+DB/files+cờ đồng thời; không tắt riêng cờ để xóa projection. Bước tiếp theo: rà nguồn và lập đặc tả9 nhóm cho đợt3 màn nhập lượng một lần, bắt đầu nhận hàng/phiếu cân rồi sản xuất–đóng gói–xuất; tái dùng nghiệp vụ nền. Đợt4 chốt toàn chuỗi còn tiếp; đợt5 hóa đơn một phần phải chốt đặc tả riêng.

## 19/10/2026 — Tiền cá nhân chỉ đọc đã kiểm đủ bốn cổng

Nhánh `feat/tien-ca-nhan-20261019`, [PR #15](https://github.com/tienduongmarcom/aphvh/pull/15), base PR #14/a50f5f1. Mã nghiệp vụ/kiểm cuối **`fe3140ad38e3febea317a32f07b1aee7f0b6969a`**. Không tăng version/tag/merge/deploy, không thêm schema/cờ/DocPerm. Production theo xác nhận người vận hành vẫn0.15.3/21 cờ; candidate24 cờ, ba cờ tiền mới mặc định tắt.

Facade `personal_cash.accounts/current` và Dialog **Tiền tôi đang giữ** trên Khách hàng/Phiếu quỹ nhà máy chỉ xem số trách nhiệm, giữ chỗ, khả dụng của session đang đăng nhập. Dùng chung công thức/mốc/khóa Cash với chốt ca và delta bàn giao; không suy owner. NoCost/nhà máy kể cả cộng quản lý chỉ quỹ cấu hình, kiểm Company/Account User Permission. Chỉ đọc cột Cash/metadata nội bộ, không trả GL/nguồn/đối ứng/phân bổ người khác hoặc cấp quyền GL/chốt/nhận/hoàn. Giữ quyền JE native có sẵn: không suy NoCost cộng Accounts Manager bị chặn mọi JE. Đổi Company/quỹ xóa số cũ và bỏ phản hồi lỗi thời. Sửa cleanup Dialog chênh lệch giao nhận từ finally sang always theo jqXHR nền ghim; chưa kiểm riêng mất phản hồi ở lối chênh lệch này.

Cục bộ **375 kh_aph +108 lab9x** đạt, Python/JS/diff đạt. Đúngfe3140a: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39226640207), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39226651607), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39226647318), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39226655570) đều success. Commit hồ sơ sau mã này chỉ đổi tài liệu, không là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact UAT đúngfe3140a: **268 HTTP/Desk PASS,0 FAIL**, b01477; hai kiểm kỹ thuật core/site trắng cũng PASS. Năm ca mới kiểm scope/no GL, nguồn nhà máy/PE/chưa rõ không suy owner, giữ chỗ đúng người và delta cùng Cash không thêm GL/PLE, Chrome dùng phiên nhà máy giả riêng/cùng principal server (không Administrator) bỏ200 rồi đọc lại/đổi APH→VH→APH, hủy sau mốc/vụ lệch riêng người/mốc lỗi phải xác minh. Đã xem `tien-ca-nhan.png`:332/0/332, readonly, form sạch, chỉ đúng quỹ. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Đây là dữ liệu UAT giả.

Cổng2b đã đọc log:20 probe nghiêm sau mở bảo trì, image không tồn tại không gián đoạn web, quay lui ci-b→ci-a và kiểm53 dòng/0 lỗi. Cổng3 đã tải/đọc artifact `cong-3-bang-chung`: schema nâng/site mới **1.065/1.065**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ tiền về0. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp, log giữ bảo trì và workflow kiểm maintenance_mode=1. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL: [39199145864/874aa53](https://github.com/tienduongmarcom/aphvh/actions/runs/39199145864) cleanup native delete không có message, sửa caller raw; [39201881053/4651d2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39201881053) Chrome chưa bắt được phản hồi, bổ sung principal server/API probe/chẩn đoán và chờ form sẵn sàng; [39221412038/7978ad5](https://github.com/tienduongmarcom/aphvh/actions/runs/39221412038) bộ thử đọc Currency readonly0 qua get_value thành undefined/NaN, sửa kiểm số gốc0 và vùng hiển thị đúng control Frappe16.52.0, không mặc định undefined thành0; [39224149992/3b64df6](https://github.com/tienduongmarcom/aphvh/actions/runs/39224149992) Chrome đã PASS nhưng HTTP dùng lại cookie đã khởi tạo CSRF trong Desk, sửa tách hai phiên cùng nhân sự giả. Không tắt CSRF/giảm assertion/số ca. Các lượt cũ hủy khi đổi mã không thay bằng chứng cuối.

**ĐANG DỞ đợt2B:** bước nền xem tiền đã kiểm kỹ thuật; adapter phiếu quỹ nhà máy sang giữ chỗ/đối chiếu chung, quyền tự chốt/nhận/hoàn nhà máy và bảng chốt ngày/ngoại lệ còn tiếp. Đặc tả9 nhóm và điều kiện adapter kế tiếp tại `docs/dac-ta-tien-ca-nhan-2b.md`. Bước tiếp chốt quỹ nhận trước gửi, một H duy nhất nối nguồn factory, các lối nhận cùng một JE/state atomic; giữ ca cũ đã nhận, xử lý chuyển tiếp ca chờ thiếu mốc/người. Không mở guard/GL để vượt NoCost. Nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Khi phát hành vẫn diễn tập bản sao production có dữ liệu và rollback snapshot/image/cờ theo runbook; không tắt riêng bàn giao để xóa projection.


## 19/10/2026 — Thu quầy/quỹ cũ và bảo trì đã kiểm đủ bốn cổng

Nhánh `feat/thu-quay-quy-nha-may-20261019`, [PR #14](https://github.com/tienduongmarcom/aphvh/pull/14), base PR #13/2618e72. Mã cuối **`c02c3764dae495a48b564931062cbae3e78d9db3`**. Không tăng version/tag/merge/deploy; production theo xác nhận gần nhất vẫn0.15.3/21 cờ.

Thu quầy có mã lượt theo người gọi + Company, dấu nội dung ngay trên PE và khóa Company xuyên suốt hai hình thức thu. Gửi lại nguyên cửa sổ trả đúng PE cũ; đổi nội dung/hủy phiếu không tự ghi thu lại. Server chặn giả/sửa/sao chép/xóa dấu; không backfill hay suy người giữ từ owner. Khi custody bật, caller quầy phải gửi request_id. Đóng/mở lại hoặc tải lại trang tạo lượt mới: nhân viên cần kiểm phiếu đã thu trước khi thu tiếp.

Quỹ nhà máy cũ chặn người lập/người giữ tự nhận và quản lý/Admin nhận thay; đúng người nhận gửi lại cùng số/tài khoản trả kết quả cũ, không tạo JE lần nữa. Chưa phải adapter đầy đủ sang giữ chỗ/đối chiếu mới. Không cấp GL cho nhà máy. Thủ tục nâng cấp nạp lại backend sau bật/tắt bảo trì, khắc phục cache site_config TTL60 từng web worker trước sao lưu/mở lại; Cổng2b kiểm thêm20 probe nghiêm, không retry/bỏ qua503.

Cục bộ **365 kh_aph +108 lab9x** đạt, Python/JS/shell/diff đạt. Đúngc02: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39195670324), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39195680580), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39195678186) và [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39195684243) đều success.

Đã tải/đọc artifact UAT đúngc02: **263 HTTP/Desk PASS,0 FAIL**, b01472; hai kiểm kỹ thuật core/site trắng cũng PASS. Core63.508 tệp không đổi, ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11. Ba ca HTTP mới kiểm retry/đổi nội dung, hai phiên cùng lượt tiền mặt+bank chỉ hai PE, giả dấu/hủy/giữ lịch sử. Chrome cố ý bỏ HTTP200 sau commit rồi gửi lại cùng Dialog, một PE và GL/PLE không tăng lần nữa. Đã xem thu-quay.png: form khách native, toast Đã ghi ACC-PAY-2026-00008, không lỗi. Cổng2b đã đọc log:20 probe nghiêm, kéo image không tồn tại không gián đoạn web, khôi phục ci-b vềci-a đạt.

Cổng3 đúngc02 đã tải/đọc artifact: schema nâng/site mới **1.065/1.065**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ custody/closing/handover về0. Ca cố ý lỗi tự khôi phục đúng0.15.3, đếm/tổng/chi tiết/versions khớp và workflow kiểm maintenance_mode=1. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL: [39190026643/a6fae60](https://github.com/tienduongmarcom/aphvh/actions/runs/39190026643) dùng finally trên jqXHR, sửa always theo request.js Frappe16.52.0; [39192414323/db2201f](https://github.com/tienduongmarcom/aphvh/actions/runs/39192414323) một worker pong rồi worker khác503 do cache bảo trì, sửa nạp lại backend; [39193896826/b7](https://github.com/tienduongmarcom/aphvh/actions/runs/39193896826) cả263 ca parsedPASS nhưng grep đếm thiếu dòng Chrome compactJSON, sửa chuẩn hóa qua emit và assert đúng một case PASS, giữ nguyên số72/assertion. Các lượt hủy khi đổi mã/trùng Cổng2 không dùng làm bằng chứng cuối.

**ĐANG DỞ đợt2B:** nối đầy đủ quỹ nhà máy vào giữ chỗ/đối chiếu và quyền tiền cá nhân tối thiểu không GL, sau đó bảng chốt ngày/ngoại lệ. Cần rà cách hoàn tất Dialog chênh lệch giao nhận còn dùng then(...).finally theo cùng phiên bản; chưa kiểm riêng tình huống mất phản hồi của lối đó. Đặc tả9 nhóm: `docs/dac-ta-thu-quay-quy-cu-2b.md`. Nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Bước tiếp theo: đặc tả và nối adapter quỹ nhà máy vào cùng nguồn giữ chỗ/đối chiếu, xây giao diện tiền cá nhân tối thiểu; không cấp GL để vượt chặn NoCost.

## 19/10/2026 — Đối chiếu lệch và hoàn bàn giao đã kiểm đủ bốn cổng

Nhánh `feat/xu-ly-lech-hoan-tien-20261019`, [PR #13](https://github.com/tienduongmarcom/aphvh/pull/13), base PR #12 (6431ec0). Mã nghiệp vụ/kiểm **`8fc93b7a1b674aee3722fe7b1f59de760a2f088d`**. Cờ24 `kh_aph_cash_handover` mặc định tắt, cần custody/closing. Không tăng version/tag/merge/deploy: production vẫn0.15.3/21 cờ, các PR #9–#13 chưa phát hành.

Đã có hai DocType native `APH Doi chieu lech tien` + `APH Can cu doi chieu quy`. Chốt vụ chỉ quản lý, cần xác minh mới sau vụ lệch và ca khớp còn hiệu lực của từng phía Cash, kết quả/tệp riêng tư; không tự tạo JE hoặc sửa số đếm/lệch cũ. Hủy đối chiếu mở lại chặn giao ra, giữ hồ sơ/tệp kể cả nguồn bàn giao đã hủy có quan sát. Ca cũ state trống vẫn được coi mở. Company/Account/GL/nguồn và NoCost cộng manager đều kiểm server; không cấp thêm GL.

Hoàn toàn bộ thực nhận bằng phiếu bàn giao ngược chiều mới: đúng người đã nhận tự gửi, người giao ban đầu tự nhận lại. Khóa tiền/giữ chỗ/kiểm nguồn đã dùng, mã yêu cầu giữ idempotency kể cả hủy rồi lập lại bằng mã mới. Cùng Cash chỉ đảo trách nhiệm; khác Cash hoặc Bank về Cash một native JE mới, JE gốc vẫn đã ghi sổ, không PE/PLE/131/doanh thu mới. Bank chỉ làm nguồn hoàn đúng gốc, không mở chi Bank tùy ý. Không hoàn từng phần hoặc hoàn tiếp phiếu hoàn. Hồ sơ đã gửi/hủy không xóa tay, kể cả Admin. Native Form/Workspace/Dialog có lối vào và lịch sử.

Cục bộ **358 kh_aph +108 lab9x** PASS, Python/JS/diff đạt. Đúng8fc93b7: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39186195911), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39186264582), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39186262143), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39186267181) đều success. Commit hồ sơ sau mã này chỉ đổi tài liệu, không là mã kiểm nghiệp vụ mới.

Đã tải/đọc artifact: **259 HTTP/Desk PASS,0 FAIL**, b01468, giữ249 ca trước và thêm10. Các ca mới: đóng/mở lại với mốc/ca/tệp, hai phiên chốt, ca lỗi thời, nguồn hủy; hoàn cùng Cash/khác Cash/Bank, hai phiên tạo/nhận, nguồn đã dùng bị chặn; Chrome mất phản hồi200 sau commit rồi retry cùng Dialog chỉ một phiếu giữ chỗ, không thêm JE/GL/PLE. Có kiểm hủy/lập lại theo mã mới, tệp trùng giữ URL/blob cũ, không xóa lịch sử. Đã xem `hoan-tien.png`: phiếu hoàn đã gửi/chờ nhận, form sạch và liên kết gốc; sau browser Python xác nhận nhận lại và số quỹ/sổ khớp. Đây là ảnh/dữ liệu giả. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11.

Cổng3: schema nâng/site mới **1.063/1.063**, lệch0, bỏ qua6/6 mục; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ custody/closing/handover đều về0. Ca cố ý lỗi tự quay lui, đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Đã tải/đọc artifact `cong-3-bang-chung`. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL, không bỏ assertion: [39176704265/d415cf3](https://github.com/tienduongmarcom/aphvh/actions/runs/39176704265) upload tệp cùng nội dung bị guard chặn vì native dedupe URL; đã cho File mới riêng tư tham chiếu byte-identical blob có quyền đọc, File cũ/sửa/xóa/công khai vẫn chặn. [39178203449/810fe9d](https://github.com/tienduongmarcom/aphvh/actions/runs/39178203449) native CancelledLinkError cho nguồn hủy; controller chỉ cho đúng source_name là bàn giao hủy có quan sát sau guard manager/quyền/phạm vi/khóa, giữ invalid link/child và link hủy khác; không ignore_links/core patch. [39184751627/033a89a](https://github.com/tienduongmarcom/aphvh/actions/runs/39184751627) equality phản hồi tạo hoàn đồng thời; đã chuẩn hóa Currency None/DB0 và JE rỗng, thêm unit fresh/loaded. Cả ba được kiểm lại trên8fc93b7; các lượt0b79558 hủy khi đổi mã không dùng làm bằng chứng cuối.

**ĐANG DỞ đợt2B:** adapter nhận quỹ nhà máy/thu quầy cũ, token thu cũ và quyền tiền cá nhân tối thiểu không GL còn thiếu. Bước tiếp nối các đường cũ, chặn tự nhận ở đó và chống ghi thu quầy lặp trước khi gọi tiền toàn cửa hàng hoàn tất; đợt3–4 vẫn theo kế hoạch, đợt5 cần chốt riêng. Đặc tả9 nhóm `docs/dac-ta-xu-ly-lech-hoan-tien-2b.md`. Nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Không tắt riêng cờ bàn giao sau phát sinh để xóa projection; khôi phục snapshot/image/cờ theo runbook.

## 19/10/2026 — Bàn giao tiền đã kiểm đủ bốn cổng; đợt2B còn tiếp

Nhánh `feat/ban-giao-tien-20261018`, [PR #12](https://github.com/tienduongmarcom/aphvh/pull/12), base PR #11 (014c05a). Mã nghiệp vụ/kiểm **`1787448b02c5768b0f1b48ee71da7297f78e268e`**. Đã có Native DocType `APH Ban giao tien`, Workspace/Dialog; cờ24 `kh_aph_cash_handover` mặc định tắt, cần custody/closing. Không tăng version/tag/merge/triển khai, production vẫn0.15.3 với21 cờ.

Gửi giữ chỗ nguồn, đúng người nhận tự xác nhận số thực; không tự nhận/nhận thay kể cả Admin. Cùng Cash chỉ chuyển trách nhiệm, không GL/PLE; khác Cash/nộp Bank một native JE hai dòng tiền, không thu khách/giảm nợ lần nữa. Thiếu/thừa lưu lý do/người/hạn xử lý; vượt nguồn chỉ lưu số đếm, không chuyển. Hủy đề nghị chưa chuyển giải phóng giữ chỗ nhưng giữ vụ lệch và blob căn cứ. JE liên kết không sửa/gỡ/hủy tay; ca nháp kiểm lại khi trách nhiệm thay đổi. Ví có lệch chưa xử lý hoặc bất kỳ nhóm trách nhiệm/chưa rõ âm bị chặn giao ra, không suy người đã chi.

Cục bộ **338 kh_aph +108 lab9x** đạt, cú pháp Python/JS và diff đạt. Đúng1787448: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39145460833), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39145541665), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39145540867) và [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39145543386) đều success.

Đã tải/đọc artifact UAT: **249 HTTP/Desk PASS,0 FAIL**, b01458; hai kiểm kỹ thuật core/site trắng cũng PASS. Bảy ca bàn giao đạt: giữ chỗ/cùng Cash không sổ; thực95/100 và retry không đổi nội dung; chuyển Cash; nộp Bank; hai đề nghị tranh nguồn/hai phiên nhận chỉ một JE; vượt nguồn và quyền; Chrome mất phản hồi sau commit rồi nhận lại cùng Dialog không thêm JE/GL/PLE. Trong các ca có thêm nhận25/20,0/10, tệp/vụ lệch giữ sau hủy, nhóm chưa rõ âm chặn giao. Đã xem ảnh `ban-giao-tien.png` đúng mã cuối, hồ sơ sạch/đã nhận/thực20/bút toán liên kết. Core63.508 tệp không đổi, ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11.

Cổng3: schema nâng/site mới **1.061/1.061**, lệch0, bỏ qua6/6 mục; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ custody/closing/handover đều về0. Ca cố ý lỗi tự quay lui, đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Đã đọc artifact `cong-3-bang-chung`. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ bằng chứng lỗi [UAT39141849273](https://github.com/tienduongmarcom/aphvh/actions/runs/39141849273), mã3dadd51: MariaDB1020 ở hai phiên gửi. Đã sửa retry tối đa3 lần tại đúng biên RPC, rollback toàn lần thử, không retry ValidationError/không rollback caller nội bộ; giữ nguyên assertion đồng thời. Mã cuối kiểm lại đạt, không dùng PASS của PR #11 thay cho mã mới.

**ĐANG DỞ đợt2B:** chưa có đảo bàn giao/đóng vụ lệch, adapter nhà máy/thu quầy cũ, idempotency thu quầy cũ hoặc quyền tiền cá nhân không GL. Không coi tiền toàn cửa hàng hoàn tất. Bước tiếp: thiết kế xử lý kết quả lệch/đảo có kiểm soát, rồi nối đường cũ và quyền tối thiểu. Đặc tả9 nhóm `docs/dac-ta-ban-giao-tien-2b.md`; nghiệm thu người dùng/dữ liệu/máy in thật gom cuối theo anh Tiến. Không tắt riêng cờ bàn giao sau phát sinh để xóa projection; khôi phục snapshot/image/cờ theo runbook.

## 18/10/2026 — Lát xác minh quỹ và chốt ca 2B đã kiểm; bàn giao tiền còn tiếp

Nhánh `feat/chot-ca-tien-mat-20261018`, [PR #11](https://github.com/tienduongmarcom/aphvh/pull/11), base PR #10 (14dceff). Mã nghiệp vụ/kiểm **`022322cab2eea0dade0848fa133bbb6c19199273`**. Không tăng version/tag hoặc triển khai: production vẫn0.15.3 theo xác nhận vận hành đã có; các PR #9–#11 chưa phát hành.

Đã có ba DocType native: `APH Xac minh quy` + `APH Phan bo quy`, `APH Chot ca tien`; Workspace Tiền và vay có lối vào và danh sách ca lệch. Cờ23 `kh_aph_cash_closing` mặc định tắt, cần cờ22 custody. Quản lý xác minh phân bổ số dư Cash/VND có căn cứ, phần chưa rõ riêng; người giữ tự chốt phải có/thực đếm/lệch và người/hạn xử lý. Không ghi GL/PLE, không lấy số đếm làm đầu ca mới. Snapshot lưu băm từng GL, actor/time server; nháp/sổ/bản trước đổi thì kiểm lại. Hủy/repost/sửa sổ trước mốc hoặc sổ mới ghi trước ngày chốt phải xác minh lại, bản cũ giữ nguyên. Retry cùng ca không submit hai lần. Tệp kiểm đếm riêng tư đúng hồ sơ, chặn sửa/xóa blob đã xác nhận. Không suy owner/backfill tiền lịch sử.

Quyền native Company/Account/từng dòng GL và từng nguồn vẫn được kiểm; khóa Cash theo company và current read. Account User chỉ đọc/chốt ca chính mình, quản lý không chốt thay; Không xem giá vốn/Kế toán nhà máy bị chặn kể cả cộng quyền. API current chỉ trả số của chính người đang đăng nhập. Chứng cứ JSON chỉ chứa mã GL và băm, không chứa tiền/người của nguồn. Chưa cấp thêm quyền GL cho người bán/nhà máy.

Cục bộ **327 kh_aph +108 lab9x** đạt; Python/JS và diff đạt. Đủ bốn cổng trên đúng022322c: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39138158466), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39138169799), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39138168695), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39138171169). Các lượt trước be3d555/95d384c đã hủy khi thay mã, không lấy làm bằng chứng mã cuối.

Đã tải/đọc artifact: **242 HTTP/Desk PASS,0 FAIL**, b01451; thêm2 kiểm kỹ thuật core/site trắng cũng PASS (244 dòng PASS toàn bộ evidence). Sáu ca mới đạt: phân1000 thành700/200/chưa rõ100; tệp riêng tư/giữ blob; thiếu20/thừa10, không đổi sổ; hai phiên retry và hai nháp cùng khoảng; nháp lỗi thời; hủy sau chốt, xác minh lại có liên kết, sổ lùi ngày; kế toán thường chốt đúng mình, không đọc phân bổ/ca người khác, Company scope và NoCost cộng manager; Chrome đọc snapshot800/800/0, form sạch/khóa. Đã xem `chot-ca-tien.png`; chỉ là ảnh UAT giả. Core63.508 tệp không đổi.

Cổng3: schema nâng/site mới **1.059/1.059**, lệch0, bỏ qua đúng6/6 mục; quay lui **1.052/1.052**, đếm/tổng/cờ/versions/settings/UI khớp, custody/closing đều0. Ca cố ý lỗi tự quay lui, so đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi đến phát hành.

**Bước tiếp theo:** bàn giao/giữ chỗ nguồn/nhận và đảo có kiểm soát; nối adapter quỹ nhà máy, chặn tự nhận, chống lặp thu quầy, vòng xử lý kết quả lệch và quyền tiền cá nhân tối thiểu cho người bán/nhà máy. Chưa có các phần này, không coi toàn bộ2B hoặc tiền toàn cửa hàng đã hoàn tất. Giới hạn lát này10.000 dòng/quỹ, VND; cùng ngày dòng mới theo ID GL/mốc server, không suy giờ nghiệp vụ không có trên GL. Blueprint field/quyền/khóa ở `docs/thiet-ke-chot-ca-ban-giao-2b.md` mục10. Nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật vẫn gom cuối theo anh Tiến.

## 18/10/2026 — Đợt2A người giữ tiền đã kiểm kỹ thuật/UAT;2B còn thiết kế

Theo yêu cầu tiếp tục sau PR #9, đã làm lớp nguồn đợt2A trên nhánh `feat/nguoi-giu-tien-20261018`, [PR #10](https://github.com/tienduongmarcom/aphvh/pull/10), base nhánhPR #9 (30a8773). Mã nghiệp vụ/kiểm **`929d16a84e1f1e6df32d0a614c228060c5e76c4b`**. Thêm cờ thứ22 `kh_aph_cash_custody` mặc định tắt,10 Custom Field trên PE/JE Account/SI/PI/POS/Funds Receipt–Action/quỹ nhà máy; truyền người thực giữ/giao qua đường thu quầy/thu ngay/JE tự sinh. Nguồn submit không đổi người giữ; không suy owner/backfill. Cùng accountCash trên JE không có hai người khác nhau vì GL gộp dòng.

Báo cáo Rà người giữ tiền mặt đọc GL có quyền, nguồn thiếu metadata hiện Chưa xác minh. Đây là phát sinh theo nguồn, KHÔNG là số tiền mỗi người hiện còn giữ; chưa có chốt ca/bàn giao mới. POS tổng hợp/nguồn ngoài adapter vẫn có thể chưa xác minh, chưa kiểm vận hành POS đầy đủ. Đặc tả9 nhóm: `docs/dac-ta-nguoi-giu-tien-2a.md`.

Cục bộ317 kh_aph +108 lab9x đạt, cú pháp Python/JS/diff đạt. Đủ bốn cổng trên đúng929d16a: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39133916442), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39133916266), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39133913616), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39133918974).

Đã tải/đọc artifact: **236 PASS/0 FAIL**, b01445. Bảy ca2A đạt: mặt+bank tách đúng; nguồn chuẩn/không rõ/không đổi sau submit; Receipt/hoàn→JE chỉ đếm một lần; scope/role/report chỉ đọc; SI thu ngay→PE; PI trả mặt; quỹ nhà máy→JE; Chrome mở vùng Accounts chuẩn và kiểm ô có dữ liệu/form sạch. Core63.508 tệp không đổi. Ảnh `nguoi-giu-tien.png` chụp khung đầu form trước cuộn hoàn tất, không dùng ảnh này làm bằng chứng vị trí ô; bằng chứng hiển thị/dữ liệu là assertion Chrome, chưa là nghiệm thu sử dụng thật.

Cổng3 từ production0.15.3/21 cờ cũ: schema nâng/site mới1.056 mục khớp (bỏ qua đúng6 mục); quay lui schema1.052 mục/tổng/đếm/cờ/versions/cài đặt/giao diện khớp; cờ mới về0. Ca cố ý lỗi quay lui khớp chi tiết/versions và giữ bảo trì. Nền CI chưa có phát sinh sổ (các nhóm0), không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ bằng chứng lỗi: [39122361020](https://github.com/tienduongmarcom/aphvh/actions/runs/39122361020) dừng ở Chrome vì vùng Accounts thu gọn, đã sửa thao tác bằng `frm.scroll_to_field`, không bỏ assertion; [39132682231](https://github.com/tienduongmarcom/aphvh/actions/runs/39132682231) thiếu mẫu thuế trên SI thử, đã khai rõ t_aph thay vì nới guard thuế. Lượt929d16a đã kiểm lại cả hai và hai nguồn hóa đơn/quỹ nhà máy.

**Chưa phát hành/merge/tag hoặc triển khai:** production giữ0.15.3/digest đã xác nhận,21 cờ; #9 và #10 chưa đưa vào production. Commit hồ sơ sau929d16a chỉ thay tài liệu, không là mã kiểm nghiệp vụ mới. Nghiệm thu dữ liệu/người dùng/máy in thật gom cuối theo chủ dự án.

**ĐANG DỞ đợt2B:** thiết kế9 nhóm ở `docs/thiet-ke-chot-ca-ban-giao-2b.md`, chưa có code/schema/PASS2B. Bước tiếp chốt blueprint field/DocPerm/khóa/fingerprint cho xác minh tiền bắt đầu và đối chiếu tổng người–quỹ–GL, rồi chốt ca/bàn giao dùng chung. Bao phủ lối quỹ nhà máy cũ, chống tự nhận và token thu tiền mặt cũ; không dùng tổng thu/owner làm tiền đang giữ, không tạo thu khách lần hai. Đợt3–4 vẫn theo kế hoạch; đợt5 chờ nghiệp vụ riêng.

## 18/10/2026 — Gom nghiệm thu thật ở cuối; bổ sung lối in lại A5

Chủ dự án chốt chưa đủ hàng hóa/tồn kho nên nghiệm thu thực tế gom cuối, không chặn phát triển đợt2–4; từng phần vẫn kiểm UAT bằng dữ liệu giả. Đã cập nhật kế hoạch và IN02. Đợt5 vẫn chờ chốt nghiệp vụ riêng.

Ứng viên `feat/in-lai-a5-20261018` thêm nút In → Phiếu xuất kho A5 (2 liên) trên DN đã lưu. `ban_nhanh.print_note` dùng renderer chung với print_batch, kiểm read/print/scope/guard, hỗ trợ phiếu lập chuẩn và snapshot cũ; chặn phiếu hủy/trả. Không tạo/sửa phiếu, không ghi sổ, không cần create/submit. Giá bán thuần/snapshot đã lưu, tổng lượng bỏ trống nếu khác ĐVT. Không schema/cờ mới hoặc sửa core. Đặc tả9 nhóm: `docs/dac-ta-in-lai-a5.md`.

Mã nghiệp vụ **`1e89ace187468d976cb3361d3a0dd6ea75f917c1`**, [PR #9](https://github.com/tienduongmarcom/aphvh/pull/9). Cục bộ305 kh_aph +108 lab9x đạt, JS/Python cú pháp và diff đạt. Đủ bốn cổng trên cùng SHA: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39109706356), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39109822145), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39109706459), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39109824398).

Đã tải/đọc artifact: **229 PASS/0 FAIL**, b01438; `HTTP_014_A5_EXISTING_NOTE` và `NATIVE_DESK_IN_LAI_A5` đạt (bấm hai lần, cùng HTML, không đổi chứng từ/sổ, phiếu chuẩn dùng snapshot cũ). Core63.508 tệp không thay đổi. Đã xem ảnh form và hai trang PDF A5 ngang; đúng hai liên, khối ký không cắt. Cổng3 dùng baseline production0.15.3: tổng/đếm/chi tiết khớp; schema nâng/site mới1.046 mục khớp sau bỏ qua6 mục; quay lui schema1.052 mục/cờ/versions/cài đặt/giao diện khớp; ca cố ý lỗi tự quay lui và giữ bảo trì. Nền CI chưa có phát sinh sổ (các nhóm0), không thay diễn tập bản sao dữ liệu thật khi phát hành.

**Hoàn tất kỹ thuật/UAT lối in lại A5; chưa phát hành.** Production giữ0.15.3, chưa tăng version/tag/merge/triển khai. Nghiệm thu người dùng/dữ liệu/máy in thật gom cuối. Đã rà nguồn đợt2 tại `docs/dot-2-ra-soat-nguon-tien.md`, phát hiện thêm đường thu ngay từ SI cần bao phủ; đây là bản rà, chưa phải đặc tả đủ để code toàn đợt. **ĐANG DỞ đợt2:** hoàn thiện nguồn Cash (POS/PI trả ngay/chi/đầu kỳ/chuyển tiền), bảng field/khóa nguồn/công thức tiền theo người, vòng đời và ma trận quyền trước triển khai. Không tự gán người giữ cho khoản lịch sử chưa rõ. Commit hồ sơ sau SHA trên chỉ thay tài liệu, không là lượt CI nghiệp vụ mới.

## 18/10/2026 — Đối chiếu lại kế hoạch 5 đợt theo production0.15.3

Chủ dự án gửi bảng việc còn lại. Đã cập nhật `docs/ke-hoach-van-hanh-tiep-noi.md` từ mốc0.15.2 sang0.15.3: đồng bộ dữ liệu giao nhận sang mẫu chuẩn/in lại chuẩn/tổng hợp đã nằm trong mã phát hành, không coi là chưa làm. Giữ nền nghiệp vụ đợt2–4 hiện có; phần mở rộng/màn hình thống nhất còn chưa hoàn tất. Sheet Dũng là bước đệm cho đợt3 theo chủ dự án; đợt5 chờ chốt nghiệp vụ.

**ĐANG DỞ GN06:** thiếu nút mở riêng bản A5 từ DN đã lưu; Dialog “Lập phiếu xuất & In” tạo DN, không dùng chỉ để thử máy in. Đã ghi đúng khoảng thiếu ở kế hoạch và IN02; chưa viết tính năng in lại A5 trong lượt đối chiếu này. Nghiệm thu người dùng/máy in/dữ liệu đại diện và quy chế vẫn mở. Bước tiếp là hoàn thiện lối A5 rồi nghiệm thu đợt1; đợt2 cần đặc tả9 nhóm trước code. Chỉ sửa tài liệu, kiểm diff/đối chiếu nguồn; không chạy lại hồi quy hoặc đổi production.

## 18/10/2026 — Production0.15.3 đã triển khai ĐẠT theo log VM

Anh Tiến gửi log từ `tienduongmarcom@erpnext-prod:~/trien-khai`: image0.15.3 digest **`sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`**, kết thúc **`=== XONG 0.15.3: ĐẠT ===`**. Digest khớp [workflow39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607), nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Đây là xác nhận triển khai từ người vận hành; Codex không SSH hoặc kiểm độc lập giao diện production.

Đã cập nhật manifest khách về0.15.3 và baseline Cổng3 sang cùng tag/digest, giữ nền ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11 và21 cờ. Các cổng của release đã kiểm nâng từ0.15.2; baseline mới dùng cho lượt kiểm kế tiếp, chưa coi đã diễn tập CI từ0.15.3. Đã parse YAML và kiểm manifest/baseline/tag/digest/nguồn/21 cờ khớp, cú pháp15 khối shell đạt, 18 ca cấu hình khách/bộ cài đạt, diff đạt. Không đổi mã ứng dụng hoặc triển khai lại VM.

Bước tiếp: tải lại Desk, kiểm mẫu A5 với máy in thật và thông tin giao nhận theo `docs/nghiem-thu-mau-in-20261018.md`; ghi actual trước khi đóng GN06. Quy chế biểu mẫu vẫn là dự thảo; đợt chốt ca/người giữ tiền và nhà máy theo kế hoạch sau. Không nâng lại hoặc restore backup cũ sau khi mở nhập liệu; cần đối soát giao dịch mới nếu có lỗi. Không suy từ log triển khai thành đã nghiệm thu nhân sự/dữ liệu/máy in thật.

## 18/10/2026 — Image0.15.3 phát hành đạt; chờ diễn tập và nâng VM

[Workflow phát hành39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) đã thành công toàn bộ trên tag `v0.15.3` = `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Đã đọc log job phát hành117613939264: kiểm phiên bản/tag đạt, 302+108 unit đạt cả runner và build, image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.3` đẩy thành công với manifest digest **`sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`**. Nhãn revision đúng mã đóng gói.

Đã tải và đọc artifact của chính workflow tag: UAT227 PASS/0 FAIL, phiên bản0.15.3/0.2.11, core63.508 tệp không đổi; Cổng3 tổng/đếm/chi tiết khớp, schema1.046 mục/cờ khớp site mới, quay lui schema1.034 mục/versions/cài đặt/giao diện khớp, ca lỗi khớp và giữ bảo trì. Nền Cổng3 chưa có phát sinh sổ; vẫn bắt buộc diễn tập bản sao dữ liệu production hiện tại trên VM.

**ĐANG DỞ — bước người vận hành:** vào phiên SSH `tienduongmarcom@erpnext-prod`, trong `~/trien-khai` checkout đúng tag, chạy `dien_tap_ban_sao.sh 0.15.3` rồi chỉ khi đạt mới `trien_khai_frontend.sh 0.15.3`; chuỗi lệnh có `&&` tại `docs/phat-hanh-0.15.3.md`. Giữ21 cờ, không thêm cờ. Phiên Codex không có kết nối SSH VM nên chưa tự chạy diễn tập/nâng; production/manifest vẫn0.15.2. Khi có log `=== XONG 0.15.3: ĐẠT ===` và digest khớp, cập nhật manifest và baseline Cổng3 theo bản production mới. Chưa nghiệm thu máy in/nhân sự thật hoặc ban hành quy chế biểu mẫu.

## 18/10/2026 — Chủ dự án đã đẩy tag0.15.3, workflow phát hành đang chạy

Đã kiểm tag remote `v0.15.3` trỏ đúng `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Chủ dự án gửi log đẩy tag thành công. [Workflow phát hành39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) đang chạy lại Cổng2/2b/3/UAT rồi mới dựng và đẩy image. Chưa có digest phát hành0.15.3, chưa triển khai VM.

Nguồn đã thống nhất: PR #4 merge `f05c8a1`; PR #5 merge `8a0ea61e5408e1ef1feff8d2f2dde0aed66d9f2d` vào main. Đã kiểm mã96a7ef0 nằm trong main, phần mã ứng dụng/app lõi/Docker/tools/workflow/UAT/cấu hình khách trên main khớp mã đóng gói; phần sau chỉ thêm hồ sơ. Nghiệm thu máy in/nhân sự và quy chế biểu mẫu còn mở.

**ĐANG DỞ:** theo dõi workflow tag trên đúng SHA, đọc artifact và digest sau khi đạt; sau đó diễn tập bản sao production hiện tại rồi nâng bằng `docs/phat-hanh-0.15.3.md`. Phiên này chưa có SSH tới `erpnext-prod`; production/manifest vẫn0.15.2 cho tới log VM xác nhận.

## 18/10/2026 — 0.15.3 đủ bốn cổng, nguồn chốt qua PR #5 → main

Chủ dự án yêu cầu lên production và đồng bộ nguồn về main. PR #4 đã merge `f05c8a1`, chứa tag0.15.2 và nguồn PR #1–#3. Quyết định gộp tiếp PR #5 vào main bằng merge giữ lịch sử sau khi đủ cổng; mã đóng gói dùng gắn tag vẫn là **`96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`** (kh_aph0.15.3/lab9x0.2.11), không gắn theo commit hồ sơ/merge chưa chạy cổng riêng.

Đạt trên cùng mã đóng gói: [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858), [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872). Cục bộ302+108 đạt. Đã tải/đọc artifact UAT:227 PASS/0 FAIL, b01436, phiên bản đúng0.15.3/0.2.11, core63.508 tệp không đổi. Đã xem hai trang A5 và hai trang tổng hợp A4 từ CI. Cổng3: so tổng/đếm/chi tiết khớp; schema site nâng/site mới1.046 mục khớp (bỏ qua đúng6 mục); quay lui schema1.034/cờ/versions/cài đặt/giao diện khớp; ca lỗi tự quay lui khớp và giữ bảo trì. Nền CI chưa có phát sinh sổ, không thay diễn tập bản sao dữ liệu thật hiện tại.

**ĐANG DỞ:** theo AGENTS mục Phát hành, chủ dự án tự gắn tag `v0.15.3` đúng SHA trên; lệnh trong `docs/phat-hanh-0.15.3.md`. Sau workflow phát hành đạt và có digest mới, chạy diễn tập và triển khai trên phiên SSH `erpnext-prod`. Từ máy hiện tại hostname không phân giải và không có terminal SSH gắn với chat. Production/manifest vẫn0.15.2; chưa có tag/image/digest hoặc log nâng0.15.3. Máy in/nhân sự thật và quy chế biểu mẫu còn mở; không coi yêu cầu triển khai là kết quả nghiệm thu.

## 18/10/2026 — Đã gộp PR #4 vào main; ứng viên 0.15.3 đang kiểm

Theo yêu cầu chủ dự án, đổi đích PR #4 từ nhánh PR #3 sang main rồi merge đúng head `0c1e10425fbfe39eff961ddfef20663f4b70bf9b`, giữ lịch sử. Main mới `f05c8a181c269d2075b6d822addb571f26b7bef6` chứa tag0.15.2 và head PR #2/#3 (đã kiểm ancestry); PR #1 được GitHub đánh dấu merged, #2/#3 vẫn mở nhưng mã đã nằm trong main. PR #5 chuyển đích sang main; chưa merge PR #5.

Ứng viên đóng gói0.15.3/lab9x0.2.11 là `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Cục bộ302+108 đạt. [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858) đang kiểm trên SHA này. Không dùng các cổng7c2217e thay kết quả đóng gói. Bước tiếp đọc artifact rồi chốt tag theo AGENTS; SSH hiện không phân giải được tên VM. Production vẫn0.15.2.

## 18/10/2026 — Chủ dự án yêu cầu lên production, chuẩn bị 0.15.3

Anh Tiến yêu cầu đưa bản mới lên production. Đã đổi nhãn kh_aph0.15.3/lab9x0.2.11, giữ nền16.51.1/16.52.0 và21 cờ. Phạm vi theo PR #5 và mã nghiệp vụ7c2217e đã kiểm. Hướng dẫn đầy đủ tại `docs/phat-hanh-0.15.3.md`. Cần chạy lại bốn cổng trên SHA đóng gói mới; chưa có image/digest0.15.3.

**ĐANG DỞ:** kiểm SHA đóng gói, chốt để chủ dự án gắn tag theo AGENTS, theo dõi workflow phát hành rồi diễn tập/nâng VM. Kiểm SSH chỉ đọc từ máy hiện tại báo không phân giải được tên `erpnext-prod`, không có đường kết nối VM trong phiên này; không coi đã triển khai. Production/manifest vẫn0.15.2. Nghiệm thu máy in thật và ban hành quy chế biểu mẫu còn mở.

## 18/10/2026 — Bộ mẫu trên PR #5 đạt đủ bốn cổng, chưa phát hành

Mã ứng viên: `7c2217e8737e96700fa050aac446bb3591a830a8`, nhánh `feat/thong-tin-giao-nhan-20261017`. Đã đẩy cả sửa phiếu nhanh A5 và bộ mẫu theo chế độ; cập nhật mô tả PR theo phạm vi cuối. Cục bộ 302+108 ca đạt.

Bằng chứng **đều đạt trên cùng SHA**: [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39101464777), [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463208), [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463191), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463224).

Đã tải và đọc artifact UAT: **227 PASS, 0 FAIL**, b014 có 36 PASS. Ca phiếu nhanh xác nhận A5 ngang, giá bán thuần, giấu giá vốn, dấu nháp và sổ không đổi; ca tổng hợp kiểm tám đợt/bốn company, quyền in và sổ không đổi. Core 63.508 tệp không thêm/xóa/sửa so với image nền. Đã xem cả hai trang A5 và hai trang tổng hợp do CI sinh; khối ký không bị cắt. PDF A5 từ CI được chép ra `outputs/phieu-xuat-a5-ci-7c2217e.pdf` của chat.

Đã đọc artifact Cổng 3: so tổng/đếm/chi tiết trước–sau nâng khớp; schema site nâng và site mới 1.046 mục khớp sau bỏ qua đúng sáu mục theo workflow; quay lui khớp schema 1.034 mục/cờ/versions/cài đặt/giao diện; ca cố ý lỗi khớp đếm/tổng/chi tiết/versions và giữ bảo trì. **Nền Cổng 3 không có phát sinh sổ (các nhóm chi tiết bằng 0)**, nên đây là bằng chứng cơ chế nâng/quay lui trên CI, không thay diễn tập dữ liệu production hiện tại.

**ĐANG DỞ:** GN06 còn nghiệm thu máy in/người dùng thật; quy chế biểu mẫu còn là dự thảo. Có chín ca cụ thể tại `docs/nghiem-thu-mau-in-20261018.md`. Bước tiếp in A4/A5 và ghi actual, chốt ứng viên phát hành theo runbook khi đủ điều kiện. Production vẫn 0.15.2; chưa tăng version, tag, merge hoặc triển khai. Commit bàn giao sau SHA trên chỉ thay tài liệu, không là lượt CI nghiệp vụ mới.

## 18/10/2026 — Đồng bộ bộ mẫu theo chế độ kế toán, đang chờ CI và nghiệm thu máy in

Đã cập nhật bảy mẫu chuẩn, phiếu xuất nhanh A5 và đường in biên bản giao nhận theo chế độ của từng đơn vị: APH–TT133, VH–TT99, Minh Khang–mẫu quản trị nội bộ theo TT152, TL–mẫu quản trị nội bộ. Bản in giữ số lượng yêu cầu/thực tế, Nợ/Có, bộ phận, quyển số, chữ ký, trạng thái nháp/hủy và dữ liệu giao nhận mới; không tự ghi sổ khi in. Phiếu kho chuẩn không tự điền giá nếu quyền/nghiệp vụ không cho phép. Đã có booklet xem trước tại `outputs/bo-mau-phieu-thong-tu-2026.pdf` với 19 tình huống giả lập (21 trang, gồm 2 liên giao nhận và 2 liên A5).

Kiểm cục bộ hiện đạt **302 ca ứng dụng + 108 ca lõi**; đã render và xem toàn bộ booklet. Bộ sinh Print Format đã chạy. Đây là mã chưa chạy CI trên SHA cuối và chưa đưa lên production 0.15.2. Quy chế biểu mẫu mới ở trạng thái dự thảo tại `docs/quy-che-bieu-mau-chung-tu.md`, cần kế toán trưởng ban hành trước khi coi là quy định nội bộ chính thức.

**ĐANG DỞ:** chạy lại kiểm sau thay đổi cuối, kiểm CI đúng SHA, in thử A4/A5 trên máy thật và đối chiếu với người dùng; sau khi đạt mới xem xét phát hành/triển khai theo runbook. Không tag, merge, đổi version hoặc triển khai trong lượt này.

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
