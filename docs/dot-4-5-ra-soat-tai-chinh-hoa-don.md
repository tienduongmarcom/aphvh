# Đợt 4–5 — rà nguồn tài chính và điểm cần chốt (Claude, 20/10/2026)

Tài liệu rà soát, **không phải** tuyên bố hoàn thành. Theo kế hoạch: kiểm code/ca đã có trước, không kết luận "chưa có" chỉ vì
thiếu màn tổng hợp; phần cần quyết định nghiệp vụ thì ghi lại, không tự suy diễn.

## Đợt 4 — đối chiếu nguồn đã có

| Mã | Nội dung | Nguồn đã có (code / báo cáo) | Khoảng trống thật | Cần chủ dự án chốt? |
|---|---|---|---|---|
| TC01 | Đầu kỳ | `dau_ky.py`, báo cáo `Doi chieu so du dau ky`, `Khach chua co cong no dau ky`, đối ứng 9990 ngày 30/09/2026 | Nghiệm thu với số dư thật (để cuối) | Không |
| TC02 | Mua–nhận–hóa đơn–ứng trước–trả NCC | PR/PI native; NM01a/b (PR #17/#18) nhận theo PO, chờ định giá giữ chỗ; `funds.py` (ứng trước theo kế hoạch, không FIFO) | Chưa có màn đối chiếu "PO → PR → PI → thanh toán" một nhà cung cấp trên một chỗ | Tiêu chí lệch giá PI so PR (dung sai) chưa có trong quyết định |
| TC03 | Chi phí chưa trả / đến muộn / trả trước | Landed Cost Voucher theo kg (`landed_cost_kg.py`), chi phí chuyến (0.10.0); TK 242/335 có trong cây TK (`tai_khoan_chuan.py`) | Không có lịch phân bổ chi phí trả trước tự động | **Có**: có dùng phân bổ 242 tự động hay bút toán tay hàng tháng |
| TC04 | Giá thành / dở dang / repost | `stock_entry_kg` kg-v4, `factory_costing` (phân bổ xưởng cuối tháng, quyết toán dở dang), NM02–04 cửa sổ ghi lượng (lượt này) | Báo cáo giá thành tháng theo mặt hàng là màn kế toán, chưa có | Không (quy tắc đã chốt R075–R079) |
| TC05 | Tài sản / CCDC / khấu hao | Chỉ có tài khoản 211/214/242 trong cây TK; quỹ nhà máy ghi mua CCDC | Chưa cấu hình Asset Category / khấu hao | **Có**: phương pháp, thời gian khấu hao, ngưỡng tài sản vs CCDC, phân bổ CCDC bao nhiêu kỳ |
| TC06 | Vay / lãi / vốn | `tien_vay.py`, báo cáo `Du no vay theo khe uoc`, ô khế ước trên dòng bút toán | Đủ cho vận hành; nghiệm thu với khế ước thật để cuối | Không |
| TC07 | Thu hộ / nội bộ | `thu_ho.py`, `funds.py` route bank/holding/due-from có duyệt, báo cáo `Tien thu ho chua xu ly` | Mua bán/chuyển hàng **khác đơn vị** chưa có quy tắc giá/hóa đơn nội bộ (xem NM01c) | **Có**: giá chuyển nội bộ, có lập hóa đơn hay không giữa APH/VH/MK/TL |
| TC08 | Báo cáo điều hành / tạm tính / chất lượng dữ liệu | `Lai gop quan tri`, `Dong tien 7 30 ngay`, `Du lieu can ra soat`, `Chot ngay va can xu ly`, `Ton kho theo tai khoan va dia diem` | Chưa có một bảng chỉ tiêu tháng cho ban giám đốc | **Có**: danh sách chỉ tiêu, kỳ, ai xem |

Kết luận: phần nền đã đủ để vận hành và nghiệm thu với dữ liệu thật; việc lập trình tiếp ở đợt 4 nên **chờ 4 quyết định**
(TC03, TC05, TC07, TC08) và kết quả nghiệm thu dữ liệu thật để biết chênh lệch thật nằm ở đâu, thay vì viết thêm báo cáo đoán.

## Đợt 5 — hóa đơn một phần (HD01): câu hỏi cần chốt trước khi đặc tả

1. Một lần giao có thể xuất **nhiều** hóa đơn (theo đơn vị / có-không VAT) hay đúng một?
2. Khách yêu cầu hóa đơn **theo dòng / theo lượng** khác lượng giao: cho lệch tối đa bao nhiêu, ai duyệt?
3. Hóa đơn gộp nhiều lần giao, nhiều đơn: cho phép không, trong cùng tháng hay khác tháng?
4. Điều chỉnh / thay thế / hủy trên MISA (NĐ 123/2020, NĐ 70/2025): ERP chỉ ghi số tham chiếu (như hiện tại) hay cần trạng
   thái hàng đợi riêng cho từng loại?
5. Hàng đã giao nhưng khách chưa lấy hóa đơn quá thời hạn xuất hóa đơn theo luật: cảnh báo sau bao nhiêu ngày, ai xử lý?

Câu 4–5 có yếu tố pháp lý: ghi thêm vào `docs/bang-ra-soat-phap-ly-APH-VH.md` khi chủ dự án/kế toán xác nhận.
