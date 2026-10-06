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
echo "1/5 Sao lưu (CSDL + tệp) trước khi nâng cấp"
./erpctl exec -T backend bench --site frontend backup --with-files </dev/null
BK="$(./erpctl exec -T backend bash -c 'ls -t sites/frontend/private/backups/*-database.sql.gz | head -1' </dev/null | tr -d '\r')"
[ -n "$BK" ] || { echo "Không thấy bản sao lưu: dừng"; exit 1; }
for f in database.sql.gz files.tar private-files.tar site_config_backup.json; do
  b="${BK%-database.sql.gz}"; ./erpctl cp "backend:/home/frappe/frappe-bench/${b}-${f}" "sao-luu/$NGAY/" 2>/dev/null || true
done
printf '%s\n' "$CU" > "sao-luu/$NGAY/phien-ban-truoc.txt"
echo "2/5 Đổi phiên bản $CU -> $MOI"
sed -i "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$MOI/" .env
./erpctl pull
./erpctl up -d
sleep 20
echo "3/5 Migrate"
if ! ./erpctl exec -T backend bench --site frontend migrate; then
  echo "MIGRATE LỖI. Quay lui: ./quay-lui.sh $NGAY"; exit 3
fi
echo "4/5 Kiểm sau nâng cấp"
./erpctl cp khach.json backend:/tmp/khach.json
if ! ./erpctl exec -T backend bench --site frontend execute aphvh.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' | tee "sao-luu/$NGAY/kiem-sau-nang-cap.txt" | grep -q "KHÔNG ĐẠT: 0"; then
  echo "KIỂM KHÔNG ĐẠT. Xem sao-luu/$NGAY/kiem-sau-nang-cap.txt. Quay lui: ./quay-lui.sh $NGAY"; exit 4
fi
echo "5/5 == XONG: $CU -> $MOI, kiểm đạt. Bản sao lưu trước nâng cấp: sao-luu/$NGAY"
