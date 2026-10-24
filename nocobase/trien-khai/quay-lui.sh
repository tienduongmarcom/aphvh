#!/usr/bin/env bash
# Quay lui sau nâng cấp:
#   bash quay-lui.sh                       → đưa plugin về bản cũ gần nhất (.cu-*), giữ dữ liệu.
#   bash quay-lui.sh sao-luu/csdl-X.dump   → ĐỒNG THỜI thay CSDL bằng bản sao lưu X (mất mọi phát sinh sau thời điểm X). Hỏi xác nhận.
set -euo pipefail
cd "$(dirname "$0")"
CU=$(ls -1dt storage/plugins/@aphvh/.cu-* 2>/dev/null | head -1 || true)
[ -n "$CU" ] || { echo "Không có bản plugin cũ để quay lui."; exit 1; }
if [ -n "${1:-}" ]; then
  [ -s "$1" ] || { echo "Không thấy $1"; exit 1; }
  read -r -p "THAY TOÀN BỘ CSDL bằng $1? Gõ DONG Y để tiếp tục: " xn
  [ "$xn" = "DONG Y" ] || { echo "Đã hủy."; exit 1; }
fi
docker compose stop app
bash sao-luu.sh   # giữ lại trạng thái hiện tại trước khi quay lui
rm -rf storage/plugins/@aphvh/plugin-kho && mv "$CU" storage/plugins/@aphvh/plugin-kho
if [ -n "${1:-}" ]; then
  docker compose exec -T db dropdb -U nocobase nocobase
  docker compose exec -T db createdb -U nocobase nocobase
  docker compose exec -T db pg_restore -U nocobase -d nocobase --no-owner < "$1"
fi
docker compose up -d app
echo "Đã quay lui plugin về $(grep '"version"' storage/plugins/@aphvh/plugin-kho/package.json)."
