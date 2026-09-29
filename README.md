# aphvh — tùy biến ERPNext cho An Phú Hưng và Vĩnh Hưng

App riêng chạy trên ERPNext v16. Bản 0.1 chỉ làm một việc ERPNext không tự làm được:
**chia giá thành phẩm theo kg cho phiếu sản xuất có nhiều đầu ra.**

## Bản 0.1 làm gì

| Thành phần | Nội dung |
|---|---|
| Loại phiếu kho **"Đóng gói theo kg"** | Mục đích Repack. Một phiếu được có nhiều thành phẩm. |
| Chia giá theo kg | Tổng giá đầu vào (theo sổ kho, bình quân) chia cho các dòng thành phẩm theo số kg. Phần lẻ làm tròn dồn vào dòng nhiều kg nhất. |
| Quy đổi kg | Mã tồn kho bằng **Kg**: hệ số 1. Mã tồn kho bằng đơn vị khác (Thùng…): lấy **Trọng lượng/đơn vị** và **Đơn vị trọng lượng = Kg** trên mã hàng. |
| Lưu trên chứng từ | Phiếu lưu mã quy tắc `kg-v1`; mỗi dòng lưu `Kg / ĐVT tồn kho` và `Số kg tính giá` lúc lưu/gửi. |
| Tính lại giá (repost) | Khi chi phí nhập khẩu đổi hoặc có chứng từ lùi ngày, ERPNext tính lại phiếu theo quy tắc và số kg **đã lưu**, không đọc lại trọng lượng hiện tại trên mã hàng. |

Phiếu kho loại khác, và công ty không dùng loại phiếu này, giữ nguyên hành vi chuẩn của ERPNext.

**Chưa hỗ trợ ở bản 0.1** (phiếu sẽ báo lỗi): phụ phẩm định giá riêng, chi phí cộng thêm
trên phiếu, dòng vừa có kho nguồn vừa có kho đích.

## Mở rộng về sau

- Quy tắc mới (ví dụ phụ phẩm tính theo giá trị thuần có thể thực hiện được) = mã quy tắc mới
  trong `constants.py` + hàm mới trong `costing_rules.py`. Phiếu cũ giữ `kg-v1`.
- Báo cáo (đối chiếu 1381, giá về kho theo lô, tỷ lệ thu hồi) đọc dữ liệu đã có, không cần
  sửa chứng từ cũ, miễn là chứng từ đã gắn chiều phân tích "Lô nhập khẩu".

## Cấu trúc

```
aphvh/
  hooks.py            khai báo extend_doctype_class, after_install, after_migrate
  constants.py        tên loại phiếu, mã quy tắc, đơn vị Kg
  costing_rules.py    phép chia thuần (kiểm thử không cần Frappe)
  stock_entry_kg.py   lớp mở rộng Stock Entry
  install.py          custom field + loại phiếu (chạy lại được nhiều lần)
  tests/              kiểm thử đơn vị
Dockerfile            dựng bản cài ERPNext kèm app
```

## Dựng và cài (Docker, theo cấu hình pwd.yml)

```bash
# 1. Lấy mã nguồn đúng phiên bản đã nghiệm thu
git clone git@github.com:<chu-so-huu>/aphvh.git && cd aphvh && git checkout v0.1.0

# 2. Dựng bản cài (tự chạy kiểm thử đơn vị trong lúc dựng)
docker build -t aphvh-erpnext:0.1.0 .

# 3. Trong tệp compose, đổi mọi dòng "image: frappe/erpnext:v16.36.0" thành
#    "image: aphvh-erpnext:0.1.0", rồi khởi động lại (configurator tự cập nhật apps.txt)
docker compose -p <du-an> -f <tep-compose> up -d

# 4. Cài app vào site
docker exec <du-an>-backend-1 bench --site frontend install-app aphvh
```

Sao lưu site trước bước 3. Gỡ app: `bench --site frontend uninstall-app aphvh`
(phiếu đã gửi vẫn giữ nguyên giá trị trên sổ).

## Kiểm thử

```bash
python -m unittest aphvh.tests.test_costing_rules -v
```
