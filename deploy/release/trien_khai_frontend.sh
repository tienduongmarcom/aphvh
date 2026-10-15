#!/bin/bash
# Đưa một bản mới lên site `frontend` trên erpnext-prod trong MỘT lệnh (từ 0.11.3; cùng các bước của TRIEN_KHAI_FRONTEND.md).
# Chạy TRÊN SSH vào máy chủ, trong ~/trien-khai đã checkout đúng tag:
#   bash deploy/release/trien_khai_frontend.sh 0.11.3 kh_aph_sales_p1
# Gặp lỗi ở đâu thì dừng ở đó và in "!!! DỪNG". Bước nâng cấp lỗi thì nang-cap.sh tự quay lui.
set -euo pipefail
[ $# -ge 1 ] || { echo "Dùng: $0 <phiên bản> [cờ mới ...]"; exit 2; }
PB="$1"; shift; CO_MOI=("$@")
loi() { echo "!!! DỪNG: $1"; exit 1; }
BE=erp-aph-vh-backend-1
TK="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TK"
grep -q "__version__ = \"$PB\"" kh_aph/__init__.py || loi "thư mục $TK không phải tag v$PB"

echo "== 1. Dấu vân trước + digest image đang chạy"
docker image inspect "$(docker inspect -f '{{.Image}}' $BE)" -f '{{json .RepoDigests}}'
docker exec -i -w /home/frappe/frappe-bench/sites $BE /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-$PB-truoc.txt
# Từ 0.14.2: site đã có dữ liệu thì phải có diễn tập bản sao ĐẠT cho đúng bản này trong 12 giờ qua
# (bash deploy/release/dien_tap_ban_sao.sh <PB> [cờ mới]); bộ cài khi đó chạy chế độ co_du_lieu=1.
CO_DL=0
if ! python3 deploy/release/kiem_trang.py ~/dv-$PB-truoc.txt; then
  DAU=~/dien-tap-$PB.ok
  [ -f "$DAU" ] || loi "site đã có dữ liệu: chạy trước  bash deploy/release/dien_tap_ban_sao.sh $PB ${CO_MOI[*]:-}"
  python3 - "$DAU" "$PB" <<'PY' || loi "dấu diễn tập không hợp lệ hoặc quá 12 giờ: chạy lại dien_tap_ban_sao.sh"
import json, sys, time
d = json.load(open(sys.argv[1]))
assert d["phien_ban"] == sys.argv[2], d
tuoi = time.time() - d["luc"]
assert 0 <= tuoi < 12 * 3600, tuoi
print(f"Diễn tập bản sao {d['phien_ban']} ĐẠT cách đây {int(tuoi // 60)} phút: tiếp tục, bộ cài chạy chế độ có dữ liệu")
PY
  CO_DL=1
fi

echo "== 2. Sao lưu Cloud Storage"
sudo systemctl start erpnext-backup.service

echo "== 3. Script vận hành + khach.json"
cp deploy/khach-hang/nang-cap.sh deploy/khach-hang/quay-lui.sh ~/erp/aph-vh/
cp khach/aph-vh/khach.json ~/erp/aph-vh/khach.json

echo "== 4. Nâng cấp"
cd ~/erp/aph-vh
./nang-cap.sh "$PB" 2>&1 | tee ~/log-$PB-nang-cap.txt
grep -q "kiểm đạt" ~/log-$PB-nang-cap.txt || loi "nâng cấp không đạt (đã tự quay lui)"

echo "== 5. Cờ mới + bộ cài + cây kho + kiểm"
ex() { ./erpctl exec -T backend bench --site frontend "$@"; }
for f in "${CO_MOI[@]}"; do ex set-config -p "$f" 1; done
ex execute kh_aph.cai_dat_tinh_nang.cai --kwargs '{"xac_nhan_site": "frontend", "co_du_lieu": '$CO_DL'}' | grep -q '"idempotent": true' || loi "bộ cài"
ex execute kh_aph.cai_dat_tinh_nang.kiem --kwargs '{"xac_nhan_site": "frontend", "co_du_lieu": '$CO_DL'}' | grep -q '"idempotent": true' || loi "kiểm bộ cài"
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
ex execute kh_aph.kho_chuan.dung --kwargs '{"duong_dan": "/tmp/khach.json", "xac_nhan_site": "frontend"}' | grep "^Cây kho"
ex execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' > ~/log-$PB-kiem.txt
grep "Cây kho chuẩn đủ" ~/log-$PB-kiem.txt || true; tail -1 ~/log-$PB-kiem.txt
grep -q "KHÔNG ĐẠT: 0" ~/log-$PB-kiem.txt || loi "kiểm triển khai có mục KHÔNG ĐẠT"
ex clear-cache
./erpctl restart backend queue-short queue-long scheduler websocket frontend

echo "== 6. Dấu vân sau + sao lưu"
cd "$TK"
docker exec -i -w /home/frappe/frappe-bench/sites $BE /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-$PB-sau.txt
python3 deploy/release/so_dau_van.py ~/dv-$PB-truoc.txt ~/dv-$PB-sau.txt --phan tong || loi "tổng sổ lệch"
sudo systemctl start erpnext-backup.service
docker images --digests ghcr.io/tienduongmarcom/kh-aph-erpnext | grep -E " $PB " || true
rm -f ~/dien-tap-$PB.ok
echo "=== XONG $PB: ĐẠT ==="
