#!/usr/bin/env bash
# Chi cap nhat plugin GUI tu GitHub Actions da PASS vao NocoBase UAT 13041.
# KHONG dung cai-dat.sh: lenh do co the thay doi schema/du lieu.
set -euo pipefail

REPO="tienduongmarcom/aphvh"
BRANCH="feat/nocobase-041-factory-mes"
HOME_UAT="$HOME/aphvh-uat-041/nocobase/trien-khai"
PROJECT="aphvh-nocobase-uat041"
STAMP="$(date +%Y%m%d-%H%M%S)"

for t in gh docker curl python3 tar shasum; do
  command -v "$t" >/dev/null || { echo "THIEU $t"; exit 1; }
done
[ -d "$HOME_UAT" ] || { echo "Khong co UAT: $HOME_UAT"; exit 1; }
cd "$HOME_UAT"
[ "$(pwd -P)" = "$(cd "$HOME/aphvh-uat-041/nocobase/trien-khai" && pwd -P)" ] || exit 1
[ -f .env ] || { echo "Thieu .env UAT"; exit 1; }

set -a
source ./.env
set +a
[ "${PORT:-}" = "13041" ] || { echo "SAI PORT, chi chap nhan 13041"; exit 1; }
[ "${COMPOSE_PROJECT_NAME:-}" = "$PROJECT" ] || { echo "SAI COMPOSE PROJECT"; exit 1; }

CID="$(docker compose ps -q db </dev/null)"
[ -n "$CID" ] || { echo "UAT db khong chay"; exit 1; }
RUNNING_PROJECT="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' "$CID")"
[ "$RUNNING_PROJECT" = "$PROJECT" ] || { echo "KHONG DUNG PROJECT: $RUNNING_PROJECT"; exit 1; }

echo "== 1. Xac minh PR #46 va workflow cho dung commit =="
HEAD="$(gh pr view 46 -R "$REPO" --json headRefOid --jq .headRefOid)"
[ -n "$HEAD" ] || exit 1
RUN_ID="$(gh run list -R "$REPO" --workflow nocobase-041-source.yml --branch "$BRANCH" --limit 30 \
  --json databaseId,headSha,conclusion \
  --jq "[.[] | select(.headSha == \"$HEAD\" and .conclusion == \"success\")][0].databaseId // empty")"
[ -n "$RUN_ID" ] || {
  echo "CHUA CO CI PASS cho commit $HEAD. Dung, khong doi plugin."; exit 1;
}
echo "CI PASS: commit $HEAD, run $RUN_ID"

mkdir -p sao-luu
EVIDENCE="$PWD/sao-luu/uat041-client-${STAMP}"
mkdir -p "$EVIDENCE/artifact" "$EVIDENCE/new-plugin"
gh run download "$RUN_ID" -R "$REPO" -n nocobase-041-uat-package -D "$EVIDENCE/artifact"
PKG="$EVIDENCE/artifact/plugin-kho-0.4.1.tgz"
[ -s "$PKG" ] && [ -s "$PKG.sha256" ] || { echo "Thieu goi/sha256"; exit 1; }
EXPECT="$(awk '{print $1}' "$PKG.sha256")"
ACTUAL="$(shasum -a 256 "$PKG" | awk '{print $1}')"
[ "$ACTUAL" = "$EXPECT" ] || { echo "SAI SHA256"; exit 1; }
GIT_SHA="$(tar xOf "$PKG" ./BUILD_SOURCE_SHA 2>/dev/null || tar xOf "$PKG" BUILD_SOURCE_SHA)"
[ "$GIT_SHA" = "$HEAD" ] || { echo "GOI KHONG KHOP COMMIT"; exit 1; }
tar xzf "$PKG" -C "$EVIDENCE/new-plugin"
NEW="$EVIDENCE/new-plugin"
[ -s "$NEW/dist/server/index.js" ] && [ -s "$NEW/dist/client/index.js" ] || {
  echo "GOI KHONG CO CA CLIENT + SERVER"; exit 1;
}
grep -RaqF 'Không thể tải dữ liệu sản xuất' "$NEW/dist/client" || {
  echo "CLIENT KHONG CO MA GIAO DIEN MOI. Dung."; exit 1;
}
grep -q '"version": "0.4.1"' "$NEW/package.json" || { echo "SAI VERSION"; exit 1; }

echo "== 2. Sao luu database UAT (khong don backup cu) =="
DUMP="$EVIDENCE/db-truoc-giao-dien.dump"
docker compose exec -T db pg_dump -U nocobase -Fc -d nocobase > "$DUMP"
docker compose exec -T db pg_restore -l < "$DUMP" >/dev/null
[ -s "$DUMP" ] || { echo "DUMP RONG"; exit 1; }

echo "== 3. Thay plugin CHI UAT 13041, backup plugin cu =="
CURRENT="storage/plugins/@aphvh/plugin-kho"
BACKUP="storage/plugins/@aphvh/.uat041-before-gui-${STAMP}"
[ -d "$CURRENT" ] && [ ! -e "$BACKUP" ] || { echo "PLUGIN UAT THIEU HOAC BACKUP DA CO"; exit 1; }

SWAPPED=0
APP_STOPPED=0
rollback() {
  rc=$?
  trap - EXIT
  if [ "$SWAPPED" = 1 ]; then
    echo "!! LOI: QUAY LUI PLUGIN UAT"
    docker compose stop app </dev/null || true
    if [ -d "$CURRENT" ]; then mv "$CURRENT" "$EVIDENCE/plugin-loi"; fi
    if [ -d "$BACKUP" ]; then mv "$BACKUP" "$CURRENT"; fi
    docker compose up -d app </dev/null || true
  elif [ "$APP_STOPPED" = 1 ]; then
    # Neu loi sau stop nhung truoc mv plugin, khoi dong lai ban UAT cu.
    docker compose up -d app </dev/null || true
  fi
  exit "$rc"
}
trap rollback EXIT

docker compose stop app </dev/null
APP_STOPPED=1
mv "$CURRENT" "$BACKUP"
SWAPPED=1
mv "$NEW" "$CURRENT"
docker compose up -d app </dev/null

HEALTH=0
for i in $(seq 1 45); do
  if curl -fsS --max-time 2 "http://127.0.0.1:13041/api/__health_check" >/dev/null 2>&1; then
    HEALTH=1; break
  fi
  sleep 2
done
[ "$HEALTH" = 1 ] || { echo "HEALTH FAIL sau cap nhat"; exit 1; }

echo "== 4. Smoke API chi doc =="
python3 - <<'PY'
import os,sys
sys.path.insert(0,os.path.abspath("../kiem"))
from kiem_api import API
api=API("http://127.0.0.1:13041",os.environ["ADMIN_EMAIL"],os.environ["ADMIN_PASSWORD"])
s,r=api.call("me_sx:get",q="?filterByTk=67")
assert s==200 and str(r.get("data",{}).get("id"))=="67",(s,r)
print("Mẻ 67: PASS, khong ghi du lieu")
PY

SWAPPED=0
APP_STOPPED=0
trap - EXIT
echo "=== UAT 13041 DOI GIAO DIEN PASS ==="
echo "Commit: $HEAD"
echo "Backup plugin: $BACKUP"
echo "Backup database + goi CI: $EVIDENCE"
echo "CHUA TU DONG PASS E2E 403: can kiem tra browser x-role."
echo "KHONG DOI 13606, KHONG MERGE PR."
