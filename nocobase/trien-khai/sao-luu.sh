#!/usr/bin/env bash
# Sao lưu CSDL + tệp đính kèm, KIỂM bản sao lưu đọc được, giữ 30 bản gần nhất. Đặt lịch hằng đêm (crontab): 30 23 * * * bash /đường/dẫn/sao-luu.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p sao-luu
t=$(date +%Y%m%d-%H%M%S)
f="sao-luu/csdl-$t.dump"
docker compose exec -T db pg_dump -U nocobase -Fc nocobase > "$f"
[ -s "$f" ] || { echo "!! Bản sao lưu rỗng — DỪNG."; rm -f "$f"; exit 1; }
n=$(docker compose exec -T db pg_restore -l < "$f" | grep -c "TABLE DATA" || true)
[ "$n" -gt 10 ] || { echo "!! Bản sao lưu không đọc được (chỉ $n bảng) — DỪNG."; exit 1; }
tar czf "sao-luu/tep-$t.tgz" storage/uploads 2>/dev/null || true
ls -1t sao-luu/csdl-*.dump | tail -n +31 | xargs -r rm -f
ls -1t sao-luu/tep-*.tgz 2>/dev/null | tail -n +31 | xargs -r rm -f
echo "Đã sao lưu $f ($(du -h "$f" | cut -f1), $n bảng dữ liệu, đã kiểm đọc được)"
