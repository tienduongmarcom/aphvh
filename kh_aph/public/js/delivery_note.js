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
		"additional_discount_percentage", "discount_amount", "coupon_code", "kh_aph_xuat_hoa_don",
	];
	const FORMAT_ISSUE = "Phiếu xuất kho bán hàng";
	const FORMAT_HANDOVER = "Biên bản giao nhận";

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

	const print_a5 = async (frm) => {
		if (frm.is_dirty()) return frappe.msgprint("Lưu phiếu trước khi in.");
		const preview = window.open("", "_blank");
		if (!preview) return frappe.msgprint("Cho phép mở cửa sổ in trong trình duyệt rồi bấm lại.");
		preview.opener = null;
		try {
			const result = await frappe.call({method: "kh_aph.ban_nhanh.print_note",
				args: {delivery_note: frm.doc.name}, freeze: true});
			preview.document.open(); preview.document.write(result.message.html); preview.document.close();
			preview.focus(); preview.print();
		} catch (error) {
			preview.close();
			throw error;
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
				if (!tra && frappe.boot?.kh_aph?.trung_tam_ban && !kh_aph.price.restricted() &&
					frm.perm?.some(p => p.print)) {
					frm.add_custom_button("Phiếu xuất kho A5 (2 liên)", () => print_a5(frm), "In");
				}
			}
			if (kh_aph.price.cost_restricted()) {
				kh_aph.price.toggle_grid(frm, "items", COST, false);
				kh_aph.price.toggle_grid(frm, "packed_items", COST, false);
			}
			if (kh_aph.price.hn_storekeeper()) lock_prices(frm);
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
kh_aph.inv.setup("Delivery Note");

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
frappe.ui.form.on("Delivery Note", kh_aph.vat.handlers);

// Atomic handoff/pickup and manual receipt confirmation.
frappe.ui.form.on("Delivery Note", {
    refresh(frm) {
        if (!frm.meta.fields.some(f => f.fieldname === "kh_aph_delivery_state")
            || frm.is_new() || frm.doc.is_return || frm.doc.docstatus === 2) return;
        if (frappe.boot?.kh_aph?.trung_tam_ban && frm.meta.fields.some(f => f.fieldname === "kh_aph_nguoi_thuc_giao"))
            frm.set_df_property("kh_aph_nguoi_thuc_giao", "read_only", frm.doc.docstatus !== 0 || !frm.perm.some(p => p.submit));
        const confirm = async (action) => {
            if (frm.is_dirty()) {
                frappe.msgprint("Lưu phiếu trước khi xác nhận giao/nhận hàng.");
                return;
            }
            await frappe.call({method: "kh_aph.delivery_status.confirm",
                args: {name: frm.doc.name, action}, freeze: true,
                freeze_message: "Đang xác nhận giao/nhận hàng…"});
            await frm.reload_doc();
        };
        if (frm.doc.docstatus === 0 && frm.perm.some(p => p.submit)) {
            if (!frm.doc.kh_aph_cach_giao || frm.doc.kh_aph_cach_giao === "Vận chuyển")
                frm.add_custom_button("Bàn giao cho người vận chuyển", () => confirm("handoff"), "Giao hàng");
            if (!frm.doc.kh_aph_cach_giao || ["Khách đến lấy", "Xe khách đến lấy"].includes(frm.doc.kh_aph_cach_giao))
                frm.add_custom_button("Khách đến lấy", () => confirm("pickup"), "Giao hàng");
        } else if (frm.doc.docstatus === 1 && frm.doc.kh_aph_delivery_state === "Đang giao"
            && (frm.perm.some(p => p.write) || (frappe.user_roles || []).some(r =>
                ["Nhân viên bán hàng", "Thủ kho bán hàng"].includes(r)))) {
            frm.add_custom_button("Khách đã nhận", () => {
                if (!frm.doc.kh_aph_mau_giao_nhan) return confirm("receive");
                if (frm.is_dirty()) return frappe.msgprint("Lưu phiếu trước khi xác nhận nhận hàng.");
                frappe.prompt([
                    {fieldname: "reported_by", label: "Ai báo đã nhận?", fieldtype: "Select", options: ["Khách báo", "Nhà xe báo"], reqd: 1},
                    {fieldname: "received_on", label: "Ngày khách nhận", fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1},
                ], async values => {
                    await frappe.call({method: "kh_aph.delivery_status.confirm", args: {name: frm.doc.name, action: "receive", ...values}, freeze: true});
                    await frm.reload_doc();
                }, "Khách đã nhận hàng", "Xác nhận");
            }, "Giao hàng");
        }
    },
});
