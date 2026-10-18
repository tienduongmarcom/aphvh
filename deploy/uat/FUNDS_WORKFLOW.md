# Tiền thực nhận, cọc và kế hoạch phân bổ

Ứng viên UAT, **chưa nghiệm thu** cho tới khi workflow cùng SHA xanh. Feature flag `kh_aph_funds_workflow`; không có install/migrate hook tự bật hoặc tự tạo tài khoản kế toán.

## Ghi tiền trước

Accounts Manager duyệt `APH Funds Route`: đơn vị nhận, tài khoản Liabilities giữ tiền, chủ hàng tùy chọn và tài khoản Asset phải thu đơn vị nhận trên sổ chủ hàng. Đây là lựa chọn tài khoản được duyệt, không tự suy từ số hiệu hoặc tự tạo chart.

`APH Funds Receipt` ghi đúng bank/quỹ thực nhận bằng JE Nợ tiền/Có giữ tiền. Khách có thể chưa xác định. Mã giao dịch ổn định chống ghi trùng. Ghi tiền không tự giảm hóa đơn cũ. Xác minh khách có actor/time/comment; tiền đã xác minh chưa dùng được tính ròng vào hạn mức chung một lần.

## Thao tác riêng, không FIFO

| Thao tác | Kết quả |
|---|---|
| Reserve | Giữ cọc cho đơn và nguồn cụ thể, hoặc cọc chung; không ghi thêm ngân hàng/khách nợ |
| Allocate | Chỉ cấn hóa đơn ERP được chọn của đúng khách; có thể dùng một phần cọc |
| Transfer | Chuyển phần cọc còn lại sang đơn/nguồn chỉ định; giữ lịch sử cọc cũ |
| Release | Trả cọc về tiền chưa phân bổ; không tự vào nợ cũ |
| Refund | Ghi thực chi đúng quỹ/bank được chọn, có mã giao dịch; không hoàn quá tiền còn lại |
| Settle | Khi thật sự trả thu hộ cho chủ hàng: chọn rõ hai quỹ/bank, hai tham chiếu; ghi hai sổ của một chuyển tiền thực, không cấn khách thêm lần nữa |

Accounts User lập kế hoạch; Accounts Manager duyệt. Chứng từ đã duyệt bất biến, hủy theo thứ tự phụ thuộc; JE liên kết không được sửa/hủy riêng. Khóa receipt/invoice bảo vệ thao tác đồng thời. Cọc giữ một nguồn không cấn nguồn/đơn khác trước khi có chuyển/giải phóng.

APH nhận tiền TL: thực thu APH ghi ngân hàng/liability APH. Phân bổ đã duyệt ghi Nợ phải thu APH trên sổ TL/Có nợ khách TL; ngân hàng không được ghi lại. Liability APH vẫn phản ánh tiền thực giữ của TL. Chỉ lúc thực trả chủ hàng mới ghi giảm liability/bank APH và tăng tiền/giảm phải thu trên sổ TL. Không tự chuyển ngân hàng hoặc coi bút toán liên company là giao dịch ngân hàng mới.

MISA chỉ hóa đơn thuế. Các JE/Invoice ở đây là sổ vận hành ERP.

## Ba số trên đơn chung

`shared_financials` đối chiếu hóa đơn đã ghi sổ, nợ còn lại và cọc giữ riêng: còn thanh toán toàn đơn, công nợ đã giao, giá trị chưa giao. Tiền chưa gán đơn không tự giảm số còn thanh toán của đơn. Không tính cọc cùng lúc trong đã thanh toán và đang giữ. Form Desk hiển thị cả cọc giữ lại.

## Sao kê và kiểm thử

`reconcile_rows` đối chiếu mã giao dịch/ngày/tiền thực nhận; chỉ trả Khớp/Chưa ghi thực thu/Cần đối soát. Nó không ghi ngân hàng hoặc tự phân bổ. Dòng chưa rõ có thể ghi phiếu thực thu rồi xác minh sau. CSV cần chuẩn hóa các cột `external_reference`, `posting_date`, `amount` trước khi gửi đối chiếu.

HTTP UAT: unknown payer, chống trùng, xác minh bằng Chrome, không cấn nợ cũ, cọc chung/nguồn, APH thu TL theo tuyến, cấn một phần, trả chủ hàng thực, chuyển/giải phóng/hoàn, ba số, quyền, concurrent overspend, hủy đảo và restore. Fixture accounts chỉ trong CI; không dùng tên/quyền/kho tài khoản fixture cho frontend.

Các gate production gồm mapping thật, dữ liệu/master, migration/rollback và quyền VM. Tài liệu này không xác nhận đầy đủ 202 quyết định.
