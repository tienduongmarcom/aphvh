#!/usr/bin/env bash
# Sao lưu site ERPNext (CSDL + tệp đính kèm công khai/riêng + cấu hình site) rồi chép lên Cloud Storage.
# Chạy bằng root qua systemd (erpnext-backup.timer). Cấu hình ở /etc/erpnext-backup.conf:
#   BUCKET=gs://<tên-bucket>
# Frappe tự xóa bản sao lưu cục bộ cũ hơn 23 giờ mỗi lần sao lưu, nên lịch sử dài hạn nằm trên bucket
# (bucket tự xóa bản cũ theo quy tắc vòng đời).
set -euo pipefail

CONF=/etc/erpnext-backup.conf
[ -r "$CONF" ] && . "$CONF"
: "${BUCKET:?Chưa đặt BUCKET trong $CONF}"
SITE="${SITE:-frontend}"
CONTAINER="${CONTAINER:-erpnext-clean-backend-1}"
VOLUME="${VOLUME:-erpnext-clean_sites}"
GCLOUD="${GCLOUD:-/snap/bin/gcloud}"

DIR="$(docker volume inspect "$VOLUME" --format '{{ .Mountpoint }}')/${SITE}/private/backups"

MARK="$(mktemp)"
trap 'rm -f "$MARK"' EXIT
sleep 1

docker exec "$CONTAINER" bench --site "$SITE" backup --with-files

mapfile -t FILES < <(find "$DIR" -maxdepth 1 -type f -newer "$MARK" | sort)
if [ "${#FILES[@]}" -ne 4 ]; then
    echo "Sao lưu không đủ 4 tệp (có ${#FILES[@]}): ${FILES[*]:-}" >&2
    exit 1
fi
for f in "${FILES[@]}"; do
    [ -s "$f" ] || { echo "Tệp rỗng: $f" >&2; exit 1; }
done

DEST="${BUCKET%/}/${SITE}/$(TZ=Asia/Ho_Chi_Minh date +%Y-%m-%d_%H%M)/"
"$GCLOUD" storage cp "${FILES[@]}" "$DEST"
echo "Đã chép ${#FILES[@]} tệp lên $DEST"
