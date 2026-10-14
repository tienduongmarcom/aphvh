# APH–VH–MK–TL — Khôi phục bộ quyết định 202 câu hỏi nghiệp vụ

**Ngày tổng hợp:** 14/10/2026  
**Mục đích:** Bản có thể chuyển cho Claude/đội triển khai mà không đánh tráo phần thiếu thành nguyên văn đã xác minh.

> **CẢNH BÁO VỀ ĐỘ ĐẦY ĐỦ:** Đây **không phải nguyên văn đầy đủ 202 câu**. 
> Nguồn hội thoại hiện truy xuất được phần cuối (Q172–202), một số số câu rời rạc 
> và nhiều quyết định nghiệp vụ đã được tóm tắt. Tài liệu bàn giao `APHVH_CLAUDE_START_HERE_20261013.md` 
> cũng ghi rõ không chứa nguyên văn 202 câu. 
> **Không được tự gán các điều khoản theo nhóm dưới đây thành Q1–171 hoặc tuyên bố 202/202 đã được kiểm chứng.**

**Nguồn tham chiếu đã nhận diện:** hội thoại gốc https://chatgpt.com/share/6ac912f8-714c-83ec-96ad-9fd4c9533c57 ; 
tài liệu bàn giao 13/10 và các lựa chọn hiện diện trong chuỗi chat. Liên kết share không đọc được tự động ở phiên này.

## A. Quyết định nghiệp vụ đã khôi phục — phân nhóm chủ đề, KHÔNG phải số câu gốc


### 01. Phạm vi và nguyên tắc hệ thống
- **R001.** ERPNext mới trên GCloud, site `frontend`; không sử dụng cấu hình của `erpnext.local` cũ làm baseline.
- **R002.** Bốn đơn vị vận hành APH, VH, MK, TL; TL cũng được gọi là XB, không phải công ty thứ năm.
- **R003.** Một hệ thống quản lý vận hành thực tế; MISA dùng cho nghiệp vụ hóa đơn/kế toán thuế bên ngoài.
- **R004.** Một danh mục khách hàng chung, không tạo khách trùng chỉ vì khác công ty hoặc nơi giao.
- **R005.** Không tạo giao dịch nội bộ giả chỉ để hợp thức hóa khác biệt giữa công ty sở hữu, công ty thu tiền và đơn vị xuất hóa đơn.

### 02. Đơn bán và giá bán
- **R006.** Nhân viên lập một đơn bán tổng hợp; mỗi dòng hàng xác định đúng SKU, công ty sở hữu và kho nguồn.
- **R007.** Đơn tổng hợp có thể chứa hàng APH, VH, MK và TL; chứng từ nội bộ và sổ theo công ty thực tế.
- **R008.** Một đơn có thể giao từng phần, giao từ nhiều kho hoặc giao nhiều địa điểm.
- **R009.** Theo dõi số lượng đặt, đã giao, còn giao và phần bị hủy, không cộng trùng doanh số.
- **R010.** Trước khi giao, được đổi kho/công ty nguồn cho phần chưa giao; phần đã giao giữ nguyên lịch sử.
- **R011.** Bảng giá gợi ý; giá thực tế trên đơn được điều chỉnh theo phân quyền, cảnh báo khi thấp hơn ngưỡng hoặc giá vốn.
- **R012.** Giá bán đã chốt theo thỏa thuận khách hàng có thể là giá bao gồm VAT nếu có; không tự cộng VAT hai lần.
- **R013.** Không gắn hoa hồng hay doanh số cho một nhân viên kinh doanh chưa tồn tại trong thực tế.
- **R014.** Người tạo đơn được ghi nhận để truy vết, không tự hiểu là người phụ trách khách hàng.

### 03. Xuất kho, giao hàng và trả hàng
- **R015.** Trạng thái nghiệp vụ: Chờ xuất → Đang giao → Khách đã nhận.
- **R016.** Shipper ngoài nhận hàng: xác nhận Đang giao để xuất kho và phát sinh công nợ; xác nhận khách nhận sau đó không ghi sổ lần hai.
- **R017.** Khách đến lấy: có thể chuyển Chờ xuất → Khách đã nhận, xuất kho ngay.
- **R018.** Mỗi đợt giao có trạng thái và số lượng riêng; mỗi kho xác nhận phần hàng của mình.
- **R019.** Nhân sự được phân quyền có thể đổi trạng thái, hệ thống lưu người và thời gian.
- **R020.** Không bắt buộc tải ảnh hoặc chứng cứ khi xác nhận đã giao.
- **R021.** Giao thiếu/giao một phần, khách hủy phần còn lại, hoặc đổi khách nhận được xử lý trên số lượng thực tế.
- **R022.** Xe quay về: nhập lại kho theo lượng thực nhận; chuyển khách khác: gắn với đơn của khách mới; chuyển kho khác: tạo nghiệp vụ chuyển kho.
- **R023.** Hàng còn đang vận chuyển không tự động cộng lại tồn khả dụng.
- **R024.** Chênh lệch số lượng giao hàng được xử lý bằng điều chỉnh chứng từ hợp lệ; không tạo trả hàng giả do lỗi nhập liệu.
- **R025.** Hàng trả lại được theo dõi riêng theo tình trạng còn bán được, cách ly, hoàn tiền, bù trừ hoặc đổi hàng.
- **R026.** Giảm giá sau giao hàng lập điều chỉnh riêng; giảm cho toàn bộ đơn phân bổ theo tỷ trọng giá trị dòng.
- **R027.** Tiền vận chuyển ngoài do khách trả trực tiếp cho lái xe khi đúng thực tế, không giả lập công ty thu hộ hoặc COD.

### 04. Thu tiền, cọc và công nợ
- **R028.** Hiển thị đồng thời số còn phải thanh toán toàn đơn, công nợ phần đã giao và giá trị chưa giao.
- **R029.** Ghi nhận tiền theo đúng tài khoản ngân hàng hoặc quỹ của đơn vị thực nhận.
- **R030.** APH thường nhận tiền phần APH+TL; VH/MK thường nhận phần của chính mình; không tự đổi đơn vị nhận nếu khác thực tế.
- **R031.** Tiền xác định được khách nhưng chưa rõ đơn được ghi nhận chưa phân bổ, cho phép phân bổ từng phần về sau.
- **R032.** Tiền chưa rõ người chuyển/đơn vẫn ghi nhận vào đúng quỹ hoặc ngân hàng và xử lý nhận diện sau.
- **R033.** Tiền cọc đơn mới được giữ riêng, không tự cấn sang công nợ cũ theo FIFO.
- **R034.** Cọc có thể dành riêng cho nguồn APH/VH/MK/TL hoặc là cọc chung; phân bổ từng phần theo thỏa thuận.
- **R035.** Khi hủy đơn có cọc: hoàn, giữ, chuyển đơn hoặc bù công nợ theo thỏa thuận; không tự động.
- **R036.** Khách thanh toán gộp nhiều đơn: lưu thu thực tế, phân bổ thủ công về sau.
- **R037.** Đối soát ngân hàng: ghi nhận ngay các giao dịch có thông tin; nhập sao kê CSV/Excel để đối chiếu, chống trùng.
- **R038.** In phiếu thu, đối chiếu công nợ; đối chiếu định kỳ hàng tháng và khi có biến động công nợ.
- **R039.** Khách chưa xác nhận công nợ: cảnh báo, không chặn hoạt động thông thường.
- **R040.** Hạn mức công nợ tính chung một khách qua bốn đơn vị; kiểm tra khi tạo đơn và khi giao.
- **R041.** Khoản tiền chưa phân bổ đã xác minh đúng khách được trừ ròng khi đánh giá hạn mức mà không cấn nợ tự động.
- **R042.** Khách rủi ro cao có thể cần phê duyệt bán chịu/giao tiếp; phê duyệt gắn đúng nội dung được duyệt.
- **R043.** Nợ quá hạn thông thường chỉ cảnh báo, không tự chặn bán hàng khi còn trong hạn mức.
- **R044.** Ngày đến hạn mặc định theo khách, có thể đổi trên đơn; các đợt giao của một đơn dùng cùng hạn theo ngày xác nhận đơn.
- **R045.** Đổi hạn thanh toán theo quyền, giữ lịch sử ngày cũ.
- **R046.** Tiền mặt Dũng thu tại nhà máy nằm trong một quỹ tiền mặt thực tế, nhưng đánh dấu rõ nguồn tiền.
- **R047.** Tiền mặt bàn giao vật lý cho người nhận, có xác nhận; không mặc định chuyển thành nộp ngân hàng.
- **R048.** Cho phép bàn giao tiền từng phần; chênh lệch chờ điều tra, không tự động quy trách nhiệm.
- **R049.** Thông báo chuyển khoản của khách không đồng nghĩa ngân hàng đã nhận; kế toán Hà Nội xác minh tiền vào.

### 05. Kho, đơn vị tính và kiểm kê
- **R050.** Quản lý hàng hóa theo SKU, kho, công ty sở hữu và đơn vị tính; hàng bao có quy cách quy đổi sang kg.
- **R051.** Moving Average riêng theo SKU và kho theo thiết kế được chốt.
- **R052.** Hàng đóng bao theo số bao nguyên; không bắt buộc bán lẻ bằng cách xé bao niêm phong.
- **R053.** Phiếu cần hiển thị số bao/kg hoặc đơn vị thùng, hộp theo loại hàng.
- **R054.** Kiểm kê toàn kho, kiểm kê xoay vòng hoặc đột xuất; cho phép giao dịch trong lúc kiểm kê với mốc thời gian.
- **R055.** Chênh lệch kiểm kê lớn cần cảnh báo và xử lý có trách nhiệm/nhật ký.
- **R056.** Thiếu tồn trong thời gian chờ xử lý làm giảm lượng có thể bán; thừa tồn chưa xác nhận chưa tự động bán.
- **R057.** Đề nghị bổ sung hàng dựa trên ngưỡng kho/SKU, tồn khả dụng và hàng đang vận chuyển dự kiến.
- **R058.** Yêu cầu bổ sung/chuyển kho chưa xuất thực tế không tự động giữ hàng tại kho nguồn (Q79).
- **R059.** Một yêu cầu có thể được đáp ứng từ nhiều kho nguồn.
- **R060.** Chuyển kho giữa địa điểm không tự thay đổi công ty sở hữu hàng.
- **R061.** Đơn hàng báo vượt tồn, giao từ nhiều nguồn và thay đổi nguồn thực tế theo quyền.

### 06. Mua hàng, định giá và chi phí
- **R062.** Kế toán Hà Nội quản lý mua hàng và giá mua; nhà máy có thể xác nhận số lượng/chất lượng thực nhận.
- **R063.** Hàng thương mại nhập chưa rõ giá: quản lý chờ định giá, không đưa vào tồn khả dụng với giá 0.
- **R064.** Nguyên liệu nhà máy cần đưa sản xuất trước khi giá chính thức có thể dùng giá tạm được kế toán kiểm soát; sau đó điều chỉnh/repost khi xác định giá.
- **R065.** Chi phí thu mua theo chuyến có thể phân bổ vào giá trị hàng hoặc ghi nhận chi phí riêng theo thực tế.
- **R066.** Chi phí chung chuyến phân bổ theo trọng lượng kg khi chọn phân bổ.
- **R067.** Chi phí bổ sung sau nhập phải được ghi nhận và phân bổ lại bằng nghiệp vụ hợp lệ.
- **R068.** Hao hụt tự nhiên được tính phù hợp vào giá trị phần hàng còn lại, hao hụt bất thường ghi chi phí riêng.
- **R069.** Ghi hao hụt ngay khi phát hiện và đối chiếu kiểm kê định kỳ.

### 07. Sản xuất Phú Thọ
- **R070.** APH vận hành nhà máy Phú Thọ; nguyên liệu mua về kho trước rồi xuất vào sản xuất.
- **R071.** Dũng là người dùng ERPNext tại nhà máy, công nhân không phải đăng nhập ERPNext giai đoạn này.
- **R072.** Sản xuất liên tục có thể có nhiều lệnh đan xen, tạo nhiều loại thành phẩm và phụ phẩm từ một quá trình.
- **R073.** BOM chủ yếu phục vụ dự kiến nguyên liệu; xuất thực tế có thể khác, cần cảnh báo nhưng không bắt buộc duyệt mọi chênh lệch.
- **R074.** Thành phẩm thực tế nhập kho chung, không ép liên kết từng kg thành phẩm tới từng đơn bán.
- **R075.** Lệnh sản xuất kết thúc theo thực tế ngừng cấp nguyên liệu và kiểm kê/bàn giao sản lượng.
- **R076.** Theo dõi dở dang ước tính trong khi dây chuyền đang chạy; khi dừng và thu hồi hết thì WIP được quyết toán về 0.
- **R077.** Phụ phẩm như cám có thể tái phối trộn mà không bắt theo dõi tỷ lệ cám từng mẻ.
- **R078.** Phân bổ giá thành nhiều thành phẩm/phụ phẩm linh hoạt, có thể dùng trọng lượng làm căn cứ mặc định cho chi phí chung.
- **R079.** Chi phí sản xuất cuối tháng có thể ước tính rồi điều chỉnh theo hóa đơn/thực tế, kéo theo xử lý giá vốn khi cần.
- **R080.** Đóng bao, đóng thùng, phối trộn hoặc repack theo nghiệp vụ thực tế; giữ cân bằng khối lượng theo quy tắc từng nghiệp vụ.
- **R081.** Đa số thành phẩm chuyển về kho bán HN/ĐN/HCM; một phần bán hoặc khách lấy trực tiếp tại nhà máy.
- **R082.** APH nhận sấy hỗ trợ VH/MK theo luồng chuyển đi-về số bao thực tế; không xây module gia công sấy phức tạp giai đoạn đầu.

### 08. Vai trò, nhà máy và bán hàng tại nhà máy
- **R083.** Dũng chỉ xử lý số lượng nhập, xuất, sản xuất, hàng trả và chi phí nhỏ tại nhà máy trong phạm vi công việc.
- **R084.** Dũng không được xem giá mua, giá vốn, định giá tồn và tổng giá thành sản xuất, kể cả qua báo cáo/API/in/export.
- **R085.** Dũng vẫn có thể thấy số tiền chi phí thực tế do mình chi và thông tin giá bán/tiền khách của phần việc được giao.
- **R086.** Chi phí nhỏ tại nhà máy có thể nhập từng khoản hoặc tổng hợp nhiều dòng trong ngày; không bắt buộc tải hóa đơn/ảnh.
- **R087.** Chi công bốc xếp/thời vụ có thể nhập khoản gộp, không cần danh sách từng người lao động.
- **R088.** Chi phí điện, lương, khấu hao và chi phí chung do Hà Nội quản lý, ước tính cuối kỳ và cập nhật sau.
- **R089.** Chưa yêu cầu module bảo dưỡng máy phòng ngừa; ghi sửa chữa có thể liên kết thiết bị nếu thuận tiện.
- **R090.** Dũng có thể bán phụ phẩm trực tiếp; người mua trả đủ có thể dùng khách lẻ chung, công nợ phải có khách xác định.
- **R091.** Thành phẩm chính bán tại nhà máy theo giá Hà Nội chốt, Dũng không được tự sửa giá (Q138).
- **R092.** Chỉ cho xuất bán chịu theo hạn mức và quyền đã thống nhất; cảnh báo nợ quá hạn như nguyên tắc chung.

### 09. Thuế, hóa đơn và báo cáo
- **R093.** Chỉ kế toán Hà Nội thực hiện lập hóa đơn GTGT trên MISA; ERPNext ghi nhận tham chiếu hóa đơn ngoài.
- **R094.** Trạng thái hóa đơn tách biệt với giao hàng, thanh toán và công nợ.
- **R095.** Hồ sơ hóa đơn ERPNext lưu số, ngày, đơn vị phát hành, trạng thái và liên kết đơn/lần giao.
- **R096.** Có hỗ trợ hóa đơn điều chỉnh, thay thế, hủy bằng trạng thái và tham chiếu; không tự động thay đổi ownership.
- **R097.** Không ép đối chiếu số tiền hóa đơn MISA bằng đúng doanh số quản trị nếu thực tế nghiệp vụ khác (Q148).
- **R098.** Quản lý hàng đợi hóa đơn, nhân sự phụ trách; tránh xử lý trùng bằng quyền/nhật ký.
- **R099.** Báo cáo quản trị theo công ty, kho, SKU, khách hàng, đơn hàng, doanh số và lợi nhuận.
- **R100.** Lãi gộp và lãi sau chi phí trực tiếp cùng được xem (Q157-C).
- **R101.** Tổng lãi đơn vị cho báo cáo nội bộ cộng trực tiếp APH+VH+MK+TL, không loại giao dịch nội bộ; cần ghi rõ không phải hợp nhất kế toán (Q161-A).
- **R102.** Tổng dòng tiền phải loại chuyển tiền nội bộ để không bị đếm hai lần.
- **R103.** Dòng tiền dự kiến có tầm nhìn 7/30 ngày, tách thực tế với dự kiến.
- **R104.** Lãi tạm tính được đánh dấu khi giá thành/COGS cuối kỳ chưa khóa.
- **R105.** Phân quyền người xem và thao tác theo kho, đơn vị và vai trò; kỳ khóa không cho sửa lùi tùy tiện.

## B. Những câu có số thứ tự Q172–Q202 trong lịch sử hội thoại

| Số câu | Lựa chọn cuối cùng | Nội dung quyết định đã chốt (diễn giải) |
|---:|:---:|---|
| 172 | Trả lời bằng lời | Không có nhân viên kinh doanh/chủ khách hàng riêng; ghi người nhập đơn để audit, chưa quản lý chia doanh số hay hoa hồng. |
| 173 | A + hoãn triển khai | Danh sách CSKH chung; không quản lý phân công/hoạt động CSKH trong ERPNext giai đoạn này. |
| 174 | C | Kế toán bán hàng được tạo khách mới, sửa liên hệ/địa chỉ; hạn mức nợ/MST/điều khoản tài chính hạn chế theo quyền; lưu lịch sử. |
| 175 | Điều chỉnh bằng lời | Giữ mã khách `KH...`; kiểm tra trùng; KHÔNG giữ trường mã MISA cũ trong ERPNext (sửa quyết định để dữ liệu sạch). |
| 176 | C | Tự động cấp mã `KH...`, quản trị viên được đổi mã có kiểm soát và giữ liên kết. |
| 177 | C | Khách có nhiều địa chỉ; trên đơn chọn địa chỉ có sẵn hoặc nhập mới, không bắt buộc lưu địa chỉ mới. |
| 178 | C | Cho phép một đơn giao nhiều địa chỉ hoặc tạo nhiều đơn riêng; theo dõi từng lần giao. |
| 179 | A | Thông tin người nhận và số điện thoại không bắt buộc; ghi chú khi cần. |
| 180 | C | Cho phép đổi địa chỉ trước giao hoặc khi đang vận chuyển theo quyền và lưu lịch sử; không thay kho/số lượng do đổi địa chỉ. |
| 181 | C | Chưa giao thì sửa sản phẩm/số lượng theo quyền; đã giao một phần chỉ sửa phần chưa giao; hàng đã giao dùng nghiệp vụ trả/đổi. |
| 182 | A | Kế toán được tự hủy phần hàng chưa giao, không bắt buộc duyệt; giữ nguyên hàng đã giao/công nợ và xử lý cọc riêng. |
| 183 | C | Khách hủy khi xe đang vận chuyển: xe về thì nhập kho, chuyển khách khác thì gắn đơn mới, chuyển kho khác theo nghiệp vụ thực tế. |
| 184 | C | Khách nhận một phần: phần từ chối có thể giao tiếp hoặc hủy; hàng phải theo dõi đến khi về kho/chuyển khách khác. |
| 185 | C | Kế toán hoặc người được phân quyền xác nhận số lượng khách thực nhận, không bắt buộc chứng từ ảnh, lưu lịch sử. |
| 186 | C | Sai số lượng giao: kỳ chưa khóa sửa qua nghiệp vụ/chứng từ hợp lệ theo quyền; kỳ đã khóa dùng điều chỉnh riêng. |
| 187 | A | Ngày ghi nhận giao hàng là ngày kế toán xác nhận/nhập ERPNext, không bắt buộc ngày giao thực tế, không tự backdate. |
| 188 | A | Đơn tự hoàn tất khi giao đủ; công nợ chưa thanh toán vẫn theo dõi riêng. |
| 189 | B | Quá ngày giao dự kiến thì đánh dấu trên danh sách, có bộ lọc, không gửi thông báo riêng. |
| 190 | B | Ngày giao dự kiến không bắt buộc; nếu trống thì không cảnh báo quá hạn. |
| 191 | A | Một loại phiếu xuất kho kiêm giao hàng. |
| 192 | C | Một phiếu có chế độ in có giá/không giá, không giá mặc định; chế độ có giá theo phân quyền. |
| 193 | C | Đơn nhiều công ty: có thể in phiếu tổng hợp cho khách và phiếu riêng mỗi công ty. |
| 194 | C (sửa từ A) | Mặc định phiếu tổng hợp không hiển thị công ty dòng; khi cần in chi tiết theo công ty, gồm phiếu riêng APH/VH/MK phục vụ hồ sơ khách. Đây là quyết định C thay cho A cũ. |
| 195 | C | Đầu phiếu tổng hợp trung lập mặc định; cho chọn công ty trên đầu phiếu/phiếu riêng phù hợp khi cần. |
| 196 | C | Đơn có VAT đề xuất phiếu theo công ty; kế toán chọn in tổng hợp/riêng; đối chiếu hóa đơn MISA. |
| 197 | C | Được in trước khi có hóa đơn; sau cập nhật hóa đơn MISA có thể in lại kèm tham chiếu, không đổi số phiếu. |
| 198 | C | Được in lại theo lượng khách thực nhận, giữ phiên bản/lịch sử phiếu gốc, không ghi sổ hai lần. |
| 199 | C | In số bao và kg theo hàng đóng bao; hàng kg thì kg, hàng thùng/hộp theo đơn vị phù hợp. |
| 200 | A | Hàng đóng bao tiêu chuẩn: số kg trên phiếu/tồn theo số bao × kg/bao quy cách; không bắt buộc cân thực tế từng bao. |
| 201 | C | Chọn bán theo kg hoặc bao; hệ thống quy đổi đơn vị từ cùng một SKU. |
| 202 | A | Giá cơ sở theo kg; giá/bao tự quy đổi = giá/kg × kg/bao, không quản lý hai bảng giá độc lập. |

## C. Các số câu rời rạc trước Q172 có thể xác định

- Q79 — Đề nghị chuyển/bổ sung hàng không giữ (reserve) tồn kho nguồn trước khi xuất thực tế.
- Q103 — Repack/đổi đóng gói phải bảo toàn trọng lượng theo quy tắc nghiệp vụ; không tạo hao hụt giả.
- Q132 — Chưa triển khai lập lịch bảo dưỡng định kỳ máy móc (A).
- Q138 — Dũng bán thành phẩm chính tại nhà máy theo giá Hà Nội ấn định, không được sửa (A).
- Q148 — Không buộc số tiền hóa đơn MISA khớp tuyệt đối doanh thu quản trị vận hành (A).
- Q157 — Xem đồng thời lãi gộp và lãi sau chi phí trực tiếp (C).
- Q158–160 — Có thông tin các lựa chọn lần lượt C, C, C nhưng chưa đủ nguyên văn để xác định tiêu đề.
- Q161 — Lợi nhuận quản trị của các đơn vị cộng trực tiếp, không loại giao dịch nội bộ (A).
- Q162–163 — Có thông tin lựa chọn C, C nhưng chưa đủ nguyên văn từng câu.
- Q165 — Công nợ quá hạn cảnh báo, không chặn ngay nếu trong hạn mức (A).
- Q166 — Ngày đến hạn theo khách mặc định, được sửa trên đơn (C).
- Q167 — Các lần giao chung hạn thanh toán dựa trên ngày xác nhận đơn (A).
- Q168 — Cho phép gia hạn công nợ theo quyền và lưu ngày gốc (C).
- Q169–170 — Chiết khấu sau giao ghi điều chỉnh riêng; giảm toàn đơn phân bổ theo tỷ trọng doanh thu các dòng.

## D. Những khoảng chưa thể bảo đảm tính nguyên văn

- **Q1–Q171:** Chưa có bản lịch sử nguyên văn đầy đủ để bảo đảm số câu/đề bài/ba phương án/phương án đã sửa.
- **Q203:** Chỉ là câu hỏi đã nêu sau khi kết thúc 202 câu, **chưa được chốt**; không đưa vào bộ 202.
- **Ưu tiên nguồn:** Nếu có bản xuất/PDF cuộc hội thoại gốc, trích từng Q1–Q202, giữ lựa chọn mới nhất, thêm cột trích nguồn và đánh dấu phần mâu thuẫn; không tự đặt lại số câu.
- **Giới hạn triển khai:** Phải đối chiếu lại chênh lệch giữa ghi nợ khi shipper nhận hàng và báo cáo theo hàng khách thực nhận, cùng việc giá tạm nguyên liệu sản xuất so với hàng thương mại chờ định giá. Không tự sửa quyết định của người dùng.
