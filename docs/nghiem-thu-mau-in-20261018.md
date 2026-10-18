# Nghiệm thu mẫu in — 18/10/2026

Mã ứng viên: `7c2217e8737e96700fa050aac446bb3591a830a8`, PR #5. Production hiện là 0.15.2; chỉ kiểm mẫu mới trên môi trường UAT đã cài ứng viên. Không tạo chứng từ thử trên production. Các dòng dưới **chưa nghiệm thu máy in/người dùng thật**.

Người thực hiện: kế toán bán hàng kiểm phiếu nhanh; kế toán kho kiểm thực giao và hai liên; kế toán tổng hợp kiểm thu/chi; kế toán trưởng kiểm chế độ biểu mẫu và quyền. Ghi tên người kiểm, ngày, máy in, phiên bản và kết quả thực tế cho từng dòng.

| Ca | Đầu vào và thao tác | Kết quả cần đạt | Thực tế |
|---|---|---|---|
| IN01 | Đơn chung có phiếu giao nháp APH, in nhanh trên giấy A5 ngang, tỷ lệ 100% | Đủ liên Lưu kho/Giao nhận; tên/mã hàng, kg và bao khi có, giá bán thuần, thành tiền/bằng chữ, năm ô ký đọc được; cột thực xuất trống; có dấu CHỜ XUẤT | Chưa kiểm |
| IN02 | Phiếu đã xác nhận giao, mở lại bản in nhanh | Lượng thực xuất đúng phiếu; đúng người thực giao và thời điểm; có dấu bản sao; không tạo thêm phiếu hay ghi sổ lần nữa | Chưa có nút mở riêng A5 từ DN đã lưu; chờ bổ sung trước kiểm máy in |
| IN03 | Phiếu nhiều dòng, tên hàng/địa chỉ dài, in A5 ngang | Tự sang trang khi cần, lặp tiêu đề bảng, không mất dòng/cắt chữ hoặc tách khối ký; hai liên vẫn phân biệt được | Chưa kiểm |
| IN04 | In Phiếu nhập kho và Phiếu xuất kho bán hàng APH/VH trên A4 | APH ghi TT133, VH ghi TT99; mẫu điều chỉnh ghi vận dụng; đủ kho, đối tượng, Nợ/Có, yêu cầu/thực tế, đơn vị tính và ô ký; các phần giá theo quyền/nghiệp vụ hiện hành | Chưa kiểm |
| IN05 | In Phiếu thu chi tiền mặt của APH/VH | Đúng chiều thu/chi, người nộp/nhận, số tiền, tiền chữ, quyển số, chứng từ kèm và năm vị trí ký; không sai company/quỹ | Chưa kiểm |
| IN06 | In mẫu của Minh Khang và TL | Minh Khang là mẫu nội bộ hộ kinh doanh, có căn cứ chế độ TT152; TL là mẫu quản trị nội bộ; không gán số mẫu doanh nghiệp cho hai đơn vị này | Chưa kiểm |
| IN07 | In chuẩn/in lại Biên bản giao nhận từ phiếu có thông tin giao nhận mới, rồi từ phiếu cũ hoặc phiếu trả | Phiếu mới dùng đúng người nhận, điện thoại, lái xe, biển số, người giao và thời điểm đã lưu; phiếu cũ/phiếu trả giữ thông tin phù hợp nguồn; biên bản đủ hai liên | Chưa kiểm |
| IN08 | In tổng hợp nhiều DN của nhiều company, người nhận khác nhau | Mỗi DN có khối người giao–nhận riêng, đúng company/kho/lượng; không gộp người nhận hoặc lộ giá vốn | Chưa kiểm |
| IN09 | Người bị cấm xem giá vốn thử in; người ngoài phạm vi thử mở phiếu công ty khác | Quyền vẫn chặn đúng như ứng viên đã kiểm; không dùng Administrator thay cho kiểm tài khoản nhân sự | Chưa kiểm |

Khi có lỗi, lưu ảnh/PDF và số phiếu UAT, ghi rõ expected/actual rồi sửa và kiểm lại đúng ca. Không kết luận đạt toàn bộ từ bản PDF mẫu hoặc số bài tự động.

Quy chế biểu mẫu tại `docs/quy-che-bieu-mau-chung-tu.md` vẫn là dự thảo để doanh nghiệp ban hành. Nghiệm thu mẫu không thay cho diễn tập nâng cấp trên bản sao production ngay trước triển khai.
