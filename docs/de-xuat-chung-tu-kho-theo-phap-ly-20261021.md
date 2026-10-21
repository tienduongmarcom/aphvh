# Đề xuất chứng từ kho, giao nhận, tiền và công nợ — rà soát 21/10/2026

> Phạm vi bổ sung sau trao đổi: [đổi tại xe, đổi/trả sau giao và giảm giá hàng xấu](bo-sung-doi-tra-giam-gia-20261021.md). Bao gồm đơn giản hóa xác nhận khách nhận ship và nhập nhà xe mới; ưu tiên phần cập nhật này khi khác thiết kế ship ban đầu.


> Thiết kế để chủ dự án xem xét; chưa ban hành biểu mẫu, chưa đổi code, quyền, site hoặc bản in production0.16.4. Tài liệu này bổ sung hai thiết kế kho ngày21/10 và ưu tiên khi có khác biệt về căn cứ pháp lý. Không tự coi mọi chứng từ hiện tại đã tuân thủ chỉ vì nâng cấp ĐẠT.

## 1. Mục tiêu và phạm vi

Giảm giấy trùng và số lần nhập cho90% khách tự lấy/xe khách lấy, vẫn chứng minh riêng: quyết định xuất, giao nhận thực tế, thu tiền và số nợ khách xác nhận. Nhà máy giữ phân hệ riêng. Phân biệt chứng từ kế toán, bằng chứng giao nhận và hóa đơn/chứng từ điện tử quản lý thuế; gom thao tác không đồng nghĩa gom pháp nhân hoặc ghi sổ nhiều lần.

## 2. Căn cứ và hiện trạng cần sửa

Nguồn chính thức đã đọc: văn bản/thông tin trên cổng Chính phủ, Công báo và cổng đăng ký kinh doanh; bản ký NĐ254 trang11–12,14,16–17,46–47 và TT91 trang32 đã kiểm trực tiếp vì PDF ảnh. Mốc pháp lý của bản đề xuất là21/10/2026; không dùng dự thảo thay văn bản có hiệu lực.

- **Luật Kế toán**, đối chiếu bản hợp nhất41/VBHN-VPQH ngày16/03/2026: Điều16 nội dung;18 lập một lần, đủ liên, nội dung liên giống nhau, không tẩy xóa;19 chữ ký/ủy quyền;41 lưu trữ;52 giới hạn kiêm nhiệm. Điều19 đã được sửa từ2025, không chỉ có cách ký số duy nhất cho mọi chứng từ điện tử.
- **TT133/2016**: chứng từ hướng dẫn, doanh nghiệp được thiết kế phù hợp nhưng phải đủ nội dung theo luật. Cấu hình dự án: An Phú Hưng dùngTT133; không tự chuyển sangTT99 chỉ vì văn bản mới hơn.
- **TT99/2025**, hiệu lực01/01/2026: Điều9 cho tham khảo/sửa/thiết kế biểu mẫu và yêu cầu quy chế hạch toán hoặc tài liệu tương đương; Điều10 phân cấp ký, kế toán trưởng/người được kế toán trưởng ủy quyền không ký thừa ủy quyền chức danh quản lý điều hành trừ trường hợp luật có quy định khác. Phụ lụcI có01-VT,02-VT,01-TT,02-TT; Biên bản giao nhận TSCĐ không phải mẫu giao hàng bán thông thường. Cấu hình dự án: Vĩnh Hưng dùngTT99.
- **TT152/2025** là chế độ hộ/cá nhân kinh doanh, không gắn số mẫu doanh nghiệpTT133/99 thành mẫu bắt buộc cho Minh Khang. Mẫu quản trị và sổ bắt buộc phải đối chiếu riêng theo chế độ/phương pháp thuế của hộ.
- **NĐ254/2026**, hiệu lực01/07/2026: Điều43 làm hết hiệu lựcNĐ123/2020,NĐ70/2025 và Điều1NĐ41/2022; không tiếp tục dẫn hai nghị định cũ làm căn cứ chính cho giao dịch mới. Điều44 có chuyển tiếp, không xóa hồ sơ lịch sử.
- **TT91/2026**, hiệu lực01/07/2026: Điều25 làm hết hiệu lựcTT32/2025; Điều24 quy định chuyển tiếp, bao gồm xử lý hóa đơn cũ. Việc thay văn bản không đồng nghĩa phải hủy hóa đơn đúng đã phát hành trước đây.

Nguồn code hiện tại: A5 `kh_aph/templates/ban_nhanh/phieu_dot_xuat.html`; mẫu chuẩn và biên bản ở `kh_aph/kh_aph/print_format/`; đối soát qua `kh_aph/print_utils.py` → `ban_quay.doi_soat`. A5 đang dùng giá bán thuần, biên bản có tùy chọn giá gồmVAT, đối soát theo ngày chưa phải snapshot ký từng lượt. Đây là các điểm phải đồng bộ trước build, không đổi nhãn rồi coi đã giải quyết.

## 3. Bộ chứng từ và quy trình đề xuất

| Việc | Chứng từ/biểu mẫu đề xuất | Cách giảm trùng |
| --- | --- | --- |
| Khách đặt hàng | Đơn bán/phiếu xác nhận đơn khi khách cần | Không mặc định in thêm nếu đã đủ thông tin trên phiếu giao thực tế |
| Khách/xe được khách chỉ định lấy tại cửa hàng hoặc vệ tinh | **Phiếu xuất kho kiêm biên bản giao nhận hàng hóa**, bố cụcA5 theo mẫu của chủ dự án | Một bộ giấy cho xuất và ký nhận, không in thêm biên bản cùng nội dung; tên ghép là đề xuất mẫu doanh nghiệp, không phải tên mẫu bắt buộc do thông tư ban hành |
| Gửi người vận chuyển | Cùng mẫu, có hai phần nhận vận chuyển và khách nhận cuối | Chữ ký nhận chở không tự thành khách đã nhận; có thể dùng cùng hồ sơ qua hai chặng, không bắt hai lần nhập hàng |
| Gom vệ tinh về cửa hàng, cùng chủ sở hữu | Chứng từ chuyển kho có nguồn/đích, thực xuất/thực nhận; chứng từ lưu thông tương ứng nếu thuộc diện áp dụng | Thực nhận tại cửa hàng rồi mới xuất bán ở kho giao thực tế; không lấy chữ ký tài xế chuyển nội bộ làm chữ ký khách |
| Thực thu tiền mặt | **Phiếu thu**, vận dụng01-TT đúng chế độ; chi/hoàn tiền dùngPhiếu chi tương ứng | Liên kết lần giao và khoản phân bổ, không ghi thêm thu khi in hoặc khi nộp tiền vào két |
| Tiền vào ngân hàng | Chứng từ ghi nhận thu qua ngân hàng, tham chiếu giao dịch ngân hàng | Không gọi là thu tiền mặt; không xác nhận thực thu chỉ dựa ảnh chuyển tiền của người trả |
| Có tăng hoặc giảm nợ | **Biên bản đối chiếu và xác nhận công nợ** | Một bản theo khách, bảng chi tiết từng đơn vị và cọc/tiền chưa phân bổ; giữ từng chủ nợ riêng |
| Thiếu/thừa, chất lượng, hàng trả | Biên bản ghi nhận chênh lệch/giao nhận hàng trả, tham chiếu phiếu gốc; chứng từ nhập/điều chỉnh và xử lý hóa đơn nếu cần | Chỉ thêm khi có ngoại lệ; biên bản riêng không tự thay chứng từ ghi sổ hoặc hóa đơn điều chỉnh |

Đề xuất in theo phát sinh: giao hàng chỉ bộ giao nhận; thu thêm thì kèm phiếu thu; tăng/giảm nợ thì kèm đối chiếu. Một nút có thể chuẩn bị cả bộ nhưng từng giấy có số, bên chịu trách nhiệm và trạng thái riêng. Chưa chốt số liên mẫuA5 mới: hướng dẫn02-VT và01-TT có luân chuyển3liên; giảm còn2liên là lựa chọn thiết kế phải ghi trong quy chế và kiểm đủ nơi lưu, không tuyên bố thông tư bắt mọi phiếu giao hàng phải2 hoặc3liên.

## 4. Quy tắc, ngoại lệ và hóa đơn

**Tên gọi:** với hàng bán thông thường, phụ lụcTT133/99 không buộc chọn một trong hai tên “Phiếu giao nhận” hoặc “Biên bản bàn giao”. Mẫu xuất kho tham khảo làPhiếu xuất kho02-VT; phần chứng minh hai bên giao/nhận hàng có thể thiết kế thêm. Đề xuất dùng “Biên bản giao nhận hàng hóa” khi in riêng, hoặc tên ghép tại mục3 khi đã tích hợp. Không dùng mẫu01-TSCĐ cho giao hàng bán. Chỉ ghi “vận dụng02-VT” nếu nội dung và quy chế thực sự phù hợp, không tự nhận bản ghép là nguyên mẫu Bộ Tài chính.

**Giá:** tách rõ giá bán/thuế/phải thanh toán với giá trị xuất kho theo kế toán. Không đưa giá bán vào ô khiến người đọc hiểu đó là giá vốn02-VT. Bản khách/kho không có quyền giá vốn không được làm lộ giá vốn. Nếu cần kế toán bổ sung định khoản/giá trị sau, lưu phần bổ sung kế toán liên kết rõ, không âm thầm đổi nội dung các liên đã ký hoặc in một liên cùng số với nội dung khác rồi coi giống nhau. Khả năng dùng một mẫu vừa A5 vừa chứng từ kế toán đầy đủ cần kiểm bản mẫu cụ thể trước khi thay.

**Hóa đơn:** NĐ254 Điều9 khoản1 gắn thời điểm bán hàng với chuyển quyền sở hữu/quyền sử dụng, không phụ thuộc đã thu tiền; khoản3 yêu cầu lập theo khối lượng/giá trị từng lần giao. Không đợi khách ký đối soát, thanh toán đủ hoặc yêu cầu lấy hóa đơn mới xử lý. Hàng đợiMISA/đánh dấu ERP là công cụ theo dõi, không phải quyền trì hoãn hóa đơn. Tính năng tự động hóa hóa đơn một phần có thể làm sau; quy trình MISA hiện hành vẫn phải đáp ứng nghĩa vụ từng lần giao. Chưa kiểm thực tế luồngMISA để kết luận đang đáp ứng hay vi phạm.

**Chuyển kho:** NĐ254 Điều6 khoản3 điểm d quy định lựa chọn hóa đơn/PXK kiêm vận chuyển nội bộ cho điều chuyển đến cơ sở phụ thuộc trong phạm vi nêu tại điều khoản; Điều7 khoản8 nêu hàng chuyển kho/sản xuất nội bộ trong một cơ sở; Điều8 khoản7 quản lý PXK kiêm vận chuyển nội bộ như hóa đơn. Phải phân loại thực tế nơi đăng ký, quan hệ phụ thuộc, địa phương và mô hình kê khai. Bản inSE/Phiếu chuyển khoA5 không tự trở thành chứng từ điện tử đã đăng ký hợp lệ. Khác pháp nhân không gọi mặc định là chuyển kho nội bộ; xác định giao dịch/chủ thể trước. Quy ướcTL nội bộ không tự miễn nghĩa vụ thuế của người bán thực tế.

**Mất mạng:** giữ quyết định chủ dự án cho người được giao quyền lập giấy tay mới và giao; dùng số quyển/tờ duy nhất, đủ nội dung, người ký đúng quyền, thời điểm thực tế. Chứng từ giấy nhập lại là cùng nghiệp vụ, không thu/xuất hai lần; không ký chứng từ trắng, không tẩy xóa hoặc lùi ngày hóa đơn giả. Quyền giao bằng giấy không đồng nghĩa được thay hóa đơn điện tử bằng giấy tay hoặc tự hoãn phát hành. Nhánh sự cố hóa đơn cần đối chiếu đúng loại sự cố/nhà cung cấp theoNĐ254/TT91 trước khi cấu hình, chưa thiết kế chi tiết thủ tục thay thế ở đây.

## 5. Dữ liệu, trạng thái và chữ ký

Một lần giao lưu: đơn vị bán/chủ hàng, khách/mã/địa chỉ/SĐT, kho thực xuất, mã và tên hàng, đơn vị, số bao/kg yêu cầu và thực giao, quy cách, thời gian/địa điểm, người giao/nhận, xe/người chở nếu có, căn cứ được khách chỉ định, sai lệch và tham chiếu đơn/phiếu/hóa đơn. Phần ký xác nhận nội dung thực giao chỉ ký sau khi điền thực tế; phiếu chuẩn bị in trước không được coi là bằng chứng đã giao.

Nợ: lưu số dư đầu mốc, phát sinh tăng/giảm, số cuối mốc theo từng đơn vị; cọc/tiền chưa phân bổ riêng, chứng từ tham chiếu, thời điểm chốt dữ liệu và quyền người ký. Chữ ký nhận hàng không mặc nhiên là chữ ký nợ; lái xe phải được khách giao quyền nợ riêng. Ký khi mất mạng phải thể hiện phạm vi số đã biết/mốc gần nhất, không ghi số dư toàn hệ thống chắc chắn nếu chưa kiểm; số cập nhật khác phải xin xác nhận bổ sung, không thay snapshot cũ.

Các trạng thái độc lập: chuẩn bị/đã giao thực tế/chưa ghi ERP/đã ghi ERP; chưa có ảnh/có ảnh/chưa nhận giấy gốc/đã nhận gốc/đã đối chiếu; nợ chưa ký/đã ký đúng phạm vi. Không gom tất cả thành một dấu “Hoàn tất”. Mẫu mới phải có phiên bản và lịch sử in lại; in lại không tự mặc định là bản gốc mới.

## 6. Nhân sự, kiểm soát và lưu trữ

Ít tài khoản thao tác là mục tiêu; không hứa một người được kiêm kế toán/thủ kho/thủ quỹ/người duyệt ở mọi đơn vị. Phải đối chiếuĐiều52 Luật Kế toán và trường hợp ngoại lệ tạiNĐ174 trước khi cấu hình nhân sự; chưa có đủ loại hình pháp lý/quy mô/tổ chức từng đơn vị để khẳng định ngoại lệ. Không tự xóa ô người duyệt hoặc kế toán trưởng trên phiếu thu/chi chuẩn. TT99 Điều10 khoản4 có giới hạn ký thay quản lý riêng; quy chế phải nêu người và phạm vi được ủy quyền thực sự, không chỉ dựa vào roleERP.

Người giao và người nhận hàng ký phần thực giao; tài khoản nhập có thể là đầu mối cửa hàng, vệ tinh không cần tài khoản. Người thực giữ tiền phải tách với người nhập hộ; nộp két là bàn giao nội bộ, không lập thu khách lần nữa; không tự xác nhận nhận tiền từ chính mình.

Giữ quyết định lưu gốc tập trung kế toán cửa hàng, vệ tinh chuyển giấy về. Đề xuất phân tập theo **đơn vị → năm/tháng → loại/số chứng từ**, hồ sơ cùng lượt có bảng liên kết và vị trí tập/tờ, người/ngày nhận gốc, ảnh đầy đủ các trang. Chưa nhận gốc vẫn hiện việc tồn. Ảnh chụp hỗ trợ tra cứu không tự cho phép hủy giấy gốc. Hóa đơn điện tử lưu dữ liệu nguyên gốc/chữ ký/mã và khả năng tra cứu theoNĐ254 Điều5, không chỉPDF ảnh.

Điều41 Luật Kế toán phân biệt tối thiểu5năm tài liệu quản trị không dùng trực tiếp ghi sổ và10năm tài liệu trực tiếp ghi sổ/BCTC, trừ quy định khác; không áp chung5năm cho mọi giấy. Đề xuất quy chế doanh nghiệp lưu cả bộ giao–thu–nợ gắn ghi sổ tối thiểu10năm, xác định thời điểm tính theo quy định; hồ sơ tranh chấp chưa giải quyết giữ tiếp. Đây là chính sách đề xuất, cần phân loại riêng chế độ hộ kinh doanh, không coi mọi loại tài liệu đương nhiên cùng thời hạn luật định.

## 7. Tác động hệ thống

Tái dùngDN/SE/PE và sổ chuẩn. Chuẩn bị/in/ký/lưu bằng chứng không tự ghi kho/tiền/nợ lần nữa. Giữ Company/Warehouse/NoCost và quyền mọi đơn vị của bản đối chiếu tổng. Dùng một bộ giấy không gộp chủ nợ pháp lý hoặc đối trừ chéo công ty. Không tự đổi thời điểm ghi nhận kế toán/thuế chỉ bằng tên chứng từ hoặc trạng tháiERP; cần đối chiếu hợp đồng, sự kiện thực tế và quy tắc hiện hành.

## 8. Tiêu chí kiểm trước khi bật mẫu mới (chưa chạy)

1. APH/TT133, VH/TT99, hộ kinh doanh và đơn vị chưa xác định chế độ hiện đúng nguồn/mã mẫu; không dùngAPH làm tên chung.
2. Pickup cửa hàng/vệ tinh: in trước, điền thực tế, ký đúng tư cách; không thêm biên bản trùng; giao từng phần đúng đợt.
3. Ship: nhận chở và nhận khách cuối phân biệt; trường hợp xe khách được chỉ định không phải ký nhận lần hai.
4. Phiếu thu tiền mặt/bank tách đúng; in lặp/nhập bù giấy tay không tạo thu/xuất trùng.
5. Một lượt nhiều đơn vị: phiếu xuất/thu đúng chủ thể; một đối chiếu có bảng riêng và người đủ quyền ký.
6. Có tăng rồi giảm về0 vẫn in đối chiếu theo yêu cầu chủ dự án; đây là kiểm soát nội bộ, không ghi là quy định bắt buộc ký sau mỗi giao dịch của thông tư.
7. Bản đã ký giữ nguyên số liệu; bổ sung kế toán/in lại không đổi âm thầm nội dung liên; không lộ giá vốn.
8. Phân cấp chữ ký đáp ứng pháp luật/quy chế; không suy roleERP tương đương ủy quyền hoặc miễn kiêm nhiệm.
9. Kho vệ tinh/chuyển nội bộ được phân loại trước khi chọn giấy lưu thông; giấyERP không giả nhãnPXK điện tử quản lý như hóa đơn.
10. Từng lần chuyển giao thuộc diện hóa đơn có hồ sơMISA đúng thời điểm; không đợi cuối đơn/cuối tháng/khách ký nợ.
11. Mất mạng: giữ giấy gốc/thời gian thực tế, số duy nhất, số nợ biết đến mốc nào ghi đúng mốc đó; tách quy trình sự cố hóa đơn.
12. A5 máy in thật đủ cột/chữ ký, nhiều dòng/nhiều trang, đủ liên; ảnh/gốc/XML truy xuất được theo phạm vi quyền.

## 9. Triển khai, khôi phục và phần cần xác minh

Hiện chỉ tài liệu, không cầnmigration/rollbackdữ liệu, không gắn tag hay đổi production. Khi build: chốt bản mẫu vận dụng + quy chế/phân cấp, giữ mẫu cũ truy xuất, cờ mặc định tắt, version hóa hồ sơ đã ký; kiểmsitegiả/bản sao rồi bật. Nghiệm thu thực tế gom cuối theo chủ dự án. Không lấy việc chưaUAT làm lý do bỏ qua nghĩa vụ chứng từ khi vận hành.

Cần dữ kiện trước cấu hình cuối: loại hình pháp lý/tổ chức kế toán của từng đơn vị để xét kiêm nhiệm; đăng ký và mô hình thuế của các kho vệ tinh để chọn chứng từ lưu thông; cách đang xuấtMISA cho từng lần giao và quy trình sự cố. Chưa có dữ kiện thì giữ mục là chưa xác minh, không tự cấp ngoại lệ. Phần đổi mẫu3liên vẫn là nháp, không suy đã được duyệt.

### Nguồn chính thức

- [Luật Kế toán — VBHN41/2026](https://congbao.chinhphu.vn/van-ban/van-ban-hop-nhat-so-41-vbhn-vpqh-469126/63459.htm) — Điều16–19,41,52.
- [TT133 — cổng đăng ký kinh doanh](https://dangkykinhdoanh.gov.vn/vn/pages/ChiTietVanBan.aspx?TypeVB=1&vID=26957); [Công báo](https://congbao.chinhphu.vn/van-ban/thong-tu-so-133-2016-tt-btc-21048/15526.htm).
- [TT99 — bản Công báo, Điều8–10 và Phụ lụcI](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2025/10/46529/59631-1-20251563-156499-2025-tt-btc.pdf); [hướng dẫn ghi biểu mẫu](https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2025/10/46529/59634-1-20251565-156699-2025-tt-btc.pdf).
- [TT152/2025](https://vanban.chinhphu.vn/?docid=216533&pageid=27160&typegroupid=6).
- [NĐ254/2026 — bản ký](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/254-ndcp.signed.pdf) — Điều5,6,7,8,9,43,44.
- [TT91/2026 — bản ký](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/7/91-btc.signed.pdf) — Điều24,25.
- [NĐ174/2016](https://vanban.chinhphu.vn/?docid=187897&pageid=27160) — đối chiếu lưu trữ/kiêm nhiệm theo trường hợp trước cấu hình; chưa khẳng định đủ điều kiện ngoại lệ của khách.
