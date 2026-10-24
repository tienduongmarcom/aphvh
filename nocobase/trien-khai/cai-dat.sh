#!/usr/bin/env bash
# Cài mới / nâng cấp APH-VH NocoBase (Mac hoặc VM có Docker). Chạy lại an toàn; nâng cấp tại chỗ, không xóa dữ liệu.
#   cd nocobase/trien-khai && bash cai-dat.sh
# Nâng cấp: dừng app (khóa ghi) → sao lưu + kiểm bản sao lưu → kiểm checksum gói → giải nén ra thư mục tạm, kiểm phiên bản
#           → đổi plugin (giữ bản cũ) → khởi động, kiểm sức khỏe → lỗi thì TỰ QUAY LUI plugin cũ → bảng / quyền → đối chiếu bảo toàn.
set -euo pipefail
cd "$(dirname "$0")"
PHIEN_BAN="0.4.0"
GOI="plugin-kho-${PHIEN_BAN}.tgz"
command -v docker >/dev/null || { echo "Chưa có Docker. Cài Docker Desktop (Mac) hoặc docker engine (VM) rồi chạy lại."; exit 1; }
[ -f "$GOI" ] || { echo "Không thấy $GOI (git pull chưa?)."; exit 1; }
tinh_sha() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
[ "$(tinh_sha "$GOI")" = "$(cut -d' ' -f1 "$GOI.sha256")" ] || { echo "SAI CHECKSUM $GOI — dừng, không cài."; exit 1; }
echo "Gói $GOI: checksum đúng."
if [ ! -f .env ]; then
  r() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$1"; }
  cat > .env <<EOT
APP_KEY=$(r 48)
DB_PASSWORD=$(r 24)
ADMIN_EMAIL=admin@aphvh.local
ADMIN_PASSWORD=$(r 14)
PORT=13000
EOT
  chmod 600 .env
  echo "Đã tạo .env (mật khẩu quản trị nằm trong tệp này, KHÔNG đưa lên git)."
fi
set -a; . ./.env; set +a
mkdir -p storage/plugins/@aphvh pgdata
cho() { for i in $(seq 1 "${1:-120}"); do curl -fsS "http://localhost:${PORT}/api/__health_check" >/dev/null 2>&1 && return 0; sleep 5; done; return 1; }

echo "== 1. Khởi động CSDL"
docker compose up -d db
for i in $(seq 1 60); do docker compose exec -T db pg_isready -U nocobase >/dev/null 2>&1 && break; sleep 2; done
CO_DU_LIEU=0
docker compose exec -T db psql -U nocobase -d nocobase -tAc "SELECT 1 FROM ton_kho LIMIT 1" >/dev/null 2>&1 && CO_DU_LIEU=1
if [ "$CO_DU_LIEU" = 1 ]; then
  echo "== 1b. Đã có dữ liệu: dừng app (khóa ghi), sao lưu và kiểm bản sao lưu"
  docker compose stop app || true
  bash sao-luu.sh
fi

echo "== 2. Chuẩn bị plugin $PHIEN_BAN (chưa đổi bản đang chạy)"
TAM="storage/plugins/@aphvh/.moi-$PHIEN_BAN"
rm -rf "$TAM" && mkdir -p "$TAM"
tar xzf "$GOI" -C "$TAM"
grep -q "\"version\": \"$PHIEN_BAN\"" "$TAM/package.json" || { echo "Gói không đúng phiên bản $PHIEN_BAN — dừng."; rm -rf "$TAM"; exit 1; }
CU=""
if [ -d storage/plugins/@aphvh/plugin-kho ]; then
  CU="storage/plugins/@aphvh/.cu-$(date +%Y%m%d-%H%M%S)"
  mv storage/plugins/@aphvh/plugin-kho "$CU"
fi
mv "$TAM" storage/plugins/@aphvh/plugin-kho
quay_lui() {
  echo "!! Lỗi khi nâng cấp — quay lui plugin cũ ($CU)"
  if [ -n "$CU" ]; then rm -rf storage/plugins/@aphvh/plugin-kho && mv "$CU" storage/plugins/@aphvh/plugin-kho; fi
  docker compose restart app || docker compose up -d app
  echo "Đã quay lui plugin. Dữ liệu: chưa đổi bảng (bước 4 chưa chạy). Bản sao lưu ở trien-khai/sao-luu/."
  exit 1
}
echo "== 3. Khởi động app với plugin mới"
docker compose up -d app
cho 120 || quay_lui
docker compose exec -T app yarn nocobase pm enable @aphvh/plugin-kho || quay_lui
docker compose restart app
cho 60 || quay_lui
echo "== 4. Bảng dữ liệu, menu, nhóm quyền, 4 đơn vị (chỉ thêm, không xóa)"
python3 ../schema/tao_bang.py --url "http://localhost:${PORT}" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"
python3 ../schema/cai_dat.py --url "http://localhost:${PORT}" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"
echo "== 4b. Nâng cấp dữ liệu 0.4.0 (cấu hình mặc định, giữ quyền cũ, bổ sung số liệu dòng cũ, giữ tồn đơn đang chờ giao)"
mkdir -p sao-luu
python3 ../schema/nang_cap.py --url "http://localhost:${PORT}" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD" | tee "sao-luu/nang-cap-0.4.0-$(date +%Y%m%d-%H%M%S).json"
echo "== 5. Đối chiếu bảo toàn sau nâng cấp"
(cd ../kiem && python3 doi_chieu.py --url "http://localhost:${PORT}" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD") || echo "!! Đối chiếu có lệch — xem chi tiết ở trên, chưa dùng thật."
[ -n "$CU" ] && echo "Plugin cũ giữ ở $CU (quay lui tay: bash quay-lui.sh)."
echo "=== XONG $PHIEN_BAN: mở http://localhost:${PORT} — đăng nhập $ADMIN_EMAIL, mật khẩu xem trong tệp .env ==="
