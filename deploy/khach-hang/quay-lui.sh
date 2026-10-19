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
# 0.14.3: bản sao lưu có sha256.txt (nang-cap.sh ghi) thì phải khớp trước khi ghi đè.
if [ -f "$S/sha256.txt" ]; then
  if command -v sha256sum >/dev/null; then (cd "$S" && sha256sum -c --quiet sha256.txt); else (cd "$S" && shasum -a 256 -c --quiet sha256.txt); fi \
    || { echo "Bản sao lưu $S không khớp sha256.txt: KHÔNG khôi phục"; exit 1; }
fi
echo "Sẽ quay về phiên bản $TRUOC và GHI ĐÈ dữ liệu hiện tại bằng bản sao lưu $N."
if [ "${2:-}" != "--tu-dong" ]; then read -r -p "Gõ CO để tiếp tục: " X; [ "$X" = CO ] || { echo "Hủy"; exit 1; }; fi
set -a; source .env; set +a
sed -i.bak "s/^CUSTOM_TAG=.*/CUSTOM_TAG=$TRUOC/" .env && rm -f .env.bak
./erpctl pull; ./erpctl up -d; sleep 20
# Tệp đưa vào container qua stdin (không docker cp): giữ quyền đọc cho user frappe dù bản sao lưu là 600 (umask 077).
DB="$(ls "$S"/*-database.sql.gz | head -1)"; PUB="$(ls "$S"/*-files.tar | grep -v private | head -1 || true)"; PRI="$(ls "$S"/*-private-files.tar | head -1 || true)"
./erpctl exec -T backend bash -c 'cat > /tmp/db.sql.gz' < "$DB"
ARGS=(/tmp/db.sql.gz)
[ -n "$PUB" ] && { ./erpctl exec -T backend bash -c 'cat > /tmp/pub.tar' < "$PUB"; ARGS+=(--with-public-files /tmp/pub.tar); }
[ -n "$PRI" ] && { ./erpctl exec -T backend bash -c 'cat > /tmp/pri.tar' < "$PRI"; ARGS+=(--with-private-files /tmp/pri.tar); }
./erpctl exec -T backend bench --site frontend --force restore "${ARGS[@]}" --db-root-username root --db-root-password "$DB_PASSWORD"
./erpctl exec -T backend bench --site frontend migrate
# Khôi phục CSDL không đụng site_config: trả các cờ tính năng kh_aph_* về đúng như lúc sao lưu
# (cờ không có trong bản sao lưu = tắt). Chỉ đọc tên cờ; không in giá trị nào khác của site_config.
SC="$(ls "$S"/*-site_config_backup.json 2>/dev/null | head -1 || true)"
if [ -n "$SC" ]; then
  CO="$(./erpctl exec -T backend python3 -c '
import json, sys
FLAGS = ("kh_aph_server_cost_guard", "kh_aph_post_receivable_on_delivery", "kh_aph_shared_sales_order",
         "kh_aph_global_credit_warning", "kh_aph_high_risk_credit_guard", "kh_aph_quantity_valuation_mvp",
         "kh_aph_funds_workflow", "kh_aph_source_change",
         "kh_aph_factory_costing", "kh_aph_factory_cash", "kh_aph_sales_adjust", "kh_aph_data_review",
         "kh_aph_kho_chuan", "kh_aph_sales_p1", "kh_aph_quan_tri",
         "kh_aph_du_lieu", "kh_aph_dau_ky", "kh_aph_kho_van_hanh", "kh_aph_gia_san",
         "kh_aph_trung_tam_ban", "kh_aph_tien_vay", "kh_aph_cash_custody", "kh_aph_cash_closing", "kh_aph_cash_handover", "kh_aph_factory_handover")
d = json.load(sys.stdin)
for f in FLAGS:
    try: v = int(str(d.get(f) or 0).strip() or 0)
    except ValueError: v = 0
    print(f, 1 if v else 0)
' < "$SC" | tr -d '\r')"
  while read -r f v; do
    [ -n "$f" ] && ./erpctl exec -T backend bench --site frontend set-config -p "$f" "$v" </dev/null
  done <<< "$CO"
  printf '%s\n' "$CO" > "$S/co-sau-quay-lui.txt"
  echo "Cờ tính năng sau quay lui:"; cat "$S/co-sau-quay-lui.txt"
  ./erpctl exec -T backend bench --site frontend clear-cache </dev/null
else
  echo "CẢNH BÁO: thiếu site_config_backup.json trong $S, giữ nguyên cờ tính năng hiện tại."
fi
echo "== XONG: đã quay về $TRUOC"
