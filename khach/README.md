# Thư mục khách hàng

Mỗi khách một thư mục `khach/<ten>/`:

- `khach.json`: cấu hình (công ty, thông tư, kho, nhà máy, `che_do_du_lieu`, `ngay_chot`).
- `phien-ban.yaml`: phiên bản image đang chạy và môi trường.

Cổng 2 (`.github/workflows/cong-2-site-trang.yml`) tự chạy cho MỌI thư mục có `khach.json`:
dựng site trắng theo cấu hình rồi chạy bộ kiểm. Thêm khách mới = thêm thư mục, không sửa workflow.
