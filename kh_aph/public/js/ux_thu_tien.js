// UX-3: tìm khách (mã/tên/MST/điện thoại) và thu tiền 5 bước. Ghi bằng hàm thu tiền ĐÃ KIỂM `kh_aph.ban_quay.thu_tien`:
// chỉ phân bổ vào các hóa đơn người dùng chọn theo đúng thứ tự chọn, phần còn lại là CHƯA PHÂN BỔ. Không FIFO, không cấn chéo đơn vị.
frappe.provide("kh_aph.ux");
if (!kh_aph.ux.tim_khach) {
    const vnd = v => format_currency(v || 0, "VND");
    kh_aph.ux.tim_khach = function(on_pick) {
        const d = new frappe.ui.Dialog({title: "Tìm khách", fields: [
            {fieldname: "q", label: "Mã, tên, tên gọi tắt, MST hoặc số điện thoại", fieldtype: "Data", reqd: 1},
            {fieldname: "kq", fieldtype: "HTML"}],
            primary_action_label: "Tìm", primary_action(v) {
                frappe.call({method: "kh_aph.ux_task.tim_khach", args: {q: v.q}, callback(r) {
                    const rows = r.message || [];
                    const box = d.fields_dict.kq.$wrapper.empty();
                    if (!rows.length) return box.html("<p>Không thấy khách trong phạm vi quyền. Kiểm tra lại số hoặc tên.</p>");
                    if (rows.length > 1) box.append(`<p class="text-warning"><b>${rows.length} khách khớp — chọn đúng khách, không chọn đại.</b></p>`);
                    rows.forEach(x => $(`<button class="btn btn-default btn-block text-left mb-2" style="font-size:15px">
                        <b>${frappe.utils.escape_html(x.customer_name || x.name)}</b> · ${frappe.utils.escape_html(x.name)}
                        ${x.tax_id ? " · MST " + frappe.utils.escape_html(x.tax_id) : ""}${x.mobile_no ? " · " + frappe.utils.escape_html(x.mobile_no) : ""}
                        <span class="text-muted"> (khớp ${frappe.utils.escape_html(x.khop)})</span></button>`)
                        .appendTo(box).on("click", () => { d.hide(); on_pick(x.name); }));
                }});
            }});
        d.show();
    };

    kh_aph.ux.thu_tien = function(customer, chon_san = []) {
        if (!customer) return kh_aph.ux.tim_khach(c => kh_aph.ux.thu_tien(c));
        frappe.call({method: "kh_aph.ux_task.cong_no_khach", args: {customer}, callback(r) {
            const cn = r.message;
            const don_vi = cn.don_vi || [];
            const request_id = [...crypto.getRandomValues(new Uint8Array(16))].map(v => v.toString(16).padStart(2, "0")).join("");
            const bang = don_vi.map(x => `<tr><td>${frappe.utils.escape_html(x.company)}</td><td class="text-right">${vnd(x.phai_thu)}</td>
                <td class="text-right">${vnd(x.qua_han)}</td><td class="text-right">${vnd(x.chua_phan_bo)}</td></tr>`).join("");
            const company0 = don_vi.length === 1 ? don_vi[0].company : (frappe.defaults.get_user_default("Company") || "");
            let sending = false;
            const d = new frappe.ui.Dialog({title: "Ghi nhận khách trả tiền", size: "large", fields: [
                {fieldtype: "HTML", options: `<p style="font-size:15px"><b>1. Khách:</b> ${frappe.utils.escape_html(customer)}</p>
                    <table class="table table-bordered" style="font-size:14px"><tr><th>Đơn vị</th><th class="text-right">Còn phải thu</th>
                    <th class="text-right">Trong đó quá hạn</th><th class="text-right">Tiền đã nhận chưa phân bổ</th></tr>
                    ${bang || '<tr><td colspan="4">Không có hóa đơn còn nợ trong phạm vi quyền.</td></tr>'}</table>
                    <p class="text-muted">Mỗi đơn vị một số riêng; tiền nhận vào đơn vị này không giảm nợ đơn vị khác.</p>`},
                {fieldtype: "Section Break", label: "2. Tiền thực nhận"},
                {fieldname: "company", label: "Đơn vị thực nhận tiền", fieldtype: "Link", options: "Company", reqd: 1, default: company0,
                    change: () => cap_nhat()},
                {fieldname: "tien_mat", label: "Tiền mặt", fieldtype: "Currency", change: () => cap_nhat()},
                {fieldname: "chuyen_khoan", label: "Chuyển khoản", fieldtype: "Currency", change: () => cap_nhat()},
                {fieldname: "tk_ngan_hang", label: "Tài khoản ngân hàng nhận", fieldtype: "Link", options: "Account", depends_on: "eval:doc.chuyen_khoan>0",
                    get_query: () => ({filters: {company: d.get_value("company"), account_type: "Bank", is_group: 0}})},
                {fieldname: "ma_gd", label: "Mã giao dịch / nội dung chuyển khoản", fieldtype: "Data", depends_on: "eval:doc.chuyen_khoan>0"},
                {fieldname: "nguoi_giu_tien", label: "Người thực giữ tiền mặt", fieldtype: "Link", options: "User",
                    hidden: !frappe.boot.kh_aph?.cash_custody, depends_on: "eval:doc.tien_mat>0"},
                {fieldtype: "Section Break", label: "3. Trả cho hóa đơn nào"},
                {fieldname: "hoa_don", fieldtype: "HTML"},
                {fieldtype: "Section Break", label: "4. Xem trước"},
                {fieldname: "xem_truoc", fieldtype: "HTML"},
                {fieldname: "ghi_chu", label: "Ghi chú", fieldtype: "Data"}],
                primary_action_label: "5. Xác nhận ghi phiếu thu",
                primary_action(v) {
                    if (sending) return;
                    const tong = (v.tien_mat || 0) + (v.chuyen_khoan || 0);
                    if (tong <= 0) return frappe.msgprint("Nhập số tiền khách thực trả.");
                    sending = true; d.get_primary_btn().prop("disabled", true);
                    frappe.call({method: "kh_aph.ban_quay.thu_tien", freeze: true, args: {company: v.company, customer,
                        tien_mat: v.tien_mat || 0, chuyen_khoan: v.chuyen_khoan || 0, tk_ngan_hang: v.tk_ngan_hang || "", ma_gd: v.ma_gd || "",
                        nguoi_giu_tien: v.nguoi_giu_tien || "", ghi_chu: v.ghi_chu || "", hoa_don: chon(), request_id},
                        callback: res => {
                            d.hide();
                            (res.message.phieu_thu || []).forEach(pe => window.open(
                                `/printview?doctype=Payment%20Entry&name=${encodeURIComponent(pe)}&format=${encodeURIComponent("Phiếu thu chi")}&trigger_print=1`));
                            frappe.show_alert({message: "Đã ghi " + (res.message.phieu_thu || []).join(", "), indicator: "green"});
                        }}).always(() => { sending = false; d.get_primary_btn().prop("disabled", false); });
                }});
            let thu_tu = [...chon_san];
            const chon = () => thu_tu.filter(n => (don_vi.find(x => x.company === d.get_value("company"))?.hoa_don || []).some(h => h.name === n));
            function cap_nhat() {
                const dv = don_vi.find(x => x.company === d.get_value("company"));
                const hd = dv ? dv.hoa_don : [];
                const box = d.fields_dict.hoa_don.$wrapper.empty();
                if (!hd.length) box.html("<p>Đơn vị này không có hóa đơn còn nợ: toàn bộ tiền ghi là chưa phân bổ.</p>");
                hd.forEach(h => {
                    const on = thu_tu.includes(h.name);
                    $(`<label class="d-block" style="font-size:15px"><input type="checkbox" ${on ? "checked" : ""}> ${frappe.utils.escape_html(h.name)}
                        · ngày ${frappe.utils.escape_html(h.posting_date)} · hạn ${frappe.utils.escape_html(h.due_date)} · còn ${vnd(h.outstanding)}</label>`)
                        .appendTo(box).find("input").on("change", e => {
                            thu_tu = e.target.checked ? thu_tu.concat(h.name) : thu_tu.filter(n => n !== h.name); cap_nhat(); });
                });
                let con = (d.get_value("tien_mat") || 0) + (d.get_value("chuyen_khoan") || 0), dong = [];
                for (const n of chon()) {
                    const h = hd.find(x => x.name === n), a = Math.min(con, h.outstanding);
                    dong.push(`<tr><td>${frappe.utils.escape_html(n)}</td><td class="text-right">${vnd(a)}</td></tr>`); con -= a;
                }
                d.fields_dict.xem_truoc.$wrapper.html(`<table class="table table-bordered" style="font-size:15px">
                    <tr><th>${frappe.utils.escape_html(d.get_value("company") || "Chưa chọn đơn vị")} thực nhận</th>
                    <th class="text-right">${vnd((d.get_value("tien_mat") || 0) + (d.get_value("chuyen_khoan") || 0))}</th></tr>
                    ${dong.join("")}<tr><td><b>Chưa phân bổ</b> (kế toán phân bổ sau khi xác minh)</td><td class="text-right"><b>${vnd(con)}</b></td></tr></table>
                    <p class="text-muted">Thứ tự trả theo thứ tự anh/chị tích chọn. Không tự trả hóa đơn cũ nhất.</p>`);
            }
            d.show(); cap_nhat();
        }});
    };

    if (frappe.ui.form?.on) frappe.ui.form.on("Customer", {refresh(frm) {
        if (!frappe.boot?.kh_aph?.ux_task_first || frm.is_new()) return;
        frm.add_custom_button("Ghi nhận khách trả tiền", () => kh_aph.ux.thu_tien(frm.doc.name)).addClass("btn-primary");
    }});
}
