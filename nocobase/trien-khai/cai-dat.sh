#!/usr/bin/env bash
# Cài / cập nhật APH-VH NocoBase trên máy có Docker (Mac hoặc VM). Chạy lại an toàn.
#   cd nocobase/trien-khai && bash cai-dat.sh
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo "Chưa có Docker. Cài Docker Desktop (Mac) hoặc docker engine (VM) rồi chạy lại."; exit 1; }
if [ ! -f .env ]; then
  r() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$1"; }
  cat > .env <<EOF
APP_KEY=$(r 48)
DB_PASSWORD=$(r 24)
ADMIN_EMAIL=admin@aphvh.local
ADMIN_PASSWORD=$(r 14)
PORT=13000
EOF
  chmod 600 .env
  echo "Đã tạo .env (mật khẩu quản trị nằm trong tệp này, KHÔNG đưa lên git)."
fi
set -a; . ./.env; set +a
mkdir -p storage/plugins pgdata
echo "== 1. Khởi động"
docker compose up -d
echo -n "Chờ NocoBase sẵn sàng"
for i in $(seq 1 120); do
  curl -fsS "http://localhost:${PORT}/api/__health_check" >/dev/null 2>&1 && break; echo -n "."; sleep 5
done; echo
echo "== 2. Plugin APH-VH"
rm -rf storage/plugins/@aphvh/plugin-kho && mkdir -p storage/plugins/@aphvh/plugin-kho
tar xzf plugin-kho-*.tgz -C storage/plugins/@aphvh/plugin-kho
docker compose exec -T app yarn nocobase pm enable @aphvh/plugin-kho
for i in $(seq 1 60); do curl -fsS "http://localhost:${PORT}/api/__health_check" >/dev/null 2>&1 && break; sleep 5; done
echo "== 3. Bảng dữ liệu, menu, nhóm quyền, 4 đơn vị"
python3 ../schema/tao_bang.py --url "http://localhost:${PORT}" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"
python3 ../schema/cai_dat.py --url "http://localhost:${PORT}" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"
echo "=== XONG: mở http://localhost:${PORT}  — đăng nhập $ADMIN_EMAIL, mật khẩu xem trong tệp .env ==="
