# Thư mục khách hàng

Mỗi khách một thư mục `khach/<ten>/`:

- `khach.json`: cấu hình (công ty, thông tư / hộ kinh doanh / đơn vị nội bộ, `loai_hinh`, `che_do_du_lieu`, `ngay_chot`).
  Không có mục kho: khách tự tạo cây kho trên giao diện (từ 0.8.0).
- `phien-ban.yaml`: phiên bản image đang chạy và môi trường.

Cổng 2 (`.github/workflows/cong-2-site-trang.yml`) tự chạy cho MỌI thư mục có `khach.json`:
dựng site trắng theo cấu hình rồi chạy bộ kiểm. Thêm khách mới = thêm thư mục, không sửa workflow.
