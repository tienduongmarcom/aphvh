// Thông tin nhận diện và nợ tại đơn; chỉ đọc, không sửa snapshot/chứng từ đã lưu.
frappe.provide("kh_aph.ux");
(function () {
    const esc = value => frappe.utils.escape_html(String(value || ""));
    const money = value => format_currency(Number(value || 0), "VND");
    function context(frm) {
        if (!frappe.boot?.kh_aph?.ux_task_first) return;
        const customer = frm.doc.customer, generation = (frm.__context_generation || 0) + 1;
        frm.__context_generation = generation;
        if (!customer) {frm.__customer_context?.empty(); return;}
        // Giữ hai thông tin luôn hiện nhưng không nhân đôi với các ô fetch_from cũ.
        frm.toggle_display(["customer_phone", "customer_address"], false);
        const section = frm.__customer_context?.[0]?.isConnected ? frm.__customer_context :
            frm.dashboard.add_section('<div class="kh-customer-context"></div>');
        frm.__customer_context = section;
        frm.dashboard.show();
        if (!section.find(".kh-customer-context").length) section.html('<div class="kh-customer-context"></div>');
        const box = section.find(".kh-customer-context");
        box.text("Đang tải hồ sơ khách…");
        const current = () => frm.doc.customer === customer && frm.__context_generation === generation;
        let identity = null, debt = null, identityFailed = false, debtFailed = false;
        const render = () => {
            if (!current()) return;
            const person = identity ? `<div><b>${esc(identity.customer_name)}</b> · ${esc(customer)}</div>
                <div>Điện thoại: <b>${esc(identity.mobile_no || "Chưa có số điện thoại")}</b></div>
                <div>Địa chỉ: ${esc(identity.primary_address || "Chưa có địa chỉ")}</div>` : `<div>${identityFailed ? 'Không tải được hồ sơ khách. Kiểm tra lại trước khi xác nhận đơn.' : 'Đang tải hồ sơ khách…'}</div>`;
            let balance = `<div class="text-muted">${debtFailed ? 'Chưa kiểm tra được công nợ; không coi số chưa tải là bằng không.' : 'Đang kiểm tra công nợ…'}</div>`;
            if (debt) {
                const sum = key => debt.don_vi.reduce((n, r) => n + Number(r[key] || 0), 0);
                balance = debt.xem_hoa_don ? `<div>Còn phải thu theo hóa đơn: <b>${money(sum("phai_thu"))}</b>
                    · Trong đó quá hạn: <b>${money(sum("qua_han"))}</b> <button type="button" class="btn btn-default btn-xs kh-debt-detail">Xem chi tiết</button></div>`
                    : '<div class="text-muted">Công nợ: không có quyền xem hóa đơn. Không suy là khách hết nợ.</div>';
                if (debt.xem_tien && sum("chua_phan_bo") > 0) balance += `<div>Tiền đã nhận chưa phân bổ: ${money(sum("chua_phan_bo"))}</div>`;
            }
            box.html(person + balance);
            box.find(".kh-debt-detail").on("click", () => {
                const rows = debt.don_vi.map(r => `<tr><td>${esc(r.company)}</td><td>${money(r.phai_thu)}</td><td>${money(r.qua_han)}</td><td>${debt.xem_tien ? money(r.chua_phan_bo) : "Không có quyền xem"}</td></tr>`).join("");
                const dialog = new frappe.ui.Dialog({title: "Công nợ trong phạm vi được xem", size: "large", fields: [
                    {fieldtype: "HTML", options: `<table class="table"><thead><tr><th>Công ty</th><th>Còn phải thu</th><th>Quá hạn</th><th>Chưa phân bổ</th></tr></thead><tbody>${rows}</tbody></table><p>Tiền chưa phân bổ được giữ riêng; không tự cấn nợ giữa các công ty. Chi tiết tính từ hóa đơn đã ghi sổ.</p>`}
                ]}); dialog.show();
            });
        };
        frappe.call({method: "kh_aph.ux_task.customer_identity", args: {customer}}).then(r => {
            if (!current()) return; identity = r.message; render();
        }, () => {if (current()) {identityFailed = true; render();}});
        frappe.call({method: "kh_aph.ux_task.cong_no_khach", args: {customer}}).then(r => {
            if (!current()) return; debt = r.message; render();
        }, () => {if (current()) {debtFailed = true; render();}});
    }
    frappe.ui.form.on("APH Shared Sales Order", {
        setup(frm) {if (frappe.boot?.kh_aph?.ux_task_first) frm.set_query("customer", () => ({query: "kh_aph.ux_task.customer_query"}));},
        refresh: context,
        customer: context
    });
})();
