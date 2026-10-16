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
    const dialog = new frappe.ui.Dialog({title: "Lập phiếu xuất theo lượng giao đợt này", size: "extra-large",
        fields: [
            {fieldtype: "HTML", options: '<div class="alert alert-info">Chọn lượng giao bằng kg; hàng theo bao phải đủ bao theo quy cách đã lưu. Phiếu được tạo ở trạng thái <b>Chờ xuất</b>. Kho xác nhận thực giao mới trừ tồn và ghi công nợ.</div>'},
            {fieldname: "rows", label: "Hàng giao đợt này", fieldtype: "Table", cannot_add_rows: true,
                cannot_delete_rows: true, in_place_edit: true,
                data: rows.map(r => ({...r, qty: 0})), fields: [
                    {fieldname: "source_row", fieldtype: "Data", hidden: 1},
                    {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", in_list_view: 1, read_only: 1, columns: 2},
                    {fieldname: "warehouse", label: "Kho nguồn", fieldtype: "Data", in_list_view: 1, read_only: 1, columns: 3},
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
                const made = await frappe.call({method: "kh_aph.ban_nhanh.create_drafts", freeze: true,
                    args: {shared_order: frm.doc.name, selections: JSON.stringify(selections), request_id}});
                created = true;
                const names = made.message.delivery_notes.map(n => n.name);
                const print = await frappe.call({method: "kh_aph.ban_nhanh.print_batch",
                    args: {shared_order: frm.doc.name, request_id}});
                preview.document.open(); preview.document.write(print.message.html); preview.document.close();
                preview.focus(); preview.print(); dialog.hide();
                frappe.msgprint({title: "Đã lập phiếu chờ xuất", indicator: "green",
                    message: names.map(n => frappe.utils.get_form_link("Delivery Note", n, true)).join("<br>") +
                        "<br>In chưa ghi sổ. Chuyển phiếu cho kho đối chiếu và xác nhận xuất."});
            } catch (error) {
                preview.close();
                if (created) frappe.msgprint("Đã lập phiếu chờ xuất nhưng chưa mở được bản in. Bấm lại cùng lượng để mở bản in; hệ thống sẽ dùng lại phiếu đã lập.");
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
}
frappe.ui.form.on("APH Shared Sales Order", {
    async refresh(frm) {
        if (!frappe.boot?.kh_aph?.funds_workflow || frappe.boot.kh_aph.price_restricted || frm.doc.docstatus !== 1) return;
        const response = await frappe.call({method:"kh_aph.funds.shared_financials",args:{name:frm.doc.name}});
        frm.__kh_aph_financials = response.message;
        const f = response.message;
        frm.__kh_aph_funds_section?.remove();
        frm.__kh_aph_funds_section = frm.dashboard.add_section(
            `<div data-kh-funds-summary="1"><p>Còn thanh toán toàn đơn: <strong>${format_currency(f.remaining_to_pay,"VND")}</strong></p>` +
            `<p>Công nợ đã giao: <strong>${format_currency(f.dispatched_debt,"VND")}</strong></p>` +
            `<p>Giá trị chưa giao: <strong>${format_currency(f.undelivered_value,"VND")}</strong></p>` +
            `<p>Cọc giữ lại: <strong>${format_currency(f.reserved_deposit,"VND")}</strong></p></div>`,"Thanh toán và cọc");
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
			frm.add_custom_button(__("Đơn bán theo đơn vị"), () => {
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
