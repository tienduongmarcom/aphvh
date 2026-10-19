# Trạng thái phát hành APH-VH (một nơi duy nhất — cập nhật mỗi lần phát hành / triển khai)

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

## 18/10/2026 — Ứng viên in lại A5, nghiệm thu thật gom cuối

Chủ dự án cho phép gom nghiệm thu dữ liệu/người dùng/máy in thật đến cuối kế hoạch; vẫn kiểm UAT giả từng phần trước phát hành. Ứng viên `feat/in-lai-a5-20261018` thêm nút A5 từ DN đã lưu và API chỉ đọc, dùng renderer chung. Mã nghiệp vụ `1e89ace187468d976cb3361d3a0dd6ea75f917c1`, [PR #9](https://github.com/tienduongmarcom/aphvh/pull/9): cục bộ305+108 ca đạt; [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39109706356), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39109822145), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39109706459), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39109824398) đều đạt đúng SHA. Artifact đã đọc:229 PASS/0 FAIL, b01438, core63.508 tệp không đổi; HTTP/Chrome in lại hai lần không tăng phiếu/sổ. Đã xem hai trang A5. Cổng3 đã kiểm từ baseline0.15.3, so nâng/quay lui/ca lỗi khớp và giữ bảo trì; nền CI chưa có phát sinh sổ. Chi tiết ở đầu `docs/ban-giao.md`. Production vẫn0.15.3/digest đã xác nhận, chưa có tag/image hoặc triển khai mới. Bước tiếp hoàn thiện đặc tả đợt2 theo bản rà nguồn `docs/dot-2-ra-soat-nguon-tien.md`, không chờ dữ liệu thật. Chưa có mã chốt ca/bàn giao mới. Commit sau mã kiểm chỉ thay hồ sơ.

## 18/10/2026 — Kế hoạch 5 đợt đã đối chiếu lại, không đổi production

Production vẫn0.15.3/digest đã xác nhận ở mục dưới. Kế hoạch tiếp nối đã cập nhật đúng phần đồng bộ dữ liệu mẫu chuẩn/in lại/tổng hợp có trong0.15.3. GN06 còn lối mở lại A5 từ phiếu đã có và nghiệm thu thực tế; IN02 ghi rõ thiếu nút, chưa tính đạt. Đợt2–4 còn phần mở rộng trên nghiệp vụ nền; đợt5 chờ chốt riêng. Lượt này chỉ cập nhật hồ sơ, không đổi mã/cờ/version hoặc triển khai.

## 18/10/2026 — Production0.15.3 đã triển khai ĐẠT

Người vận hành gửi log `erpnext-prod/frontend`, trong `~/trien-khai`: **`=== XONG 0.15.3: ĐẠT ===`**, image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.3`, digest **`sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`**, khớp workflow39105247607/nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Đã đổi `khach/aph-vh/phien-ban.yaml` và baseline Cổng3 sang bản production này; chưa chạy lại diễn tập CI từ baseline mới.

Nguồn xác nhận là log người vận hành; Codex không có SSH và chưa kiểm độc lập giao diện. Giữ nền/21 cờ. Bản0.15.2/digest `sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333` là mốc lịch sử/quay lui có điều kiện, không tự restore sau khi có giao dịch mới. Bước tiếp nghiệm thu người dùng/máy in A5 theo chín ca trong `docs/nghiem-thu-mau-in-20261018.md`; triển khai đạt không thay nghiệm thu nghiệp vụ thật.

## 18/10/2026 — Image0.15.3 đã phát hành đạt, chưa triển khai VM

[Workflow39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) thành công toàn bộ trên tag `v0.15.3`, nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.3`, manifest digest **`sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`**. Đã đọc log push/metadata và artifact: UAT227 PASS/0 FAIL, core nguyên vẹn, Cổng2/2b/3 đạt, so nâng/quay lui/ca lỗi khớp. kh_aph0.15.3/lab9x0.2.11, nền và21 cờ giữ nguyên.

**Bước tiếp trên SSH máy chủ:** checkout tag trong `~/trien-khai`, diễn tập trên bản sao hiện tại rồi nâng bằng chuỗi `&&` ở `docs/phat-hanh-0.15.3.md`. Nền Cổng3 không có phát sinh sổ, không thay diễn tập dữ liệu thật hiện tại. Phiên Codex không có SSH; chưa ghi đã diễn tập hoặc nâng VM. Production/manifest vẫn0.15.2/digest cũ cho đến log `=== XONG 0.15.3: ĐẠT ===` và digest khớp; sau xác nhận mới đổi manifest và baseline Cổng3. Không đổi tag/image đã phát hành.

## 18/10/2026 — Tag0.15.3 đã đẩy đúng mã, đang phát hành image

Tag remote `v0.15.3` = `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. [Workflow phát hành39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) đang chạy. Chưa có image/digest0.15.3 đạt phát hành; chưa chạy diễn tập hoặc nâng VM.

PR #4 và #5 đã merge main, main ở `8a0ea61e5408e1ef1feff8d2f2dde0aed66d9f2d`, chứa mã đóng gói. Giữ manifest production0.15.2 cho đến log triển khai thành công. Bước tiếp đọc kết quả/artifact/digest phát hành rồi chạy runbook0.15.3 trên SSH máy chủ; phiên Codex hiện không kết nối được tên `erpnext-prod`.

## 18/10/2026 — 0.15.3 sẵn sàng gắn tag; production vẫn0.15.2

Mã đóng gói **`96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`**, kh_aph0.15.3/lab9x0.2.11: đủ [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872). Đã đọc artifact: UAT227 PASS/0 FAIL, phiên bản đúng, PDF A5/tổng hợp đạt kiểm hình; nâng/quay lui/ca lỗi khớp và giữ bảo trì. Nền Cổng3 chưa có phát sinh sổ, cần diễn tập bản sao production hiện tại khi triển khai thật.

Nguồn: PR #4 đã gộp main, PR #5 chốt gộp main giữ lịch sử theo yêu cầu production. Chọn mã đóng gói trên khi chủ dự án gắn tag theo AGENTS; commit sau chỉ thay hồ sơ. Bước tiếp: tag → workflow phát hành đạt/có digest → diễn tập bản sao hiện tại → nângfrontend. Lệnh tại `docs/phat-hanh-0.15.3.md`. Chưa có tag/image0.15.3; phiên này không kết nối được SSH `erpnext-prod`. Manifest giữ0.15.2 cho đến log VM xác nhận. Không ghi đã lên production từ kết quả CI.

## 18/10/2026 — Nguồn main đã đồng bộ 0.15.2; 0.15.3 đang kiểm

PR #4 đã merge vào main tại `f05c8a181c269d2075b6d822addb571f26b7bef6`; main chứa tag0.15.2 và lịch sử các nhánh trước. PR #5 nay nhắm main, chưa merge. Ứng viên0.15.3/lab9x0.2.11: `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`.

Bốn cổng đang kiểm: [2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858). Chưa có tag/image/digest0.15.3. Production vẫn0.15.2; cần workflow phát hành đạt và diễn tập bản sao hiện tại trước nâng VM. Đường SSH từ phiên này chưa khả dụng.

## 18/10/2026 — Chuẩn bị ứng viên production 0.15.3 theo yêu cầu chủ dự án

Đã đổi kh_aph0.15.3/lab9x0.2.11, giữ nền và21 cờ. Chưa gắn tag hoặc có image0.15.3; cần bốn cổng trên SHA đóng gói mới. Runbook tại `docs/phat-hanh-0.15.3.md`. Sau khi kiểm đạt: chủ dự án gắn tag theo AGENTS, workflow phát hành đạt rồi chạy diễn tập bản sao hiện tại và nâng cấp trên VM.

Production hiện vẫn0.15.2/digest đã xác nhận. SSH thử chỉ đọc từ máy hiện tại không phân giải được `erpnext-prod`; chưa truy cập hoặc thay đổi VM. Manifest giữ nguyên cho đến log triển khai thành công.

## 18/10/2026 — Bộ mẫu `7c2217e` đạt đủ bốn cổng, chưa phát hành

SHA đầy đủ `7c2217e8737e96700fa050aac446bb3591a830a8`. [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39101464777), [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463208), [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463191), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463224) đều đạt. Cục bộ 302+108 ca đạt. Đã đọc artifact: UAT 227 PASS/0 FAIL, b014 có 36 PASS, core 63.508 tệp nguyên vẹn. Đã xem PDF CI: hai liên đúng hai trang A5, tổng hợp tám đợt/bốn company hai trang A4, khối ký nguyên vẹn.

Cổng 3 so tổng/đếm/chi tiết khớp, schema/cờ khớp site mới, quay lui và ca lỗi tự quay lui khớp phiên bản/dữ liệu và giữ bảo trì. Nền CI không có phát sinh sổ, không thay diễn tập bản sao production có dữ liệu ngay trước triển khai. Bằng chứng chi tiết ở đầu `docs/ban-giao.md`.

**Chưa phát hành:** còn nghiệm thu máy in/nhân sự thật theo `docs/nghiem-thu-mau-in-20261018.md`, quy chế biểu mẫu chưa ban hành. Production giữ 0.15.2; chưa tăng version/tag/merge hoặc triển khai VM. Commit hồ sơ sau mã kiểm chỉ thay tài liệu.

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
