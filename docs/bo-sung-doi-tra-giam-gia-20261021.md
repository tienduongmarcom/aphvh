# Bổ sung thiết kế: đổi tại xe, đổi/trả sau giao và giảm giá hàng xấu

> 21/10/2026. Yêu cầu bổ sung của chủ dự án, cùng phạm vi tối ưu kho–giao nhận. Thiết kế đề xuất, chưa code hoặc áp dụng production0.16.4. Tái dùng chứng từ chuẩn, không dựng sổ kho/nợ khác.

## 1. Mục tiêu và phạm vi

Nhân sựU50 xử lý từ đơn/phiếu gốc bằng một lối “Đổi / Trả / Giảm giá”. Hệ thống phân biệt giao nhận thực tế và trạng thái đã ghi sổ, không suy “chưa rời xe” đồng nghĩa chưa xuất. Không sửa thẳng mã/lượng/giá trên chứng từ đã ghi sổ hoặc giấy đã ký để xóa dấu giao dịch cũ.

## 2. Hiện trạng và căn cứ

Đã đọc `kh_aph/sales_adjust.py`: có phân loại trả/giảm, nháp xe quay về/chuyển khách, kiểm chứng từ giảm; helper xe quay về hiện chỉ nhận DN Đang giao, chưa đủ cho khách đã nhận rồi trả. `delivery_receivable` xử lý liên kết công nợ, cần tận dụng có kiểm tra thay vì tạo thêm lần ghi giảm. Đọc nguồn không phải chứng minh các tình huống mới đã PASS.

Theo [TT91/2026 bản ký](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/91-btc.signed.pdf), Điều10 khoản5 điểm c.1 (trang20), có quy định xử lý hóa đơn khi trả một phần/toàn bộ, bao gồm đổi hàng làm thay đổi giá trị; giữ hồ sơ liên quan. Phân biệt giao dịch phát sinh sau bán với hóa đơn ban đầu lập sai. Phương án hóa đơn/MISA cho giảm giá chất lượng và đổi ngang giá phải đối chiếu hồ sơ cụ thể, không gắn nhãn “hủy hóa đơn gốc” mặc định. Căn cứ hiện hành/hiệu lực xem `de-xuat-chung-tu-kho-theo-phap-ly-20261021.md`.

## 3. Quy trình, nhân sự

| Tình huống | Thao tác gọn | Xử lý phía sau |
| --- | --- | --- |
| Hàng mới lên xe, chưa ghi xuấtERP | Đầu mối chọn “Đổi tại kho”, kho kiểm hàng gỡ xuống và hàng giao thay | Sửa phiếu chuẩn bị chưa ghi sổ nếu đúng sự kiện thực tế; giấy cũ thu hồi/đánh dấu thay thế, giữ lịch sử. Nếu đã giao nhận thực tế thì vẫn lưu dấu thực giao/nhận lại, không xóa bằng cách sửa nháp |
| Đã ghi xuấtERP, khách đổi khi xe còn tại kho | Chọn dòng trả bớt và mã/lượng lấy thay ngay trên phiếu gốc | Tạo chứng từ nhận lại đúng lượng thực nhập và xuất mới đúng lượng thực giao; điều chỉnh tiền/nợ theo liên kết. Không hủy cả đơn chỉ để đổi một phần |
| Khách đã mang hàng về rồi trả | Tìm khách/phiếu, chọn “Trả hàng”, lượng, lý do, kho nhận thực tế | Tiếp nhận đề nghị; ghi nhận kho khi nhận hàng thật; xử lý giảm nợ/tiền/hóa đơn theo chứng từ và thẩm quyền |
| Khách đổi hàng sau khi đã mang về | Cùng lối trên, chọn thêm hàng mới | Liên kết trả và giao mới; không giả nhận kho khi hàng chưa về. Được duyệt giao mới trước thì vẫn là giao dịch riêng, không cấn lượng trả dự kiến thành tồn có thể bán |
| Khách giữ hàng nhưng đàm phán giảm giá vì hàng xấu | Chọn “Giảm giá do chất lượng” trên đơn/phiếu cũ, ghi dòng/lượng bị ảnh hưởng và đề nghị giảm | Chờ người có quyền chấp nhận; khi ghi nhận đúng chứng từ thì giảm giá trị/nợ, **không nhập lại kho hoặc giảm lượng đã giao** |

Kho xác nhận lượng/tình trạng và nơi nhận thực; đầu mối cửa hàng thao tác phần mềm; người có thẩm quyền xử lý giảm giá/ngoại lệ theo quyền hiện hành. Không mặc định mọi thao tác đều phải đợi kế toán trưởng hoặc cấp duyệt mới; bảng phân cấp giá/hoàn tiền còn cần đối chiếu trước build.

## 4. Quy tắc và ngoại lệ

- Khách thay mã để dùng thử là giao mã thay theo thỏa thuận bán hàng; không tự coi là hàng mẫu miễn phí hoặc hàng gửi dùng thử có quyền trả vô điều kiện.
- Tách “Khách đề nghị trả/giảm” với “Đã nhận lại hàng” và “Đã ghi giảm tiền/nợ”. Đề nghị chưa được chấp nhận không làm thay số nợ chính thức. Số đang tranh luận hiển thị riêng, không giả khách không còn quá hạn.
- Giảm vì chất lượng gắn đúng đợt/phiếu/dòng cũ và đơn vị bán; không trừ kín vào giá của đơn mới. Giảm giá hàng bán khác với xóa nợ không thu được/chiết khấu thương mại; không dùng chung một lý do hoặc chứng từ mặc định cho tất cả.
- Hàng nhập lại có thể bán tiếp hoặc có vấn đề: chọn kho nhận/tình trạng theo cây kho và quy định hiện có; không tự tạo kho mới hay tự đưa hàng hỏng vào tồn bán được. Kho nhận có thể khác kho đã xuất nếu cùng chủ sở hữu và quyền cho phép, giữ liên kết gốc; khác đơn vị phải xử lý chủ thể riêng.
- Giới hạn trả lũy kế theo dòng gốc trừ các phiếu trả đã ghi nhận, kể cả hai người đồng thời; không cho dùng cùng khoản giảm hai lần. Kiểm các giảm giá trước để không giảm vượt giá trị còn được xử lý.
- Chênh lệch đổi hàng được tính từ giá trị trả được chấp nhận và giá trị hàng mới đã duyệt, có thuế khi áp dụng, không chỉ nhân lượng giá hiện tại củaItem. Dòng trả truy nguồn giá/quy cách/thuế gốc; giá bán mã mới theo giao dịch mới.
- Đã thanh toán thì khoản trả/giảm có thể thành tiền khách còn được nhận hoặc số dư có; cho chọn hoàn tiền hay giữ để phân bổ, không tự hoàn hoặc chuyển thành cọc. Hoàn thực tế mới có chứng từ chi; chưa chi giữ nghĩa vụ phải hoàn. Chưa thu tiền thì giảm đúng khoản phải thu; thu/hoàn/bù trừ không lặp.
- Không tự lấy tiền được trả ở một công ty cấn nợ hoặc tiền mua hàng của công ty khác. Bản đối chiếu tổng vẫn có từng đơn vị và số dư có/cọc riêng.
- Phiếu trả bị hủy, kỳ đã khóa, giá vốn/repost, chứng từ liên kết hoặc lỗi một bước phải có trạng thái rõ. Giữ kết quả bước đã thành công, retry nối lại đúng chứng từ; không giả toàn bộ đã xong hoặc xóa sự kiện thực tế.

### Bổ sung chủ dự án chốt: nợ đơn cũ và trả hỏng một phần bao

- **Giảm giá đơn trước:** khách có thể thương lượng giảm phần công nợ của đơn đã giao từ trước, không cần lập đơn mới. TừKhách hàng → khoản nợ/phiếu cũ → Đổi/Trả/Giảm giá, hoặc ngay trên phiếu gốc; hiển thị đơn vị, ngày, mã hàng, lượng đã giao, số đã trả/giảm và khoản còn phải thu để chọn đúng. Đề nghị chưa thống nhất giữ riêng; khi chấp nhận và ghi nhận đúng chứng từ mới giảm đúng khoản nợ cũ. Không thay giá/lượng lịch sử, không giấu khoản giảm vào lần bán tiếp theo; kỳ cũ khóa thì xử lý phát sinh theo kỳ hợp lệ và giữ liên kết nguồn.
- **Trả hàng hỏng lẻ trong bao:** ví dụ đã bán1bao25kg, khách dùng/giữ20kg và mang trả5kg hỏng. Cho nhập **5kg**, không bắt trả1bao25kg hoặc làm tròn thành cả bao. Phiếu nhận trả ghi thực nhận5kg;20kg còn lại vẫn là lượng khách giữ, không tự nhập lại. Nếu chỉ báo hỏng mà chưa trả vật chất thì dùng nhánhGiảm giá/đề nghị xử lý, không giả nhập5kg.
- Lượngkg nhận lại và **bao bì vật lý nhận lại** là hai thông tin khác nhau. 5kg/25kg=0,2bao quy đổi không có nghĩa nhận0,2vỏ bao. Ghi số bao/vỏ thực nhận nếu nghiệp vụ cần (vd1bao đã mở), không ép quy tắckg=bao nguyên×25. Quy cách quy đổi lấy từ dòng gốc, không theoItem đã sửa sau này. Cần đối chiếu validation bao hiện có trước build để hỗ trợ lẻkg đúng sổ mà không phá kiểm bao các luồng khác.
- Hànghỏng5kg ghi đúng tồn thực nhận và tình trạng/kho không bán được theo cấu hình được duyệt, không tăng tồn bán được. Mua/bán20kg còn lại và số bao bì theo dõi riêng, không tự sửa chứng từ gốc còn20kg để xóa lịch sử25kg đã giao.
- Số được xử lý theo5kg được chấp nhận và giá/thuế dòng gốc hoặc thỏa thuận giảm hợp lệ; không hoàn tiền cả25kg, không mặc định dùng giá bán hôm nay. Hệ thống hiện trước **giá trị trả/giảm, phần giảm khoản phải thu và tiền thực hoàn**.
- Nếu khách đã trả tiền, có nhánhHoàn tiền cho phần được chấp nhận; thực chi mới ghi chứng từchi. Nếu còn nợ, mặc định giảm đúng khoản phải thu tương ứng, phần dư sau đối chiếu mới xử lýhoàn/giữ/phân bổ theo lựa chọn. Trường hợp thỏa thuận hoàn tiền dù còn khoản nợ khác phải thể hiện rõ hai giao dịch và đúng quyền, không tự cấn nợ khác. Tổng giá trị giảm được phân bổ một lần; chứng từchi tất toán nghĩa vụ hoàn, không ghi giảm doanh thu/nợ thêm lần nữa.

## 5. Dữ liệu và màn hình

Màn hình thường chỉ hỏi: loại việc; dòng/lượng trả hoặc giảm; hàng thay nếu đổi; lý do. Tự lấy khách/đơn vị/phiếu/người nhận từ nguồn. Kho nhận chỉ hiện khi nhận hàng; mức đề nghị giảm chỉ hiện với giảm giá; lựa chọn hoàn/giữ/bù trong cùng đơn vị chỉ hiện khi có số dư cần xử lý. Hiển thị trước: hàng nhận lại, hàng giao mới, tăng/giảm nợ, phải thu thêm/phải hoàn/chờ xử lý. Không cho nhập một số “giảm công nợ” không truy nguyên.

Hồ sơ lưu IDdòng gốc, lượng/quy cách, giá/thuế lịch sử và số đã trả/giảm; thời gian sự kiện/nhập; nguồn giấy tay; người đề nghị/quyết định/nhận hàng/thực thu-chi; lý do, bằng chứng chất lượng, chứng từ kho/nợ/tiền/MISA liên kết. Dùng field/childlink tối thiểu theo blueprint trước build; chưa quyết định tạoDocType mới có lifecycle riêng.

## 6. Chứng từ và kiểm soát

- Đổi khi đã ghi xuất: hồ sơ nhận lại và phiếu xuất mã mới; có thể chuẩn bị/in cùng lượt, không bắt nhập lại khách/hàng gốc. Phiếu/biên bản cùng lượt có số tham chiếu riêng, không làm mất hai chiều kho.
- Sau giao: phiếu nhận hàng trả và bằng chứng giao nhận thực tế. Không in ký khống lượng chưa nhận; nhiều lần mang trả ghi từng lần.
- Hàng xấu giữ lại giảm giá: đề xuất **Biên bản thỏa thuận giảm giá do chất lượng**, tham chiếu phiếu/hóa đơn/dòng, lý do, mức giảm/thuế/tổng và người có quyền hai bên; có thể gom cùng trang xác nhận nợ nếu đủ nội dung và tư cách ký. Đây là mẫu quản trị đề xuất, không khẳng định tên mẫu bắt buộc của thông tư.
- Tăng/giảm nợ thì in xác nhận công nợ theo quyết định của chủ dự án. Thu thêm/hoàn tiền có chứng từ tương ứng. Lái xe được nhận hàng không tự có quyền chấp thuận giá/giảm nợ cho khách.
- Nhà xe quen/mới: cho chọn hoặc nhập ngay tên/SĐT (biển số tùy chọn), tùy chọn lưu lần sau; snapshot theo chuyến, không sửa ngược lịch sử. Gửi ship vẫn inPhiếu xuất kho/phần nhà xe nhận. Khách cuối không bắt ký nếu không có yêu cầu/thỏa thuận riêng; đầu mối bấmKhách đã nhận, ghi ngày, nguồnKhách/Nhà xe báo và user/time. Không tự ghi thêm kho/nợ. Các tên/trường bắt buộc nhà xe mới là đề xuất thiết kế, chưa phải mẫu đã duyệt.
- Giấy gốc lưu tập trung kế toán cửa hàng; vệ tinh chuyển về. Ảnh/giấy/thỏa thuận/chứng từ điều chỉnh giữ liên kết phiếu gốc và lịch sử; không lấy in lại thay chứng từ đã ký rồi bỏ bản cũ.

## 7. Tác động hệ thống

Trả hàng thật ảnh hưởng kho/giá vốn theo chứng từ chuẩn và điều chỉnh khoản phải thu theo cơ chế hiện có, tránh ghi giảm hai lần. Hàng thay là xuất mới; giảm giá chất lượng chỉ tài chính/thuế, không biến thành trả hàng giả. Nợ có thể thuộc kỳ trước nhưng thỏa thuận giảm phát sinh hiện tại: giữ liên kết kỳ cũ, không sửa lùi sổ đã khóa. MISA xử lý hóa đơn theo loại sự kiện và luật hiện hành; biên bản đối chiếu không tự thay chứng từ điều chỉnh.

## 8. Ca nghiệm thu đề xuất, chưa chạy

1. Đổi ngay trên xe trước và sau ghi xuất, giữ chứng từ cũ, tồn đúng hai chiều khi đã ghi.
2. Đổi một phần nhiều mã/nhiều kho, không hủy phần giao đúng; mã thay hết tồn không xác nhận xuất giả.
3. Trả sauKhách đã nhận, trả một phần nhiều lần, hai user đồng thời không vượt lượng.
4. Đề nghị trả nhưng hàng chưa về: chưa tăng tồn bán được; giao thay trước có kiểm quyền/tồn/giá riêng.
5. Nhận trả kho khác/hàng hỏng: đúng Company, quyền, tình trạng; không làm lộ giá vốn.
6. Đã thu/chưa thu/thu một phần, đổi ngang giá/thu thêm/hoàn thừa: phân bổ và tiền thực đúng.
7. Giảm vì hàng xấu đã dùng hết: lượng kho không đổi, truy đúng dòng cũ, không trừ đơn mới.
8. Đang đàm phán/chấp nhận một phần/từ chối: nợ chính thức chỉ thay khi ghi nhận hợp lệ.
9. Trả kết hợp giảm giá trước đó: không hoàn/giảm trùng; nhiều đơn vị không tự cấn chéo.
10. Giao/nhận/thu/hoàn bị mất mạng sau một bước, nhập bù/retry không trùng; đối chiếu số còn chờ.
11. Kỳ cũ khóa/hóa đơn đã phát hành: giữ lịch sử, xử lý điều chỉnh đúng hồ sơ/MISA, không lùi ngày giả.
12. Đơn cũ còn nợ giảm do chất lượng: chọn trực tiếp khoản cũ, không cần đơn mới, kỳ khóa không sửa lùi, số đang thương lượng chưa trừ nợ.
13. Bán1bao25kg trả5kg hỏng: tăng tồn thực nhận đúng5kg trong kho/tình trạng phù hợp, không tăng25kg/tồn bán được;20kg vẫn do khách giữ.
14. Trả5kg nhưng chưa nhận/đề nghị giảm không trả: không tự tăng tồn; kiểm0,2bao quy đổi khác số vỏ thực nhận, quy cáchItem đổi không sửa quy đổi gốc.
15. Ca5kg đã trả tiền/còn nợ/trả một phần: đúng giá trị và thuế, khoản giảm/hoàn phân bổ một lần; không hoàn cả25kg hoặc vừa giảm nợ vừa hoàn trùng; retrychi không trùng.
16. Chứng từ giấy có đúng tư cách ký và chênh lệch; trạng thái khách nhận ship không tạo sổ; nhân sựU50 hoàn thành thao tác không phải tìm nhiều màn hình.

## 9. Triển khai và khôi phục

Chỉ bổ sung thiết kế vàoPR36, không đổi mã/chế độ kế toán, không phát hành hay đổi cờ. Khi build phải kiểm lại service hiện có, blueprint khóa/chứng từ/quyền và transaction từng bước, sửa đồng bộ mẫu/case tìm theo nhãn; không tuyên bố tất cả phần trả/giảm đang thiếu vì đã có nền trong code. Cổng thử và bản sao production phải kiểm tác động tồn–giá vốn–nợ–tiền/hủy/retry; nghiệm thu dữ liệu/nhân sự thật vẫn gom cuối. Giữ lịch sử chứng từ điều chỉnh khi quay lui, không restore xóa giao dịch mới.
