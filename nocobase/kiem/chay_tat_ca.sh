#!/usr/bin/env bash
# Chạy toàn bộ kiểm thử trên BẢN THỬ: bộ 0.3.2 nguyên vẹn (cấu hình tương thích 0.3.2) rồi bộ 0.4.0 (cấu hình 0.4.0) + đối chiếu.
#   EMAIL=… MAT_KHAU=… URL=http://localhost:13000 bash chay_tat_ca.sh
set -u
cd "$(dirname "$0")"
A=(--url "${URL:-http://localhost:13000}" --email "$EMAIL" --password "$MAT_KHAU")
loi=0
python3 cau_hinh.py "${A[@]}" cu || exit 1
for f in kiem_api kiem_quyen kiem_golive kiem_032; do
  echo "===== $f (0.3.2)"; python3 $f.py "${A[@]}" | tail -2 || loi=1
  [ "${PIPESTATUS[0]}" = 0 ] || loi=1
done
python3 cau_hinh.py "${A[@]}" moi || exit 1
echo "===== kiem_040"; python3 kiem_040.py "${A[@]}" | tail -4; [ "${PIPESTATUS[0]}" = 0 ] || loi=1
echo "===== đối chiếu"; python3 doi_chieu.py "${A[@]}" | tail -1 || loi=1
[ $loi = 0 ] && echo "TẤT CẢ ĐẠT" || echo "CÓ BỘ KIỂM LỖI"
exit $loi
