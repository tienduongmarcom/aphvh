# APH–VH–MK–TL — bàn giao ứng viên UAT

Đọc [HANDOFF_20261012.md](HANDOFF_20261012.md) trước. Báo cáo nghiệm thu: [ACCEPTANCE_20261011.md](ACCEPTANCE_20261011.md). Bằng chứng baseline hiện hành: [handoff-20261012.json](handoff-20261012.json). `candidate-20261011.json` và ZIP 07:14 là lịch sử ban đầu, không dùng làm gói release mới.

Production mới là `frontend`, không dùng `erpnext.local`. TL = XB. Runtime kiểm được: Frappe 16.35.0, ERPNext 16.36.1, kh_aph 0.9.1, lab9x 0.2.0. Nhánh là draft UAT, không tự merge/publish/deploy.

Setup chỉ trên `aphvh-web-uat` trắng, Administrator, database/Redis và container riêng. Không chạy runner này trên VM production. Sáu flag cần bật rõ ràng trong UAT:

- kh_aph_server_cost_guard
- kh_aph_post_receivable_on_delivery
- kh_aph_shared_sales_order
- kh_aph_global_credit_warning
- kh_aph_high_risk_credit_guard
- kh_aph_quantity_valuation_mvp

```sh
bench --site aphvh-web-uat execute kh_aph.uat_candidate_setup.setup_uat
bench --site aphvh-web-uat clear-cache
```

Setup lặp idempotent; bổ sung schema ứng viên và giữ native permissions. Số schema hiện hành xem log fresh-site-evidence, không dùng số 13 field của bản cũ. `uat_wsgi` chỉ dùng trong container cô lập, phục vụ assets cho test Chrome; production vẫn dùng nginx theo cấu hình hiện tại.

CI build image không publish, kiểm hash/runtime, cổng site trắng, 14 bản ghi cost, 48 dispatch và 21 inventory/Desk, mọi restore và cleanup. 21 gồm 20 ca nghiệp vụ + restore; chỉ PASS khi log có đủ và không FAIL. Native Desk test chốt giá qua nút/dialog và kiểm preview 3 bao thành 75 kg, giá bao 500.000. Không suy ra toàn bộ Desk đã nghiệm thu.

Vận hành: input giá theo VND/kg; bao nguyên × quy cách snapshot = kg; Item quản lý bao có stock UOM Kg. Hàng chờ giá dùng APH Pending Receipt, không PR giá 0; người được phép chốt bằng nút Chốt giá nhập. LCV theo kg dùng Distribute Manually + kh_aph_by_kg. Sản xuất dùng Đóng gói theo kg hoặc Sản xuất theo kg qua BOM/Work Order; hao hụt tự nhiên lưu lý do, hao hụt bất thường xuất chi phí riêng.

Tiền/cọc liên company theo kế hoạch, đổi nguồn sau giao, toàn bộ native Desk/role thật, COGS backdated và migration tồn bao vẫn có gate trong HANDOFF. MISA chỉ hóa đơn thuế. Không tự FIFO, tự đổi bank hoặc tự dùng cọc cho nợ cũ. Nghiệm thu toàn bộ 202 cần đối chiếu bản nguyên văn.
