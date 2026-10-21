<!-- Nguồn: gói bàn giao Codex APHVH_CLAUDE 13/10/2026 (BUSINESS_DECISIONS.md), chép nguyên văn. -->
# Quyết định nghiệp vụ hiện có — không thay cho nguyên văn 202 câu

1. APH/VH/MK/TL là 4 Company; TL=XB (hàng không hóa đơn), không tạo Company thứ năm. MISA chỉ hóa đơn thuế. Chỉ frontend là production mới; không dùng baseline erpnext.local.
2. Nhân viên lập một đơn chung, dòng chọn Item/kho nguồn. Hậu trường chứng từ và sổ tách theo Company sở hữu kho. Giao nhiều lần, lưu đặt/đã giao/còn lại.
3. Ba trạng thái Chờ xuất → Đang giao → Khách đã nhận. Shipper nhận: xuất tồn và phát sinh nợ khi Đang giao. Khách tự lấy: tới Khách đã nhận xuất ngay. Nhận hàng sau đó không ghi sổ lần hai. Lưu actor/time; không bắt buộc attachment. Kho xác nhận phần mình, thiếu có thể đổi nguồn phần chưa giao.
4. Hiển thị tổng còn thanh toán toàn đơn, công nợ phần đã giao, giá trị chưa giao. Thu tiền vào đúng quỹ/bank thực nhận; APH thường nhận APH+TL, VH/MK nhận phần mình. Không tự tráo bank hoặc cấn nợ company khác ngoài kế hoạch được duyệt.
5. Tiền chưa rõ khách/đơn vẫn ghi thực nhận và chưa phân bổ; xác minh và phân bổ từng phần sau. Không FIFO, không tự cấn hóa đơn cũ. Đối soát chống trùng; yêu cầu sao kê Excel/CSV, hiện code mới kiểm dữ liệu chuẩn hóa, chưa parser mọi ngân hàng.
6. Cọc chung hoặc chỉ định nguồn; giữ/chuyển/giải phóng/cấn hóa đơn/hoàn tiền theo thỏa thuận. APH nhận TL cần route bank/holding/due-from được chief duyệt; bank TL chỉ phát sinh khi chuyển thật, không giả tiền nhận.
7. Hạn mức chung khách qua 4company; cảnh báo lúc lập, kiểm lúc giao; tiền chưa phân bổ đã xác minh trừ ròng đúng một lần. Khách rủi ro cao cần phê duyệt; đổi lượng/thu hồi/đổi nội dung làm phê duyệt hết hiệu lực. Chưa ký xác nhận nợ chỉ cảnh báo bình thường. Đối chiếu nợ tháng/bất kỳ lúc nào, lưu bằng chứng; chưa nghiệm thu đủ toàn bộ quy trình xác nhận từ xa.
8. Giá bán gợi ý bảng giá, nhân viên sửa; thấp ngưỡng cảnh báo/duyệt. Giá vốn Moving Average theo Item/Warehouse. Dũng tuyệt đối không xem giá vốn kể cả cộng role. Tài khoản giả lập đã test, chưa xác nhận role tài khoản thật.
9. Stock/giá vốn theo kg, theo dõi số bao thực tế nguyên và snapshot kg/bao trên chứng từ; không suy số bao lịch sử từ quy cách hiện tại. Giá/kg × kg/bao thành giá/bao. Giao/trả/hủy bảo toàn cả kg/bao.
10. Nhập chưa biết giá: chờ định giá ngoài tồn khả dụng/GL/SLE; không giá0. Chốt đúng giá mới tạo nhập có giá. Chi phí chuyến theo trọng lượng kg; có thể vào MA hoặc expense riêng, phát sinh sau phải repost thực.
11. Hao hụt phát hiện ghi ngay +kiểm kê định kỳ, lý do/kho/actor/time. Tự nhiên giữ chi phí trong tồn còn lại; bất thường expense riêng đúng company.
12. Sản xuất/Repack/BOM/WorkOrder/phụ phẩm đã có UAT kg và định giá, phụ phẩm fixture fixed5000/kg. Không coi fixture này là bảng giá master thực. Chưa chứng minh toàn bộ thuê ngoài/nhà cung cấp/hoá đơn thực.
13. Phiếu giao riêng/tổng hợp đúng từng DN; PDF kiểm CI, chưa máy in thực. Quyền thay đổi trạng thái giữ đúng scope xử lý đơn.

Nếu cần đối chiếu từng câu1–202 phải lấy bản quyết định gốc từ người dùng/nguồn được họ xác nhận; không hỏi lại từng câu và không bịa số thứ tự.


## Bổ sung19/10/2026 — chất lượng hàng nhận nhà máy

Anh Tiến xác nhận khi triển khai đợt3: hàng có vấn đề thường không trả lại mà đàm phán giảm giá; thường vẫn đưa vào dùng ngay, giá điều chỉnh sau. Ghi đủ lượng thực nhận dùng vào kho, tách lượng có vấn đề như phần trong tổng lượng và lưu ghi chú đàm phán; không tự tạo trả hàng/trừ lượng hoặc tự giảm giá. Kế toán mua xử lý giá điều chỉnh theo chứng từ và đối chiếu hiện có. Đây là trường hợp thông thường, không suy mọi chuyến đều cấm trả hàng hoặc không cần kiểm chất lượng.

## Bổ sung21/10/2026 — nhận tại kho và giấy gốc giao nhận

Chủ dự án trực tiếp xác nhận: lái xe do khách chỉ định/xác nhận đến nhận đủ và ký tại kho được tính là khách đã nhận hàng; không mặc nhiên áp cho ship/nhà xe do bên bán bố trí hoặc người chưa được khách xác nhận. Ghi căn cứ chỉ định/người thực nhận, không bắt thêm một lần xác nhận nhận tại nhà khách cho nhánh này.

Giấy gốc có chữ ký được gom và lưu tập trung tại kế toán cửa hàng; kho vệ tinh chuyển giấy về. Ảnh/tệp và giấy gốc là hai mốc khác nhau. Chưa chốt số liên/bố cục mẫu mới hoặc thời hạn chuyển giấy/lưu; không suy quyết định này là duyệt bản nháp3liên. Thiết kế tiếp nối tại `thiet-ke-kho-giao-nhan-tiep-noi-0164.md`, chưa áp schema/quy trình mới vào production.

## Bổ sung21/10/2026 — giấy dự phòng, phiếu thu và ký đối soát nợ

Không bắt khách/xe chờ phần mềm xác nhận xuất thành công khi mất mạng. Cho phép lập giấy tay mới do người phụ trách được giao quyền quyết định, kể cả lượt chưa chuẩn bị/kiểm ERP; ghi nhận hệ thống và đối chiếu sau có mạng, giữ đúng thực giao/thu và giấy gốc. Không suy mọi nhân viên được tự duyệt hoặc được bỏ kiểm sổ khi nhập bù.

Khi thực thu tiền phải lập phiếu thu cho người nộp/khách ký. Khi có tăng hoặc giảm công nợ phải có biên bản đối soát ký và lưu, kể cả phát sinh tăng/giảm bù nhau, dư cuối0. Một bản theo khách trình bày riêng từng đơn vị, cọc và tiền chưa phân bổ; không tự cấn chéo. Lái xe có quyền nhận hàng chỉ ký công nợ khi khách giao thêm quyền ký nợ riêng. Ảnh và giấy gốc tiếp tục xử lý sau, kế toán cửa hàng lưu tập trung. Thiết kế cập nhật tại `bo-sung-kho-mat-mang-thu-tien-doi-soat-20261021.md`, chưa triển khai vào ERP.
