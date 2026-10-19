# Nối quỹ nhà máy, chốt ca tự thân và bảng chốt ngày — đợt2B

## 1. Mục tiêu và giới hạn

Hoàn thiện phần kỹ thuật còn lại của đợt2B trên nền PR #15/35d7d42: phiếu quỹ nhà máy dùng chung giữ chỗ/bàn giao/đối chiếu/hoàn; người bán/nhà máy tự kiểm đếm chốt ca; kế toán trưởng xem tiền–hàng–nợ và việc tồn. Không thực hiện đợt3 nhập sản xuất một lần, đợt4 chốt tháng/báo cáo điều hành toàn chuỗi hoặc đợt5 hóa đơn một phần/MISA. Nghiệm thu nhân sự/dữ liệu/máy in thật vẫn gom cuối theo anh Tiến.

## 2. Hiện trạng và bằng chứng nguồn

Production được người vận hành xác nhận0.15.3,21 cờ. PR #15 đã đủ4 cổng,268 HTTP/Desk, chỉ xem tiền cá nhân. Nguồn chính: factory_cash.py, cash_handover.py, cash_issue.py, cash_closing.py, personal_cash.py. Lối quỹ cũ ghi JE trực tiếp khi nhận; phiếu chờ chưa có giữ chỗ. Không dùng kết quả PR #15 thay bằng chứng mã mới.

## 3. Quy trình và trách nhiệm

Người thực giữ được ghi rõ tự lập/gửi Phiếu quỹ nhà máy, chọn người và quỹ nhận trước khi gửi; không suy owner. on_submit tạo đúng một APH Ban giao tien và giữ chỗ cùng transaction. Người nhận tự đếm, dùng nút cũ hoặc bàn giao native đều gọi cùng service canonical. Cùng Cash chỉ đổi trách nhiệm; khác Cash/nộp Bank một JE. Người đã nhận tự tạo hoàn toàn bộ; người giao ban đầu tự nhận lại. Kế toán trưởng đối chiếu vụ lệch bằng mốc mới/ca khớp/tệp căn cứ hiện có; phiếu nhà máy phản ánh trạng thái đối chiếu, không đổi số nhận gốc.

Người giữ mở Chốt ca tiền của tôi trên Khách hàng/Phiếu quỹ nhà máy, nhập thực đếm/lý do/người/hạn khi lệch, xem số phải có rồi tự xác nhận. Người quản lý không chốt hoặc nhận thay. Bảng Chốt ngày và cần xử lý nằm trong Tiền và vay, chỉ đọc; thao tác xử lý quay về nguồn, không thêm cấp duyệt hoặc DocType nhiệm vụ.

## 4. Quy tắc và ngoại lệ

Cờ25 `kh_aph_factory_handover` mặc định tắt, cần factory_cash/custody/closing/handover. Cờ tắt giữ đường cũ cho phiếu chưa nối; phiếu đã nối tuyệt đối không quay về đường JE cũ khi tắt cờ. Phiếu cũ đã nhận chỉ replay đúng kết quả cũ, giữ JE/lịch sử. Phiếu cũ còn chờ, chưa có JE phải được đúng người giữ chuyển tiếp/giữ chỗ; thiếu người giữ hoặc mốc/khả dụng thì từ chối, không tự gán lịch sử. Thay quỹ nhà máy khi còn hồ sơ phải đối chiếu trước, không tự chuyển sang quỹ mới.

Hủy đề nghị chưa nhận giải phóng giữ chỗ nhưng giữ nguồn/vụ lệch/tệp; đã nhận dùng hoàn, không hủy JE tay. Hoàn đúng toàn bộ số đã nhận, đúng quỹ/người gốc; không cho chi Bank tùy ý. Thiếu/thừa/vượt nguồn dùng nguyên quy tắc canonical: số nhận, lý do, người/hạn xử lý, không chi vượt nguồn và không sửa số cũ. Nhóm trách nhiệm/chưa rõ âm hoặc ví còn vụ lệch thì chặn giao ra. Tiền lịch sử chưa rõ vẫn tách riêng.

## 5. Dữ liệu và trạng thái

Nguồn thêm tai_khoan_nhan (Data tên Account được server kiểm), quy_giao và ban_giao_tien (server), xu_ly_chenh_lech (server). H thêm factory_source duy nhất cho phiếu gốc; hoàn dùng reversal_of hiện có. Không tạo sổ tiền thứ hai. Chốt cá nhân vẫn lưu APH Chot ca tien; hai dấu server personal_request/personal_payload bảo đảm retry đúng actor/Company/Cash/nội dung. Snapshot/transfer_hash/previous_shift/closed_at dùng nguyên cơ chế canonical. Nháp lỗi thời phải lập lượt mới, không tự cập nhật số trước khi xác nhận.

Bảng ngày: tiền/cọc/việc tồn theo hiện tại; tiền thực đếm ghi rõ thời điểm ca gần nhất. Công nợ Customer từ PLE chưa delink đến ngày chọn: đầu ngày+tăng−giảm=cuối; cọc/chưa phân bổ riêng theo nguồn Funds. Hàng gồm phiếu trong ngày và hồ sơ ký/chênh lệch còn tồn, lượng theo từng mã/kho/đơn vị, số bao có sẵn trên nguồn. Ngoại lệ gồm hủy nguồn tiền/nợ, hoàn khách và hóa đơn trả/giảm trong ngày. Sao kê chỉ đọc Bank Transaction native đã lưu và phân bổ; kết quả đối chiếu tệp tạm hiện không lưu nên không tự coi là đã khớp. Chưa có dữ liệu phải hiển thị rõ. Tối đa5.000 dòng mỗi tập,30 Cash/100 nhóm trách nhiệm mỗi quỹ; vượt giới hạn báo lỗi, không cắt số liệu.

## 6. Phân quyền và kiểm soát

Không sửa C.guard hoặc cấp DocPerm GL/JE/H/snapshot cho nhà máy. Capability server sống trong ContextVar của đúng actor, nguồn và bộ Company/quỹ/người/số tiền; không whitelist context. Chỉ nguồn đã xác thực cho phép insert/update H hoặc JE chuyển tiền liên kết; dịch vụ thường giữ native permission. NoCost/nhà máy kể cả cộng quản lý vẫn chỉ tiền cá nhân tại quỹ cấu hình, Company/Account User Permission. Danh sách quỹ nhận chỉ tên tài khoản tiền VND cùng Company, đã lọc User Permission; không trả số dư/quỹ khác công ty. Người nhận nhà máy chỉ nhận vào quỹ cấu hình. Facade không trả JE cho NoCost; chốt cá nhân không trả source_rows/hash/phân bổ người khác. Native đọc GL/H/snapshot vẫn chặn. Bảng ngày chặn NoCost/nhà máy kể cả cộng quản lý và cần quyền quản lý + từng nguồn/Company/Account.

## 7. Tác động hệ thống

Gửi giữ chỗ/chốt ca/đối chiếu/bảng ngày không ghi GL/PLE/doanh thu/nợ/kho/giá vốn/sản xuất/MISA. Nhận khác quỹ và hoàn khác quỹ chỉ một JE chuyển hai tài khoản tiền, metadata đúng người; cùng Cash chỉ delta trách nhiệm. Không ghi thu khách lần hai. Khóa Cash theo Company trước nguồn/H; retry toàn RPC khi MariaDB xung đột, không commit giữa chuỗi. Chốt ca lưu số thực đếm làm bằng chứng, không thay số đầu hay xóa thiếu/thừa.

## 8. Tiêu chí kiểm

Unit và HTTP/Chrome trên dữ liệu giả: cờ tắt/thiếu cờ, role/Company/Account/actor/source/hoàn sai bộ; legacy đã nhận giữ nguyên, legacy chờ phải chuyển tiếp; nguồn mới bắt chọn đích và người giữ tự gửi; hai phiên qua hai lối nhận chỉ một H/JE, không thêm PE/PLE; cùng Cash thiếu5 không JE/chặn giao mới; mốc mới+ca tự thân+tệp đóng vụ và đồng bộ nguồn; hủy giữ chỗ giữ lịch sử; nhận lại hoàn Cash/Bank bằng người nhà máy không cấp GL; chốt đúng mình/retry/chốt đồng thời/nội dung khác/nháp lỗi thời. Chrome dùng phiên nhân sự riêng, bỏ200 sau lưu nháp và sau chốt rồi retry cùng cửa sổ chỉ một ca; bảng native đúng quyền/nhóm. Bảng ngày so tiền với ca, sao kê native chưa rõ12, công nợ giữ dấu, có lượng/hồ sơ hàng, đọc không đổi sổ. Bốn cổng cùng mã, đọc artifact và ảnh trước ghi PASS. Chưa có bằng chứng thì trạng thái đang kiểm.

## 9. Triển khai và khôi phục

Chưa tăng version/tag/merge/deploy. Candidate25 cờ, production21. Schema chỉ qua bộ cài rõ ràng; reload nguồn/H/ca/report và cập nhật Workspace, không after_migrate tự bật. Cờ25 đã bổ sung đồng bộ bộ cài, handoff, dấu vân, quay lui và Cổng3. UAT giữ cờ25 tắt cho hồi quy lối cũ, bật riêng cuối b014 (nạp lại backend), rồi trả tắt trong finally. Cổng3 bật4 cờ tiền khi nâng từ0.15.3 và kiểm trả về0 khi rollback. Khi phát hành vẫn diễn tập trên bản sao production có dữ liệu, so đếm/tổng/chi tiết/schema/cờ/versions; khôi phục image+DB/files/cờ đồng thời, giữ bảo trì khi lỗi. Không tắt riêng cờ để bỏ projection sau phát sinh.

## Truy nguyên bộ ca tích hợp

Bộ chạy `deploy/uat/http/b014_factory_handover.py` tạo dữ liệu giả, kiểm qua HTTP với phiên nhân sự riêng và khôi phục baseline. Bật cờ25 chỉ trong lát cuối; không thay kết quả hồi quy lối cũ. Mỗi hàng dưới là một case JSON trong artifact `http-b014-evidence.txt`:

| Case | Đầu vào/thao tác và kết quả bắt buộc |
|---|---|
| HTTP_2B_FACTORY_TRANSITION_OFF_HISTORY | Cờ tắt vẫn lối cũ; đã nhận5 chỉ replay; nguồn chờ20 không nhận thẳng khi chưa chuyển tiếp giữ chỗ |
| HTTP_2B_FACTORY_RESERVE_SCOPE | Đúng người giữ chuyển tiếp20: một H, giữ chỗ20, khả dụng580; native H/GL vẫn chặn nhân sự nhà máy |
| HTTP_2B_FACTORY_TWO_ROUTES_ONE_JE | Hai phiên người nhận gọi lối cũ và native cùng lúc: cùng kết quả, một JE/hai GL, không thêm thu khách/nợ |
| HTTP_2B_FACTORY_REVERSE_RESTRICTED | Người nhận tạo hoàn20, người nhà máy nhận lại: một JE hoàn, JE gốc giữ nguyên, không cấp GL |
| HTTP_2B_FACTORY_SAME_CASH_ISSUE | Giao30 nhận25 cùng Cash: lệch−5 được lưu, không JE, chặn giao mới |
| HTTP_2B_FACTORY_OWN_SHIFT | Cùng request chỉ một nháp, đổi nội dung/người chốt bị chặn; hai phiên tự chốt chỉ một ca, không GL/quyền đọc snapshot native |
| HTTP_2B_FACTORY_RESOLVE_CANCEL_AUDIT | Xác minh mới + ca khớp hai phía + tệp: đóng vụ không JE; hủy đề nghị10 giải phóng giữ chỗ, không xóa lịch sử |
| HTTP_2B_FACTORY_BANK_AND_RETURN | Nộp Bank10 rồi hoàn đúng người/quỹ: hai JE chuyển tiền tổng cộng, không công nợ khách |
| HTTP_2B_FACTORY_STALE_SHIFT | Sau preview có JE mới: xác nhận ca bị từ chối, không chốt dở hay thêm sổ, giữ nháp cũ |
| DESK_2B_FACTORY_SHIFT_RETRY | Chrome phiên nhà máy bỏ200 sau lưu nháp và sau chốt, retry cùng cửa sổ: chỉ một ca đã chốt, số phải có/thực575 |
| HTTP_2B_FACTORY_DAY_CLOSE | Quỹ575 và lần đếm575, sao kê native chưa rõ12, hàng/nợ có đối chiếu; chặn NoCost/khác Company, đọc không đổi sổ |
| DESK_2B_DAY_CLOSE | Chrome phiên kế toán trưởng mở native report đủ8 nhóm; không popup ValidationError đã xử lý che bảng |

Nghiệm thu tài khoản nhân sự thật và số dư thật vẫn là bước riêng; bộ ca này không chứng minh tải lớn hoặc hoàn tất đợt3–5.

## Bằng chứng mã cuối đã hoàn tất

Mã nghiệp vụ/kiểm `d0c1f16fb7287da84066f9142bc304be2f616918`:394+108 unit đạt; [UAT39264977970](https://github.com/tienduongmarcom/aphvh/actions/runs/39264977970) đạt280 HTTP/Desk,0FAIL/b01489, artifact đã đọc, ảnh ca nhà máy và bảng ngày đã xem. Report không còn popup đã xử lý, vẫn giữ dòng cần xác minh. [Cổng2](https://github.com/tienduongmarcom/aphvh/actions/runs/39264983886) và [Cổng2b](https://github.com/tienduongmarcom/aphvh/actions/runs/39264983968) đạt; [Cổng3](https://github.com/tienduongmarcom/aphvh/actions/runs/39264989203) đạt; artifact đã đọc: schema1.065/1.065, rollback1.052/1.052, bốn cờ mới trả0, dữ liệu/versions khớp và ca cố ý lỗi tự quay về0.15.3/giữ bảo trì. Nền CI GL0 không thay diễn tập dữ liệu production khi phát hành. Không phát hành hoặc nghiệm thu dữ liệu thật từ bằng chứng này.
