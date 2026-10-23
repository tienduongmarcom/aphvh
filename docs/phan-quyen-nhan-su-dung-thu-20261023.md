# Nhân sự dùng thử và chuẩn bị phân quyền — 23/10/2026

Chủ dự án yêu cầu chuẩn bị cho dùng thử ngày24/10 và phân quyền tối23/10. Danh sách/vị trí dưới đây do chủ dự án cung cấp. Hồ sơ quyền dưới đây đã được viết trong bộ chuẩn bị, chưa áp lên production; đã chốt dùng mã đăng nhập nội bộ; chưa áp tài khoản/quyền lên production. Không lấy tài khoản Administrator hoặc bộ vai trò rộng của fixture UAT gán cho nhân viên.

## Chính sách tháng đầu đã chốt

Chủ dự án đồng ý linh hoạt trong tháng đầu rồi thu hẹp theo vận hành: quyền rộng trong công việc, không chia quá nhỏ ngay. Hường/Hạnh được theo dõi và thu hồi nợ; Hạnh thêm kho ngoài nhà máy. Dung xử lý kế toán/mua trong nước; Lan/Hà cùng tổng hợp/thuế trước khi chia rõ. Trang duyệt bán hàng; Ninh xem điều hành/giá vốn/lợi nhuận; Ninh/Trang/Ánh nhận tiền cuối ngày. Dũng giữ phạm vi nhà máy/ẩn giá vốn. Tâm để sau theo chỉ đạo riêng, không coi là thiếu tính năng đợt này.

Giữ tài khoản riêng, nhật ký, cấm tự nhận tiền mình bàn giao, chống ghi trùng, phạm vi kho và đường sửa/hủy chứng từ đã ghi. Không cấp System Manager để chữa thao tác bị chặn. Tuần đầu ghi điểm vướng; cuối tháng rà lại quyền theo nhiệm vụ thực tế. Không có job tự siết quyền hoặc tự thay dữ liệu. Các quyền xem/nhận/duyệt hẹp bên dưới là cách tránh cấp quyền quản trị, không bổ sung cấp duyệt vào giao dịch thông thường.

## 1. Danh sách và trách nhiệm

| Nhân sự | Vị trí đã xác nhận | Phạm vi thao tác đề xuất để đối chiếu | Kiểm soát cần giữ |
| --- | --- | --- | --- |
| Cô Hường | Kế toán bán hàng | Đơn bán, chuẩn bị/in xuất, thu tại quầy theo nơi thực nhận; tiền cá nhân và theo dõi/thu hồi công nợ khách | Không tự tăng quyền giao kho, hủy sổ, duyệt ngoại lệ hoặc xem giá vốn |
| Cô Hạnh | Kế toán bán hàng kiêm thủ kho | Như bán hàng và thu hồi công nợ; thêm xác nhận xuất/nhận tại các kho ngoài nhà máy và hồ sơ ký | Kiêm nhiệm được, nhưng không tự xác nhận nhận tiền bàn giao từ mình; chỉ kho ngoài nhà máy, phải lập danh sách Warehouse thực tế |
| Dung | Kế toán trưởng, nhập hàng trong nước | Mua trong nước, kiểm kế toán, duyệt ngoại lệ theo phân công, xử lý lệch/chốt số | Không mặc định System Manager; giữ lịch sử duyệt/sửa/hủy và kỳ khóa |
| Lan | Kế toán tổng hợp và kế toán thuế | Nghiệp vụ tổng hợp/thuế theo phân công; không mặc định nhận tiền cuối ngày hoặc làm đầu mối thu hồi nợ | Tiền cuối ngày giao cho chủ; Hường/Hạnh theo dõi thu hồi nợ. Phần ngân hàng còn chờ phân công |
| Hà | Kế toán tổng hợp và kế toán thuế | Như Lan, tách người thực hiện và người kiểm tra theo phân công tổng hợp/thuế | Quyền mua/chi/tài sản chưa suy từ tên chức danh |
| Trang | Giám đốc bán hàng | Chủ, giám đốc bán hàng; duyệt dưới sàn/vượt hạn mức và nhận tiền cuối ngày | Quyền xem giá vốn/lợi nhuận không tự suy từ chức danh |
| Tâm | Nhập hàng quốc tế | Chỉ đặt hàng phòng nhập khẩu; chưa triển khai quyền của Tâm trong đợt dùng thử này | Không mở rộng sang nhận kho, chi tiền, sửa giá vốn hoặc mua trong nước |
| Ninh | CEO | Báo cáo điều hành, xem giá vốn/lợi nhuận đã được chủ dự án cho phép; được nhận tiền cuối ngày cùng Trang/Ánh | Không cấp quyền sửa sổ/đổi quyền chỉ để xem báo cáo |
| Ánh | Người được chỉ định nhận tiền cuối ngày | Nhận đúng bàn giao được gửi cho tài khoản mình, nhập số thực nhận | Không suy quyền quản trị/kế toán hoặc xem toàn sổ từ quyền nhận tiền |
| Dũng | Kế toán nhà máy | Nhận/chuyển hàng, sản xuất, đóng gói, tiền cá nhân/quỹ nhà máy theo phân công đã có | Giữ hồ sơ không xem giá vốn; không cộng quyền kế toán quản lý để vượt chặn; chỉ các kho nhà máy; quỹ cụ thể phải đối chiếu cấu hình |

Dung và Dũng là hai người khác nhau. Chỉ ánh xạ bằng tên đăng nhập đã đối chiếu, không tìm gần đúng theo tên hoặc bỏ dấu.

## 2. Việc cần biết trước khi áp quyền

- Đã chốt dùng mã đăng nhập nội bộ, không gửi thư tự động. Tâm để sau; chuẩn bị9tài khoản đợt này, bảng bên dưới. Không cần cung cấp mật khẩu trong chat.
- Đã chốt: tiền cuối ngày giao cho chủ, công nợ Hường/Hạnh theo dõi thu hồi. Đã chốt người nhận tiền cuối ngày: Ninh, Trang, Ánh; Trang/Ninh là chủ. Mỗi lượt chọn một người thực nhận, không tự động chia hoặc gán cả ba. Phần ngân hàng/tổng hợp/thuế Lan/Hà chưa chia chi tiết.
- Đã chốt Hạnh các kho trừ nhà máy, Dũng các kho nhà máy: cần đối chiếu danh sách Warehouse thực tế và thuộc tính loại/địa điểm, không suy bằng chuỗi tên. Tâm để sau. Bán hàng nhiều đơn vị phải giữ đường chọn nguồn chung.
- Trang được duyệt dưới sàn/vượt hạn mức; Ninh được xem giá vốn/lợi nhuận. Chưa suy quyền xem giá vốn cho Trang hoặc quyền sửa sổ cho Ninh từ quyết định này.
- Nếu có quyền/Share/User Permission cũ, kiểm cả quyền hiện có trước khi cộng vai trò mới.

## 3. Ràng buộc từ code hiện tại

- ban_quay.QUYEN_KTBH cấp quyền ghi/submit Payment Entry và Sales Order, đọc/in DN/SI; không tự chứng minh có quyền xác nhận xuất. Hành vi thực tế còn phụ thuộc các vai trò và User Permission khác.
- Bộ áp người dùng ux_task.ap_dung_nguoi_dung hiện chỉ đổi Workspace/Module Profile và thêm giới hạn Warehouse. Nó KHÔNG phải bộ gán đủ quyền nghiệp vụ; mặc định chay_that=0 để xem thay đổi.
- Module Profile chỉ ẩn menu, không bảo vệ dữ liệu. Phải kiểm API, danh sách, in/báo cáo/tệp theo tài khoản thật trên môi trường thử.
- Báo cáo quản trị quan_tri.can_quyen hiện yêu cầu Accounts Manager/System Manager. Nhu cầu CEO chỉ xem cần đường quyền đọc riêng đã kiểm; không cấp vai trò quản lý kế toán chỉ để mở báo cáo.
- Tiền cá nhân có facade riêng, không cần mở toàn GL. Nhận bàn giao kiểm đúng người; cấm tự nhận vẫn giữ kể cả cộng vai trò quản lý.
- Không bỏ28cờ trong bản chuẩn bị dùng thử này; không cài lại site hay thử chứng từ giả trên production.

### Quyền hẹp đã triển khai, cần kiểm đúng nguồn phát hành

- CEO có vai trò đọc riêng cho lãi gộp và dòng tiền; không cấp Accounts Manager, quyền sửa sổ hoặc khóa kỳ.
- Ninh/Trang/Ánh chỉ nhận bàn giao được chỉ định cho mình. Kế toán bán hàng gửi tiền từ số đang giữ; dùng bút toán native của đúng lượt, không cấp đọc/ghi toàn GL/JE. Cấm tự nhận và kiểm gửi lại giữ nguyên.
- Trang có vai trò duyệt khách rủi ro và được chuẩn bị vào bảng người duyệt giá sàn theo từng Company, không tự duyệt. Hạn mức chung vẫn là cảnh báo hiện hành; không mô tả thành cơ chế chặn mới.
- Hạnh có công nợ tài chính tổng hợp toàn khách nhưng không kéo theo bản in phiếu nguồn ở kho ngoài phạm vi. Hồ sơ cũ kèm phiếu nguồn vẫn bị chặn.

Đã tải và đọc UAT39929582119 đúng `ae49241`:143ca014 PASS, tất cả hồi quy PASS. Có chuẩn bị9User disabled/retry/không email, Module Profile, đăng nhập bằng mã nội bộ và chuyển hai chiều bằng hồ sơ Hạnh/Dũng chỉ trong UAT. Cổng239929658679 và2b39929662938 cùng nguồn SUCCESS; cổng339929667314 cũng SUCCESS, schema1189/1189 và rollback1105/1105 lệch0, phục hồi nâng sai KHỚP. Mục đầu hai hồ sơ bàn giao ghi kết quả sau cùng. Chưa phát hành hoặc áp người thật.

## 4. Bộ dùng thử ngắn theo nhân sự

Chạy giao dịch giả trên site thử, hoặc chỉ giao dịch thật hợp lệ trên production sau khi đủ điều kiện phát hành. Không nhập tồn/công nợ giả vào production để vượt chặn.

| Người/nhóm | Thao tác cần kiểm | Kết quả cần thấy |
| --- | --- | --- |
| Hường | Chọn khách trùng tên, chọn mã hàng, lập/in phiếu và thu quầy | Có địa chỉ/SĐT/tên hàng đúng; in chưa ghi kho/nợ; thu đúng đơn vị/người giữ, không trùng khi bấm lại |
| Hạnh | Thực giao tại kho ngoài nhà máy, hồ sơ ký; thử kho nhà máy | Đúng lượng thực giao; ảnh/giấy bổ sung sau; nguồn ngoài quyền bị chặn; không tự nhận tiền của mình |
| Dung | Giảm giá đơn cũ theo5kg trong25kg; xử lý ngoại lệ |20kg giữ giá; khoản giảm có căn cứ, quyền đúng, không ghi giảm hai lần |
| Ninh/Trang/Ánh nhận tiền; Lan/Hà kiểm theo phân công | Chủ nhận bàn giao cuối ngày; tổng hợp/thuế đối chiếu nguồn | Đúng người nhận đã chốt; phân biệt tăng/giảm từng đơn vị, cọc/chưa phân bổ; không tạo thu lần hai |
| Trang | Duyệt dưới sàn/vượt hạn mức có lý do; xem đơn/báo cáo | Chỉ người được giao quyền duyệt, lưu lý do/dấu duyệt; không suy thêm quyền sửa sổ |
| Tâm | Để sau đợt này theo chủ dự án | Chưa cấu hình/đánh dấu đã nghiệm thu nhập quốc tế |
| Ninh | Mở báo cáo điều hành có giá vốn/lợi nhuận; thử sửa chứng từ | Được xem giá vốn/lợi nhuận; không suy quyền sửa/ghi/hủy từ quyền xem |
| Dũng | Nhận hàng, nhập sản xuất, chuyển kho và tiền cá nhân | Lượng đúng, nhà máy độc lập cửa hàng; không lộ giá vốn/GL hoặc quỹ ngoài phạm vi qua API/in/báo cáo |

Đầu vào tối thiểu: mã hàng/quy cách, tồn tại kho thử, khách và nguồn thu/quỹ đã xác minh. Khi thiếu dữ liệu thật, vẫn kiểm được quyền/màn hình trên dữ liệu giả; không lấy kết quả đó thay nghiệm thu số liệu thật.

## 5. Trạng thái

Chưa áp quyền lên production; production vẫn0.16.4. PR38 chứa giao nhận/nhận trả và chuẩn bị phân quyền. Đã đọc native143ca014 trên `ae49241`, cài mới/diễn tập triển khai cùng nguồn đạt; diễn tập nâng cấp từ production cùng nguồn cũng đã đạt. Không lấy PASS của nguồn trước thay cho nguồn cuối. Nghiệm thu với nhân sự, hàng/tồn thật và máy in thật để cuối theo chủ dự án. Phần thu/hoàn đổi mã trong một cửa sổ còn mở, không gọi toàn kế hoạch đã hoàn tất. Trạng thái tiếp nối ở `docs/ban-giao.md` và `deploy/release/TRANG_THAI.md`.


## 6. Mã đăng nhập nội bộ đã chuẩn bị

Chủ dự án chọn mã nội bộ ngày23/10. Đã đối chiếu màn User trên production (bỏ bộ lọc danh sách): chỉ có Administrator và Guest, chưa có nhân sự. Không coi quan sát này thay việc kiểm trùng ngay trước tạo.

| Mã đăng nhập | Người | Ghi chú |
| --- | --- | --- |
| huong | Cô Hường | Bán hàng, theo dõi thu hồi nợ |
| hanh | Cô Hạnh | Bán hàng và kho ngoài nhà máy |
| dungktt | Dung | Kế toán trưởng, mua trong nước |
| lan | Lan | Tổng hợp, thuế |
| ha | Hà | Tổng hợp, thuế |
| trang | Trang | Duyệt bán hàng, nhận tiền |
| ninh | Ninh | Xem điều hành/giá vốn/lợi nhuận, nhận tiền |
| anh | Ánh | Nhận tiền |
| dungnm | Dũng | Nhà máy, không xem giá vốn |

`kh_aph.staff_accounts.xem_ke_hoach` là công cụ chỉ đọc cho quản trị, sau cờ UX hiện có; kiểm trùng username hoặc định danh User, không tìm theo họ tên, không tự nhận tài khoản trùng. Trường email kỹ thuật dự kiến `<mã>@nhansu.invalid` chỉ phục vụ trường bắt buộc của User, không phải hộp thư. Không gửi welcome email, không đặt mật khẩu chung, không ghi mật khẩu/reset link vào repo. `xem_ke_hoach` không ghi; `chuan_bi` là bước ghi tường minh, chỉ tạo User disabled và hồ sơ quyền, không kích hoạt hoặc đặt mật khẩu. Người dùng đăng nhập bằng username sau khi tài khoản được tạo/kích hoạt và thiết lập mật khẩu đúng quy trình.

Đã kiểm native phạm vi Hạnh trên5bed91b: biên bản tài chính tổng hợp dùng được; phiếu nguồn ngoài kho, packet cũ và tệp tương ứng vẫn bị chặn.


### Tiến độ quyền duyệt khách rủi ro

Đã viết vai trò Duyệt khách rủi ro và bộ cài tường minh: approve/revoke dùng quyền này, sửa hạn mức/dấu rủi ro Customer vẫn yêu cầu quản lý kế toán. NoCost luôn chặn khi cộng vai trò. Đã kiểm native vai trò duyệt trong bộ dispatch48; chưa gán Trang trên production. Quyền giá dưới sàn vẫn dùng bảng người duyệt hiện có. Hạn mức chung trong global_credit hiện là cảnh báo, không mô tả thành cơ chế chặn/duyệt vượt hạn mức đã hoàn thiện.


### Tiến độ quyền điều hành và nhận tiền

Đã viết vai trò Xem báo cáo điều hành và Nhận bàn giao tiền, chưa cấp vào nhân sự thật. CEO mở riêng hai báo cáo, không kèm khóa kỳ/sửa sổ; người nhận chỉ thấy bàn giao được chỉ định, không mở GL/JE. KTBH gửi/nhận bằng số tiền cá nhân và dịch vụ bàn giao chuẩn, tránh cấp Accounts User để chữa lỗi. Đã kiểm native trên5bed91b; chưa áp tài khoản thật. Vai trò nhận tiền không mặc định có quyền hoàn/gửi tiền mới; khi cần nghiệp vụ ngoài phạm vi phải giao đúng người thực hiện, không dùng quyền quản trị thay.


### Phạm vi công nợ khi Hạnh bị giới hạn kho

Đã viết quyền đánh dấu Đối soát công nợ toàn khách: chỉ bản tài chính summary_only, không kéo theo bản in phiếu nguồn. Hồ sơ kho chỉ thấy/tải các bản summary này; packet cũ có phiếu nguồn vẫn bị chặn cả API/list/file. Warehouse User Permission phải áp riêng vào chứng từ kho/bán/mua đã liệt kê; không nới hạn chế tài khoản/bộ phận/Company. Phiếu hàng/thu in riêng theo quyền native. Đã kiểm native trên5bed91b, chưa áp người thật; danh sách kho thực tế vẫn cần đối chiếu trước áp.


## 7. Chuẩn bị và kích hoạt sau kiểm thử

`staff_accounts.chuan_bi(duong_dan)` chỉ xem kế hoạch. Tham số `chay_that=1` và `xac_nhan_site` chính xác mới tạo tài khoản disabled theo hồ sơ, không mật khẩu/email, không thay tài khoản ngoài lượt. Bộ này chưa được chạy trên production. Phải đọc native trên mã có bộ chuẩn bị trước áp thật; toàn bộ quyền/Workspace/Company/kho phải đủ và không còn kho chưa phân loại.

Sau khi bộ kiểm đạt và nâng cấp đúng nguồn: quản trị đối chiếu kế hoạch, chuẩn bị9tài khoản, đặt mật khẩu riêng bằng màn User, bật đăng nhập bằng username trong System Settings và kích hoạt từng người đã được kiểm. Không gửi mật khẩu/reset link qua chat hoặc commit vào repo. Không bật tài khoản khi còn thiếu kiểm quyền/phạm vi. Cấu hình Trang trong bảng người duyệt giá sàn theo Company, giữ tự duyệt tắt; phê duyệt khách rủi ro dùng vai trò riêng. Không tự thay cơ chế cảnh báo hạn mức chung thành chặn mới.

Hạnh được các kho cửa hàng/vệ tinh, Dũng các kho nhà máy theo cây địa điểm; transit dùng chung cần cho giao nhận nhưng không mở thêm kho đích ngoài quyền. Công nợ Hạnh dùng biên bản tài chính tổng hợp; các phiếu hàng/thu in riêng trong phạm vi quyền. Kho mới trong nhóm địa điểm đã giao đi theo quyền hậu duệ; kho ngoài địa điểm cấu hình khiến bộ chuẩn bị dừng để đối chiếu.


### Bổ sung phạm vi nhóm địa điểm và giá sàn

Quyền kho dùng nhóm địa điểm đúng cấu hình, có hậu duệ, thay vì danh sách lá cố định. Kho cách ly/chờ xử lý mới sinh trong cửa hàng vẫn dùng được; không mở quyền sang nhóm nhà máy. Thay cây kho làm mới cache ngay và sau commit để không giữ phạm vi cũ. Kho ngoài địa điểm chưa xác định phải đối chiếu trước áp.

Bộ chuẩn bị đã bao gồm allowlist Trang duyệt giá sàn từng Company, tự duyệt tắt; không ghi đè cấu hình khác nếu đã có. Tài khoản vẫn disabled và chưa có mật khẩu dùng chung, không email. Sau native đạt, quản trị đặt mật khẩu riêng, bật đăng nhập bằng username, rồi kích hoạt theo hồ sơ. Cần kiểm trực tiếp bằng nhân sự thật trước đánh dấu nghiệm thu vận hành.


### Chuyển nhà máy và cửa hàng

Tên kho nhận dự kiến là metadata cùng đơn vị, không phải quyền thao tác tại kho đó. Người gửi xuất từ kho mình vào transit; người nhận dùng cửa sổ nhận chuyến để xem lượng đúng chuyến chỉ định đến kho mình. Không cấp đọc phiếu nguồn/Warehouse nguồn hoặc giá ngoài phạm vi; phiếu nhận native chỉ đi từ transit vào kho được giao. Chuyến lịch sử thiếu kho dự kiến cần kế toán đủ phạm vi xử lý trước khi áp hồ sơ hẹp, không mở toàn kho để chữa. Đã đọc143ca native trênae49241: chuyển nhà máy→cửa hàng và ngược lại bằng hai hồ sơ Hạnh/Dũng đạt, sai kho bị chặn, retry chỉ một phiếu nhận, không sinh công nợ; vẫn chặn đọc Warehouse/phiếu nguồn ngoài phạm vi. Đây là bản sao tài khoản trên site UAT, không phải nhân sự thật đã nghiệm thu.
