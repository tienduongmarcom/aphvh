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

// Đơn bán hàng: nhân viên bán hàng, thủ kho Hà Nội thấy giá bán nhưng không thấy giá tồn kho và
// lãi gộp trên dòng. Cảnh báo công nợ/giá do máy chủ hiện khi lưu, xác nhận (sales_warnings.py).
(() => {
	const COST = ["valuation_rate", "gross_profit"];

	frappe.ui.form.on("Sales Order", {
		refresh(frm) {
			if (kh_aph.price.cost_restricted()) kh_aph.price.toggle_grid(frm, "items", COST, false);
		},
	});
})();

// 0.3.1: Xuất hóa đơn GTGT (Có/Không). Máy chủ quyết định thuế khi lưu (kh_aph/invoice_flag.py);
// trên màn hình chỉ xem trước: chọn Không thì bỏ ngay dòng thuế, chọn Có thì thuế tính lại khi lưu.
// Đổi khách thì lấy mặc định của khách (nếu khách đã đặt).
frappe.provide("kh_aph.inv");
if (!kh_aph.inv.setup) {
	kh_aph.inv.FIELD = "kh_aph_xuat_hoa_don";
	kh_aph.inv.NO = "Không";
	kh_aph.inv.strip = (frm) => {
		if (frm.doc[kh_aph.inv.FIELD] !== kh_aph.inv.NO || frm.doc.docstatus !== 0) return;
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
	kh_aph.inv.setup = (doctype) => {
		frappe.ui.form.on(doctype, {
			kh_aph_xuat_hoa_don(frm) {
				if (frm.doc[kh_aph.inv.FIELD] === kh_aph.inv.NO) {
					kh_aph.inv.strip(frm);
				} else if (frm.doc[kh_aph.inv.FIELD] && !(frm.doc.taxes || []).length) {
					frappe.show_alert({message: "Thuế GTGT sẽ được tính lại khi lưu.", indicator: "blue"});
				}
			},
			taxes_and_charges(frm) {
				setTimeout(() => kh_aph.inv.strip(frm), 300);
			},
			customer(frm) {
				if (!frm.doc.customer || frm.doc.docstatus !== 0) return;
				frappe.db.get_value("Customer", frm.doc.customer, kh_aph.inv.FIELD).then((r) => {
					const v = r && r.message && r.message[kh_aph.inv.FIELD];
					if (v && v !== frm.doc[kh_aph.inv.FIELD]) frm.set_value(kh_aph.inv.FIELD, v);
				});
			},
			validate(frm) {
				kh_aph.inv.strip(frm);
			},
		});
	};
}
kh_aph.inv.setup("Sales Order");

// 0.3.5 — "Áp thuế theo" (Công ty/HTX hay Hộ KD/cá nhân) nối với Loại thuế chuẩn của ERPNext:
// đổi ô này thì ERPNext tính lại mẫu thuế từng dòng ngay trên màn hình; đổi khách thì ô tự theo loại của khách.
frappe.provide("kh_aph.vat");
if (!kh_aph.vat.handlers) {
	kh_aph.vat.handlers = {
		kh_aph_ap_thue(frm) {
			const v = frm.doc.kh_aph_ap_thue || "";
			if ((frm.doc.tax_category || "") !== v) frm.set_value("tax_category", v);
		},
		tax_category(frm) {
			const v = frm.doc.tax_category || "";
			if (v && frm.doc.kh_aph_ap_thue !== v) frm.set_value("kh_aph_ap_thue", v);
		},
	};
}
frappe.ui.form.on("Sales Order", kh_aph.vat.handlers);
