# Chuyển ứng viên sang frontend

## Hiện trạng và cách đóng gate (13/10/2026, bản 0.10.0)

- **Kiểm kê chỉ đọc đã chạy trên VM** (`collect_frontend_inventory.py` ở SHA 3ef5cf0): Frappe 16.35.0 / ERPNext 16.36.1 /
  lab9x 0.2.0 / kh_aph 0.9.1; 6 service cùng image `kh-aph-erpnext:0.9.1@sha256:ce75590079309b678b2a15cc2e4a8ccc413345f1eff30b07bd161cd435107bb1`;
  Compose `/home/tienduongmarcom/erp/aph-vh`; 4 company APH/VH/MK/TL; chỉ 4 kho gốc "All Warehouses"; 0 khách,
  0 mặt hàng, 0 chứng từ, 0 GL/SLE/PLE; chỉ user Administrator; mọi cờ tắt. RAM 3,9 GB (2,5 GB trống), đĩa 23 GB trống.
- **Bộ cài production**: `kh_aph.cai_dat_tinh_nang.cai/kiem` dùng chính phần schema đã kiểm trên UAT; khóa
  Administrator + gõ đúng tên site + đủ 8 cờ + site chưa có dữ liệu nghiệp vụ. `setup_uat` vẫn chỉ cho UAT.
- **Migration/rollback rehearsal**: vì frontend trắng, thay bản sao trên VM bằng **Cổng 3** (CI) dựng từ đúng digest
  production ở trên → `nang-cap.sh` → bộ cài → so schema với site dựng mới → `quay-lui.sh` → dấu vân
  (`dau_van_site.py`: đếm, tổng GL/SLE/Bin/PLE, schema, cờ) khớp bản trước nâng cấp. Phát hành cần Cổng 3.
- **Mục 3–4 dưới đây vẫn bắt buộc nếu frontend đã có dữ liệu** khi tới cửa sổ triển khai (kiểm lại ở bước 1 của
  `TRIEN_KHAI_FRONTEND.md`).
- Thủ tục cửa sổ triển khai: `deploy/release/TRIEN_KHAI_FRONTEND.md`.


Đây là thứ tự thực hiện và tiêu chí kiểm chứng. Chưa phải bằng chứng production
đã triển khai. Không chạy script UAT trắng lên frontend, không sửa writable layer
của container production và không ghi đè tag 0.9.1.

## 1. Kiểm kê thực tế — chỉ đọc

Từ checkout đúng SHA, trên VM đang chứa các container đã biết:

```sh
python3 deploy/release/collect_frontend_inventory.py
```

Hai script cạnh nhau là độc lập với app ứng viên; dùng app hiện có trong backend.
SQL chạy transaction READ ONLY rồi rollback. Không xuất site_config/password/key.
Output cho biết version, company, kho, item, role, account và đường dẫn Compose.
`NOT_TESTED` là trạng thái nghiệp vụ bắt buộc; đọc thành công không phải UAT PASS.

Kiểm tra version thực tế Frappe 16.35.0 / ERPNext 16.36.1 / lab9x 0.2.0 / kh_aph
0.9.1; nếu khác phải đối chiếu trước khi lựa chọn image. TL là XB. Chỉ dùng site
frontend, không erpnext.local. Kho lá phải thuộc đúng company; item stock phải dùng
Kg/Moving Average với quy cách bao đã thống nhất. Không tự tạo tài khoản vốn/nợ
liên company dựa vào số hiệu thử nghiệm trong CI.

## 2. Đóng bản code và bằng chứng

Source SHA, base-image digest, candidate image digest và log UAT phải đi cùng nhau.
Hồi quy bao/kg, tồn riêng company, nợ lúc giao, trả/hủy, vốn, sản xuất/phụ phẩm,
tiền thực thu/cọc, đổi nguồn và guard người không xem vốn cần xanh trên cùng SHA.
Mọi FAIL phải giữ nguyên trong bằng chứng và xử lý; không đổi assertion để che lỗi.
Không lấy dữ liệu test giả lập thay cho tài khoản Dũng/kế toán trưởng thật.

## 3. Snapshot và rehearsal trên bản sao

Backup frontend bằng `bench --site frontend backup --with-files` trong backend với
cwd /home/frappe/frappe-bench. Giữ database/public/private cùng thời điểm và cấu
hình mã hóa ở nơi hạn chế truy cập; không gửi khóa lên chat/artifact công khai.
Giữ image ID/digest của cả sáu service app và tệp Compose đúng hiện trạng.

Phục hồi backup vào volume/site/db/Redis tách biệt; tắt scheduler, email và MISA
thật. Kiểm tra counts/balance trước migrate. Clone phải phản ánh dữ liệu thật,
không thay bằng CI site trắng. Dùng schema installer đã kiểm chứng trên clone;
`uat_candidate_setup.setup_uat` bị giới hạn cho site UAT; installer production là
`kh_aph.cai_dat_tinh_nang` (từ 0.10.0, chỉ nhận site chưa có dữ liệu nghiệp vụ). Review trước/sau Custom Field, Property Setter, DocPerm và chart;
không reset toàn bộ quyền hoặc tạo lại hệ thống tài khoản production.

Đối chiếu GL, SLE, Payment Ledger, Bin và số bao vật lý mở đầu. Kho chỉ có kg mà
chưa có bao thì cần kiểm kê vật lý; không suy ra số bao lịch sử bằng cách chia kg
cho quy cách hiện tại. Tiền đã thu phải đối chiếu đúng bank/quỹ của company thực
nhận; mapping thu hộ được kế toán duyệt. Không tự cấn nợ cũ hoặc FIFO.

## 4. Rollback diễn tập

Trước khi chạy thật, phục hồi cùng backup với image cũ trên clone rồi so counts,
series, GL/SLE/Payment Ledger/Bin và file. Chỉ coi rollback PASS sau phục hồi thực.
Migrate có thể ghi schema ngoài transaction; SQL rollback không thay backup.

Khi deploy thực, giữ cửa sổ dừng nhập liệu, queue và scheduler theo Compose đã
kiểm kê; đổi cùng image cho frontend/backend/queue-short/queue-long/websocket/
scheduler. Không đổi một backend rồi để worker cũ xử lý cùng database.
Nếu cần rollback trước mở nhập liệu: phục hồi cùng snapshot database/files và
image/Compose cũ. Sau mở nhập liệu, không tự restore làm mất giao dịch mới;
cần đối soát và phương án forward fix/thu hồi giao dịch có ghi nhận.

## 5. Mở production

Chỉ mở nhập liệu sau kiểm tra site/frontend route, Desk, role thật, lượng tồn và
công nợ thực; các flags chỉ bật khi schema và cấu hình liên quan đã kiểm chứng.
MISA tiếp tục chỉ hóa đơn thuế; chứng từ ERP ghi tồn/công nợ vận hành.
Full 202 cần bản quyết định gốc để đối chiếu từng dòng; không tuyên bố 202/202
từ bản tóm lược hoặc từ tổng số test.
