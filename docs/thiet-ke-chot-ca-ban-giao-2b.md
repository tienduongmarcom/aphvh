# Bước2B — Chốt ca và bàn giao tiền dùng chung

Ngày18/10/2026. Thiết kế tiếp nối2A; **lát xác minh/chốt ca đang triển khai, chưa đủ toàn bộ2B**. Không dùng báo cáo phát sinh2A thay cho số tiền hiện còn giữ. Không cần hỏi lại quyết định không tự nhận, không ghi thu khách lần hai, chênh lệch chờ điều tra hoặc nghiệm thu thật gom cuối.

## 1. Mục tiêu/phạm vi

Quản lý trách nhiệm tiền mặt theo company, tài khoản Cash và người giữ; chốt số phải có/thực đếm; giao/nhận có xác nhận riêng và giữ thiếu/thừa. Cùng tài khoản chỉ chuyển trách nhiệm, không ghi GL. Khác tài khoản chuyển tiền đúng một lần bằng chứng từ native. Chuyển giữa company giữ tuyến thu hộ hiện có, không ghép vào bàn giao cùng quỹ. Không mở hóa đơn một phần, không thay MISA hoặc kế toán thuế.

## 2. Hiện trạng

2A có metadata người giữ trên nguồn và bảng rà GL, chưa có số dư trách nhiệm. `factory_cash.xac_nhan_nhan` có khóa phiếu/số thực nhận/JE chuyển tiền nhưng chưa đáp ứng đầy đủ chốt ca chung và cấm tự nhận theo người thực giao. `ban_quay.thu_tien` chưa có token chống lặp cho tiền mặt; phải bổ sung trước coi luồng tiền chung đạt.

Đã đọc ERPNext16.51.1 `general_ledger.make_entry/make_reverse_gl_entries`: GL được tạo bằng Document.submit; hủy thường đánh dấu và tạo dòng đảo is_cancelled; chế độ immutable có thể giữ dòng đảo hoạt động. Không suy dòng GL duy nhất từ một phiếu hoặc bỏ qua chế độ hủy. Hook/khóa cần kiểm trên image thật, không chỉ mock.

## 3. Quy trình và trách nhiệm

1. Kế toán trưởng xác minh phân bổ tiền hiện có theo người tại thời điểm bắt đầu. Phần chưa rõ nằm ở nhóm Chưa xác minh, không gán owner.
2. Các đường thu/chi ghi người thực giữ phía Cash. Nhân viên xem số phải có của chính mình, nhập thực đếm và chốt ca.
3. Người giao tạo đề nghị, chọn người nhận và khoản dự kiến. Khi gửi, nguồn được giữ chỗ, chưa chuyển tiền/trách nhiệm.
4. Đúng người nhận đăng nhập nhập số thực nhận và xác nhận. Server đối chiếu, chuyển trách nhiệm/ghi chuyển tài khoản một lần; có lệch thì lưu vụ cần xử lý ngay trên hồ sơ nguồn.
5. Kế toán trưởng phân công người xử lý/hạn/kết quả cho lệch; việc điều chỉnh sổ phải có chứng từ chuẩn liên kết. Kế toán tổng hợp1 kiểm độc lập, tổng hợp2 nhận tiền/đối chiếu theo phân công đã chốt.

Không ai xác nhận nhận tiền từ chính mình, kể cả Accounts Manager/System Manager/Administrator. Người quản lý có thể xử lý ngoại lệ nhưng không được đóng vai người đã thực nhận bằng nút nhận thay.

## 4. Quy tắc và ngoại lệ

- Số phải có là trách nhiệm tiền đã xác minh, không phải tổng thu theo owner. Ngân hàng không có “người giữ tiền mặt”.
- Đề nghị chưa nhận giữ chỗ nguồn; không giảm số phải có của người giao và không tăng tiền khả dụng của người nhận.
- Xác nhận theo số thực nhận. Nếu dự kiến100/thực nhận95, chuyển95, giữ lệch5 cần điều tra; không tự bù chi phí/nợ hoặc tự kết luận ai làm mất. Nếu thực nhận lớn hơn dự kiến, kiểm đủ nguồn người giao và lưu thừa, không tạo tiền mới.
- Cùng tài khoảnCash: chuyển trách nhiệm có tổng delta bằng0, GL/PLE không đổi. Khác tài khoản: debit quỹ nhận/credit quỹ giao bằng số thực nhận, không có dòng131/doanh thu; native permissions/controller vẫn kiểm.
- Không chuyển nguồn chưa xác minh, không chiếm một số tiền cho hai đề nghị. Không tự cho số âm vì đặt ca/đổi ngày.
- Ca qua ngày dùng mốc thời gian cụ thể, không chỉ posting_date. Lùi ngày/hủy/repost sau chốt phải làm xuất hiện ngoại lệ/đối chiếu lại, không ghi đè số đã chốt.
- Hủy đề nghị chưa nhận giải phóng giữ chỗ. Bàn giao đã nhận không sửa/hủy tay; cần nghiệp vụ đảo có hai phía, kiểm nguồn chưa dùng tiếp và liên kết chứng từ đảo native nếu có. Không hồi phục backup để sửa một bàn giao.
- Thực đếm vượt nguồn khả dụng vẫn phải được lưu để xử lý lệch, nhưng chưa xác nhận chuyển vượt nguồn hoặc tự tạo tiền mới. Quỹ/người có thiếu/thừa chưa xử lý không tiếp tục giao ra bằng phần tiền đang tranh lệch; luồng nhận thêm và đối chiếu vẫn giữ được. Không cộng cùng một khoản thiếu vào nhiều lần giữ chỗ qua các ca.
- Bằng chứng/ghi chú thay đổi giữ lịch sử; không xóa bản cũ khi đã nhận. Không tạo DocType Nhiệm vụ riêng để lưu trạng thái trùng.

## 5. Dữ liệu và công thức

Các hồ sơ sau có lifecycle riêng, nên dùng DocType thay vì thêm trạng thái lên Payment Entry:

| Hồ sơ đề xuất | Field chính/nguồn | Trạng thái |
|---|---|---|
| Xác minh tiền bắt đầu (parent+child phân bổ) | company, accountCash, cutoff_time, GL fingerprint/GL balance, từng holder/amount, phần chưa xác minh, căn cứ, actor/time/lý do | Nháp → Đã xác minh; bản sau thay mốc trước có lịch sử, không xóa bản trước |
| Chốt ca tiền mặt | company/account/holder, start/end time, expected/count/difference, mốc nguồn, người chốt/time, căn cứ, người xử lý/hạn/kết quả | Đang nhập → Đã chốt / Có lệch; mở lại có lý do/lịch sử và quyền quản lý |
| Bàn giao tiền | company/from_account/to_account/from_holder/to_holder, expected/received/difference, request_key/hash, source reservation, actor/time hai phía, native_transfer, bằng chứng và vòng xử lý lệch | Nháp → Chờ nhận → Đã nhận hoặc Có lệch; hủy trước nhận/đảo sau nhận là thao tác có kiểm soát |

Tên field/doctype và quyền chính xác phải chốt trong blueprint triển khai, giữ ASCII/nhãn Việt và no_copy cho mốc server. Các số tiền hữu hạn, tối đa2 số lẻ; số nguồn là Currency VND. Ngày giờ theo múi giờ site; lưu datetime server và actor đã xác thực.

Với một quỹ đã xác minh tại mốcT:

`phải_có(holder) = phân_bổ_tại_T + GL_Cash_sau_T_đúng_người + nhận_trách_nhiệm_cùng_quỹ - giao_trách_nhiệm_cùng_quỹ`

`khả_dụng = phải_có - giữ_chỗ_đề_nghị_chờ_nhận`

Chuyển khác tài khoản đã nằm trong GL, không cộng delta trách nhiệm lần nữa. Tổng các người + phần chưa xác minh phải khớp số dư GL quỹ. Không dùng ngày ghi sổ thay mốc tạo/đảo một cách tùy tiện: hủy/repost có thể thay tập GL trước mốcT. Khi fingerprint/tổng không khớp, chặn bàn giao mới và mở ngoại lệ xác minh lại; không tự phân bổ phần lệch theo tỷ lệ.

Chốt ca lưu snapshot bất biến của expected/count/difference và mốc nguồn. Ca sau không coi số thực đếm thành GL mới. Đầu kỳ người giữ không làm thay số dư tài khoản đã nhập. Xác minh lại phải có căn cứ và giữ bản trước; không biến một lần xác minh thành cách xóa lệch không dấu vết.

## 6. Quyền và chống đồng thời

- Native DocPerm + Company/Account scope kiểm cả hai bên; người giữ/phụ trách là User nội bộ hoạt động. Người không đọc được nguồn không được dùng nguồn.
- Người giao gửi đề nghị bằng tài khoản chính mình; cho phép kế toán chuẩn bị nháp, không giả actor xác nhận. Chỉ người nhận đích xác nhận; cấm from_holder=to_holder trên server ở mọi đường API và cộng role.
- Người nhận tạo/submit JE chuyển tài khoản phải có quyền native phù hợp. Không cấp bypass bằng ignore_permissions cho mọi người giữ; phạm vi nhà máy dùng adapter hẹp đã được kiểm riêng.
- Khóa quỹ/nguồn theo thứ tự ổn định trong cùng transaction; các đường ghi/hủy/repost GL liên quan phải tương thích khóa này. Khóa riêng đề nghị không đủ chống hai đề nghị chiếm chung tiền.
- Key/hash duy nhất cho thao tác gửi/nhận/đảo; retry cùng nội dung trả kết quả cũ, đổi nội dung cùng key bị chặn. Không commit giữa chuyển trách nhiệm và JE; lỗi một phía rollback toàn bộ.
- Đường thu tiền mặt cũ và Dialog phải có token idempotency hoặc định danh nguồn chuẩn; không chỉ chống trùng mã ngân hàng. Kiểm cả phản hồi bị mất sau commit và hai phiên đồng thời.
- Khi bật2B, lối nhận quỹ nhà máy cũ phải đi qua adapter cùng guard cấm tự nhận/chống trùng; không để manager bypass hoặc hai lối ghi hai JE cho cùng bàn giao. Nguồn cũ chưa rõ người giao cần xác minh có căn cứ, không suy owner và không sửa metadata đã submit của2A.
- Báo cáo quản lý đọc số trong scope; Dũng vẫn không xem giá vốn kể cả cộng role. Tách báo cáo tiền cá nhân tối thiểu khỏi toàn bộ GL/nguồn có giá vốn.

## 7. Tác động hệ thống

Chốt ca/kiểm đếm/cùng-quỹ không ghi GL/PLE, không giảm nợ. Thu khách/hoàn khách vẫn theo PE/JE/Funds chuẩn và kế hoạch phân bổ đã duyệt. Chuyển khác tài khoản chỉ tác động tiền của cùng company. Kho/giá vốn/sản xuất/MISA không thay. Báo cáo chốt ngày tổng hợp từ hồ sơ nguồn và sổ chuẩn, không giữ bộ công nợ mới.

## 8. Bộ nghiệm thu bắt buộc trước bật2B

| Ca | Kết quả bắt buộc |
|---|---|
| Xác minh bắt đầu có người rõ/chưa rõ | Tổng phân bổ + chưa rõ = GL; không tự đoán owner hoặc sửa sổ |
| Thu cũ/PE/JE/thu ngay/Funds/nhà máy/POS tổng hợp | Đúng một tác động tiền; người chưa rõ được thể hiện và không dùng làm nguồn xác minh giả |
| Chốt ca đủ/thiếu/thừa/qua ngày | Snapshot đúng, lưu lệch/người xử lý/hạn, không tự bù GL |
| Giao cùng quỹ/khác quỹ/nộp bank | Cùng quỹ GL không đổi; khác quỹ chỉ một chuyển tiền; nợ/doanh thu không đổi |
| Nhận95/100; nhận thừa | Chuyển đúng số thực nhận trong nguồn có thật, lưu lệch riêng |
| Tự nhận + cộng role/quản lý/API trực tiếp | Server từ chối |
| Hai đề nghị/hai phiên nhận/mất phản hồi sau commit | Nguồn không bị dùng hai lần, retry trả đúng kết quả cũ |
| Hủy/repost/lùi ngày sau chốt; nguồn GL đổi trước mốcT | Không âm thầm thay số chốt; phát hiện sai tổng và chặn nguồn cần xác minh lại |
| Đảo bàn giao đã dùng tiếp/đổi bằng chứng | Chặn hoặc theo đảo đủ liên kết/quyền, giữ lịch sử |
| User Permission Company/Account, Dũng cộng quyền | Không đọc/ghi vượt phạm vi/không lộ vốn |
| Cài lại/nâng bản sao có số dư/quay lui | Không backfill owner, tổng người/quỹ/sổ khớp và lịch sử nguyên vẹn |

Các ca của lát xác minh/chốt ca đã chạy, xem mục11. Bàn giao/giữ chỗ/đảo/adapter nhà máy chưa chạy cho2B; không dùng kết quả2A hoặc lát đầu thay toàn bộ bộ ca này.

## 9. Triển khai

Tách code2B sau khi nền2A được kiểm, thêm cờ/schema rõ ràng, mặc định tắt. Bật trên UAT giả trước; migration chỉ thêm cấu trúc, không tự gán tiền lịch sử. Trước vận hành thật cần người có trách nhiệm xác minh số tiền bắt đầu, phân quyền nhân sự và thử luồng đại diện; nghiệm thu thực tế gom cuối theo chủ dự án. Diễn tập/quay lui dùng runbook snapshot/image/cờ; không restore sau mở giao dịch mà không đối soát.

Bước triển khai đầu: hoàn thiện blueprint field/DocPerm, thuật toán khóa và fingerprint/ca hủy-repost, rồi làm xác minh tiền bắt đầu + đối chiếu read-only. Chỉ nối bàn giao khi công thức tổng người–quỹ–GL đã kiểm bằng dữ liệu giả có giao dịch. Không coi thiết kế này là module đã chạy.

## 10. Blueprint lát xác minh và chốt ca (18/10/2026)

Cờ23 `kh_aph_cash_closing` cần cờ22; mặc định tắt. Ba DocType native có controller, schema rõ ràng, không hook tự cài. Workspace Tiền và vay có Xác minh quỹ / Chốt ca tiền / Ca tiền chênh lệch.

| Hồ sơ | Field cụ thể | Quyền và vòng đời |
|---|---|---|
| APH Xac minh quy | company, account, reason bắt buộc; evidence; allocations(holder, amount); unverified_amount; gl_balance; previous_verification; source_hash/source_rows; closed_by/closed_at | Accounts Manager/System Manager có tạo/sửa nháp/submit, không cancel/sửa đã submit. Xác minh sau liên kết bản trước và bắt buộc lý do. |
| APH Phan bo quy | holder User nội bộ đang hoạt động đúng phạm vi, amount không âm, không trùng holder | Child của xác minh, không CRUD độc lập. |
| APH Chot ca tien | company/account/holder; verification/previous_shift/started_at; expected_amount/counted_amount/difference/status; reason/assignee/due_date/evidence; dấu sổ/actor/time | Accounts User xem/chốt chính mình; quản lý xem trong scope nhưng không chốt thay. Ca lệch phải có lý do, người xử lý, hạn. Không cancel/sửa/mở lại trong lát này. |

Vai trò Không xem giá vốn/Kế toán nhà máy bị chặn cả cộng manager; chưa cấp GL qua module này. Quyền native Company, Account, GL và từng nguồn vẫn bắt buộc. API current chỉ trả mốc, tiền của chính người đăng nhập và thời gian kiểm; không trả các người khác/GL. Chứng cứ JSON chỉ chứa mã GL và băm, không chứa tiền hoặc người của nguồn. Account User không được đọc phân bổ của bản xác minh.

Khóa tất cả Cash account của company theo tên trong transaction, tương thích hook before_submit/before_cancel các nguồn chuẩn và before_insert GL (kể cả dòng đảo). GL và nguồn đọc for_update của Frappe16.52.0, tránh snapshot cũ sau đợi khóa. Không commit trong service. Giới hạn10.000 dòng/quỹ được báo lỗi rõ thay vì cắt dữ liệu. Nguồn ngoài adapter để nhóm chưa rõ, không suy owner.

Tại mốc xác minh lưu dấu từng GL gồm ID/ngày/creation/tiền/cờ hủy/nguồn/người giữ; API chỉ lưu băm của nội dung này. Lần sau tập GL cũ phải giữ nguyên, dòng mới hoạt động cộng theo người trên nguồn. Tổng phân bổ + chưa rõ luôn so số dư Cash hiện có. Hủy/repost/sửa dòng cũ kể cả tổng bằng nhau làm mốc hết hiệu lực, bắt xác minh mới có lý do; không sửa bản chốt. Sổ mới có posting_date trước ngày của ca gần nhất cũng chặn chốt mới. **Trong cùng ngày**, native GL chỉ có ngày ghi sổ: dòng tạo sau chốt được tính ở ca sau bằng định danh mới; không suy giờ nghiệp vụ không có trên GL. Ca qua ngày dùng started_at/closed_at server, không chia nhóm theo posting_date.

Nháp giữ fingerprint; nếu sổ hoặc bản trước đổi trước submit, từ chối và yêu cầu lưu/đối chiếu lại. close(name) khóa hồ sơ, retry cùng tên trả kết quả cũ. Hai nháp cùng khoảng thời gian không chốt đồng thời vì so previous_shift dưới khóa. Thực đếm không trở thành GL/đầu ca mới; chênh lệch lưu trên hồ sơ, chưa có nút xác nhận xử lý/mở lại. API native submit cũng chạy cùng guard.

Kiểm: 10 ca unit mới cho Decimal/fingerprint/tổng/quyền/cờ tắt; HTTP quỹ giả1000 phân700/200/chưa rõ100, thu100 rõ +50 chưa rõ, ca thiếu20/thừa10, hai phiên retry, nháp lỗi thời, hủy sau chốt, xác minh thay mốc, ghi lùi ngày, không chốt thay và không lộ ca khác; Chrome đọc snapshot đã chốt. Đã có kết quả tích hợp trên022322c; xem mục11 và ban-giao/TRANG_THAI.

Triển khai chỉ cấu trúc, không phân bổ lịch sử hoặc sửa sổ; khi bật thật kế toán trưởng xác minh quỹ có căn cứ. Cổng3 thêm cả custody/closing vào FLAGS_MOI, rollback trả hai cờ0 theo snapshot. Nhóm bàn giao/giữ chỗ/đảo/adapter nhà máy/idempotency thu cũ và bảng tổng hợp vẫn là bước sau; không được bật như module bàn giao hoàn chỉnh. Nghiệm thu người dùng/thực địa theo quyết định gom cuối.

## 11. Bằng chứng lát đầu

PR #11, mã022322cab2eea0dade0848fa133bbb6c19199273:327+108 unit đạt,242 HTTP/Desk PASS/0 FAIL (b01451), thêm2 kiểm kỹ thuật core/site trắng PASS. Đã đọc artifact UAT39138168695 và xem ảnh chot-ca-tien.png: snapshot800/800/0 khóa, form sạch. Bằng chứng tệp kiểm đếm gồm chặn tệp công khai, chặn xóa/đổi riêng tư sau xác nhận và tải lại blob còn nguyên. Kế toán Accounts User chốt được chính mình, không đọc bản phân bổ/ca khác; NoCost cộng manager bị chặn.

Bốn cổng: C2 39138158466, C2b39138169799, UAT39138168695, C3 39138171169 đều success đúng mã. C3 schema1.059/1.059 (bỏ qua6 mục có chủ đích), rollback1.052/1.052 và tổng/đếm/cờ/settings/UI/versions khớp; hai cờ mới về0. Cố ý gây lỗi tự quay lui và giữ bảo trì. Core63.508 tệp không đổi. Không có FAIL trên mã cuối; các lượt trước hủy khi cập nhật mã không dùng làm bằng chứng.

Đây là dữ liệu giả và nền CI GL0 cho migration, không phải nghiệm thu nhân sự hoặc bản sao production có phát sinh. Chưa phát hành/bật cờ trên production, vẫn0.15.3. Các phần bàn giao/giữ chỗ/đảo, xử lý kết quả lệch và adapter người bán/nhà máy tiếp tục theo mục8–10.
