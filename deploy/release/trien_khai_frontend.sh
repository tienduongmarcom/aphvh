#!/bin/bash
# Đưa một bản mới lên site `frontend` trên erpnext-prod trong MỘT lệnh (từ 0.11.3; cùng các bước của TRIEN_KHAI_FRONTEND.md).
# Chạy TRÊN SSH vào máy chủ, trong ~/trien-khai đã checkout đúng tag:
#   bash deploy/release/trien_khai_frontend.sh 0.14.3 [cờ mới ...]
# 0.14.3:
#  - Site có dữ liệu: bắt buộc dấu diễn tập (dien_tap_ban_sao.sh) khớp ĐÚNG phiên bản, image ID, commit nguồn, khach.json, cờ mới,
#    site đích, dưới 12 giờ.
#  - CHẾ ĐỘ BẢO TRÌ từ trước bản sao lưu tới khi mọi bước kiểm đạt (người dùng không ghi được; worker + lịch chạy dừng).
#  - Lỗi ở BẤT KỲ bước nào sau khi bật bảo trì: giữ bảo trì, in nơi lưu bằng chứng + lệnh quay lui. Bước nâng cấp lỗi thì
#    nang-cap.sh tự quay lui.
#  - So sổ trước / sau: tổng, số bản ghi, chi tiết theo công ty / tài khoản / đối tượng, mã hàng / kho, chứng từ, số bao.
# Biến môi trường (CI): ERP_DIR, TAG (tag image, mặc định = phiên bản), SAO_LUU_CLOUD=0, DAU_RA, LOG_RA.
set -euo pipefail
[ $# -ge 1 ] || { echo "Dùng: $0 <phiên bản> [cờ mới ...]"; exit 2; }
PB="$1"; shift; CO_MOI=("$@")
ERP_DIR="${ERP_DIR:-$HOME/erp/aph-vh}"
TAG="${TAG:-$PB}"
DAU_RA="${DAU_RA:-$HOME}"
L="${LOG_RA:-$HOME}"
BAO_TRI=0
loi() {
  echo "!!! DỪNG: $1"
  if [ "$BAO_TRI" = 1 ]; then
    BK="$(ls -td "$ERP_DIR"/sao-luu/*/ 2>/dev/null | head -1 | xargs -r basename)"
    echo "!!! SITE ĐANG Ở CHẾ ĐỘ BẢO TRÌ (người dùng chưa vào được). Bằng chứng: $L/log-$PB-*.txt, $L/dv-$PB-*.txt"
    echo "    Quay lui về bản trước (khôi phục bản sao lưu lúc bắt đầu bảo trì, không mất giao dịch): cd $ERP_DIR && ./quay-lui.sh $BK"
    echo "    Hoặc, nếu đã kiểm thấy ổn, mở lại: cd $ERP_DIR && ./erpctl exec -T backend bench --site frontend set-maintenance-mode off && ./erpctl restart backend && ./erpctl exec -T backend bench --site frontend scheduler resume && ./erpctl up -d"
  fi
  exit 1
}
trap 'loi "lệnh lỗi ở dòng $LINENO"' ERR
TK="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$TK"
grep -q "__version__ = \"$PB\"" kh_aph/__init__.py || loi "thư mục $TK không phải tag v$PB"
# Container backend tìm lại mỗi lần (nâng cấp tạo lại container; tên có thể đổi ID).
be() { (cd "$ERP_DIR" && ./erpctl ps -q backend | head -1); }
dv() { docker exec -i -w /home/frappe/frappe-bench/sites "$(be)" /home/frappe/frappe-bench/env/bin/python - frontend < "$TK/deploy/release/dau_van_site.py"; }
set -a; source "$ERP_DIR/.env"; set +a
IMG="${CUSTOM_IMAGE:-frappe/erpnext}:$TAG"

echo "== 1. Dấu vân (thăm dò) + digest image đang chạy + điều kiện diễn tập"
docker image inspect "$(docker inspect -f '{{.Image}}' "$(be)")" -f '{{json .RepoDigests}}'
dv > "$L/dv-$PB-tham-do.txt"
CO_DL=0
if ! python3 deploy/release/kiem_trang.py "$L/dv-$PB-tham-do.txt"; then
  DAU="$DAU_RA/dien-tap-$PB.ok"
  [ -f "$DAU" ] || loi "site đã có dữ liệu: chạy trước  bash deploy/release/dien_tap_ban_sao.sh $PB ${CO_MOI[*]:-}"
  docker image inspect "$IMG" >/dev/null 2>&1 || docker pull "$IMG"
  python3 deploy/release/dau_dien_tap.py kiem "$DAU" --pb "$PB" --image "$(docker image inspect "$IMG" -f '{{.Id}}')" \
    --nguon "$(git -C "$TK" rev-parse HEAD)" --khach khach/aph-vh/khach.json --site frontend --co ${CO_MOI[@]+"${CO_MOI[@]}"} \
    || loi "dấu diễn tập không khớp bản sẽ triển khai: chạy lại  bash deploy/release/dien_tap_ban_sao.sh $PB ${CO_MOI[*]:-}"
  CO_DL=1
fi

if [ "${SAO_LUU_CLOUD:-1}" = 1 ]; then echo "== 2. Sao lưu Cloud Storage"; sudo systemctl start erpnext-backup.service; fi

echo "== 3. Script vận hành + khach.json"
cp deploy/khach-hang/nang-cap.sh deploy/khach-hang/quay-lui.sh "$ERP_DIR/"
cp khach/aph-vh/khach.json "$ERP_DIR/khach.json"

echo "== 4. BẬT BẢO TRÌ, dừng worker + lịch chạy, dấu vân TRƯỚC (chốt)"
cd "$ERP_DIR"
ex() { ./erpctl exec -T backend bench --site frontend "$@" </dev/null; }
BAO_TRI=1
ex set-maintenance-mode on
# Frappe16.52 giữ site_config trong RAM từng web worker 60 giây.
# CLI đổi file không xóa cache của worker đang chạy; nạp lại trước bước tiếp.
./erpctl restart backend
ex scheduler pause
./erpctl stop queue-short queue-long scheduler
cd "$TK"; dv > "$L/dv-$PB-truoc.txt"; cd "$ERP_DIR"
grep -q '^DAU_VAN ' "$L/dv-$PB-truoc.txt" || loi "không lấy được dấu vân trước"

echo "== 5. Nâng cấp (nang-cap.sh: sao lưu kiểm đủ + sha256, đổi image, migrate, kiểm; lỗi thì tự quay lui)"
set +e
GIU_BAO_TRI=1 ./nang-cap.sh "$TAG" 2>&1 | tee "$L/log-$PB-nang-cap.txt"
set -e
grep -q "kiểm đạt" "$L/log-$PB-nang-cap.txt" || loi "nâng cấp không đạt (xem log; nang-cap.sh đã tự quay lui nếu lỗi sau khi đổi image)"

echo "== 6. Cờ mới + bộ cài + cây kho + kiểm"
for f in ${CO_MOI[@]+"${CO_MOI[@]}"}; do ex set-config -p "$f" 1; done
ex execute kh_aph.cai_dat_tinh_nang.cai --kwargs '{"xac_nhan_site": "frontend", "co_du_lieu": '$CO_DL'}' > "$L/log-$PB-cai.txt"
grep -q '"idempotent": true' "$L/log-$PB-cai.txt" || loi "bộ cài"
ex execute kh_aph.cai_dat_tinh_nang.kiem --kwargs '{"xac_nhan_site": "frontend", "co_du_lieu": '$CO_DL'}' > "$L/log-$PB-kiem-cai.txt"
grep -q '"idempotent": true' "$L/log-$PB-kiem-cai.txt" || loi "kiểm bộ cài"
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
ex execute kh_aph.kho_chuan.dung --kwargs '{"duong_dan": "/tmp/khach.json", "xac_nhan_site": "frontend"}' > "$L/log-$PB-kho.txt"
grep "^Cây kho" "$L/log-$PB-kho.txt" || true
ex execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' > "$L/log-$PB-kiem.txt"
grep "Cây kho chuẩn đủ" "$L/log-$PB-kiem.txt" || true; tail -1 "$L/log-$PB-kiem.txt"
grep -q "KHÔNG ĐẠT: 0" "$L/log-$PB-kiem.txt" || loi "kiểm triển khai có mục KHÔNG ĐẠT"

echo "== 7. Dấu vân SAU, so sổ (vẫn bảo trì)"
cd "$TK"; dv > "$L/dv-$PB-sau.txt"
BOQUA=(); [ -n "${DUOC_DOI:-}" ] && BOQUA=(--bo-qua "$DUOC_DOI")
python3 deploy/release/so_dau_van.py "$L/dv-$PB-truoc.txt" "$L/dv-$PB-sau.txt" --phan tong,dem,chi_tiet ${BOQUA[@]+"${BOQUA[@]}"} > "$L/log-$PB-so.txt" \
  || { grep -v ": khớp\|lệch 0$" "$L/log-$PB-so.txt" | head -60; loi "sổ trước / sau nâng cấp lệch"; }
grep "^tong\|^dem\|^chi_tiet:\|KẾT QUẢ" "$L/log-$PB-so.txt"

echo "== 8. MỞ LẠI: tắt bảo trì, chạy lại lịch + worker"
cd "$ERP_DIR"
ex clear-cache
ex set-maintenance-mode off
# Frappe16.52 giữ site_config trong RAM từng web worker 60 giây.
# CLI đổi file không xóa cache của worker đang chạy; nạp lại trước bước tiếp.
./erpctl restart backend
ex scheduler resume
./erpctl up -d
BAO_TRI=0
trap - ERR
cd "$TK"
if [ "${SAO_LUU_CLOUD:-1}" = 1 ]; then sudo systemctl start erpnext-backup.service; fi
docker images --digests "${CUSTOM_IMAGE:-frappe/erpnext}" | grep -E " $TAG " || true
rm -f "$DAU_RA/dien-tap-$PB.ok"
echo "=== XONG $PB: ĐẠT ==="
