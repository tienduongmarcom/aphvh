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

// Đơn mua hàng: kế toán nhà máy chỉ xem để lấy hàng vào phiếu nhập, không thấy giá.
(() => {
	const HEAD = ["currency_and_price_list", "currency", "conversion_rate", "buying_price_list", "price_list_currency", "plc_conversion_rate", "ignore_pricing_rule", "sb_last_purchase", "base_total", "base_net_total", "total", "net_total", "taxes_section", "taxes_and_charges", "section_break_52", "taxes", "totals", "totals_section", "base_totals_section", "discount_section", "sec_tax_breakup", "other_charges_calculation", "item_wise_tax_details", "grand_total", "rounded_total", "base_grand_total", "base_rounded_total", "in_words", "base_in_words", "total_taxes_and_charges", "base_total_taxes_and_charges", "discount_amount", "base_discount_amount", "additional_discount_percentage", "advance_paid", "payment_schedule_section", "payment_schedule"];
	const ITEM = ["rate_and_amount", "price_list_rate", "base_price_list_rate", "margin_type", "margin_rate_or_amount", "rate_with_margin", "base_rate_with_margin", "discount_percentage", "discount_amount", "distributed_discount_amount", "rate", "amount", "base_rate", "base_amount", "stock_uom_rate", "net_rate", "net_amount", "base_net_rate", "base_net_amount", "valuation_rate", "landed_cost_voucher_amount", "amount_difference_with_purchase_invoice", "rate_difference_with_purchase_invoice", "item_tax_amount", "rm_supp_cost", "sales_incoming_rate", "billed_amt", "last_purchase_rate", "blanket_order_rate", "pricing_rules", "item_tax_template"];

	frappe.ui.form.on("Purchase Order", {
		refresh(frm) {
			if (!aphvh.price.restricted()) return;
			aphvh.price.toggle_fields(frm, HEAD, false);
			aphvh.price.toggle_grid(frm, "items", ITEM, false);
		},
	});
})();
