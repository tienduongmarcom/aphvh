# Ứng viên 0.15.2 — giao nhận và kiểm soát tiền

Đích: site `frontend`, VM `erpnext-prod`, Compose `~/erp/aph-vh`. Bản đang chạy: 0.15.1, digest `sha256:c4b61eb4b2924d50f64bbeaf83623da3e7259f9484b28d6f3e228939912edf47`. Chưa phát hành image 0.15.2 hoặc triển khai production.

## Phạm vi

- Hồ sơ bản ký riêng tư trên phiếu giao hàng, ghi chú và dấu đối chiếu; đổi hồ sơ phải đối chiếu lại. Chặn xóa tệp đang được dùng. Có hàng đợi thiếu bản ký/chưa đối chiếu.
- Kiểm quyền và số thực nhận khi bàn giao quỹ nhà máy; chặn sửa tay kết quả nhận hoặc gắn bút toán có sẵn.
- Chống dùng trùng mã giao dịch giữa phiếu thu/chi chuẩn, bút toán và tiền thực thu/cọc, cả khi hai phiên nhập đồng thời. Sao kê kiểm quyền tệp và quyền lưu mẫu ngân hàng.
- Giới hạn báo cáo/thao tác tài chính theo công ty được cấp. Hồ sơ không xem giá vốn vẫn bị chặn khi cộng vai trò kế toán.
- Đồng nhất tổng phải thanh toán có VAT với hóa đơn; không đếm lại phần đổi nguồn của đơn đã đóng. Chuỗi cọc–giao từng phần–nhận/bản ký–thu nốt không tự cấn nợ cũ.

## Cài đặt và ảnh hưởng

Không đổi nền: ERPNext 16.51.1/Frappe 16.52.0, lab9x 0.2.10. Không thêm cờ, dùng 21 cờ hiện có. Chạy migrate và bộ cài chuẩn để thêm/cập nhật các ô hồ sơ giao nhận, quyền và Workspace. JS được đóng trong image và nạp bằng hook; không cần thao tác build riêng trên máy chủ. Bộ nâng cấp thay đồng bộ các service để nạp mã mới. Không sửa core hoặc tự điều chỉnh số dư/sổ lịch sử.

## Bằng chứng

Trước khi đổi nhãn phiên bản: mã `267ce9f64df9cb5cc124f194f8e8d5bba888778c` đủ bốn cổng (UAT39020061567, Cổng239020065621, Cổng2b39020061544, Cổng339020061545). Mốc nghiệp vụ `96ce98d` có 375 unit đạt và artifact UAT215 PASS/0 FAIL. Ứng viên 0.15.2 phải đọc CI theo đúng SHA mới; các kết quả trước không thay cho kiểm bản đóng gói.

## Phát hành và triển khai

Chủ dự án gắn tag `v0.15.2` vào đúng SHA ứng viên sau khi bốn cổng xanh. Workflow “Phát hành image” chạy lại các cổng, rồi mới đẩy image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.2`. Không ghi đè tag cũ. Chỉ dùng hướng dẫn dưới khi image phát hành đã đạt, biết digest và checkout đúng tag.

Trên VM, trong phiên SSH đang dùng (không chạy trên máy Mac):

```bash
cd ~/trien-khai
git fetch origin tag v0.15.2
git checkout --detach v0.15.2
bash deploy/release/dien_tap_ban_sao.sh 0.15.2
```

Chỉ khi diễn tập báo ĐẠT, mới chạy:

```bash
bash deploy/release/trien_khai_frontend.sh 0.15.2
```

Không thêm cờ. Người dùng dừng nhập dữ liệu trong cửa sổ triển khai. Bộ triển khai bật bảo trì trước sao lưu, so số lượng/tổng/chi tiết và chỉ mở lại khi đạt. Với dữ liệu danh mục mới nhập, diễn tập bản sao trên VM là bắt buộc; CI dùng dữ liệu giả lập không thay cho bước này.

Nếu lỗi, dừng tại lỗi và giữ bảo trì; dùng thư mục sao lưu/lệnh quay lui được script in ra. Không chạy lại mù hoặc mở nhập liệu. Sau khi đã mở nhập liệu, không tự phục hồi backup làm mất giao dịch mới.

## Sau triển khai

Xác nhận log `=== XONG 0.15.2: ĐẠT ===`, digest và phiên bản service; cập nhật `phien-ban.yaml` theo log thực tế. Mở Desk và kiểm các phiếu/danh mục hiện có. Gom nghiệm thu với nhân sự, dữ liệu và máy in theo `docs/nghiem-thu-tong-the.md`; chưa xác nhận toàn bộ 202 quyết định.
