#!/bin/bash
# Diễn tập nâng cấp trên BẢN SAO production, TÁCH BIỆT HOÀN TOÀN (0.14.3). Bắt buộc trước trien_khai_frontend.sh khi `frontend` có dữ liệu.
# Chạy TRÊN SSH vào máy chủ, trong ~/trien-khai đã checkout đúng tag:
#   bash deploy/release/dien_tap_ban_sao.sh 0.14.3 [cờ mới ...]
# Đụng production ở đúng hai chỗ, đều chỉ đọc: lấy dấu vân + tạo một bản sao lưu (`bench backup`) trong container đang chạy.
# Mọi thứ còn lại chạy trên tài nguyên RIÊNG của lượt này (mã lượt ngẫu nhiên $RID, gắn nhãn vn.9xlab.dien-tap=$RID):
#   mạng docker riêng, MariaDB riêng (mật khẩu ngẫu nhiên), Redis riêng, ổ sites riêng, site tên dt-$RID. Không chung ổ / mạng /
#   hàng đợi với production, nên worker production không thấy việc của bản sao, tệp giao diện không bị ghi đè.
#   Bản sao: tắt lịch chạy, tắt gửi thư (mute_emails), không có worker, không có web.
#   Dọn dẹp chỉ xóa đúng container / ổ / mạng mang nhãn của lượt này.
# Đạt thì ghi dấu ~/dien-tap-<PB>.ok ràng buộc: phiên bản, image ID, commit nguồn, sha256 khach.json, cờ mới, site đích (12 giờ).
# Biến môi trường: IMG, BE, SITE_GOC, DAU_RA, BO_KIEM_TAG (chỉ CI), GIU_BAN_SAO=1 (không dọn, để điều tra).
set -euo pipefail
[ $# -ge 1 ] || { echo "Dùng: $0 <phiên bản> [cờ mới ...]"; exit 2; }
PB="$1"; shift; CO_MOI=("$@")
loi() { echo "!!! DỪNG: $1"; exit 1; }
BE="${BE:-erp-aph-vh-backend-1}"
SITE_GOC="${SITE_GOC:-frontend}"
IMG="${IMG:-ghcr.io/tienduongmarcom/kh-aph-erpnext:$PB}"
DAU_RA="${DAU_RA:-$HOME}"
B=/home/frappe/frappe-bench
TK="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TK"
grep -q "__version__ = \"$PB\"" kh_aph/__init__.py || [ -n "${BO_KIEM_TAG:-}" ] || loi "thư mục $TK không phải tag v$PB"
RID="$(date +%m%d%H%M)$(head -c 3 /dev/urandom | od -An -tx1 | tr -d ' \n')"
NHAN="vn.9xlab.dien-tap=$RID"
MANG="dt-$RID"; DB="dt-$RID-db"; RD="dt-$RID-redis"; OSITES="dt-$RID-sites"; TAM="dt-$RID"
LOG="$DAU_RA/log-dien-tap-$PB"
DAU="$DAU_RA/dien-tap-$PB.ok"
rm -f "$DAU"
DT_ROOT="$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
export DT_ROOT

dv() { docker exec -i -w $B/sites "$1" $B/env/bin/python - "$2" < deploy/release/dau_van_site.py; }
# Container tạm: image bản mới, entrypoint bash (không chạy entrypoint của image), mạng + ổ sites RIÊNG.
tam() { docker run --rm -i --label "$NHAN" --network "$MANG" -v "$OSITES:$B/sites" -w $B -e DT_ROOT --entrypoint bash "$IMG" -c "$1"; }
don_dep() {
  if [ "${GIU_BAN_SAO:-0}" = 1 ]; then echo "== GIỮ bản sao lượt $RID để điều tra (dọn sau: docker rm -f $DB $RD; docker volume rm $OSITES; docker network rm $MANG)"; return; fi
  echo "== Dọn tài nguyên lượt $RID"
  docker ps -aq --filter "label=$NHAN" | xargs -r docker rm -f >/dev/null 2>&1 || true
  docker volume ls -q --filter "label=$NHAN" | xargs -r docker volume rm >/dev/null 2>&1 || true
  docker network ls -q --filter "label=$NHAN" | xargs -r docker network rm >/dev/null 2>&1 || true
}
trap don_dep EXIT

echo "== 1. Dấu vân + sao lưu $SITE_GOC (chỉ đọc, container đang chạy)"
docker image inspect "$(docker inspect -f '{{.Image}}' "$BE")" -f '{{json .RepoDigests}}'
DUAN="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$BE")"
DBGOC="$(docker ps -q --filter "label=com.docker.compose.project=$DUAN" --filter label=com.docker.compose.service=db | head -1)"
RDGOC="$(docker ps -q --filter "label=com.docker.compose.project=$DUAN" --filter label=com.docker.compose.service=redis-cache | head -1)"
[ -n "$DBGOC" ] && [ -n "$RDGOC" ] || loi "không tìm thấy container db / redis của dự án $DUAN"
IMG_DB="$(docker inspect -f '{{.Config.Image}}' "$DBGOC")"; IMG_RD="$(docker inspect -f '{{.Config.Image}}' "$RDGOC")"
dv "$BE" "$SITE_GOC" > "$LOG-truoc.txt"
grep -q '^DAU_VAN ' "$LOG-truoc.txt" || loi "không lấy được dấu vân"
docker exec "$BE" bench --site "$SITE_GOC" backup </dev/null > "$LOG-sao-luu.txt" 2>&1 || loi "sao lưu lỗi"
BK="$(docker exec "$BE" bash -c "ls -t sites/$SITE_GOC/private/backups/*-database.sql.gz | head -1" </dev/null | tr -d '\r')"
[ -n "$BK" ] || loi "không thấy bản sao lưu"
docker exec "$BE" gzip -t "$BK" </dev/null || loi "bản sao lưu hỏng (gzip)"
echo "Bản sao lưu: $BK"

echo "== 2. Image bản mới: $IMG"
docker image inspect "$IMG" >/dev/null 2>&1 || docker pull "$IMG"
IMG_ID="$(docker image inspect "$IMG" -f '{{.Id}}')"
docker image inspect "$IMG" -f '{{json .RepoDigests}} {{.Id}}'

echo "== 3. Dựng môi trường riêng lượt $RID ($IMG_DB, $IMG_RD)"
docker network create --label "$NHAN" "$MANG" >/dev/null
docker volume create --label "$NHAN" "$OSITES" >/dev/null
docker run -d --label "$NHAN" --name "$DB" --network "$MANG" --network-alias db -e MARIADB_ROOT_PASSWORD="$DT_ROOT" \
  "$IMG_DB" --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci --skip-character-set-client-handshake >/dev/null
docker run -d --label "$NHAN" --name "$RD" --network "$MANG" --network-alias redis "$IMG_RD" >/dev/null
for i in $(seq 1 60); do docker exec "$DB" healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1 && break; sleep 2; done
docker exec "$DB" healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1 || loi "MariaDB riêng không lên"
tam 'ls -1 apps > sites/apps.txt
  printf "%s" "{\"db_host\": \"db\", \"db_port\": 3306, \"redis_cache\": \"redis://redis:6379\", \"redis_queue\": \"redis://redis:6379\", \"redis_socketio\": \"redis://redis:6379\", \"socketio_port\": 9000}" > sites/common_site_config.json' </dev/null
# Bản sao lưu + site_config gốc chảy qua stdin vào ổ riêng (không docker cp, không in nội dung).
docker exec "$BE" cat "$BK" </dev/null | tam 'cat > sites/goc.sql.gz'
docker exec "$BE" cat "sites/$SITE_GOC/site_config.json" </dev/null | tam 'cat > sites/goc_site_config.json'

echo "== 4. Khôi phục vào site $TAM"
tam "set -e
  gunzip -c sites/goc.sql.gz > /tmp/goc.sql
  bench new-site $TAM --source_sql /tmp/goc.sql --mariadb-user-host-login-scope='%' \
    --db-root-username root --db-root-password \"\$DT_ROOT\" --admin-password \"\$(head -c 24 /dev/urandom | base64)\" --force
  rm -f /tmp/goc.sql sites/goc.sql.gz
  env/bin/python - <<'PY'
import json
g = json.load(open('sites/goc_site_config.json'))
p = 'sites/$TAM/site_config.json'
t = json.load(open(p))
for k, v in g.items():
    if k.startswith('kh_aph_') or k == 'encryption_key':
        t[k] = v
t.update(pause_scheduler=1, mute_emails=1, maintenance_mode=0)
json.dump(t, open(p, 'w'), indent=1)
print('Đã chép', sum(1 for k in g if k.startswith('kh_aph_')), 'cờ kh_aph_*; tắt lịch chạy + thư')
PY
  rm -f sites/goc_site_config.json" </dev/null > "$LOG-khoi-phuc.txt" 2>&1 || { tail -20 "$LOG-khoi-phuc.txt"; loi "khôi phục bản sao lỗi"; }
tail -1 "$LOG-khoi-phuc.txt"

echo "== 5. migrate + cờ mới + bộ cài + cây kho + kiểm trên $TAM (image mới)"
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

echo "== 6. So sổ $SITE_GOC (trước) với $TAM (sau): tổng, số bản ghi, chi tiết theo công ty / tài khoản / đối tượng / mã hàng / kho / bao"
tam "cd sites && ../env/bin/python - $TAM" < deploy/release/dau_van_site.py > "$LOG-sau.txt" 2>/dev/null || true
grep -q '^DAU_VAN ' "$LOG-sau.txt" || loi "không lấy được dấu vân bản sao"
# Thay đổi số bản ghi được duyệt trước (vd bản mới thêm tài khoản / kho): DUOC_DOI='dem\.(Account|Warehouse)$'
BOQUA=(); [ -n "${DUOC_DOI:-}" ] && BOQUA=(--bo-qua "$DUOC_DOI")
python3 deploy/release/so_dau_van.py "$LOG-truoc.txt" "$LOG-sau.txt" --phan tong,dem,chi_tiet "${BOQUA[@]}" > "$LOG-so.txt" \
  || { grep -v ": khớp\|lệch 0$" "$LOG-so.txt" | head -60; loi "sổ bản sao lệch"; }
grep "^tong\|^dem\|^chi_tiet:\|KẾT QUẢ" "$LOG-so.txt"

python3 deploy/release/dau_dien_tap.py tao "$DAU" --pb "$PB" --image "$IMG_ID" --nguon "$(git -C "$TK" rev-parse HEAD)" \
  --khach khach/aph-vh/khach.json --site "$SITE_GOC" --co ${CO_MOI[@]+"${CO_MOI[@]}"}
echo "=== DIỄN TẬP $PB: ĐẠT (lượt $RID, dấu $DAU, còn hạn 12 giờ, chỉ dùng được cho đúng image / commit / khach.json / cờ này) ==="
