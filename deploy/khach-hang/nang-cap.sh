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
quay_lui() {
  echo "$1"
  if [ "$TU_QUAY_LUI" = 1 ]; then echo "TỰ QUAY LUI về $CU..."; ./quay-lui.sh "$NGAY" --tu-dong && echo "Đã quay về $CU. Xem lỗi ở trên, KHÔNG nâng cấp lại tới khi sửa." || echo "QUAY LUI CŨNG LỖI: gọi người hỗ trợ ngay, bản sao lưu ở sao-luu/$NGAY"
  else echo "Quay lui bằng tay: ./quay-lui.sh $NGAY"; fi
}
echo "1/5 Sao lưu (CSDL + tệp) trước khi nâng cấp"
./erpctl exec -T backend bench --site frontend backup --with-files </dev/null
BK="$(./erpctl exec -T backend bash -c 'ls -t sites/frontend/private/backups/*-database.sql.gz | head -1' </dev/null | tr -d '\r')"
[ -n "$BK" ] || { echo "Không thấy bản sao lưu: dừng"; exit 1; }
for f in database.sql.gz files.tar private-files.tar site_config_backup.json; do
  b="${BK%-database.sql.gz}"; ./erpctl cp "backend:/home/frappe/frappe-bench/${b}-${f}" "sao-luu/$NGAY/" 2>/dev/null || true
done
printf '%s\n' "$CU" > "sao-luu/$NGAY/phien-ban-truoc.txt"
echo "2/5 Đổi phiên bản $CU -> $MOI"
sed -i.bak "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$MOI/" .env && rm -f .env.bak
# Kéo image mới lỗi (tag không có, mạng, quyền ghi ghcr) thì CHƯA migrate gì: chỉ trả phiên bản về như cũ, không cần khôi phục dữ liệu.
if ! ./erpctl pull; then
  sed -i.bak "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$CU/" .env && rm -f .env.bak; ./erpctl up -d
  echo "KÉO IMAGE $MOI LỖI. Đã giữ nguyên phiên bản $CU, dữ liệu không bị đổi."; exit 2
fi
./erpctl up -d
sleep 20
echo "3/5 Migrate"
# Từ 0.7.0 lõi 9xLab (lab9x) là app riêng: site cũ chưa cài thì cài trước khi migrate (chạy lại được).
if ! ./erpctl exec -T backend bench --site frontend list-apps </dev/null | grep -q '^lab9x'; then
  ./erpctl exec -T backend bench --site frontend install-app lab9x </dev/null || { quay_lui "CÀI LÕI lab9x LỖI."; exit 3; }
fi
if ! ./erpctl exec -T backend bench --site frontend migrate; then
  quay_lui "MIGRATE LỖI."; exit 3
fi
echo "4/5 Kiểm sau nâng cấp"
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
if ! ./erpctl exec -T backend bench --site frontend execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' | tee "sao-luu/$NGAY/kiem-sau-nang-cap.txt" | grep -q "KHÔNG ĐẠT: 0"; then
  quay_lui "KIỂM KHÔNG ĐẠT. Xem sao-luu/$NGAY/kiem-sau-nang-cap.txt."; exit 4
fi
echo "5/5 == XONG: $CU -> $MOI, kiểm đạt. Bản sao lưu trước nâng cấp: sao-luu/$NGAY"
