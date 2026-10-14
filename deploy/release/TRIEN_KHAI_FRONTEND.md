# Triển khai bản 0.11.4 lên `frontend` (máy erpnext-prod)

Production đang chạy 0.11.4 (từ 14/10/2026 ~22:15, 15 cờ, digest `54bf5a99…`). Bản 0.11.5 không thêm cờ: `trien_khai_frontend.sh 0.11.5` (không kèm cờ). (Ghi chú cũ:) Bản 0.11.4 (đặc tả `docs/dac-ta-0.11.4.md`) thêm cờ thứ 15
`kh_aph_quan_tri`, gồm:
- 3 báo cáo: lãi gộp quản trị cộng ngang 4 đơn vị, dòng tiền 7 / 30 ngày, khách chưa xác nhận công nợ;
- khóa / mở khóa kỳ trên form Company;
- ghi nhận xác nhận công nợ trên form Customer.

**Chạy trên SSH vào máy chủ erpnext-prod** (user `tienduongmarcom`):

```bash
cd ~/trien-khai && git fetch -q https://github.com/tienduongmarcom/aphvh.git tag v0.11.4 && git checkout -q --detach v0.11.4
bash deploy/release/trien_khai_frontend.sh 0.11.4 kh_aph_quan_tri 2>&1 | tee ~/log-0.11.4-tong.txt
```

**Đạt khi** dòng cuối là `=== XONG 0.11.4: ĐẠT ===`.
- Nâng cấp lỗi thì `nang-cap.sh` tự quay lui.
- Muốn quay lui sau khi đã xong: `./quay-lui.sh <thư mục sao-luu mới nhất>`.

**Sau khi triển khai:**
- Kế toán trưởng khóa từng tháng đã kết thúc trên form Company → Kỳ kế toán → Khóa kỳ. ERPNext không cho khóa tháng đang chạy.
- Chiết khấu hoặc hoa hồng gắn được vào một đơn: ghi bằng bút toán và chọn ô "Đơn bán" trên dòng chi phí.

---

# (Lịch sử) Triển khai bản 0.11.3 lên `frontend` — đã làm 14/10/2026 ~21:00, ĐẠT

Production đang chạy 0.11.2 (từ 14/10/2026 17:10): 13 cờ, cây kho 55 kho, site chưa có dữ liệu nghiệp vụ.

Bản 0.11.3 (đặc tả `docs/dac-ta-0.11.3.md`) thêm cờ thứ 14 `kh_aph_sales_p1`:
- trả hàng 2 chiều (hàng về đâu × xử lý tiền);
- giảm giá sau giao;
- hạn thanh toán chung và gia hạn;
- đổi địa chỉ khi đang giao;
- báo cáo đơn quá hạn giao;
- hồ sơ hóa đơn MISA có hàng đợi và khóa chống trùng.

**Điều kiện:**
- Tag `v0.11.3` phát hành xanh: UAT candidate (b0111 14, b0112 13, b0113 13), Cổng 2, 2b, Cổng 3 (nâng cấp từ 0.11.2 theo
  digest).
- Bước 1 phải TRẮNG.

**Chạy trên SSH vào máy chủ erpnext-prod** (user `tienduongmarcom`). Repo công khai nên không cần token:

```bash
cd ~/trien-khai
git fetch -q https://github.com/tienduongmarcom/aphvh.git tag v0.11.3 && git checkout -q --detach v0.11.3
bash deploy/release/trien_khai_frontend.sh 0.11.3 kh_aph_sales_p1 2>&1 | tee ~/log-0.11.3-tong.txt
```

**Đạt khi** dòng cuối là `=== XONG 0.11.3: ĐẠT ===`.
- Script dừng ngay ở bước lỗi và in `!!! DỪNG: …`. Nâng cấp lỗi thì `nang-cap.sh` tự quay lui.
- Bộ dựng cây kho chạy lại phải báo "tạo 0".
- Dòng cuối của log in digest image 0.11.3: gửi lại để ghim cho Cổng 3 của bản sau.

**Quay lui trước khi nhập liệu:** `cd ~/erp/aph-vh && ./quay-lui.sh <thư mục sao-luu mới nhất>`. Hệ thống về 0.11.2.

**Cấu hình khách sau 0.11.3:**
- Kế toán đặt "Điều khoản thanh toán" (Payment Terms Template) trên từng khách để đơn tự có hạn chung.
- Công ty có "Tài khoản tiền mặt mặc định" để phiếu chi hoàn tiền tự lập.

---

# (Lịch sử) Triển khai bản 0.11.2 lên `frontend` — đã làm 14/10/2026 ~17:10, ĐẠT (script gộp `~/trien-khai-0112.sh`)

Production đang chạy 0.11.1 (từ 14/10/2026 14:43): 12 cờ bật, đã chạy bộ cài 0.11.1, site chưa có dữ liệu nghiệp vụ.

Bản 0.11.2 (đặc tả `docs/dac-ta-0.11.2.md`):
- Thêm cờ thứ 13 `kh_aph_kho_chuan`: cây kho chuẩn do app dựng, ô Loại kho, chặn bán từ kho không bán, đóng gói 2 công
  đoạn ("Đóng gói thành phẩm"), bao bì không cộng kg, kiểm kê có mốc.
- Quyết toán dở dang về 0 theo định mức (cờ `kh_aph_factory_costing` sẵn có), báo cáo "Tiêu hao so với định mức".
- Gỡ ô "Kho bồn dở dang" của 0.11.1 (production chưa dùng).

**Điều kiện:**
- Tag `v0.11.2` đã phát hành với các cổng xanh: UAT candidate (bộ 0.11.1 đủ 14 PASS, bộ 0.11.2 đủ 13 PASS), Cổng 2,
  Cổng 2b, **Cổng 3 (nâng cấp từ 0.11.1)**.
- Kiểm kê bước 1 phải TRẮNG. Không TRẮNG thì **dừng**.

Tất cả lệnh dưới đây chạy **trên SSH vào máy chủ erpnext-prod**, user `tienduongmarcom`:

```bash
# 0. Lấy script đúng bản phát hành (token chỉ đọc nhập bằng read -s, không lưu)
cd ~/trien-khai
read -s -p "Token chỉ đọc: " GH_TOKEN; echo
git fetch "https://x-access-token:${GH_TOKEN}@github.com/tienduongmarcom/aphvh.git" tag v0.11.2
unset GH_TOKEN
git checkout --detach v0.11.2 && git log --oneline -1

# 1. Dấu vân trước (chỉ đọc): phải TRẮNG, kh_aph 0.11.1, 12 cờ = 1, kh_aph_kho_chuan = 0
#    Ghi digest image 0.11.1 đang chạy (gửi lại để điền PROD_DIGEST của Cổng 3 cho bản sau)
docker image inspect "$(docker inspect -f '{{.Image}}' erp-aph-vh-backend-1)" -f '{{json .RepoDigests}}'
docker exec -i -w /home/frappe/frappe-bench/sites erp-aph-vh-backend-1 /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-0112-truoc.txt
python3 deploy/release/kiem_trang.py ~/dv-0112-truoc.txt

# 2. Sao lưu lên Cloud Storage ngay trước
sudo systemctl start erpnext-backup.service && sudo journalctl -u erpnext-backup.service -n 5 --no-pager

# 3. Cập nhật script vận hành (quay-lui.sh 0.11.2 biết cờ thứ 13) và cấu hình khách (có mục cay_kho)
cp deploy/khach-hang/nang-cap.sh deploy/khach-hang/quay-lui.sh ~/erp/aph-vh/
cp khach/aph-vh/khach.json ~/erp/aph-vh/khach.json

# 4. Nâng cấp cả 6 service (tự sao lưu trước, migrate, kiểm; lỗi thì tự quay lui về 0.11.1)
cd ~/erp/aph-vh && ./nang-cap.sh 0.11.2
#    Phải thấy "== XONG: 0.11.1 -> 0.11.2, kiểm đạt". Ghi lại thư mục sao-luu/<NGAY>.

# 5. Bật cờ mới, chạy bộ cài (gõ đúng tên site), dựng cây kho (chạy 2 lần: lần 2 phải "tạo 0"), kiểm
./erpctl exec -T backend bench --site frontend set-config -p kh_aph_kho_chuan 1
./erpctl exec -T backend bench --site frontend execute kh_aph.cai_dat_tinh_nang.cai --kwargs '{"xac_nhan_site": "frontend"}'
./erpctl exec -T backend bench --site frontend execute kh_aph.cai_dat_tinh_nang.kiem --kwargs '{"xac_nhan_site": "frontend"}'
./erpctl exec -T backend bash -c 'cat > /tmp/khach.json' < khach.json
./erpctl exec -T backend bench --site frontend execute kh_aph.kho_chuan.dung --kwargs '{"duong_dan": "/tmp/khach.json", "xac_nhan_site": "frontend"}' | tail -8
./erpctl exec -T backend bench --site frontend execute kh_aph.kho_chuan.dung --kwargs '{"duong_dan": "/tmp/khach.json", "xac_nhan_site": "frontend"}' | grep "^Cây kho"
./erpctl exec -T backend bench --site frontend execute kh_aph.kiem_trien_khai.chay --kwargs '{"duong_dan": "/tmp/khach.json"}' | tail -3
./erpctl exec -T backend bench --site frontend clear-cache
./erpctl restart backend queue-short queue-long scheduler websocket frontend

# 6. Dấu vân sau + sao lưu Cloud Storage
cd ~/trien-khai
docker exec -i -w /home/frappe/frappe-bench/sites erp-aph-vh-backend-1 /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-0112-sau.txt
python3 deploy/release/so_dau_van.py ~/dv-0112-truoc.txt ~/dv-0112-sau.txt --phan tong
sudo systemctl start erpnext-backup.service
```

**Đạt khi:**
- Bước 4 in ra "kiểm đạt".
- Bước 5: `"idempotent": true` hai lần; lần dựng cây đầu "Cây kho: tạo 55"; lần hai "Cây kho: tạo 0"; kiểm triển khai có
  dòng "Cây kho chuẩn đủ (55 kho) ĐẠT" và "KHÔNG ĐẠT: 0". Cảnh báo "kho ngoài cây chuẩn" (nếu có) chỉ để kế toán xem.
- Bước 6: phần `tong` khớp (chưa có giao dịch nên GL/SLE/Bin không đổi; số Warehouse tăng 55 là đúng thiết kế).

**Quay lui trước khi nhập liệu:** `cd ~/erp/aph-vh && ./quay-lui.sh <thư mục sao-luu ở bước 4>`. Hệ thống về 0.11.1:
12 cờ bật, `kh_aph_kho_chuan` tắt, cây kho mới mất theo bản sao lưu.

## Cấu hình khách cần làm sau 0.11.2 (kế toán trưởng / anh Hùng / Dũng làm trên giao diện)

1. Nhóm hàng bao bì (túi, thùng, nhãn): tích "Bao bì đóng gói". Mỗi quy cách bao bì một mã riêng (báo cáo rà soát nhóm
   "Bao bì" chỉ ra mã đang mang nhiều quy cách).
2. Thành phẩm đóng thùng / gói: nhập Trọng lượng/đơn vị (kg tịnh) và Đơn vị trọng lượng = Kg.
3. Định mức (BOM): CĐ1 một BOM cho mỗi loại bánh (số lượng = sản lượng một mẻ), CĐ2 một BOM cho mỗi quy cách. Đặt mặc định
   và đang dùng. "Tỷ lệ hao hụt cho phép (%)" để 0 nếu đúng định mức là mức bình thường.
4. Stock Settings: "Ngưỡng chênh lệch kiểm kê cần lý do (%)".
5. Xưởng: hai trung tâm chi phí loại "Xưởng sản xuất" (đã làm ở 0.11.1). Quyết toán: mở kho dở dang → Kho → Quyết toán
   dở dang về 0.

---

# (Lịch sử) Triển khai bản 0.11.1 lên `frontend` — đã làm 14/10/2026 14:43, KHỚP

Production đang chạy 0.11.0: 8 cờ bật, đã chạy bộ cài 0.11.0, site chưa có dữ liệu nghiệp vụ.

Bản 0.11.1:
- Thêm 4 cờ: `kh_aph_factory_costing`, `kh_aph_factory_cash`, `kh_aph_sales_adjust`, `kh_aph_data_review`.
- Sửa lỗi chặn kế toán mở Purchase Invoice, Stock Reconciliation, Landed Cost Voucher, BOM, Work Order và GL. Nguyên nhân:
  hook quyền trả `None`, mà Frappe 16 coi `None` là từ chối. **Phải lên bản này trước khi khách nhập liệu.**

Đặc tả: `docs/dac-ta-0.11.1.md`.

**Điều kiện:**
- Tag `v0.11.1` đã phát hành với các cổng xanh: UAT candidate (bộ ca 0.11.1 đủ 14 PASS), Cổng 2, Cổng 2b, **Cổng 3
  (nâng cấp từ 0.11.0)**.
- Bộ cài vẫn từ chối site đã có dữ liệu nghiệp vụ (khách, mặt hàng, chứng từ, sổ). Nếu kiểm kê ở bước 1 không ra
  TRẮNG thì **dừng**.

Tất cả lệnh dưới đây chạy **trên SSH vào máy chủ erpnext-prod**, user `tienduongmarcom`:

```bash
# 0. Lấy script đúng bản phát hành (token chỉ đọc nhập bằng read -s, không lưu)
cd ~/trien-khai
read -s -p "Token chỉ đọc: " GH_TOKEN; echo
git fetch "https://x-access-token:${GH_TOKEN}@github.com/tienduongmarcom/aphvh.git" tag v0.11.1
unset GH_TOKEN
git checkout --detach v0.11.1 && git log --oneline -1

# 1. Dấu vân trước (chỉ đọc): phải TRẮNG, kh_aph 0.11.0, 8 cờ cũ = 1, 4 cờ mới = 0
docker exec -i -w /home/frappe/frappe-bench/sites erp-aph-vh-backend-1 /home/frappe/frappe-bench/env/bin/python - frontend \
  < deploy/release/dau_van_site.py > ~/dv-0111-truoc.txt
python3 deploy/release/kiem_trang.py ~/dv-0111-truoc.txt

# 2. Sao lưu lên Cloud Storage ngay trước
sudo systemctl start erpnext-backup.service && sudo journalctl -u erpnext-backup.service -n 5 --no-pager

# 3. Cập nhật script vận hành (quay-lui.sh 0.11.1 trả lại đủ 12 cờ khi quay lui)
cp deploy/khach-hang/nang-cap.sh deploy/khach-hang/quay-lui.sh ~/erp/aph-vh/

# 4. Nâng cấp cả 6 service (tự sao lưu trước, migrate, kiểm; lỗi thì tự quay lui về 0.11.0)
cd ~/erp/aph-vh && ./nang-cap.sh 0.11.1
#    Phải thấy "== XONG: 0.11.0 -> 0.11.1, kiểm đạt". Ghi lại thư mục sao-luu/<NGAY>.

# 5. Bật 4 cờ mới rồi chạy bộ cài (gõ đúng tên site), kiểm lại
for f in kh_aph_factory_costing kh_aph_factory_cash kh_aph_sales_adjust kh_aph_data_review; do
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
  < deploy/release/dau_van_site.py > ~/dv-0111-sau.txt
python3 deploy/release/so_dau_van.py ~/dv-0111-truoc.txt ~/dv-0111-sau.txt --phan tong
sudo systemctl start erpnext-backup.service
```

**Đạt khi:**
- Bước 4 in ra "kiểm đạt".
- Bước 5 có `"idempotent": true` hai lần và "KHÔNG ĐẠT: 0".
- Bước 6: phần `tong` khớp.

Bộ cài làm ba thay đổi, đều là đúng thiết kế:
- Tạo 6 tài khoản 1548x và 6323 cho APH, nên số đếm Account tăng thêm 6.
- Đổi Selling Settings sang mã khách `KH-.#####`.
- Bật trong Buying Settings tùy chọn cập nhật giá trị nhập kho theo giá hóa đơn mua.

**Quay lui trước khi nhập liệu:** `cd ~/erp/aph-vh && ./quay-lui.sh <thư mục sao-luu ở bước 4>`. Hệ thống về 0.11.0:
8 cờ cũ bật, 4 cờ mới tắt.

### Cấu hình khách sau 0.11.1 (kế toán trưởng làm trên giao diện)

1. Tạo trung tâm chi phí theo Sheet 4 của file tài sản, rồi đặt ô "Loại trong giá thành":
   - Hai xưởng chọn "Xưởng sản xuất".
   - Nhà máy chung chọn "Nhà máy chung" (mỗi công ty chỉ một trung tâm loại này).
2. Nhóm tài sản dùng cho sản xuất: đặt tài khoản chi phí khấu hao là 15484. Trung tâm chi phí trên thẻ tài sản quyết định
   tài sản thuộc xưởng nào.
3. (Thay ở 0.11.2) Kho dở dang do app dựng: "Dở dang dây chuyền đậu / phồng tôm". Hàng dở dang dùng mã hàng rời, không
   quản lý theo bao.
4. Nhóm hàng và mặt hàng:
   - Tích "Cho nhập giá tạm" cho nhóm nguyên liệu, bán thành phẩm, bao bì, vật tư nhà máy.
   - Tích "Thành phẩm chính: giá Hà Nội chốt" cho nhóm thành phẩm chính.
   - Nhập hệ số phẩm cấp trên từng thành phẩm.
5. Company APH: chọn "Quỹ tiền mặt nhà máy" (kế toán tự mở tài khoản tiền chi tiết trước), và lập danh mục
   "APH Khoan muc chi nha may".
6. Làm xong thì chạy lại `kh_aph.handoff_preflight.inspect` như mục cuối tài liệu này.

---

# (Lịch sử) Triển khai bản 0.10.0 lên `frontend` (máy erpnext-prod)

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
sinh sổ); trình duyệt vào được `http://<IP máy chủ erpnext-prod>`, Desk mở, danh sách "APH Shared Sales Order" mở được.

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
