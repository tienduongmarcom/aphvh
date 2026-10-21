# Đối chiếu triển khai kho – giao nhận, ngày 21/10/2026

## 1. Mục tiêu và phạm vi

Ưu tiên khách hoặc lái xe do khách cử đến lấy; dùng ít người thao tác phần mềm, in trước khi giao, hoàn thiện hồ sơ sau. Ship luôn có phiếu xuất, khách cuối chỉ ký khi có yêu cầu. Trả một phần bao phải ghi đúng kg và bao/vỏ thực nhận. Đổi mã dùng chứng từ nhập trả và xuất mới; giảm giá đơn cũ không được giấu vào đơn mới. Giấy tay khi mất mạng, phiếu thu và bản đối soát nợ theo lượt là phần đã chốt nhưng chưa hoàn thiện trong PR38.

**PR38 là ứng viên đang phát triển, chưa phải bản phát hành hoàn tất toàn phạm vi.** Không dùng số ca đạt của một phần để đóng các yêu cầu còn thiếu.

## 2. Hiện trạng và nguồn

- Production: 0.16.4, tag `1dffa623dc28d239321b7c9cd249968def402123`, digest `sha256:1a8f00639516ff4843d408fca61695c6b7ca0cfe680cf6c1db28fb0f16d09f38`; người vận hành đã xác nhận nâng cấp đạt. Không ghi dữ liệu production trong lượt phát triển này.
- PR38: `feat/kho-giao-nhan-don-gian-20261021`, vẫn nháp. Nền main đã gồm PR37 chuyển Cổng3 sang đúng production0.16.4.
- Mã kiểm nghiệp vụ trước bổ sung chặn giảm trùng: `3b0219ff63c321419dc8efcff6eb6fecf9487e11`, UAT39581676952 FAIL ở helper Chrome; đã xem ảnh nhập nhà xe và giữ bằng chứng, chưa kết luận phần nhận cuối/giấy gốc đã đạt.
- Bằng chứng trước đó: UAT39578838909 trên `320558a` có các ca mới đạt nhưng toàn lượt FAIL ở tên nhà xe chứa HTML. Cổng2 và2b cùng mã đạt; Cổng3 cùng mã đã đạt: schema1115/1115, rollback1105/1105 lệch0; đã đọc artifact.
- Mã nghiệp vụ chính: `sales_return.py`, `return_quantity.py`, `sales_exchange.py`, `sales_p1.py`, `delivery_info.py`, `delivery_status.py`, `ho_so_giao_nhan.py`, `ban_nhanh.py`, `bag_stock.py`, `kho_chuan.py`.

## 3. Nhân sự và thao tác đã nối

| Việc | Người thao tác | Đường thao tác | Giới hạn hiện tại |
| --- | --- | --- | --- |
| Chuẩn bị giao, in | Kế toán bán hàng theo quyền native | Đơn bán chung → Lập phiếu xuất & In | Dùng DN nháp hiện có; chưa có lịch sử PDF bất biến theo mỗi lần chuẩn bị |
| Xác nhận giao | Người có quyền xác nhận DN | Kiểm lượng/người thực giao → Khách đến lấy hoặc Bàn giao vận chuyển | Kho vệ tinh không cần tài khoản; người nhập vẫn chịu trách nhiệm nội dung |
| Xe khách đến lấy | Đầu mối cửa hàng | Chọn cách giao, người nhận và căn cứ khách chỉ định | Tính khách đã nhận tại kho; căn cứ này không cấp quyền ký nợ |
| Ship | Đầu mối cửa hàng | Chọn/nhập tên và SĐT nhà xe; sau đó ghi nguồn báo và ngày nhận cuối | Không bắt khách chờ tải ảnh; bằng chứng khách cuối khi có yêu cầu riêng chưa có bộ kiểm soát hoàn chỉnh |
| Nhận trả | Người có quyền lập/xác nhận DN | Phiếu gốc hoặc Khách hàng → Nhận hàng trả lại → kiểm phiếu nháp → xác nhận | Nhập kg và bao riêng; chọn cách ly/bán lại được; chọn kho khác còn qua form chuẩn |
| Đổi mã | Người có quyền lập đơn | Phiếu nhận trả đã ghi → Lập đơn hàng thay → chọn mã/lượng/giá trên form đơn chuẩn | Một đơn thay còn hiệu lực; chưa có màn tính và thu/hoàn chênh lệch trong một thao tác |
| Hoàn tiền | Kế toán theo quyền tiền | Đối trừ khoản gốc bằng dịch vụ native, kiểm phiếu chi nháp rồi xác nhận thực chi | Thiếu quyền đối trừ thì giữ credit và chuyển kế toán xử lý; chưa có nút mở/hoàn một lượt đầy đủ |
| Nhận giấy gốc | Kế toán lưu tập trung | DN → Nhận giấy gốc → vị trí tập | Độc lập ảnh; chưa có thao tác chuyển vị trí lưu đã xác nhận |

## 4. Quy tắc và ngoại lệ

| Tình huống | Đã viết/kiểm gì | Phần còn phải hoàn thiện |
| --- | --- | --- |
| Bấm lại lập phiếu | Dùng request/hash, khóa nguồn và giới hạn lượng; nền GN10 đã có ca mất phản hồi thật | Chưa thay toàn bộ các lối cũ bằng một đường mới duy nhất |
| Bao25kg trả5kg | Nhận đúng5kg; bao vật lý0 hoặc1 theo thực tế, không dùng0.2bao; cách ly | Xử lý tiêu hủy/tái đóng gói hàng lẻ trong kho cách ly chưa hoàn thiện |
| Chưa thu tiền | Giảm khoản gốc, không tạo phiếu chi khống | Còn kiểm hồ sơ giảm giá trước đó |
| Thu một phần/đủ | Native giữ credit riêng khi cần; đối trừ đúng nguồn rồi chuẩn bị hoàn phần dư | Chưa có tổng quan thu/hoàn/chênh lệch trước khi bấm xác nhận trong một cửa sổ |
| Đổi sang mã khác | Nhập trả riêng, đơn thay riêng, không tự sinh lại mã cũ; giữ nguồn khi hủy/lập lại | Chưa tự nối phân bổ credit sang khoản mới hoặc hoàn chênh lệch trong một lượt |
| Giảm giá nợ đơn cũ | Từ Khách hàng mở đề nghị JE nháp theo khoản còn nợ; khóa nguồn/chống nhiều nháp | Giảm theo dòng/lượng, giảm sau đã trả tiền còn thiếu; đã viết chặn trả vượt phần còn lại sau giảm cho khoản một dòng, khoản nhiều dòng hoặc trả một phần sau giảm dừng để kế toán phân bổ |
| Mất mạng lâu | Quyết định cho người được giao quyền lập giấy tay đã có trong đặc tả | Chưa có sổ số giấy, nhập bù/liên kết duy nhất và trạng thái xử lý lệch hoàn chỉnh |
| Gom kho vệ tinh | Đã chặn dùng kho Vận chuyển làm nguồn bán | Chuẩn bị SE nháp/in trước xe đi, nhận thực lượng và gom vào cùng lượt giao còn thiếu |

## 5. Dữ liệu và trạng thái

Dữ liệu mới lưu trên chứng từ native, không tạo sổ kho/nợ hoặc DocType nhiệm vụ riêng. `kh_aph_mau_giao_nhan=1` phân biệt phiếu mới với lịch sử; không tự đổi thế hệ hay đánh dấu giấy cũ đã về.

| Dữ liệu | Nguồn và kiểm soát |
| --- | --- |
| Nhà xe, điện thoại, căn cứ chỉ định, yêu cầu ký cuối | Snapshot trên DN; sau ghi sổ không sửa trực tiếp; payload mới chặn ký tự khiến Frappe âm thầm lọc tên |
| Báo khách nhận | Nguồn Khách/Nhà xe báo, ngày nhận, user/time; nhận lại cùng yêu cầu không thay dấu hoặc ghi lại sổ |
| Nhận trả | Link DN và dòng gốc, lý do, request/hash, kg/bao/quy cách gốc; kiểm tổng lượng gồm cả nháp đang giữ |
| Đơn thay | Link phiếu nhận trả bất biến; khóa duy nhất cho đơn còn hiệu lực; hủy nhả khóa, giữ link lịch sử |
| Giấy gốc | User, thời điểm, vị trí lưu do API ghi; chưa có gốc khác với chưa có ảnh/ảnh chưa đối chiếu |
| Ảnh ký tại kho | Cơ chế file riêng tư và đối chiếu hiện có; lịch sử thay/xóa bằng chứng đầy đủ vẫn cần rà soát tiếp |
| Đối soát nợ ký theo lượt | Chưa có snapshot bất biến mới; mẫu theo ngày hiện có không thay được yêu cầu này |

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

| Ca | Bằng chứng đã đọc trước lượt mới | Kết luận giới hạn |
| --- | --- | --- |
| HTTP_014_TRA_LE_5KG | PASS UAT39578838909 |5kg cách ly,0bao, không ghi sổ lúc nháp, reserve/retry, giảm một lần |
| HTTP_014_TRA_LE_CHUA_THU_KHONG_HOAN | PASS cùng lượt | Chưa thu không chuẩn bị chi |
| HTTP_014_TRA_LE_THU_MOT_PHAN_HOAN_DUNG | PASS cùng lượt | Thu một phần/đủ, đối trừ và thực chi đúng nguồn, không tạo SI giảm lần nữa |
| HTTP_014_DOI_MA_MOI | PASS cùng lượt | Mã khác, một đơn thay, giữ nguồn, hủy/lập lại và giao mới |
| HTTP_014_XE_KHACH_CHI_DINH | PASS cùng lượt | Căn cứ chỉ định và nhận tại kho |
| HTTP_014_TRA_SAU_GIAM_CHAT_LUONG | Mới viết, chưa chạy native | Chặn trả cả giá gốc sau đã giảm chất lượng, kiểm giá trị còn lại và đề nghị giảm cũ chưa ghi |
| HTTP_014_NHA_XE_MOI_BAO_NHAN | Chưa PASS toàn ca ở lượt trên | Đã sửa lỗi lưu tên; cần kiểm lại đúng mã3b0219f |
| NATIVE_DESK_KHO_GIAO_NHAN_GON | Chưa tới ở lượt trên | Chưa coi thêm nhập nhà xe/nhận cuối/trảkg đã kiểm Chrome trên mã cuối |
| HTTP_014_NHAN_GIAY_GOC | Chưa tới ở lượt trên | API, danh sách thiếu gốc và Chốt ngày cần bằng chứng native |
| PDF A5 dữ liệu giả | Đã xem PDF tạo bằng Chrome |2trang khi không cần ký cuối,3trang khi có; chưa kiểm máy in thật |

Cục bộ516ca kh_aph,14 ca bỏ qua;108ca lõi đạt. Đây không phải số ca nghiệm thu nhân sự thật. Bộ014 kỳ vọng127PASS, phải đọc artifact và kiểm đúng SHA; giữ mọi lượt FAIL làm bằng chứng. Các ca chi tiết của toàn phạm vi trong các đặc tả không được tự đổi thành PASS chỉ vì bảng này có một phần đạt.

Bảng Chốt ngày hiện phụ thuộc cờ `kh_aph_factory_handover`; ca CI giấy gốc bật đúng schema rồi khôi phục cờ. Cần tách phụ thuộc này khi chuẩn hóa cấu hình Nhà máy độc lập.

## 9. Triển khai và khôi phục

PR38 vẫn nháp; app chưa tăng version, chủ dự án chưa gắn tag mới và production chưa đổi. Các mở rộng hiện dùng các cờ tính năng sẵn có; các cờ có mặc định tắt nhưng nhiều cờ đã bật ở production, nên không được tự nâng trước khi chốt đầy đủ phạm vi và bộ kiểm.

Schema đi qua bộ cài rõ ràng, không after_migrate. Giữ mã kỹ thuật/DocType, không đổi Company hay chế độ kế toán. Trước phát hành phải đủ cổng trên mã chốt, hồ sơ nghiệm thu và diễn tập bản sao production thực theo SOP; nâng trong tmux. Quay lui dùng image0.16.4 và snapshot ngay trước lần nâng mới, không restore xóa giao dịch phát sinh sau nâng mà chưa xử lý phần phát sinh.
