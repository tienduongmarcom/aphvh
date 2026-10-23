# Trạng thái phát hành APH-VH (một nơi duy nhất — cập nhật mỗi lần phát hành / triển khai)

## 23/10/2026 — Đủ bốn cổng: giao nhận và hồ sơ phân quyền nhân sự

Mã ứng viên đã kiểm: `ae49241a14f3b47cb799d9654d99b9bcf40b6e3d`, PR38 vẫn nháp. Chưa tăng version, gắn tag, gộp hoặc triển khai; production vẫn0.16.4/digest1a8f0063 như hồ sơ phát hành. Chưa chạy bộ chuẩn bị9nhân sự lên production, chưa đặt mật khẩu/kích hoạt; toàn bộ thao tác nhân sự mới chỉ ở site UAT dùng một lần.

- UAT [39929582119](https://github.com/tienduongmarcom/aphvh/actions/runs/39929582119) SUCCESS. Đã tải/đọc artifact:014=143PASS/0FAIL, inventory33,funds20,cost16,dispatch48,0111=15,0112=13,0113=13,0114=8,012=9,013=10,native4,prepare3. Có9User tạo disabled/reuse/không email; Module Profile và login bằng mã nội bộ; quyền CEO/nhận tiền hẹp; Hạnh công nợ tổng hợp độc lập kho; chuyển hai chiều Hạnh/Dũng, sai kho/native redirect bị chặn, retry một phiếu nhận, không công nợ. Không suy thành nghiệm thu nhân sự thật.
- Cổng2 [39929658679](https://github.com/tienduongmarcom/aphvh/actions/runs/39929658679) SUCCESS: đã đọc log53mục/0lỗi.
- Cổng2b [39929662938](https://github.com/tienduongmarcom/aphvh/actions/runs/39929662938) SUCCESS: đã đọc log108+650unit, dựng/nâng/quay lui đều53mục/0lỗi, giữ ca nâng sai và probe có hạn chót.
- Cổng3 [39929667314](https://github.com/tienduongmarcom/aphvh/actions/runs/39929667314) SUCCESS: đã tải/đọc artifact, schema1189/1189 lệch0 (6/6mục bỏ qua theo danh sách tường minh), rollback1105/1105 lệch0; cố ý nâng sai→khôi phục, tổng/đếm/chi tiết KHỚP. Không chạm VM thật.
- Cục bộ650unit app không bỏ qua và108lõi đạt; Pyflakes/diff đạt. PDF native đã kiểm số trang/kích thước: bộ giấy4trang A4+2A5+A4, phiếu nhanh2A5, đối soát cọc2A4. Bằng chứng in cọc không tạo thu lần hai đã PASS trong014; chưa máy in thật.

Giữ FAIL39926823240 và nguyên nhân/cách sửa ở mục dưới; không bỏ ca hay giảm143. Các cổng263fe81 trước đó cũngSUCCESS, nhưng bằng chứng ứng viên ở trên là cùngae49241. Bản ghi sau mốc này chỉ cập nhật hồ sơ/PR, không thay mã đã kiểm.

Tiếp theo còn: thu/hoàn chênh lệch đổi mã trong một cửa sổ theo phạm vi cũ; nghiệm thu dữ liệu/nhân sự/máy in/MISA thật để cuối theo chủ dự án. Trước bật nhân sự: phát hành đúng nguồn theo quy trình, quản trị xem kế hoạch `staff_accounts.chuan_bi` mặc định chỉ đọc, đối chiếu kho/tài khoản sẵn có, chuẩn bịdisabled rồi đặt mật khẩu riêng/bật username/kích hoạt. Không gửi mật khẩu hoặc reset link qua chat. Không tuyên bố toàn kế hoạch hoặc production đã hoàn tất.


## 23/10/2026 — Đối chiếu lại ca phạm vi kho nhận dự kiến

UAT39926823240 đúngd198495 FAIL tại HTTP014 chuẩn bị gom kho: ca cũ đòi từ chối chỉ vì kho nhận dự kiến ngoài quyền Warehouse. Đã đọc log gốc; đây là điều kiện đã được thay bằng metadata nơi đến trong thiết kế hai đầu kho. Sửa ca thành đủ ba kiểm: vẫn từ chối mở Warehouse nơi đến, cho chuẩn bị nháp từ kho nguồn được giao, và từ chối chuẩn bị nếu dùng kho nguồn ngoài phạm vi. Không bỏ chặn xuất/nhận thực tế, không giảm số ca143. Lượt FAIL được giữ, chưa tới ca hai nhân sự nên chưa chứng minh143. Đã đọc Cổng339923900504 trên5bed91b: schema1189/1189 lệch0 (bỏ qua6/6 mục được khai tường minh), quay lui1105/1105 lệch0, phục hồi sau nâng sai KHỚP.

Cổng239929259865/2b39929263786/339929267700 đang chạy263fe81 trước chỉnh ca này; cần ghi kết quả đúng nguồn. Bộ108unit lõi đạt;650unit app đang chạy lại. Hồ sơ nhân sự đã bỏ mô tả cũ còn nói các quyền hẹp chưa được viết. Production0.16.4, chưa bật/tạo nhân sự thật; còn thu/hoàn đổi mã một cửa và nghiệm thu thực tế.


## 23/10/2026 — Giữ kiểm soát nhận chuyến cả trên phiếu native

Bổ sung lock_outgoing kiểm quyền nguồn hoặc projection đúng kho dự kiến cả khi người dùng lập phiếu nhận native. Nhận khác kho dự kiến phải qua cửa sổ nhận có dấu/lý do, không bỏ qua bằng StockEntry thủ công. Đã thêm native thử raw redirect và vẫn giữ case hai chiều; chưa có kết quả. Bộ chuẩn bị gắn Module Profile có sẵn theo nhiệm vụ để bớt menu, không thay quyền. Native fixture bật đăng nhập username CHỈ trên UAT bằng SystemSettings.save rồi kiểm mã hanh trả đúng principal nội bộ; bộ chuẩn bị thật vẫn không đổi cấu hình login hoặc kích hoạt.650unit không bỏ qua đạt trước assert native mới; Pyflakes/JS/diff giữ nghiêm.

UAT39926823240 đang kiểmd198495 trước ba bổ sung này, tổng143; không hủy lượt hữu ích. Cả4cổng5bed91b đãSUCCESS (UAT142/Cổng239923899687/2b39923899864/339923900504); UAT142 đã đọc artifact, cổng3 mới cần tải/đọc chi tiết cuối trước ghi mức schema. Không suy sang nguồn mới. Production vẫn0.16.4, chưa chuẩn bị hoặc bật nhân sự thật. Tiếp theo đọc143, sửa nếu lỗi, rồi chạy nguồn cuối có username/module/native guard. Còn thu/hoàn đổi mã một cửa theo phạm vi cũ, không gọi toàn kế hoạch đã hoàn tất.


## 23/10/2026 — Đã đọc142PASS; bổ sung kiểm chuyển hai đầu khác phạm vi kho

UAT39923012594 đúng5bed91bd9bf6c5a7d46b03d15e46c93aa75edea5 SUCCESS, đã tải/đọc142PASS014 và tất cả bộ hồi quy:0114=8,dispatch48,funds20,cost16,inventory33,0111=15,0112=13,0113=13,012=9,013=10,native4,prepare3. Bộ chuẩn bị9disabled/reuse, quỹ nhận hẹp/KTBH gửi khôngGL, CEO đọc giá vốn/dòng tiền và từ chối sửa/NoCost, công nợ tổng hợp không đọc packet ngoài kho đều đã qua native. Cổng239923899687 và2b39923899864 cùng5bed91b SUCCESS; Cổng339923900504 còn chạy lúc cập nhật, chưa suy kết quả cho mã sau.

Rà thêm đầu nhà máy↔cửa hàng: quyền tách Warehouse đúng nhưng người gửi không được chọn tên kho nhận ngoài phạm vi, người nhận không được đọc phiếu nguồn có kho gửi ngoài phạm vi. Đã tách metadata kho dự kiến (chỉ tên lá cùng Company, không tồn/giá) khỏi quyền kho thao tác; CF kho dự kiến ignore_user_permissions, nguồn/đích thực vẫn native. Đầu nhận chỉ xem projection lượng của đúng chuyến đã gửi đến kho mình, có quyền StockEntrycreate/submit/Company/Item; không mở raw nguồn/Warehouse nguồn. Mapper chỉ bỏ đọc nguồn đã ràng buộc, target reset quyền rồi kiểm create/nativeinsert/submit như trước; không trả giá hoặc mở quyền sổ. Chuyến không chỉ định kho nhận vẫn cần đọc nguồn native như cũ. List không lộ tên phiếu không được đọc/không gửi đến kho mình.

Thêm HTTP_014_CHUYEN_KHO_TACH_NHAN_SU, tổng143giữ142cũ: hai bản sao hồ sơ Hạnh/Dũng được bật mật khẩu ngẫu nhiên CHỈ trong UAT dùng một lần, sau khi đã chứng minh bộ chuẩn bị tạo9disabled/khôngemail. Kiểm gửi/nhận cả hai chiều, chuẩn bị/in/submit, không đọc Warehouse/phiếu nguồn ngoài phạm vi, sai kho bị chặn trước nhận, native receipt/retry/không nợ.650unit không bỏ qua, JS/Pyflakes/diff đạt; chưa native mã mới. Không bật ai trên production;0.16.4 giữ nguyên. Còn thu/hoàn đổi mã một cửa và nghiệm thu thật theo kế hoạch.


## 23/10/2026 — Quyền theo nhóm địa điểm, giá sàn và sửa khai báo khế ước

Rà vận hành phát hiện cấp theo lá sẽ chặn Hạnh khi hệ thống sinh kho cách ly/chờ xử lý mới. Đã đổi kế hoạch User Permission sang NHÓM địa điểm cấu hình + transit chuẩn, bao gồm hậu duệ; không cấp gốc toànCompany. Hạnh chỉ nhóm cửa hàng/vệ tinh, Dũng chỉ nhóm nhà máy (và Company tương ứng). Kho mới trong địa điểm được giao theo quyền nhóm; kho ngoài địa điểm cấu hình phải dừng đối chiếu. Hook Warehouse on_update/after_rename/on_trash bỏ cache của mọi người có giới hạn kho ngay và sau commit, tránh quyền cũ sau chuyển cây hoặc người khác tạo kho mới; không ghi UserPermission/role.

Bộ chuẩn bị bổ sung Trang vào allowlist giá dưới sàn theo đúng4Company, không tự duyệt; không ghi đè cấu hình khác đã có. Chưa kích hoạt User hoặc đổi cách login. Native mới có HTTP_014_CHUAN_BI_NHAN_SU (tổng142):9disabled/retry/khôngemail, phạm vi Warehouse thật, Ninh đọcGL không tạoJE, Ánh khôngGL/JE, Hường/Hạnh ẩn vốn, kho cách ly mới đúng nhóm.647unit không bỏ qua đạt trước sửa metadata khế ước.

UAT39921214288 đúngcd62652 FAIL lúc cài: add_permission viewer khế ước kích hoạt validation, bắt bản khai APH Khe uoc vay đã có System Manager.import=1 nhưng allow_import chưa bật. Đã đọc fresh-site-evidence gốc (NameError kh_aph phía cuối chỉ là fallback bench). Sửa manifest bật allow_import cho khế ước để khớp quyền System Manager đã khai; không cấp import cho viewer/nhân sự, không nhập dữ liệu hoặc ghi sổ. Không bỏ validation. Cổng239921522178 cùngcd62652 SUCCESS,2b39921525877/339921529787 còn chạy; không suy sang sửa mới. Cần native142 đúng mã cuối. Production0.16.4 giữ nguyên, chưa chạy chuẩn bị người thật.


## 23/10/2026 — QA quyền CEO bắt thiếu quyền đọc khoản vay

UAT39919338739 đúng81b58da FAIL bộ0114: CEO mở được lãi gộp nhưng dòng tiền gọi get_list APH Khe uoc vay và bịPermissionError. Các bộ trước đó inventory33,funds20,cost16,dispatch48,b0111=15,b0112=13,b0113=13,native4,prepare3 PASS; chưa chạy014. Đã tải/đọc artifact và giữ lỗi. Sửa đúng một quyền đọc/report khế ước vay cho vai trò viewer, không cấp ghi/duyệt khoản vay hoặc vai trò kế toán. NoCost hook khế ước vẫn chặn. Bản mới cũng chứa bộ chuẩn bị tài khoản644ca chưa native, phải kiểm đủ trên nguồn sửa.

Đã đọc Cổng2b39916449799 đúng0d6e866: dựng/nâng/quay lui53mục khônglỗi; Cổng339916449912 cùngSHA SUCCESS đã tải/đọc schema1161/1161 lệch0, rollback1105/1105 lệch0 và phục hồi sau nâng sai KHỚP. Các bằng chứng này chỉ tới quyền duyệt khách rủi ro trước viewer/receiver/công nợ mới, không thay kết quả native mã sau. Production0.16.4 không đổi.


## 23/10/2026 — Bộ chuẩn bị9nhân sự, chưa kích hoạt

staff_accounts.chuan_bi mặc định chỉ xem kế hoạch. Ghi thật yêu cầu Administrator và xác nhận đúng site, đủ vai trò/Workspace/Company/kho; tạo9User disabled, không mật khẩu/welcome email/đổi cấu hình đăng nhập. Không cấp System Manager; Hường/Hạnh/Trang không cần Accounts User/Sales Manager để chữa thao tác. Ninh chỉ viewer+receiver; Ánh chỉ receiver; Dũng factory+NoCost+StockUser. Lan/Hà Accounts User theo tổng hợp/thuế; không tự thành người nhận tiền hoặc quản trị. Trang có quyền khách rủi ro, người duyệt giá sàn còn cần cấu hình allowlist riêng trước kích hoạt.

Phân kho bằng địa điểm loại nha_may/ban_hang trong khach.json và cây cha thực tế cùng Company; nhóm/lá tên tùy ý đều truy theo cha. Kho transit chuẩn có metadata Transit dùng chung chỉ trong Company có địa điểm tương ứng. Kho mới không xác định, vòng cha, saiCompany phải đối chiếu trước, không đoán theo tên. User Permission Warehouse áp riêng vào chứng từ kho/bán/mua; Company áp đúng4đơn vị hoặc Company có kho nhà máy của Dũng. Không sửa tài khoản cũ; chỉ reuse bản disabled đúng marker/lượt chuẩn bị, username/tên/vai trò/Workspace/toàn bộUserPermission còn khớp. Lỗi ghi rollback nguyên lượt.

644ca cục bộ không bỏ qua đạt. Đã thêm native vào fixture014: preview9, tạo9disabled, chạy lại không trùng, vai trò đúng, khôngSystemManager, khôngemail hoặc thay chế độ login. Chưa chạy mã mới. UAT39919338739 kiểm81b58da trước bộ chuẩn bị, đang chạy; Cổng2b39916449799 vàCổng339916449912 đúng0d6e866 SUCCESS, không suy sang mã sau. Production0.16.4 không đổi. Sau native đạt còn cấu hình giá sàn, mật khẩu/kích hoạt bằng quản trị, kiểm thực tế theo nhân sự; không tự coi tài khoản disabled là đã đăng nhập dùng được. Còn thu/hoàn đổi mã một cửa.


## 23/10/2026 — Tách công nợ tài chính khỏi bộ phiếu có giới hạn kho

Thêm vai trò đánh dấu Đối soát công nợ toàn khách, không tự cấp quyền chứng từ. Chỉ khi đã có quyền kế toán và mọi giới hạn Warehouse đều áp riêng vào chứng từ kho/bán/mua được liệt kê, mới được lập bản TỔNG HỢP công nợ theo Company/Customer. Các giới hạn Account/CostCenter/Project/dimension khác vẫn chặn; Warehouse toàn hệ thống hoặc applicable_for trống vẫn chặn. Bản này đóng băng summary_only=true và chỉ chứa biên bản tài chính, KHÔNG ghép phiếu nguồn. Native quyền từng nguồn vẫn kiểm lúc tạo; phiếu hàng/thu in riêng theo quyền. Hồ sơ có giới hạn kho chỉ đọc/list/tải PDF summary_only=true, không mở lại packet cũ có phiếu ngoài phạm vi; query SQL chặn luôn payload cũ. Không sửa hoặc public hóa PDF cũ. Đã thêm hồi quy API/list/file/Company và pure scope;640ca cục bộ không bỏ qua đạt. Native mới chưa chạy, chưa cấp role Hạnh.

UAT39918413501 đúng4f75492 FAIL sớm ở kiểm SHA credit_release.py: workflow còn ghim hash trước thay đổi quyền duyệt. Chưa chạy schema/UAT nghiệp vụ mã mới. Đã sửa so SHA tệp trong image với SHA của đúng checkout, giống kiểm hooks, không bỏ kiểm toàn vẹn. Cổng2b39916449799 đúng0d6e866 SUCCESS (chờ đọc log chi tiết); Cổng339916449912 cùngSHA còn chạy. Không suy sang CEO/cash receiver/công nợ mới. Tiếp theo dispatch141 trên mã sửa, đọc native assertions quyền và giữ mọi lượt FAIL.


## 23/10/2026 — Sửa bộ đọc PDF trên đúng container, giữ lượt lỗi

UAT39915893234 đúng9a150f8 FAIL tại b014_debt_statement.chay_coc: ModuleNotFoundError pypdf trên runner. PDF đã được tạo nhưng chưa chạy xong assertion/nội dung/NoCost/khôi phục ca cọc, không coi đạt. Đã tải artifact, render và xem cả2trang doi-soat-coc-theo-don.pdf: đối soát đủ bảng/chữ ký, phiếu thu100.000 có Nợ1111/Có3388/số khoản nhận/ô ký, không cắt nội dung. Sửa helper dùng cùng pypdf trong container ERPNext như bộ giấy cũ, không cài runner hoặc bỏ assert. Lượt39918301530 vừa dispatch3984cec bị hủy sớm vì chưa chứa sửa helper, không tínhPASS/FAIL nghiệp vụ. Chạy lại141ca trên mã sửa tiếp theo. Quyền CEO/nhận tiền637unit đã viết, chưa có native chứng minh.


## 23/10/2026 — ĐANG KIỂM: quyền điều hành và nhận tiền hẹp

Đã viết executive_access: vai trò Xem báo cáo điều hành, quyền đọc/report trên nguồn, chỉ mở hai báo cáo lãi gộp và dòng tiền; không mở guard khóa kỳ/sửa chứng từ. Giới hạn Company vẫn qua native; hồ sơ có dimension chi tiết khác bị chặn tổng hợp. Có quyền Report tùy chỉnh riêng không tự ghi đè. Bộ cài tạo role trước rồi thêm vào đúng hai Report, giữ vai trò cũ; context in_import chỉ quanh save Report chuẩn, khôi phục ngay.

Đã viết cash_receiver capability theo actor/tuple nguồn đã khóa: người chỉ có Nhận bàn giao tiền đọc đúng hồ sơ gửi cho mình, xác nhận qua canonical receive; nội bộ đọc đủ Cash để kiểm nguồn, không trả snapshot hay cấp GL/JE. Khác quỹ tạo đúng JE liên kết một lần, cùng quỹ chỉ chuyển trách nhiệm; retry giữ hash. Từ chối tự nhận/nhận thay/sửa nguồn; NoCost không cộng role để vượt chặn; nhà máy giữ adapter cũ. Kế toán bán hàng được tạo/gửi/hủy bàn giao của mình qua số tiền cá nhân và native H, không thêm Accounts User/GL; nhận cũng dùng capability. UI dùng form cũ, ẩn nút hoàn nếu không có quyền tạo; Workspace tiền thêm đường bàn giao chờ nhận và hai báo cáo, không thêm màn.

Đã thêm ca HTTP_014_NHAN_TIEN_QUYEN_HEP; bộ014 tăng141, giữ toàn bộ140ca cũ. Ca mới kiểm sai người, readonly GL/JE, đúng người nhận60/100, khác quỹ ghi1JE2GL khôngPE/PLE, retry, cùng quỹ khôngJE, KTBH gửi30cho chủ không cầnGL. Bộ0114 mở rộng ca hiện có: CEO xem đúng giá vốn/lãi, mở dòng tiền, không sửa SI/khóa kỳ; cộngNoCost bị chặn.637ca cục bộ không bỏ qua đạt trước đổi lối tắt; JS/Pyflakes đạt. Chưa có bằng chứng native mã mới, chưa tạo/cấp quyền người thật.

UAT39915893234 vẫn kiểm9a150f8 (phiếu thu cọc), không chứa quyền mới; Cổng2b39916449799/Cổng339916449912 kiểm0d6e866 cũ, không suy sang phần này. Bắt buộc đọc/giữ kết quả rồi chạy đủ cổng trên mã cuối. Còn đối chiếu phạm vi kho Hạnh/Dũng, bộ áp tài khoản và thu/hoàn đổi mã một cửa. PR38nháp; production0.16.4 không đổi.


## 23/10/2026 — Tách quyền duyệt khách rủi ro, chưa áp nhân sự

Thêm vai trò Duyệt khách rủi ro qua bộ cài schema rõ ràng dưới cờ high_risk_credit_guard hiện có. Chỉ cấp đọc Company/Customer/DN và đọc/tạo/ghi phiếu duyệt bất biến; không cấp JE/GL, sửa Customer, ghi kho hoặc tài chính. validate_release/approve/revoke nhận vai trò riêng hoặc Accounts Manager; chỉnh dấu rủi ro/hạn mức trên Customer vẫn chỉ Accounts Manager. ROLE_NO_COST chặn cả khi cộng vai trò duyệt/Accounts Manager. Không gán vai trò vào tài khoản thật. Không thay quy tắc hạn mức: global_credit đang cảnh báo, high-risk mới chặn giao và dùng dấu duyệt. Không gọi phần này là đã duyệt vượt mọi hạn mức.

628ca cục bộ đủJinja2 không bỏ qua đạt. Mở rộng bộ dispatch48 hiện có bằng nhân sự giả chỉ có vai trò duyệt: phải duyệt/thu hồi đúng người, không sửa hạn mức hoặc tạo JE, sổ không đổi. Chưa có kết quả native trên mã này. Đã đẩy0d6e866f25b4d1dc7f40811ea1dab46cdfdb4ec1 và dispatch Cổng2b39916449799/Cổng339916449912, đang xếp hàng. Bước tiếp theo bắt buộc: đọc UAT9a150f8, tải/xem PDF phiếu thu cọc; sau khi lượt đó kết thúc dispatch UAT trên mã quyền0d6e866 (không hủy trước), đọc ca dispatch duyệt hẹp và các cổng. UAT39915893234 đang chạy9a150f8 trước thay đổi quyền, không chứa vai trò mới; chưa dispatch lượt mới để tránh hủy lượt in đang hữu ích. Còn CEO chỉ đọc, nhận tiền hẹp, phạm vi kho Hạnh và thu/hoàn đổi mã. Production0.16.4 và PR38nháp giữ nguyên.


## 23/10/2026 — Đọc đủ140ca, chuẩn bị mã nhân sự nội bộ

UAT39897679945 đúng8f97806440b6f8b0ff08f483585b8aa8880114b9 SUCCESS. Đã tải candidate-image-evidence và đọc140PASS bộ014; HTTP_014_CHUAN_BI_GOM_KHO xác nhận gợi ý theo đơn/không giữ chỗ/draft/retry/phạm vi; HTTP_014_DOI_SOAT_COC_THEO_NGUON xác nhận cọc50.000/khả dụng50.000, không giảm nợ hai lần, bản cũ bất biến sau nhả tiếp. Các bộ còn lại: inventory33,funds20,cost16,dispatch48,b0111=15,b0112=13,b0113=13,b0114=8,b012=9,b013=10,native4,prepare3 PASS. Đã render/xem PDF doi-soat-coc-theo-don.pdf một trang không cắt bảng/chữ ký. Cổng339897682847 cùng8f97806: đã tải/đọc schema1154/1154 lệch0, quay lui1105/1105 lệch0, phục hồi sau nâng sai KHỚP. Không suy sang phần in phiếu thu9a150f8.

Đã dispatch UAT39915893234 đúng9a150f80b95d33b6f5d0b8f6bfdfefa9944b01a3 cho phiếu thu cọc/bộ giấy mới, đang chạy; chưa kết luận. Chủ dự án chọn mã nội bộ: huong,hanh,dungktt,lan,ha,trang,ninh,anh,dungnm; Tâm để sau. Thêm staff_accounts chỉ đọc kế hoạch/kiểm trùng username và định danh email kỹ thuật .invalid, không tạo User/gửi thư/đặt mật khẩu/cấp vai trò. Cục bộ625ca không bỏ qua đạt (chạy có Jinja2); lượt đầu thiếu Jinja2 bỏ17ca đã chạy lại đầy đủ. Production vẫn chỉ có Administrator/Guest theo màn User đã bỏ lọc, chưa áp quyền nhân sự. Còn quyền hẹp CEO/duyệt bán chịu/nhận tiền, xung đột giới hạn kho Hạnh với đối soát tổng khách, và thu/hoàn chênh lệch đổi mã một cửa. PR38nháp, production0.16.4 không đổi.


## 23/10/2026 — Ghép phiếu thu khoản thực nhận, không tạo PE mới

Đã viết funds_print.receipt_html/print_receipt: nguồn FundsReceipt đã ghi và JE gốc phải khớp Company/link/số nhận/đối ứng, tài khoảnVND và quyền đọc/in trên nguồn/Company/Account/JE/Customer. Dữ liệu trình bày giữ số khoản nhận, không giả lập hoặc chènPE; Nợ/Có đọc JE gốc. Dùng lại PrintFormat Phiếu thu chi đang dùng theo công ty, tự phân biệtCash/Bank; không phát minh mẫu hay đổi chế độ kế toán. Nút In phiếu thu trên khoản nhận đã ghi; bộPDF tự ghép khi chọn FundsReceipt, không in lại phiếu nhận cũ chỉ vì chọn action. In không ghiGL/PLE/PE hoặc thu tiền lần nữa. Actor hạn chế bịfunds.require chặn trước đọc nguồn.

Cục bộ621ca không bỏ qua đạt, JS/Pyflakes/diff đạt. Ca nativecọc140 được mở rộng kiểmPDF có phiếu thu, APIin không ghi sổ và NoCost bị chặn; chưa có kết quả của phần in. UAT39897679945/Cổng339897682847 đang kiểm8f97806 trước phần in; không chứa bước này. Bằng chứng139/UAT39895504031 đúng8e61a68 đã tải/đọc đủ139PASS, các bộ hồi quy; ảnh phần trả không popup, PDF4trang đúngA4+2A5+A4. Cổng339893222080 đúngd54522d đã tải/đọc1154/1154 vàrollback1105/1105 lệch0, sau cố ý nâng sai khớp chi tiết. Không suy sang mã mới. Còn thu/hoàn chênh lệch đổi mã một cửa và phân quyền nhân sự thật; PR38nháp/production0.16.4 giữ nguyên.

## 23/10/2026 — Nối tiền/cọc vào đối soát theo nguồn; chờ native140

Đã mở nguồn chọn APH Funds Receipt/Action trên cùng Dialog đối soát và nút từ form tiền/cọc; kiểm nguồn đúng khách/đơn vị/mốc, action phải có khoản thực nhận hợp lệ. Chỉ chọn JE liên quan có đúng đối tượng khách để tính phát sinh công nợ; khoản giữ tiền không có đối tượng khách không tự thành giảm nợ. Không in toàn bộ JE nội bộ cho khách. Payload/bản in có chứng từ tiền/cọc chọn và cọc còn giữ theo receipt/reservation/đơn/nguồn Company. Tính lại từ cùng funds_rules.position, không FIFO hoặc trừ cọc vào nợ lần nữa; receipts/actions sau ngày mốc không cộng vào số hiện tại. Nguồn Company/đơn ngoài quyền bị chặn; bản đã cấp giữ số/PDF cũ sau khi giải phóng tiếp.

Đã tăng MODIFIED và chạy generator cho mẫu in,615ca cục bộ không bỏ qua đạt, JS/Pyflakes/diff đạt. Thêm ca HTTP_014_DOI_SOAT_COC_THEO_NGUON: nhận100.000, giữ70.000, nhả20.000 còn50.000/khả dụng50.000, không tạo nợ; retry, sai khách, sau nhả tiếp vẫn giữ bản ký cũ. Kỳ vọng140PASS và artifact doi-soat-coc-theo-don.pdf; chưa có native mã mới. Bộ giấy từ FundsReceipt/Action trình bày trong biên bản, chưa có phiếu thu cọc riêng tự ghép như PE; không coi phần này đã đủ mọi mẫu thu. Còn thu/hoàn chênh lệch đổi mã một cửa và quyền nhân sự.

UAT39895504031 đúng8e61a68 đãSUCCESS139ca theo workflow; đang tải/đọc artifact để chốt chi tiết/ảnh/PDF. Không chứa gom theo đơn ede9ee9 hoặc phần cọc mới. Cổng339893222080 đúngd54522d đãSUCCESS nhưng tải artifact lần đầu lỗi mạng, đang thử lại. Không suy các lượt này sang mã sau. PR38nháp, production0.16.4 không đổi.

## 23/10/2026 — Thêm gom hàng trực tiếp từ đơn, đang chờ native

Đã viết order_transfer.preview và nút Gom hàng cho đơn trên form đơn chung: lấy phần còn chưa giao/chưa lậpDNnháp bằng cùng nguồn ban_nhanh, gom cùng mã theo Company/kho giao khách, điền sẵn mã/tên/kg/bao vào cửa sổ chuyển kho hiện có. Người dùng chỉ chọn kho thực lấy, lượng cần chuyển và người/xe. Kho nhận theo đơn giữ readonly; đổi nơi giao phải dùng đổi nguồn phần chưa giao trước. Không thêm màn/sổ/CF/cờ; không tạo chứng từ từ preview, không trả giá vốn/giá bán. Server kiểm quyền chuyển/StockEntrycreate và toàn bộ nguồn đơn/Company/Item/Warehouse; không cấp quyền để vượt phạm vi. Cửa sổ dùng factory_transfer.send cũ để chuẩn bị nháp/in, ghi nguồn đơn vào ghi chú; xác nhận xuất/nhận vẫn native.

Lượng là gợi ý nhu cầu chưa giao, KHÔNG phải thiếu tồn sau bù trừ, không giữ chỗ hoặc trừ các chuyến gom khác. Nhân viên kiểm lượng thực cần chuyển; hàng có quy cách lẻ không tự làm tròn kg/bao. Không coi đây là sổ phân bổ chuyển kho theo đơn hoặc tự chuyển nguồn đơn. Cục bộ608ca không bỏ qua đạt, JS/Pyflakes/diff đạt. Đã mở rộng HTTP_014_CHUAN_BI_GOM_KHO kiểm nguồn đơn/quyền/draft/retry/khôngghi sổ, chưa có kết quả native của phần này. UAT39895504031 kiểm8e61a68 cũ, chưa chứa gom theo đơn; chờ đọc kết quả trước lượt tiếp. PR38nháp/production0.16.4 giữ nguyên. Còn thu/hoàn chênh lệch đổi mã trong một cửa, nguồn cọc theo đơn trong bộ giấy và cấu hình quyền nhân sự thật.

## 23/10/2026 — Sửa helper chọn đúng kết quả Chrome; giữ139ca

UAT39893134196 đúngd54522d FAIL tại b014_quality_parts.py đọc dòngJSON đầu tiên: CI_REALTIME_NOT_PROVISIONED/INFO thay vì NATIVE_DESK_GIAM_THEO_PHAN/PASS. Process Chrome đãexit0, assertion UI/giá chưa bị bỏ; không coi toàn lượt đạt. Đã sửa chọn chính xác tên ca, bắt đúng một kết quả và statusPASS; không bỏ INFO bằng cách nhận bất kỳ dòngPASS. Cần chạy lại trên mã sửa. Cổng239893214536 và2b39893218066 cùngd54522d SUCCESS; đã đọc log601+108unit/53mục dựng mới và53mục dựng/nâng/quay lui. Cổng339893222080 đang chạy lúc cập nhật, chưa kết luận mới.

Đã ghi phân công10người, người nhận tiềnNinh/Trang/Ánh và chính sách quyền linh hoạt tháng đầu tại docs/phan-quyen-nhan-su-dung-thu-20261023.md và docs/quyet-dinh-nghiep-vu.md. Tâm để sau theo chủ dự án. Chưa áp quyền production; không hỏi lại quyết định đã chốt. Cần ánh xạ tên đăng nhập và kiểm quyền CEOxem/Trangduyệt/người nhận tiền theo nguồn, không cấp System Manager đại trà. Toàn PR38 vẫn nháp, production0.16.4 không đổi.

## 23/10/2026 — Chuẩn bị dùng thử; sửa phân loại lỗi hạ tầng Chrome

UAT39891158617 đúngfa8ce18 FAIL tại Chrome do assertion gom mọi HTTP lỗi, gồm404/socket.io của CI chạy bench web trực tiếp không có dịch vụ realtime. Trace cho biết blocking=[]: không còn popup quyền che Dialog; chưa coi cả lượt đạt. Đã giới hạn ngoại lệ đúng404 endpoint/socket.io cùngbase của bộ thử và in INFO riêng; mọi lỗi API/asset/runtime khác và modal che vẫn FAIL. Không bỏ ca quyền/giá/hoàn hoặc thay kỳ vọng139. Lượt lỗi giữ nguyên. Chủ dự án cần nhân sự dùng thử ngày24/10 và chuẩn bị phân quyền tối23/10: ưu tiên chốt bản đang dở, chưa trộn bỏ28cờ. Đang xin danh sách nhân sự/phạm vi để chuẩn bị cấu hình; không tự cấp quyền production.

## 23/10/2026 — ĐANG DỞ: chờ UAT bản sửa quyền và popup

Mã nghiệp vụfa8ce18 đã đẩy; UAT39891158617 đang chạy đúngfa8ce18, kỳ vọng139ca bộ014. Lượt5eeaaad/39890844075 đã bị concurrency hủy khi chuyển sang bản sửa popup, không phảiPASS/FAIL nghiệp vụ. Chưa có kết quả mới. Bước tiếp theo: đọc kết quả/artifact mới; nếu lỗi giữ nguyên ca và sửa; nếu xanh vẫn xem ảnh nhan-tra-tung-phan.png không có modal che và PDF4trang, rồi cập nhật bằng chứng đúngSHA. Đã cập nhật đặc tả9nhóm và bảng đối chiếu, không đóng các mục còn thiếu. Cục bộ601ca đạt. Cổng3 trước đó2a3fefc đã đọc schema1154/1154, quay lui1105/1105 lệch0 và phục hồi sau nâng sai khớp chi tiết; không suy cho mã sau. Production0.16.4 và PR38nháp giữ nguyên.

## 23/10/2026 — QA ảnh bắt popup quyền trên màn nhận trả

Đã xem ảnh nhan-tra-tung-phan.png của UAT39888905491: đủ5kg đã giảm/20kg chưa giảm nhưng có popup Insufficient Permission for Sales Invoice Item che màn. Vì vậy Chrome PASS của lượt đó chưa đủ đạt giao diện. Đã đổi truy vấn nút thu cũ sang Sales Invoice cha có quyền chuẩn, lọc đúng phiếu giao/company/customer; tài khoản không có quyền SI chỉ dùng màn thu facade mới, tự chọn phân bổ rõ ràng. Không cấp quyền bảng con. Thêm assertion Chrome không có modal lỗi/HTTP lỗi trước chụp. JS/diff đạt. Cần chạy lại trên mã mới; giữ run lỗi và ảnh làm bằng chứng.

Đã đọc Cổng239888993070 đúng2a3fefc:596unit/53mục không lỗi; Cổng339888909929 SUCCESS đã tải artifact, chưa suy cho mã sau. UAT139 mới chưa hoàn tất, production0.16.4 không đổi.

## 23/10/2026 — Sửa quyền phân loại khoản giảm cũ sau UAT139 thất bại

UAT39888905491 đúng2a3fefc FAIL tại ca tài khoản nhà máy có ROLE_NO_COST cộng Accounts Manager vẫn gọi được classify_quality. Giữ nguyên assertion và lượt lỗi. Đã thêm guard riêng dùng chung preview/classify: hồ sơ hạn chế bị chặn trước đọc nguồn, không cấp hoặc bỏ quyền native. Đã bổ sung hồi quy tài khoản cộng vai trò,601ca cục bộ không bỏ qua đạt. Bản này cũng chứa rà giá thuần3520b3b chưa có native kết quả. Cần chạy lại139ca trên đúng mã sửa; không coi PR38 hoàn tất, không đổi production0.16.4.

## 23/10/2026 — Rà giá thuần, làm tròn và nội dung kế toán nhìn thấy

Đã thêm kiểm giá trả theo đúng độ chính xác native của net_rate, nhưng tiền thuần từng dòng không được lệch khỏi các phần đã chọn quá0,5VND; tổng trần khoản gốc giữ nguyên. Chặn nguồn thuế/chi phí phức hợp chưa hỗ trợ thay vì coi tất cả là một thuế suất. Khi lập trả theo phần, giá là giá thuần: bỏ discount header và cờ giá đã gồm thuế được mapper chép để không trừ/tách hai lần; thuế suất/tài khoản nguồn giữ nguyên. Không đổi precision toàn hệ thống hoặc bỏ kiểm tiền.

Đã ghi tóm tắt mã hàng/kg/tiền giảm/thuế vào nội dung đề nghị mới và Comment khi phân loại cũ, không thêm màn hình/ô nhập. Mở đề nghị nháp cũ có thông báo rõ chưa thay nội dung bằng dữ liệu vừa nhập. Cục bộ600ca không bỏ qua đạt; JS/Pyflakes/diff đạt. Chưa có native kết quả của thay đổi này. UAT39888905491/Cổng339888909929/Cổng239888993070 đang kiểm đúng2a3fefc, chưa chứa bản rà này. Không suy kết quả cũ cho mã sau; PR38 nháp, production0.16.4 không đổi.

## 23/10/2026 — Bổ sung phân loại khoản giảm cũ; chờ native139

Đã viết classify_quality: kế toán có quyền ghi JE chọn dòng/kg/tiền giảm cho JE đã ghi có nguồn SI. Khóa quỹ→SI→JE, giữ modified và retry cùng phân loại; đối chiếu đúng tổng tiền, thuế, tài khoản và cost center trước lưu. Chỉ ghi JSON phân loại và Comment căn cứ; không đổi kỳ/đơn vị/accounts, không tạo khoản giảm/chi mới. allow_on_submit chỉ cho ô metadata; bảo vệ ContextVar theo đúng object, không cho API/form tự sửa/xóa hoặc phân loại lại. Có kiểm tài chính trước/sau, không bật cờ bỏ repost/permission. Phân loại cũ chưa rõ nguồn hoặc đã có trả chưa phân loại vẫn dừng để kế toán đối chiếu, không tự đoán.

Đã nối nút Bổ sung phần hàng đã giảm trên JE và cùng Dialog chọn lượng/tiền. Return facade chỉ đọc phần giá bán đã được duyệt theo DN có quyền nhận trả và phạm vi native của SI/JE, không cấp quyền đọc GL/JE chung cho kế toán bán hàng; thêm ca KTBH lập/ghi trả sau giảm. Handler đăng ký một lần trong phiên Desk, tránh lặp khi qua nhiều DocType. Giữ28cờ, bộ cài tường minh; trước schema mới đọc cũ không truy cột thiếu, thao tác mới phải báo chưa cài.

Cục bộ596ca không bỏ qua đạt; JS/Pyflakes/diff đạt. UAT39885705681 đúng5bff6e6 FAIL được giữ: đã đọc artifact136PASS gồm RESTORE và NATIVE_DESK_GIAM_THEO_PHAN PASS (đúng20kg chưa giảm/5kg đã giảm, không ghi sổ khi kiểm màn). Hai phiên giữ cùng3kg chỉ một nháp được tạo; lượt dừng ở helper rpc đòi message sau xóa nháp thành công. Đã sửa dùng phản hồi native rỗng, vẫn bắt buộc phiếu không còn và lượng nhả đúng. Ảnh mới chưa có trong artifact lượt này do thiếu đường upload, đã thêm cả ảnh thành công/lỗi vào workflow kế tiếp.

Bộ014 kế tiếp139PASS kỳ vọng (thêm retro so với138); chưa có kết quả hoàn/tổng giảm/giảm100% hoặc bổ sung khoản cũ trên mã mới. PR38 nháp, production0.16.4 không đổi. Nền c21a799/UAT39775206078 đã135PASS/PDF4trang; không suy cho phần mới. Còn gom từ đơn, chênh lệch đổi mã và nguồn cọc trong bộ giấy.

## 23/10/2026 — ĐANG NỐI giảm/nhận trả theo phần hàng

Chủ dự án chốt phân biệt phần đã giảm và chưa giảm, đã ghi docs/quyet-dinh-nghiep-vu.md. Đã viết quality_parts.py (số thập phân, lượng riêng theo thỏa thuận, không FIFO/bình quân cả mã); quality_allocation.py nối JSON phân bổ trên JE chuẩn và JSON chi tiết phần trả trên dòng DN chuẩn. Không DocType/sổ/cờ mới. Đường mới chọn dòng, kg và tiền giảm gồm thuế; lưu phân bổ net/thuế theo quy tắc hiện có. Phần đã giảm và chưa giảm còn lượng riêng; nhập trả trộn hai phần giữ chi tiết, chỉ quy đổi đơn giá dòng native trên chính lượng thực trả, không đổi giá phần giữ lại. Giữ tổng trần khoản gốc và cơ chế đối trừ/hoàn chuẩn; hàng đã giảm hết giá trị vẫn nhận kho, không tạo chi0/hoàn lần nữa.

Đã nối Dialog trên Customer/SI và phần chọn hàng trả, khóa sửa phân bổ, kiểm lại lúc ghi JE, chặn hủy nguồn khi có phiếu trả phân loại; nháp được tính giữ lượng. Cục bộ587ca không bỏ qua đạt, JS/Pyflakes/diff đạt. Thêm2HTTP+1Chrome (kỳ vọng138PASS bộ014):20kg giá gốc/5kg giảm, trả trộn,2phiên giữ cùng lượng, giá giả/hủy nguồn, hoàn đúng137.500 sau thu đủ và nhận hàng giảm100% không hoàn nữa. CHƯA có kết quả native mã mới. Khoản giảm lịch sử chưa có phân bổ còn cần cửa bổ sung có đối chiếu, đang làm; không coi luồng cũ đã hỗ trợ trả một phần sau giảm.

Đã tải/đọc artifact UAT39775206078 đúngc21a799 SUCCESS:135PASS bộ014 gồm RESTORE, NATIVE_PDF_BOOT PASS; PDF4trang với2A5 đúng kích thước. Đây là bằng chứng nền trước phần giảm mới, không suy sang mã sau. Cổng2/2b/3 cũ giữ bằng chứng đúngSHA như mục trước. PR38 vẫn nháp, production0.16.4 không đổi. Còn gom từ nhu cầu đơn/thu hoàn đổi mã trong cùng cửa và nguồn cọc trong bộ giấy.

## 22/10/2026 — PDF native đúng4trang; Chốt ngày cửa hàng đã nativePASS

UAT39772096251 đúngfb6ab9c FAIL do bộ kiểm mới: import os/subprocess bên trong chay khiến os trở thành biến cục bộ trước phép đọc PDF (UnboundLocalError), không phải lỗi sản phẩm. Đã bỏ import cục bộ trùng, giữ import module và assertion4trang, kiểm Pyflakes riêng tệp đạt. Cục bộ570ca không bỏ qua vẫn đạt. Cần chạy lại toàn lượt trên mã sửa helper; không lấy kết quả riêng để gọi cả lượtPASS.

Đã tải/đọc artifact: bộ014129PASS gồm RESTORE rồi1FAIL helper; HTTP_2B_FACTORY_DAY_CLOSE và DESK_2B_DAY_CLOSE đãPASS với ca mở rộng tắt cầu nối Nhà máy. Người quản lý vẫn xem sao kê/hàng/nợ, tài khoản hạn chế bị chặn, không ghi sổ. PDF doi-soat-bo-giay.pdf được tạo/lưu trước lỗi helper; đã đọc bằng pypdf và xem đủ4ảnh: A4đối soát +2A5Landscape595×420pt +A4phiếu thu. Mã/ô ký cùng trên mỗiA5, chữ và bảng không cắt, giữ ô ký20mm. Đây là ca một dòng giả, chưa máy in thật hoặc cam kết mọi độ dài hàng/địa chỉ đều một trang.

Cổng239772314861 đúngfb6ab9c SUCCESS, đã đọc log570ca image và53mục cấu hình không lỗi. Cổng2b39771765446 đúng6868cff SUCCESS, đã đọc log dựng/nâng/quay lui đều53mục đạt. Cổng339771761224 đúng6868cff đang bước cố ý làm hỏng/tự khôi phục; chưa lấy kết quả. Câu hỏi tính giá trả một phần sau giảm vẫn chờ chủ dự án, không tự chốt công thức. PR38 nháp; production0.16.4/28cờ giữ nguyên.

Đã đẩy mã sửa helper c21a799; UAT39775206078 đang chạy lại135ca. Lượt mới chưa có kết quả.

Cổng339771761224 đúng6868cff đã SUCCESS; tải/đọc artifact cong-3-bang-chung: schema1151/1151 (bỏ qua6/6 theo phép thử), quay lui1105/1105 lệch0; sau cố ý nâng sai, chi_tiet khớp. Chỉ chứng minh6868cff, không thay UAT mới/cổng trên mã phát hành cuối.

## 22/10/2026 — UAT135 xanh nhưng QA phát hiện phần ký A5 tràn trang

Đã tải/đọc candidate-image-evidence UAT39766960041 đúng98c37e39ad2fb3ee032ea0ac4a40b153c581a258: bộ014135PASS gồm RESTORE; inventory33, funds20, cost16, dispatch48, b0111=15, b0112=13, b0113=13, b0114=8, b012=9, b013=10, native16511=4 đềuPASS. Các ca mới gom kho chuẩn bị/in→xuất→nhận, hồ sơ khách ký riêng, lịch sử ảnh, đối soát bất biến/quyền và ngoại tệ đã nativePASS. Chrome kế toán thật mất phản hồi sau200/bấm lại chỉ một biên bảnPASS. Chưa suy sang thay đổi Chốt ngày sau đó.

QA PDF phát hiện lỗi ngoài assertion cũ: bộ doi-soat-bo-giay.pdf có6trang, mỗi liên A5 bị tách bảng hàng/ô ký. Đã xem trang2/3 xác nhận. Nguồn Frappe16.52.0 prepare_header_footer đặt lại lề trên/dưới15mm khi không có header/footer, đè options6mm; HTML chưa có .print-format để read_options_from_html lấy lại lề. Đã thêm selector chính thức với6/7mm/A5Landscape, giữ chữ9pt và ô ký20mm; thời điểm in bỏ microsecond. Thêm assertion native bộ một dòng phải đúng4trang với2A5 có cả mã/ô ký, không nới để chấp nhận6trang. Chưa có kết quả native của bản sửa PDF. Lượt39766960041 vẫn xanh nghiệp vụ nhưng KHÔNG coi bố cục mẫu in đạt.

PR38 vẫn nháp, production0.16.4 giữ nguyên. Cần chạy lại UAT trên mã sửa, xem đủ PDF và ảnh; các phần còn thiếu trong bảng đối chiếu tiếp tục mở.

Đã đồng bộ docs/doi-chieu-kho-giao-nhan-20261021.md với bằng chứng135 và giới hạn QA; giữ riêng phần chưa làm. Câu hỏi tính tiền trả một phần sau giảm giá đang chờ chủ dự án chọn bình quân theo mã hay phân biệt phần đã giảm/chưa giảm; chưa tự áp công thức mới. UAT sửaPDF39772096251 đúngfb6ab9c đang chạy; UAT39771756550 đúng6868cff bị lượt mới thay thế/hủy, không tínhPASS.

## 22/10/2026 — Tách Chốt ngày cửa hàng khỏi cầu nối Nhà máy

Chốt ngày dùng cờ chốt ca + bàn giao + người giữ tiền hiện có; giữ C.guard(manager=True), quyền Company và quyền nguồn, không cần bật quỹ/cầu nối Nhà máy. Mục chuyển tiếp nhà máy chỉ đọc khi cờ đó bật. Bộ cài schema chốt ca nạp báo cáo; lối tắt Thu chi và công nợ dùng các cờ cửa hàng. Không thêm cờ, quyền hoặc sổ. Cục bộ570ca không bỏ qua đạt; thêm2ca đơn vị và mở rộng ca native hiện có: tắt cầu nối nhà máy vẫn xem sao kê/Chốt ngày, nhân sự hạn chế vẫn bị chặn. Chưa có kết quả native của thay đổi này.

Đã tải/đọc artifact cong-3-bang-chung của Cổng339764128191 đúng9a99835ab74dea33a05e7bdf35be09933a279fcf SUCCESS: quay lui schema1105/1105 lệch0; bước cố tình nâng cấu hìnhZZ sai rồi tự khôi phục có chi_tiet khớp, GL/PLE/SLE không lệch. Đây là diễn tập CI dữ liệu giả, không bản sao production thật và không chứng minh mã sau9a99835. UAT39766960041 đúng98c37e3 đang chạy nghiệp vụ135ca, chưa chứa thay đổi Chốt ngày này. PR38 nháp; production0.16.4/28cờ giữ nguyên. Còn phân bổ giảm theo dòng/lượng, nối gom kho từ đơn, cửa sổ đổi mã và nguồn cọc trong bộ giấy; không tuyên bố toàn phạm vi hoàn tất.

## 22/10/2026 — PDF native tạo được; sửa ca kiểm tệp403HTML

Đã đọc artifact UAT39763635543 đúng3c9f34c: NATIVE_PDF_BOOT PASS, bộ đối soát được tạo/tải và lưu doi-soat-bo-giay.pdf; đã đọc3trang/PDF và xem trang biên bản native, bảng/ô ký không bị cắt. Bản này gồm biên bảnA4 + phiếu xuất chuẩnA4 + phiếu thuA4 vì fixture dùng payload thế hệ cũ. Chưa coi nhánh ghép A5 mới đã kiểm.

Lượt FAIL vẫn giữ: ca chặn tải tệp gặp đúng403HTML của /private/files, nhưng helper denied dành RPC lại đòi JSON.exc_type. Đã tách helper riêng chỉ chấp nhận HTTP403 và không nhận PDF; không thay quyền/tệp hay nới assert RPC. Positive control kế toán tải PDF vẫn giữ. Đổi fixture đơn mới sang customer_signatureKhông để mang dấu mẫu giao nhận1 và buộc chạy nhánh ghép hai bản A5. Mốc in đối soát bỏ microsecond kỹ thuật, giữ số lưu gốc bất biến; tái sinh8JSON mốc10:20. Cần chạy lại135 đúng mã kế tiếp; giấy tay vẫn có nativePASS, hồ sơ khách ký/gom kho và các guard mới chưa có kết luận đầy đủ. PR38 nháp, production0.16.4 không đổi.

## 22/10/2026 — Giới hạn bộ giấy theo quyền nguồn và giữ Administrator dùng được

Rà lại quyền snapshot: bộ PDF có phiếu nguồn, nên chỉ kiểm Company/Customer là chưa đủ cho tài khoản còn User Permission trên kho/hàng/link của nguồn. Đã mở rộng guard dựa Link và Table metadata của DN/SI/PE/JE cùng dimension kế toán; các giới hạn ngoài Company/Customer chặn đồng thời tạo/đọc/danh sách/PDF. Không vô tình chặn quyền Employee không liên quan nguồn. Người đủ phạm vi Company/Customer vẫn dùng như cũ. Thêm negative control scope_wh cho cả dữ liệu payload và tệp; giữ positive control CompanyAPH.

Đã khớp chính sách giá của app: Administrator được dùng dù Frappe liệt kê cả vai trò hạn chế; nhân viên NoCost vẫn bị chặn kể cả kiêm quản lý, hồ sơ nhà máy bị hạn chế giá không được vào đối soát. Sửa nút hiển thị tương ứng, thêm kiểm Administrator đọc bản đã cấp. Cục bộ568ca không bỏ qua đạt; JS/diff đạt. Các mở rộng ca hiện có không đổi kỳ vọng135PASS, chưa có native kết quả của guard mới. UAT39763635543 mã3c9f34c còn đang kiểm134, Cổng339764128191 mã9a99835 đang chạy. PR38 nháp, production0.16.4 giữ nguyên.

Đã viết docs/huong-dan-kho-giao-nhan-gon.md: nhân sự, khách/xe khách lấy, ship, khách ký cuối, kho vệ tinh, gom kho, giấy tay và lưu giấy/đối soát; ghi rõ đây là ứng viên và phần chưa hoàn thiện. Không gọi giấy tay là workflow offline hoặc coi bản hướng dẫn là nativePASS. Còn phân bổ giảm theo dòng/lượng, trả một phần sau giảm và nối nhu cầu gom kho từ đơn.

## 22/10/2026 — Tách việc thiếu ảnh/gốc và quy đổi tiền chưa phân bổ

Chốt ngày giữ riêng việc thiếu ảnh và thiếu giấy gốc của bản khách ký tại đích và biên bản đối soát. Nhận gốc trước ảnh vẫn lưu được và không giữ khách lại; việc thiếu ảnh còn hiện đến khi bổ sung. Nguồn là DN/biên bản hiện có, không tạo bảng việc hoặc ghi sổ. Biên bản dùng get_list và quyền/phạm vi native, chỉ trả nguồn trong Company đang xem.

Đã đối chiếu nguồn Payment Entry16.51.1: unallocated_amount tính theo tiền tài khoản khách, Receive quy đổi source_exchange_rate, Pay dùng target_exchange_rate. Snapshot hiện quy đổi về VND trước cộng, không đổi tỷ giá hoặc sửa PE/PLE. Thêm2ca đơn vị và HTTP_014_DOI_SOAT_TIEN_CHUA_PHAN_BO_NGOAI_TE với khách/tài khoảnUSD giả,10USD×25.000=250.000VND, không đổi sổ lúc chụp. Cục bộ566ca không bỏ qua đạt; bộ014 kỳ vọng135PASS. Native135 chưa chạy; UAT39763635543 mã3c9f34c vẫn đang kiểm134ca trước các mở rộng này. Cổng339764128191 mã9a99835 đang chạy. PR38 nháp, production0.16.4 và28cờ giữ nguyên. Còn phân bổ giảm/trả theo dòng và nối nhu cầu gom kho từ đơn; không tự coi các phần chưa kiểm đã đạt.

## 22/10/2026 — Giữ đúng chuyến, cho sửa người chở khi còn chuẩn bị

Đã bổ sung guard phiếu chuyển có mã lượt: không đổi Company, purpose, stock_entry_type, cờ qua Transit hoặc phiếu chuyển gốc; không xóa kho nhận dự kiến của bản chuẩn bị. Người/xe và ghi chú được sửa trên nháp chuẩn bị, sau xuất bất biến; lượng thực tế vẫn sửa/ghi trên phiếu native. Không thêm cờ/quyền hoặc sổ. Thêm ca đơn vị và mở rộng ca HTTP chuẩn bị chuyển (đổi xe trước xuất, chặn tráo Company). Cục bộ563ca không bỏ qua đạt, chưa có native kết quả của guard mới. UAT39763635543 đúng3c9f34c đang chạy134ca, chưa bao gồm guard này; giữ các lượtFAIL và giấy tay nativePASS đã đọc ở các mục trước. PR38 nháp, production0.16.4 không đổi.

## 22/10/2026 — Chỉnh bố cục đối soát và thư mục phép thử PDF CI

UAT39714397708 đúngb3b4507 FAIL sớm tại NATIVE_PDF_BOOT: phép thử Python khởi tạo từ thư mục bench thay vì sites nên logger tìm /home/frappe/logs/database.log. Đã đọc log lỗi119612952998; sửa đúng cwd sang /home/frappe/frappe-bench/sites như các helper native khác. Chưa chạy các ca134 trong lượt này; không coi cấu hình host/PDF hoặc hồ sơ khách ký đã được xác nhận.

Đã dựng/xem PDF Chrome với dữ liệu giả đủ4đơn vị: bản đầu bị tràn bảng và phần ký sang trang riêng. Đã cố định cột, giữ tên pháp nhân đầy đủ tại bảng đầu, lưu tên viết tắt từng Company trong snapshot cho bảng chi tiết, giảm khoảng trắng lặp và giữ mã/khách/mốc cùng khối ký. Bản sửa4đơn vị/5phát sinh/4dòng tiền giữ vừa1A4; đã xem ảnh và kiểm baseline tên người lập nằm trong lề. Đây là QA Chrome cục bộ, chưa thay bằng chứng PDF native/máy in thật. Tái sinh8JSON mốc22/10 10:10;561ca cục bộ không bỏ qua đạt. PR38 nháp, production0.16.4 không đổi. Cần chạy lại UAT134 trên mã mới, đọc lỗi/ảnh/PDF, tiếp tục các phần còn dở trong bảng đối chiếu.

## 22/10/2026 — Giấy tay native đạt; đang sửa PDF và kiểm hồ sơ khách ký riêng

UAT39711917331 đúngedb3c67 FAIL tại lần tạo PDF đối soát đầu tiên (OSError), không phải ca giấy. Đã tải/đọc artifact /tmp/uat-kho-39711917331: HTTP_014_GIAY_TAY_NHAP_BO_SUNG PASS đủ nháp không ghi sổ, khóa trùng, tệp riêng, thời điểm thực tế, hủy/amend kế thừa và gắn giấy vào DN/PE đã ghi không ghi lại sổ. Bộ014 có129PASS kể cả restore, các bộ hồi quy khác cùng lượt không cóFAIL. Chưa coi snapshot/PDF đạt. Host trình duyệt UAT là aphvh-web-uat, chưa có DNS/port phục vụ PDF trong container; đã cấu hình host_name riêng CI thành http://aphvh-p0-web-uat:8000, thêm phép thử PDF native ngay bước chuẩn bị và giữ traceback HTTP để xác định nếu còn lỗi. Chưa có lượt xác nhận sửa PDF.

Đã viết hồ sơ khách ký tại đích trên DN, độc lập bản giao nhà xe; chỉ hiện/cho nhập khi phiếu mới gửi vận chuyển và yêu cầuCó. Giấy gốc trước ảnh được, giữ người/thời điểm/vị trí; nhận hồ sơ khi đang giao dùng chính dấu Khách đã nhận hiện có trong cùng transaction, không ghi kho/nợ/tiền thêm. Người nhập kiểm và lưu cùng thao tác, không cấp duyệt mới. Bản khách ký vào lịch sử/tệp riêng tư và Chốt ngày, không thêm màn hình chính/cờ. Thêm ca native HTTP_014_KHACH_KY_TAI_DICH, bộ014 kỳ vọng134PASS; chưa có kết quả native của phần này hoặc phần chuẩn bị chuyển kho/lịch sử sau1725d3b.

Bổ sung giữ đúng các link đơn/hóa đơn mà mapper trả hàng16.51.1 chép, chặn tráo nguồn; không áp si_detail vì native mapper không chép trường no_copy đó. Mẫu chuyển kho escape tên xe/ghi chú/kho cuối, kiểm ô thực giao trống khi nháp và tái sinh8JSON mốc09:10. Cục bộ561ca không bỏ qua đạt; JS/Python/diff đạt. PR38 nháp, production/tag0.16.4 và28cờ giữ nguyên. Còn phân bổ giảm theo dòng/lượng, trả một phần sau giảm và nối nhu cầu gom kho trực tiếp từ đơn; không tuyên bố hoàn tất toàn phạm vi.

## 22/10/2026 — Giữ phiên bản ảnh ký cũ và dấu đối chiếu trước khi thay

Hồ sơ DN có lịch sử JSON do server ghi trên chính phiếu, không sổ nhiệm vụ/DocType mới. Mỗi lần chọn/gỡ/thay tệp, ghi chú, đối chiếu hoặc nhận gốc giữ trước/sau, user/time; tệp cũ vẫn riêng tư và không bị xóa/công khai/đổi nguồn, kể cả phiếu hủy. Chặn sửa lịch sử bằng form/API và xóa phiếu đã có bằng chứng/gốc. Mục Hồ sơ giao nhận có Lịch sử bản ký để mở các tệp cũ; thay ảnh vẫn bỏ dấu đối chiếu hiện tại để kiểm lại. Đã nối các ô giấy gốc vào đúng cụm hồ sơ.

Cục bộ552ca không bỏ qua đạt, JS/cú pháp/diff đạt. Mở rộng ca HTTP_014_HO_SO_BAN_KY kiểm thay tệp/giữ blob cũ/chặn xóa và giả lịch sử, không tăng số ca: bộ014 vẫn133PASS kỳ vọng cùng phần chuẩn bị chuyển kho. Chưa có bằng chứng native của lịch sử mới. UAT39711917331 mãedb3c67 đang chạy, không chứa chuyển kho/lịch sử sau đó. PR38 vẫn nháp, production0.16.4/28cờ không đổi. Bằng chứng khách cuối riêng và giảm/trả theo dòng vẫn cần hoàn thiện; không tuyên bố cả phạm vi xong.

## 22/10/2026 — Chuẩn bị và in phiếu chuyển kho trước khi thực giao

Đã thêm lựa chọn chuẩn bị nháp vào dịch vụ Stock Entry chuyển kho hiện có. Màn Chuyển hàng đi mặc định Chuẩn bị phiếu & In: kho nhận cuối dự kiến, người/xe chở, phiếu nháp không ghi kho/GL/nợ. Bấm lại cùng lượt mở phiếu cũ, cả sau khi phiếu đã ghi, không tự xác nhận nháp. Người dùng kiểm lượng thực giao trên phiếu chuẩn rồi xác nhận; nhận về kho vẫn dùng Stock Entry nhận từ Transit, có thể nhận từng phần. Kho dự kiến được điền sẵn, đổi kho thực nhận cần lý do. Không chuyển khác Company, không lấy Transit làm kho nguồn. Cho bỏ bản chuẩn bị chưa ghi bằng xóa native; phiếu đã ghi/hủy giữ lịch sử như cũ.

Chuyển/nhận dùng cờ kho vận hành hoặc nhận nhà máy, giữ28cờ; cửa hàng không cần bật màn Nhà máy để dùng. Mẫu phiếu kho nháp đặt lượng ở cột yêu cầu, để trống thực xuất/nhập, hiện kho nhận cuối và người chở. Đã tái sinh8JSON với mốc22/10 09:00. Cục bộ550ca không bỏ qua đạt; thêm HTTP_014_CHUAN_BI_GOM_KHO, bộ014 kỳ vọng133PASS. Chưa có bằng chứng native của mở rộng này. UAT39711917331 đang kiểm riêng mãedb3c67 với132ca, chưa bao gồm chuyển kho mới. PR38 nháp, production/tag0.16.4 giữ nguyên; các phần giảm/trả theo dòng và bằng chứng khách cuối vẫn đang dở.

## 22/10/2026 — Sửa dữ liệu kiểm sửa đổi giấy tay, giữ nguyên chặn đổi nguồn

UAT39708719665 đúng7efd4b1 dừng ở ca sửa đổi giấy tay: kịch bản gửi lại số giấy/vị trí cũ sau khi giấy gốc đã chuyển về cửa hàng. Guard từ chối đúng việc đổi nguồn. Đã sửa fixture để mô phỏng các ô no_copy trống của thao tác Sửa đổi native, kế thừa đúng số và vị trí hiện tại; thêm ca đơn vị kiểm kế thừa. Không nới kiểm của sản phẩm. Cục bộ546ca đạt, không bỏ qua. Cổng239708673680 và Cổng339708723517 đúng7efd4b1 SUCCESS; chưa suy cho mã sửa kiểm kế tiếp. Cần chạy lại UAT132; snapshot/PDF mới chưa có bằng chứng native. PR38 nháp, production0.16.4 không đổi.

## 22/10/2026 — ĐANG KIỂM bản đối soát theo lượt và bộ PDF đã cấp

Đã viết entity bằng chứng `Bien ban doi soat no` (Biên bản đối soát theo lượt), không thêm màn hình chính hay sổ tài chính. Từ DN/PE/Khách chọn chứng từ đã ghi: chụp nợ theo Company, tăng/giảm của lượt và khoản khác tại cùng mốc; tách phải thu/dư có, cọc và tiền chưa phân bổ, không tự cấn chéo. Bản Customer theo ngày cũ cũng đã giới hạn Company/Customer/vai trò và ghi rõ phạm vi. Snapshot dùng cờ quản trị hiện có, yêu cầu cơ chế khóa sổ tiền đang bật để chụp đồng thời; cả hai đã có trong28cờ, không cờ mới.

Bộ PDF gồm biên bản và giấy nguồn DN/PE/SI cần thiết (không đưa toàn JE nội bộ cho khách), giữ A5 của phiếu nhanh. Lưu riêng tư vào hồ sơ để in lại giữ đúng byte; số đã chụp và nguồn bất biến, bản bổ sung nối bản trước. Kiểm vai trò tài chính, NoCost, Company/Customer, phạm vi dimension, quyền đọc/in nguồn và current-read sau khóa sổ. File và lịch sử ký được bảo vệ; quyền lấy hàng không thay quyền ký nợ. Giấy gốc có người/thời điểm/vị trí riêng, ảnh có thể bổ sung sau. API/form không tự tạo hoặc ghi DN/SI/PE/JE/GL/SLE.

Cục bộ545ca kh_aph đạt **không bỏ qua**, chạy với Jinja2 ở /tmp/kiem-mau-a5-goi;15ca mẫu in và kiểm ranh giới mặc định in đạt. Kiểm cú pháp JS/Python đạt. Thêm2ca HTTP và1ca Chrome bằng đúng kế toán bán hàng (phiên CSRF riêng), gồm mất phản hồi sau200/retry, phạm vi một/nhiều Company, privatePDF, chụp ròng0, giấy gốc/ảnh riêng, giữ PDF sau hủy thu và bản bổ sung. Bộ014 kỳ vọng132PASS. CHƯA có kết quả native của phần snapshot/PDF mới; chưa kiểm bố cục PDF native hoặc máy in thật.

UAT39703447598 đúngc4b93fa FAIL được giữ: HTTP_014_MO_PHIEU_HOAN và NATIVE_DESK_KHO_GIAO_NHAN_GON PASS, đã xem ảnh mở đúng PE192.500. Ca giấy tay đã qua lưu/khóa trùng/tệp riêng tư/ghi kho/cập nhật nơi giữ, rồi kịch bản dùng modified cũ sau lưu nên TimestampMismatchError trước guard thời điểm. Đã sửa lấy lại kết quả lưu, giữ assertion ValidationError, không nới chặn. Đã nối insert_after toàn bộ ô giấy tay vào đúng section thu gọn (ảnh trước cho thấy checkbox bị đặt lên đầu PE). Lượt giấy128 trước39702265051 bị concurrency hủy khi chạy lượt129 mới, không coi đạt.

PR38 vẫn nháp, production/version/tag giữ0.16.4. Cần chạy UAT132 đúng mã mới, đọc PDF/ảnh/log; tiếp tục phần gom kho vệ tinh, giảm theo dòng/lượng và trả một phần sau giảm, tách bằng chứng khách cuối/lịch sử ảnh kho đầy đủ. Nghiệm thu người/hàng/tồn/máy in thật vẫn để cuối.

## 22/10/2026 — Mở phiếu hoàn đã có ngay từ phiếu nhận trả

Bổ sung nút Mở phiếu hoàn tiền, tải lại phiếu nhận trả sau ghi để thấy liên kết nháp do hook chuẩn bị. API chỉ đọc DN/PE, kiểm quyền cả hai, cùng Company/khách, loại chi và chưa hủy; không lập/ghi tiền thêm. Chặn mọi lối form/API tự gán, xóa hoặc tráo ô chứng từ xử lý; các hook chuẩn bị nháp giữ đường ghi nội bộ hiện có. Sửa mô tả xử lý đổi hàng để đúng đơn hàng thay mã mới.

Cục bộ529ca (14 bỏ qua) đạt, gồm kiểm quyền/nguồn/ô liên kết. Bộ014 kỳ vọng129PASS: thêm ca mở phiếu đã có/chặn tráo nguồn và mở bằng Chrome thật, giữ ảnh kho-phieu-hoan.png; CHƯA có kết quả native của phần mới. Lượt39702265051 mãe91d55d đang kiểm riêng giấy tay với128PASS kỳ vọng, không bao gồm nút hoàn và guard mới. Đặc tả bước kế tiếp snapshot nợ/bộ giấy theo lượt tại docs/dac-ta-doi-soat-theo-luot-20261022.md, chưa triển khai entity/API/PDF mới.

Production0.16.4,28cờ và version/tag giữ nguyên; PR38 nháp. Bước tiếp đọc các lượt UAT đúng mã, sửa lỗi thật, tiếp tục snapshot/bộ giấy, gom kho và giảm theo dòng/lượng. Không coi127PASS củab574457 là bằng chứng cho các mở rộng sau đó.

## 22/10/2026 — Thu gọn giấy tay thành thông tin lưu trên phiếu nhập bổ sung

Chủ dự án làm rõ giấy viết tay chỉ lưu để nhập bổ sung khi mất mạng. Đã thu hẹp thiết kế: không hồ sơ/sổ/đồng bộ offline riêng. Trên phiếu xuất (DN), phiếu kho (SE), phiếu thu chi (PE) thêm phần thu gọn: số giấy theo điểm/quyển/tờ, thời điểm giao/thu thực tế, nơi giữ gốc và ảnh/PDF riêng tư tùy chọn. Nhập và ghi sổ native như thường, không bỏ kiểm tồn/giá/hạn mức/kỳ khóa hoặc tự đổi ngày hạch toán.

Nguồn mới `paper_archive.py`: khóa duy nhất giấy theo Company/loại phiếu (cả nháp), giữ định danh sau ghi sổ, hủy giữ giấy và dùng Sửa đổi để nhập lại đúng lịch sử. Nháp sửa được trước ghi. Lưu ảnh sau và chuyển nơi giữ gốc không ghi kho/tiền/nợ lần hai; tệp đang là giấy nguồn không bị xóa/đổi thành công khai hoặc chuyển sang phiếu khác. Tái dùng cờ kho vận hành/người giữ tiền hiện có, schema qua bộ cài rõ ràng, vẫn28cờ; không DocType mới, không tự duyệt/giao/thu.

Cục bộ525ca kh_aph (14 bỏ qua) đạt, có9ca ranh giới giấy mới. Bộ014 bổ sung HTTP_014_GIAY_TAY_NHAP_BO_SUNG, kỳ vọng128PASS: còn phải chạy native trên đúng mã mới, chưa tuyên bố đạt phần giấy tay. Bản b574457 trước mở rộng giấy đã đủ bốn cổng: UAT39631103596, Cổng239631068245, Cổng2b39632778370, Cổng339632783717 SUCCESS. Đã đọc Cổng3: schema1115/1115, rollback1105/1105 lệch0, dữ liệu và nhánh lỗi chủ động KHỚP; không suy kết quả này cho code giấy mới.

PR38 vẫn nháp, production0.16.4 giữ nguyên, chưa tăng version/tag/triển khai. Tiếp theo đọc UAT128 đúng mã giấy mới, sửa lỗi thật rồi nối các phần còn thiếu: snapshot nợ/bộ giấy theo lượt, gom kho, giảm theo dòng/lượng và thao tác hoàn/chênh lệch gọn. Nghiệm thu người/hàng/máy in thật vẫn để cuối.

## 21/10/2026 — UAT kho/giao nhận đạt trên b574457; toàn phạm vi vẫn đang phát triển

Đúng mã `b57445753daf9513a8448d24e92d926d1a9a4d9c`: [UAT39631103596](https://github.com/tienduongmarcom/aphvh/actions/runs/39631103596) SUCCESS. Đã tải và đọc artifact `candidate-image-evidence` id12360337173, đủ127PASS bộ014 và HTTP_UAT_RESTORE (khôi phục số bản ghi/series); các bộ kho/quỹ/giá vốn/giao hàng/hồi quy cũ của cùng lượt cũng đạt. Đã xem ảnh Chrome `kho-nha-xe-moi.png` và `kho-nhan-tra-kg.png`.

Bằng chứng mới gồm: nhận5kg từ bao25kg vào cách ly, bao vật lý0; chưa thu thì không hoàn; thu một phần hoàn96.250 và thu đủ hoàn192.500, đối trừ/thực chi đúng khoản; đổi mã bằng đơn native; xe khách chỉ định; nhà xe nhập mới, báo nhận chỉ ghi dấu; nhận giấy gốc độc lập ảnh và cập nhật danh sách/Chốt ngày. Trả sau giảm chất lượng đã đạt trường hợp khoản một dòng, nhận đủ25kg theo giá trị còn lại đã đối chiếu, chặn giá gốc và đề nghị giảm nháp quá hạn số dư. Trả một phần sau giảm hoặc phân bổ nhiều dòng chưa hỗ trợ tự động, vẫn chặn để kế toán đối chiếu; không tuyên bố đã bao phủ.

Lỗi Chrome nhận hàng nhà máy ở lượt0cf đã hết trong lượt mới: yêu cầu tìm biến thể báo cáo số lượng trảrỗng, giữ các lối Report/query/giá vốn bị chặn. Cổng2 [39631068245](https://github.com/tienduongmarcom/aphvh/actions/runs/39631068245) cùng mã SUCCESS. Cổng2b39632778370 và Cổng339632783717 đang chạy cùng mã, chưa có kết luận. Cục bộ516ca (14 bỏ qua),108ca lõi đã đạt. Các lượt FAIL trước giữ nguyên làm bằng chứng.

**ĐANG DỞ:** nhập giấy dự phòng khi mất mạng, snapshot đối soát nợ/bộ giấy theo lượt, chuẩn bị và gom kho vệ tinh, giảm theo dòng/lượng và trả một phần sau giảm, thao tác hoàn/chênh lệch gọn, bằng chứng khách cuối riêng khi yêu cầu và lịch sử phiên bản đầy đủ. Xem bảng9nhóm `docs/doi-chieu-kho-giao-nhan-20261021.md`. PR38 vẫn nháp; version/tag/production0.16.4 và28cờ không đổi. Nghiệm thu dữ liệu/nhân sự/máy in thật tiếp tục để cuối theo quyết định đã chốt.

## 21/10/2026 — Sửa yêu cầu phụ của báo cáo số lượng cho hồ sơ ẩn vốn

UAT39625443467 đúng0cfbcdb FAIL trong ca Chrome nhận hàng nhà máy cũ, trước khi chạy các ca mới ở cuối. Đã đọc log đầy đủ: Query Report của Frappe16.52 tự gọi reportview.get_list với Report/reference_report=Ton kho so luong, report_type=Custom Report để tìm biến thể. Chính sách ẩn vốn chặn yêu cầu này và bật Message che thao tác. Không coi là ca mới đạt hoặc bỏ kiểm Chrome.

Đã thêm facade rất hẹp: chỉ đúng yêu cầu tìm biến thể của báo cáo số lượng với hai trường name/report_name, ba bộ lọc xác định, sắp xếp và limit0 mới nhận danh sách rỗng. Không đọc DB/Report/query, không mở quyền báo cáo giá vốn hoặc xuất dữ liệu. before_request chỉ bỏ chặn cho đúng đường API này; yêu cầu khác/fieldquery/wildcard/or_filters/ignore_permissions vẫn bị chặn. Danh sách phiếu nhà máy vốn được phép và người không bị hạn chế vẫn gọi native, giữ quyền if_owner và phạm vi chuẩn.

Đã đọc nguồn query_report.js/db.js/handler.py đúng16.52.0. Cục bộ516ca (14 ca bỏ qua) đạt, gồm6ca ranh giới mới. Bổ sung ca HTTP kiểm rỗng/không đọcSQL/không mở báo cáo vốn và giữ danh sách phiếu được phép; bộ014 kỳ vọng127PASS. Cần chạy native đúng mã mới, chưa tuyên bố khắc phục hoàn toàn ca trình duyệt. Không nâng production hoặc đổi phiên bản; PR38 vẫn nháp.


## 21/10/2026 — Giới hạn xử lý khoản đã giảm và cấu hình kiểm Chốt ngày

Kiểm giá trị trả sau giảm hiện chỉ tự đối chiếu trường hợp trả toàn bộ lượng gốc của khoản một dòng. Trả một phần sau giảm, nhiều dòng hoặc đã có trả từng phần phải dừng để kế toán phân bổ đúng khoản giảm cho lượng thực trả; chưa có metadata/thao tác gọn để tự quyết định phần nào đã được giảm. Không coi giới hạn tổng hóa đơn là đủ chứng minh đúng giá của từng phần hàng. Đã thêm kiểm ranh giới này; cục bộ510ca (14 ca bỏ qua) đạt.

Các ca mới được đặt sau toàn bộ ca cũ để tránh ảnh hưởng chuẩn số liệu cũ. Bảng Chốt ngày hiện phụ thuộc cờ factory_handover; ca giấy gốc bật/tắt bằng helper CI có kiểm site và chạy đúng schema, không bỏ guard của sản phẩm. Phụ thuộc tên cờ này cần lưu ý khi tiếp tục tách Nhà máy; chưa thay mô hình cờ production. Bộ014 vẫn126PASS kỳ vọng. Cần chạy UAT đúng mã tiếp theo; các lượt FAIL trước giữ nguyên, chưa chứng minh Chrome/giấy gốc/ca trả sau giảm đã đạt.

Production0.16.4 giữ nguyên, PR38 vẫn nháp. Bước tiếp đọc log/ảnh lỗi mới và sửa nguyên nhân, giữ đúng bằng chứng theo SHA; không gắn tag hoặc coi toàn phạm vi hoàn tất.


## 21/10/2026 — Đang kiểm chặn giảm trùng và giữ nguồn điều chỉnh

Đã thêm kiểm giá trị trả mới so với khoản gốc trừ các SI giảm và JE giảm chất lượng đã ghi. Giá thuần trả không vượt đúng dòng giao gốc, kể cả một mã có nhiều mức giá. Giữ mã/hash nhận trả bất biến; JE đề nghị giảm giữ khoản gốc qua sửa/amend và kiểm lại số còn nợ lúc xác nhận. Cùng thứ tự khóa quỹ → khoản gốc. Không tự tăng tiền hoàn vì nợ đã giảm do chất lượng. Với khoản đã giảm có nhiều dòng, hiện dừng để kế toán đối chiếu phân bổ; chưa giả đã hỗ trợ giảm/trả theo dòng đầy đủ.

Đã thêm ca HTTP đơn cũ giảm100.000, khách chưa trả tiền rồi trả cả25kg: yêu cầu chặn giá trị trả ban đầu, giữ nguyên kho/nợ khi lỗi; sau kế toán đối chiếu giá còn lại mới nhận đủ25kg, không hoàn khống; đề nghị giảm thêm còn nháp phải bị chặn nếu nguồn đã hết nợ. **Chưa có kết quả native của ca mới.** Cục bộ509ca (14 ca bỏ qua) đạt; kiểm cú pháp JS/Python đạt. Bộ014 kỳ vọng126PASS, giữ toàn bộ117ca cũ và chuyển các ca mới về cuối để dữ liệu mới không ảnh hưởng chuẩn so sánh cũ.

UAT39581676952 đúng3b0219f FAIL ở helper Chrome sau khi nhập nhà xe. Đã xem ảnh: nhập tên/SĐT nhà xe mới thành công. Chưa có stderr chi tiết do check=True của subprocess che mất. Đã thêm stderr/ảnh lỗi; bộ đếm chỉ kiểm ô dữ liệu, bỏ Section/Column/Tab/HTML do Frappe16.52 tự thêm (đã đọc nguồn). Chưa khẳng định đây là lỗi duy nhất của lượt đó, cần chạy lại. Chuyển kiểm Chrome sau các ca nhận cuối/giấy gốc độc lập; vẫn bắt buộc đạt và không bỏ assertion nghiệp vụ.

Cổng3 [39578848510](https://github.com/tienduongmarcom/aphvh/actions/runs/39578848510) mã320558a success, đã đọc artifact: schema1115/1115, rollback1105/1105 lệch0, so sổ và nhánh hỏng chủ động KHỚP. Đây chưa phải chứng minh code chặn giảm trùng mới. Bảng9nhóm và phần còn thiếu: `docs/doi-chieu-kho-giao-nhan-20261021.md`. PR38 vẫn nháp, chưa tăng version/tag/triển khai; production0.16.4/28cờ không đổi.


## 21/10/2026 — Trả lẻ, hoàn tiền và đổi mã đã có bằng chứng native; đang sửa tên nhà xe

UAT [39578838909](https://github.com/tienduongmarcom/aphvh/actions/runs/39578838909), đúng mã `320558a42f1a4b8a9dd9297fb440d6a1e7ef04fc`, vẫn FAIL và được giữ nguyên. Đã đọc artifact: các ca trả 5kg/bao vật lý0, chưa thu không hoàn, thu một phần hoàn96.250 và thu đủ hoàn192.500, đối trừ đúng nguồn, đổi mã mới, chặn đơn thay trùng, hủy/lập lại và xe khách chỉ định đều PASS. Đây là dữ liệu giả của CI, không phải nghiệm thu nhân sự/hàng thật.

Lỗi tiếp theo nằm ở tên nhà xe thử chứa `<UAT>`. Đối chiếu đúng nguồn Frappe16.52.0: `_sanitize_content` lọc nội dung giống HTML khi lưu Data, gây khác tên đầu vào và snapshot. Đã chặn dấu ngoặc nhọn trước khi tạo phiếu ở payload thế hệ mới, để không âm thầm đổi tên/hash; giữ hash payload cũ. Ca HTTP mới bắt buộc từ chối tên chứa thẻ, đồng thời kiểm tên hợp lệ chứa `&` được giữ nguyên và escape khi in. Không bỏ kiểm trạng thái hoặc kiểm tên; tách assertion để lần sau thấy giá trị thực nếu lỗi.

Cục bộ500ca kh_aph (14 ca bỏ qua) và108ca lõi đạt. Có thêm4ca ranh giới hoàn tiền: đúng hóa đơn giữ số dư có, thiếu quyền đối trừ không chuẩn bị chi, còn nợ không tạo chi, ngoại tệ không bị hoàn như VND. Cổng2/2b mã320558a đã success; Cổng3 còn đang chạy. Phải chạy lại UAT125ca và các cổng đúng mã sửa tên mới, chưa coi toàn bộ đã đạt.

PR38 vẫn nháp, production0.16.4/28cờ không đổi. Chưa tăng phiên bản, gắn tag hay triển khai. Còn offline, snapshot đối soát/bộ giấy theo lượt, chuẩn bị và gom kho, giảm theo dòng/kiểm trả sau giảm trước, chọn kho nhận trả gọn, bằng chứng khách cuối riêng và lịch sử bản in/bằng chứng đầy đủ. Các phần này chưa được coi là hoàn tất từ những ca PASS ở trên.


## 21/10/2026 — UAT đã chứng minh trả5kg; sửa nhánh hóa đơn giảm giữ số dư riêng

UAT39575256295 đúng771b365 FAIL được giữ nguyên. Artifact chứng minh HTTP_014_TRA_LE_5KG PASS (kho cách ly5kg, sổbao0, nháp không ghi sổ, retry/reserve và giảm một lần), HTTP_014_TRA_LE_CHUA_THU_KHONG_HOAN PASS. Lỗi thật ở thu một phần: ERPNext16.51.1 tự chuyển update_outstanding_for_self=1 khi giá trị trả vượt phần còn nợ, nên giả định mọi hóa đơn giảm trừ thẳng vào gốc là sai. Không bỏ hoặc hạ assertion.

Đã đối chiếu nguồn native theo đúng tag16.51.1 và sửa: với hóa đơn giảm giữ số dư riêng, dùng reconcile_dr_cr_note của ERPNext đối trừ tối đa phần còn nợ của chính hóa đơn gốc, cùng khách/Company/TK VND. Dịch vụ native tạo bút toán hai dòng cùng công nợ, không thêm doanh thu hoặc tiền. Chỉ khi có quyền tạo/xác nhậnJE mới tự đối trừ; thiếu quyền giữ hàng trả/credit đã ghi và báo kế toán đối trừ, không chuẩn bị chi nhầm. Phiếu chi vẫn nháp và chỉ tham chiếu số dư có còn lại đúng hóa đơn sở hữu số dư. Bù trừ/Đổi hàng dùng đối trừ nguồn tương tự, không tự chi. Bổ sung assertion kiểm cả hóa đơn gốc và hóa đơn giảm hết số dư sau chi.

Cục bộ495ca kh_aph (14skip) đạt. Chưa có nativePASS cho sửa này, đổi mã, theo dõi gốc và mẫuA5 cuối. Bước tiếp chạyUAT125ca và các cổng đúng mã mới, đọc bằng chứng không chỉ nhìn xanh. PR38 vẫn draft, chưa tăng version/tag/phát hành; production0.16.4 và28cờ giữ nguyên. Toàn phạm vi còn phần offline, đối soát snapshot/bộ giấy theo lượt, chuẩn bị/gom kho và giảm theo dòng/kiểm trả sau giảm trước đó.


## 21/10/2026 — A5: tăng khoảng ký, tách bản nhận cuối khi khách yêu cầu

QA trực quan phát hiện bản gọn trước có chỗ ký quá ít. Đã giữ chữ chính9pt và tăng khối ký tại kho lên20mm, giảm dòng trùng về kho/lý do; không thu nhỏ toàn bộ phiếu. Ship không yêu cầu ký cuối: hai liên Phiếu xuất kho A5. Chỉ khi chọn cần khách ký tại nơi nhận mới in thêm một Biên bản giao nhận hàng hóa có cột thực nhận trống, ngày/giờ/người nhận, chất lượng/chênh lệch và hai khối ký25mm. Đây là bản xác nhận hàng ở đích, không phải mẫu3liên nháp cũ hay bản đối soát nợ. Không tự điền số thực nhận cuối bằng lượng đã xuất.

Đã tạo/xem PDF dữ liệu giả bằng Chrome: hai dòng tên dài ra2trang A5 ngang khiKhông,3trang khiCó; các trang đều có số phiếu và đơn vị, phần ký đủ khoảng trống, tiêu đề bảng mang số phiếu để truy khi sang trang. Cục bộ495ca(14skip) đạt. Chưa nghiệm thu máy in/nhân sự thật, chưa phát hành. Lượt771b365 UAT39575256295 vừa lỗi bước nghiệp vụ, cần tải log/artifact để xác định nguyên nhân, không suyĐẠT; các thay đổi sau771b365 chưa chạy trong lượt này. PR38 vẫn draft; production0.16.4 giữ nguyên.


## 21/10/2026 — ĐANG DỞ: theo dõi giấy gốc trong Kho vận và Chốt ngày

Thêm lối native Giấy gốc chưa về trong Kho vận, chỉ lọc phiếu thế hệ mới đã ghi sổ, không đánh dấu thiếu hàng loạt lịch sử. Chốt ngày giữ việc thiếu giấy gốc của ngày trước dù ảnh đã đối chiếu; phân biệt thiếu/đã nhận gốc với trạng thái ảnh. Nhận giấy ở API hiện có làm hết việc thiếu gốc, không ghi lại kho/nợ/tiền. Không thêm màn hình, DocType nhiệm vụ hay số dư riêng.

Cục bộ495ca kh_aph (14skip) đạt; thêm kiểm ngày trước có ảnh đã đối chiếu nhưng chưa có gốc. Bổ sung HTTP vào ca giấy gốc, giữ bộ014125PASS. CHƯA cóPASS native cho phần này hoặc đổi mã44c3c3d. Các lượt771b365 vẫn đang kiểm; cần lưu kết quả theo đúngSHA, không suy sang code mới. PR38 vẫn draft, production0.16.4 giữ nguyên, không version/tag/site.

Phần còn thiếu của toàn phạm vi: nhập giấy tay khi mất mạng, snapshot đối soát có ký và bộ giấy theo lượt, chuẩn bị chuyển/gom kho trước khi giao, giảm giá theo dòng và xử lý trả sau giảm giá cũ. Còn cần hoàn thiện việc chọn kho nhận trả khác kho nguồn, chứng cứ khách cuối khi có yêu cầu riêng và lịch sử phiên bản in. Nghiệm thu nhân sự/hàng tồn/máy in thật vẫn gom cuối; không gọi toàn phạm vi đã xong.


## 21/10/2026 — ĐANG DỞ: đổi sang mã mới bằng đơn bán chuẩn

Đường nhận trả mới chọn Đổi hàng không còn tự chuẩn bị lại mã cũ. Thêm nút Lập đơn hàng thay: API chỉ đọc mở lại đơn đã lưu hoặc điền khách/nguồn vào form đơn chuẩn chưa lưu; người bán chọn mã, lượng, kho, giá mới. Link phiếu nhận trả bất biến, khóa duy nhất cho một đơn thay còn hiệu lực; hủy giữ link lịch sử và nhả khóa cho lập lại. Kiểm cùng khách/Company, cả đường đổi nguồn không được chuyển Company của đơn thay. Native lưu/xác nhận/giao tiếp tục sở hữu giá, hạn mức, tồn và nợ; đơn nháp không ghi sổ. Không tự cấn tiền giữa đơn vị hoặc tự coi trao đổi đã tất toán tiền.

Cục bộ494ca kh_aph (14skip) đạt; kiểm cú pháp JS đạt. Thêm ca HTTP đổi mã, mở lại/chống trùng, chặn xóa nguồn/chuyển Company, hủy rồi lập lại và xuất mã mới; kỳ vọng bộ014125PASS. CHƯA có bằng chứng native cho thay đổi này. Lượt UAT39575256295 và Cổng2b39575261403/Cổng339575265840 đang chạy trên771b365 trước phần đổi mã; Cổng2 cùng mã39575248458 success. Chưa coi các cổng này xác nhận code mới chưa nằm trong run.

PR38 vẫn draft, không tag/phát hành/site. Production0.16.4 giữ nguyên. Cần hoàn thiện offline, snapshot ký đối soát, chuẩn bị/gom kho, giảm theo dòng/chống giảm trùng sau giảm cũ, bộ giấy cùng lượt, danh sách giấy gốc còn thiếu. Bước tiếp chờ đọc bằng chứng nghiệp vụ của lượt hiện tại rồi chạy UAT125ca đúng mã đổi hàng, sửa lỗi thật nếu có.


## 21/10/2026 — ĐANG DỞ PR38: chặn bán từ kho vận chuyển, chờ kiểm nghiệp vụ toàn lát

Đã sửa guard kho chuẩn (cờ hiện có kh_aph_kho_chuan): đơn chung/đơn con/DN/hóa đơn có xuất kho không lấy kho Vận chuyển làm nguồn bán; trả hàng và hóa đơn không xuất kho giữ đường xử lý riêng. Thêm ca HTTP vào bộ0112, không đổi sốPASS kỳ vọng bộ đó. FormDN cập nhật ô giao nhận ngay khi đổi cách giao, không cần tải lại form.

Cục bộ487ca kh_aph (14skip),108ca lõi đạt. Cổng3 run39571303257 mãfc8e721 đã success và đọc artifact: nâng cấp từ0.16.4, schemafresh1113/1113 và rollback1105/1105 lệch0; so sổ/quay lui/nhánh lỗi chủ độngKHỚP. Cổng2b cùng mã39571323837 success, log xác nhận dựng/nâng/quay lui đạt. Các kết quả này chưa gồm sửaA5/giới hạn hoàn/guardTransit mới nhất. Cần chạy bốn cổng đúng mã cuối; UAT124ca bộ014 chưa cóPASS, không coi đơn vị thuần là kiểm native.

PR38 vẫn draft, version/tag/site giữ nguyên0.16.4. Phần mới đã viết: trảlẻkg, xe khách có chỉ định, nhà xe chọn/nhập, dấu báo nhận, giấy gốc độc lập, A5 và giới hạn chuẩn bị tiền hoàn. Chưa hoàn thiện offline, snapshot ký đối soát, chuẩn bị chuyển/gom kho trước xe đi, đổi mã mới, giảm theo dòng/chống giảm trùng, bộ giấy cùng lượt. Bước tiếp đọc kết quảHTTP/Chrome để sửa lỗi thật, rồi tiếp tục các phần chưa triển khai; chưa đủ điều kiện phát hành toàn phạm vi.


## 21/10/2026 — ĐANG KIỂM: giới hạn phiếu hoàn theo số dư sau trả hàng

Bổ sung cho phiếu nhận trả tạo bằng đường mới: sau khi hóa đơn giảm đã trừ đúng khoản gốc, chỉ chuẩn bị phiếu chi bằng phần số dư có còn lại, tối đa giá trị lần trả. Chưa thu/còn nợ sau giảm thì không tạo phiếu hoàn nháp. Phiếu hoàn mới tham chiếu khoản gốc bằng phân bổ âm, để native kiểm số dư và tất toán khi thực chi; không tạo hóa đơn giảm lần nữa. Đường trả lịch sử chưa đổi cách chuẩn bị nháp; giao dịch khác VND yêu cầu kế toán đối chiếu tỷ giá riêng. Chưa coi thay đổi này đã PASS native.

Cục bộ483ca kh_aph (14skip) đạt; lõi108ca đã đạt ở mốc trước (không đổi lõi). Thêm2ca HTTP kiểm chưa thu và thu một phần/đủ, dự kiến b014124PASS; cần chạy đúng mã mới. Mãf7f284c đang có UAT39573964111 chạy cho bản sửa A5, chưa gồm giới hạn hoàn này. Cổng2 của f7f284c run39573956188 success. Cổng3 run39571303257 của fc8e721 success; phải đọc artifact và kiểm lại mã cuối, không suy sang thay đổi hoàn chưa chạy. PR38 vẫn draft, chưa tag/phát hành; production0.16.4 giữ nguyên, phần offline/đối soát/gom kho/đổi mã và giảm theo dòng vẫn còn mở.


## 21/10/2026 — ĐANG DỞ PR38: sửa phân trang A5 và lỗi tương thích mẫu cũ

Ứng viên `fc8e721cbeddfe5e1011be1f4dff87c912572ed2`: Cổng2 run39571104062 và Cổng2b run39571323837 success. UAT39571298855 FAIL tại ca in cũ vì mất chú thích “Người thực nhận hàng”; giữ bằng chứng trong artifact candidate-image-evidence/http-b014-evidence.txt, chưa chạy tới ca trả lẻ mới. Đã sửa giữ chú thích cũ cho phiếu thế hệ cũ; không bỏ assertion. Cổng3 run39571303257 đang chạy, chưa kết luận.

Kiểm PDF bằng Chrome với dữ liệu giả: mẫu A5 mới có hai dòng hàng tên dài và yêu cầu khách ký tại nơi giao, hai liên ra đúng2trang A5 ngang; đã xem cả hai trang, phần ký không bị tách riêng. Giữ chữ chính9pt, thu gọn khoảng cách/thông tin cuối phiếu cho thế hệ mới; phiếu cũ giữ bố cục cũ. Đây là kiểm bố cục trên máy, chưa phải nghiệm thu máy in/người dùng thật. Bổ sung5ca kiểm ranh giới trả lẻ: nguồn khác/phiếu xuất thường bị chặn, giữ quy cách gốc dù Item đổi,5kg không bao không thành25kg hoặc0.2bao.

Cục bộ480ca kh_aph (14skip) và108ca lõi đạt; kiểm cú pháp helper Chrome đạt. PR38 vẫn draft, chưa tăng version/tag, production vẫn0.16.4. Chưa hoàn thiện đổi mã hàng, giảm giá theo dòng/chống giảm trùng sau giảm trước đó, hoàn tiền gọn, nhập giấy tay khi mất mạng, snapshot đối soát và gom kho. Bước tiếp chạy lạiUAT đúng mã đã sửa, đọc bằng chứng ca mới; tiếp tục phần còn thiếu, không coi phần đã kiểm này là hoàn tất toàn phạm vi.


## 21/10/2026 — NềnCổng3 ĐẠT; ứng viên kho tiếp tục sửa/kiểm, chưa phát hành

PR37 đã gộp main7a588c9. Cổng3 run39567580998 success đúngd5a9491ffb27e68c93f708fc831f9fbdb79917f7, đã đọc log/artifactcong-3-bang-chứng12331362860: nền0.16.4 đúngdigest, diễn tập/nâng/sochi tiết/quay lui/nhánh hỏng chủ độngKHỚP; schemafresh1099/1099,rollback1105/1105, lệch0. Đây là nền trước sửa nghiệp vụ, không chứng minh ứng viên mới đãPASS.

PR38 trảlẻ mã164962b: Cổng239568824265 success; UAT39568824330 FAIL ởfixtureItemmới thiếuItemTaxTemplate trước khi vào ca trảlẻ, đã giữrun và sửafixturegánthuếtheomãmẫugiả; không nới kiểmthuế. Manual39568812563 bịhủy do lượtPRthay thế. Chưa cóPASSnative của ca mới.

Working branch có thêm kho/ảnh–giấygốc độc lập: API nhận giấy gốc kiểmwrite/modified, lưuuser/time/vị trí, retry giữdấu, không đổi sổ; đối chiếu bản kýnhàxe cho phiếu thếhệmới đanggiao. Đã đối chiếuAutocomplete đúngFrappe16.52: phảiignore_validation mới nhậpnhàxemới ngoài gợiý, label gợiýescape; đổi tênxe mới xóaSĐTxe cũ. UI/caseChrome mới kiểm nhậpnhàxe và2ô báo nhận, kg/bao nhận trả; HTTPmới dự kiến122PASS (117cũ+5mới), chưa chạy đúngheadmới. Cục bộ475ca(14skip) đạt trước lần sửafixturecuối; kiểmcúphápJSđạt. Chưa hoànthiệnđổi mã/giảmtheodòng/hoàn gọn/offline/snapshotđốisoát, chưa nângversion/tag/site. Bước tiếp chạy lạiUAT/Cổng2 trênheadmới, sửa lỗi thật, tiếp tục phầncònthiếu.


## 21/10/2026 — ĐANG DỞ: thêm thông tin nhà xe/xe khách và dấu nhận cuối

Working branchfeat/kho-giao-nhan-don-gian-20261021 đã bổ sung thế hệ thông tin giao nhận1: xe khách phải có căn cứ chỉ định, tínhpickup; nhà xeData/Autocomplete chọn đã dùng hoặc nhập mới+tên/SĐT, snapshot từngphiếu, nguồn báo/ngày nhận cuối readonly theoAPI. Chuẩn bị/inA5 ghi nhàxe, bên nhận vận chuyển khác khách cuối; mẫu chuẩn/reprint đồng bộ carrier/căn cứ. Hashpayload cũ không thêm khóa mới để giữretry. CửaKhách thêm lốiGiảmgiáđơn cũ gọi đề nghịJEnháp sẵn có; khóaSI và kiểm quyền đọc khi mở lạiJEnháp, chưa thay cơ chế giảm theo dòng.

Cục bộ475ca (14skip) và kiểm cú phápJS đã chạy trong quá trình sửa; cần lưu kết quả cuối sau đồng bộmẫu. Cổng3nền0.16.4 run39567580998 mãd5a9491 còn đang chạy; UATtrảlẻ mã164962b run39568824330/Cổng239568824265 đang chạy; lượtmanual39568812563 bịhủy do lượtPRthay thế, không làPASS. HTTPmới dự kiến120PASS=117cũ+trảlẻ+2ship, chưa chạy trên mãship. PR38 vẫndraft. Chưa hoàn thiện đổi mã,giảmgiátheodòng/giảmtrùngsauđãgiảm,hoàn tiền gọn,giấygốc,offline,snapshotđốisoát; chưa phát hành/site/tag.


## 21/10/2026 — ĐANG DỞ triển khai tối ưu kho: lát nhận trả lẻ kg

Nhánhfeat/kho-giao-nhan-don-gian-20261021 bắt đầu từ nềnCổng3 PR37. Đã thêm đường lậpDNtrả nháp theo phiếu gốc dùKhách đã nhận, khóa nguồn/reserve lượng mọiuser, requestid/hash retry; cho5kg và bao vật lý độc lập, nhậpCáchly qua luồng có sẵn. Bổ sung ôTrả lẻ theo kg, sổbao ghi đúngkg vàbao0 khi không nhận vỏ; JS không nhân ngược thành bao nguyên. UI nhận trả trênphiếu/Khách, chưa thống nhất xong mọi lốiĐổi/Trả/Giảmgiá. Cờsales_adjust/sales_p1 hiện có (mặc địnhtắt) sở hữu bổ sung; schema gọi bộ cài rõ ràng.

Cục bộ472ca (14skip) đạt trước thay đổi caseHTTP; thêmHTTP_014_TRA_LE_5KG vào b014, dự kiến118PASS thay117 do thêm1ca, CHƯA có kết quảCI. Không coi unit là đã kiểm native. Cần kiểm thực tế mapping/permissions/giá trị giảm/receiptCáchly vàrollback. Chưa hoàn thiện các látship,phiếuA5,giấy gốc,offline,đốisoát snapshot,giảm nợ cũ theo dòng,đổi mã/hoàn tiền. Chưa nângversion/tag/deploy, production0.16.4 giữ nguyên. Bước tiếp: chạyUATnative ca mới, sửa lỗi nếu có; tiếp tục látship và các phần còn thiếu, không tuyên bố cả phạm vi đã xong.


## 21/10/2026 — ĐANG KIỂM nền Cổng3 từ production0.16.4

PR36 thiết kế đã gộp main e9a2755 sau chủ dự án chốt tiếp tục. Chuẩn bị phát triển luồng kho/ship/đổi trả/giảm nợ cũ và trảhỏng lẻkg; chưa sửa nghiệp vụ/site. Đổi nền Cổng3 sang0.16.4/digest1a8f0063… đúng log production. Chờ run thực trên mã mới, chưa tuyên bốĐẠT hoặc phát hành. Production vẫn0.16.4,28cờ; nghiệm thu thật gom cuối.


## 21/10/2026 — Chốt bổ sung: giảm nợ đơn cũ, trả hỏng một phần bao và hoàn tiền

Chủ dự án xác nhận có giảm giá chất lượng cho khoản nợ đơn trước và trả lẻ hàng hỏng (bao25kg trả5kg để hoàn tiền). Đã bổ sung vào `docs/bo-sung-doi-tra-giam-gia-20261021.md`: chọn khoản/phiếu cũ không cần đơn mới;5kg thực nhận khác cảbao/vỏ thực nhận,20kg khách giữ; quy đổi theo dònggốc, hànghỏng không tự thành tồn bán. Tiền trả/giảm truy giá-thuế/thỏa thuận hợp lệ, tách giảm phải thu với thực hoàn, không dùng cùng giá trị hai lần. Thêm4ca đề xuất, tổng16ca chưa chạy; chưacode/site/mẫu, production0.16.4 giữ nguyên.


## 21/10/2026 — Bổ sung phạm vi đổi tại xe, đổi/trả sau giao và giảm giá hàng xấu

Chủ dự án bổ sung ba tình huống vào lần tối ưu này. Đã ghi `docs/bo-sung-doi-tra-giam-gia-20261021.md`: từ phiếu gốc một lốiĐổi/Trả/Giảm giá; phân biệt đã/chưa ghi xuất và giao thực tế; trả ghi kho theo lượng thực nhận, giao thay xuất riêng; giảm giá giữ hàng chỉ tài chính, đề nghị đang thương lượng chưa tự giảm nợ. Truy đúng dòng/đơn vị/giá-quy cách-thuế gốc, không vượt trả lũy kế hoặc giảm trùng, không cấn chéoCompany; tiền thừa cho xử lýhoàn/giữ/phân bổ rõ, không tự coi là cọc. Có12ca đề xuất chưa chạy.

Đã đọc nền sales_adjust/delivery_receivable và bản kýTT91 Điều10 khoản5c.1 về trả/đổi; không coi đã kiểm toàn luồng mới. Đồng thời lưu quyết định ship: luôn inPhiếu xuất, khách cuối không phải ký khi không có yêu cầu/thỏa thuận riêng, nguồn báo nhận và user/time lưu dấu; nhà xe cho chọn/nhập mới ngay (chi tiết bắt buộc là đề xuất). Chỉ tài liệu, chưacode/schema/quyền/mẫu/site; production0.16.4 giữ nguyên.


## 21/10/2026 — Rà soát pháp lý bộ chứng từ kho–giao nhận: đề xuất, chưa đổi mẫu

Đã thêm `docs/de-xuat-chung-tu-kho-theo-phap-ly-20261021.md`: phân biệt02-VT, giao nhận hàng hóa tự thiết kế, phiếu thu tiền mặt/bank, đối chiếu nợ và chứng từ lưu thông. Đề xuấtA5 “Phiếu xuất kho kiêm biên bản giao nhận hàng hóa” cho tự lấy, chưa phải tên mẫu bắt buộc/đã được duyệt. Ít user không đồng nghĩa miễn chữ ký/kiêm nhiệm; TT99 Điều10 khoản4 giới hạn kế toán trưởng ký thay quản lý. Không lấy giá bán thay giá trị xuất kho, không thay nội dung liên đã ký.

**Cập nhật căn cứ:** đã kiểm bản kýNĐ254/2026 Điều43: từ01/07/2026 NĐ123/2020,NĐ70/2025 hết hiệu lực; TT91/2026 Điều25 thayTT32/2025, giữ quy định chuyển tiếp. Hồ sơ cũ dẫn các văn bản này là lịch sử, không đủ căn cứ giao dịch mới. NĐ254 Điều9 khoản1,3: hóa đơn theo thời điểm chuyển giao/từng lần giao, không chờ đối chiếu nợ. Tự động hóa hóa đơn một phần có thể phát triển sau nhưng phải kiểm quy trìnhMISA hiện hành đáp ứng nghĩa vụ; chưa kiểmMISA thật/chưa kết luận tuân thủ. Phân loại pháp lý kho vệ tinh/nhân sự trước khi chọnPXK điện tử lưu thông hoặc kiêm nhiệm; không suy giấy tay thay hóa đơn điện tử.

Chỉ tài liệu, chưacode/schema/quyền/cờ/mẫu/site/tag. Production0.16.4 giữ nguyên. Các ca kiểm trong đề xuất chưa chạy; cần chốt mẫu vận dụng/quy chế và dữ kiện đăng ký đơn vị–vệ tinh, luồngMISA/sự cố trước cấu hình cuối. Nghiệm thu thực tế vẫn gom cuối.


## 21/10/2026 — Điều chỉnh thiết kế: giao khi mất mạng, ký phiếu thu và đối soát nợ

Chủ dự án bác bỏ điều kiện phải chờ ERP xác nhận xuất thành công mới cho xe rời. Đã chốt: người phụ trách được giao quyền được lập giấy tay mới và quyết định giao khi mất mạng, kể cả chưa chuẩn bị phiếu trước; ảnh/gốc xử lý sau. Khi thực thu phải lập phiếu thu cho người nộp ký; có tăng hoặc giảm nợ phải in biên bản ký, kể cả cuối lượt về0. Một bản theo khách, chi tiết từng đơn vị, cọc/tiền chưa phân bổ riêng. Lái xe chỉ ký nợ khi khách giao thêm quyền ký nợ riêng. Các quyết định này đã ghi vào quyết định nghiệp vụ, không hỏi lại.

Đã lập `docs/bo-sung-kho-mat-mang-thu-tien-doi-soat-20261021.md` đủ9nhóm và15ca kiểm bổ sung đề xuất, cập nhật chỉ dẫn ưu tiên trong thiết kế trước. Đối chiếu nguồn: mẫu Phiếu thu chi/biên bản đối soát đã có, nguồn nợ hiện theo ngày chứ chưa snapshot ký theo lượt. Thiết kế mới phải giữ snapshot/mốc/phạm vi và số giấy duy nhất xuyên user, không tạo sổ trùng/thu hai lần; người thu khác user nhập phải ghi đúng người giữ tiền. Mất mạng không bảo đảm số dư toàn hệ thống hiện tại: chỉ ký số đã biết/phát sinh với mốc rõ, sau lệch xin xác nhận lại, không sửa số trên bản đã ký hoặc ghi0 giả. Lái xe thiếu quyền nợ không làm chậm giao, hồ sơ chuyển chờ khách ký riêng.

**Chưa code/schema/quyền/cờ/mẫu/site.** Production vẫn0.16.4/digest1a8f0063…; không biến số giấy tay thành bút toán đã ghi hoặc tắt kiểm tồn/hạn mức để nhập bù. Bước tiếp: hoàn thiện trường/khóa/quyền hồ sơ giấy mới, snapshot đối soát và bộ giấy cùng lượt; danh sách người được giao quyền/phạm vi và người giữ tiền thực tế cần cấu hình khi build. Nghiệm thu toàn bộ với nhân sự/dữ liệu thật vẫn gom cuối.

## 21/10/2026 — Tiếp nối kho–giao nhận: đã đối chiếu và lập thiết kế, chưa code

Chủ dự án xác nhận mục kiểm sau nâng0.16.4 về địa chỉ đầu đơn đã xong. Chưa suy thành đã kiểm thêm/sửa SĐT thật hoặc nghiệm thu tất cả nghiệp vụ. Production vẫn0.16.4/digest1a8f0063… như mốc dưới.

Đã đọc nguồn và lập `docs/thiet-ke-kho-giao-nhan-tiep-noi-0164.md`:9nhóm,5sơ đồ,4luồng chính và37ca UAT đề xuất. **Hai quyết định mới được người dùng trực tiếp chốt:** lái xe do khách chỉ định/xác nhận ký nhận tại kho tính là khách đã nhận; giấy gốc lưu tập trung kế toán cửa hàng, vệ tinh chuyển về. Ghi thêm vào quyết định nghiệp vụ, không hỏi lại.

Điểm đã xác minh từ code: DN chờ xuất đã in được; A5 hai liên có cột thực xuất trống khi nháp, nhiều lối in khác mục đích; bảng tổng hợp chỉ nhận DN đã submit; đối chiếu bản ký hiện chỉ khi Khách đã nhận. Chuyển nội bộ send hiện tạo+xác nhận rồi mới mở SE, cần nhánh chuẩn bị/in trước xe đi. validate_kho_ban xét KHONG_BAN nhưng danh sách chưa có Vận chuyển; receive chuyến đối chiếu quy cách Item hiện tại cần kiểm snapshot khi quy cách đổi. Hai điểm sau là rủi ro đọc nguồn, không tuyên bố đã tái hiện/sửa trên production.

Thiết kế: ưu tiên90% tự lấy bằng Chuẩn bị & In → ký thực tế → Xác nhận thực giao, không thêm duyệt thường; pickup xe khách có chỉ định không phải chờ receive lần nữa. Gửi ship tách ký nhận chở/khách nhận cuối; gom cùng Company giữ nguồn–Transit–đích rồi xuất bán tại kho thực giao, khác Company chưa tự làm. Tái dùng DN/SE/service đã kiểm, giữ Nhà máy riêng. Bản in dự kiến/phiên bản/thực giao và nhận giấy gốc là hồ sơ, không sổ kho/nợ mới. Không nhập lại khách/địa chỉ đã có.

**Chưa triển khai:** chưa sửa app/schema/quyền/cờ/mẫu in/site. Số liên/bố cục mẫu vận hành, thời hạn chuyển giấy và danh sách nhân sự thật vẫn là đề xuất chưa chốt; giữ mẫu A5 đã duyệt, mẫu3liên vẫn nháp. Có thể làm phần độc lập đã rõ, không phải đợi đủ hàng tồn thật. Trước code/phát hành kế tiếp cập nhật và kiểm mốc Cổng3 sang production0.16.4 theo hồ sơ. Nghiệm thu thực tế toàn bộ vẫn gom cuối. Bước tiếp: chốt các lựa chọn mẫu còn lại, triển khai lát A tự lấy/in trước giao theo hợp đồng và ca kiểm đã ghi; không tự tạo tag/đánh số bản mới từ hồ sơ thiết kế.

## 21/10/2026 — Production0.16.4 đã được người vận hành xác nhận ĐẠT

Anh Tiến gửi log từ `tienduongmarcom@erpnext-prod:~/trien-khai`: image **ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.4**, digest **sha256:1a8f00639516ff4843d408fca61695c6b7ca0cfe680cf6c1db28fb0f16d09f38**, dòng cuối **=== XONG 0.16.4: ĐẠT ===**. Digest khớp log push và registry đã đối chiếu ở [phát hành39539645648](https://github.com/tienduongmarcom/aphvh/actions/runs/39539645648), nguồn tag **v0.16.4 = 1dffa623dc28d239321b7c9cd249968def402123** (PR #30 đã gộp main).

Trước nâng, người vận hành gửi diễn tập thực **10210410cb2c5d**, dấu `/home/tienduongmarcom/dien-tap-0.16.4.ok`: tổng/đếm/chi tiết KHỚP, DIỄN TẬP0.16.4:ĐẠT. Đây là bằng chứng người vận hành gửi; agent không tự SSH kiểm lại VM. Mốc khach/aph-vh/phien-ban.yaml đã cập nhật0.16.4. Không cờ mới, bộ28cờ theo thủ tục nâng giữ nguyên; không suy thêm kết quả kiểm quyền/nhân sự thật từ log này.

Bản sửa địa chỉ/SĐT đã triển khai. Bước kiểm sau nâng còn mở: tải lại giao diện, chọn khách đã có địa chỉ liên kết và kiểm đầu Đơn bán chung; khách chưa có SĐT vẫn báo thiếu đúng thực tế. Thêm/sửa SĐT trong nghiệp vụ thật rồi tải lại đơn sẽ đọc thông tin hiện tại; không cần nhập lại địa chỉ/khách để chữa lỗi. Chưa có xác nhận của người dùng về kết quả hiển thị trên production; kiểm Chrome dữ liệu giả đã đạt trong hồ sơ dưới. Nghiệm thu toàn bộ với nhân sự/hàng tồn/máy in thật vẫn để cuối theo yêu cầu.

Quay lui có điều kiện về **image0.16.3/digesta252478b…** và snapshot tương ứng ngay trước nâng0.16.4; không restore snapshot cũ sau giao dịch mới khi chưa xử lý phần phát sinh. Mục phát hành đã hoàn tất, không chạy lại chỉ để kiểm. Việc chuẩn bị lần phát triển sau: Cổng3 hiện còn mốc0.16.3 đã kiểm; cần chuyển nền sang0.16.4/digest trên và chạy riêng trước lần phát hành kế tiếp. Chưa thay workflow hoặc coi chuyển mốc đó đã PASS trong PR hồ sơ này.

## 21/10/2026 — Image0.16.4 đã phát hành, chờ diễn tập và nâng production

Chủ dự án đã push tag **v0.16.4**, kiểm tag đúng **1dffa623dc28d239321b7c9cd249968def402123**. [Phát hành39539645648](https://github.com/tienduongmarcom/aphvh/actions/runs/39539645648) **success**: Cổng2/2b/3/UAT và build/push đều success đúng nguồn tag. Image **ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.4**, digest **sha256:1a8f00639516ff4843d408fca61695c6b7ca0cfe680cf6c1db28fb0f16d09f38**; đã đối chiếu log pushing manifest/containerimage.digest với registry docker buildx imagetools inspect, khớp. Không ghi đè tag/image.

Production vẫn0.16.3/digesta252…/28cờ, chưa có log diễn tập hoặc XONG0.16.4:ĐẠT trên erpnext-prod/frontend; phien-ban.yaml giữ0.16.3. Bước tiếp trên SSH máy chủ: vào tmux nang-cap-0164, checkout tag0.16.4, chạy dien_tap_ban_sao.sh0.16.4. Chỉ sau ĐẠT/so sổ khớp/dấu đúng còn hạn mới trien_khai_frontend.sh0.16.4 trong bảo trì. Không cờ mới; không setup_uat trên production. Hướng dẫn chính xác: docs/phat-hanh-0164.md. Nếu SSH ngắt chỉ nối lại phiên, không chạy lượt song song. Nghiệm thu nhân sự/hàng tồn/máy in thật vẫn để cuối.

## 21/10/2026 — Đã gộp bản vá0.16.4 vào main, chờ chủ dự án gắn tag

[PR #30](https://github.com/tienduongmarcom/aphvh/pull/30) đã gộp giữ lịch sử bằng **1dffa623dc28d239321b7c9cd249968def402123**. Đã đối chiếu tree: mã app/kiểm giống hệt c9433f3 đã đạt bốn cổng dưới đây; chỉ hai tệp hồ sơ thay sau mã kiểm. Tagv0.16.4 chưa tồn tại khi kiểm, agent không tạo tag/image hoặc sửa VM. Production vẫn0.16.3/digesta252…; phien-ban.yaml giữ đúng mốc này.

Hướng dẫn đúng nguồn và tmux: `docs/phat-hanh-0164.md`. Bước cần người vận hành: chủ dự án tự gắn tag đúng merge commit trên theo AGENTS; chờ phát hành xanh/digest rồi SSH erpnext-prod/frontend, diễn tập bản sao thực và nâng trong tmux nang-cap-0164, không thêm cờ. Khi SSH ngắt chỉ nối lại phiên. Không cần nhập lại địa chỉ khách đã liên kết. Nghiệm thu thực tế toàn nghiệp vụ vẫn để cuối.

## 21/10/2026 — Ứng viên0.16.4 đã đạt bốn cổng: sửa địa chỉ/SĐT khách nhập riêng

[PR #30](https://github.com/tienduongmarcom/aphvh/pull/30), nhánh fix/dia-chi-khach-lien-ket-20261021, mã app/kiểm cuối **c9433f332230f7704e9ccd87476ddb9154386da1**. Commit hồ sơ theo sau chỉ tài liệu. Production vẫn **0.16.3/digesta252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95**, chưa tag/phát hành image0.16.4 hoặc sửa VM/dữ liệu thật.

Nguyên nhân xác nhận qua đọc Customer/Address: địa chỉ đã liên kết đúng khách nhưng cache primary_address trống khi import riêng/chưa đánh dấu chính; đầu đơn0.16.3 chỉ đọc cache nên báo thiếu. Đã dùng chung bộ đọc nhận diện cho customer_identity/customer_query/tim_khach. Đọc Address/Contact theo quyền get_list, liên kết Customer đúng loại/đúng người; loại địa chỉ ngừng dùng, ưu tiên Link chính hợp lệ rồi hồ sơ đánh dấu chính/thứ tự tạo. SĐT ưu tiên Contact mobile/phone, rồi bảng Contact Phone (kể cả chưa đánh dấu số chính); Contact rỗng không che số trên liên hệ khác cùng khách. Không có Contact thì dùng số khai trực tiếp Customer, rồi số Address. Đọc lại mỗi lần tải để thấy số mới, không phục hồi cache cũ khi đã xóa số Contact. Customer-only cũ chưa có hồ sơ/Link thay thế vẫn dùng được; từ chối quyền có thông báo riêng. Không tự sửa Customer, chọn địa chỉ giao, snapshot chứng từ cũ hoặc logic kho–nợ–tiền; không đổi schema/quyền/28cờ.

Bốn cổng **success cùng c9433f3**:
- [Cổng2 39534100779](https://github.com/tienduongmarcom/aphvh/actions/runs/39534100779): cài mới.
- [Cổng2b 39534123205](https://github.com/tienduongmarcom/aphvh/actions/runs/39534123205): dựng/nâng/lỗi kéo image không gây gián đoạn/quay lui.
- [UAT 39534119807](https://github.com/tienduongmarcom/aphvh/actions/runs/39534119807): đã tải/đọc artifact candidate-image-evidence, **310 JSON PASS,0FAIL** gồm core/chuẩn bị/khôi phục, không gọi là310ca nghiệp vụ. Riêng b014117PASS. HTTP_UX03 xác nhận import Address không chọn chính, loại địa chỉ ngừng dùng/khách khác, thêm–sửa–xóa–thêm SĐT, Contact chưa chọn số chính/có Contact rỗng, cả ba API đúng, Customer không bị ghi lại. DESK_UX0 xác nhận đầu đơn mới hiện đúng, đổi sang khách rỗng không giữ địa chỉ/số người trước rồi chọn lại; không tạo thêm đơn. Đã xem ảnh khach-dia-chi-lien-ket.png: tên/mã, địa chỉ giả và SĐT0900000143 hiện đúng trên đơn chưa lưu, không hộp thoại che. Chrome phiên quản trị tiếng Anh, không dùng ảnh này kết luận toàn bộ nhãn tiếng Việt. Core63.508tệp không đổi; dữ liệu giả được khôi phục, gồm Contact/Contact Phone/Dynamic Link.
- [Cổng3 39534126136](https://github.com/tienduongmarcom/aphvh/actions/runs/39534126136): đã đọc artifact cong-3-bang-chung. Nền đúng production0.16.3/digesta252…, diễn tập bản sao tách biệt/nâng0.16.4/so sổ KHỚP; schema site nâng/site mới1099/1099, lệch0, bỏ qua6/6; rollback1105/1105. Cố ý lỗi kiểm nâng: tự quay về0.16.3, giữ bảo trì, đếm/tổng/chi tiết/phiên bản KHỚP. Sổ CI không thay diễn tập bản sao production thực.

Cục bộ **467ca kh_aph (14skip theo môi trường),108ca lõi đạt**. Giữ bằng chứng: Cổng239532525494/lượt1 mã568ab90 FAIL tải moby/buildkit unauthorized trước chạy app; lượt2 cùng mã đạt, không tuyên bố chữa gốc registry. Các run mã19799c5/568ab90 bị hủy khi bổ sung ca Liên hệ không là PASS của mã cuối.

Bước tiếp: gộp PR giữ lịch sử/đúng tree mã đã kiểm; **chủ dự án tự gắn tagv0.16.4** theo AGENTS, chờ workflow phát hành toàn bộ success và digest. Sau đó SSH đúng erpnext-prod/frontend, vào tmux nang-cap-0164, diễn tập bản sao thực0.16.4 ĐẠT/dấu hợp lệ rồi mới trien_khai_frontend.sh0.16.4 trong bảo trì; không cờ mới/không setup_uat. SSH rớt thì nối lại phiên, không chạy thêm lượt song song. Mốc phien-ban.yaml giữ0.16.3 cho đến log triển khai thực. Quay lui về image0.16.3 với snapshot trước nâng, xử lý giao dịch phát sinh trước restore cũ. Nghiệm thu nhân sự/hàng/tồn/máy in thật vẫn để cuối.

## 21/10/2026 — ĐANG KIỂM ứng viên0.16.4: nhận diện khách từ địa chỉ/liên hệ nhập riêng

Production vẫn0.16.3/digesta252478b… đã ĐẠT. Lỗi người dùng báo và kiểm chỉ đọc trên Customer/Address: Address đã liên kết Customer nhưng ô tóm tắt primary_address còn trống, đầu đơn0.16.3 đọc ô này nên báo thiếu. Không lưu mã/tên/địa chỉ thật vào ca thử, không sửa dữ liệu production.

Sửa customer_identity/customer_query/tim_khach dùng chung bộ đọc Address/Contact liên kết đúng Customer, theo get_list/quyền native; loại Address ngừng dùng, ưu tiên Link chính hợp lệ rồi hồ sơ được đánh dấu chính/thứ tự tạo. Đọc thông tin hiện tại mỗi lần tải, kể cả khi cache Customer còn giá trị cũ. SĐT ưu tiên Contact mobile/phone, rồi số trong bảng Contact Phone nếu chưa đánh dấu số chính; khi không có Contact dùng SĐT trực tiếp Customer, rồi Address. Contact rỗng không che số của liên hệ khác cùng khách. Thêm/sửa/xóa số Contact không làm sống lại cache cũ. Giữ dữ liệu Customer-only cũ nếu chưa có hồ sơ/Link thay thế; từ chối quyền có thông báo riêng. Không tự điền cache Customer, đổi địa chỉ giao hoặc snapshot chứng từ cũ. Không đổi schema, quyền,28cờ hoặc logic ghi sổ.

Cục bộ467ca (14skip) đạt. Đã mở rộng HTTP trên dữ liệu giả: import địa chỉ không chọn chính, loại địa chỉ ngừng dùng/khách khác, thêm–sửa–xóa–thêm SĐT, đối chiếu ba API và Customer không bị ghi lại. Chrome mở đơn chưa lưu, đổi sang khách rỗng rồi chọn lại, kiểm đúng địa chỉ/SĐT và ảnh khach-dia-chi-lien-ket.png; kiểm không tạo thêm đơn. Còn chờ bốn cổng trên đúng mã và xem ảnh thực tế CI, chưa tuyên bố PASS/tạo tag/phát hành.

Housekeeping trước đó đã xong: [PR #29](https://github.com/tienduongmarcom/aphvh/pull/29) gộp6bd06a0; [Cổng3 39529511187](https://github.com/tienduongmarcom/aphvh/actions/runs/39529511187) success mãeb22911, artifact cong-3-bang-chung đã đọc: diễn tập/nâng/quay lui/so chi tiết KHỚP; UAT39529591303 vàCổng239529591299 success commit15c6c08 chỉ sửa tài liệu saueb22911. Cổng3 nay lấy production0.16.3 đúngdigest. Không phát hành/tag cho housekeeping.

## 21/10/2026 — Production0.16.3 đã được người vận hành xác nhận ĐẠT

Anh Tiến gửi log tại `tienduongmarcom@erpnext-prod:~/trien-khai`: image **ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.3**, digest **sha256:a252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95**, dòng cuối **=== XONG 0.16.3: ĐẠT ===**. Digest khớp image phát hành39518896902 và registry đã kiểm; nguồn tag **v0.16.3 = a1f95b062f2ff7334ed36c176dfb742bf828974a** (PR #26 đã gộp main). Trước đó diễn tập thực **10210126238079**, dấu `/home/tienduongmarcom/dien-tap-0.16.3.ok`, tổng/đếm/chi tiết khớp, ĐẠT. Mốc khách đã cập nhật `khach/aph-vh/phien-ban.yaml`. Không cờ mới; bộ28cờ giữ nguyên theo thủ tục nâng. Đây là bằng chứng người vận hành gửi, không phải agent tự SSH kiểm lại VM.

ĐÃ TRIỂN KHAI bản làm gọn năm khu/nhận diện khách–hàng/thu tiền–in/chuẩn tên chung. Nghiệm thu với nhân sự đại diện, hàng/tồn và máy in thật vẫn để cuối theo yêu cầu, không coi log nâng cấp thành nghiệm thu toàn nghiệp vụ. Mẫu3liên vẫn nháp; công nợ ròng chốt qua báo cáo chuẩn. Vận hành trong tmux và nối lại đúng phiên khi SSH ngắt, không chạy lặp lượt đang chạy.

Quay lui có điều kiện về image0.16.2/digest34a32f71… với snapshot tương ứng lúc nâng0.16.3; không restore snapshot cũ sau giao dịch mới khi chưa xử lý phần phát sinh. ĐANG KIỂM housekeeping: chuyển mốc Cổng3 sang0.16.3/digest trên để lần sau diễn tập đúng production, chạy CI riêng, không sửa mã app hay triển khai lại. Bước tiếp ghi kết quả Cổng3 vào đây và gộp PR hồ sơ; không phát hành/tag mới cho việc ghi nhận này.

## 21/10/2026 — Image0.16.3 đã phát hành, CHƯA xác nhận triển khai production

Chủ dự án đã push tag **v0.16.3**, đã kiểm GitHub trỏ đúng merge commit **a1f95b062f2ff7334ed36c176dfb742bf828974a**. [Phát hành39518896902](https://github.com/tienduongmarcom/aphvh/actions/runs/39518896902) **success**: UAT, Cổng2,2b,3 và bước build/push đều success cùng nguồn tag. Image **ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.3**, digest **sha256:a252478ba9840da9578cfee6ff1bce7412a5afd156c3150ec8da49c59c56ce95**; đã đối chiếu log pushing manifest/containerimage.digest với đọc registry bằng docker buildx imagetools inspect, khớp. Không tag lại hoặc ghi đè image.

Production vẫn theo xác nhận0.16.2/digest34a32f71…/28cờ; chưa nhận log diễn tập hoặc `XONG0.16.3:ĐẠT` trên erpnext-prod/frontend. Không đổi `khach/aph-vh/phien-ban.yaml` trước bằng chứng triển khai. Bước tiếp ở SSH máy chủ: đúng checkoutv0.16.3 → `bash deploy/release/dien_tap_ban_sao.sh 0.16.3`; chỉ sau ĐẠT/so sổ khớp/dấu hợp lệ mới `bash deploy/release/trien_khai_frontend.sh 0.16.3` trong cửa sổ bảo trì. Không thêm cờ. Hướng dẫn tách Mac/VM: `docs/phat-hanh-0163.md`. Không chạy các lệnh này trong thư mục Mac. Nghiệm thu nhân sự/hàng/tồn/máy in thật vẫn để cuối.

## 21/10/2026 — Đã gộp bản tối ưu0.16.3 vào main, chờ chủ dự án gắn tag

Theo yêu cầu tiếp tục, PR #26 đã gộp bằng merge commit **a1f95b062f2ff7334ed36c176dfb742bf828974a**, giữ lịch sử mã kiểm12d9d24 và commit hồ sơ54dfacc. Tree mã app giống mã đã đạt bốn cổng; không squash/đẩy đè main. Tag v0.16.3 chưa tồn tại khi kiểm trước gộp. Production vẫn0.16.2/digest34a32f71…/28cờ; chưa phát hành image, chưa chạy VM.

Đã chuẩn bị hướng dẫn cụ thể `docs/phat-hanh-0163.md`, tách Mac (chủ dự án gắn tag đúng merge commit trên) và SSH erpnext-prod (chỉ sau workflow phát hành success: diễn tập bản sao rồi nâng theo runbook, không cờ mới). AGENTS quy định chủ dự án tự gắn tag; agent chưa tạo/push tag. PR ghi nhận bước này chỉ tài liệu, không cần coi là mã app kiểm mới. Các run bốn cổng và giới hạn giữ ở mốc dưới. Bước chờ: chủ dự án gắn tag, chờ image và diễn tập production thực; không coi CI ĐẠT là production ĐẠT.

## 21/10/2026 — Bản tối ưu0.16.3 đã kiểm kỹ thuật, chưa phát hành

[PR #26](https://github.com/tienduongmarcom/aphvh/pull/26), nhánh `feat/toi-uu-giao-dien-20261020`; mã nghiệp vụ và kiểm cuối **`12d9d24a2ce613b354fc1e72ad815f984e4a217c`**. Commit hồ sơ theo sau chỉ đổi tài liệu, không phải mã nghiệp vụ được kiểm mới. Production vẫn **0.16.2**, digest `sha256:34a32f71f10f20421405c0bd1155abb0570b1d48b564f1df6b8e25d6aa146917`,28 cờ theo xác nhận bàn giao; không truy cập/sửa VM, không tag, gộp hoặc phát hành image trong lượt này.

Đã làm: năm khu Bán hàng / Kho vận / Tiền và kế toán / Nhà máy / Dữ liệu và cấu hình; Nhà máy riêng, tái dùng đủ lối cũ trước khi ẩn các thế hệ Việc/Bàn/Trung tâm. Custom Sidebar chuẩn mang tên Vận hành, ẩn tham chiếu cũ cho cả Workspace Manager, giữ tùy chỉnh riêng và nguồn/route. Đầu đơn hiện nhận diện khách hiện tại, SĐT/địa chỉ hoặc thông báo thiếu; gợi ý theo quyền; công nợ hóa đơn gọn và xem chi tiết. Mã/tên hàng riêng; cửa thu nhanh dùng chung service/mã lượt cũ; giảm nút/in lặp; chỉ một bộ nhập giao nhận theo thế hệ phiếu. Tên hiển thị chung trung lập; số đơn MỚI dùng DBC, số cũ/ID/Link giữ nguyên. Không thêm cờ/quyền, không đổi GL/SLE/PLE hoặc thời điểm ghi kho/nợ/tiền. Mẫu ba liên vẫn là bản nháp.

Bốn cổng **success cùng mã trên**:
- [Cổng2 / cài mới](https://github.com/tienduongmarcom/aphvh/actions/runs/39461537062).
- [Cổng2b / triển khai–quay lui](https://github.com/tienduongmarcom/aphvh/actions/runs/39461551570).
- [UAT HTTP/Chrome](https://github.com/tienduongmarcom/aphvh/actions/runs/39461545287): đã tải/đọc13 tệp, **308 bản ghi PASS,0 FAIL**, gồm kỹ thuật/chuẩn bị/khôi phục; b014117 PASS. Core63.508 tệp không đổi. Đã kiểm ca mất phản hồi thu tiền/gửi lại: một PE, không thêm GL/PLE; metadata năm khu/Sidebar và nhận diện khách theo quyền.
- [Cổng3 / nâng từ0.16.2, lượt2](https://github.com/tienduongmarcom/aphvh/actions/runs/39461556488/attempts/2): đã đọc đúng artifact12286420231 tại `work/ci-toi-uu-12d9d24/cong3-luot2-chinh-xac/`. Diễn tập tách biệt và triển khai0.16.3 ĐẠT; schema nâng/site mới1099/1099, lệch0, bỏ qua6/6 theo cấu hình; rollback1105/1105, đếm/tổng/cờ/phiên bản/cài đặt/giao diện khớp. Ca cố ý lỗi tự quay về0.16.2 và giữ bảo trì, đếm/tổng/chi tiết/phiên bản khớp. Nền CI sổ giao dịch0 không thay diễn tập bản sao production có dữ liệu lúc phát hành.

Cục bộ **454 ca kh_aph (14 bỏ qua theo môi trường),108 ca lõi đạt**; Python/JS/diff đạt. So tĩnh27 JSON giữ trường/kiểu/Link/quyền và5 nhóm hook kiểm soát; chỉ autoname cấp số mới thay đổi. Đã xem ux-viec-ban-hang.png, ux-buoc-tiep.png, xuat-ngay-retry.png: thanh bên quản trị còn năm khu, tên Vận hành/DBC và cột mã–tên có trong ảnh. Ảnh Workspace chụp khi nội dung còn mờ lúc chuyển trang, ảnh bước tiếp có hộp thoại; không dùng chúng khẳng định đã nghiệm thu độ dễ đọc/toàn bộ nhãn tiếng Việt. Số đo máy T01/T03 không giảm số thao tác, T02 từ5 xuống4; không suy thành tiết kiệm thời gian của nhân viên.

Giữ bằng chứng lỗi, không giảm assert: UAT39458034247/dba7604 FAIL vì ca Chrome tìm nút Thu tiền cũ trên Customer; đã cập nhật đúng tên Ghi nhận khách trả tiền, giữ kiểm mất phản hồi/retry/một PE. Xem ảnh lượt đó phát hiện quản trị vẫn thấy Workspace cũ; sửa tham chiếu hidden, có unit/HTTP và ảnh mới đối chiếu. Cổng3 [39461556488/lượt1](https://github.com/tienduongmarcom/aphvh/actions/runs/39461556488/attempts/1) FAIL vì MySQL1020 tại kho_chuan.dung cập nhật tabCompany trên IMAGE NỀN0.16.2, trước nâng ứng viên; giữ log/artifact lượt1 tại work/ci-toi-uu-12d9d24/cong3, chạy lại cùng SHA lượt2 đạt; không tuyên bố đã sửa gốc xung đột này. Các lượt hủy khi bổ sung mã không là PASS. Hai ca Chrome chập chờn từ hồ sơ Claude tiếp tục theo dõi, không kết luận đã chữa chỉ vì lượt này xanh.

Còn lại: duyệt/gộp PR và phát hành theo runbook khi chủ dự án chọn; chủ dự án tự gắn tag. Trước production phải diễn tập bản sao thực còn hạn, đúng image/commit/khach.json/cờ. Nghiệm thu với nhân sự, hàng/tồn và máy in thật để cuối theo yêu cầu. Công nợ trên đơn chỉ tổng hóa đơn số dư dương trong quyền, không phải số dư công nợ ròng; đối chiếu/chốt bằng báo cáo chuẩn. Tắt cờ không tự xóa metadata hoặc khôi phục mọi cấu hình Sidebar. Hướng dẫn và ca nghiệm thu: `docs/huong-dan-giao-dien-0163.md`; phạm vi9 nhóm: `docs/dac-ta-toi-uu-giao-dien-0163.md`.

### Nhật ký các mốc trước — không thay trạng thái mới nhất ở trên

## 20/10/2026 — ĐANG KIỂM: ẩn tường minh màn cũ cho cả quản trị

Đã xem ảnh xuat-ngay-retry.png của dba7604: nhãn Vận hành/DBC/thông tin khách/cột mã–tên đã có, nhưng Administrator vẫn thấy Trung tâm cũ. Nguồn Frappe16.52 cho Workspace Manager xem is_hidden, nên cấu hình Custom Sidebar bổ sung tham chiếu hidden cho đúng các Workspace cũ thuộc module; không sửa quyền/xóa trang hay ẩn trang riêng. Unit454 (14 skip) đạt, mở rộng HTTP giữ kiểm năm màn mới và tham chiếu cũ ẩn. Các lượt69131a7 hủy khi đang chuẩn bị image do bổ sung này; không là PASS. Cần bốn cổng/ảnh đúng mã mới trước kết luận; production0.16.2 giữ nguyên.

## 20/10/2026 — ĐANG KIỂM: đồng bộ ca Chrome với cửa thu tiền đã gom

UAT39458034247 tại dba7604 FAIL ở DESK_2B_CASHIER_LOST_RESPONSE: selector còn tìm nút Thu tiền cũ trên Customer, trong khi UX chỉ giữ Ghi nhận khách trả tiền. Sửa đúng hai điểm chọn nút, không đổi thao tác thu/gửi lại hoặc assert một PE/không thêm GL/PLE, không sửa mã nghiệp vụ để né lỗi. Log và artifact FAIL giữ tại work/ci-toi-uu-dba7604 và work/reports. Cổng2 39458030862 và2b39458019691 success dba7604; Cổng3 còn chạy, chưa kết luận toàn bộ. Thêm hướng dẫn docs/huong-dan-giao-dien-0163.md; production vẫn0.16.2, chưa tag/deploy. Bước tiếp: chạy lại bốn cổng đúng mã có selector mới, xem ảnh và đối chiếu bằng chứng.

## 20/10/2026 — Cấp số DBC cho đơn chung mới trong ứng viên0.16.3

Theo quy tắc tên trung lập, đổi autoname cấp số mới sang DBC; số cũ/ID/Link giữ nguyên, không backfill. PR #26 vẫn đang kiểm, chưa phát hành/tag/VM; production0.16.2 giữ nguyên. Không lấy PASS của mã trước Sidebar/tiền tố mới làm PASS mã hiện tại.

## 20/10/2026 — Ứng viên0.16.3 bổ sung cấu hình thanh bên, đang kiểm

PR #26 bổ sung `Custom Sidebar` chuẩn sau khi dựng đủ năm Workspace: nhãn Vận hành, chỉ ẩn lối tự sinh do package sở hữu, giữ nguồn/liên kết/tùy chỉnh riêng. Không Core patch, không thêm cờ hoặc quyền. Cục bộ454 test (14 skip) +108 lõi đạt;4cổng/ảnh cho mã này còn kiểm. Cổng2/2b ở mã trước Sidebar8a5e003 success, không coi là PASS bản mới. Chưa phát hành/tag/VM; production vẫn0.16.2/digest34a32f71…/28cờ.

## 20/10/2026 — PR #26 tối ưu giao diện đang kiểm, chưa có bản phát hành mới

Nhánh `feat/toi-uu-giao-dien-20261020`, mã nghiệp vụ đầu `cc616a3`: năm khu, Nhà máy riêng, nhận diện khách/hàng rõ, công nợ hóa đơn gọn, thu tiền cùng service, giảm điều hướng/nút trùng và chuẩn nhãn chung. Không sửa GL/SLE/PLE, cờ/quyền, số đơn hoặc mẫu3liên. Cục bộ453 test (14 skip) và108 lõi đạt; ĐANG DỞ kiểm4cổng/ảnh đúng SHA, chưa PASS CI. Production giữ0.16.2/digest34a32f71…/28cờ, không tag/deploy. Chi tiết tại đầu docs/ban-giao.md; không lấy bằng chứng0.16.2 thay cho ứng viên.

## 20/10/2026 — Codex đã nhận hồ sơ, chưa có ứng viên phát hành mới

Đối chiếu main `7dcff5a`/PR#25 chỉ tài liệu. Đã kiểm trạng thái4 cổng và phát hành0.16.2 đúng95a8b1e, Cổng3 mốc0.16.2 đúnge062287; đã tải/đọc artifact UAT39427294383. Nhánh tiếp nối `feat/toi-uu-giao-dien-20261020` hiện chỉ ghi phạm vi hội thoại tại `docs/dac-ta-toi-uu-giao-dien-0163.md`, chưa sửa code/schema/quyền, không version/tag/phát hành/VM. Production giữ0.16.2/digest34a32f71…/28cờ theo hồ sơ, không dùng bằng chứng cũ làm PASS cho mã mới. ĐANG DỞ: chuẩn tên và làm gọn theo yêu cầu mới; Nhà máy riêng, thông tin khách/hàng luôn rõ, công nợ gọn; mẫu3liên chưa duyệt.

## 20/10/2026 ~21:35 — Production 0.16.2 đã triển khai ĐẠT (mốc bàn giao Claude → Codex)

Anh Tiến chạy trên `erpnext-prod/frontend`: diễn tập bản sao rồi `=== XONG 0.16.2: ĐẠT ===`. Image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.2`
digest **`sha256:34a32f71f10f20421405c0bd1155abb0570b1d48b564f1df6b8e25d6aa146917`**, workflow phát hành 39432250494, nguồn tag `v0.16.2` =
`95a8b1e63358b190faccfa300010445ee799cac9` (main). 4 cổng trên 95a8b1e: UAT 39427294383, Cổng 2 39427281958, 2b 39427285899, Cổng 3 39427290220.
28 cờ giữ nguyên, không cờ mới. Cổng 3 đã đổi mốc sang 0.16.2 (run 39441058175, PR #24, main 72e6a0b).

Trước đó cùng ngày: **0.16.1** (tag cfdd5af, phát hành 39394763705) lần 1 tự quay lui oan về 0.16.0 do SIGPIPE trong `nang-cap.sh`
(kiểm thực tế `KHÔNG ĐẠT: 0`); sửa PR #22 (62668ab), lần 2 ĐẠT, so sổ KHỚP. Digest 0.16.1 không được ghi lại.
Quay lui có điều kiện: 0.16.0 `sha256:ce8db011…` hoặc bản sao lưu lúc nâng 0.16.2 trong `~/erp/aph-vh/sao-luu/`; không restore sau khi
đã có giao dịch mới. Chi tiết, việc còn mở và lưu ý tiếp nối: mục đầu `docs/ban-giao.md`.

## 20/10/2026 — Production 0.16.0 đã triển khai ĐẠT

Anh Tiến chạy trên `erpnext-prod/frontend`: diễn tập bản sao rồi `=== XONG 0.16.0: ĐẠT ===`. Image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.16.0`
digest **`sha256:ce8db011338a7f6f521107999ee515a94366deeb7c96a50b2570376b903ccbf3`**, workflow phát hành 39375471396 (UAT/Cổng 2/2b/3
đạt trong workflow), nguồn tag `v0.16.0` = `457be4af64157f40b5a71c8065c0d13b7914ce8b` (nhánh PR #19, chuỗi PR #9–#19 chưa gộp main).
28 cờ bật: 21 cũ + cash_custody, cash_closing, cash_handover, factory_handover, factory_receiving, factory_production, ux_task_first.
Quay lui có điều kiện: 0.15.3 `sha256:330607a2…` + bản sao lưu lúc nâng; không restore sau khi đã có giao dịch mới.
Bước tiếp: gộp PR #9–#19 vào main; đổi baseline Cổng 3 sang 0.16.0/digest trên (chưa đổi); áp Workspace mới cho người dùng; nghiệm thu người thật.

## 20/10/2026 — Claude: PR #19 (NM01c/NM02–05, UX-01) đang kiểm, production vẫn 0.15.3

Mã kiểm cuối `a3cfd6d` đủ 4 cổng (UAT 39368636121, b014 117 PASS/0 FAIL; Cổng 3 39368638182). Thêm cờ 27 `kh_aph_factory_production`, 28 `kh_aph_ux_task_first` (mặc định tắt, đồng bộ FLAGS/quay-lui/dấu vân/preflight/Cổng 3). Chưa tag/phát hành. Chi tiết `docs/ban-giao.md`.

## 20/10/2026 — Bàn giao tiếp nối cho Claude theo yêu cầu chủ dự án

Chủ dự án chuyển phần việc tiếp theo và rà lỗi độc lập cho Claude; sau khi Claude hoàn thành sẽ bàn giao ngược cho Codex. Hồ sơ tập trung: `docs/BAN_GIAO_CHO_CLAUDE.md`, gồm baseline e929498/mã kiểm a75ced9, PR #18,4 cổng/293 HTTP và giới hạn, vùng cần rà độc lập, thứ tự phần còn lại và mẫu bằng chứng bàn giao ngược. Đây là commit hồ sơ, không thay code/quyền/schema/production. Production theo xác nhận vẫn0.15.3; nghiệm thu dữ liệu/nhân sự thật vẫn gom cuối. Codex dừng phát triển tại đây để Claude tiếp nối; không coi các vùng cần rà là lỗi đã xác nhận hoặc phần chưa làm là đã hoàn tất.

## 20/10/2026 — Nhận chờ định giá theo đơn mua 3B đã kiểm đủ bốn cổng

[PR #18](https://github.com/tienduongmarcom/aphvh/pull/18), nhánh `feat/nhan-cho-gia-theo-don-mua-20261020`, base PR #17/4b638b0. Mã nghiệp vụ/kiểm cuối **`a75ced9b8b4613d71fe45117bc36b7215f85877d`**. Cùng cửa sổ nhà máy chọn nhận có giá hoặc chờ giá; pending lưu đúng PO/dòng nguồn, người thực nhận, actor/thời điểm, tệp cân private và phần có vấn đề trong tổng lượng. Giữ chỗ lượng chờ trên cả PR chuẩn/PI update_stock, kể cả tắt26. Người có quyền mua cập nhật PO; KTT chốt đúng giá PO qua một PR native, không ghi kho giá0. Hủy PR trả giữ chỗ, hủy pending sau đó giải phóng nhưng giữ hồ sơ. Chỉ miễn đúng backlink pending nguồn khi native hủy PR; mọi backlink khác vẫn kiểm.

Cục bộ **419 kh_aph +108 lab9x** đạt, Python/JS/diff đạt. Bốn cổng success cùng mã cuối: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39350330165), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39350329373), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39350325419), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39350333813). Commit hồ sơ sau đó chỉ đổi tài liệu/AGENTS, không là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact tại `work/ci-pending-a75ced9/`: **293 HTTP/Desk PASS,0 FAIL**, b014102; core63.508 tệp không đổi, hai kiểm kỹ thuật core/site trắng PASS. ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Đủ8 ca mới: giữ chỗ/replay/tệp; PR và PI native khi26=0; chặn đổi mode/giả giá/gỡ nguồn/giảm hoặc hủy PO; hai phiên pending/có giá chỉ một nhận4kg khi còn6; finalize một PR4kg đúng dòng/giá PO; hủy giữ lịch sử; mã chưa có lịch sử giá/PO.rate0 chỉ nhận pending; Chrome bỏ200 sau commit rồi bấm lại một pending1kg/không thêm sổ. Luồng pending cũ không PO cũng PASS: ngoài khả dụng, chặn giá0/vai trò và gán Link native, finalize nguyên tử/retry.11 bản ghi khôi phục baseline đều PASS, gồm pending/child/PI/File/Series.

Đã xem `nha-may-nhan-cho-gia.png`: phiếu09k5kg7mr0 Submitted, PO PUR-ORD-2026-00004,1kg ở trạng thái Chờ định giá, người thực nhận/người nhập/thời điểm rõ; không hiện giá vốn hoặc nút chốt giá cho NoCost. Dữ liệu/tài khoản đều giả. Cổng2b đã đọc log:20 probe nghiêm sau mở bảo trì, kéo image lỗi giữ bản B/web pong, quay lui ci-b→ci-a, kiểm53 dòng/0 lỗi.

Cổng3 đã đọc artifact: schema nâng/site mới **1.085/1.085**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp. Năm cờ mới custody/closing/handover/factory_handover/factory_receiving về0,21 cờ cũ giữ1. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp, workflow kiểm maintenance_mode=1. Nền CI GL0 không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ FAIL [38318ab/UAT39346121476](https://github.com/tienduongmarcom/aphvh/actions/runs/39346121476):2 ca3B đầu PASS, fixture sửa PO thiếu item_code nên native bỏ qua/trả rỗng và helper lỗi KeyError. Sửa payload đủ mã/ngày/mô tả, đọc phản hồi rỗng đúng API, giữ assert giảm PO phải bị chặn/dữ liệu không đổi. Giữ FAIL [02d9a70/UAT39348470916](https://github.com/tienduongmarcom/aphvh/actions/runs/39348470916):6 ca đầu PASS; PO mới cho ItemA tự điền giá mua gần nhất, trái giả định fixture.rate0. Sửa dùng mã mới chưa có lịch sử giá; giữ assert PO.rate0/chặn nhập có giá/finalize0, không giảm assertion/số ca. Artifact/log hai FAIL giữ tại work/ci-pending-38318ab và work/ci-pending-02d9a70. Các lượt0c8d884/8e71fa4 hủy khi bổ sung current-read/capability/tiền tệ và đúng actor fixture, không dùng làm bằng chứng cuối.

Đặc tả9 nhóm và bảng truy nguyên8 ca: `docs/dac-ta-nhan-cho-gia-theo-don-mua-3b.md`; hướng dẫn nhân sự: `docs/huong-dan-nhan-hang-nha-may.md`. Lát3B chỉ PO VND/tỷ giá1, hàng tồn Kg/hệ số1, không lô/sê-ri/gia công/giao thẳng. Pending cũ không tự backfill PO; lượng chờ chưa khả dụng; dấu cần đàm phán là snapshot, không workflow giải quyết giá. Tái dùng26 mặc định tắt, không core patch/ignore_permissions/version/tag/merge/deploy. Production theo xác nhận vẫn0.15.3/21 cờ.

**ĐANG DỞ toàn đợt3:** nhận chuyển đến NM01c, sản xuất/dở dang/đóng gói/xuất và bảng ngày nhà máy còn tiếp theo `docs/dot-3-ra-soat-nguon-nha-may.md`. Bước tiếp: đặc tả9 nhóm nhận chuyến chuyển, phân biệt cùng Company với giao dịch khác Company, giữ nguồn/đang chuyển/đã nhận trên chứng từ chuẩn và chống nhận trùng. Chưa gọi toàn NM01 hoặc đợt3 hoàn tất; nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối.

## 20/10/2026 — Nhận nhanh nhà máy 3A đã kiểm đủ bốn cổng

[PR #17](https://github.com/tienduongmarcom/aphvh/pull/17), nhánh `feat/nhan-hang-nha-may-20261019`, base PR #16/565910a. Mã nghiệp vụ/kiểm cuối **`1fffcbaa9b40faf5b33fe246a6d4c7faf68c7b61`**. Nhận Kg từ đơn mua có giá qua Dialog trên PO hoặc Tồn kho số lượng; tạo một Purchase Receipt chuẩn, ghi người thực nhận, tệp cân riêng tư, ghi chú và phần hàng cần đàm phán trong tổng lượng nhận. Theo quyết định chủ dự án: hàng có vấn đề thường dùng ngay, giá điều chỉnh sau; không tự trả hàng/giảm giá. Cờ26 `kh_aph_factory_receiving` mặc định tắt; không bypass quyền hoặc mở giá vốn cho nhà máy.

Cục bộ **405 kh_aph +108 lab9x** đạt, JS/diff đạt. Cả bốn cổng success đúng mã trên: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39281475156), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39281543596), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39281539311), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39281548157). Commit hồ sơ tiếp theo chỉ đổi tài liệu; không coi đó là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact tại `work/ci-receiving-1fffcba/`: **285 HTTP/Desk PASS,0 FAIL**, b01494; hai kiểm kỹ thuật core/site trắng PASS. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Năm ca mới kiểm quyền/preview chỉ lượng, nhận4kg còn6 và retry một phiếu, chặn giá client/kho sai/sửa dấu, hai phiên chỉ một nhận4kg còn2, Chrome bỏ phản hồi200 sau commit rồi bấm lại cùng Dialog chỉ một PR/một SLE còn1. Tệp cân thật trong UAT giữ private và gắn đúng PR. Đã xem ảnh `nha-may-nhan-hang.png`: PR MAT-PRE-2026-00003 hoàn tất, lượng1kg, người thực nhận/người nhập/thời điểm được lưu, không hiện giá vốn trên form của vai trò bị hạn chế.

Cổng2b đã đọc log: kiểm ping nghiêm sau mở bảo trì, kéo image không tồn tại giữ bản B/web pong, quay lui ci-b→ci-a, kiểm53 dòng/0 lỗi. Cổng3 đã đọc artifact: schema nâng/site mới **1.074/1.074**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp. Năm cờ mới custody/closing/handover/factory_handover/factory_receiving trả0,21 cờ cũ giữ1. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Nền CI GL0 không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ lịch sử lỗi: [be6a44b UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39273247208) FAIL MariaDB1020 ở ca hai phiên; sửa bằng retry_rpc hiện có tại biên receive, rollback/thử lại toàn hàm có giới hạn, không retry lỗi nghiệp vụ. [a7bc040 UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39276735273) bốn HTTP mới PASS nhưng Chrome FAIL404 asset; sửa report dùng native render_include, chung nguồn JS với PO, không thêm build/core patch. Bản cuối kiểm cả script được include và File riêng tư; không giảm assertion/số ca. Các lượt b31c976 hủy khi bổ sung current-read/khóa và bảo vệ hồ sơ, không dùng làm bằng chứng bản cuối.

**ĐANG DỞ toàn đợt3:** lát3A mới nhận hàng Kg từ PO có giá hợp lệ, không lô/sê-ri/gia công/giao thẳng. Chưa hoàn tất NM01 hoặc toàn nhà máy. Bước tiếp: đặc tả rồi nối nhận chờ định giá theo từng dòng PO, giữ chỗ lượng giữa pending và PR; sau đó nhận chuyển đến, sản xuất/dở dang/đóng gói/xuất và bảng ngày theo `docs/dot-3-ra-soat-nguon-nha-may.md`. Nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối. Chưa tăng version/tag/merge/deploy; production theo xác nhận vẫn0.15.3/21 cờ.

## 19/10/2026 — Quỹ nhà máy, chốt ca cá nhân và bảng ngày đã kiểm đủ bốn cổng

Nhánh `feat/hoan-tat-quy-nha-may-20261019`, [PR #16](https://github.com/tienduongmarcom/aphvh/pull/16), base PR #15/35d7d42. Mã nghiệp vụ/kiểm cuối **`d0c1f16fb7287da84066f9142bc304be2f616918`**. Nối nguồn quỹ nhà máy với một bàn giao/giữ chỗ/đối chiếu/hoàn chung; chốt ca tự thân và bảng native Chốt ngày và cần xử lý. Không cấp GL/JE/H/snapshot native cho nhà máy hoặc sửa C.guard. Cờ25 `kh_aph_factory_handover` mặc định tắt. Không version/tag/merge/deploy; production theo xác nhận vận hành vẫn0.15.3/21 cờ.

Cục bộ **394 kh_aph +108 lab9x** đạt, Python/JS/diff đạt. Bốn cổng đúngd0c1f16: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39264983886), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39264983968), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39264977970), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39264989203). Cả bốn cổng đều success đúng mã nghiệp vụ/kiểm này; đã đọc artifact và xem ảnh. Commit hồ sơ sau đó chỉ đổi tài liệu/AGENTS, không là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact UAT đúngd0c1f16: **280 HTTP/Desk PASS,0 FAIL**, b01489; hai kiểm kỹ thuật core/site trắng cũng PASS. Core63.508 tệp không đổi, ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Đã xem `nha-may-chot-ca.png`: nguồn nhận25/30 ở trạng thái Chênh lệch đã đối chiếu, phiên nhà máy tự chốt và retry trả ca u5ig2j8g1g; chỉ một ca. Đã xem `chot-ngay.png`: report native đủ8 nhóm, dòng cần xác minh vẫn còn, không popup che bảng. Dữ liệu đều giả. Cổng2b đã đọc log:20 probe nghiêm sau mở bảo trì, kéo image không tồn tại không đổi bản B/web vẫn pong, quay lui ci-b→ci-a và kiểm53 dòng/0 lỗi.

Cổng3 đúngd0c1f16 đã tải/đọc artifact `cong-3-bang-chung`: schema nâng/site mới **1.065/1.065**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp. Bốn cờ custody/closing/handover/factory_handover từ1 trả về0,21 cờ cũ giữ1. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp, log giữ bảo trì và workflow kiểm maintenance_mode=1. Nền CI có GL0; không thay diễn tập bản sao production có dữ liệu khi phát hành.

Bản trước b375ff0 đã đủ4 cổng, **280 HTTP/Desk PASS,0 FAIL**, b01489; artifact UAT/Cổng3 đã tải/đọc, ảnh ca nhà máy và bảng ngày đã xem. QA ảnh phát hiện report hiện popup che bảng: ValidationError đã chuyển thành dòng cần xác minh vẫn còn trong message_log. d0c1f16 chỉ gỡ thông báo mới của lỗi đã xử lý, giữ thông báo trước và không nuốt PermissionError; thêm unit và Chrome assert không popup. Ảnh mới d0c1f16 đã kiểm như trên; không dùng ảnh b375 làm bằng chứng giao diện sạch.

12 ca mới kiểm: nguồn cũ đã nhận giữ nguyên/chờ phải chuyển tiếp; một H giữ chỗ; hai phiên qua lối cũ và native chỉ một JE/hai GL, không PE/PLE mới; cùng Cash thiếu5 không JE; hoàn Cash/Bank đúng người nhà máy không cấp GL; mốc mới+ca+tệp đóng vụ; hủy giữ chỗ giữ lịch sử; tự chốt/retry/đổi nội dung/nháp lỗi thời; Chrome bỏ200 sau lưu nháp và chốt rồi retry cùng cửa sổ; bảng ngày đúng quyền/tiền/ca/sao kê native/hàng/nợ và chỉ đọc. Đặc tả9 nhóm cùng bảng truy nguyên case tại `docs/dac-ta-hoan-tat-quy-nha-may-2b.md`.

Giữ FAIL [39234474071/28aad95](https://github.com/tienduongmarcom/aphvh/actions/runs/39234474071):77 ca cũ PASS, ConnectionResetError lúc chờ web sau bật cờ25; sửa chỉ readiness/luôn trả cờ finally và trace, không retry mù nghiệp vụ. Các lượt44e1bb hủy khi bổ sung User Permission nguồn và chặn phản hồi UI cũ; c53301d hủy khi bổ sung ngoại lệ đúng backlink nguồn khi cancel. Native Frappe16.52 kiểm backlink sau cancel: chỉ miễn đúng bản nguồn gương dưới capability, mọi backlink tĩnh/động khác vẫn kiểm. Không giảm assertion hoặc số ca.

Tiền/cọc/việc tồn theo hiện tại; thực đếm ghi thời điểm ca gần nhất, nợ đến ngày chọn. Sao kê chỉ từ Bank Transaction native đã lưu; kết quả đối chiếu tệp tạm chưa có lịch sử lưu, không tự coi đã khớp. Nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Khi phát hành vẫn diễn tập bản sao production có dữ liệu và rollback image+DB/files+cờ đồng thời; không tắt riêng cờ để xóa projection. Bước tiếp theo: rà nguồn và lập đặc tả9 nhóm cho đợt3 màn nhập lượng một lần, bắt đầu nhận hàng/phiếu cân rồi sản xuất–đóng gói–xuất; tái dùng nghiệp vụ nền. Đợt4 chốt toàn chuỗi còn tiếp; đợt5 hóa đơn một phần phải chốt đặc tả riêng.

## 19/10/2026 — Tiền cá nhân chỉ đọc đã kiểm đủ bốn cổng

Nhánh `feat/tien-ca-nhan-20261019`, [PR #15](https://github.com/tienduongmarcom/aphvh/pull/15), base PR #14/a50f5f1. Mã nghiệp vụ/kiểm cuối **`fe3140ad38e3febea317a32f07b1aee7f0b6969a`**. Không tăng version/tag/merge/deploy, không thêm schema/cờ/DocPerm. Production theo xác nhận người vận hành vẫn0.15.3/21 cờ; candidate24 cờ, ba cờ tiền mới mặc định tắt.

Facade `personal_cash.accounts/current` và Dialog **Tiền tôi đang giữ** trên Khách hàng/Phiếu quỹ nhà máy chỉ xem số trách nhiệm, giữ chỗ, khả dụng của session đang đăng nhập. Dùng chung công thức/mốc/khóa Cash với chốt ca và delta bàn giao; không suy owner. NoCost/nhà máy kể cả cộng quản lý chỉ quỹ cấu hình, kiểm Company/Account User Permission. Chỉ đọc cột Cash/metadata nội bộ, không trả GL/nguồn/đối ứng/phân bổ người khác hoặc cấp quyền GL/chốt/nhận/hoàn. Giữ quyền JE native có sẵn: không suy NoCost cộng Accounts Manager bị chặn mọi JE. Đổi Company/quỹ xóa số cũ và bỏ phản hồi lỗi thời. Sửa cleanup Dialog chênh lệch giao nhận từ finally sang always theo jqXHR nền ghim; chưa kiểm riêng mất phản hồi ở lối chênh lệch này.

Cục bộ **375 kh_aph +108 lab9x** đạt, Python/JS/diff đạt. Đúngfe3140a: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39226640207), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39226651607), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39226647318), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39226655570) đều success. Commit hồ sơ sau mã này chỉ đổi tài liệu, không là mã nghiệp vụ được kiểm mới.

Đã tải/đọc artifact UAT đúngfe3140a: **268 HTTP/Desk PASS,0 FAIL**, b01477; hai kiểm kỹ thuật core/site trắng cũng PASS. Năm ca mới kiểm scope/no GL, nguồn nhà máy/PE/chưa rõ không suy owner, giữ chỗ đúng người và delta cùng Cash không thêm GL/PLE, Chrome dùng phiên nhà máy giả riêng/cùng principal server (không Administrator) bỏ200 rồi đọc lại/đổi APH→VH→APH, hủy sau mốc/vụ lệch riêng người/mốc lỗi phải xác minh. Đã xem `tien-ca-nhan.png`:332/0/332, readonly, form sạch, chỉ đúng quỹ. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11/kh_aph0.15.3. Đây là dữ liệu UAT giả.

Cổng2b đã đọc log:20 probe nghiêm sau mở bảo trì, image không tồn tại không gián đoạn web, quay lui ci-b→ci-a và kiểm53 dòng/0 lỗi. Cổng3 đã tải/đọc artifact `cong-3-bang-chung`: schema nâng/site mới **1.065/1.065**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ tiền về0. Ca cố ý lỗi tự quay về0.15.3, đếm/tổng/chi tiết/versions khớp, log giữ bảo trì và workflow kiểm maintenance_mode=1. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL: [39199145864/874aa53](https://github.com/tienduongmarcom/aphvh/actions/runs/39199145864) cleanup native delete không có message, sửa caller raw; [39201881053/4651d2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39201881053) Chrome chưa bắt được phản hồi, bổ sung principal server/API probe/chẩn đoán và chờ form sẵn sàng; [39221412038/7978ad5](https://github.com/tienduongmarcom/aphvh/actions/runs/39221412038) bộ thử đọc Currency readonly0 qua get_value thành undefined/NaN, sửa kiểm số gốc0 và vùng hiển thị đúng control Frappe16.52.0, không mặc định undefined thành0; [39224149992/3b64df6](https://github.com/tienduongmarcom/aphvh/actions/runs/39224149992) Chrome đã PASS nhưng HTTP dùng lại cookie đã khởi tạo CSRF trong Desk, sửa tách hai phiên cùng nhân sự giả. Không tắt CSRF/giảm assertion/số ca. Các lượt cũ hủy khi đổi mã không thay bằng chứng cuối.

**ĐANG DỞ đợt2B:** bước nền xem tiền đã kiểm kỹ thuật; adapter phiếu quỹ nhà máy sang giữ chỗ/đối chiếu chung, quyền tự chốt/nhận/hoàn nhà máy và bảng chốt ngày/ngoại lệ còn tiếp. Đặc tả9 nhóm và điều kiện adapter kế tiếp tại `docs/dac-ta-tien-ca-nhan-2b.md`. Bước tiếp chốt quỹ nhận trước gửi, một H duy nhất nối nguồn factory, các lối nhận cùng một JE/state atomic; giữ ca cũ đã nhận, xử lý chuyển tiếp ca chờ thiếu mốc/người. Không mở guard/GL để vượt NoCost. Nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Khi phát hành vẫn diễn tập bản sao production có dữ liệu và rollback snapshot/image/cờ theo runbook; không tắt riêng bàn giao để xóa projection.


## 19/10/2026 — Thu quầy/quỹ cũ và bảo trì đã kiểm đủ bốn cổng

Nhánh `feat/thu-quay-quy-nha-may-20261019`, [PR #14](https://github.com/tienduongmarcom/aphvh/pull/14), base PR #13/2618e72. Mã cuối **`c02c3764dae495a48b564931062cbae3e78d9db3`**. Không tăng version/tag/merge/deploy; production theo xác nhận gần nhất vẫn0.15.3/21 cờ.

Thu quầy có mã lượt theo người gọi + Company, dấu nội dung ngay trên PE và khóa Company xuyên suốt hai hình thức thu. Gửi lại nguyên cửa sổ trả đúng PE cũ; đổi nội dung/hủy phiếu không tự ghi thu lại. Server chặn giả/sửa/sao chép/xóa dấu; không backfill hay suy người giữ từ owner. Khi custody bật, caller quầy phải gửi request_id. Đóng/mở lại hoặc tải lại trang tạo lượt mới: nhân viên cần kiểm phiếu đã thu trước khi thu tiếp.

Quỹ nhà máy cũ chặn người lập/người giữ tự nhận và quản lý/Admin nhận thay; đúng người nhận gửi lại cùng số/tài khoản trả kết quả cũ, không tạo JE lần nữa. Chưa phải adapter đầy đủ sang giữ chỗ/đối chiếu mới. Không cấp GL cho nhà máy. Thủ tục nâng cấp nạp lại backend sau bật/tắt bảo trì, khắc phục cache site_config TTL60 từng web worker trước sao lưu/mở lại; Cổng2b kiểm thêm20 probe nghiêm, không retry/bỏ qua503.

Cục bộ **365 kh_aph +108 lab9x** đạt, Python/JS/shell/diff đạt. Đúngc02: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39195670324), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39195680580), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39195678186) và [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39195684243) đều success.

Đã tải/đọc artifact UAT đúngc02: **263 HTTP/Desk PASS,0 FAIL**, b01472; hai kiểm kỹ thuật core/site trắng cũng PASS. Core63.508 tệp không đổi, ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11. Ba ca HTTP mới kiểm retry/đổi nội dung, hai phiên cùng lượt tiền mặt+bank chỉ hai PE, giả dấu/hủy/giữ lịch sử. Chrome cố ý bỏ HTTP200 sau commit rồi gửi lại cùng Dialog, một PE và GL/PLE không tăng lần nữa. Đã xem thu-quay.png: form khách native, toast Đã ghi ACC-PAY-2026-00008, không lỗi. Cổng2b đã đọc log:20 probe nghiêm, kéo image không tồn tại không gián đoạn web, khôi phục ci-b vềci-a đạt.

Cổng3 đúngc02 đã tải/đọc artifact: schema nâng/site mới **1.065/1.065**, lệch0, bỏ qua6/6; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ custody/closing/handover về0. Ca cố ý lỗi tự khôi phục đúng0.15.3, đếm/tổng/chi tiết/versions khớp và workflow kiểm maintenance_mode=1. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL: [39190026643/a6fae60](https://github.com/tienduongmarcom/aphvh/actions/runs/39190026643) dùng finally trên jqXHR, sửa always theo request.js Frappe16.52.0; [39192414323/db2201f](https://github.com/tienduongmarcom/aphvh/actions/runs/39192414323) một worker pong rồi worker khác503 do cache bảo trì, sửa nạp lại backend; [39193896826/b7](https://github.com/tienduongmarcom/aphvh/actions/runs/39193896826) cả263 ca parsedPASS nhưng grep đếm thiếu dòng Chrome compactJSON, sửa chuẩn hóa qua emit và assert đúng một case PASS, giữ nguyên số72/assertion. Các lượt hủy khi đổi mã/trùng Cổng2 không dùng làm bằng chứng cuối.

**ĐANG DỞ đợt2B:** nối đầy đủ quỹ nhà máy vào giữ chỗ/đối chiếu và quyền tiền cá nhân tối thiểu không GL, sau đó bảng chốt ngày/ngoại lệ. Cần rà cách hoàn tất Dialog chênh lệch giao nhận còn dùng then(...).finally theo cùng phiên bản; chưa kiểm riêng tình huống mất phản hồi của lối đó. Đặc tả9 nhóm: `docs/dac-ta-thu-quay-quy-cu-2b.md`. Nghiệm thu nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Bước tiếp theo: đặc tả và nối adapter quỹ nhà máy vào cùng nguồn giữ chỗ/đối chiếu, xây giao diện tiền cá nhân tối thiểu; không cấp GL để vượt chặn NoCost.

## 19/10/2026 — Đối chiếu lệch và hoàn bàn giao đã kiểm đủ bốn cổng

Nhánh `feat/xu-ly-lech-hoan-tien-20261019`, [PR #13](https://github.com/tienduongmarcom/aphvh/pull/13), base PR #12 (6431ec0). Mã nghiệp vụ/kiểm **`8fc93b7a1b674aee3722fe7b1f59de760a2f088d`**. Cờ24 `kh_aph_cash_handover` mặc định tắt, cần custody/closing. Không tăng version/tag/merge/deploy: production vẫn0.15.3/21 cờ, các PR #9–#13 chưa phát hành.

Đã có hai DocType native `APH Doi chieu lech tien` + `APH Can cu doi chieu quy`. Chốt vụ chỉ quản lý, cần xác minh mới sau vụ lệch và ca khớp còn hiệu lực của từng phía Cash, kết quả/tệp riêng tư; không tự tạo JE hoặc sửa số đếm/lệch cũ. Hủy đối chiếu mở lại chặn giao ra, giữ hồ sơ/tệp kể cả nguồn bàn giao đã hủy có quan sát. Ca cũ state trống vẫn được coi mở. Company/Account/GL/nguồn và NoCost cộng manager đều kiểm server; không cấp thêm GL.

Hoàn toàn bộ thực nhận bằng phiếu bàn giao ngược chiều mới: đúng người đã nhận tự gửi, người giao ban đầu tự nhận lại. Khóa tiền/giữ chỗ/kiểm nguồn đã dùng, mã yêu cầu giữ idempotency kể cả hủy rồi lập lại bằng mã mới. Cùng Cash chỉ đảo trách nhiệm; khác Cash hoặc Bank về Cash một native JE mới, JE gốc vẫn đã ghi sổ, không PE/PLE/131/doanh thu mới. Bank chỉ làm nguồn hoàn đúng gốc, không mở chi Bank tùy ý. Không hoàn từng phần hoặc hoàn tiếp phiếu hoàn. Hồ sơ đã gửi/hủy không xóa tay, kể cả Admin. Native Form/Workspace/Dialog có lối vào và lịch sử.

Cục bộ **358 kh_aph +108 lab9x** PASS, Python/JS/diff đạt. Đúng8fc93b7: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39186195911), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39186264582), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39186262143), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39186267181) đều success. Commit hồ sơ sau mã này chỉ đổi tài liệu, không là mã kiểm nghiệp vụ mới.

Đã tải/đọc artifact: **259 HTTP/Desk PASS,0 FAIL**, b01468, giữ249 ca trước và thêm10. Các ca mới: đóng/mở lại với mốc/ca/tệp, hai phiên chốt, ca lỗi thời, nguồn hủy; hoàn cùng Cash/khác Cash/Bank, hai phiên tạo/nhận, nguồn đã dùng bị chặn; Chrome mất phản hồi200 sau commit rồi retry cùng Dialog chỉ một phiếu giữ chỗ, không thêm JE/GL/PLE. Có kiểm hủy/lập lại theo mã mới, tệp trùng giữ URL/blob cũ, không xóa lịch sử. Đã xem `hoan-tien.png`: phiếu hoàn đã gửi/chờ nhận, form sạch và liên kết gốc; sau browser Python xác nhận nhận lại và số quỹ/sổ khớp. Đây là ảnh/dữ liệu giả. Core63.508 tệp không đổi; ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11.

Cổng3: schema nâng/site mới **1.063/1.063**, lệch0, bỏ qua6/6 mục; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ custody/closing/handover đều về0. Ca cố ý lỗi tự quay lui, đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Đã tải/đọc artifact `cong-3-bang-chung`. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ các FAIL, không bỏ assertion: [39176704265/d415cf3](https://github.com/tienduongmarcom/aphvh/actions/runs/39176704265) upload tệp cùng nội dung bị guard chặn vì native dedupe URL; đã cho File mới riêng tư tham chiếu byte-identical blob có quyền đọc, File cũ/sửa/xóa/công khai vẫn chặn. [39178203449/810fe9d](https://github.com/tienduongmarcom/aphvh/actions/runs/39178203449) native CancelledLinkError cho nguồn hủy; controller chỉ cho đúng source_name là bàn giao hủy có quan sát sau guard manager/quyền/phạm vi/khóa, giữ invalid link/child và link hủy khác; không ignore_links/core patch. [39184751627/033a89a](https://github.com/tienduongmarcom/aphvh/actions/runs/39184751627) equality phản hồi tạo hoàn đồng thời; đã chuẩn hóa Currency None/DB0 và JE rỗng, thêm unit fresh/loaded. Cả ba được kiểm lại trên8fc93b7; các lượt0b79558 hủy khi đổi mã không dùng làm bằng chứng cuối.

**ĐANG DỞ đợt2B:** adapter nhận quỹ nhà máy/thu quầy cũ, token thu cũ và quyền tiền cá nhân tối thiểu không GL còn thiếu. Bước tiếp nối các đường cũ, chặn tự nhận ở đó và chống ghi thu quầy lặp trước khi gọi tiền toàn cửa hàng hoàn tất; đợt3–4 vẫn theo kế hoạch, đợt5 cần chốt riêng. Đặc tả9 nhóm `docs/dac-ta-xu-ly-lech-hoan-tien-2b.md`. Nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật gom cuối theo anh Tiến. Không tắt riêng cờ bàn giao sau phát sinh để xóa projection; khôi phục snapshot/image/cờ theo runbook.

## 19/10/2026 — Bàn giao tiền đã kiểm đủ bốn cổng; đợt2B còn tiếp

Nhánh `feat/ban-giao-tien-20261018`, [PR #12](https://github.com/tienduongmarcom/aphvh/pull/12), base PR #11 (014c05a). Mã nghiệp vụ/kiểm **`1787448b02c5768b0f1b48ee71da7297f78e268e`**. Đã có Native DocType `APH Ban giao tien`, Workspace/Dialog; cờ24 `kh_aph_cash_handover` mặc định tắt, cần custody/closing. Không tăng version/tag/merge/triển khai, production vẫn0.15.3 với21 cờ.

Gửi giữ chỗ nguồn, đúng người nhận tự xác nhận số thực; không tự nhận/nhận thay kể cả Admin. Cùng Cash chỉ chuyển trách nhiệm, không GL/PLE; khác Cash/nộp Bank một native JE hai dòng tiền, không thu khách/giảm nợ lần nữa. Thiếu/thừa lưu lý do/người/hạn xử lý; vượt nguồn chỉ lưu số đếm, không chuyển. Hủy đề nghị chưa chuyển giải phóng giữ chỗ nhưng giữ vụ lệch và blob căn cứ. JE liên kết không sửa/gỡ/hủy tay; ca nháp kiểm lại khi trách nhiệm thay đổi. Ví có lệch chưa xử lý hoặc bất kỳ nhóm trách nhiệm/chưa rõ âm bị chặn giao ra, không suy người đã chi.

Cục bộ **338 kh_aph +108 lab9x** đạt, cú pháp Python/JS và diff đạt. Đúng1787448: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39145460833), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39145541665), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39145540867) và [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39145543386) đều success.

Đã tải/đọc artifact UAT: **249 HTTP/Desk PASS,0 FAIL**, b01458; hai kiểm kỹ thuật core/site trắng cũng PASS. Bảy ca bàn giao đạt: giữ chỗ/cùng Cash không sổ; thực95/100 và retry không đổi nội dung; chuyển Cash; nộp Bank; hai đề nghị tranh nguồn/hai phiên nhận chỉ một JE; vượt nguồn và quyền; Chrome mất phản hồi sau commit rồi nhận lại cùng Dialog không thêm JE/GL/PLE. Trong các ca có thêm nhận25/20,0/10, tệp/vụ lệch giữ sau hủy, nhóm chưa rõ âm chặn giao. Đã xem ảnh `ban-giao-tien.png` đúng mã cuối, hồ sơ sạch/đã nhận/thực20/bút toán liên kết. Core63.508 tệp không đổi, ERPNext16.51.1/Frappe16.52.0/lab9x0.2.11.

Cổng3: schema nâng/site mới **1.061/1.061**, lệch0, bỏ qua6/6 mục; rollback **1.052/1.052**, đếm/tổng/cờ/versions/cài đặt/giao diện khớp, ba cờ custody/closing/handover đều về0. Ca cố ý lỗi tự quay lui, đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Đã đọc artifact `cong-3-bang-chung`. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ bằng chứng lỗi [UAT39141849273](https://github.com/tienduongmarcom/aphvh/actions/runs/39141849273), mã3dadd51: MariaDB1020 ở hai phiên gửi. Đã sửa retry tối đa3 lần tại đúng biên RPC, rollback toàn lần thử, không retry ValidationError/không rollback caller nội bộ; giữ nguyên assertion đồng thời. Mã cuối kiểm lại đạt, không dùng PASS của PR #11 thay cho mã mới.

**ĐANG DỞ đợt2B:** chưa có đảo bàn giao/đóng vụ lệch, adapter nhà máy/thu quầy cũ, idempotency thu quầy cũ hoặc quyền tiền cá nhân không GL. Không coi tiền toàn cửa hàng hoàn tất. Bước tiếp: thiết kế xử lý kết quả lệch/đảo có kiểm soát, rồi nối đường cũ và quyền tối thiểu. Đặc tả9 nhóm `docs/dac-ta-ban-giao-tien-2b.md`; nghiệm thu người dùng/dữ liệu/máy in thật gom cuối theo anh Tiến. Không tắt riêng cờ bàn giao sau phát sinh để xóa projection; khôi phục snapshot/image/cờ theo runbook.

## 18/10/2026 — Lát xác minh quỹ và chốt ca 2B đã kiểm; bàn giao tiền còn tiếp

Nhánh `feat/chot-ca-tien-mat-20261018`, [PR #11](https://github.com/tienduongmarcom/aphvh/pull/11), base PR #10 (14dceff). Mã nghiệp vụ/kiểm **`022322cab2eea0dade0848fa133bbb6c19199273`**. Không tăng version/tag hoặc triển khai: production vẫn0.15.3 theo xác nhận vận hành đã có; các PR #9–#11 chưa phát hành.

Đã có ba DocType native: `APH Xac minh quy` + `APH Phan bo quy`, `APH Chot ca tien`; Workspace Tiền và vay có lối vào và danh sách ca lệch. Cờ23 `kh_aph_cash_closing` mặc định tắt, cần cờ22 custody. Quản lý xác minh phân bổ số dư Cash/VND có căn cứ, phần chưa rõ riêng; người giữ tự chốt phải có/thực đếm/lệch và người/hạn xử lý. Không ghi GL/PLE, không lấy số đếm làm đầu ca mới. Snapshot lưu băm từng GL, actor/time server; nháp/sổ/bản trước đổi thì kiểm lại. Hủy/repost/sửa sổ trước mốc hoặc sổ mới ghi trước ngày chốt phải xác minh lại, bản cũ giữ nguyên. Retry cùng ca không submit hai lần. Tệp kiểm đếm riêng tư đúng hồ sơ, chặn sửa/xóa blob đã xác nhận. Không suy owner/backfill tiền lịch sử.

Quyền native Company/Account/từng dòng GL và từng nguồn vẫn được kiểm; khóa Cash theo company và current read. Account User chỉ đọc/chốt ca chính mình, quản lý không chốt thay; Không xem giá vốn/Kế toán nhà máy bị chặn kể cả cộng quyền. API current chỉ trả số của chính người đang đăng nhập. Chứng cứ JSON chỉ chứa mã GL và băm, không chứa tiền/người của nguồn. Chưa cấp thêm quyền GL cho người bán/nhà máy.

Cục bộ **327 kh_aph +108 lab9x** đạt; Python/JS và diff đạt. Đủ bốn cổng trên đúng022322c: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39138158466), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39138169799), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39138168695), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39138171169). Các lượt trước be3d555/95d384c đã hủy khi thay mã, không lấy làm bằng chứng mã cuối.

Đã tải/đọc artifact: **242 HTTP/Desk PASS,0 FAIL**, b01451; thêm2 kiểm kỹ thuật core/site trắng cũng PASS (244 dòng PASS toàn bộ evidence). Sáu ca mới đạt: phân1000 thành700/200/chưa rõ100; tệp riêng tư/giữ blob; thiếu20/thừa10, không đổi sổ; hai phiên retry và hai nháp cùng khoảng; nháp lỗi thời; hủy sau chốt, xác minh lại có liên kết, sổ lùi ngày; kế toán thường chốt đúng mình, không đọc phân bổ/ca người khác, Company scope và NoCost cộng manager; Chrome đọc snapshot800/800/0, form sạch/khóa. Đã xem `chot-ca-tien.png`; chỉ là ảnh UAT giả. Core63.508 tệp không đổi.

Cổng3: schema nâng/site mới **1.059/1.059**, lệch0, bỏ qua đúng6/6 mục; quay lui **1.052/1.052**, đếm/tổng/cờ/versions/settings/UI khớp, custody/closing đều0. Ca cố ý lỗi tự quay lui, so đếm/tổng/chi tiết/versions khớp và giữ bảo trì. Nền CI có GL0, không thay diễn tập bản sao production có dữ liệu khi đến phát hành.

**Bước tiếp theo:** bàn giao/giữ chỗ nguồn/nhận và đảo có kiểm soát; nối adapter quỹ nhà máy, chặn tự nhận, chống lặp thu quầy, vòng xử lý kết quả lệch và quyền tiền cá nhân tối thiểu cho người bán/nhà máy. Chưa có các phần này, không coi toàn bộ2B hoặc tiền toàn cửa hàng đã hoàn tất. Giới hạn lát này10.000 dòng/quỹ, VND; cùng ngày dòng mới theo ID GL/mốc server, không suy giờ nghiệp vụ không có trên GL. Blueprint field/quyền/khóa ở `docs/thiet-ke-chot-ca-ban-giao-2b.md` mục10. Nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật vẫn gom cuối theo anh Tiến.

## 18/10/2026 — Đợt2A người giữ tiền đã kiểm kỹ thuật/UAT;2B còn thiết kế

Theo yêu cầu tiếp tục sau PR #9, đã làm lớp nguồn đợt2A trên nhánh `feat/nguoi-giu-tien-20261018`, [PR #10](https://github.com/tienduongmarcom/aphvh/pull/10), base nhánhPR #9 (30a8773). Mã nghiệp vụ/kiểm **`929d16a84e1f1e6df32d0a614c228060c5e76c4b`**. Thêm cờ thứ22 `kh_aph_cash_custody` mặc định tắt,10 Custom Field trên PE/JE Account/SI/PI/POS/Funds Receipt–Action/quỹ nhà máy; truyền người thực giữ/giao qua đường thu quầy/thu ngay/JE tự sinh. Nguồn submit không đổi người giữ; không suy owner/backfill. Cùng accountCash trên JE không có hai người khác nhau vì GL gộp dòng.

Báo cáo Rà người giữ tiền mặt đọc GL có quyền, nguồn thiếu metadata hiện Chưa xác minh. Đây là phát sinh theo nguồn, KHÔNG là số tiền mỗi người hiện còn giữ; chưa có chốt ca/bàn giao mới. POS tổng hợp/nguồn ngoài adapter vẫn có thể chưa xác minh, chưa kiểm vận hành POS đầy đủ. Đặc tả9 nhóm: `docs/dac-ta-nguoi-giu-tien-2a.md`.

Cục bộ317 kh_aph +108 lab9x đạt, cú pháp Python/JS/diff đạt. Đủ bốn cổng trên đúng929d16a: [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39133916442), [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39133916266), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39133913616), [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39133918974).

Đã tải/đọc artifact: **236 PASS/0 FAIL**, b01445. Bảy ca2A đạt: mặt+bank tách đúng; nguồn chuẩn/không rõ/không đổi sau submit; Receipt/hoàn→JE chỉ đếm một lần; scope/role/report chỉ đọc; SI thu ngay→PE; PI trả mặt; quỹ nhà máy→JE; Chrome mở vùng Accounts chuẩn và kiểm ô có dữ liệu/form sạch. Core63.508 tệp không đổi. Ảnh `nguoi-giu-tien.png` chụp khung đầu form trước cuộn hoàn tất, không dùng ảnh này làm bằng chứng vị trí ô; bằng chứng hiển thị/dữ liệu là assertion Chrome, chưa là nghiệm thu sử dụng thật.

Cổng3 từ production0.15.3/21 cờ cũ: schema nâng/site mới1.056 mục khớp (bỏ qua đúng6 mục); quay lui schema1.052 mục/tổng/đếm/cờ/versions/cài đặt/giao diện khớp; cờ mới về0. Ca cố ý lỗi quay lui khớp chi tiết/versions và giữ bảo trì. Nền CI chưa có phát sinh sổ (các nhóm0), không thay diễn tập bản sao production có dữ liệu khi phát hành.

Giữ bằng chứng lỗi: [39122361020](https://github.com/tienduongmarcom/aphvh/actions/runs/39122361020) dừng ở Chrome vì vùng Accounts thu gọn, đã sửa thao tác bằng `frm.scroll_to_field`, không bỏ assertion; [39132682231](https://github.com/tienduongmarcom/aphvh/actions/runs/39132682231) thiếu mẫu thuế trên SI thử, đã khai rõ t_aph thay vì nới guard thuế. Lượt929d16a đã kiểm lại cả hai và hai nguồn hóa đơn/quỹ nhà máy.

**Chưa phát hành/merge/tag hoặc triển khai:** production giữ0.15.3/digest đã xác nhận,21 cờ; #9 và #10 chưa đưa vào production. Commit hồ sơ sau929d16a chỉ thay tài liệu, không là mã kiểm nghiệp vụ mới. Nghiệm thu dữ liệu/người dùng/máy in thật gom cuối theo chủ dự án.

**ĐANG DỞ đợt2B:** thiết kế9 nhóm ở `docs/thiet-ke-chot-ca-ban-giao-2b.md`, chưa có code/schema/PASS2B. Bước tiếp chốt blueprint field/DocPerm/khóa/fingerprint cho xác minh tiền bắt đầu và đối chiếu tổng người–quỹ–GL, rồi chốt ca/bàn giao dùng chung. Bao phủ lối quỹ nhà máy cũ, chống tự nhận và token thu tiền mặt cũ; không dùng tổng thu/owner làm tiền đang giữ, không tạo thu khách lần hai. Đợt3–4 vẫn theo kế hoạch; đợt5 chờ nghiệp vụ riêng.

## 18/10/2026 — Ứng viên in lại A5, nghiệm thu thật gom cuối

Chủ dự án cho phép gom nghiệm thu dữ liệu/người dùng/máy in thật đến cuối kế hoạch; vẫn kiểm UAT giả từng phần trước phát hành. Ứng viên `feat/in-lai-a5-20261018` thêm nút A5 từ DN đã lưu và API chỉ đọc, dùng renderer chung. Mã nghiệp vụ `1e89ace187468d976cb3361d3a0dd6ea75f917c1`, [PR #9](https://github.com/tienduongmarcom/aphvh/pull/9): cục bộ305+108 ca đạt; [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39109706356), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39109822145), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39109706459), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39109824398) đều đạt đúng SHA. Artifact đã đọc:229 PASS/0 FAIL, b01438, core63.508 tệp không đổi; HTTP/Chrome in lại hai lần không tăng phiếu/sổ. Đã xem hai trang A5. Cổng3 đã kiểm từ baseline0.15.3, so nâng/quay lui/ca lỗi khớp và giữ bảo trì; nền CI chưa có phát sinh sổ. Chi tiết ở đầu `docs/ban-giao.md`. Production vẫn0.15.3/digest đã xác nhận, chưa có tag/image hoặc triển khai mới. Bước tiếp hoàn thiện đặc tả đợt2 theo bản rà nguồn `docs/dot-2-ra-soat-nguon-tien.md`, không chờ dữ liệu thật. Chưa có mã chốt ca/bàn giao mới. Commit sau mã kiểm chỉ thay hồ sơ.

## 18/10/2026 — Kế hoạch 5 đợt đã đối chiếu lại, không đổi production

Production vẫn0.15.3/digest đã xác nhận ở mục dưới. Kế hoạch tiếp nối đã cập nhật đúng phần đồng bộ dữ liệu mẫu chuẩn/in lại/tổng hợp có trong0.15.3. GN06 còn lối mở lại A5 từ phiếu đã có và nghiệm thu thực tế; IN02 ghi rõ thiếu nút, chưa tính đạt. Đợt2–4 còn phần mở rộng trên nghiệp vụ nền; đợt5 chờ chốt riêng. Lượt này chỉ cập nhật hồ sơ, không đổi mã/cờ/version hoặc triển khai.

## 18/10/2026 — Production0.15.3 đã triển khai ĐẠT

Người vận hành gửi log `erpnext-prod/frontend`, trong `~/trien-khai`: **`=== XONG 0.15.3: ĐẠT ===`**, image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.3`, digest **`sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`**, khớp workflow39105247607/nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Đã đổi `khach/aph-vh/phien-ban.yaml` và baseline Cổng3 sang bản production này; chưa chạy lại diễn tập CI từ baseline mới.

Nguồn xác nhận là log người vận hành; Codex không có SSH và chưa kiểm độc lập giao diện. Giữ nền/21 cờ. Bản0.15.2/digest `sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333` là mốc lịch sử/quay lui có điều kiện, không tự restore sau khi có giao dịch mới. Bước tiếp nghiệm thu người dùng/máy in A5 theo chín ca trong `docs/nghiem-thu-mau-in-20261018.md`; triển khai đạt không thay nghiệm thu nghiệp vụ thật.

## 18/10/2026 — Image0.15.3 đã phát hành đạt, chưa triển khai VM

[Workflow39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) thành công toàn bộ trên tag `v0.15.3`, nguồn `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. Image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.3`, manifest digest **`sha256:330607a23533814481df2973c8f7d3b323d7782892407cef04a4086e8fa30496`**. Đã đọc log push/metadata và artifact: UAT227 PASS/0 FAIL, core nguyên vẹn, Cổng2/2b/3 đạt, so nâng/quay lui/ca lỗi khớp. kh_aph0.15.3/lab9x0.2.11, nền và21 cờ giữ nguyên.

**Bước tiếp trên SSH máy chủ:** checkout tag trong `~/trien-khai`, diễn tập trên bản sao hiện tại rồi nâng bằng chuỗi `&&` ở `docs/phat-hanh-0.15.3.md`. Nền Cổng3 không có phát sinh sổ, không thay diễn tập dữ liệu thật hiện tại. Phiên Codex không có SSH; chưa ghi đã diễn tập hoặc nâng VM. Production/manifest vẫn0.15.2/digest cũ cho đến log `=== XONG 0.15.3: ĐẠT ===` và digest khớp; sau xác nhận mới đổi manifest và baseline Cổng3. Không đổi tag/image đã phát hành.

## 18/10/2026 — Tag0.15.3 đã đẩy đúng mã, đang phát hành image

Tag remote `v0.15.3` = `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`. [Workflow phát hành39105247607](https://github.com/tienduongmarcom/aphvh/actions/runs/39105247607) đang chạy. Chưa có image/digest0.15.3 đạt phát hành; chưa chạy diễn tập hoặc nâng VM.

PR #4 và #5 đã merge main, main ở `8a0ea61e5408e1ef1feff8d2f2dde0aed66d9f2d`, chứa mã đóng gói. Giữ manifest production0.15.2 cho đến log triển khai thành công. Bước tiếp đọc kết quả/artifact/digest phát hành rồi chạy runbook0.15.3 trên SSH máy chủ; phiên Codex hiện không kết nối được tên `erpnext-prod`.

## 18/10/2026 — 0.15.3 sẵn sàng gắn tag; production vẫn0.15.2

Mã đóng gói **`96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`**, kh_aph0.15.3/lab9x0.2.11: đủ [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872). Đã đọc artifact: UAT227 PASS/0 FAIL, phiên bản đúng, PDF A5/tổng hợp đạt kiểm hình; nâng/quay lui/ca lỗi khớp và giữ bảo trì. Nền Cổng3 chưa có phát sinh sổ, cần diễn tập bản sao production hiện tại khi triển khai thật.

Nguồn: PR #4 đã gộp main, PR #5 chốt gộp main giữ lịch sử theo yêu cầu production. Chọn mã đóng gói trên khi chủ dự án gắn tag theo AGENTS; commit sau chỉ thay hồ sơ. Bước tiếp: tag → workflow phát hành đạt/có digest → diễn tập bản sao hiện tại → nângfrontend. Lệnh tại `docs/phat-hanh-0.15.3.md`. Chưa có tag/image0.15.3; phiên này không kết nối được SSH `erpnext-prod`. Manifest giữ0.15.2 cho đến log VM xác nhận. Không ghi đã lên production từ kết quả CI.

## 18/10/2026 — Nguồn main đã đồng bộ 0.15.2; 0.15.3 đang kiểm

PR #4 đã merge vào main tại `f05c8a181c269d2075b6d822addb571f26b7bef6`; main chứa tag0.15.2 và lịch sử các nhánh trước. PR #5 nay nhắm main, chưa merge. Ứng viên0.15.3/lab9x0.2.11: `96a7ef0352b45c31b8d26428aad3ddbcafeeb37c`.

Bốn cổng đang kiểm: [2](https://github.com/tienduongmarcom/aphvh/actions/runs/39103161614), [2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157904), [3](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157872), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39103157858). Chưa có tag/image/digest0.15.3. Production vẫn0.15.2; cần workflow phát hành đạt và diễn tập bản sao hiện tại trước nâng VM. Đường SSH từ phiên này chưa khả dụng.

## 18/10/2026 — Chuẩn bị ứng viên production 0.15.3 theo yêu cầu chủ dự án

Đã đổi kh_aph0.15.3/lab9x0.2.11, giữ nền và21 cờ. Chưa gắn tag hoặc có image0.15.3; cần bốn cổng trên SHA đóng gói mới. Runbook tại `docs/phat-hanh-0.15.3.md`. Sau khi kiểm đạt: chủ dự án gắn tag theo AGENTS, workflow phát hành đạt rồi chạy diễn tập bản sao hiện tại và nâng cấp trên VM.

Production hiện vẫn0.15.2/digest đã xác nhận. SSH thử chỉ đọc từ máy hiện tại không phân giải được `erpnext-prod`; chưa truy cập hoặc thay đổi VM. Manifest giữ nguyên cho đến log triển khai thành công.

## 18/10/2026 — Bộ mẫu `7c2217e` đạt đủ bốn cổng, chưa phát hành

SHA đầy đủ `7c2217e8737e96700fa050aac446bb3591a830a8`. [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39101464777), [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463208), [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463191), [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39101463224) đều đạt. Cục bộ 302+108 ca đạt. Đã đọc artifact: UAT 227 PASS/0 FAIL, b014 có 36 PASS, core 63.508 tệp nguyên vẹn. Đã xem PDF CI: hai liên đúng hai trang A5, tổng hợp tám đợt/bốn company hai trang A4, khối ký nguyên vẹn.

Cổng 3 so tổng/đếm/chi tiết khớp, schema/cờ khớp site mới, quay lui và ca lỗi tự quay lui khớp phiên bản/dữ liệu và giữ bảo trì. Nền CI không có phát sinh sổ, không thay diễn tập bản sao production có dữ liệu ngay trước triển khai. Bằng chứng chi tiết ở đầu `docs/ban-giao.md`.

**Chưa phát hành:** còn nghiệm thu máy in/nhân sự thật theo `docs/nghiem-thu-mau-in-20261018.md`, quy chế biểu mẫu chưa ban hành. Production giữ 0.15.2; chưa tăng version/tag/merge hoặc triển khai VM. Commit hồ sơ sau mã kiểm chỉ thay tài liệu.

## 18/10/2026 — Bộ mẫu theo thông tư đang chờ kiểm SHA cuối

Đã đồng bộ mẫu kho, thu/chi, bán hàng, giao nhận, đối soát và phiếu xuất nhanh A5 theo chế độ hiện hành của từng đơn vị; căn cứ và giới hạn được ghi tại `docs/bang-ra-soat-phap-ly-APH-VH.md`, quy chế nội bộ còn là dự thảo. Render cục bộ 19 tình huống giả lập đạt 21 trang; kiểm cục bộ 302 ca ứng dụng + 108 ca lõi đạt. Booklet xem trước: `outputs/bo-mau-phieu-thong-tu-2026.pdf`.

**Chưa phát hành:** thay đổi này chưa có CI trên SHA cuối, chưa in máy thật, chưa tag/merge và chưa triển khai. Production vẫn 0.15.2. Bước kế tiếp là chạy kiểm đúng SHA, nghiệm thu giấy A4/A5 với người dùng rồi mới quyết định phát hành theo runbook.

## 18/10/2026 — Phiếu xuất nhanh A5 theo mẫu chủ dự án, chưa kiểm CI

Anh Tiến cung cấp PDF phiếu đang dùng và yêu cầu chỉnh riêng phiếu xuất nhanh theo mẫu A5. Yêu cầu mới thay cách trình bày A4/không giá của phiếu nhanh: A5 ngang, Times New Roman, thông tin đơn vị/khách/người nhận/kho/địa chỉ, bảng hàng có mã/ĐVT/kg/bao × kg mỗi bao/đơn giá/thành tiền, tổng tiền hàng bằng chữ, chứng từ kèm theo và năm vị trí ký theo mẫu. Giữ hai liên Lưu kho/Giao nhận, thông tin xe/người thực giao/thời điểm/chênh lệch và dấu chờ xuất/bản sao.

Giá bán thuần lấy từ `Delivery Note Item.net_rate/net_amount` (giữ đúng cả giá0), tổng cộng các net_amount, ghi rõ chưa thuế; không cộng lại thuế, không biến phiếu thành hóa đơn hoặc biên bản bàn giao mới. Chỉ fallback rate/amount khi trường net là None. Tiền chữ dùng VND; ngoại tệ ghi tổng và mã tiền, không đọc thành đồng. Không truy vấn/đưa giá vốn vào ngữ cảnh in. Giữ guard/quyền/scope trên server và không ghi sổ khi in. Không thêm schema/cờ/version.

Đã kiểm cục bộ **300 ca kh_aph đạt**, gồm kiểm giá thuần/giá0/không đưa giá vốn vào ngữ cảnh, escape và trạng thái nháp/đã xuất; cú pháp và diff đạt. Bộ sinh Print Format đã chạy, JSON chuẩn không đổi vì đây là template nhanh riêng. PDF Chrome từ chính template với dữ liệu giả: mỗi liên một trang A5 ngang594,96×420pt; đã xem cả hai liên. Phiếu25 dòng tự sang trang, lặp tiêu đề bảng, giữ phần ký nguyên khối. File xem thử tại thư mục `outputs/phieu-xuat-nhanh-a5.pdf` của chat, không đưa dữ liệu khách vào repo. Đã cập nhật ca HTTP kiểm giá từ DN/A5 và bỏ tuyên bố quantity_only cũ theo yêu cầu mới; **chưa chạy ca HTTP/CI của thay đổi này**, không dùng các cổng xanh bdb91a8 để chứng minh mã mới.

**ĐANG DỞ: GN06 và nghiệm thu thực tế chưa đóng.** Bước tiếp: kiểm CI đúng SHA mới, đồng bộ các đường mẫu chuẩn/in lại/tổng hợp theo phạm vi đã chốt; nghiệm thu máy in A5 và nhân viên. Chỉ phiếu nhanh đổi có giá theo yêu cầu này; mẫu kho chuẩn vẫn theo quy tắc riêng cho tới khi có yêu cầu đổi. Production giữ **0.15.2**, chưa push/phát hành/triển khai thay đổi A5.

## 18/10/2026 — GN10/GN11 đã đạt: xuất ngay và mất phản hồi sau commit

Tiếp tục [PR #5](https://github.com/tienduongmarcom/aphvh/pull/5) trên `feat/thong-tin-giao-nhan-20261017` từ `e2369ab`. **Mã nghiệp vụ đã kiểm: `bdb91a826cb506d67870e14d1319cededc4a5008`**. Commit sau mốc này chỉ cập nhật hồ sơ, không phải lượt CI mới. Đã đọc lại AGENTS GitHub, bàn giao, quyết định, kiến trúc và runbook; giữ production 0.15.2.

Đã thêm lựa chọn Xuất ngay trong Dialog, mặc định vẫn nháp. Người có quyền submit mới thấy lựa chọn; cần người thực giao, cách giao và người nhận. API POST tạo+xác nhận trọn đợt trong một transaction qua controller native; lỗi nhóm sau rollback cả DN/SI/GL/SLE. Tách hash nháp/xuất ngay, kiểm cờ ghi nợ lúc xuất, quyền/scope và lượng/nguồn/thông tin/dấu xuất thực tế khi retry. Không nâng nháp cũ thành đã xuất. Vận chuyển tới Đang giao, tự lấy tới Khách đã nhận; không ghi sổ khi mở lại bản in/nhận hàng/retry. Sau thành công tải lại lượng và công nợ trên đơn. Không thêm schema/cờ/quyền hoặc sửa core.

Bằng chứng trên đúng SHA:

- Cục bộ **299 kh_aph +107 lab9x =406 ca đạt**; cú pháp Python/JS, diff đạt.
- [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39086136285) và [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39086133337): đạt site trắng và diễn tập dựng/nâng/quay lui.
- [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39086133438): **227 PASS, 0 FAIL**, b01436 gồm restore. Đã đọc cả 4 ca HTTP xuất ngay và 1 ca Desk. Thiếu submit/Dũng/thiếu người giao bị chặn không để nháp; hai cách giao và retry sau nhận đúng; APH đã xử lý rồi VH thiếu tồn thì cả đợt rollback và Bin không đổi, bổ sung tồn giả rồi retry cùng token thành công hai Company; scope bị chặn cả retry; gọi đồng thời chỉ một DN/một SI.
- Ca `NATIVE_DESK_XUAT_NGAY_LOST_RESPONSE`: Chrome thực dùng Fetch chặn phản hồi200 sau server commit, xác minh DN `MAT-DN-2026-00017` đã submit/Khách đã nhận rồi bấm lại đúng Dialog/token. Counts DN/SI/GL/SLE không tăng. Đã xem ảnh kết quả `xuat-ngay-retry.png` trong artifact.
- [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39086133314): đạt từ baseline production0.15.2 đúng digest. Đọc dấu vân: trước/sau nâng khớp `dem/tong/chi_tiet`; schema/cờ khớp site trắng; trước lỗi/sau tự quay lui khớp `dem/tong/chi_tiet/versions`.

Đặc tả9 nhóm: `docs/dac-ta-xuat-ngay.md`. Kế hoạch truy nguyên: `docs/ke-hoach-van-hanh-tiep-noi.md`.

**ĐANG DỞ: đợt 1 chưa đóng. Bước tiếp GN06:** đồng bộ dữ liệu giao nhận giữa bản in nhanh, mẫu in chuẩn/in lại và phiếu tổng hợp. `phieu_xuat_kho_ban_hang.html`/`bien_ban_giao_nhan.html` còn đọc ô cũ `kh_aph_nguoi_nhan`, `kh_aph_lai_xe`/biển số trong khi phiếu nhanh đã dùng ô đợt/native mới; `delivery_slip.render` còn ô ký trống chung. Cần chọn dữ liệu mới khi có cách giao đợt, fallback phiếu cũ/phiếu trả, escape và kiểm từng đường in/PDF; không gán một người nhận chung cho nhiều DN khác nhau. Sau đó nghiệm thu máy in/người dùng/dữ liệu thật. Chốt ca/tiền/nhà máy và hóa đơn một phần vẫn theo các đợt sau.

Production vẫn **0.15.2**; chưa tăng version/tag/merge/phát hành/triển khai PR #5. Phát hành phải kiểm SHA phiên bản cuối và diễn tập bản sao production hiện tại theo runbook.

## 18/10/2026 — GN09 đã đạt kiểm thử: xử lý chênh lệch giao nhận

Tiếp tục [PR #5](https://github.com/tienduongmarcom/aphvh/pull/5), nhánh `feat/thong-tin-giao-nhan-20261017`, từ mốc tài liệu `602b73e` / mã 1A đã kiểm `5155ca4`. **Mã nghiệp vụ GN09 đã kiểm: `9c45e7492e55797c48483d19004e52aecf6614ca`**. Các commit sau mốc này chỉ cập nhật tài liệu, không phải lượt CI mới. Đã đọc lại AGENTS trên GitHub và các quyết định/kiến trúc/bàn giao/runbook.

Đã có vòng báo chênh lệch → giao người/hạn → chốt kết quả hoặc mở lại có lý do trên DN nguồn. Quyền read/write và scope native vẫn áp dụng; thao tác giao/chốt/mở lại đòi Accounts Manager hoặc Administrator, người phụ trách phải có quyền trên đúng phiếu. Chốt cần bản ký hiện tại đã đối chiếu; không tự đóng vì chỉ có dấu đối chiếu. Căn cứ gồm kết luận không điều chỉnh sổ hoặc phiếu trả/hóa đơn giảm đã submit, đúng nguồn/Company/Customer. Thay tệp/ghi chú tự mở lại, giữ kết quả cũ trong Comment. Khóa đọc hiện hành bảo vệ khi chốt và hủy căn cứ đồng thời. Không tạo DocType Nhiệm vụ hoặc sổ lượng/tiền riêng.

Hủy phiếu nguồn có hồ sơ đòi trưởng và quyền cancel native. Hồ sơ kết thúc trong cùng transaction hủy; không buộc nhận hàng hoặc bản ký giả để thoát vòng. Nếu hóa đơn/liên kết native còn hiệu lực thì hủy bị chặn và dấu hồ sơ rollback. Phiếu đã hủy vẫn xem hồ sơ readonly; phiếu amend không sao chép trạng thái cũ. Không tự tạo/hủy chứng từ tài chính thay người dùng.

Bằng chứng trên đúng SHA:

- Cục bộ **294 kh_aph + 107 lab9x = 401 ca đạt**; cú pháp Python/JS và diff đạt.
- [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39083098771): đạt site trắng.
- [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39083095486): đạt dựng/nâng/quay lui.
- [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39083095506): **222 PASS, 0 FAIL**; b014 có 31 PASS gồm restore. Đã đọc artifact của cả 5 ca HTTP chênh lệch và 1 ca Desk; xem ảnh Dialog thật. Đã kiểm Dũng cộng vai trò, scope người phụ trách, phiên cũ/field giả, mở lại khi đổi bằng chứng, chứng từ nháp/sai nguồn, chốt không ghi sổ, chốt–hủy đồng thời, hủy nguồn không nhận hàng giả và hoàn tồn đúng.
- [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39083095503): đạt từ baseline 0.15.2 đúng digest. Đọc dấu vân: trước/sau nâng khớp `dem/tong/chi_tiet`; schema/cờ sau cài khớp site trắng; trước lỗi/sau tự quay lui khớp `dem/tong/chi_tiet/versions`.

Đặc tả 9 nhóm tại `docs/dac-ta-chenh-lech-giao-nhan.md`; kế hoạch truy nguyên cập nhật tại `docs/ke-hoach-van-hanh-tiep-noi.md`. Những chứng từ xử lý ngoài DN trả/SI giảm, hoặc hóa đơn gộp chưa truy được dòng nguồn phải giữ mở để đối soát, không chọn đại chứng từ hay tạo trả kho giả.

**ĐANG DỞ: đợt 1 chưa đóng. Bước tiếp theo GN10:** thao tác xuất ngay có quyền trong Dialog, một lần gọi tạo+xác nhận nguyên tử, kiểm quyền submit/lượng/tồn/duyệt và retry không ghi sổ hai lần. GN06 còn các đường in/máy in thật; GN11 còn cắt mạng đúng lúc server commit; nhân sự/dữ liệu thật chưa nghiệm thu. Chốt ca/người giữ tiền/nhà máy là đợt sau. Production vẫn **0.15.2**, chưa tăng version/tag/merge/phát hành/triển khai PR #5. Khi phát hành phải kiểm đúng SHA cuối và diễn tập bản sao production hiện tại theo runbook.

## 17/10/2026 — Đợt 1A đã đạt kiểm thử, chưa phát hành

PR [#5](https://github.com/tienduongmarcom/aphvh/pull/5), nhánh `feat/thong-tin-giao-nhan-20261017`, nền `0c1e104` của nhánh bàn giao. Mã nghiệp vụ đã kiểm: **`5155ca48f4a2039d164de419459fcde92a1bfdbb`**. Commit cập nhật hồ sơ sau mốc này chỉ thay tài liệu, không phải SHA đã chạy CI.

Đã thêm cách giao, người nhận, điện thoại, lái xe, biển số và địa chỉ trong Dialog lập phiếu theo đợt. Địa chỉ thay thế phải đúng Customer và quyền đọc; để trống giữ địa chỉ từng SO nguồn. Nội dung mới tham gia hash chống trùng, giữ hash cũ cho API không truyền thông tin giao nhận. Kho ghi riêng người trực tiếp giao; cần quyền submit và xác nhận đúng cách giao. Dấu người/thời điểm xuất do server ghi, giữ nguyên khi nhận hàng và lưu bản ký. Phiếu đã xuất không sửa đè thông tin. Bản in nhanh có hai liên Lưu kho/Giao nhận, không giá và có dấu bản sao khi in lại sau xuất. Dùng cờ Trung tâm Bán hàng hiện có; thêm sáu Custom Field qua bộ cài rõ ràng, không after_migrate, không sửa core/sổ tài chính.

Bằng chứng trên đúng SHA:

- Cục bộ: **278 kh_aph + 107 lab9x = 385 ca đạt**; cú pháp Python/JS và diff đạt. Bộ sinh Print Format chuẩn chạy không đổi JSON (template nhanh render riêng).
- [Cổng 2](https://github.com/tienduongmarcom/aphvh/actions/runs/39041879339): đạt site trắng.
- [Cổng 2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39041876332): đạt dựng/nâng/quay lui.
- [UAT](https://github.com/tienduongmarcom/aphvh/actions/runs/39041876201): **216 PASS, 0 FAIL**, b014 có 25 PASS gồm restore. Đã đọc artifact, kiểm sáu trường Dialog và cả hai trang PDF A4. Chuỗi VAT/cọc/giao/thu: 770.000 / 192.500 / 100.000 / 92.500, chưa giao 577.500, nợ cũ không đổi, lãi gộp 75.000.
- [Cổng 3](https://github.com/tienduongmarcom/aphvh/actions/runs/39041876215): đạt từ đúng baseline production 0.15.2/digest đã xác nhận. Đọc dấu vân: trước/sau nâng khớp `dem/tong/chi_tiet`; schema/cờ sau cài khớp site trắng; trước lỗi/sau tự quay lui khớp `dem/tong/chi_tiet/versions`.

ĐANG DỞ: đợt 1 chưa đóng. Bước tiếp theo là thiết kế/triển khai GN09: người phụ trách, kết quả và liên kết chứng từ xử lý chênh lệch trên phiếu nguồn; không coi đối chiếu bản ký là xử lý xong. GN10 xuất ngay trong Dialog chưa có; GN06 còn các đường in khác và máy in thật; GN11 chưa cắt kết nối trình duyệt tại thời điểm server commit. Fallback địa chỉ SO có unit, chưa có ca HTTP riêng. Chi tiết 9 nhóm tại `docs/dac-ta-giao-nhan-dot-1.md`, thứ tự 5 đợt tại `docs/ke-hoach-van-hanh-tiep-noi.md`. Chốt ca/người giữ tiền/nhà máy vẫn thuộc đợt sau.

Production vẫn **0.15.2**, chưa tăng version/tag/merge/phát hành/triển khai PR #5, chưa nghiệm thu tài khoản nhân sự/dữ liệu/máy in thật. Khi đến bước phát hành phải kiểm đúng SHA phiên bản cuối và diễn tập bản sao production hiện tại theo runbook.

## 17/10/2026 — Khôi phục mạch kế hoạch vận hành, đọc lại quy tắc GitHub

Theo yêu cầu anh Tiến, đã đọc lại AGENTS.md trên origin/feat/ho-so-giao-nhan-20261017 và đối chiếu bàn giao, quyết định nghiệp vụ, kiến trúc, quy trình khách/release. Local khớp remote d622abc trước lượt này. Production giữ 0.15.2; các phiên bản cũ trong thân AGENTS/runbook là mô tả lịch sử, không dùng thay mốc TRANG_THAI/manifest/log đã xác nhận.

Đã ghi `docs/ke-hoach-van-hanh-tiep-noi.md`: thứ tự 5 đợt, bảngGN01–GN12 với code/ca hiện có và phần thiếu, thiết kế thông tin giao nhận/chênh lệch, điểm nốiT01–T07 và phạm viNM/TC/HD. Đây là hồ sơ tiếp nối chính thức theo các tệp yêu cầu người dùng cung cấp lại; không phải tuyên bố đã hoàn thành tính năng. Không sửa mã/core/quyền/dữ liệu, chưa chạy lại test cho thayđổi tài liệu.

ĐANG DỞ: đợt 1 còn thông tin giao nhận, bản in 2 liên và vòng xử lý chênh lệch. Bước tiếp: xác minh meta native16.51.1 trước chọnfield, triển khaiGN03–GN04 + token GN01, kiểm hồi quy và server quyền, sau đó GN06/GN09. Đợt 2 chốt ca/người giữ chưa viết; nhà máy/chốt ngày chưa có màn thống nhất; hóa đơnmột phần vẫn cần chốt riêng. Không tag/merge/phát hành/triển khai trong lượt này.

## 17/10/2026 — Production 0.15.2 đã triển khai theo log anh Tiến

Anh Tiến chạy trên `erpnext-prod`, site `frontend`, trong `~/trien-khai` ở tag `v0.15.2`. Diễn tập bản sao tách biệt lượt `10171255a25ef6` báo `tong`, `dem`, `chi_tiet` khớp và ghi dấu `/home/tienduongmarcom/dien-tap-0.15.2.ok`. Sau đó bộ triển khai báo **`=== XONG 0.15.2: ĐẠT ===`**. Image VM `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.2` có digest **`sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333`**, khớp workflow phát hành39030251134. Nguồn `24b795cc28f47ca2f31aef8edbbd8e5984c12ee3`; nền ERPNext16.51.1/Frappe16.52.0, lab9x0.2.10, giữ21 cờ.

Đã cập nhật manifest khách về0.15.2. Bằng chứng là log người vận hành gửi trong chat; Codex không có SSH và chưa kiểm độc lập giao diện production. Không chạy lại nâng cấp hoặc dùng backup cũ để phục hồi sau khi mở nhập liệu. Nếu phát sinh lỗi sau mở nhập liệu, cần đối soát giao dịch mới trước khi chọn cách khắc phục.

Bước tiếp: tải lại Desk, kiểm mở danh mục/phiếu hiện có; tiếp tục nhập hàng hóa, tồn kho/số dư, người dùng và cấu hình thực tế. Gom nghiệm thu toàn chuỗi theo `docs/nghiem-thu-tong-the.md` khi dữ liệu sẵn sàng. Chưa ký nghiệm thu nghiệp vụ thật hoặc toàn bộ202 quyết định. Các mục “chưa triển khai” phía dưới là lịch sử trước mốc này. Bản trước0.15.1/digest `sha256:c4b61eb4b2924d50f64bbeaf83623da3e7259f9484b28d6f3e228939912edf47` chỉ là mốc quay lui có điều kiện, không tự restore làm mất dữ liệu mới.

## 17/10/2026 — Image 0.15.2 đã phát hành, chưa triển khai VM

[Workflow phát hành39030251134](https://github.com/tienduongmarcom/aphvh/actions/runs/39030251134) hoàn tất thành công, đủ mọi job UAT/Cổng2/2b/3/phát hành, trên tag `v0.15.2` = `24b795cc28f47ca2f31aef8edbbd8e5984c12ee3`. Log build/push xác nhận image `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.2` có manifest digest `sha256:fea385a9512d97fa4489e441873e6b6f88ea627f46c9d65f9d041c50e2427333` (kết thúc12:19 UTC). Không đổi tag đã phát hành.

Bước tiếp: người vận hành SSH vào `erpnext-prod`, checkout đúng tag trong `~/trien-khai`, chạy `dien_tap_ban_sao.sh 0.15.2` trên dữ liệu hiện tại. Chỉ sau diễn tập ĐẠT mới chạy `trien_khai_frontend.sh 0.15.2`; không thêm cờ. Chưa có log VM mới nên production vẫn0.15.1, manifest khách giữ nguyên. Codex không có phiên SSH; không coi phát hành image là đã triển khai/ nghiệm thu dữ liệu thật.

## 17/10/2026 — Ứng viên 0.15.2 sẵn sàng gắn tag

Mã đóng gói **`24b795cc28f47ca2f31aef8edbbd8e5984c12ee3`** đủ bốn cổng xanh: [UAT39028411357](https://github.com/tienduongmarcom/aphvh/actions/runs/39028411357), [Cổng239028414365](https://github.com/tienduongmarcom/aphvh/actions/runs/39028414365), [Cổng2b39028411350](https://github.com/tienduongmarcom/aphvh/actions/runs/39028411350), [Cổng339028411353](https://github.com/tienduongmarcom/aphvh/actions/runs/39028411353). Đã đọc artifact: UAT215 PASS/0 FAIL; Cổng3 số lượng/tổng/chi tiết khớp trước-sau nâng cấp và sau ca lỗi tự quay lui; schema khớp site mới. Unit268+107=375 đạt. PR #4 chuyển sang sẵn sàng duyệt, chưa merge.

**Bước tiếp theo:** chủ dự án gắn tag `v0.15.2` vào đúng SHA trên theo AGENTS.md; workflow phát hành chạy lại các cổng trước khi đẩy image. Chưa có image/digest 0.15.2 được phát hành, chưa chạy VM. Khi image đạt, theo `docs/phat-hanh-0.15.2.md`: diễn tập trên bản sao dữ liệu thật hiện tại rồi triển khai (21 cờ hiện có, không thêm cờ). Production vẫn0.15.1. Codex không có phiên SSH. Commit sau SHA trên chỉ chốt tài liệu/bằng chứng, không đổi mã đã kiểm; chọn SHA trên khi gắn tag để có đúng mốc đủ cổng.

## 17/10/2026 — Chuẩn bị ứng viên phát hành 0.15.2

Theo yêu cầu tiếp tục của anh Tiến: nâng nhãn app lên 0.15.2 cho phạm vi PR #4, giữ nền và 21 cờ. Sửa `khach/aph-vh/phien-ban.yaml` từ thông tin cũ 0.14.3 về production 0.15.1 theo log đã xác nhận; không ghi ứng viên thành bản đã triển khai. Hướng dẫn cụ thể ở `docs/phat-hanh-0.15.2.md` gồm phạm vi, migrate/bộ cài, diễn tập bắt buộc khi đã có dữ liệu, triển khai và quay lui. Chưa tag/merge/đẩy image/đổi production.

ĐANG DỞ: chờ bốn cổng trên SHA đóng gói 0.15.2. Sau khi xanh, chốt SHA cho chủ dự án gắn tag theo AGENTS.md. Sau workflow phát hành đạt mới chạy diễn tập trên VM rồi triển khai; Codex hiện không có phiên SSH. Nghiệm thu thực tế vẫn gom sau khi dữ liệu sẵn sàng.

## 17/10/2026 — Chốt kiểm luồng tiền, nhà máy, phạm vi tài chính và chuỗi VAT

Mã đã kiểm: `96ce98d6784fc9fd26818306bbe0a1fc54c5fd4a`, PR [#4](https://github.com/tienduongmarcom/aphvh/pull/4). Đủ bốn cổng trên cùng SHA: [UAT 39018390715](https://github.com/tienduongmarcom/aphvh/actions/runs/39018390715), [Cổng 2 39018394462](https://github.com/tienduongmarcom/aphvh/actions/runs/39018394462), [Cổng 2b 39018390706](https://github.com/tienduongmarcom/aphvh/actions/runs/39018390706), [Cổng 3 39018390742](https://github.com/tienduongmarcom/aphvh/actions/runs/39018390742) đều đạt. Cục bộ: 268 kh_aph + 107 lab9x = 375 ca đạt.

Đã đọc artifact UAT: 215 PASS, 0 FAIL; funds 20, b0111 15, b0114 8, b014 24 gồm phục hồi. Ca xuyên suốt cùng đơn xác nhận tổng có VAT 770.000 → cọc 100.000 → giao 5/20 kg/hóa đơn 192.500 → cấn cọc → nhận hàng/lưu bản ký/đối chiếu không ghi sổ lần hai → thu nốt 92.500; nợ đã giao 0, phần chưa giao 577.500, nợ cũ giữ nguyên, lãi gộp 75.000. Các ca chặn trùng mã PE/JE/phiếu thực thu và nhập đồng thời, quyền File/Bank, giới hạn Company, sửa tay kết quả quỹ nhà máy, hồ sơ không xem giá vốn cộng vai trò kế toán đều đạt trong bộ hồi quy.

Artifact Cổng 3: số lượng, tổng và chi tiết sổ trước/sau nâng cấp khớp; cấu trúc site nâng cấp khớp site cài mới; cố ý làm lỗi nâng cấp đã tự quay lui, giữ bảo trì và khôi phục số lượng/tổng/chi tiết. Lượt UAT trước `39017622574` dừng do helper đòi trường message khi xóa nháp (API trả rỗng); đã sửa đúng hai lối xóa nháp, giữ nguyên assertion nghiệp vụ và chạy lại toàn bộ.

Mốc này hoàn tất vòng phát triển/kiểm giả lập nêu dưới, không xác nhận toàn bộ 202 quyết định hoặc nghiệm thu người dùng thật. Bước tiếp theo: gom nghiệm thu thực tế theo `docs/nghiem-thu-tong-the.md` khi có danh mục hàng, tồn kho/số dư và nhân sự/máy in; xử lý chênh lệch thực tế nếu có. Production vẫn **0.15.1** theo digest đã ghi, chưa tag/merge/phát hành/triển khai. Commit bàn giao sau SHA trên chỉ cập nhật hai tài liệu trạng thái, không đổi mã đã kiểm.

## 17/10/2026 — Thêm chuỗi xuyên suốt và sửa ba số thanh toán có VAT

Trong cùng PR #4: thêm ca trên một đơn chung có VAT10%: tổng770000 → cọc100000 → giao5/20kg, hóa đơn192500 → cấn cọc, còn92500 → nhận hàng/bản ký (không ghi sổ lần hai) → thu nốt, nợ phần đã giao0, phần chưa giao577500. Kiểm nợ cũ không tự bị cấn và lãi gộp của phần đã giao75000 (doanh thu chưa thuế175000 − giá vốn100000).

Sửa `funds.shared_financials`: trước dùng net_total đơn chung chưa thuế với grand_total hóa đơn có thuế; nay tổng phải thanh toán lấy grand_total của SO nguồn chuẩn. Nguồn Closed không cộng lại phần chưa giao đã chuyển/hủy: chỉ giữ hóa đơn đã ghi của nguồn đóng. Hóa đơn trộn nguồn mở/đóng phải đối soát, không tự đoán phân bổ. Không sửa sổ hoặc giá trên chứng từ. Thêm chặn hồ sơ Dũng cộng Accounts Manager ở ba thao tác giá thành. Kiểm cục bộ268 kh_aph +107 lab9x=375 ca đạt. B014 nay mong24 PASS gồm restore, toàn artifact dự kiến215 kết quả PASS.

ĐANG DỞ: CI phải xanh trên SHA mới; các mốc cũ bên dưới là lịch sử. Chưa phát hành/triển khai, production0.15.1. Nghiệm thu dữ liệu/người dùng/máy in thật vẫn gom sau khi khách sẵn sàng danh mục/tồn kho.

## 17/10/2026 — Khép luồng tiền và phạm vi báo cáo (đang kiểm)

Tiếp tục PR #4 theo xác nhận của anh Tiến: rà thu/cọc–phân bổ–bàn giao–sao kê, nhà máy và tài chính bằng dữ liệu giả; gom nghiệm thu thật sau khi có danh mục/tồn kho. Production vẫn0.15.1.

Bản sửa: xác nhận nhận tiền nhà máy kiểm quyền phiếu/Company, chặn sửa tay kết quả ghi sổ và gắn JE có sẵn, kiểm số tiền hữu hạn/tối đa2 số lẻ. Sao kê kiểm quyền File/Account; lưu mẫu dùng quyền write Bank và save chuẩn. Phiếu tiền/cọc ghi đúng tham chiếu thực thu/chi vào JE; mã giao dịch chung theo Account áp PE/JE/FundsReceipt/FundsAction, khóa tài khoản và đọc hiện tại để chặn nhập đồng thời qua các lối khác nhau. Xác minh khách/tạo kế hoạch chỉ POST.

Báo cáo lãi gộp/dòng tiền/công nợ giới hạn Company được cấp; lọc ngoài phạm vi bị chặn. Phân loại đối tác nội bộ vẫn xét đủ đơn vị để không tính nhầm dự thu/chi. Người chỉ xem một phần không được ghi xác nhận công nợ chung toàn khách; báo cáo không so số dư một phần với số xác nhận chung. Hồ sơ Dũng vẫn chặn dù cộng Accounts Manager.

Kiểm cục bộ trước mở rộng phạm vi sổ quỹ/vay:264 kh_aph +107 lab9x=371 ca đạt. Đã bổ sung kiểm Company cho sổ quỹ, công nợ giám đốc, khế ước và khóa/mở khóa kỳ; lấy danh sách khế ước qua quyền native thay get_all. Có ca HTTP scope APH cùng đối chứng ngoài phạm vi VH. UAT mở rộng: funds20, b0111=15, b0114=8, b014=23 (gồm restore); thêm tài khoản giới hạn Company, tệp riêng không chia sẻ, chặn sửa mẫu Bank không có quyền và hai phiên tạo JE cùng mã. Giữ các ca nghiệp vụ cũ, không nới assertion. Cần đọc CI trên SHA mới; mốc7827add không nghiệm thu cho thay đổi này.

ĐANG DỞ: đẩy bản sửa và chạy UAT/Cổng2/2b/3, sửa nguyên nhân nếu lỗi; đọc artifact đối chiếu/khôi phục. Không tag/merge/triển khai. Các nghiệp vụ giá thành/nhà máy và tài chính có sẵn được hồi quy trong cùng bộ UAT; chưa coi nghiệm thu người dùng thật hoặc toàn bộ202 quyết định hoàn tất.

## Mốc kiểm ngày 17/10/2026 — hồ sơ giao nhận và hàng đợi tiền

Mã nguồn ứng viên `7827add608f7cee8af59c62f69df506660c8cbc3`, PR #4, nhánh `feat/ho-so-giao-nhan-20261017`. Chưa phát hành hoặc triển khai; production vẫn 0.15.1. Người dùng yêu cầu tiếp tục bằng dữ liệu giả và gom nghiệm thu thực tế sau khi có danh mục hàng/tồn kho.

Đã có bản ký riêng tư gắn đúng Delivery Note, ghi chú chênh lệch, người/thời điểm đối chiếu. Kiểm quyền đọc/ghi và modified; thay tệp/ghi chú làm mất dấu đối chiếu. Chặn xóa blob trước native File.on_trash bằng extend_doctype_class; chặn công khai/đổi liên kết tệp đang tham chiếu. Có nút gỡ bản ký trên phiếu, không bắt đính kèm khi giao/nhận. Không ghi sổ lần hai. Workspace Bán hàng và Tiền/vay gom phiếu thiếu hồ sơ, chờ đối chiếu, tiền chưa rõ khách, phân bổ nháp, bàn giao tiền chờ nhận/chênh lệch.

Cổng 1: 254 kh_aph + 107 lab9x = 361 ca đạt (Python 3.12/Jinja2). UAT run 39011438406: 209 kết quả PASS/0 FAIL trong artifact, gồm 21/21 b014 và khôi phục; có ảnh Desk, kiểm tải lại blob sau yêu cầu xóa bị chặn. Cổng 2 run39011440839 đạt; Cổng 2b39011438502 đạt. Cổng 3 run39011438376 đạt: so schema, quay lui chủ động và nâng lỗi tự quay lui/giữ bảo trì, dấu vân dữ liệu khớp. Đủ bốn cổng trên SHA7827add. Các bằng chứng này thuộc SHA7827add; cập nhật tài liệu sau đó không được gọi là kiểm lại mã nguồn mới.

ĐANG DỞ: không coi toàn dự án hoàn tất. Theo `docs/nghiem-thu-tong-the.md` tiếp tục rà các khoảng trống thực sự trong luồng giữ tiền/nhà máy/tài chính; nhiều mục trong bảng 202 ngày14/10 đã được làm ở0.11.x–0.14, không xây lại theo bảng lịch sử. Nghiệm thu bằng nhân sự/máy in/dữ liệu thật còn chờ danh mục/tồn kho/số dư và cấu hình khách. Không tự tag, merge hoặc triển khai production.


## 17/10/2026 — Phát triển tiếp, gom nghiệm thu thực tế sau khi có dữ liệu

Anh Tiến xác nhận chưa có danh mục hàng/tồn kho nên chưa thử thực tế; yêu cầu tiếp tục hoàn thiện và nghiệm thu tổng thể sau. Không chặn phát triển vì thiếu dữ liệu thật. Nhánh `feat/ho-so-giao-nhan-20261017` từ mốc bàn giao 6fe0cd7; production vẫn 0.15.1, chưa tag/triển khai mới.

Đã viết hồ sơ bản ký trên Delivery Note, dùng cờ Trung tâm Bán hàng hiện có: tệp riêng gắn đúng phiếu, ghi chú chênh lệch, người/thời điểm đối chiếu có kiểm quyền write và chống phiếu cũ. Thay tệp/ghi chú làm mất dấu đối chiếu; không bắt buộc đính kèm khi giao/nhận, không ghi GL/SLE. Workspace có phiếu đã nhận thiếu bản ký / bản ký chưa đối chiếu. Chặn xóa tệp đang là bản ký. Có 13 ca unit và ca HTTP/Chrome mới trong b014 (mong 21 PASS gồm restore). Cổng 3 nâng baseline lên digest production 0.15.1 đúng mốc VM.

Bổ sung lối vào Tiền và vay cho tiền thực nhận/chưa rõ khách, phân bổ nháp, tuyến đã duyệt, bàn giao nhà máy chờ nhận/chênh lệch; dùng nguyên quyền và chứng từ nguồn. Kịch bản gom nghiệm thu: `docs/nghiem-thu-tong-the.md`. Kiểm cục bộ: 252 ca kh_aph và 107 ca lab9x đạt (Python 3.12, Jinja2).

ĐANG DỞ: chạy UAT/Cổng 2/2b/3 trên SHA mới, xử lý lỗi thực nếu có; kiểm UI hồ sơ. Tiếp theo hoàn thiện tiền/đối soát, nhà máy, tổng hợp tài chính theo thứ tự đã chốt. Nghiệm thu nhân sự và máy in thật chưa làm; không tuyên bố toàn dự án hoàn tất.

## Mốc hiện tại — 17/10/2026 13:22 (Việt Nam): frontend 0.15.1

| Mục | Giá trị |
|---|---|
| Production | Site `frontend`, VM `erpnext-prod`; kh_aph 0.15.1, lab9x 0.2.10, ERPNext 16.51.1/Frappe 16.52.0 |
| Nguồn | Tag `v0.15.1` → `b803c7a95e13c57af3a0f58da6e0c8ea48079db2` |
| Image | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.15.1` |
| Digest | `sha256:c4b61eb4b2924d50f64bbeaf83623da3e7259f9484b28d6f3e228939912edf47` |
| CI/phát hành | [Run 39005035290](https://github.com/tienduongmarcom/aphvh/actions/runs/39005035290), attempt 1: UAT/Cổng 2/Cổng 2b/Cổng 3 và đẩy image đạt, đúng SHA |
| Diễn tập VM | Lượt `10170555e7bc7c`: tong/dem/chi_tiet khớp, `DIỄN TẬP 0.15.1: ĐẠT`, theo log anh Tiến gửi |
| Triển khai VM | Anh Tiến gửi log digest khớp và `=== XONG 0.15.1: ĐẠT ===` lúc 13:22; Codex không trực tiếp SSH/kiểm Desk production |
| Quay lui khi cần | Theo `quay-lui.sh` và đúng sao lưu ngay trước nâng trong `~/erp/aph-vh/sao-luu/`, kiểm `phien-ban-truoc.txt` = `0.14.3` và checksum; không tự chọn sao lưu cũ |
| Việc còn mở | Kiểm vận hành giao diện/quyền với nhân sự thật; hồ sơ bản ký/ca tiền/nhà máy/tài chính mới. Không tuyên bố toàn dự án hoàn tất |

Các mốc bên dưới được giữ nguyên làm lịch sử; thông tin production/ứng viên cũ không còn là trạng thái hiện tại. Giữ nguyên tag đã phát hành.

## 17/10/2026 11:25 — 0.15.0 chưa phát hành, chuẩn bị 0.15.1

v0.15.0=c236b27 giữ nguyên. Run phát hành38998723309 attempt1/2: UAT/Cổng2/Cổng3 đạt, Cổng2b503 sau nâng B rồi kéo image thiếu; job đẩy image chưa chạy. Ứng viên0.15.1 sửa phép kiểm: xác nhận B HTTP-ready trước thử kéo image lỗi, sau đó vẫn đòi200 ngay sau thao tác; probe có deadline và kiểm body pong, có3 ca HTTP thật. Cổng2b nay tự chạy trên nhánh PR #3. ĐANG DỞ: CI SHA mới phải đủ4 cổng xanh trước tag mới. Chưa có tag0.15.1, chưa merge/phát hành/triển khai; production không đổi.

## 17/10/2026 09:20 — Sửa fixture Warehouse User Permission

SHA 76f6bde: Cổng 2 38987997088 / Cổng 3 38987993537 xanh, UAT 38987993529 lỗi đối chứng dương scope_wh do Company có kho chuyển tiếp mặc định ngoài kho chính. Sửa tài khoản UAT áp Warehouse permission vào đúng 4 DocType Warehouse/SO/DN/đơn chung; không mở thêm kho, không bỏ kiểm quyền. Ba ca nhiều kho/sửa nháp/Company đã đạt, restore đạt; Warehouse và rollback nhóm sau còn chờ. ĐANG DỞ: CI SHA mới, chưa tag/phát hành/triển khai.

## 17/10/2026 — PR #3 mở rộng nghiệm thu nhiều kho/phạm vi quyền

PR #2 a271099 đã xanh đủ UAT/Cổng 2/Cổng 3 (38925577491 / 38925582784 / 38925578136). PR #3 mốc 8705848 đã xanh đủ (38925615925 / 38925623196 / 38925615939), có quay lui và nâng lỗi. Nay bổ sung 5 ca HTTP nhiều kho, native lỗi nhóm sau, sửa nháp, User Permission Company/Warehouse, kiểm scope khi in/thử lại. ĐANG DỞ: chờ CI SHA mới; kết quả mốc cũ không nghiệm thu thay đổi mới. Production vẫn 0.14.3/digest bên dưới; chưa tag/phát hành/triển khai.

## 16/10/2026 22:40 — Sửa vị trí ca kiểm workflow

CI SHA 25974b9 / bd66e95 dừng build: test mới đọc `.github/workflows` nhưng Docker loại `.github` khỏi image. Chuyển nguyên ca kiểm ranh giới sang `deploy/release/test_print_defaults_gate.py`, chạy bắt buộc ngay sau checkout Cổng 3; test bộ cài vẫn chạy trong image. Không skip ca, không nới assertion, không thêm workflow vào image production. ĐANG DỞ: kiểm cục bộ rồi đẩy hai PR, đọc CI SHA mới; frontend không đổi.

## 16/10/2026 22:20 — Ứng viên đang sửa Cổng 3, chưa phát hành

PR #2 3b01cc7 / PR #3 8952265: UAT và Cổng 2 đạt; Cổng 3 (38897717545 / 38897741846) lỗi so schema mẫu in bước 5. Chưa chạy các bước quay lui phía sau. Sửa nhận mẫu Classic trong lab9x 0.2.10 và thu hẹp ngoại lệ schema chỉ 6 chứng từ native, giữ so nghiêm 5 mẫu app. Test mới: bộ cài mới/nâng cấp/mẫu riêng/idempotent và phạm vi ngoại lệ. ĐANG DỞ: chờ CI SHA sau sửa; chưa kết luận đủ cổng. Production vẫn mốc 0.14.3/digest bên dưới; không tag/merge/phát hành/triển khai.

| Mục | Giá trị |
|---|---|
| Production (site `frontend`, VM `erpnext-prod`) | **kh_aph 0.14.3**, lab9x 0.2.9, ERPNext 16.50.0 + Frappe 16.51.0 |
| Image production | `ghcr.io/tienduongmarcom/kh-aph-erpnext:0.14.3` — digest `sha256:706bf959addeca5bcb255fee0437ae7aeb355d910d1fc0625ae93fe66367ebc8` |
| Lên production lúc | 16/10/2026 ~16:29 (diễn tập tách biệt ĐẠT 16:23: tong + dem + chi_tiet khớp), 21 cờ bật |
| Nguồn | commit `b14ad8d` (tag `v0.14.3`); CI xanh trên đúng commit (UAT 38840547684, Cổng 3 38840547719) |
| Quay lui về | bản sao lưu trước nâng cấp trong `~/erp/aph-vh/sao-luu/` (thư mục có `phien-ban-truoc.txt` = `0.14.2`, có `sha256.txt`): `./quay-lui.sh <thư mục>` |
| Ứng viên | Nền **0.14.4** `thu/erpnext-v16.51.1` (PR #2); tính năng **0.15.0** `feat/ban-hang-nhanh-20261016` dựa trên nền đó; chưa phát hành/triển khai, chờ CI |
| CI bắt buộc trước khi gắn tag | UAT candidate, Cổng 2, Cổng 3 xanh trên đúng commit |
| Thủ tục | `bash deploy/release/dien_tap_ban_sao.sh <PB>` → `bash deploy/release/trien_khai_frontend.sh <PB>` (≤ 12 giờ sau) |
| Lịch người dùng | Bắt đầu dùng thử 18/10/2026 |

Lịch sử: 0.14.2 (15/10 ~22:44, `0f528c3c…`), 0.14.0 (15/10 ~15:45, `3a259c9b…`), 0.13.0 (`e3136592…`), 0.12.1 (`897f81c2…`), 0.11.4 (`54bf5a99…`), 0.11.3 (`716f1401…`),
0.11.2 (`f2417393…`), 0.11.1 (`9335dfa1…`).
