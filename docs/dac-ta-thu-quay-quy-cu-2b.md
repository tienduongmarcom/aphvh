# Thu quầy chống lặp và xác nhận quỹ nhà máy cũ — lát tiếp đợt 2B

## 1. Mục tiêu và phạm vi

Chặn thu khách hai lần khi gửi lại cùng cửa sổ thu quầy; chặn tự nhận/nhận thay ở phiếu quỹ nhà máy cũ. Chỉ là gia cố hai đường cũ, chưa phải adapter đầy đủ sang APH Ban giao tien, chưa mở quyền tiền cá nhân cho nhà máy.

## 2. Hiện trạng và nguồn

Kế thừa PR #13/2618e72, production vẫn 0.15.3. Thu quầy ở `kh_aph.ban_quay.thu_tien` tạo một PE mỗi hình thức, metadata người giữ từ PR #10. Quỹ cũ ở `kh_aph.factory_cash.xac_nhan_nhan` ghi một JE tiền–tiền khi nhận. Không tạo thêm sổ tiền hoặc nguồn thu mới.

## 3. Quy trình và trách nhiệm

Kế toán bán hàng mở Dialog Thu tiền; mỗi cửa sổ giữ một mã ngẫu nhiên, khóa nút khi đang gửi. Khi mất phản hồi, gửi lại nguyên cửa sổ trả đúng PE cũ. Khi đã đóng/mở lại hoặc tải lại trang, phải kiểm phiếu thu trước khi thu mới: không có cơ chế suy hai mã khác nhau là cùng khoản tiền mặt.

Nhà máy lập phiếu bàn giao cho người nhận khác người lập/người giữ. Chỉ đúng người được chỉ định nhận và đếm; quản lý/Administrator không được nhận thay. Quản lý xử lý chênh lệch theo hồ sơ và quyền sẵn có.

## 4. Quy tắc và ngoại lệ

Bật custody thì RPC quầy bắt buộc mã 16–64 ký tự chữ/số/gạch ngang; caller cũ phải bổ sung request_id. Mã có phạm vi người gọi + Company. Khóa Company xuyên suốt kiểm và ghi hai PE, retry toàn RPC khi xung đột DB; không commit giữa hai PE. Nội dung gồm company/khách/số tiền/hình thức/tài khoản/mã ngân hàng/danh sách hóa đơn theo thứ tự/ghi chú/người giữ. Cùng mã khác nội dung bị từ chối. Cùng mã có PE đã hủy cũng bị từ chối, không tự thu lại. Mã ngân hàng tiếp tục chống trùng dùng chung.

Nhà máy gửi lại đúng số đếm/tài khoản trên phiếu đã nhận có JE còn submitted trả kết quả cũ; khác nội dung/hủy JE bị chặn. Số lệch vẫn lưu chờ điều tra như trước; chưa nối vụ lệch cũ vào hồ sơ đối chiếu mới hoặc giữ chỗ theo người.

## 5. Dữ liệu và trạng thái

PE thêm hai Data ẩn/readonly/no_copy: kh_aph_luot_thu_quay (SHA256 người + company + token), kh_aph_noi_dung_thu_quay (SHA256 nội dung chuẩn hóa, tiền hai số lẻ). Hai PE cùng lượt mang cùng cặp dấu; số tiền/hóa đơn/người giữ vẫn trên nguồn PE. Server chỉ cho RPC tạo dấu, cấm giả/sửa/sao chép/xóa PE có dấu. Không backfill chứng từ cũ, không đoán người giữ từ owner. Owner chỉ dùng chặn người lập tự nhận.

## 6. Phân quyền và kiểm soát

Giữ cờ/role quầy; kiểm đọc Company/Customer trước tìm lượt; kiểm đọc PE trước trả lại. Không cấp GL cho nhà máy, không mở dữ liệu giá vốn. Phiếu nhà máy tiếp tục kiểm đọc phiếu và Company; không dùng role quản lý vượt người nhận. Lịch sử sửa/hủy native được giữ.

## 7. Tác động hệ thống

Thu khách chỉ PE native tạo GL/PLE và giảm nợ một lần; retry không ghi thêm. Nhận quỹ chỉ JE hai dòng tiền như trước, không giảm công nợ lần hai. Không ảnh hưởng kho/giá vốn/sản xuất/MISA, không tự cấn nợ cũ hay đổi company/bank.

## 8. Nghiệm thu kỹ thuật

Ca cũ vẫn phải đạt. Thêm HTTP: retry tiền mặt chuẩn hóa 31/31.00, đổi tiền/người giữ/mã thiếu bị chặn, hai phiên thu tiền mặt + chuyển khoản cùng mã chỉ hai PE và cùng kết quả; giả/sửa metadata bị chặn; hủy rồi retry không tái thu, không xóa dấu lịch sử. Bổ sung ca quỹ cũ: quản trị nhận thay/tự nhận bị chặn; nhận lại cùng lượng/tài khoản không đổi GL, thay lượng bị chặn. Chrome cố ý ngắt phản hồi HTTP200 sau commit, gửi lại cùng Dialog phải giữ đúng số PE/GL/PLE. Unit kiểm khóa trước tìm, quyền, replay, dấu giả, cờ tắt, quản lý nhận thay và retry nhà máy. Chỉ ghi đạt sau bốn cổng đúng SHA. Nghiệm thu nhân sự/dữ liệu/máy in thật để cuối theo anh Tiến.

## 9. Triển khai và khôi phục

Không thêm cờ; hai field PE cài rõ ràng trong cash_custody.schema (cờ22 mặc định tắt), không after_migrate. Quầy dùng mã khi custody bật; cờ tắt không đọc field mới. Không tăng version/tag/triển khai trong lát này. Khi phát hành cần đủ schema/caller đã nâng, diễn tập bản sao production và khôi phục image + DB/files/cờ theo runbook; không xóa dấu PE để xử lý lỗi. Bản quỹ cũ vẫn còn hạn chế nói trên nên chưa gọi đợt2B hoàn tất.

## Lỗi triển khai phát hiện khi kiểm

Cổng2b39192414323/db2201f: sau nâng cấp, probe200/pong rồi bước kéo image không tồn tại (đã dừng trước khi sửa gì) nhận503. Log có hai Gunicorn worker. Đối chiếu Frappe16.52.0 `app.py` gọi init với cached=True; config.py cache site_config trong RAM từng worker TTL60. Đổi maintenance bằng CLI không xóa cache trong các web process đang chạy. Sửa nang-cap.sh và trien_khai_frontend.sh: restart riêng backend sau cả bật/tắt bảo trì, trước sao lưu hoặc mở worker. Không clear/restart dữ liệu hay sửa core. Cổng2b tăng thêm20 probe bắt buộc200/pong ngay sau readiness (mỗi probe một lần, không retry/bỏ qua503), giữ nguyên assert kéo lỗi không gián đoạn web. Giữ run FAIL làm bằng chứng, chạy lại bốn cổng đúng SHA cuối. Khi mở bằng tay cũng phải nạp lại backend sau tắt bảo trì.
