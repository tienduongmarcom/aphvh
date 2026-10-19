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

## Kết quả chốt 19/10/2026

Mã ứng viên/kiểm **c02c3764dae495a48b564931062cbae3e78d9db3**, PR #14. 365 kh_aph +108 lab9x cục bộ đạt; Python/JS/shell/diff đạt. Cả bốn cổng success trên cùng SHA: [2](https://github.com/tienduongmarcom/aphvh/actions/runs/39195670324), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39195680580), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39195678186), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39195684243). Đã tải/đọc artifact cuối: 263 HTTP/Desk PASS/0FAIL, b01472; core63.508 tệp không đổi, fresh setup idempotent. Đã xem thu-quay.png có toast phiếu thu, kiểm mất HTTP200 sau commit rồi gửi lại cùng Dialog chỉ một PE, GL/PLE không tăng lần nữa. ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11.

Cổng2b qua20 probe nghiêm, image lỗi không đổi bản đang chạy, khôi phục ci-b vềci-a. Cổng3: nâng/site mới1065/1065 lệch0, bỏ qua6/6; rollback1052/1052 khớp đếm/tổng/cờ/versions/cài đặt/giao diện, ba cờ tiền mới về0. Cố ý lỗi tự khôi phục, so chi tiết/versions khớp, maintenance_mode=1. Nền CI GL0: vẫn cần diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL và nguyên nhân: UAT39190026643/a6fae60 do finally không có trên jqXHR (đã sửa always); Cổng2b39192414323/db2201f do cache bảo trì từng worker (đã sửa restart backend); UAT39193896826/b7 cả263 ca parsedPASS nhưng grep thiếu dòng Chrome compactJSON (đã chuẩn hóa qua emit và assert đúng một case PASS, giữ nguyên số72 và điều kiện kiểm). Các run hủy khi đổi mã/trùng không là bằng chứng cuối.

Nguồn Frappe16.52.0 đã đối chiếu: [request.js trả jqXHR/always](https://github.com/frappe/frappe/blob/v16.52.0/frappe/public/js/frappe/request.js#L309), [request init](https://github.com/frappe/frappe/blob/v16.52.0/frappe/app.py#L217), [cached=is_request](https://github.com/frappe/frappe/blob/v16.52.0/frappe/__init__.py#L200), [cache site_config TTL60 trong RAM](https://github.com/frappe/frappe/blob/v16.52.0/frappe/config.py#L149). Không sửa core.

Chưa phát hành/triển khai hoặc nghiệm thu nhân sự, dữ liệu và máy in thật. Adapter đầy đủ quỹ nhà máy, tiền cá nhân không GL và bảng chốt ngày còn tiếp; không đánh dấu toàn đợt2B hoàn tất.
