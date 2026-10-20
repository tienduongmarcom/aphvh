# Đợt3B — nhận chờ định giá gắn từng dòng đơn mua

## 1. Mục tiêu và phạm vi

Nối cửa sổ nhận nhà máy vào APH Pending Receipt đã có, không tạo chứng từ/sổ kho thứ hai. Lát này chỉ đơn mua VND/tỷ giá1 và hàng tồn Kg/hệ số1 từ PO đã xác nhận, không lô/sê-ri/gia công/giao thẳng. Phiếu chờ chưa vào tồn khả dụng; không dùng giá0 để ghi kho. Nhận không PO theo màn chuẩn hiện có giữ nguyên, không tự gán nguồn cho hồ sơ cũ. Tái dùng cờ26 factory_receiving mặc định tắt.

## 2. Hiện trạng và phần thay đổi

PR #17/1fffcba đã kiểm nhận có giá. Baseline trước PR #18: pending_valuation.finalize tạo PR độc lập, chưa lưu PO/dòng nguồn. Thêm Link PO trên pending, ID dòng PO trên child, dấu lượt/hồ sơ nhận giống lát3A; lượng chờ giữ chỗ cho đúng dòng. Mọi đường PR/PI cập nhật kho phải kiểm tổng đã nhận+chờ+nhận lần này không vượt PO. Phần giữ chỗ bảo vệ hồ sơ đã phát sinh kể cả khi tắt cờ; tắt cờ không giải phóng hàng đã nhận vật lý.

## 3. Quy trình và trách nhiệm

Nhà máy chọn PO, chọn nhận chờ định giá, nhập tổng kg/bao/người nhận/tệp cân/ghi chú/phần có vấn đề. Submit một pending, chưa có SLE/GL/PLE. Kế toán trưởng cập nhật giá hợp lệ trên PO bằng lối chuẩn rồi chốt giá trên pending; giá từng dòng phải bằng PO hiện hành. Native mapper giữ PO/taxes/links và native quyền PR; không bỏ quy tắc cùng giá. Một PR đã submit thay thế lượng giữ chỗ; retry mở đúng kết quả. Người vận hành ký giấy không cần tài khoản.

## 4. Quy tắc và ngoại lệ

Còn nhận = qty PO − received_qty native − tổng pending đã submit chưa có PR hoạt động. Nháp pending không giữ chỗ; kiểm lại lúc submit. Hai phiên dùng khóa Company→PO→pending và đọc hiện tại; retry có giới hạn chỉ ở RPC của chính nghiệp vụ khi DB xung đột. PR native và PI update_stock có hook khóa/kiểm cùng nguồn, không chỉ màn nhanh. Gộp nhiều dòng cùng nguồn trước kiểm. Hủy PR làm lượng pending trở lại giữ chỗ; muốn nhận lại phải hủy pending sau xử lý PR. Không xóa hồ sơ có mã lượt, không sửa nguồn/lượng/hồ sơ sau xác nhận. Hủy/giảm PO không được bỏ lượng đang chờ; thay giá theo native còn được nếu không phá nguồn/lượng. Chốt PO đóng/tạm giữ phải xử lý PO trước.

Hàng có vấn đề vẫn là phần trong tổng thực nhận, ghi để đàm phán; không tự trả/giảm giá. Hàng chưa định giá vẫn ngoài khả dụng theo quy tắc hiện có; không suy câu “thường dùng ngay” thành quyền xuất tồn giá0.

## 5. Dữ liệu và trạng thái

Pending thêm kh_aph_receiving_purchase_order Link PO, tám dấu kh_aph_receiving_{request,payload,actor,at,receiver,ticket,note,price_review}; child thêm kh_aph_receiving_source_row Data và kh_aph_receiving_quality_qty Float. Dấu readonly/no_copy, request unique/hidden/NULL cho phiếu cũ. Nguồn/chất lượng readonly, chỉ service tạo. Một pending chỉ một PO, company/supplier/item/warehouse đúng nguồn/phạm vi quyền. Chỉ trạng thái cũ Chờ định giá→Đã định giá và docstatus chuẩn. Dấu giá cần đàm phán là snapshot lúc nhận, không là workflow giải quyết giá.

## 6. Quyền và kiểm soát

Factory guard/Company/Supplier/Item/Warehouse/PO read như3A; thêm quyền native pending create/submit/read, không cấp thêm role hoặc ignore_permissions. Finalize chỉ Administrator hoặc Accounts Manager không có hồ sơ bị chặn giá; native PR create/submit/read vẫn kiểm. Tệp mới private, chính người tạo sở hữu và chưa gắn hồ sơ; gắn pending trong cùng transaction. PR định giá giữ hồ sơ tham chiếu pending, không chuyển mất bản gốc. API đọc trả allowlist lượng/mã, không giá cho NoCost. SQL tổng giữ chỗ chỉ trả tổng nội bộ của dòng PO đã được xác thực, không lộ tên/hồ sơ ngoài quyền.

## 7. Tác động hệ thống

Pending không tăng tồn/SLE/GL/PLE/sổ bao khả dụng. Finalize một PR native mới tăng kho/giá trị/sổ bao và received_qty PO, không giảm nợ khách/thu tiền. Không can thiệp sản xuất, MISA, kho dở dang. Không backfill PO cho phiếu chờ cũ. Kiểm all-writer bao gồm PI update_stock, giữ native validation và transaction rollback khi lỗi.

## 8. Tiêu chí kiểm

PO giá0 chỉ được nhận pending, không finalize giá0 hoặc nhập kho có giá0. PO10kg: pending4 gồm1kg vấn đề giữ chỗ4, nhận có giá còn6; retry pending không tăng chứng từ/sổ, đổi mode/nội dung cùng nonce bị chặn. Nháp không giữ chỗ; submit native giả nguồn bị chặn. Hai phiên pending/nhập có giá tranh phần còn: không vượt10. PR chuẩn và PI update_stock không lấy lượng đang chờ, kể cả tắt26. Chốt giá bằng vai trò sai/giá0/giá lệch PO/sai dòng bị chặn; cập nhật PO rồi finalize một PR4kg đúng source, pending không bị tính thêm lần nữa. Retry một PR; hủy PR trả giữ chỗ, hủy pending sau đó giải phóng; hồ sơ giữ lịch sử. PO giảm/xóa dòng/hủy khi còn pending bị chặn. File private và NoCost không lộ giá; Chrome cùng Dialog mất phản hồi/bấm lại một pending. Kiểm cục bộ, HTTP/Desk,4 cổng cùng SHA và artifact/ảnh. Chưa tuyên bố PASS khi chưa có bằng chứng.

## 9. Triển khai và khôi phục

Schema qua factory_receiving.schema/bộ cài rõ ràng, không after_migrate tự bật. Tái dùng26, không đổi version/tag/production. Hồ sơ cũ không nguồn vẫn hoạt động như trước. Lúc nâng production cần diễn tập bản sao có dữ liệu; quay lui image+DB/files/cờ đồng bộ, không chỉ tắt cờ để bỏ giữ chỗ. Nghiệm thu nhân sự/dữ liệu thật gom cuối. Đã kiểm kỹ thuật đủ4 cổng đúnga75ced9b8b4613d71fe45117bc36b7215f85877d (20/10/2026); artifact/ảnh đã đọc/xem, liên kết trong docs/ban-giao.md. Nghiệm thu nhân sự/dữ liệu thật vẫn chờ đợt cuối.


Bộ ca tích hợp mới (8 ca): HTTP_3B_PENDING_RESERVE_REPLAY; HTTP_3B_NATIVE_RESERVATION_FLAG_OFF; HTTP_3B_PENDING_SOURCE_TAMPER; HTTP_3B_PENDING_VALUED_RACE; HTTP_3B_PENDING_FINALIZE_ONCE; HTTP_3B_PENDING_CANCEL_HISTORY; HTTP_3B_UNPRICED_ORDER_PENDING_ONLY; DESK_3B_PENDING_RETRY. Đã PASS b014102/toàn HTTP293,0 FAIL trên a75ced9; cục bộ419+108,4 cổng cùng mã đạt. Không tính unit thay HTTP/Desk.


| Yêu cầu | Ca tự kiểm truy nguyên | Kết quả bắt buộc |
|---|---|---|
| 3B01 ghi lượng, tệp và bấm lặp | HTTP_3B_PENDING_RESERVE_REPLAY | pending4/PO10, còn6, không SLE/GL/PLE mới; tệp private đúng hồ sơ |
| 3B02 tất cả lối nhập tôn trọng giữ chỗ | HTTP_3B_NATIVE_RESERVATION_FLAG_OFF | PR/PI cập nhật kho vượt phần còn bị chặn cả khi26=0 |
| 3B03 dữ liệu/nguồn bất biến | HTTP_3B_PENDING_SOURCE_TAMPER | đổi mode/giả giá/gỡ PO/giảm PO/hủy PO còn chờ bị chặn |
| 3B04 nhận đồng thời | HTTP_3B_PENDING_VALUED_RACE | hai phiên khác mode mỗi4 khi còn6, chỉ một thành công, còn2 |
| 3B05 quyền và chốt giá | HTTP_3B_PENDING_FINALIZE_ONCE | NoCost bị chặn; giá sai PO bị chặn; đúng giá tạo PR4 đúng dòng, retry một PR |
| 3B06 hủy và lịch sử | HTTP_3B_PENDING_CANCEL_HISTORY | hủy PR trả giữ chỗ; hủy pending giải phóng; không xóa hồ sơ/tệp |
| 3B07 chưa có giá thật | HTTP_3B_UNPRICED_ORDER_PENDING_ONLY | mã mới/PO.rate=0 chỉ được pending, finalize0 bị chặn |
| 3B08 cửa sổ thật và mất phản hồi | DESK_3B_PENDING_RETRY | NoCost, bỏ200 sau commit/bấm lại cùng Dialog một pending1kg, không thêm sổ |
