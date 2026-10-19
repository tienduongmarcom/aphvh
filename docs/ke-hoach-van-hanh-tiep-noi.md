# Kế hoạch tiếp nối — Vận hành nhanh và kiểm soát tiền–hàng–công nợ

## Nguồn và phạm vi

Anh Tiến cung cấp lại lịch sử chat “Lỗi kết nối app Work” và ba đề xuất về bán hàng/bàn giao, nhà máy, tổng thể; sau đối chiếu đã yêu cầu tiếp tục và chấp thuận kế hoạch ngày 17/10/2026. Tài liệu này giữ mạch công việc để agent khác không cần hỏi lại. Không dùng yêu cầu NocoBase hoặc hệ thống 8082 làm baseline. Không xác nhận toàn bộ 202 quyết định; nguồn gốc đầy đủ 202 câu chưa có trong các tệp vừa nhận.

Baseline đã triển khai: kh_aph 0.15.3, nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`, ERPNext 16.51.1/Frappe 16.52.0/lab9x 0.2.11. Digest image `sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`. [Workflow phát hành39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) đạt đủ bốn cổng; 302+108 ca cục bộ, UAT227 PASS/0 FAIL. Người vận hành đã gửi log `=== XONG 0.15.3: ĐẠT ===` với digest khớp. Đây là bằng chứng mã/phát hành/triển khai, không thay nghiệm thu nhân sự, dữ liệu hoặc máy in thật.

Giữ 4 Company APH/VH/MK/TL, TL=XB; MISA chỉ hóa đơn thuế; native ERPNext sở hữu chứng từ/sổ. Không làm lại cọc, thu hộ, giá vốn, sản xuất đã có. Mục tiêu mới là giảm thao tác, truy người thực giao và người thực giữ tiền, liên kết các nghiệp vụ có sẵn. Nhân viên kho/vận hành có thể ký giấy mà không có tài khoản phần mềm.

Quy tắc bắt buộc đọc từ `AGENTS.md`, `docs/quyet-dinh-nghiep-vu.md`, `docs/kien-truc-giao-dien.md`, quy trình khách và release. Không sửa core, tạo sổ trùng, DocType Nhiệm vụ có trạng thái riêng hoặc dùng UI ẩn giá thay kiểm quyền server. Workspace điều hướng, Dialog cho thao tác ngắn; Native Page chỉ khi đủ 6 tiêu chí đã chốt. Phần mở rộng giao nhận dùng cờ Trung tâm Bán hàng hiện có; cần đánh giá riêng cờ cho tính năng mới khác theo AGENTS, không tự coi 21 cờ hiện tại bao phủ mọi phạm vi tương lai.

## Thứ tự và trạng thái thật

**Chốt với chủ dự án ngày18/10/2026:** nghiệm thu thực tế với người dùng, hàng hóa/tồn kho/số dư thật và máy in được gom ở cuối khi dữ liệu đủ. Từng phần vẫn phải kiểm kỹ thuật/UAT bằng dữ liệu giả, giữ quyền/chống trùng/so sổ và kiểm nâng/quay lui. Ghi riêng “đã kiểm UAT, chờ nghiệm thu thực tế”; không chặn phát triển đợt2–4 vì dữ liệu thật chưa sẵn sàng. Đợt5 vẫn phải chốt nghiệp vụ riêng trước code.

| Đợt | Kết quả cần có | Mốc 0.15.3 | Điều kiện đóng đợt |
|---|---|---|---|
| 1 — Bán hàng/giao nhận | Phiếu nhanh, người giao/nhận, thực giao và hồ sơ ký/chênh lệch | Production0.15.3 đã có luồng chính; PR #9 đã bổ sung lối in lại A5, đủ bốn cổng trên1e89ace; chưa phát hành | Kỹ thuật/UAT A5 đạt; chuyển đặc tả đợt2, nghiệm thu người dùng/máy in gom cuối |
| 2 — Tiền | Người giữ, chốt ca, bàn giao và ngoại lệ | Có thu/cọc/thu hộ/quỹ nhà máy; PR #10 có metadata người giữ và báo cáo rà nguồn2A, đủ bốn cổng trên929d16a,236 UAT PASS; PR #11 đã kiểm xác minh/chốt ca; PR #12 đã viết giữ chỗ và xác nhận thực nhận, đủ bốn cổng đúng1787448,249 HTTP/Desk PASS/0 FAIL; PR #13 đã kiểm đối chiếu có căn cứ/hoàn ngược chiều,4 cổng đạt trên8fc93b7,259 HTTP/Desk PASS; PR #14 đã kiểm token thu quầy/guard quỹ cũ và bảo trì,4 cổng đúngc02,263 HTTP/Desk PASS; PR #15 đã kiểm xem tiền cá nhân; PR #16 nối nguồn nhà máy/chốt tự thân/bảng ngày, đủ4 cổng đúngd0c1f16,394+108 unit và280 HTTP/Desk PASS/0FAIL | Phần kỹ thuật lát2B đạt; nghiệm thu nhân sự và số dư thật gom cuối, chưa phát hành. Chuyển rà nguồn/đặc tả đợt3 |
| 3 — Nhà máy | Nhập lượng một lần, nối chứng từ | Có nghiệp vụ nền; chưa có màn hình nhập ngắn thống nhất; sheet của Dũng là bước đệm theo chủ dự án | Nhận/sản xuất/đóng gói/xuất hoạt động theo quyền, không lộ giá vốn |
| 4 — Tài chính | Đối chiếu đầy đủ, chốt tháng/báo cáo điều hành | Có nhiều công cụ riêng; chưa chứng minh toàn chuỗi | Đối chiếu dữ liệu đại diện và xác định tạm tính/hoàn tất |
| 5 — Hóa đơn một phần | Yêu cầu theo dòng/lượng/lần giao, hàng đợi MISA | Chưa chốt đặc tả riêng | Chốt nghiệp vụ trước code, không gộp vào bản vá giao nhận |

Thứ tự trên không cấm khảo sát điểm nối tiền trong đợt 1; không mở code chốt ca/nhà máy khi thiết kế phần nguồn chưa rõ. Không chờ danh mục/tồn kho thật mới phát triển; dùng site UAT và dữ liệu giả. Nghiệm thu người thật/máy in/số dư thật là bước riêng.

## Đợt 1 — bảng truy nguyên yêu cầu, code và việc còn thiếu

| Mã | Yêu cầu | Hiện có/bằng chứng code | Việc còn lại và ca kiểm bắt buộc |
|---|---|---|---|
| GN01 | Một cửa sổ lập phiếu & in | `ban_nhanh.preview/create_drafts/print_batch`, JS DocType đơn chung | Bảo toàn token khi lỗi; thêm dữ liệu giao nhận vào nội dung chống trùng, không cho cùng token thay địa chỉ/người nhận |
| GN02 | Đặt/đã xuất/nháp/còn lập, nhiều kho/company | `dispatch_plan.py`, `ban_nhanh._rows`, UAT b014 và scope | Giữ ca giao từng phần, không vượt lượng, nháp sửa/hủy được tính lại; lỗi nhóm sau không để phiếu dở |
| GN03 | Người nhận/lái xe, điện thoại, biển số, địa chỉ, cách giao theo từng đợt | Đã có trong Dialog, server allowlist/quyền địa chỉ và nội dung chống trùng; triển khai0.15.3 | Giữ hồi quy Customer/Address/kiểu dữ liệu/scope; nghiệm thu cách nhân viên nhập thực tế |
| GN04 | Người xuất thực tế khác người nhập | Đã có `kh_aph_nguoi_thuc_giao`, tách người ký thực giao khỏi actor/time server | Giữ quyền kho và khóa sau xuất; nghiệm thu tên thực giao với nhân viên đại diện |
| GN05 | Dự kiến, thực giao tại kho, thực nhận của khách | DN nháp/submit là nguồn lượng; có biên bản thực nhận trong luồng điều chỉnh | Không tạo sổ lượng thứ hai; xác định rõ mốc thay qty nháp và mốc dùng chứng từ điều chỉnh sau xuất; không nhầm nhận thiếu với lỗi nhập |
| GN06 | In2 liên, tên người lập, người giao/nhận, bản sao không xuất lại | A5 nhanh đã có2 liên, giá bán thuần và dấu nháp/bản sao. Mẫu chuẩn dùng `kh_aph_giao_nhan`; in lại chuẩn dùng mẫu đó; `delivery_slip.render` có metadata/khối ký riêng từng DN | Dữ liệu các đường in đã đồng bộ trong0.15.3. PR #9 đã có nút mở lại A5; HTTP/Chrome kiểm quyền/không tăng sổ đạt trên1e89ace. Còn phát hành và nghiệm thu giấy A5/người dùng |
| GN07 | In không xuất kho/nợ; xác nhận thực giao mới ghi sổ | `delivery_status.confirm`, `delivery_receivable`, caHTTP b014 | Mọi đường mới đi cùng service; lặp handoff/pickup không ghiGL/SLE/SI lần hai; không cho người thiếu submit quyền xuất ngay |
| GN08 | Hồ sơ ký và dấu đối chiếu | `ho_so_giao_nhan.py`, `ban_014.js`, ca b014 hồ sơ | Giữ tệp riêng đúng phiếu, chặn xóa blob, thay tệp/ghi chú mất dấu, timestamp cũ bị chặn |
| GN09 | Chênh lệch cần xử lý có người phụ trách/kết quả | Đã triển khai0.15.3: `delivery_issue.py`, Dialog, Workspace và ca b014 chênh lệch | Giữ hồi quy báo/giao/chốt/mở lại, căn cứ và hủy native; nghiệm thu người phụ trách thực tế, theo giới hạn trong `dac-ta-chenh-lech-giao-nhan.md` |
| GN10 | Khách tự lấy/xuất ngay có quyền | PR #5 có `create_and_dispatch` và lựa chọn trong Dialog, dùng controller native | Đã kiểm hai cách giao, rollback nhóm sau, scope/submit, retry/đồng thời trên mã bdb91a8; mặc định in vẫn nháp, không thêm sổ |
| GN11 | Mất mạng/thao tác lặp/đồng thời | Khóa đơn/SO, signature/token và ca Chrome chặn phản hồi200 sau commit | Đã kiểm DN đã submit rồi retry cùng Dialog không tăng sổ; vẫn cần số đo tải/kiểm môi trường vận hành thật |
| GN12 | Scope công ty/kho trên preview, tạo, thử lại, in | `ban_nhanh._note_scope`, ca b014Company/Warehouse | Giữ đối chứng dương và từ chối ngoài phạm vi; đổi quyền sau tạo vẫn không đọc/in được phiếu cũ ngoài quyền |

### Thiết kế cần giữ khi bổ sung thông tin giao nhận

- Thông tin dự kiến đi theo đợt giao; nguồn dữ liệu là Customer/Address/đơn và thông tin người vận chuyển. Không sửa danh mục địa chỉ của khách từ Dialog giao hàng.
- Kiểm meta chuẩn của nền16.51.1 trước quyết định dùng lại các trường Delivery Note. Chỉ thêm Custom Field thật sự thiếu; tênASCII và nhãn Việt. Cài schema qua bộ cài rõ ràng, không after_migrate.
- Chỉ nhận allowlist thông tin giao; kiểm độ dài/kiểu/cách giao. Địa chỉ phải đúng khách, có quyền đọc; server kiểm lại khi lưu, không chỉ dùng bộ lọcLink ở UI.
- Người nhận/lái xe và người giao thực tế có thể không dùng ERPNext. Actor xác nhận trên phần mềm vẫn phải là tài khoản có quyền, không dùng tên tự nhập để giả actor.
- Phiếu nháp được sửa trong quyền native, trước xác nhận kho kiểm lại lượng/thông tin. Phiếu đã xuất không được ghi đè lượng/địa chỉ làm mất lịch sử; đi đúng luồng sửa có kiểm soát đã có hoặc chứng từ điều chỉnh.
- Mỗi phiếu in phải chỉ rõ lượng dự kiến khi chờ xuất và số đã ghi nhận khi đã xuất. Các chữ ký không làm phát sinh quyền phần mềm.
- Tệp mới/ghi chú mới phải làm mất xác nhận cũ. Trạng thái hồ sơ và trạng thái giao hàng là hai khái niệm khác nhau, không tự chuyển Khách đã nhận chỉ vì tải ảnh.
- Chênh lệch được lưu và phân loại trước; xử lý kho/nợ bằng chứng từ chuẩn thích hợp. Người chỉ đọc không được mở/đóng vụ, người không có quyền công ty đích không được liên kết chứng từ của công ty đó.

### Bộ ca đóng đợt 1

1. Tạo đợt 5/20 kg từ nhiều kho/2 company, kiểm nháp và in không đổiGL/SLE/PLE/SI.
2. Gọi lại cùng token/cùng nội dung trả phiếu cũ; đổi lượng, người nhận, địa chỉ hoặc cách giao với token cũ bị chặn, không thêm phiếu.
3. Địa chỉ thuộc khách khác hoặc bị giới hạn quyền không được dùng; nhập ký tựHTML vào tên/ghi chú không biến thành mã trong bản in.
4. Kho sửa lượng nháp theo thực giao; đơn còn lại tính đúng. Xác nhận handoff/pickup và retry chỉ ghi kho/nợ một lần.
5. Bản ký không đúng phiếu/công khai bị chặn; thay tệp làm mất dấu; lưu bằng timestamp cũ bị chặn.
6. Ghi chênh lệch không tự ghi sổ; liên kết/hoàn tất xử lý đòi quyền và chứng từ đúng công ty, có lịch sử. Không đóng vụ chỉ vì đã đối chiếu tệp.
7. Người bán/kho/Dũng/kế toán trưởng được thử bằng tài khoản giả riêng, kể cả tổ hợpvai trò và scope; phản hồi native tạo/lưu, in, report/export không lộ giá vốn.
8. Bản in 2 liên đọc đủ; kiểm ảnh/PDF UAT riêng với kiểm giấy/máy in thật. Không ghi đã nghiệm thu máy in từ ảnhCI.
9. Schema chạy lặp không đổi dữ liệu nghiệp vụ; đủ 4 cổng trên đúng SHA trước đề nghị gắn tag. Khi đến VM, diễn tập bản sao dữ liệu hiện tại và sochi tiết trước nâng.

## Điểm nối đợt 2 — người giữ tiền và bàn giao

| Mã | Yêu cầu | Điểm nguồn hiện có / khoảng thiếu |
|---|---|---|
| T01 | Bao phủ mọi đường thu, kể cả cũ | 2A/PR #10 đã thêm người giữ/giao trên PE, JE Account, SI/PI/POS, Funds và quỹ nhà máy, truyền qua quầy/thu ngay/JE tự sinh; 236 ca HTTP/Desk đạt trên929d16a. Chưa coi POS/nguồn ngoài adapter và nhân sự thật đã nghiệm thu; người lập không mặc nhiên là người giữ |
| T02 | Thu thực và phân bổ tách nhau | Tái dùng `funds`, nativeJE/PE/PLE; không FIFO, không giả bank TL, không đổi chủ hàng vì công ty nhận tiền |
| T03 | Chốt ca/phải có/thực đếm | PR #11 đã có xác minh phân bổ số bắt đầu và chốt tự thân trên Cash/VND; số phải có/thực đếm/lệch, người/hạn xử lý và mốc server. 327+108 unit, 242 HTTP/Desk đạt trên022322c. PR #12 nối giữ chỗ/bàn giao; PR #13 bổ sung đóng/mở lại bằng xác minh mới/ca khớp và phiếu hoàn. PR #16 thêm Dialog chốt tự thân cho phiên nhà máy, retry sau mất200 chỉ một ca;280 HTTP/Desk đã đạt, đủ4 cổng đúngd0c1f16, chưa phát hành hoặc nghiệm thu nhân sự thật |
| T04 | Bàn giao không thu khách lần hai | PR #12: cùng Cash chuyển trách nhiệm không GL; khác Cash/nộp Bank một native JE hai dòng tiền, không PE/PLE/131/doanh thu. Nguồn được xác minh, giữ chỗ và đọc lại khi khóa. PR #16 nối `factory_cash.xac_nhan_nhan` vào cùng một H/JE; nguồn cũ đã nhận giữ lịch sử, nguồn chờ phải chuyển tiếp giữ chỗ |
| T05 | Không tự nhận, kể cả cộngquyền | PR #12: người giao phải tự gửi, đúng người nhận mới xác nhận; chặn tự nhận/nhận thay kể cả Admin. Không suy owner. PR #14 đã kiểm chặn tự nhận/nhận thay ở quỹ nhà máy cũ trênc02, đủ4 cổng; PR #16 đã nối giữ chỗ/đối chiếu/hoàn vào nguồn nhà máy, đã đủ4 cổng đúngd0c1f16 |
| T06 | Thiếu/thừa, nộpbank, giữquáhạn | PR #12 lưu số thực/thiếu/thừa, người/hạn xử lý; vượt nguồn lưu quan sát không chuyển; hủy đề nghị vẫn giữ vụ lệch/tệp. Ví có lệch hoặc nhóm chưa rõ âm bị chặn giao ra. Đã có nộp Bank; PR #13 thêm đóng/mở lại có căn cứ và hoàn toàn bộ bằng phiếu ngược, đã kiểm đúng8fc93b7. PR #16 có bảng việc tồn/người phụ trách/hạn/quá hạn và adapter nhà máy; không có cơ chế gửi nhắc tự động |
| T07 | Ngân hàng/sao kê/ngoại lệ | Có quyềnFile/Bank, mãgiaodịch chung và đối soát; PR #16 bổ sung bảng native Chốt ngày và cần xử lý: tiền hiện tại, ca gần nhất, sao kê native, nợ đến ngày, hàng và hồ sơ tồn; không coi kết quả đối chiếu tệp tạm là dữ liệu đã lưu |
| T08 | Thu quầy không ghi lặp sau mất phản hồi | PR #14: mã lượt theo người + Company, dấu nội dung trên PE; cùng cửa sổ gửi lại trả PE cũ, hai hình thức cùng lượt chỉ hai PE. Dấu giả/sửa/xóa bị chặn, hủy không tự tái thu. HTTP và Chrome đã kiểm, đủ bốn cổng đúngc02;263 HTTP/Desk PASS/0FAIL. Giới hạn: đóng/tải lại trang tạo mã mới thì phải kiểm phiếu đã thu trước khi thu tiếp |
| T09 | Tiền cá nhân không cấp GL | PR #15/base PR #14: facade/Dialog chỉ đọc đã đủ4 cổng đúngfe3140a,375+108 unit và268 HTTP/Desk PASS/0FAIL (b01477). Chung mốc/công thức/khóa; chỉ số của session, không trả GL/nguồn/người khác. NoCost/nhà máy kể cả cộng quản lý chỉ quỹ cấu hình. Chrome đọc332/0/332, mất200/đọc lại/đổi Company đạt; hủy/mốc lỗi/giữ chỗ đúng người đã kiểm. PR #16 bổ sung chốt tự thân và nhận/hoàn nguồn nhà máy qua capability đúng người/nguồn, vẫn không cấp native GL/H/snapshot; đã đủ4 cổng đúngd0c1f16. Chưa phát hành. Đặc tả nền docs/dac-ta-tien-ca-nhan-2b.md và phần nối docs/dac-ta-hoan-tat-quy-nha-may-2b.md |

Không tự gán người giữ cho khoản lịch sử chưa rõ; phảihiện chưa xácminh. Phải kiểm phiên đồngthời/khóa ghi, số tiền hữu hạn, tối đa2 sốlẻ và quyềnCompany trước mọi ghi sổ.

## Đợt 3 — nhà máy

- NM01 nhận hàng: tách lượng khỏi giá; dùng nhận chuẩn/chờđịnh giá/giá tạm đã có; bổ sung cửa sổ ngắn, hàng không đạt và phiếu cân.
- NM02 sản xuất mộtlần: đầu vào/đầu ra/phụ phẩm/dở dang/chênh lệch. Không ép nguyên liệu chưa dùng hoặc hàngđang chuyển công đoạn thành hao hụt.
- NM03 dở dang/bồn: vào–ra–còn, cho công việc tiếp tục qua ngày. Vétbồn/quyết toán chỉ khi thực sự kết thúc và theo quyền kế toán.
- NM04 đóng gói/đổi bao: giữ2 nghiệp vụ, kiểm cânđối kg/bao/bì. Không sửa kg/bao để che chênh lệch.
- NM05 xuất/chuyển: phân biệt bán/cùng Company/khác Company; phiếu ký trên DN hiện không tự bao phủ Stock Entry/chuyểnkho.
- NM06 quỹ/chốt ngày: tái dùng sổ tiền, hiển thị tiền phải còn/thực đếm/bàn giao và việc treo; không nhập lại Excel.
- NM07 quyền Dũng: bảo vệ cảAPI, phản hồiinsert/save, report, export, print và tổ hợp role; không chỉ ẩnôUI. Quyền0.15.2 có hồi quy nhưng chưa nghiệmthu tài khoảnnhân sự thật.

## Đợt 4–5

TC01 đầu kỳ; TC02 mua–nhận–hóa đơn–ứngtrước–trả NCC; TC03 chi phí chưa trả/đến muộn/trả trước; TC04 giá thành/dở dang/repost; TC05 tài sản/CCDC/khấuhao; TC06 vay/lãi/vốn; TC07 thu hộ/nội bộ; TC08 báo cáo điều hành/tạm tính/chất lượng dữ liệu. Mỗi mục phải kiểm lại code và ca đã có, không kết luận chưa có chỉ vì thiếu màn tổng hợp.

HD01 hóa đơn một phần: yêu cầu từng dòng/lượng, gắn lần giao, hàngđợi xử lý, MISA điều chỉnh/thaythế/hủy. Chờ chốt đặc tả riêng; không tự triển khai từ đề xuất này.

## Mẫu hồ sơ 9 nhóm áp dụng cho từng đợt

1. Mục tiêu/phạm vi và ngoài phạm vi.
2. Hiện trạng đúng phiên bản/SHA, code và bằng chứng.
3. Quy trình: ai làm, ai chịu trách nhiệm, người làm thật và người nhập thay.
4. Quy tắc/ngoại lệ và nguyên tắc ghi sổ.
5. Dữ liệu: field/source, trạng thái, điều kiện chuyển và snapshot/lịch sử.
6. Quyền: hành động/field/Company/Warehouse và bằng chứng đối chứng dương/âm.
7. Tác động: kho/nợ/tiền/giá vốn/sản xuất/MISA; không tạo sổ trùng.
8. Nghiệm thu: input, actor, thao tác, số kỳ vọng, truy vấn đối chiếu và artifact.
9. Triển khai/khôi phục: schema/cờ, CI đúng SHA, diễn tập tách biệt, ghi rõ chưa kiểm/đã kiểm.

## Điểm dừng hiện tại

Production0.15.3 đã chứa các lát1A, GN09, GN10/GN11 và bộ mẫu mới; PR #5 đã gộp main. GN01 thông tin tham gia token; GN03 địa chỉ/người nhận theo đợt; GN04 tách người thực giao khỏi actor/time server. GN09 có vòng báo/giao/chốt/mở lại, căn cứ đúng nguồn, bảo vệ chốt–hủy đồng thời và giữ lịch sử. Đặc tả tại `docs/dac-ta-giao-nhan-dot-1.md`, `docs/dac-ta-chenh-lech-giao-nhan.md`, `docs/dac-ta-xuat-ngay.md`.

GN10/GN11 đã kiểm lại trong release0.15.3: xuất ngay tách ý định với lập nháp, nguyên tử nhiều nguồn, retry sau commit không tăng sổ; có ca Chrome chặn phản hồi200 thật. Không mở lại phần đã hoàn thành như một tính năng chưa làm.

Đồng bộ dữ liệu giao nhận đã có: `print_utils.kh_aph_giao_nhan` dùng snapshot mới và fallback phiếu cũ/phiếu trả; mẫu Phiếu xuất kho bán hàng/Biên bản giao nhận gọi helper này; `trung_tam_ban.in_lai` render mẫu chuẩn; `delivery_slip.render` tách metadata/khối ký từng DN. Đây là phần mã đã phát hành, không còn là việc chưa triển khai.

### Việc còn lại trước khi đóng đợt 1

1. **Lối in lại A5 từ phiếu đã có:** production0.15.3 chỉ mở mẫu nhanh từ Dialog lập đợt. Ứng viên `feat/in-lai-a5-20261018` bổ sung nút “Phiếu xuất kho A5 (2 liên)” trên DN và API `ban_nhanh.print_note`; dùng chung renderer, không tạo/sửa phiếu hoặc ghi sổ. Đã đủ bốn cổng trên `1e89ace187468d976cb3361d3a0dd6ea75f917c1`, UAT229 PASS/0 FAIL (b01438), gồm HTTP/Chrome in lại hai lần không tăng sổ; chưa phát hành. `trung_tam_ban.in_lai` vẫn là lối in chuẩn riêng.
2. **Nghiệm thu người dùng/máy in/dữ liệu đại diện:** theo `docs/nghiem-thu-mau-in-20261018.md`, ghi expected/actual. IN02 đã kiểm UAT lối mở lại A5 từ DN ở PR #9; còn phát hành và nghiệm thu thực tế. PDF CI và log triển khai không thay kết quả này. Tải thực tế còn chưa đo; quy chế biểu mẫu vẫn là dự thảo.

Sau khi phần kỹ thuật/UAT đạt, có thể chuyển đợt2; đợt1 giữ trạng thái chờ nghiệm thu thực tế đến cuối theo quyết định mới. Đợt2 bắt đầu bằng đặc tả9 nhóm cho người giữ tiền/chốt ca/bàn giao toàn cửa hàng, tận dụng thu/cọc/thu hộ/quỹ nhà máy hiện có. Đợt3 còn màn nhập lượng một lần; đợt4 còn đối chiếu và chốt chuỗi, không viết lại các nghiệp vụ nền. Đợt5 phải chốt nghiệp vụ riêng trước code.

Rà nguồn đợt2: `docs/dot-2-ra-soat-nguon-tien.md`. Chốt ca/giữ chỗ/bàn giao/đối chiếu đã có trong PR #11–#15; PR #16 hoàn thiện adapter nhà máy, chốt tự thân và bảng ngày. Bằng chứng mới nhất ở đầu hồ sơ bàn giao, không dùng trạng thái lịch sử dưới đây làm kết luận hiện tại.

Đợt2A: đặc tả9 nhóm `docs/dac-ta-nguoi-giu-tien-2a.md`, ứng viên PR #10 đã đạt bốn cổng trên929d16a (236 PASS/0 FAIL); chưa phát hành. Thiết kế2B `docs/thiet-ke-chot-ca-ban-giao-2b.md` đã được triển khai qua các PR #11–#16; trạng thái từng lát và bằng chứng ghi riêng ở trên. Không gọi báo cáo phát sinh2A là số tiền đang giữ.


## Điểm nối PR #13 — đối chiếu và hoàn

Mã nghiệp vụ/kiểm8fc93b7a1b674aee3722fe7b1f59de760a2f088d:358+108 unit đạt;259 HTTP/Desk PASS/0 FAIL (b01468), đủ4 cổng. Artifact đã đọc, ảnh hoan-tien.png đã xem; không thay nghiệm thu nhân sự thật hoặc diễn tập dữ liệu production khi phát hành. Đặc tả9 nhóm tại `docs/dac-ta-xu-ly-lech-hoan-tien-2b.md`. Hồ sơ đối chiếu chỉ quản lý, cần xác minh mới và ca khớp còn hiệu lực từng phía Cash; không tự tạo bút toán, giữ lệch cũ, hủy hồ sơ mở lại chặn ví. Hoàn toàn bộ theo người/quỹ/số gốc bằng phiếu ngược chiều, chặn nguồn đã dùng/giữ chỗ/trùng; Bank chỉ làm nguồn hoàn đúng bàn giao gốc, không mở luồng chi tùy ý. Không hủy JE gốc. Không hỗ trợ hoàn một phần hoặc hoàn tiếp phiếu hoàn.

Các khoảng thiếu ghi tại thời điểm PR #13 đã được xử lý tiếp: PR #14 token thu quầy/guard quỹ cũ, PR #15 tiền cá nhân chỉ đọc, PR #16 adapter nhà máy/chốt tự thân/bảng ngày. PR #16 đã đủ4 cổng đúngd0c1f16,280 HTTP/Desk PASS/0FAIL; artifact và ảnh đã đọc/xem. Phần kỹ thuật lát2B đã khép, chuyển rà nguồn/đặc tả9 nhóm đợt3; không viết lại nghiệp vụ nền. Production0.15.3 chưa đổi; nghiệm thu thật gom cuối.
