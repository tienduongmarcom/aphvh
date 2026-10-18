// kh_aph — ẩn giá (nhà máy) và giá vốn (bán hàng, thủ kho) ở mức màn hình (xem kh_aph/price_visibility.py).
// Đoạn khai báo dùng chung này có ở đầu mỗi tệp; tệp nào nạp trước thì khai báo, tệp sau dùng lại.
frappe.provide("kh_aph.price");
if (!kh_aph.price.toggle_grid) {
	kh_aph.price.restricted = () => !!(frappe.boot.kh_aph && frappe.boot.kh_aph.price_restricted);
	kh_aph.price.factory_groups = () =>
		(frappe.boot.kh_aph && frappe.boot.kh_aph.factory_price_groups) || [];
	kh_aph.price.toggle_fields = (frm, fields, show) => {
		for (const f of fields) {
			if (frm.fields_dict[f]) frm.toggle_display(f, show);
		}
	};
	kh_aph.price.toggle_grid = (frm, table, fields, show) => {
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
		if (names.length && grid.__kh_aph_hidden !== hidden && grid.set_column_disp_in_list_view) {
			grid.__kh_aph_hidden = hidden;
			grid.set_column_disp_in_list_view(names, show);
		}
	};
	kh_aph.price.strip_list_columns = (listview, fields) => {
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
// 0.3: khai báo riêng (ngoài khối trên) để không hỏng khi trình duyệt còn bản JS cũ đã nạp khối trên.
kh_aph.price.cost_restricted =
	kh_aph.price.cost_restricted || (() => !!(frappe.boot.kh_aph && frappe.boot.kh_aph.cost_restricted));
kh_aph.price.hn_storekeeper =
	kh_aph.price.hn_storekeeper || (() => !!(frappe.boot.kh_aph && frappe.boot.kh_aph.hn_storekeeper));

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
			if (!kh_aph.price.restricted() && !kh_aph.price.cost_restricted()) return;
			kh_aph.price.toggle_fields(frm, HEAD, false);
			kh_aph.price.toggle_grid(frm, "items", ITEM, false);
		},
	});
})();
