#!/usr/bin/env bash
# Dựng hệ thống cho MỘT khách trên máy này (Docker đã cài, đã docker login ghcr.io nếu image riêng tư).
# Dùng:  ./dung.sh <ten-khach-viet-lien> <phien-ban-image> <duong-dan-cau-hinh.json> [ten-mien]
# Ví dụ: ./dung.sh aph-vh 0.6.2 ./khach.json erp.congty.vn
# Biến môi trường tùy chọn: CUSTOM_IMAGE (mặc định ghcr.io/tienduongmarcom/kh-aph-erpnext), HTTP_PORT (mặc định 80), HTTP_BIND (mặc định 0.0.0.0)
set -euo pipefail
umask 077
KHACH="${1:?tên khách}"; TAG="${2:?phiên bản image}"; CFG="${3:?file cấu hình khách}"; DOMAIN="${4:-}"
[[ "$KHACH" =~ ^[a-z0-9-]+$ ]] || { echo "Tên khách chỉ gồm chữ thường, số, gạch ngang"; exit 1; }
[ -f "$CFG" ] || { echo "Không thấy $CFG"; exit 1; }
KHUON="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DIR="${ERP_HOME:-$HOME/erp}/$KHACH"
[ -e "$DIR/.env" ] && { echo "Đã có $DIR/.env: khách này đã dựng. Dùng nang-cap.sh để nâng cấp."; exit 1; }
mkdir -p "$DIR/sao-luu"
cp -r "$KHUON/compose.yaml" "$KHUON/overrides" "$KHUON/erpctl" "$KHUON/nang-cap.sh" "$KHUON/quay-lui.sh" "$DIR/"
cp "$CFG" "$DIR/khach.json"
DBPASS="$(python3 -c 'import secrets;print(secrets.token_hex(24))')"
cat > "$DIR/.env" <<EOF
PROJECT=erp-$KHACH
CUSTOM_IMAGE=${CUSTOM_IMAGE:-ghcr.io/tienduongmarcom/kh-aph-erpnext}
CUSTOM_TAG=$TAG
MARIADB_IMAGE=mariadb:11.8
REDIS_IMAGE=redis:8.6-alpine
PULL_POLICY=${PULL_POLICY:-always}
RESTART_POLICY=unless-stopped
GUNICORN_WORKERS=2
GUNICORN_THREADS=4
HTTP_BIND=${HTTP_BIND:-0.0.0.0}
HTTP_PORT=${HTTP_PORT:-80}
DB_PASSWORD=$DBPASS
DOMAIN=$DOMAIN
ERP_HTTPS=$([ -n "$DOMAIN" ] && echo 1 || echo 0)
EOF
chmod 600 "$DIR/.env"
cd "$DIR"
# Mật khẩu Administrator: nhập tay (không in ra, không lưu trong lịch sử lệnh)
if [ -t 0 ]; then
  read -r -s -p "Mật khẩu Administrator mới: " AP; echo; read -r -s -p "Nhập lại: " AP2; echo
  [ "$AP" = "$AP2" ] && [ ${#AP} -ge 10 ] || { echo "Không khớp hoặc ngắn hơn 10 ký tự"; exit 1; }
else
  AP="$(python3 -c 'import secrets;print(secrets.token_urlsafe(18))')"; printf '%s\n' "$AP" > "$DIR/admin-password.txt"
  echo "Không có bàn phím: đã tạo mật khẩu Administrator ngẫu nhiên trong $DIR/admin-password.txt (đổi ngay sau khi vào)"
fi
./erpctl up -d
echo "Chờ dịch vụ sẵn sàng..."
for i in $(seq 1 60); do
  [ "$(./erpctl ps --format '{{.Service}} {{.Health}}' 2>/dev/null | grep -c '^backend healthy' || true)" = 1 ] && break
  sleep 5
done
set -a; source .env; set +a
AP="$AP" ./erpctl exec -T -e AP backend bash -c 'bench new-site frontend --mariadb-user-host-login-scope="172.%.%.%" --db-root-username root --db-root-password "'"$DB_PASSWORD"'" --admin-password "$AP" --install-app erpnext --install-app lab9x --install-app kh_aph'
unset AP AP2
./erpctl exec -T backend bench --site frontend enable-scheduler
# hostname -I chỉ có trên Linux: máy khác (macOS khi diễn tập) dùng localhost kèm cổng
if [ -n "$DOMAIN" ]; then HOST="https://$DOMAIN"
else
  IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"; [ -n "$IP" ] || IP=localhost
  HOST="http://$IP"; [ "${HTTP_PORT:-80}" = 80 ] || HOST="$HOST:${HTTP_PORT}"
fi
./erpctl exec -T backend bench --site frontend set-config host_name "$HOST"
# nạp cấu hình khách rồi kiểm
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
./erpctl exec -T backend bench --site frontend execute kh_aph.khach_hang.ap_dung --kwargs '{"duong_dan": "/tmp/khach.json"}'
./erpctl exec -T backend bench --site frontend execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json", "ra": "/tmp/kq-trien-khai.json"}' | tee "sao-luu/kiem-trien-khai.txt"
./erpctl cp backend:/tmp/kq-trien-khai.json sao-luu/kq-trien-khai.json || true
grep -q "KHÔNG ĐẠT: 0" sao-luu/kiem-trien-khai.txt && echo "== XONG: $KHACH tại $HOST (kiểm đạt toàn bộ)" || { echo "== CHƯA ĐẠT: xem sao-luu/kiem-trien-khai.txt"; exit 2; }
