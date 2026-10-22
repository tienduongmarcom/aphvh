// Kho nguồn trên giao diện chỉ để xem trước; server kiểm lại khi lưu.
frappe.ui.form.on("APH Shared Sales Order", {
    refresh(frm) {
        if (!frappe.boot?.kh_aph?.trung_tam_ban || frappe.boot.kh_aph.price_restricted ||
            frm.doc.docstatus !== 1 || !frappe.model.can_create("Delivery Note")) return;
        frm.add_custom_button("Lập phiếu xuất & In", () => kh_aph_lap_dot_xuat(frm));
    },
});

async function kh_aph_lap_dot_xuat(frm) {
    if (frm.is_dirty()) return frappe.msgprint("Lưu thay đổi trên đơn trước khi lập phiếu xuất.");
    const response = await frappe.call({method: "kh_aph.ban_nhanh.preview", args: {shared_order: frm.doc.name}, freeze: true});
    const rows = response.message.rows.filter(r => r.remaining_qty > 0);
    if (!rows.length) return frappe.msgprint("Đã giao hoặc đã lập phiếu chờ xuất hết đơn. Kiểm tra các phiếu chờ xuất trước khi lập thêm.");
    // Giữ mã yêu cầu khi lỗi mạng để lần bấm lại không lập thêm phiếu.
    const request_id = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
    let dialog;
    dialog = new frappe.ui.Dialog({title: "Lập phiếu xuất theo lượng giao đợt này", size: "extra-large",
        fields: [
            {fieldtype: "HTML", options: '<div class="alert alert-info">Chọn lượng giao bằng kg; hàng theo bao phải đủ bao theo quy cách đã lưu. Phiếu được tạo ở trạng thái <b>Chờ xuất</b>. Kho xác nhận thực giao mới trừ tồn và ghi công nợ.</div>'},
            {fieldname: "delivery_method", label: "Cách giao đợt này", fieldtype: "Select",
                options: ["Khách đến lấy", "Xe khách đến lấy", "Vận chuyển"], default: "Khách đến lấy", reqd: 1},
            {fieldname: "recipient", label: "Người thực nhận hàng tại kho", fieldtype: "Data", reqd: 1,
                description: "Người nhận/lái xe ký nhận tại kho, không bắt buộc có tài khoản phần mềm."},
            {fieldname: "phone", label: "Điện thoại liên hệ", fieldtype: "Data"},
            {fieldname: "authorization", label: "Khách chỉ định người nhận", fieldtype: "Data",
                depends_on: "eval:doc.delivery_method==='Xe khách đến lấy'", mandatory_depends_on: "eval:doc.delivery_method==='Xe khách đến lấy'",
                description: "Ví dụ: khách gọi xác nhận hoặc tin nhắn chỉ định lái xe. Quyền nhận hàng không phải quyền ký công nợ."},
            {fieldname: "carrier", label: "Nhà xe (chọn hoặc nhập mới)", fieldtype: "Autocomplete", ignore_validation: true, translate_values: false,
                depends_on: "eval:doc.delivery_method==='Vận chuyển'", mandatory_depends_on: "eval:doc.delivery_method==='Vận chuyển'",
                onchange() {if (!dialog) return; const match = (dialog.__carriers || []).find(r => r.carrier === dialog.get_value("carrier"));
                    dialog.set_value("carrier_phone", match ? match.carrier_phone : "");}},
            {fieldname: "carrier_phone", label: "Điện thoại nhà xe", fieldtype: "Data",
                depends_on: "eval:doc.delivery_method==='Vận chuyển'", mandatory_depends_on: "eval:doc.delivery_method==='Vận chuyển'"},
            {fieldname: "customer_signature", label: "Khách cần ký biên bản giao nhận", fieldtype: "Select", options: ["Không", "Có"], default: "Không",
                depends_on: "eval:doc.delivery_method==='Vận chuyển'"},
            {fieldname: "dispatch_now", label: "Xuất ngay — đã kiểm thực giao tại kho", fieldtype: "Check", default: 0,
                hidden: !response.message.can_dispatch,
                description: "Chỉ chọn khi hàng đã thực giao. Hệ thống sẽ trừ tồn và ghi công nợ theo cách giao đã chọn.",
                onchange() {if (dialog) dialog.get_primary_btn().text(dialog.get_value("dispatch_now") ? "Xuất ngay & Mở bản in" : "Lập phiếu & Mở bản in");}},
            {fieldname: "dispatcher", label: "Người thực giao hàng tại kho", fieldtype: "Data",
                depends_on: "eval:doc.dispatch_now", mandatory_depends_on: "eval:doc.dispatch_now"},
            {fieldtype: "Column Break"},
            {fieldname: "driver_name", label: "Tên lái xe (nếu khác người nhận)", fieldtype: "Data"},
            {fieldname: "vehicle_no", label: "Biển số xe", fieldtype: "Data"},
            {fieldname: "shipping_address_name", label: "Địa chỉ giao thay thế", fieldtype: "Link", options: "Address",
                description: "Để trống để giữ địa chỉ từ từng đơn nguồn, nếu đã có.",
                get_query: () => ({query: "frappe.contacts.doctype.address.address.address_query",
                    filters: {link_doctype: "Customer", link_name: response.message.customer, disabled: 0}})},
            {fieldtype: "Section Break"},
            {fieldname: "rows", label: "Hàng giao đợt này", fieldtype: "Table", cannot_add_rows: true,
                cannot_delete_rows: true, in_place_edit: true,
                data: rows.map(r => ({...r, qty: 0})), fields: [
                    {fieldname: "source_row", fieldtype: "Data", hidden: 1},
                    {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", in_list_view: 1, read_only: 1, columns: 1},
                    {fieldname: "item_name", label: "Tên hàng", fieldtype: "Data", in_list_view: 1, read_only: 1, columns: 2},
                    {fieldname: "warehouse", label: "Kho nguồn", fieldtype: "Data", in_list_view: 1, read_only: 1, columns: 2},
                    {fieldname: "remaining_qty", label: "Còn lập (kg)", fieldtype: "Float", in_list_view: 1, read_only: 1, columns: 2},
                    {fieldname: "kg_per_bag", label: "Kg/bao", fieldtype: "Float", in_list_view: 1, read_only: 1, columns: 1},
                    {fieldname: "qty", label: "Giao đợt này (kg)", fieldtype: "Float", in_list_view: 1, columns: 2},
                    {fieldname: "ordered_qty", label: "Đặt (kg)", fieldtype: "Float", read_only: 1},
                    {fieldname: "delivered_qty", label: "Đã giao (kg)", fieldtype: "Float", read_only: 1},
                    {fieldname: "draft_qty", label: "Đã lập chờ xuất (kg)", fieldtype: "Float", read_only: 1},
                ]},
        ],
        primary_action_label: "Lập phiếu & Mở bản in",
        async primary_action(values) {
            const selections = (values.rows || []).filter(r => Number(r.qty) > 0)
                .map(r => ({source_row: r.source_row, qty: Number(r.qty)}));
            if (!selections.length) return frappe.msgprint("Nhập lượng giao cho ít nhất một dòng.");
            const preview = window.open("", "_blank");
            if (!preview) return frappe.msgprint("Cho phép mở cửa sổ in trong trình duyệt rồi bấm lại.");
            preview.opener = null;
            dialog.disable_primary_action();
            let created = false;
            try {
                const dispatch = !!values.dispatch_now;
                const made = await frappe.call({method: dispatch ? "kh_aph.ban_nhanh.create_and_dispatch" : "kh_aph.ban_nhanh.create_drafts", freeze: true,
                    args: {shared_order: frm.doc.name, selections: JSON.stringify(selections), request_id,
                        ...(dispatch ? {dispatcher: values.dispatcher} : {}),
                        delivery: JSON.stringify(Object.fromEntries(["delivery_method", "recipient", "phone", "driver_name", "vehicle_no", "shipping_address_name", "authorization", "carrier", "carrier_phone", "customer_signature"]
                            .map(key => [key, values[key] || ""])))}});
                created = true;
                const names = made.message.delivery_notes.map(n => n.name);
                const print = await frappe.call({method: "kh_aph.ban_nhanh.print_batch",
                    args: {shared_order: frm.doc.name, request_id}});
                preview.document.open(); preview.document.write(print.message.html); preview.document.close();
                preview.focus(); preview.print(); dialog.hide();
                if (dispatch) await frm.reload_doc();
                frappe.msgprint({title: dispatch ? "Đã xác nhận xuất hàng" : "Đã lập phiếu chờ xuất", indicator: "green",
                    message: names.map(n => frappe.utils.get_form_link("Delivery Note", n, true)).join("<br>") +
                        (dispatch ? "<br>Kho và công nợ đã ghi nhận. Mở lại bản in không xuất hàng lần nữa." :
                            "<br>In chưa ghi sổ. Chuyển phiếu cho kho đối chiếu và xác nhận xuất.")});
            } catch (error) {
                preview.close();
                if (created) frappe.msgprint(values.dispatch_now ?
                    "Đã xác nhận xuất nhưng chưa mở được bản in. Giữ nguyên nội dung và bấm lại trong cửa sổ này để dùng lại phiếu, không xuất lần nữa." :
                    "Đã lập phiếu chờ xuất nhưng chưa mở được bản in. Bấm lại cùng lượng để mở bản in; hệ thống sẽ dùng lại phiếu đã lập.");
                else if (values.dispatch_now) frappe.msgprint("Chưa nhận được kết quả xuất thành công. Khi thử lại, giữ nguyên nội dung trong cửa sổ này để hệ thống kiểm mã yêu cầu, tránh xuất trùng.");
                throw error;
            } finally { dialog.enable_primary_action(); }
        },
        secondary_action_label: "Điền toàn bộ phần còn lại",
        secondary_action() {
            dialog.fields_dict.rows.df.data.forEach(r => { r.qty = r.remaining_qty; });
            dialog.fields_dict.rows.grid.refresh();
        },
    });
    dialog.show();
    frappe.call({method: "kh_aph.delivery_info.recent_carriers"}).then(r => {
        dialog.__carriers = r.message || [];
        dialog.fields_dict.carrier.set_data(dialog.__carriers.map(x => ({value: x.carrier, label: frappe.utils.escape_html(x.carrier)})));
    });
}
frappe.ui.form.on("APH Shared Sales Order", {
    async refresh(frm) {
        if (!frappe.boot?.kh_aph?.funds_workflow || frappe.boot.kh_aph.price_restricted || frm.doc.docstatus !== 1) return;
        const name = frm.doc.name, customer = frm.doc.customer;
        const response = await frappe.call({method:"kh_aph.funds.shared_financials",args:{name}});
        if (frm.doc.name !== name || frm.doc.customer !== customer) return;
        frm.__kh_aph_financials = response.message;
        const f = response.message;
        const detail = `<div data-kh-funds-summary="1">` +
            (Number(f.reserved_deposit) > 0 ? `<p>Cọc giữ cho đơn: <strong>${format_currency(f.reserved_deposit,"VND")}</strong></p>` : "") +
            `<details><summary>Tiền của đơn — xem chi tiết</summary>` +
            `<p>Còn thanh toán toàn đơn: <strong>${format_currency(f.remaining_to_pay,"VND")}</strong></p>` +
            `<p>Công nợ đã giao: <strong>${format_currency(f.dispatched_debt,"VND")}</strong></p>` +
            `<p>Giá trị chưa giao: <strong>${format_currency(f.undelivered_value,"VND")}</strong></p>` +
            `<p>Cọc giữ lại: <strong>${format_currency(f.reserved_deposit,"VND")}</strong></p></details></div>`;
        if (frm.__kh_aph_funds_section?.[0]?.isConnected) frm.__kh_aph_funds_section.html(detail);
        else frm.__kh_aph_funds_section = frm.dashboard.add_section(detail);
        frm.dashboard.show();
    }
});
frappe.ui.form.on("APH Shared Sales Order", {
	setup(frm) {
		frm.set_query("warehouse", "items", () => ({filters: {is_group: 0, disabled: 0}}));
		frm.set_query("item_code", "items", () => ({filters: {disabled: 0, stock_uom: "Kg"}}));
		frm.set_query("selling_price_list", () => ({filters: {selling: 1, enabled: 1}}));
	},
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Đơn bán theo công ty"), () => {
				frappe.set_route("List", "Sales Order", {kh_aph_shared_order: frm.doc.name});
			});
		}
	},
});

frappe.ui.form.on("APH Shared Sales Order Item", {
	async warehouse(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const selected = row.warehouse;
		if (!selected) return frappe.model.set_value(cdt, cdn, "company", null);
		const response = await frappe.db.get_value("Warehouse", selected, "company");
		// Ignore an old response when the user changes warehouse quickly.
		if (locals[cdt]?.[cdn]?.warehouse === selected) {
			await frappe.model.set_value(cdt, cdn, "company", response.message?.company || null);
		}
	},
});

frappe.ui.form.on("APH Shared Sales Order", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.docstatus !== 1) return;
        frm.add_custom_button("Phiếu giao tổng hợp", async () => {
            const response = await frappe.call({method: "kh_aph.delivery_slip.deliveries",
                args: {shared_order: frm.doc.name}});
            const notes = response.message || [];
            if (!notes.length) {
                frappe.msgprint("Chưa có phiếu đã xuất mà bạn được quyền in.");
                return;
            }
            const dialog = new frappe.ui.Dialog({title: "Chọn các phiếu giao cùng đợt",
                fields: [{fieldname: "notes", label: "Phiếu giao", fieldtype: "MultiCheck",
                    options: notes.map((n, i) => ({label: frappe.utils.escape_html(`${n.name} · ${n.company} · ${n.state}`), value: String(i)}))}],
                primary_action_label: "In tổng hợp",
                async primary_action(values) {
                    if (!values.notes?.length) return frappe.msgprint("Chọn ít nhất một phiếu giao.");
                    const preview = window.open("", "_blank");
                    if (!preview) return frappe.msgprint("Cho phép mở cửa sổ in trong trình duyệt.");
                    preview.opener = null;
                    try {
                        const result = await frappe.call({method: "kh_aph.delivery_slip.consolidated",
                            args: {shared_order: frm.doc.name, delivery_notes: JSON.stringify(values.notes.map(i => notes[Number(i)].name))}, freeze: true});
                        preview.document.open();
                        preview.document.write(result.message.html);
                        preview.document.close();
                        preview.focus();
                        preview.print();
                        dialog.hide();
                    } catch (error) {
                        preview.close();
                        throw error;
                    }
                },
            });
            dialog.show();
        }, "In");
    },
});

frappe.ui.form.on("APH Shared Sales Order",{
    refresh(frm){
        if(frm.doc.docstatus===1 && frappe.boot?.kh_aph?.source_change && frappe.model.can_create("APH Source Change"))
            frm.add_custom_button("Đổi nguồn phần chưa giao",()=>frappe.new_doc("APH Source Change",{shared_order:frm.doc.name}));
    }
});
