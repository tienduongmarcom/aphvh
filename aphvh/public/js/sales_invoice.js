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

// 0.3.1: Xuất hóa đơn GTGT (Có/Không). Máy chủ quyết định thuế khi lưu (aphvh/invoice_flag.py);
// trên màn hình chỉ xem trước: chọn Không thì bỏ ngay dòng thuế, chọn Có thì thuế tính lại khi lưu.
// Đổi khách thì lấy mặc định của khách (nếu khách đã đặt).
frappe.provide("aphvh.inv");
if (!aphvh.inv.setup) {
	aphvh.inv.FIELD = "aphvh_xuat_hoa_don";
	aphvh.inv.NO = "Không";
	aphvh.inv.strip = (frm) => {
		if (frm.doc[aphvh.inv.FIELD] !== aphvh.inv.NO || frm.doc.docstatus !== 0) return;
		const had = (frm.doc.taxes || []).length || frm.doc.taxes_and_charges
			|| (frm.doc.items || []).some((r) => r.item_tax_template);
		if (!had) return;
		frm.doc.taxes_and_charges = null;
		frm.clear_table("taxes");
		for (const r of frm.doc.items || []) {
			r.item_tax_template = null;
			r.item_tax_rate = "{}";
		}
		frm.refresh_fields(["taxes_and_charges", "taxes", "items"]);
		if (frm.cscript.calculate_taxes_and_totals) frm.cscript.calculate_taxes_and_totals();
	};
	aphvh.inv.setup = (doctype) => {
		frappe.ui.form.on(doctype, {
			aphvh_xuat_hoa_don(frm) {
				if (frm.doc[aphvh.inv.FIELD] === aphvh.inv.NO) {
					aphvh.inv.strip(frm);
				} else if (frm.doc[aphvh.inv.FIELD] && !(frm.doc.taxes || []).length) {
					frappe.show_alert({message: "Thuế GTGT sẽ được tính lại khi lưu.", indicator: "blue"});
				}
			},
			taxes_and_charges(frm) {
				setTimeout(() => aphvh.inv.strip(frm), 300);
			},
			customer(frm) {
				if (!frm.doc.customer || frm.doc.docstatus !== 0) return;
				frappe.db.get_value("Customer", frm.doc.customer, aphvh.inv.FIELD).then((r) => {
					const v = r && r.message && r.message[aphvh.inv.FIELD];
					if (v && v !== frm.doc[aphvh.inv.FIELD]) frm.set_value(aphvh.inv.FIELD, v);
				});
			},
			validate(frm) {
				aphvh.inv.strip(frm);
			},
		});
	};
}
aphvh.inv.setup("Sales Invoice");

// 0.3.5 — "Áp thuế theo" (Công ty/HTX hay Hộ KD/cá nhân) nối với Loại thuế chuẩn của ERPNext:
// đổi ô này thì ERPNext tính lại mẫu thuế từng dòng ngay trên màn hình; đổi khách thì ô tự theo loại của khách.
frappe.provide("aphvh.vat");
if (!aphvh.vat.handlers) {
	aphvh.vat.handlers = {
		aphvh_ap_thue(frm) {
			const v = frm.doc.aphvh_ap_thue || "";
			if ((frm.doc.tax_category || "") !== v) frm.set_value("tax_category", v);
		},
		tax_category(frm) {
			const v = frm.doc.tax_category || "";
			if (v && frm.doc.aphvh_ap_thue !== v) frm.set_value("aphvh_ap_thue", v);
		},
	};
}
frappe.ui.form.on("Sales Invoice", aphvh.vat.handlers);
