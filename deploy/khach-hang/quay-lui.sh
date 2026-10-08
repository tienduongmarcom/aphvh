#!/usr/bin/env bash
# Quay về phiên bản trước nâng cấp: đổi lại image và khôi phục CSDL + tệp từ bản sao lưu. Chạy trong thư mục của khách.
# Dùng: ./quay-lui.sh <ten-thu-muc-trong-sao-luu> [--tu-dong]   (ví dụ 20261006-153000)
# --tu-dong: không hỏi xác nhận (do nang-cap.sh gọi khi nâng cấp lỗi).
set -euo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
N="${1:?thư mục sao lưu}"; S="sao-luu/$N"
[ -f "$S/phien-ban-truoc.txt" ] && compgen -G "$S/*-database.sql.gz" >/dev/null || { echo "Thiếu bản sao lưu đầy đủ trong $S"; exit 1; }
TRUOC="$(cat "$S/phien-ban-truoc.txt")"
echo "Sẽ quay về phiên bản $TRUOC và GHI ĐÈ dữ liệu hiện tại bằng bản sao lưu $N."
if [ "${2:-}" != "--tu-dong" ]; then read -r -p "Gõ CO để tiếp tục: " X; [ "$X" = CO ] || { echo "Hủy"; exit 1; }; fi
set -a; source .env; set +a
sed -i.bak "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$TRUOC/" .env && rm -f .env.bak
./erpctl pull; ./erpctl up -d; sleep 20
DB="$(ls "$S"/*-database.sql.gz | head -1)"; PUB="$(ls "$S"/*-files.tar | grep -v private | head -1 || true)"; PRI="$(ls "$S"/*-private-files.tar | head -1 || true)"
./erpctl cp "$DB" backend:/tmp/db.sql.gz
ARGS=(/tmp/db.sql.gz)
[ -n "$PUB" ] && { ./erpctl cp "$PUB" backend:/tmp/pub.tar; ARGS+=(--with-public-files /tmp/pub.tar); }
[ -n "$PRI" ] && { ./erpctl cp "$PRI" backend:/tmp/pri.tar; ARGS+=(--with-private-files /tmp/pri.tar); }
./erpctl exec -T backend bench --site frontend --force restore "${ARGS[@]}" --db-root-username root --db-root-password "$DB_PASSWORD"
./erpctl exec -T backend bench --site frontend migrate
echo "== XONG: đã quay về $TRUOC"
