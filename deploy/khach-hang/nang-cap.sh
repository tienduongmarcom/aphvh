#!/usr/bin/env bash
# Nâng cấp một khách lên phiên bản image mới, có sao lưu trước và kiểm sau. Chạy trong thư mục của khách.
# Dùng: ./nang-cap.sh <phien-ban-moi>
set -euo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
MOI="${1:?phiên bản mới}"
set -a; source .env; set +a
CU="$CUSTOM_TAG"
[ "$CU" = "$MOI" ] && { echo "Đã ở phiên bản $MOI"; exit 0; }
NGAY="$(date +%Y%m%d-%H%M%S)"
mkdir -p "sao-luu/$NGAY"
# Chốt chặn an toàn: lỗi sau khi đổi phiên bản thì tự quay lui (khôi phục bản sao lưu), rồi báo mã lỗi.
# Tắt tự quay lui: TU_QUAY_LUI=0 ./nang-cap.sh <phien-ban>
# Chụp snapshot ổ đĩa VM trước khi nâng cấp (tùy nhà cung cấp cloud): đặt SNAPSHOT_CMD, ví dụ
#   SNAPSHOT_CMD='gcloud compute disks snapshot erp-khach --snapshot-names pre-$MOI' ./nang-cap.sh 0.7.0
TU_QUAY_LUI="${TU_QUAY_LUI:-1}"
if [ -n "${SNAPSHOT_CMD:-}" ]; then echo "0/5 Snapshot VM"; MOI="$MOI" bash -c "$SNAPSHOT_CMD" || { echo "Snapshot lỗi: dừng, chưa đổi gì"; exit 1; }; fi
# 0.14.3: CHẾ ĐỘ BẢO TRÌ suốt sao lưu → đổi image → migrate → kiểm. Người dùng không ghi được gì nên bản sao lưu là trạng thái
# cuối cùng: tự quay lui không làm mất giao dịch. Worker + lịch chạy dừng (không chạy việc nền bằng code mới trên CSDL chưa migrate).
# Đạt thì mở lại, trừ khi GIU_BAO_TRI=1 (trien_khai_frontend.sh còn bước sau, tự mở lại khi xong).
# Lỗi sau khi đã bật bảo trì: GIỮ bảo trì để kiểm; mở bằng tay: ./erpctl exec -T backend bench --site frontend set-maintenance-mode off
#   && ./erpctl restart backend && ./erpctl exec -T backend bench --site frontend scheduler resume && ./erpctl up -d
ex() { ./erpctl exec -T backend bench --site frontend "$@" </dev/null; }
bat_bao_tri() {
  ex set-maintenance-mode on
  # Frappe16.52 giữ site_config trong RAM từng web worker 60 giây.
  # CLI đổi file không xóa cache của worker đang chạy; nạp lại trước bước tiếp.
  ./erpctl restart backend
  ex scheduler pause
  ./erpctl stop queue-short queue-long scheduler
}
mo_lai() {
  ex set-maintenance-mode off
  # Frappe16.52 giữ site_config trong RAM từng web worker 60 giây.
  # CLI đổi file không xóa cache của worker đang chạy; nạp lại trước bước tiếp.
  ./erpctl restart backend
  ex scheduler resume
  ./erpctl up -d
}
giu_bao_tri() { echo "!!! SITE ĐANG Ở CHẾ ĐỘ BẢO TRÌ (người dùng chưa vào được). Kiểm xong rồi mở lại:"
  echo "    cd $(pwd) && ./erpctl exec -T backend bench --site frontend set-maintenance-mode off && ./erpctl restart backend && ./erpctl exec -T backend bench --site frontend scheduler resume && ./erpctl up -d"; }
quay_lui() {
  echo "$1"
  if [ "$TU_QUAY_LUI" = 1 ]; then echo "TỰ QUAY LUI về $CU..."; ./quay-lui.sh "$NGAY" --tu-dong && echo "Đã quay về $CU. Xem lỗi ở trên, KHÔNG nâng cấp lại tới khi sửa." || echo "QUAY LUI CŨNG LỖI: gọi người hỗ trợ ngay, bản sao lưu ở sao-luu/$NGAY"
  else echo "Quay lui bằng tay: ./quay-lui.sh $NGAY"; fi
  giu_bao_tri
}
IMG_MOI="${CUSTOM_IMAGE:-frappe/erpnext}:$MOI"
echo "0/5 Kéo trước image $IMG_MOI (chưa đổi gì, người dùng vẫn làm việc)"
docker image inspect "$IMG_MOI" >/dev/null 2>&1 || docker pull "$IMG_MOI" || { echo "KÉO IMAGE $MOI LỖI. Chưa đổi gì."; exit 2; }
echo "1/5 Bật chế độ bảo trì, dừng worker + lịch chạy, sao lưu (CSDL + tệp)"
bat_bao_tri
ex backup --with-files
BK="$(./erpctl exec -T backend bash -c 'ls -t sites/frontend/private/backups/*-database.sql.gz | head -1' </dev/null | tr -d '\r')"
[ -n "$BK" ] || { echo "Không thấy bản sao lưu: dừng, mở lại site"; mo_lai; exit 1; }
b="${BK%-database.sql.gz}"
for f in database.sql.gz files.tar private-files.tar site_config_backup.json; do
  ./erpctl exec -T backend cat "/home/frappe/frappe-bench/${b}-${f}" </dev/null > "sao-luu/$NGAY/$(basename "$b")-$f" \
    && [ -s "sao-luu/$NGAY/$(basename "$b")-$f" ] \
    || { echo "THIẾU / RỖNG thành phần sao lưu: $f — dừng, chưa đổi phiên bản, mở lại site"; mo_lai; exit 1; }
done
gzip -t "sao-luu/$NGAY/$(basename "$b")-database.sql.gz" || { echo "Bản sao lưu CSDL hỏng — dừng, mở lại site"; mo_lai; exit 1; }
tar -tf "sao-luu/$NGAY/$(basename "$b")-files.tar" >/dev/null && tar -tf "sao-luu/$NGAY/$(basename "$b")-private-files.tar" >/dev/null \
  || { echo "Tệp đính kèm sao lưu hỏng — dừng, mở lại site"; mo_lai; exit 1; }
python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "sao-luu/$NGAY/$(basename "$b")-site_config_backup.json" \
  || { echo "site_config sao lưu hỏng — dừng, mở lại site"; mo_lai; exit 1; }
( cd "sao-luu/$NGAY" && sha256sum ./*-database.sql.gz ./*.tar ./*-site_config_backup.json > sha256.txt )
ls -l "sao-luu/$NGAY"
printf '%s\n' "$CU" > "sao-luu/$NGAY/phien-ban-truoc.txt"
echo "2/5 Đổi phiên bản $CU -> $MOI"
sed -i.bak "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$MOI/" .env && rm -f .env.bak
# Kéo image mới lỗi (tag không có, mạng, quyền ghi ghcr) thì CHƯA migrate gì: chỉ trả phiên bản về như cũ, không cần khôi phục dữ liệu.
if ! ./erpctl pull; then
  sed -i.bak "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$CU/" .env && rm -f .env.bak; mo_lai
  echo "KÉO IMAGE $MOI LỖI. Đã giữ nguyên phiên bản $CU, dữ liệu không bị đổi."; exit 2
fi
# Chỉ dựng lại phần web (vẫn bảo trì); worker + lịch chạy để dừng tới khi migrate + kiểm xong.
./erpctl up -d configurator backend frontend websocket
./erpctl stop queue-short queue-long scheduler >/dev/null 2>&1 || true
sleep 20
echo "3/5 Migrate"
# Từ 0.7.0 lõi 9xLab (lab9x) là app riêng: site cũ chưa cài thì cài trước khi migrate (chạy lại được).
if ! ./erpctl exec -T backend bench --site frontend list-apps </dev/null | grep -q '^lab9x'; then
  ./erpctl exec -T backend bench --site frontend install-app lab9x </dev/null || { quay_lui "CÀI LÕI lab9x LỖI."; exit 3; }
fi
if ! ./erpctl exec -T backend bench --site frontend migrate </dev/null; then
  quay_lui "MIGRATE LỖI."; exit 3
fi
echo "4/5 Kiểm sau nâng cấp"
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
if ! ./erpctl exec -T backend bench --site frontend execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' </dev/null | tee "sao-luu/$NGAY/kiem-sau-nang-cap.txt" | grep -q "KHÔNG ĐẠT: 0"; then
  quay_lui "KIỂM KHÔNG ĐẠT. Xem sao-luu/$NGAY/kiem-sau-nang-cap.txt."; exit 4
fi
if [ "${GIU_BAO_TRI:-0}" = 1 ]; then
  echo "5/5 == XONG: $CU -> $MOI, kiểm đạt. VẪN BẢO TRÌ (người gọi tự mở lại). Bản sao lưu trước nâng cấp: sao-luu/$NGAY"
else
  mo_lai
  echo "5/5 == XONG: $CU -> $MOI, kiểm đạt, đã mở lại site. Bản sao lưu trước nâng cấp: sao-luu/$NGAY"
fi
