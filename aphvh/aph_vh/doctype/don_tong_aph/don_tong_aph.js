// Đơn tổng APH (0.3.9): một đơn, nhiều đơn vị bán, dòng có / không xuất hóa đơn.
const aphvh_dt_so = (v) => (v == null ? "" : format_number(v, null, 0));

frappe.ui.form.on("Don Tong APH", {
	setup(frm) {
		frm.set_query("warehouse", "items", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return { filters: { company: row.cong_ty, is_group: 0 } };
		});
		frm.set_query("cong_ty", "items", () => ({ filters: { is_group: 0 } }));
	},
	refresh(frm) {
		aphvh_dt_ve_tinh_hinh(frm);
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button("Làm mới tình hình", () => {
				frappe.call("aphvh.aph_vh.doctype.don_tong_aph.don_tong_aph.tinh_hinh", { name: frm.doc.name }).then((r) => {
					frm.doc.__onload = Object.assign(frm.doc.__onload || {}, { tinh_hinh: r.message });
					aphvh_dt_ve_tinh_hinh(frm);
				});
			});
		}
	},
	customer(frm) {
		if (!frm.doc.customer) return;
		frappe.db.get_value("Customer", frm.doc.customer, ["tax_category", "aphvh_xuat_hoa_don"]).then((r) => {
			const c = r.message || {};
			frm.set_value("ap_thue", c.tax_category || "");
			frm.set_value("xuat_hd_mac_dinh", c.aphvh_xuat_hoa_don || "");
		});
	},
});

frappe.ui.form.on("Don Tong APH Item", {
	items_add(frm, cdt, cdn) {
		const rows = frm.doc.items || [];
		const prev = rows.length > 1 ? rows[rows.length - 2] : null;
		frappe.model.set_value(cdt, cdn, "xuat_hoa_don", (prev && prev.xuat_hoa_don) || frm.doc.xuat_hd_mac_dinh || "");
		if (prev && prev.cong_ty) frappe.model.set_value(cdt, cdn, "cong_ty", prev.cong_ty);
	},
	qty: aphvh_dt_tinh,
	rate: aphvh_dt_tinh,
	cong_ty(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "warehouse", "");
	},
});

function aphvh_dt_tinh(frm, cdt, cdn) {
	const r = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(r.qty) * flt(r.rate));
	frm.set_value("tong_tien_hang", (frm.doc.items || []).reduce((s, x) => s + flt(x.qty) * flt(x.rate), 0));
}

function aphvh_dt_ve_tinh_hinh(frm) {
	const f = frm.fields_dict.tinh_hinh_html;
	if (!f) return;
	const th = frm.doc.__onload && frm.doc.__onload.tinh_hinh;
	if (!th || !th.don_con || !th.don_con.length) {
		f.$wrapper.html(frm.doc.docstatus ? "<div class='text-muted'>Chưa có đơn bán hàng con.</div>" : "");
		return;
	}
	const e = frappe.utils.escape_html;
	const link = (dt, n) => `<a href="/app/${frappe.router.slug(dt)}/${encodeURIComponent(n)}">${e(n)}</a>`;
	const rows = th.don_con
		.map(
			(d) => `<tr>
			<td>${e(d.cong_ty)}</td><td>${e(d.xuat_hd)}</td><td>${link("Sales Order", d.don_ban)}</td>
			<td class="text-right">${aphvh_dt_so(d.tong)}</td><td class="text-right">${aphvh_dt_so(d.da_giao_pt)}%</td>
			<td>${(d.hoa_don || []).map((h) => link("Sales Invoice", h.replace(" (nháp)", "")) + (h.endsWith("(nháp)") ? " (nháp)" : "")).join("<br>")}</td>
			<td class="text-right">${aphvh_dt_so(d.da_lap_hd)}</td><td class="text-right">${aphvh_dt_so(d.da_thu)}</td>
			<td class="text-right"><b>${aphvh_dt_so(d.con_phai_thu)}</b></td></tr>`
		)
		.join("");
	const t = th.tong;
	f.$wrapper.html(`<table class="table table-bordered table-sm">
		<thead><tr><th>Đơn vị</th><th>Xuất HĐ</th><th>Đơn bán</th><th class="text-right">Tiền đơn</th><th class="text-right">Đã giao</th>
		<th>Hóa đơn</th><th class="text-right">Đã lập HĐ</th><th class="text-right">Đã thu</th><th class="text-right">Còn phải thu</th></tr></thead>
		<tbody>${rows}</tbody>
		<tfoot><tr><th colspan="3">Cộng</th><th class="text-right">${aphvh_dt_so(t.tong)}</th><th></th><th></th>
		<th class="text-right">${aphvh_dt_so(t.da_lap_hd)}</th><th class="text-right">${aphvh_dt_so(t.da_thu)}</th>
		<th class="text-right">${aphvh_dt_so(t.con_phai_thu)}</th></tr></tfoot></table>`);
}
