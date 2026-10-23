#!/usr/bin/env bash
# Sao lưu CSDL + tệp đính kèm, giữ 30 bản gần nhất. Đặt lịch hằng đêm (crontab): 30 23 * * * bash /đường/dẫn/sao-luu.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p sao-luu
t=$(date +%Y%m%d-%H%M%S)
docker compose exec -T db pg_dump -U nocobase -Fc nocobase > "sao-luu/csdl-$t.dump"
tar czf "sao-luu/tep-$t.tgz" storage/uploads 2>/dev/null || true
ls -1t sao-luu/csdl-*.dump | tail -n +31 | xargs -r rm -f
ls -1t sao-luu/tep-*.tgz 2>/dev/null | tail -n +31 | xargs -r rm -f
echo "Đã sao lưu sao-luu/csdl-$t.dump ($(du -h "sao-luu/csdl-$t.dump" | cut -f1))"
