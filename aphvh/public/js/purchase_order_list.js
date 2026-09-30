// aphvh — ẩn giá (nhà máy) và giá vốn (bán hàng, thủ kho) ở mức màn hình (xem aphvh/price_visibility.py).
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
// 0.3: khai báo riêng (ngoài khối trên) để không hỏng khi trình duyệt còn bản JS cũ đã nạp khối trên.
aphvh.price.cost_restricted =
	aphvh.price.cost_restricted || (() => !!(frappe.boot.aphvh && frappe.boot.aphvh.cost_restricted));
aphvh.price.hn_storekeeper =
	aphvh.price.hn_storekeeper || (() => !!(frappe.boot.aphvh && frappe.boot.aphvh.hn_storekeeper));

// Danh sách: bỏ cột tổng tiền với kế toán nhà máy.
(() => {
	const doctype = "Purchase Order";
	const settings = (frappe.listview_settings[doctype] = frappe.listview_settings[doctype] || {});
	const original_onload = settings.onload;
	settings.onload = function (listview) {
		if (original_onload) original_onload.apply(this, arguments);
		if (!aphvh.price.restricted()) return;
		aphvh.price.strip_list_columns(listview, [
			"grand_total", "rounded_total", "base_grand_total", "base_rounded_total", "total", "net_total",
			"base_total", "base_net_total", "advance_paid",
		]);
	};
})();
