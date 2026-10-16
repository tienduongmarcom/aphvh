// Warehouse ownership is a preview; the server verifies every line on save.
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
