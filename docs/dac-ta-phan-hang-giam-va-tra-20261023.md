# Giảm giá và nhận trả theo phần hàng

Ghi nhận quyết định của chủ dự án: phân biệt phần đã giảm và chưa giảm, không lấy giá bình quân toàn mã hàng. Phần này thuộc PR38 đang phát triển, chưa phát hành lên production0.16.4.

## 1. Mục tiêu và phạm vi

Một dòng giao có thể gồm nhiều phần thuộc các thỏa thuận giảm khác nhau và một phần giữ nguyên giá. Nhận trả chọn đúng phần, kg và bao thực nhận. Khoản giảm và khoản hoàn không được ghi hai lần. Phạm vi đang làm: nguồn VND, đơn vị Kg, thuế một dòng On Net Total hoặc không thuế; không mở thêm cơ chế hóa đơn MISA một phần.

## 2. Hiện trạng và nguồn code

- JE chuẩn giữ nguồn SI trong `kh_aph_giam_gia_hd`, phân bổ trong `kh_aph_phan_bo_giam`.
- Dòng DN trả giữ `kh_aph_phan_nhan_tra` và nội dung dễ đọc `kh_aph_chi_tiet_phan_tra`.
- `quality_parts.py`: số thập phân, lượng/giá riêng, không FIFO.
- `quality_allocation.py`: khóa, đối chiếu nguồn, bảo vệ phân bổ, giá native và tài chính trước/sau khi bổ sung dữ liệu cũ.
- `sales_p1.py` và `sales_return.py`: API/guard gắn với chứng từ chuẩn. `sales_return.js`: Dialog dùng chung và chọn phần nhận trả.
- Không DocType, sổ kho/nợ hoặc cờ tính năng mới.

## 3. Nhân sự và thao tác

1. Kế toán có quyền lập JE mở khoản gốc → Giảm giá theo phần hàng → dòng/kg/tiền giảm/căn cứ → JE nháp. Kiểm và ghi theo quyền hiện có; nháp chưa giảm nợ.
2. Người được giao quyền nhận trả DN chọn phần đã giảm/chưa giảm và kg/bao thực nhận. DN nháp chưa nhập kho hoặc giảm nợ; ghi DN mới phát sinh qua controller chuẩn.
3. Giá bán đã duyệt được cung cấp trong phạm vi đúng DN; không cấp quyền đọc GL/JE chung cho kế toán bán hàng chỉ để nhận trả.
4. Nếu phải hoàn, mở phiếu chi nháp đã chuẩn bị và xác nhận thực chi theo quyền tiền. Nhận hàng và ghi tiền là hai thao tác có chứng từ riêng.

Với JE cũ đã ghi nhưng chưa ghi lượng: Bổ sung phần hàng đã giảm → chọn dòng/kg/tiền → ghi căn cứ đối chiếu. Phải khớp số đã ghi, không sửa số tài chính để phù hợp phân loại mới. Timeline lưu căn cứ và tóm tắt lượng/tiền.

## 4. Quy tắc và ngoại lệ

- Tổng phần được giảm không vượt lượng gốc; phần nhập mới thuộc lượng chưa giảm. Không tự chuyển lượng từ thỏa thuận khác khi phần đã chọn hết.
- Nháp trả và phiếu trả đã ghi đều giữ lượng ở đúng phần; phiếu hủy không giữ lượng. Giữ trần cả kg/bao trên dòng giao gốc và trần giá trị của khoản phải thu.
- Nháp giảm giữ lượng nhưng chưa được dùng giá chưa xác nhận để hoàn hàng. Có đề nghị giảm nháp phải hoàn tất hoặc bỏ trước khi nhận trả.
- Phân bổ đã lưu không sửa/xóa; thỏa thuận đã làm nguồn cho nhận trả không hủy trực tiếp. Sửa đổi native giữ nguồn, không tự đổi ý nghĩa tiền cũ.
- Giá phần trả là giá thuần: không áp lại chiết khấu header cũ hoặc tách thuế đã gồm trong giá lần thứ hai. Giữ thuế suất/tài khoản nguồn.
- Native có làm tròn đơn giá. Phải khớp đúng đơn giá native và tiền phần đã chọn; chênh tiền vượt0,5VND bị chặn. Không tăng độ chính xác toàn hệ thống hoặc nới trần hoàn để vượt lỗi.
- Hàng đã giảm hết giá trị vẫn nhận về kho theo lượng, không tạo phiếu chi0 hoặc hoàn lại khoản đã giảm.
- Khoản cũ không xác minh được dòng/lượng, đã có trả cũ chưa phân loại, thuế phức hợp, ngoại tệ hoặc thay tiếp thỏa thuận sau trả: dừng để kế toán đối chiếu, chưa tự suy đoán. Đây là giới hạn triển khai hiện tại, không phải thay đổi nghiệp vụ đã chốt.

## 5. Dữ liệu và trạng thái

Khóa phần là JE nguồn trên đúng dòng SI/DN. Phân bổ giữ dòng SI, kg, tiền giảm chưa thuế và thuế. Phần chưa giảm dùng khóa rỗng; khóa này chỉ mang ý nghĩa trong đúng dòng giao gốc, không phải quỹ hoặc giá chung của mã hàng. DN giữ chi tiết lựa chọn và giá/tiền từng phần; không dùng Item hiện tại để sửa giá lịch sử.

Nếu một dòng DN nhận cả hai phần, chi tiết vẫn riêng. Đơn giá tổng hợp native chỉ phục vụ đúng lượng đã chọn trên dòng trả, không đổi giá phần khách còn giữ và không phân bổ lại giảm giá cho toàn mã.

## 6. Phân quyền và kiểm soát

API lập/phân loại giảm cần quyền kế toán và quyền native trên nguồn. Bổ sung JE đã ghi cần read/write, phạm vi SI/Company, modified và khóa nguồn. Đọc cơ sở nhận trả theo DN chỉ cung cấp giá bán đã duyệt; vẫn kiểm phạm vi native của SI/JE, không trả tài khoản, GL hoặc giá vốn và không cấp DocPerm mới.

Metadata chỉ ghi qua capability nội bộ theo object trong một thao tác. Form/API thông thường không tự gán, thay hoặc xóa phân bổ. Bổ sung nguồn cũ kiểm lại tiền hàng/thuế/tài khoản/cost center, lưu Comment và kiểm tài chính trước/sau. Không bật ignore_permissions hoặc bỏ repost. Bấm lại cùng phân loại trả bản đã lưu; khác lượng/tiền phải bị chặn.

## 7. Tác động hệ thống

- JE xác nhận giảm dùng luồng tài chính cũ; không thay quy tắc TT133/TT99 hoặc MISA.
- DN nhập trả tạo kho; SI giảm không cập nhật kho lần hai. Bao vật lý độc lập kg.
- Bổ sung phân loại chỉ ghi metadata/Comment, không thay GL/PLE/SLE/tiền hay phát sinh JE khác.
- Đối trừ và hoàn dùng cùng khoản gốc; không cấn Company khác hoặc lấy dư có cũ để tăng hoàn lượt này.

## 8. Tiêu chí nghiệm thu

Dữ liệu giả chuẩn:25kg ×35.000VND/kg, VAT10%; chỉ5kg được giảm55.000VND gồm thuế, tương ứng50.000 tiền hàng và5.000 thuế.20kg giữ giá gốc.

| Ca | Thao tác | Kết quả cần chứng minh |
| --- | --- | --- |
| Chọn đúng phần | Xem nhận trả |5kg giá thuần25.000;20kg giá thuần35.000 |
| Trả trộn |3kg đã giảm +2kg chưa giảm | Tổng giảm159.500 gồm thuế; chi tiết75.000 +70.000 chưa thuế; còn2kg đã giảm/18kg chưa giảm |
| Hai phiên | Mỗi phiên giữ3kg từ phần5kg | Chỉ một nháp được tạo; bỏ nháp nhả đúng lượng |
| Giá giả | Đổi giá trả cao hơn phần đã chọn | Chặn ở lưu/ghi; kho/nợ không đổi |
| Hoàn tiền | Thu đủ khoản sau giảm, trả5kg đã giảm | Chuẩn bị hoàn137.500, không192.500; xác nhận chi không sinh giảm nợ lần nữa |
| Giảm100% | Nhận lại hàng đã hết giá trị | Kg nhập đúng; không phát sinh phiếu hoàn0 hoặc hoàn thêm |
| Nguồn cũ | Bổ sung5kg/55.000 vào JE đã ghi | Số JE/kỳ/accounts/GL/PLE/SLE/nợ/tiền không đổi; có phân loại/căn cứ |
| Retry | Lưu lại cùng phân loại, kể cả đã có trả sau đó | Một phân loại, không ghi sổ hoặc thêm Comment lần hai |
| Quyền | KTBH nhận trả; tài khoản ngoài phạm vi thử phân loại | KTBH không cần quyền đọc JE chung; nguồn ngoài quyền vẫn chặn |

Cục bộ mới nhất601ca đạt. UAT39888905491 đúng2a3fefc đã tải/đọc138PASS gồm trả trộn, đồng thời, KTBH, hoàn137.500 và nhận hàng giảm100%; toàn lượt FAIL quyền tài khoản nhà máy cộng vai trò kế toán khi phân loại cũ. QA ảnh còn popup quyền bảng con che Dialog. Đã sửa guard server trước đọc nguồn, dùng truy vấn chứng từ cha có quyền và thêm assertion không có modal/HTTP lỗi. UAT39891158617 kiểmfa8ce18 gồm cả bản rà làm tròn/giá thuần; chưa có kết quả. Không thay yêu cầu thành PASS dựa vào unit test.

## 9. Triển khai và khôi phục

Schema qua bộ cài tính năng hiện có, không after_migrate. CF phân bổ JE cho phép cập nhật sau ghi chỉ để hỗ trợ metadata cũ; hook bảo vệ capability và tính bất biến vẫn bắt buộc. Trước schema mới, đường cũ không query cột thiếu, đường mới phải báo chưa cài.

Trước phát hành cần native nghiệp vụ/Chrome, Cổng2/2b/3 trên mã chốt và diễn tập bản sao đúng SOP. Nghiệm thu nhân sự/hàng tồn/máy in thật để cuối theo chủ dự án. Production giữ0.16.4; không gắn tag/gộp/nâng trong phần phát triển này. Quay lui phải giữ và đối chiếu các giao dịch phát sinh, không xóa lịch sử để làm báo cáo khớp.

Nguồn framework đã đối chiếu: [JE16.51.1](https://raw.githubusercontent.com/frappe/erpnext/v16.51.1/erpnext/accounts/doctype/journal_entry/journal_entry.py), [kiểm trường ảnh hưởng sổ](https://raw.githubusercontent.com/frappe/erpnext/v16.51.1/erpnext/controllers/accounts_controller.py), [trường giá DN](https://raw.githubusercontent.com/frappe/erpnext/v16.51.1/erpnext/stock/doctype/delivery_note_item/delivery_note_item.json). Không sửa core; kết quả native mới là bằng chứng vận hành.
