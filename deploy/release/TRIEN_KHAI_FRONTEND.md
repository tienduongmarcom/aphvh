# Triển khai bản 0.10.0 lên `frontend` (máy erpnext-prod)

Áp dụng **chỉ khi** kiểm kê ngay trước cửa sổ xác nhận site vẫn **chưa có dữ liệu nghiệp vụ** (như kiểm kê chỉ đọc
13/10/2026: 0 khách, 0 mặt hàng, 0 chứng từ, 0 dòng GL/SLE/PLE; 6 service cùng image
`kh-aph-erpnext:0.9.1@sha256:ce755900…`; mọi cờ tắt). Nếu đã có dữ liệu: **dừng**, làm quy trình bản sao + đối chiếu
sổ trong `RELEASE_GATES.md` mục 3–4; bộ cài `kh_aph.cai_dat_tinh_nang` cũng tự từ chối site có dữ liệu.

Vì site trắng, bản sao cô lập trên VM được thay bằng **Cổng 3** (CI): dựng từ đúng image production theo digest,
nâng cấp, cài, so schema với site dựng mới, quay lui và so dấu vân (số bản ghi, tổng GL/SLE/Bin/PLE, schema, cờ)
khớp bản trước nâng cấp. Trên VM vẫn giữ: sao lưu trước (nang-cap.sh + Cloud Storage), tự quay lui khi lỗi.

## Điều kiện trước cửa sổ

1. Tag `v0.10.0` đã phát hành: workflow "Phát hành image" xanh (UAT candidate, Cổng 2, 2b, **3**), image
   `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.10.0`. Ghi lại digest image và SHA nguồn vào biên bản.
2. Không ai đang nhập liệu (site trắng). Thông báo khách: hệ thống tạm dừng ~30 phút.

## Các bước (chạy trên VM, SSH user tienduongmarcom)

```bash
# 0. Lấy script đúng bản phát hành (token chỉ đọc nhập bằng read -s, không lưu)
cd ~/trien-khai
read -s -p "Token chỉ đọc: " GH_TOKEN; echo
git fetch "https://x-access-token:${GH_TOKEN}@github.com/tienduongmarcom/aphvh.git" tag v0.10.0
unset GH_TOKEN
git checkout --detach v0.10.0 && git log --oneline -1

# 1. Dấu vân trước (chỉ đọc) — mọi số đếm nghiệp vụ phải = 0, nếu không thì DỪNG
docker exec -i -w /home/frappe/frappe-bench/sites erp-aph-vh-backend-1 /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-0-truoc.txt
python3 - ~/dv-0-truoc.txt <<'EOF'
import json,sys
d=json.loads([l for l in open(sys.argv[1]) if l.startswith("DAU_VAN ")][0][8:])
nv=("Customer","Supplier","Item","Sales Order","Delivery Note","Sales Invoice","Purchase Order","Purchase Receipt",
    "Purchase Invoice","Payment Entry","Journal Entry","Stock Entry","Stock Reconciliation","GL Entry",
    "Stock Ledger Entry","Payment Ledger Entry")
co={k:d["dem"][k] for k in nv if d["dem"].get(k)}
print("versions",d["versions"]); print("co",d["co"])
print("DỪNG: site đã có dữ liệu", co) if co else print("TRẮNG: được tiếp tục")
EOF

# 2. Sao lưu lên Cloud Storage ngay trước
sudo systemctl start erpnext-backup.service && sudo journalctl -u erpnext-backup.service -n 5 --no-pager

# 3. Cập nhật script vận hành của khách (quay-lui.sh mới trả lại cờ khi quay lui)
cp deploy/khach-hang/nang-cap.sh deploy/khach-hang/quay-lui.sh ~/erp/aph-vh/

# 4. Nâng cấp cả 6 service (tự sao lưu trước, migrate, kiểm; lỗi thì tự quay lui về 0.9.1)
cd ~/erp/aph-vh && ./nang-cap.sh 0.10.0
#    Phải thấy: "5/5 == XONG: 0.9.1 -> 0.10.0, kiểm đạt". Ghi lại thư mục sao-luu/<NGAY>.
./erpctl ps

# 5. Bật 8 cờ rồi chạy bộ cài (gõ đúng tên site), kiểm lại
for f in kh_aph_server_cost_guard kh_aph_post_receivable_on_delivery kh_aph_shared_sales_order \
         kh_aph_global_credit_warning kh_aph_high_risk_credit_guard kh_aph_quantity_valuation_mvp \
         kh_aph_funds_workflow kh_aph_source_change; do
  ./erpctl exec -T backend bench --site frontend set-config -p "$f" 1
done
./erpctl exec -T backend bench --site frontend execute kh_aph.cai_dat_tinh_nang.cai --kwargs '{"xac_nhan_site": "frontend"}'
./erpctl exec -T backend bench --site frontend execute kh_aph.cai_dat_tinh_nang.kiem --kwargs '{"xac_nhan_site": "frontend"}'
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
./erpctl exec -T backend bench --site frontend execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' | tail -3
./erpctl exec -T backend bench --site frontend clear-cache
./erpctl restart backend queue-short queue-long scheduler websocket frontend

# 6. Dấu vân sau + sao lưu Cloud Storage
cd ~/trien-khai
docker exec -i -w /home/frappe/frappe-bench/sites erp-aph-vh-backend-1 /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-1-sau.txt
python3 deploy/release/so_dau_van.py ~/dv-0-truoc.txt ~/dv-1-sau.txt --phan tong
sudo systemctl start erpnext-backup.service
```

Đạt khi: bước 4 "kiểm đạt"; bước 5 có `"idempotent": true` hai lần và "KHÔNG ĐẠT: 0"; bước 6 `tong` khớp (không phát
sinh sổ); trình duyệt vào được `http://34.143.178.144`, Desk mở, danh sách "APH Shared Sales Order" mở được.

## Quay lui

- **Trước khi mở nhập liệu:** `cd ~/erp/aph-vh && ./quay-lui.sh <thư mục sao-luu của bước 4>` (gõ `CO`). Về image
  0.9.1, khôi phục CSDL + tệp, cờ trả về như bản sao lưu (tắt hết). Đã diễn tập ở Cổng 3.
- **Sau khi đã nhập liệu:** không khôi phục (mất giao dịch mới). Sửa tiến (bản vá) hoặc tắt cờ tính năng lỗi
  (`set-config -p <cờ> 0` + clear-cache + restart 6 service) rồi đối soát.

## Sau triển khai — trước khi nhập giao dịch thật (chưa phải PASS nghiệp vụ)

Người quản trị của khách tạo trên giao diện, mình kiểm lại bằng `kh_aph.handoff_preflight.inspect`:
- Người dùng thật: Dũng gán vai trò **APH Không xem giá vốn**, không System Manager; kế toán trưởng (Accounts
  Manager — người duyệt); người giao/nhận hàng đúng phạm vi. Chạy
  `bench --site frontend execute kh_aph.handoff_preflight.inspect --kwargs '{"dung_user": "<email Dũng>"}'`.
- Cây kho: kho lá thuộc đúng công ty sở hữu hàng.
- Mặt hàng tồn kho: ĐVT Kg, Moving Average, khai "Quy cách kg/bao" nếu quản lý theo bao; số bao mở đầu theo kiểm
  kê vật lý (không suy từ kg chia quy cách).
- Tài khoản ngân hàng/quỹ thực nhận, tài khoản giữ hộ và phải thu nội bộ cho tuyến APH nhận phần TL: kế toán trưởng
  duyệt (không lấy số hiệu tài khoản trong dữ liệu CI).
