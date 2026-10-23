# Đối chiếu triển khai kho – giao nhận, ngày 21/10/2026

## 1. Mục tiêu và phạm vi

Ưu tiên khách hoặc lái xe do khách cử đến lấy; dùng ít người thao tác phần mềm, in trước khi giao, hoàn thiện hồ sơ sau. Ship luôn có phiếu xuất, khách cuối chỉ ký khi có yêu cầu. Trả một phần bao phải ghi đúng kg và bao/vỏ thực nhận. Đổi mã dùng chứng từ nhập trả và xuất mới; giảm giá đơn cũ không được giấu vào đơn mới. Giấy tay khi mất mạng, phiếu thu và bản đối soát nợ theo lượt là phần đã chốt nhưng chưa hoàn thiện trong PR38.

Hướng dẫn thao tác theo nhân sự và tình huống: [Luồng kho – giao nhận gọn](huong-dan-kho-giao-nhan-gon.md); ghi rõ các phần còn thiếu.

**PR38 là ứng viên đang phát triển, chưa phải bản phát hành hoàn tất toàn phạm vi.** Không dùng số ca đạt của một phần để đóng các yêu cầu còn thiếu.

**Cập nhật22/10:** giấy tay chỉ lưu trên chứng từ nhập bổ sung. UAT39766960041 đúng98c37e3 đã đọc135PASS gồm khôi phục, các bộ hồi quy đều đạt. Gom kho chuẩn bị/in→xuất→nhận, hồ sơ khách ký riêng, lịch sử ảnh, snapshot/phân quyền/ngoại tệ và Chrome mất phản hồi khi tạo đối soát đã nativePASS. Tuy nhiên PDF bộ giấy bị tràn mỗi liên A5 thành2trang; đã xem đủ6trang, không coi bố cục đạt. Bản sửa lề và assertion4trang đang kiểm ở UAT39772096251 đúngfb6ab9c, cùng phần Chốt ngày tách Nhà máy. Cục bộ570ca không bỏ qua đạt. Toàn phạm vi vẫn chưa hoàn tất.

**Cập nhật23/10 (ưu tiên hơn các mốc lịch sử bên dưới):** nền c21a799/UAT39775206078 đã đủ135PASS và PDF native4trang A4+2A5+A4; mẫu một dòng đã xem đủ, chưa máy in thật. Phần giảm theo lượng đang mở rộng: UAT39888905491 đúng2a3fefc có ca trả trộn, giữ lượng đồng thời, KTBH nhận trả, hoàn137.500 và hàng giảm100% PASS, nhưng cả lượt FAIL quyền phân loại khoản giảm cũ. Ảnh còn popup quyền bảng con nên chưa đạt giao diện. Đã sửa quyền server, truy vấn cha và siết Chrome; UAT39891158617 đang kiểmfa8ce18, chưa có kết luận. Cục bộ601ca đạt. Chi tiết phạm vi/dữ liệu/ngoại lệ và ca kiểm: [Giảm và trả theo phần hàng](dac-ta-phan-hang-giam-va-tra-20261023.md). Toàn PR38 vẫn nháp.

## 2. Hiện trạng và nguồn

- Production: 0.16.4, tag `1dffa623dc28d239321b7c9cd249968def402123`, digest `sha256:1a8f00639516ff4843d408fca61695c6b7ca0cfe680cf6c1db28fb0f16d09f38`; người vận hành đã xác nhận nâng cấp đạt. Không ghi dữ liệu production trong lượt phát triển này.
- PR38: `feat/kho-giao-nhan-don-gian-20261021`, vẫn nháp. Nền main đã gồm PR37 chuyển Cổng3 sang đúng production0.16.4.
- Bằng chứng nền trước các mở rộng: `b57445753daf9513a8448d24e92d926d1a9a4d9c`. [UAT39631103596](https://github.com/tienduongmarcom/aphvh/actions/runs/39631103596) SUCCESS: đã tải artifact `candidate-image-evidence` (id12360337173), đọc đủ127PASS của bộ014, mốc khôi phục và xem hai ảnh Chrome nhập nhà xe/nhận trảkg. Các bộ hồi quy còn lại của cùng lượt cũng đạt. Cổng2 cùng mã: [39631068245](https://github.com/tienduongmarcom/aphvh/actions/runs/39631068245) SUCCESS.
- Các lượt FAIL trước đó vẫn giữ: UAT39581676952 ở helper Chrome, UAT39625443467 ở yêu cầu phụ tìm biến thể báo cáo số lượng của hồ sơ ẩn vốn. Đã sửa và kiểm lại trong lượt mới; không bỏ ca Chrome hoặc mở quyền giá vốn để vượt lỗi.
- Bằng chứng trước đó: UAT39578838909 trên `320558a` có các ca mới đạt nhưng toàn lượt FAIL ở tên nhà xe chứa HTML. Cổng2 và2b cùng mã đạt; Cổng3 cùng mã đã đạt: schema1115/1115, rollback1105/1105 lệch0; đã đọc artifact.
- Mã nghiệp vụ mới đã kiểm: `98c37e39ad2fb3ee032ea0ac4a40b153c581a258`, [UAT39766960041](https://github.com/tienduongmarcom/aphvh/actions/runs/39766960041) SUCCESS, artifact đã tải/đọc. Kiểm trực quan PDF phát hiện tràn dù assertion nghiệp vụ xanh; giữ artifact làm bằng chứng. Mã sửa `fb6ab9c` chưa có kết quả native. Cổng3 [39764128191](https://github.com/tienduongmarcom/aphvh/actions/runs/39764128191) đúng9a99835 SUCCESS, schema1151/1151 và quay lui1105/1105 lệch0; không suy cho mã sau.
- Mã nghiệp vụ chính: `sales_return.py`, `return_quantity.py`, `sales_exchange.py`, `sales_p1.py`, `delivery_info.py`, `delivery_status.py`, `ho_so_giao_nhan.py`, `ban_nhanh.py`, `bag_stock.py`, `kho_chuan.py`.

## 3. Nhân sự và thao tác đã nối

| Việc | Người thao tác | Đường thao tác | Giới hạn hiện tại |
| --- | --- | --- | --- |
| Chuẩn bị giao, in | Kế toán bán hàng theo quyền native | Đơn bán chung → Lập phiếu xuất & In | Dùng DN nháp hiện có; chưa có lịch sử PDF bất biến theo mỗi lần chuẩn bị |
| Xác nhận giao | Người có quyền xác nhận DN | Kiểm lượng/người thực giao → Khách đến lấy hoặc Bàn giao vận chuyển | Kho vệ tinh không cần tài khoản; người nhập vẫn chịu trách nhiệm nội dung |
| Xe khách đến lấy | Đầu mối cửa hàng | Chọn cách giao, người nhận và căn cứ khách chỉ định | Tính khách đã nhận tại kho; căn cứ này không cấp quyền ký nợ |
| Ship | Đầu mối cửa hàng | Chọn/nhập tên và SĐT nhà xe; sau đó ghi nguồn báo và ngày nhận cuối | Không bắt khách chờ tải ảnh; hồ sơ khách ký riêng khi yêu cầuCó đã nativePASS UAT39766960041, gốc trước ảnh và không ghi sổ lần hai |
| Nhận trả | Người có quyền lập/xác nhận DN | Phiếu gốc hoặc Khách hàng → Nhận hàng trả lại → kiểm phiếu nháp → xác nhận | Nhập kg và bao riêng; chọn cách ly/bán lại được; chọn kho khác còn qua form chuẩn |
| Đổi mã | Người có quyền lập đơn | Phiếu nhận trả đã ghi → Lập đơn hàng thay → chọn mã/lượng/giá trên form đơn chuẩn | Một đơn thay còn hiệu lực; chưa có màn tính và thu/hoàn chênh lệch trong một thao tác |
| Hoàn tiền | Kế toán theo quyền tiền | Đối trừ khoản gốc bằng dịch vụ native, kiểm phiếu chi nháp rồi xác nhận thực chi | Thiếu quyền đối trừ thì giữ credit và chuyển kế toán xử lý; đã có nút Mở phiếu hoàn tiền (HTTP/ChromePASS trênc4b93fa); chưa nối hoàn/chênh lệch một lượt đầy đủ |
| Nhận giấy gốc | Kế toán lưu tập trung | DN → Nhận giấy gốc → vị trí tập | Độc lập ảnh; chưa có thao tác chuyển vị trí lưu đã xác nhận |

## 4. Quy tắc và ngoại lệ

| Tình huống | Đã viết/kiểm gì | Phần còn phải hoàn thiện |
| --- | --- | --- |
| Bấm lại lập phiếu | Dùng request/hash, khóa nguồn và giới hạn lượng; nền GN10 đã có ca mất phản hồi thật | Chưa thay toàn bộ các lối cũ bằng một đường mới duy nhất |
| Bao25kg trả5kg | Nhận đúng5kg; bao vật lý0 hoặc1 theo thực tế, không dùng0.2bao; cách ly | Xử lý tiêu hủy/tái đóng gói hàng lẻ trong kho cách ly chưa hoàn thiện |
| Chưa thu tiền | Giảm khoản gốc, không tạo phiếu chi khống | Còn kiểm hồ sơ giảm giá trước đó |
| Thu một phần/đủ | Native giữ credit riêng khi cần; đối trừ đúng nguồn rồi chuẩn bị hoàn phần dư | Chưa có tổng quan thu/hoàn/chênh lệch trước khi bấm xác nhận trong một cửa sổ |
| Đổi sang mã khác | Nhập trả riêng, đơn thay riêng, không tự sinh lại mã cũ; giữ nguồn khi hủy/lập lại | Chưa tự nối phân bổ credit sang khoản mới hoặc hoàn chênh lệch trong một lượt |
| Giảm giá nợ đơn cũ | Đã viết chọn dòng/kg/tiền giảm và bổ sung phân loại cho JE cũ có căn cứ, không ghi sổ thêm. Tách lượng đã giảm/chưa giảm; trả trộn/hoàn đúng phần đã native PASS riêng tại2a3fefc | Cả lượt chưa đạt vì quyền; đang kiểm bản sửa. Giảm khi khoản gốc đã thu hết, giảm tiếp sau một phần đã trả hoặc lịch sử không phân loại còn cần xử lý; không tự bình quân |
| Mất mạng lâu | Giấy lưu để nhập bổ sung qua DN/SE/PE, số duy nhất theo Company/loại phiếu, thời điểm thực tế và ảnh riêng tư; không đổi ngày hạch toán | NativePASS HTTP_014_GIAY_TAY_NHAP_BO_SUNG, đã kiểm lại trong lượt xanh39766960041; không xây sổ offline/workflow riêng |
| Gom kho vệ tinh | Đã chặn dùng kho Vận chuyển làm nguồn bán | Chuẩn bị SE nháp/in trước xe đi, kho nhận dự kiến, xuất/nhận native qua Transit đã nativePASS UAT39766960041. Liên kết chọn nhu cầu trực tiếp từ đơn bán chưa có |

## 5. Dữ liệu và trạng thái

Dữ liệu mới lưu trên chứng từ native, không tạo sổ kho/nợ hoặc DocType nhiệm vụ riêng. `kh_aph_mau_giao_nhan=1` phân biệt phiếu mới với lịch sử; không tự đổi thế hệ hay đánh dấu giấy cũ đã về.

| Dữ liệu | Nguồn và kiểm soát |
| --- | --- |
| Nhà xe, điện thoại, căn cứ chỉ định, yêu cầu ký cuối | Snapshot trên DN; sau ghi sổ không sửa trực tiếp; payload mới chặn ký tự khiến Frappe âm thầm lọc tên |
| Báo khách nhận | Nguồn Khách/Nhà xe báo, ngày nhận, user/time; nhận lại cùng yêu cầu không thay dấu hoặc ghi lại sổ |
| Nhận trả | Link DN và dòng gốc, lý do, request/hash, kg/bao/quy cách gốc; kiểm tổng lượng gồm cả nháp đang giữ |
| Đơn thay | Link phiếu nhận trả bất biến; khóa duy nhất cho đơn còn hiệu lực; hủy nhả khóa, giữ link lịch sử |
| Giấy gốc | User, thời điểm, vị trí lưu do API ghi; chưa có gốc khác với chưa có ảnh/ảnh chưa đối chiếu |
| Ảnh ký tại kho | Đã viết lịch sử trước/sau trên DN, giữ tệp cũ và dấu đối chiếu; chặn xóa/công khai/giả lịch sử, có cửa xem lại; nativePASS mở rộng tại39766960041 |
| Đối soát nợ ký theo lượt | Đã viết snapshot và bộ PDF lưu riêng tư, ký/gốc riêng, bản bổ sung nối bản trước; số theo Company và cọc riêng. NativePASS số liệu/quyền/lưu bất biến tại39766960041; QA phát hiện A5 tràn, đang kiểm bản sửa; mẫu ngày cũ chỉ còn vai trò tương thích và đã lọc phạm vi |

## 6. Phân quyền và kiểm soát

API mới kiểm quyền native trên nguồn và Company/Customer/Warehouse liên quan; lập/xác nhận chứng từ dùng quyền tương ứng. Gợi ý nhà xe chỉ lấy từ DN người gọi được đọc. Không thêm quyền truy cập giá vốn; các ca NoCost cũ vẫn phải chạy cùng lượt hồi quy.

Đối trừ credit dùng dịch vụ `reconcile_dr_cr_note` đúng ERPNext16.51.1 và chỉ khi có quyền tạo/xác nhận JE; chưa đủ quyền không được chuẩn bị chi vượt phần phải hoàn. Lái xe nhận hàng không mặc nhiên có quyền ký công nợ. Quyền tài khoản nhân sự thật và danh sách người được giao quyền giao giấy tay chưa nghiệm thu; vẫn để cuối theo quyết định của chủ dự án.

## 7. Tác động kho – nợ – tiền – giá vốn – MISA

- Nháp/in không ghi sổ. DN xác nhận sở hữu biến động kho; SI không cập nhật kho chỉ ghi nợ/doanh thu/thuế theo luồng có sẵn.
- Trả lẻ ghi đúng kg và bao vào sổ bao; không suy kg từ bao đã mở. Hàng hỏng không tự vào kho bán được.
- Báo khách nhận, nhận giấy gốc và đối chiếu ảnh không ghi lại kho/nợ/tiền.
- Đối trừ cùng khoản gốc chuyển phân bổ giữa hai hóa đơn bằng JE native, không tạo doanh thu hay thu/chi thêm. Phiếu chi thực tế tất toán số dư có đúng nguồn.
- Không tự cấn giữa Company. Không thay giá/quy cách lịch sử bằng giá/quy cách Item hiện tại.
- Chưa kiểm MISA thật hoặc kết luận tuân thủ toàn bộ hóa đơn/điều chỉnh. Căn cứ hiện hành và việc còn mở xem hồ sơ pháp lý; không dùng việc chưa tự động hóa MISA để trì hoãn nghĩa vụ hóa đơn.

## 8. Truy nguyên kiểm thử

| Ca | Bằng chứng đã đọc | Kết luận giới hạn |
| --- | --- | --- |
| HTTP_014_TRA_LE_5KG | PASS UAT39631103596, đúng b574457 |5kg cách ly,0bao, không ghi sổ lúc nháp, reserve/retry, giảm một lần |
| HTTP_014_TRA_LE_CHUA_THU_KHONG_HOAN | PASS cùng lượt | Chưa thu không chuẩn bị chi |
| HTTP_014_TRA_LE_THU_MOT_PHAN_HOAN_DUNG | PASS cùng lượt | Thu một phần/đủ, đối trừ và thực chi đúng nguồn, không tạo SI giảm lần nữa |
| HTTP_014_DOI_MA_MOI | PASS cùng lượt | Mã khác, một đơn thay, giữ nguồn, hủy/lập lại và giao mới |
| HTTP_014_XE_KHACH_CHI_DINH | PASS cùng lượt | Căn cứ chỉ định và nhận tại kho |
| HTTP_014_TRA_SAU_GIAM_CHAT_LUONG | PASS UAT39631103596 | Khoản một dòng đã giảm100.000, trả đủ25kg: chặn giá gốc, nhận đúng giá trị còn lại sau đối chiếu, không hoàn khống; chặn đề nghị giảm nháp cũ. Chưa chứng minh phân bổ giảm theo dòng/lượng hoặc trả một phần sau giảm |
| HTTP_014_NHA_XE_MOI_BAO_NHAN | PASS cùng lượt | Tên mới chứa `&` lưu/escape đúng; báo khách nhận không cần chữ ký cuối khi chọnKhông, retry không ghi sổ lần hai |
| NATIVE_DESK_KHO_GIAO_NHAN_GON | PASS cùng lượt; đã xem ảnh | Chrome thật nhập nhà xe mới, hộp báo nhận chỉ hai ô, kg/bao trả riêng; không ghi sổ khi kiểm màn hình |
| HTTP_014_NHAN_GIAY_GOC | PASS cùng lượt | Nhận gốc độc lập ảnh, user/time/vị trí, danh sách thiếu gốc và Chốt ngày cập nhật; sửa trực tiếp/bấm lặp không thay dấu hoặc sổ |
| HTTP_014_AN_VON_TIM_BIEN_THE_BAO_CAO | PASS cùng lượt | Yêu cầu phụ của báo cáo số lượng nhận danh sách rỗng; không mở Report/query/Stock Balance/Bin hoặc tùy chọn bỏ quyền; ca Chrome nhận hàng nhà máy cũ chạy tiếp đạt |
| PDF A5 dữ liệu giả | Đã xem PDF tạo bằng Chrome |2trang khi không cần ký cuối,3trang khi có; chưa kiểm máy in thật |

Cục bộ mới nhất570ca kh_aph không bỏ qua đạt. Bộ014 đã đọc đủ135PASS đúng98c37e3, gồm khôi phục dữ liệu/series; inventory33, funds20, cost16, dispatch48, b0111=15, b0112=13, b0113=13, b0114=8, b012=9, b013=10, native16511=4 đềuPASS. Các ca nền trong bảng trên cũng được kiểm lại ở lượt này. Đây là dữ liệu giả, không thay nghiệm thu nhân sự/hàng tồn/máy in thật. Giữ mọi lượtFAIL. Bố cục A5 native đang sửa sau QA, không lấy lượt xanh nghiệp vụ để coi mẫu in đạt.

| Ca mở rộng | Bằng chứng39766960041 đúng98c37e3 | Giới hạn |
| --- | --- | --- |
| HTTP_014_GIAY_TAY_NHAP_BO_SUNG | PASS | Chỉ lưu trên DN/SE/PE chuẩn, không offline/sổ riêng |
| HTTP_014_HO_SO_BAN_KY | PASS | Thay ảnh giữ tệp/dấu cũ; không xóa/công khai/giả lịch sử |
| HTTP_014_CHUAN_BI_GOM_KHO | PASS | Nháp/in không ghi sổ; xuất/nhận qua Transit, đúng kho; chưa nối chọn nhu cầu từ đơn |
| HTTP_014_KHACH_KY_TAI_DICH | PASS | Chỉ ship yêu cầuCó; độc lập bản kho; gốc trước ảnh, không ghi sổ thêm |
| HTTP_014_DOI_SOAT_PHAM_VI | PASS | Company/kho/NoCost/privatePDF, tăng/giảm ròng0 vẫn đủ chi tiết |
| HTTP_014_DOI_SOAT_BAN_KY_BAT_BIEN | PASS | Bản số/PDF bất biến sau hủy nguồn, quyền ký nợ riêng, bản bổ sung nối trước |
| HTTP_014_DOI_SOAT_TIEN_CHUA_PHAN_BO_NGOAI_TE | PASS |10USD×25.000 về250.000VND, không đổi sổ |
| NATIVE_DESK_DOI_SOAT_RETRY | PASS | Kế toán bán hàng thật, mất phản hồi sau200/bấm lại chỉ một bản; ảnh đã đọc nhưng còn lớp nền modal lúc chụp |
| PDF bộ giấy A5 | QA ca một dòng đã đạt riêng |Lượt cũ6trang; bản sửa lề đúng4trang tại39772096251, đã xem đủ; cả lượt FAIL helper import, chờ chạy lại |

Đã tách Chốt ngày khỏi cờ `kh_aph_factory_handover`: dùng các cờ chốt ca, bàn giao và người giữ tiền cửa hàng; giữ quyền quản lý/phạm vi nguồn. Mục chuyển tiếp nhà máy chỉ đọc khi cầu nối bật. Cục bộ570ca đạt; ca native tắt Nhà máy đã HTTP_2B_FACTORY_DAY_CLOSE/DESK_2B_DAY_CLOSE PASS tại39772096251/fb6ab9c; toàn lượt FAIL helper PDF sau đó.

## 9. Triển khai và khôi phục

PR38 vẫn nháp; app chưa tăng version, chủ dự án chưa gắn tag mới và production chưa đổi. Các mở rộng hiện dùng các cờ tính năng sẵn có; các cờ có mặc định tắt nhưng nhiều cờ đã bật ở production, nên không được tự nâng trước khi chốt đầy đủ phạm vi và bộ kiểm.

Schema đi qua bộ cài rõ ràng, không after_migrate. Giữ mã kỹ thuật/DocType, không đổi Company hay chế độ kế toán. Trước phát hành phải đủ cổng trên mã chốt, hồ sơ nghiệm thu và diễn tập bản sao production thực theo SOP; nâng trong tmux. Quay lui dùng image0.16.4 và snapshot ngay trước lần nâng mới, không restore xóa giao dịch phát sinh sau nâng mà chưa xử lý phần phát sinh.
