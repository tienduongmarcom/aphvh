#!/usr/bin/env bash
# Phục hồi THỬ một bản sao lưu vào CSDL riêng "nocobase_phuc_hoi" (KHÔNG đụng CSDL đang chạy) rồi so số dòng các bảng chính.
#   bash phuc-hoi.sh sao-luu/csdl-YYYYMMDD-HHMMSS.dump
# Phục hồi THẬT (thay dữ liệu đang chạy) chỉ làm khi chủ dự án quyết định: xem README mục "Phục hồi thật".
set -euo pipefail
cd "$(dirname "$0")"
f="${1:?Cần đường dẫn tệp .dump}"
[ -f "$f" ] || { echo "Không thấy $f"; exit 1; }
docker compose exec -T db dropdb -U nocobase --if-exists nocobase_phuc_hoi
docker compose exec -T db createdb -U nocobase nocobase_phuc_hoi
docker compose exec -T db pg_restore -U nocobase -d nocobase_phuc_hoi --no-owner < "$f"
for b in mat_hang khach_hang kho ton_kho so_kho gia_von so_gia_von don_ban luot_giao phieu_thu so_quy nhap_lo mo_so_khoa tai_san me_sx; do
  a=$(docker compose exec -T db psql -U nocobase -d nocobase -tAc "SELECT COUNT(*) FROM $b" 2>/dev/null || echo "-")
  c=$(docker compose exec -T db psql -U nocobase -d nocobase_phuc_hoi -tAc "SELECT COUNT(*) FROM $b" 2>/dev/null || echo "-")
  printf '%-14s đang chạy %8s | bản phục hồi %8s\n' "$b" "$a" "$c"
done
echo "Bản phục hồi thử nằm ở CSDL nocobase_phuc_hoi (xóa: docker compose exec db dropdb -U nocobase nocobase_phuc_hoi)."
