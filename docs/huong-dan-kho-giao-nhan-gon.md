# Hướng dẫn luồng kho – giao nhận gọn

Bản đang phát triển trong PR38, chưa phải hướng dẫn cho production0.16.4. Các phần mới chỉ bật dùng sau khi hoàn tất kiểm thử và phát hành. Giấy tay chỉ dùng làm chứng từ gốc để nhập bổ sung khi mất mạng; không có màn hình hay sổ offline riêng.

## Ai làm

- Một đầu mối cửa hàng thao tác phần mềm, lập phiếu và hoàn thiện hồ sơ. Người này có thể đồng thời giao hàng theo phân công thực tế.
- Người kho giao/nhận đúng hàng, ghi lượng thực tế và lấy chữ ký; tại kho vệ tinh không cần tài khoản phần mềm.
- Khách hoặc người được khách cử ký nhận hàng. Quyền nhận hàng không bao gồm quyền ký công nợ; ký nợ phải có khách xác nhận ủy quyền riêng.
- Kế toán cửa hàng giữ giấy gốc tập trung. Kho vệ tinh chuyển giấy về; ảnh và giấy gốc có thể cập nhật sau khi xe đi.

## 1. Khách hoặc xe khách đến lấy

1. Lập đơn bán chung; kiểm đúng mã khách, địa chỉ, điện thoại và tên hàng bên cạnh mã hàng.
2. Chọn đúng kho thực xuất, kg và số bao. Chọn Khách đến lấy hoặc Xe khách đến lấy; với xe khách, ghi căn cứ khách chỉ định người nhận.
3. Chuẩn bị phiếu xuất và in. Bản nháp/in không ghi kho hoặc công nợ.
4. Kho kiểm hàng lên xe, ghi lượng thực giao, người giao/nhận và ký trên giấy.
5. Đầu mối kiểm lại phiếu và xác nhận giao theo thực tế. Đây là bước xuất kho và ghi nợ; ký nhận hàng không tự ghi thu tiền.
6. Bổ sung tệp ký, đối chiếu và nhận giấy gốc khi giấy về kế toán. Thay tệp giữ bản cũ và dấu đối chiếu trước đó trong Lịch sử bản ký.

Khi mạng hoặc hệ thống chặn, xử lý như mục6; không buộc khách chờ nhập xong hồ sơ mới cho xe rời.

## 2. Gửi nhà xe

1. Chọn Vận chuyển, người nhận tại kho và nhà xe. Nhà xe quen lấy lại thông tin đã có; nhà xe mới nhập tên/điện thoại tại lượt giao.
2. Luôn in phiếu xuất kho, kể cả hàng gửi ship. Kho và người nhận hàng cho nhà xe ký khi bàn giao.
3. Xác nhận xuất theo lượng thực giao; hàng chuyển sang Đang giao.
4. Khi khách hoặc nhà xe báo đã nhận, ghi nguồn báo và ngày nhận thực tế. Thao tác chỉ đánh dấu nhận, không xuất kho hoặc ghi nợ lần nữa.
5. Mặc định không yêu cầu bản khách ký tại đích. Nếu khách có yêu cầu, chọn Có lúc chuẩn bị giao: in thêm bản giao nhận để ký tại đích, theo mục3.

## 3. Khách yêu cầu bản ký tại đích

Bản giao cho nhà xe và bản khách ký tại đích lưu riêng trên cùng phiếu xuất.

- Tệp nhà xe ký: Bản phiếu đã ký và thao tác Đối chiếu bản ký.
- Tệp khách ký: Bản khách ký tại đích và thao tác Nhận hồ sơ khách ký.
- Có thể nhận giấy gốc khách ký trước, ghi vị trí tập lưu, rồi bổ sung ảnh sau. Nếu phiếu còn Đang giao, cùng thao tác nhận hồ sơ ghi ngày khách nhận bằng dấu giao nhận hiện có.
- Chốt ngày vẫn hiện phần thiếu ảnh hoặc thiếu giấy gốc. Nhận gốc không được hiểu là ảnh đã được bổ sung.
- Chỉ có phần này trên chuyến vận chuyển đã chọn yêu cầu khách ký; khách tự lấy hoặc chuyến không yêu cầu không làm thêm bước.

## 4. Giao trực tiếp ở kho vệ tinh

Đơn/phiếu chọn đúng kho vệ tinh và đơn vị sở hữu. Đầu mối cửa hàng chuẩn bị phiếu, chuyển bản in cho kho, nhận lại lượng thực giao và thông tin người nhận để xác nhận trên phần mềm. Người kho chỉ làm hàng và giấy, không cần tài khoản. Giấy gốc chuyển về kế toán cửa hàng; không ghi xuất thêm lần nữa khi giấy về.

## 5. Gom kho vệ tinh về cửa hàng rồi giao khách

Bản đang phát triển có nút **Gom hàng cho đơn** trên đơn chung đã xác nhận. Chọn nhóm đơn vị/kho nếu đơn có nhiều nơi giao; cửa sổ chuyển điền sẵn mã/tên/lượng còn chưa lập phiếu xuất và ghi số đơn trong ghi chú. Chọn kho thực lấy, kiểm lượng thực cần chuyển và người/xe, rồi Chuẩn bị phiếu & In. Lượng gợi ý chưa trừ tồn đã có hay các chuyến gom khác, không giữ chỗ. Muốn giao khách ở cửa hàng thì nguồn phần chưa giao trên đơn phải là kho cửa hàng trước. Nút này chưa có kết quả native lúc viết; vẫn dùng được đường chuyển kho chuẩn bên dưới theo bằng chứng cũ.


1. Nếu đã biết sẽ giao tại cửa hàng, dòng đơn bán chọn kho cửa hàng thuộc đúng đơn vị sở hữu. Việc chuyển nội bộ bổ sung hàng cho kho đó, chưa thực hiện giao khách.
2. Mở Tồn kho số lượng, chọn đơn vị → Chuyển hàng đi. Chọn kho nhận dự kiến là cửa hàng, các kho nguồn vệ tinh, hàng/kg/bao và người/xe chở.
3. Chuẩn bị phiếu & In tạo phiếu kho nháp. Người chở/ghi chú, lượng thực giao còn sửa được khi nháp; đơn vị và loại chuyến không đổi sang nghiệp vụ khác.
4. Khi thực giao từ vệ tinh, kiểm lại và xác nhận phiếu chuyển: hàng vào kho đang vận chuyển. Bấm lại cửa sổ cũ mở phiếu đã có.
5. Tại cửa hàng, Nhận chuyến về kho theo lượng thực nhận. Có thể nhận từng phần; phần chưa nhận còn trên đường. Nhận khác kho dự kiến phải ghi lý do và có quyền tại kho thực nhận.
6. Giao khách bằng phiếu xuất từ kho cửa hàng. Không bán trực tiếp từ kho đang vận chuyển.

Nếu đơn đã chọn kho vệ tinh nhưng sau đó đổi sang nhận ở cửa hàng, dùng luồng Đổi nguồn phần chưa giao hiện có trước khi lập lại phiếu giao; không tự sửa phiếu đã ghi. Chuyển giữa hai đơn vị sở hữu khác nhau đi theo luồng mua/bán nội bộ, không dùng phiếu chuyển cùng đơn vị này.

## 6. Mất mạng, dùng giấy tay rồi nhập bổ sung

Người phụ trách được giao quyền quyết định việc giao/thu thực tế. Lập giấy có số quyển/tờ, thời điểm, khách, hàng/kg/bao, kho, người giao/nhận và khoản tiền thực nhận nếu có; lưu chữ ký và giấy gốc.

Khi có mạng:

1. Kiểm tra trước xem nghiệp vụ đã được nhập hoặc gửi thành công chưa, nhất là lúc mất phản hồi.
2. Nhập phiếu chuẩn phù hợp: phiếu xuất, phiếu chuyển/nhập kho hoặc phiếu thu chi; không tạo thêm nghiệp vụ trong một sổ offline.
3. Điền phần giấy tay: số giấy theo điểm/quyển/tờ, thời điểm thực tế và nơi giữ giấy gốc; đính tệp riêng tư khi có.
4. Kiểm lượng/giá/quỹ và xác nhận bằng quyền hiện có. Ngày thực tế trên giấy tách với ngày hạch toán; các kiểm tồn, giá, hạn mức và kỳ khóa vẫn áp dụng.
5. Nếu phiếu đã ghi đúng nhưng thiếu giấy, bổ sung hồ sơ ngay trên phiếu đó, không lập phiếu xuất/thu lần nữa. Phiếu hủy giữ giấy, nhập lại bằng Sửa đổi để giữ nguồn.

Nếu vướng thiếu tồn hoặc kỳ khóa khi nhập sau, giữ giấy và phiếu nháp để người có thẩm quyền đối chiếu nguồn dữ liệu, không nhập số tồn giả để vượt chặn.

## 7. Thu tiền, đối soát và lưu giấy

Tiền thực nhận ghi đúng đơn vị/quỹ hoặc ngân hàng, người giữ và khoản phân bổ. In phiếu thu cho người nộp ký; ký nhận hàng không thay phiếu thu.

Từ phiếu xuất, phiếu thu chi hoặc khách hàng, dùng Đối soát & In bộ giấy để chọn các chứng từ đã ghi của lượt. Biên bản tách nợ từng đơn vị, tăng/giảm lượt, cọc và tiền chưa phân bổ. Bản đã cấp lưu PDF riêng tư để in lại đúng số cũ; phát sinh sau lập bản bổ sung nối bản trước. Chỉ người có quyền ký nợ xác nhận biên bản.

Giấy gốc: kế toán cửa hàng xếp theo loại giấy/ngày hoặc tập đã quy định, ghi đúng vị trí lưu trên hồ sơ; giấy vệ tinh chuyển về cùng tập. Ảnh, đối chiếu và người nhận gốc có dấu riêng. Chốt ngày liệt kê phần hồ sơ còn thiếu; không thêm một cấp duyệt cho việc bình thường.

## 8. Đổi/trả và giảm giá đơn cũ

- Hàng đã xuất lên xe rồi đổi mã: nhận trả lượng cũ thực nhận, sau đó lập đơn thay và xuất mã mới; không sửa đè phiếu đã xuất.
- Trả5kg từ bao25kg: nhập5kg và số bao/vỏ thực nhận0hoặc1, không nhập0,2bao. Hàng hỏng vào cách ly theo lựa chọn.
- Chưa trả tiền: giảm khoản còn nợ. Đã thu tiền: chỉ chuẩn bị hoàn phần thực phải hoàn sau đối trừ. Mở phiếu hoàn tiền từ phiếu nhận trả; nháp không có nghĩa đã chi.
- Giảm giá do chất lượng của đơn cũ xử lý theo đúng khoản gốc, không giấu vào giá của đơn mới. Đề nghị nháp chưa làm giảm nợ.
- Đường giảm theo phần hàng đang kiểm thử: chọn đúng khoản cũ, ghi dòng/kg và tiền giảm của phần đó; phần còn lại giữ giá gốc. Khi nhận trả chọn rõ phần đã giảm hoặc chưa giảm, không lấy giá bình quân cả mã.
- Khoản giảm cũ chưa ghi lượng: từ JE có nguồn khoản phải thu → Bổ sung phần hàng đã giảm. Phải đối chiếu giấy thỏa thuận và đúng tiền hàng/thuế đã ghi; thao tác chỉ bổ sung phân loại, không ghi giảm nợ thêm. Chưa xác minh được hoặc đã có trả cũ chưa phân loại thì kế toán đối chiếu bằng chứng trước.
- **Chưa hoàn thiện/kiểm đủ:** đường phân loại và hoàn sau giảm mới chưa nativePASS toàn bộ; nối nhu cầu gom kho trực tiếp từ đơn; thu/hoàn chênh lệch đổi mã trong một cửa sổ. Các điểm này còn trong phạm vi phát triển, không coi hướng dẫn là bằng chứng đã hỗ trợ đầy đủ.


## Bổ sung đang phát triển: cọc theo nguồn trong đối soát

Từ Tiền thực nhận hoặc Xử lý tiền cọc/phân bổ đã ghi, khách đã xác minh, mở Đối soát & In bộ giấy. Chọn đủ đơn vị liên quan và đúng chứng từ của lượt. Biên bản trình bày khoản tiền/cọc chọn, cọc còn giữ theo khoản nhận/đơn/nguồn và phần khả dụng riêng; không trừ cọc vào công nợ lần nữa. Bản cấp rồi giữ nguyên số/PDF khi có phát sinh sau đó, cần đối chiếu mới thì lập bản bổ sung. Cọc chung có nhãn riêng, không tự gán cho nguồn của đơn vị thực nhận. Phần này mới kiểm cục bộ, chờ HTTP/PDF native140; bản in riêng phiếu thu cọc chưa tự ghép như phiếu thu PE.


Bổ sung tiếp đang kiểm: khoản Tiền thực nhận đã ghi có nút In phiếu thu, dùng số khoản nhận và bút toán đã ghi. Chọn khoản thực nhận trong bộ đối soát sẽ ghép bản thu này; chỉ chọn thao tác giữ/chuyển/giải phóng/cấn không in lại phiếu nhận cũ. Mẫu dùng lại cách phân biệt tiền mặt/ngân hàng theo công ty hiện có. Không phát sinh PE/JE mới khi in. Phần này mới621ca cục bộ, chờ native140 và xemPDF trước phát hành.
