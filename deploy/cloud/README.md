# Máy chủ chính thức (Google Cloud) — sao lưu tự động

Máy ảo `erpnext-prod` (asia-southeast1-a), frappe_docker, compose project `erpnext-clean`, site `frontend`.

## Thành phần

| Tệp | Đặt trên máy ảo | Việc |
|---|---|---|
| `erpnext-backup.sh` | `/usr/local/bin/erpnext-backup.sh` | `bench backup --with-files` rồi chép 4 tệp (CSDL, tệp công khai, tệp riêng, cấu hình site) lên bucket, thư mục `frontend/<ngày>_<giờ>/` giờ Việt Nam |
| `erpnext-backup.service`, `.timer` | `/etc/systemd/system/` | Chạy 02:30 và 12:30 giờ Việt Nam; máy tắt lúc đến giờ thì chạy bù khi bật |
| — | `/etc/erpnext-backup.conf` | `BUCKET=gs://<project-id>-erpnext-backup` |

Bucket: riêng tư (uniform access, chặn công khai), cùng vùng asia-southeast1, tự xóa bản cũ hơn 90 ngày.
Tài khoản dịch vụ của máy ảo chỉ có quyền thêm và đọc trên bucket (objectCreator + objectViewer), cần phạm vi
truy cập `storage-rw` trên máy ảo (đổi phạm vi phải tắt máy).

Bản sao lưu có `site_config_backup.json` chứa mật khẩu CSDL và `encryption_key` của site: giữ bucket riêng tư.

Frappe tự xóa bản sao lưu cục bộ cũ hơn 23 giờ mỗi lần sao lưu, nên lịch sử nằm trên bucket.

## Kiểm tra

```bash
systemctl list-timers erpnext-backup.timer --no-pager
sudo journalctl -u erpnext-backup.service -n 20 --no-pager -o cat
gcloud storage ls gs://<project-id>-erpnext-backup/frontend/
```

## Khôi phục (về 8081 hoặc máy mới)

```bash
gcloud storage cp -r gs://<project-id>-erpnext-backup/frontend/<ngày>_<giờ>/ .
# rồi bench --site <site> restore <database.sql.gz> --with-public-files <files.tar> --with-private-files <private-files.tar>
```

Site mới khôi phục từ bản cloud dùng được ngay nếu không có dữ liệu mã hóa; khi đã có (mật khẩu email, API…)
phải chép `encryption_key` từ `site_config_backup.json` sang site_config.json của site đích.
