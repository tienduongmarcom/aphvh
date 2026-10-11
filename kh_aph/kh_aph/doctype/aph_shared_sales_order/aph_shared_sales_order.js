// Warehouse ownership is a preview; the server verifies every line on save.
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
