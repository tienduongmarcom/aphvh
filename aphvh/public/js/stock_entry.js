// aphvh — ẩn giá với kế toán nhà máy ở mức màn hình (xem aphvh/price_visibility.py).
// Đoạn khai báo dùng chung này có ở đầu mỗi tệp; tệp nào nạp trước thì khai báo, tệp sau dùng lại.
frappe.provide("aphvh.price");
if (!aphvh.price.toggle_grid) {
	aphvh.price.restricted = () => !!(frappe.boot.aphvh && frappe.boot.aphvh.price_restricted);
	aphvh.price.factory_groups = () =>
		(frappe.boot.aphvh && frappe.boot.aphvh.factory_price_groups) || [];
	aphvh.price.toggle_fields = (frm, fields, show) => {
		for (const f of fields) {
			if (frm.fields_dict[f]) frm.toggle_display(f, show);
		}
	};
	aphvh.price.toggle_grid = (frm, table, fields, show) => {
		const grid = frm.fields_dict[table] && frm.fields_dict[table].grid;
		if (!grid) return;
		const hidden = show ? 0 : 1;
		const names = fields.filter((f) => (grid.docfields || []).some((d) => d.fieldname === f));
		for (const f of names) {
			grid.docfields.find((d) => d.fieldname === f).hidden = hidden;
			for (const row of grid.grid_rows || []) {
				const df = row && (row.docfields || []).find((d) => d.fieldname === f);
				if (df) df.hidden = hidden;
			}
		}
		if (names.length && grid.__aphvh_hidden !== hidden && grid.set_column_disp_in_list_view) {
			grid.__aphvh_hidden = hidden;
			grid.set_column_disp_in_list_view(names, show);
		}
	};
	aphvh.price.strip_list_columns = (listview, fields) => {
		const drop = new Set(fields);
		const original = listview.setup_columns.bind(listview);
		listview.setup_columns = function () {
			original();
			this.columns = this.columns.filter((c) => !(c.type === "Field" && c.df && drop.has(c.df.fieldname)));
		};
		listview.setup_columns();
		listview.render_header(true);
		listview.refresh();
	};
}

// Phiếu kho (cấp liệu, sản xuất, chuyển kho, thiếu/thừa): kế toán nhà máy không thấy đơn giá,
// giá trị. Giá do hệ thống tính (bình quân, chia theo kg), không cần nhập tay.
(() => {
	const HEAD = [
		"get_stock_and_rate", "section_break_19", "total_outgoing_value", "total_incoming_value",
		"value_difference", "additional_costs_section", "additional_costs", "total_additional_costs",
		"total_amount",
	];
	const ITEM = [
		"rates_section", "basic_rate", "customer_provided_item_cost", "additional_cost",
		"landed_cost_voucher_amount", "valuation_rate", "set_basic_rate_manually", "basic_amount", "amount",
	];

	frappe.ui.form.on("Stock Entry", {
		refresh(frm) {
			if (!aphvh.price.restricted()) return;
			aphvh.price.toggle_fields(frm, HEAD, false);
			aphvh.price.toggle_grid(frm, "items", ITEM, false);
		},
	});
})();
