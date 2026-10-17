# Kế hoạch tiếp nối — Vận hành nhanh và kiểm soát tiền–hàng–công nợ

## Nguồn và phạm vi

Anh Tiến cung cấp lại lịch sử chat “Lỗi kết nối app Work” và ba đề xuất về bán hàng/bàn giao, nhà máy, tổng thể; sau đối chiếu đã yêu cầu tiếp tục và chấp thuận kế hoạch ngày 17/10/2026. Tài liệu này giữ mạch công việc để agent khác không cần hỏi lại. Không dùng yêu cầu NocoBase hoặc hệ thống 8082 làm baseline. Không xác nhận toàn bộ 202 quyết định; nguồn gốc đầy đủ 202 câu chưa có trong các tệp vừa nhận.

Baseline đã triển khai: kh_aph 0.15.2, nguồn24b795cc28f47ca2f31aef8edbbd8e5984c12ee3, ERPNext 16.51.1/Frappe 16.52.0/lab9x 0.2.10. Digest image `sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333`. Phát hành 39030251134 đạt; diễn tập VM 10171255a25ef6 khớp tổng/đếm/chi tiết và người vận hành báo triển khai ĐẠT. Cục bộ375 ca và UAT 215 PASS là bằng chứng cho phạm vi 0.15.2, không nghiệm thu cho các mục chưa viết bên dưới.

Giữ 4 Company APH/VH/MK/TL, TL=XB; MISA chỉ hóa đơn thuế; native ERPNext sở hữu chứng từ/sổ. Không làm lại cọc, thu hộ, giá vốn, sản xuất đã có. Mục tiêu mới là giảm thao tác, truy người thực giao và người thực giữ tiền, liên kết các nghiệp vụ có sẵn. Nhân viên kho/vận hành có thể ký giấy mà không có tài khoản phần mềm.

Quy tắc bắt buộc đọc từ `AGENTS.md`, `docs/quyet-dinh-nghiep-vu.md`, `docs/kien-truc-giao-dien.md`, quy trình khách và release. Không sửa core, tạo sổ trùng, DocType Nhiệm vụ có trạng thái riêng hoặc dùng UI ẩn giá thay kiểm quyền server. Workspace điều hướng, Dialog cho thao tác ngắn; Native Page chỉ khi đủ 6 tiêu chí đã chốt. Phần mở rộng giao nhận dùng cờ Trung tâm Bán hàng hiện có; cần đánh giá riêng cờ cho tính năng mới khác theo AGENTS, không tự coi 21 cờ hiện tại bao phủ mọi phạm vi tương lai.

## Thứ tự và trạng thái thật

| Đợt | Kết quả cần có | Mốc0.15.2 | Điều kiện đóng đợt |
|---|---|---|---|
| 1 — Bán hàng/giao nhận | Phiếu nhanh, người giao/nhận, thực giao và hồ sơ ký/chênh lệch | Có phiếu nháp nhanh + in, chống trùng, hồ sơ bản ký/đối chiếu; phần còn lại chưa đủ | Hoàn tất các mục GN dưới đây, test người dùng đại diện và giữ hồi quy |
| 2 — Tiền | Người giữ, chốt ca, bàn giao và ngoại lệ | Có thu/cọc/thu hộ và quỹ nhà máy; chưa có cơ chế chung toàn cửa hàng | Bao phủ mọi đường thu, đối chiếu quỹ, không tự nhận/không ghi nợ hai lần |
| 3 — Nhà máy | Nhập lượng một lần, nối chứng từ | Có nghiệp vụ nền; chưa có màn hình nhập ngắn thống nhất | Nhận/sản xuất/đóng gói/xuất hoạt động theo quyền, không lộ giá vốn |
| 4 — Tài chính | Đối chiếu đầy đủ, chốt tháng/báo cáo điều hành | Có nhiều công cụ riêng; chưa chứng minh toàn chuỗi | Đối chiếu dữ liệu đại diện và xác định tạm tính/hoàn tất |
| 5 — Hóa đơn một phần | Yêu cầu theo dòng/lượng/lần giao, hàng đợi MISA | Chưa chốt đặc tả riêng | Chốt nghiệp vụ trước code, không gộp vào bản vá giao nhận |

Thứ tự trên không cấm khảo sát điểm nối tiền trong đợt 1; không mở code chốt ca/nhà máy khi thiết kế phần nguồn chưa rõ. Không chờ danh mục/tồn kho thật mới phát triển; dùng site UAT và dữ liệu giả. Nghiệm thu người thật/máy in/số dư thật là bước riêng.

## Đợt 1 — bảng truy nguyên yêu cầu, code và việc còn thiếu

| Mã | Yêu cầu | Hiện có/bằng chứng code | Việc còn lại và ca kiểm bắt buộc |
|---|---|---|---|
| GN01 | Một cửa sổ lập phiếu & in | `ban_nhanh.preview/create_drafts/print_batch`, JS DocType đơn chung | Bảo toàn token khi lỗi; thêm dữ liệu giao nhận vào nội dung chống trùng, không cho cùng token thay địa chỉ/người nhận |
| GN02 | Đặt/đã xuất/nháp/còn lập, nhiều kho/company | `dispatch_plan.py`, `ban_nhanh._rows`, UAT b014 và scope | Giữ ca giao từng phần, không vượt lượng, nháp sửa/hủy được tính lại; lỗi nhóm sau không để phiếu dở |
| GN03 | Người nhận/lái xe, điện thoại, biển số, địa chỉ, cách giao theo từng đợt | Phiếu nhanh hiện có ô trống trên giấy; chưa có đầy đủ dữ liệu trong Dialog | Kiểm meta native trước chọn field; địa chỉ phải gắn đúng Customer và có quyền đọc; không nhận tùy ý field hệ thống/giá từ client |
| GN04 | Người xuất thực tế khác người nhập | `delivery_status` lưu User thao tác/thời gian, chưa thay được tên người ký thực giao | Trường người giao thực tế không bắt là User; kho nhập trước xác nhận; lưu riêng với actor/time của phần mềm |
| GN05 | Dự kiến, thực giao tại kho, thực nhận của khách | DN nháp/submit là nguồn lượng; có biên bản thực nhận trong luồng điều chỉnh | Không tạo sổ lượng thứ hai; xác định rõ mốc thay qty nháp và mốc dùng chứng từ điều chỉnh sau xuất; không nhầm nhận thiếu với lỗi nhập |
| GN06 | In2 liên, tên người lập, người giao/nhận, bản sao không xuất lại | `templates/ban_nhanh/phieu_dot_xuat.html`, bộ mẫu chuẩn và `trung_tam_ban` in lại | Kiểm từng đường in; phiếu nhanh hiện chưa đủ2 liên và thông tin theo đề xuất. Escape dữ liệu người/địa chỉ, không lộ giá qua bản in số lượng |
| GN07 | In không xuất kho/nợ; xác nhận thực giao mới ghi sổ | `delivery_status.confirm`, `delivery_receivable`, caHTTP b014 | Mọi đường mới đi cùng service; lặp handoff/pickup không ghiGL/SLE/SI lần hai; không cho người thiếu submit quyền xuất ngay |
| GN08 | Hồ sơ ký và dấu đối chiếu | `ho_so_giao_nhan.py`, `ban_014.js`, ca b014 hồ sơ | Giữ tệp riêng đúng phiếu, chặn xóa blob, thay tệp/ghi chú mất dấu, timestamp cũ bị chặn |
| GN09 | Chênh lệch cần xử lý có người phụ trách/kết quả | Hiện chỉ ghi chú chênh lệch và dấu đối chiếu | Thiết kế trên phiếu/chứng từ nguồn; không coi ghi chú là xử lý xong. Lưu người/thời gian và liên kết phiếu điều chỉnh, kiểm đúng Company/quyền |
| GN10 | Khách tự lấy/xuất ngay có quyền | Có `confirm(action=pickup)` nhưng chưa đủ thao tác gom trên cửa sổ nhanh | Không tự submit khi in; thiết kế lần gọi tạo+submit nguyên tử nếu bổ sung xuất ngay; kiểm quyền/lượng/tồn/duyệt lúc xuất, retry không ghi sổ hai lần |
| GN11 | Mất mạng/thao tác lặp/đồng thời | Có khóa đơn/SO, signature, request_id và ca hồi quy | Hiện mô phỏng gọi lại sau commit; chưa cắt mạng vật lý hoặc đo tải. Mỗi field mới tham gia signature phải tương thích request cũ |
| GN12 | Scope công ty/kho trên preview, tạo, thử lại, in | `ban_nhanh._note_scope`, ca b014Company/Warehouse | Giữ đối chứng dương và từ chối ngoài phạm vi; đổi quyền sau tạo vẫn không đọc/in được phiếu cũ ngoài quyền |

### Thiết kế cần giữ khi bổ sung thông tin giao nhận

- Thông tin dự kiến đi theo đợt giao; nguồn dữ liệu là Customer/Address/đơn và thông tin người vận chuyển. Không sửa danh mục địa chỉ của khách từ Dialog giao hàng.
- Kiểm meta chuẩn của nền16.51.1 trước quyết định dùng lại các trường Delivery Note. Chỉ thêm Custom Field thật sự thiếu; tênASCII và nhãn Việt. Cài schema qua bộ cài rõ ràng, không after_migrate.
- Chỉ nhận allowlist thông tin giao; kiểm độ dài/kiểu/cách giao. Địa chỉ phải đúng khách, có quyền đọc; server kiểm lại khi lưu, không chỉ dùng bộ lọcLink ở UI.
- Người nhận/lái xe và người giao thực tế có thể không dùng ERPNext. Actor xác nhận trên phần mềm vẫn phải là tài khoản có quyền, không dùng tên tự nhập để giả actor.
- Phiếu nháp được sửa trong quyền native, trước xác nhận kho kiểm lại lượng/thông tin. Phiếu đã xuất không được ghi đè lượng/địa chỉ làm mất lịch sử; đi đúng luồng sửa có kiểm soát đã có hoặc chứng từ điều chỉnh.
- Mỗi phiếu in phải chỉ rõ lượng dự kiến khi chờ xuất và số đã ghi nhận khi đã xuất. Các chữ ký không làm phát sinh quyền phần mềm.
- Tệp mới/ghi chú mới phải làm mất xác nhận cũ. Trạng thái hồ sơ và trạng thái giao hàng là hai khái niệm khác nhau, không tự chuyển Khách đã nhận chỉ vì tải ảnh.
- Chênh lệch được lưu và phân loại trước; xử lý kho/nợ bằng chứng từ chuẩn thích hợp. Người chỉ đọc không được mở/đóng vụ, người không có quyền công ty đích không được liên kết chứng từ của công ty đó.

### Bộ ca đóng đợt 1

1. Tạo đợt 5/20 kg từ nhiều kho/2 company, kiểm nháp và in không đổiGL/SLE/PLE/SI.
2. Gọi lại cùng token/cùng nội dung trả phiếu cũ; đổi lượng, người nhận, địa chỉ hoặc cách giao với token cũ bị chặn, không thêm phiếu.
3. Địa chỉ thuộc khách khác hoặc bị giới hạn quyền không được dùng; nhập ký tựHTML vào tên/ghi chú không biến thành mã trong bản in.
4. Kho sửa lượng nháp theo thực giao; đơn còn lại tính đúng. Xác nhận handoff/pickup và retry chỉ ghi kho/nợ một lần.
5. Bản ký không đúng phiếu/công khai bị chặn; thay tệp làm mất dấu; lưu bằng timestamp cũ bị chặn.
6. Ghi chênh lệch không tự ghi sổ; liên kết/hoàn tất xử lý đòi quyền và chứng từ đúng công ty, có lịch sử. Không đóng vụ chỉ vì đã đối chiếu tệp.
7. Người bán/kho/Dũng/kế toán trưởng được thử bằng tài khoản giả riêng, kể cả tổ hợpvai trò và scope; phản hồi native tạo/lưu, in, report/export không lộ giá vốn.
8. Bản in 2 liên đọc đủ; kiểm ảnh/PDF UAT riêng với kiểm giấy/máy in thật. Không ghi đã nghiệm thu máy in từ ảnhCI.
9. Schema chạy lặp không đổi dữ liệu nghiệp vụ; đủ 4 cổng trên đúng SHA trước đề nghị gắn tag. Khi đến VM, diễn tập bản sao dữ liệu hiện tại và sochi tiết trước nâng.

## Điểm nối đợt 2 — người giữ tiền và bàn giao

| Mã | Yêu cầu | Điểm nguồn hiện có / khoảng thiếu |
|---|---|---|
| T01 | Bao phủ mọi đường thu, kể cả cũ | Rà `ban_quay.thu_tien`, Payment Entry chuẩn, Funds Receipt/Action, Journal Entry và phiếu quỹ nhà máy. Người lập không mặc nhiên là người giữ; chưa có mapping toàn bộ |
| T02 | Thu thực và phân bổ tách nhau | Tái dùng `funds`, nativeJE/PE/PLE; không FIFO, không giả bank TL, không đổi chủ hàng vì công ty nhận tiền |
| T03 | Chốt ca/phải có/thực đếm | Chưa có luồng chung; cần xác định ranh giới quỹ/ca/người, khoản chuyển ca và không tự ép lệch về0 |
| T04 | Bàn giao không thu khách lần hai | Có nền `factory_cash.xac_nhan_nhan`; cần luồngchung và khoản tiền nguồn, không ghi lại doanh thu/131 |
| T05 | Không tự nhận, kể cả cộngquyền | Codehiện chưa chặn rõ người lập tự nhận; thiết kế guard dựa đúng người thực giao/người thực nhận, không chỉdựa owner hoặc tên role |
| T06 | Thiếu/thừa, nộpbank, giữquáhạn | Chưa có vòng xử lý đầyđủ; giữ tiền thực riêng với chênh lệch/điều tra, không sửa phiếuthu cho khớp |
| T07 | Ngân hàng/sao kê/ngoại lệ | Có quyềnFile/Bank, mãgiaodịch chung và đối soát; chưa có bảngchốt ngày người phụtrách/hạn xử lý thống nhất |

Không tự gán người giữ cho khoản lịch sử chưa rõ; phảihiện chưa xácminh. Phải kiểm phiên đồngthời/khóa ghi, số tiền hữu hạn, tối đa2 sốlẻ và quyềnCompany trước mọi ghi sổ.

## Đợt 3 — nhà máy

- NM01 nhận hàng: tách lượng khỏi giá; dùng nhận chuẩn/chờđịnh giá/giá tạm đã có; bổ sung cửa sổ ngắn, hàng không đạt và phiếu cân.
- NM02 sản xuất mộtlần: đầu vào/đầu ra/phụ phẩm/dở dang/chênh lệch. Không ép nguyên liệu chưa dùng hoặc hàngđang chuyển công đoạn thành hao hụt.
- NM03 dở dang/bồn: vào–ra–còn, cho công việc tiếp tục qua ngày. Vétbồn/quyết toán chỉ khi thực sự kết thúc và theo quyền kế toán.
- NM04 đóng gói/đổi bao: giữ2 nghiệp vụ, kiểm cânđối kg/bao/bì. Không sửa kg/bao để che chênh lệch.
- NM05 xuất/chuyển: phân biệt bán/cùng Company/khác Company; phiếu ký trên DN hiện không tự bao phủ Stock Entry/chuyểnkho.
- NM06 quỹ/chốt ngày: tái dùng sổ tiền, hiển thị tiền phải còn/thực đếm/bàn giao và việc treo; không nhập lại Excel.
- NM07 quyền Dũng: bảo vệ cảAPI, phản hồiinsert/save, report, export, print và tổ hợp role; không chỉ ẩnôUI. Quyền0.15.2 có hồi quy nhưng chưa nghiệmthu tài khoảnnhân sự thật.

## Đợt 4–5

TC01 đầu kỳ; TC02 mua–nhận–hóa đơn–ứngtrước–trả NCC; TC03 chi phí chưa trả/đến muộn/trả trước; TC04 giá thành/dở dang/repost; TC05 tài sản/CCDC/khấuhao; TC06 vay/lãi/vốn; TC07 thu hộ/nội bộ; TC08 báo cáo điều hành/tạm tính/chất lượng dữ liệu. Mỗi mục phải kiểm lại code và ca đã có, không kết luận chưa có chỉ vì thiếu màn tổng hợp.

HD01 hóa đơn một phần: yêu cầu từng dòng/lượng, gắn lần giao, hàngđợi xử lý, MISA điều chỉnh/thaythế/hủy. Chờ chốt đặc tả riêng; không tự triển khai từ đề xuất này.

## Mẫu hồ sơ 9 nhóm áp dụng cho từng đợt

1. Mục tiêu/phạm vi và ngoài phạm vi.
2. Hiện trạng đúng phiên bản/SHA, code và bằng chứng.
3. Quy trình: ai làm, ai chịu trách nhiệm, người làm thật và người nhập thay.
4. Quy tắc/ngoại lệ và nguyên tắc ghi sổ.
5. Dữ liệu: field/source, trạng thái, điều kiện chuyển và snapshot/lịch sử.
6. Quyền: hành động/field/Company/Warehouse và bằng chứng đối chứng dương/âm.
7. Tác động: kho/nợ/tiền/giá vốn/sản xuất/MISA; không tạo sổ trùng.
8. Nghiệm thu: input, actor, thao tác, số kỳ vọng, truy vấn đối chiếu và artifact.
9. Triển khai/khôi phục: schema/cờ, CI đúng SHA, diễn tập tách biệt, ghi rõ chưa kiểm/đã kiểm.

## Điểm dừng hiện tại

Đã triển khai lát 1A trên nhánh `feat/thong-tin-giao-nhan-20261017`, PR #5: GN01 bổ sung thông tin vào token chống trùng; GN03 thông tin nhận hàng/địa chỉ theo đợt; GN04 người thực giao và dấu xác nhận do server ghi; GN06 bản in nhanh hai liên. Có đặc tả 9 nhóm tại `docs/dac-ta-giao-nhan-dot-1.md`. Kết quả CI và SHA được cập nhật ở đầu `docs/ban-giao.md` và `deploy/release/TRANG_THAI.md`; production vẫn 0.15.2.

Đợt 1 chưa đóng: GN09 còn vòng người phụ trách/kết quả/chứng từ xử lý chênh lệch; GN10 chưa có xuất ngay trong Dialog; GN06 cần đối chiếu các đường in còn lại và máy in thật; GN11 chưa mô phỏng cắt kết nối trình duyệt ở thời điểm server commit. Tiếp theo thiết kế GN09 trên phiếu nguồn, phân biệt ghi chú/đối chiếu hồ sơ với hoàn tất xử lý; tái dùng chứng từ điều chỉnh đúng bản chất, không tạo trả kho giả cho mất hàng hoặc lỗi nhập liệu. Giữ các đợt tiền/nhà máy/tài chính và hóa đơn một phần ở phạm vi riêng đã ghi trên.
