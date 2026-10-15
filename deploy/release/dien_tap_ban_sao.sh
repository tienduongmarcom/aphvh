#!/bin/bash
# Diễn tập nâng cấp trên BẢN SAO production (0.14.2). Bắt buộc trước trien_khai_frontend.sh khi site `frontend` đã có dữ liệu.
# Chạy TRÊN SSH vào máy chủ, trong ~/trien-khai đã checkout đúng tag:
#   bash deploy/release/dien_tap_ban_sao.sh 0.14.2 [cờ mới ...]
# Làm gì (KHÔNG đổi site frontend, không đổi image/container đang chạy):
#   1. Sao lưu frontend bằng container đang chạy, lấy dấu vân frontend.
#   2. Kéo image bản mới; chạy container TẠM (docker run --rm) cùng mạng + cùng ổ sites với backend.
#   3. Khôi phục bản sao lưu vào site tạm `dien-tap` (tắt lịch chạy), chép cờ kh_aph_* + khóa mã hóa từ frontend.
#   4. migrate, bật cờ mới, bộ cài (co_du_lieu=1), cây kho, kiểm triển khai.
#   5. So tổng sổ frontend (trước) với dien-tap (sau). Xóa site tạm. Ghi dấu ~/dien-tap-<PB>.ok.
# Biến môi trường: IMG (mặc định ghcr.io/tienduongmarcom/kh-aph-erpnext:<PB>), BE (backend), ERP_DIR (thư mục compose),
# SITE_GOC (mặc định frontend), DAU_RA (thư mục ghi dấu, mặc định $HOME).
set -euo pipefail
[ $# -ge 1 ] || { echo "Dùng: $0 <phiên bản> [cờ mới ...]"; exit 2; }
PB="$1"; shift; CO_MOI=("$@")
loi() { echo "!!! DỪNG: $1"; exit 1; }
BE="${BE:-erp-aph-vh-backend-1}"
ERP_DIR="${ERP_DIR:-$HOME/erp/aph-vh}"
SITE_GOC="${SITE_GOC:-frontend}"
IMG="${IMG:-ghcr.io/tienduongmarcom/kh-aph-erpnext:$PB}"
DAU_RA="${DAU_RA:-$HOME}"
TAM=dien-tap
B=/home/frappe/frappe-bench
TK="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TK"
grep -q "__version__ = \"$PB\"" kh_aph/__init__.py || [ -n "${BO_KIEM_TAG:-}" ] || loi "thư mục $TK không phải tag v$PB"
DB_PASSWORD="$(grep '^DB_PASSWORD=' "$ERP_DIR/.env" | head -1 | cut -d= -f2-)"
[ -n "$DB_PASSWORD" ] || loi "không đọc được DB_PASSWORD trong $ERP_DIR/.env"
LOG="$DAU_RA/log-dien-tap-$PB"
rm -f "$DAU_RA/dien-tap-$PB.ok"

dv() { docker exec -i -w $B/sites "$1" $B/env/bin/python - "$2" < deploy/release/dau_van_site.py; }
MANG="$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$BE" | awk '{print $1}')"
OSITES="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/home/frappe/frappe-bench/sites"}}{{if .Name}}{{.Name}}{{else}}{{.Source}}{{end}}{{end}}{{end}}' "$BE")"
[ -n "$MANG" ] && [ -n "$OSITES" ] || loi "không tìm thấy mạng / ổ sites của $BE"
tam() { docker run --rm -i --network "$MANG" -v "$OSITES:$B/sites" -w $B -e DB_PASSWORD "$IMG" bash -c "$1"; }
export DB_PASSWORD
don_dep() {
  echo "== Dọn site tạm $TAM"
  tam "bench drop-site $TAM --force --no-backup --db-root-username root --db-root-password \"\$DB_PASSWORD\" >/dev/null 2>&1 || true; rm -rf sites/$TAM sites/archived_sites/$TAM* /tmp/dien-tap.sql" </dev/null || true
}
trap don_dep EXIT

echo "== 1. Sao lưu + dấu vân $SITE_GOC (container đang chạy, chỉ đọc)"
docker image inspect "$(docker inspect -f '{{.Image}}' "$BE")" -f '{{json .RepoDigests}}'
dv "$BE" "$SITE_GOC" > "$LOG-truoc.txt"
grep -q '^DAU_VAN ' "$LOG-truoc.txt" || loi "không lấy được dấu vân"
docker exec "$BE" bench --site "$SITE_GOC" backup </dev/null > "$LOG-sao-luu.txt" 2>&1 || loi "sao lưu lỗi"
BK="$(docker exec "$BE" bash -c "ls -t sites/$SITE_GOC/private/backups/*-database.sql.gz | head -1" </dev/null | tr -d '\r')"
[ -n "$BK" ] || loi "không thấy bản sao lưu"
echo "Bản sao lưu: $BK"

echo "== 2. Image bản mới: $IMG"
docker image inspect "$IMG" >/dev/null 2>&1 || docker pull "$IMG"
docker image inspect "$IMG" -f '{{json .RepoDigests}} {{.Id}}'
tam "grep -o '__version__ = \"[^\"]*\"' apps/kh_aph/kh_aph/__init__.py" </dev/null

echo "== 3. Khôi phục vào site tạm $TAM"
tam "bench drop-site $TAM --force --no-backup --db-root-username root --db-root-password \"\$DB_PASSWORD\" >/dev/null 2>&1 || true
  rm -rf sites/$TAM
  gunzip -c '$BK' > /tmp/dien-tap.sql
  bench new-site $TAM --source_sql /tmp/dien-tap.sql --mariadb-user-host-login-scope='172.%.%.%' \
    --db-root-username root --db-root-password \"\$DB_PASSWORD\" --admin-password \"\$(head -c 24 /dev/urandom | base64)\" --force
  rm -f /tmp/dien-tap.sql
  env/bin/python - <<'PY'
import json
g = json.load(open('sites/$SITE_GOC/site_config.json'))
p = 'sites/$TAM/site_config.json'
t = json.load(open(p))
for k, v in g.items():
    if k.startswith('kh_aph_') or k == 'encryption_key':
        t[k] = v
t['pause_scheduler'] = 1
t['maintenance_mode'] = 0
json.dump(t, open(p, 'w'), indent=1)
print('Đã chép', sum(1 for k in g if k.startswith('kh_aph_')), 'cờ kh_aph_*')
PY" </dev/null > "$LOG-khoi-phuc.txt" 2>&1 || { tail -20 "$LOG-khoi-phuc.txt"; loi "khôi phục bản sao lỗi"; }
tail -2 "$LOG-khoi-phuc.txt"

echo "== 4. migrate + cờ mới + bộ cài + cây kho + kiểm trên $TAM (image mới)"
CO="${CO_MOI[*]:-}"
tam "set -e
  bench --site $TAM migrate
  for f in $CO; do bench --site $TAM set-config -p \"\$f\" 1; done
  cat > /tmp/khach.json
  bench --site $TAM execute kh_aph.cai_dat_tinh_nang.cai --kwargs '{\"xac_nhan_site\": \"$TAM\", \"co_du_lieu\": 1}'
  bench --site $TAM execute kh_aph.cai_dat_tinh_nang.kiem --kwargs '{\"xac_nhan_site\": \"$TAM\", \"co_du_lieu\": 1}'
  bench --site $TAM execute kh_aph.kho_chuan.dung --kwargs '{\"duong_dan\": \"/tmp/khach.json\", \"xac_nhan_site\": \"$TAM\"}'
  bench --site $TAM execute kh_aph.kiem_trien_khai.chay --kwargs '{\"duong_dan\": \"/tmp/khach.json\"}'" \
  < khach/aph-vh/khach.json > "$LOG-nang-cap.txt" 2>&1 || { tail -30 "$LOG-nang-cap.txt"; loi "nâng cấp bản sao lỗi"; }
[ "$(grep -c '"idempotent": true' "$LOG-nang-cap.txt")" -ge 2 ] || { tail -30 "$LOG-nang-cap.txt"; loi "bộ cài / kiểm bộ cài"; }
grep "^Cây kho" "$LOG-nang-cap.txt" || true
tail -1 "$LOG-nang-cap.txt"
grep -q "KHÔNG ĐẠT: 0" "$LOG-nang-cap.txt" || { grep -i "không đạt" "$LOG-nang-cap.txt" | head -20; loi "kiểm triển khai bản sao có mục KHÔNG ĐẠT"; }

echo "== 5. So tổng sổ $SITE_GOC (trước) với $TAM (sau)"
tam "cd sites && ../env/bin/python - $TAM" < deploy/release/dau_van_site.py > "$LOG-sau.txt" 2>/dev/null || true
grep -q '^DAU_VAN ' "$LOG-sau.txt" || loi "không lấy được dấu vân bản sao"
python3 deploy/release/so_dau_van.py "$LOG-truoc.txt" "$LOG-sau.txt" --phan tong || loi "tổng sổ bản sao lệch"
python3 deploy/release/so_dau_van.py "$LOG-truoc.txt" "$LOG-sau.txt" --phan dem || true

don_dep; trap - EXIT
python3 - "$LOG-truoc.txt" "$PB" "$IMG" > "$DAU_RA/dien-tap-$PB.ok" <<'PY'
import json, sys, time
d = json.loads([l for l in open(sys.argv[1]) if l.startswith("DAU_VAN ")][0][8:])
print(json.dumps({"phien_ban": sys.argv[2], "image": sys.argv[3], "luc": int(time.time()), "tong": d.get("tong")}, ensure_ascii=False))
PY
echo "=== DIỄN TẬP $PB: ĐẠT (dấu $DAU_RA/dien-tap-$PB.ok, còn hạn 12 giờ) ==="
