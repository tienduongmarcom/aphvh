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

// Phiếu giao hàng: nút in Phiếu xuất kho và Biên bản giao nhận (2 liên); ẩn giá vốn với nhân viên
// bán hàng, thủ kho; thủ kho không sửa giá (giá lấy từ đơn bán hàng).
(() => {
	const COST = ["incoming_rate"];  // cả bảng hàng đóng gói (packed_items) của hàng bộ
	const ROW_PRICE = [
		"price_list_rate", "rate", "discount_percentage", "discount_amount", "margin_type",
		"margin_rate_or_amount", "item_tax_template",
	];
	const HEAD_PRICE = [
		"selling_price_list", "ignore_pricing_rule", "taxes_and_charges", "tax_category", "apply_discount_on",
		"additional_discount_percentage", "discount_amount", "coupon_code",
	];
	const FORMAT_ISSUE = "Phiếu xuất kho bán hàng APH";
	const FORMAT_HANDOVER = "Biên bản giao nhận APH";

	const print = (frm, format) => {
		if (frm.is_dirty()) {
			frappe.msgprint("Lưu phiếu trước khi in.");
			return;
		}
		const params = new URLSearchParams({
			doctype: frm.doctype,
			name: frm.doc.name,
			format,
			no_letterhead: 1,
			letterhead: "No Letterhead",
			settings: "{}",
			_lang: "vi",
			trigger_print: 1,
		});
		window.open(frappe.urllib.get_full_url("/printview?" + params.toString()));
	};

	const lock_prices = (frm) => {
		for (const f of HEAD_PRICE) {
			if (frm.fields_dict[f]) frm.set_df_property(f, "read_only", 1);
		}
		if (frm.fields_dict.taxes) frm.set_df_property("taxes", "read_only", 1);
		const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
		if (!grid) return;
		for (const f of ROW_PRICE) {
			if ((grid.docfields || []).some((d) => d.fieldname === f)) {
				grid.update_docfield_property(f, "read_only", 1);
			}
		}
	};

	frappe.ui.form.on("Delivery Note", {
		refresh(frm) {
			if (!frm.is_new() && frm.doc.docstatus < 2) {
				const tra = !!frm.doc.is_return;
				frm.add_custom_button(tra ? "Phiếu nhập kho hàng trả lại" : "Phiếu xuất kho",
					() => print(frm, FORMAT_ISSUE), "In");
				frm.add_custom_button(tra ? "Biên bản nhận lại hàng (2 liên)" : "Biên bản giao nhận (2 liên)",
					() => print(frm, FORMAT_HANDOVER), "In");
			}
			if (aphvh.price.cost_restricted()) {
				aphvh.price.toggle_grid(frm, "items", COST, false);
				aphvh.price.toggle_grid(frm, "packed_items", COST, false);
			}
			if (aphvh.price.hn_storekeeper()) lock_prices(frm);
		},
	});
})();
