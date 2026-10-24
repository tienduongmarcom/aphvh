#!/usr/bin/env bash
# UAT NocoBase 0.4.1 trên Mac — TÁCH BIỆT HOÀN TOÀN với NocoBase 13000.
# Chạy từ repo aphvh hiện tại: bash <(git show origin/feat/nocobase-041-factory-mes:nocobase/trien-khai/uat-mac-041.sh) "$PWD"
set -euo pipefail
SOURCE="${1:-$PWD}"
SOURCE="$(git -C "$SOURCE" rev-parse --show-toplevel)"
REPO="tienduongmarcom/aphvh"
BRANCH="feat/nocobase-041-factory-mes"
UAT="$HOME/aphvh-uat-041"
PROJECT="aphvh-nocobase-uat041"
PORT="13041"

for c in git gh docker openssl python3; do
  command -v "$c" >/dev/null || { echo "THIẾU $c. Dừng, chưa thay đổi gì."; exit 1; }
done
docker info >/dev/null 2>&1 || { echo "Docker Desktop chưa chạy."; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Cần chạy gh auth login trước."; exit 1; }
[ ! -e "$UAT" ] || { echo "ĐÃ CÓ $UAT. Không ghi đè bản UAT cũ; kiểm tra hoặc đổi tên thư mục trước."; exit 1; }
if (curl -fsS --max-time 2 "http://localhost:${PORT}/api/__health_check" >/dev/null 2>&1); then
  echo "Cổng ${PORT} đã có NocoBase chạy. Không chồng phiên khác."
  exit 1
fi

echo "== 1. Lấy commit mới nhất của nhánh PR #46"
git -C "$SOURCE" fetch origin "$BRANCH"
git -C "$SOURCE" worktree add --detach "$UAT" "origin/$BRANCH"
SHA="$(git -C "$UAT" rev-parse HEAD)"
cd "$UAT/nocobase/trien-khai"

echo "== 2. Tạo môi trường riêng (không dùng chung .env / pgdata / storage với app chính)"
cat > .env <<EOF
APP_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -hex 20)
ADMIN_EMAIL=uat041@aphvh.local
ADMIN_PASSWORD=$(openssl rand -hex 12)
PORT=$PORT
COMPOSE_PROJECT_NAME=$PROJECT
EOF
chmod 600 .env
set -a; . ./.env; set +a

echo "== 3. Tìm gói UAT ở GitHub Actions (BẮT BUỘC đã PASS)"
RUN_ID="$(gh run list -R "$REPO" --workflow nocobase-041-source.yml --branch "$BRANCH" --limit 15 \
  --json databaseId,conclusion,headSha --jq "[.[] | select(.conclusion == \"success\" and .headSha == \"$SHA\")][0].databaseId // empty")"
[ -n "$RUN_ID" ] || { echo "Chưa có workflow PASS kèm gói UAT. Dừng."; exit 1; }
rm -f plugin-kho-0.4.1.tgz plugin-kho-0.4.1.tgz.sha256
gh run download "$RUN_ID" -R "$REPO" -n nocobase-041-uat-package -D .
[ -s plugin-kho-0.4.1.tgz ] && [ -s plugin-kho-0.4.1.tgz.sha256 ] || {
  echo "Gói UAT/sha256 chưa có trong Actions."; exit 1;
}
PKG_SHA="$(tar xOf plugin-kho-0.4.1.tgz ./BUILD_SOURCE_SHA 2>/dev/null || tar xOf plugin-kho-0.4.1.tgz BUILD_SOURCE_SHA)"
[ "$PKG_SHA" = "$SHA" ] || {
  echo "KHÔNG KHỚP SOURCE: package=$PKG_SHA, worktree=$SHA. Không cài."; exit 1;
}
echo "Gói UAT đúng commit: $SHA"

echo "== 4. Cài mới trong Docker project $PROJECT, cổng $PORT"
bash cai-dat.sh

echo "== 5. Chạy hồi quy trên dữ liệu giả trong UAT (KHÔNG chạy trên 13000)"
mkdir -p sao-luu
set +e
(cd ../kiem && EMAIL="$ADMIN_EMAIL" MAT_KHAU="$ADMIN_PASSWORD" URL="http://localhost:$PORT" bash chay_tat_ca.sh) \
  2>&1 | tee "sao-luu/uat-041-$(date +%Y%m%d-%H%M%S).log"
STATUS=${PIPESTATUS[0]}
set -e
if [ "$STATUS" -ne 0 ]; then
  echo "TEST CHƯA ĐẠT: kiểm log trong $UAT/nocobase/trien-khai/sao-luu/"
  exit 1
fi

echo "== 6. Sao lưu sau test và thử KHÔI PHỤC vào database phụ, không đè DB UAT"
bash sao-luu.sh
DUMP="$(ls -1t sao-luu/csdl-*.dump | sed -n '1p')"
DB_CHECK="uat041_restorecheck"
docker compose exec -T db createdb -U nocobase "$DB_CHECK"
cleanup_restore() { docker compose exec -T db dropdb -U nocobase "$DB_CHECK" >/dev/null 2>&1 || true; }
trap cleanup_restore EXIT
docker compose exec -T db pg_restore -U nocobase --no-owner --no-acl -d "$DB_CHECK" < "$DUMP"
for tbl in so_kho so_gia_von ton_kho phieu_kho me_sx phieu_thu; do
  src="$(docker compose exec -T db psql -U nocobase -d nocobase -tAc "SELECT COUNT(*) FROM $tbl" | tr -d '[:space:]')"
  dst="$(docker compose exec -T db psql -U nocobase -d "$DB_CHECK" -tAc "SELECT COUNT(*) FROM $tbl" | tr -d '[:space:]')"
  [ "$src" = "$dst" ] || { echo "RESTORE LỆCH $tbl: gốc=$src, phục hồi=$dst"; exit 1; }
done
echo "Restore vào DB phụ + 6 bảng đối chiếu: PASS."
cleanup_restore
trap - EXIT

echo "=== UAT PASS THEO CHAY_TAT_CA (CHUA CO E2E TREN TRINH DUYET) ==="
echo "Truy cập http://localhost:$PORT"
echo "Đăng nhập $ADMIN_EMAIL (mật khẩu: grep ADMIN_PASSWORD .env)"
echo "Thư mục riêng: $UAT; Docker project: $PROJECT"
echo "Không chép gói UAT sang hệ thống 13000 hay production khi chưa nghiệm thu."
