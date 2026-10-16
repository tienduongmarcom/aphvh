# Đổi nguồn phần chưa giao — ứng viên đang kiểm thử

Không dùng cho frontend trước khi cùng SHA CI xanh. Phần native API: giảm lượng nguồn cũ qua update_child_qty_rate, giữ lại đã giao, tạo nguồn mới riêng company và snapshot bao. Chuyển hết một SO chưa giao dùng trạng thái Closed, giữ tên/row lịch sử; mở lại phải qua hủy coordinator. Khóa SO khi xuất để chống phiếu nháp lấy trước thay đổi nguồn. Snapshot audit không có giá. Native cancellation vẫn chặn target đã xuất/ghi nợ.

HTTP UAT thử profile NoCost + Sales Manager, 75kg/3bao đã giao 25kg/1bao chuyển 50kg/2bao APH→VH; kiểm reserved_qty, stale DN, source stock/debt, ba số và đảo theo thứ tự. UI đã có chọn dòng/kg/kho/lý do nhưng chưa smoke Chrome cho luồng source. Full move/closed, nhiều dòng/xâu source-change và stress cần bổ sung trước đóng gate production.
