// kh_aph 0.11.2 — thao tác ngắn trên Warehouse bằng Dialog (docs/kien-truc-giao-dien.md).
// Quyết toán dở dang về 0 (cờ factory_costing): kho loại "Dở dang dây chuyền" (hoặc ô Kho bồn của 0.11.1).
// Kiểm kê có mốc (cờ kho_chuan): thiếu → phiếu xuất nháp Nợ 1381; thừa → nhập nháp kho Chờ xử lý, Có 3381.
frappe.provide("kh_aph.b0112");
kh_aph.b0112.on = (co) => !!(frappe.boot.kh_aph && frappe.boot.kh_aph[co]);
kh_aph.b0112.lien_ket = (ds) => (ds || []).map((p) => `<a href="/app/stock-entry/${encodeURIComponent(p)}">${frappe.utils.escape_html(p)}</a>`).join(", ");

kh_aph.b0112.quyet_toan = (frm) => {
	const goi = (v) => frappe.call({method: "kh_aph.factory_costing.quyet_toan_do_dang", args: {kho: frm.doc.name, ...v}, freeze: true})
		.then((r) => {
			const m = r.message || {};
			if (m.can_chon) {
				frappe.prompt([{fieldname: "loai_hao_hut", label: __("Phần còn trên sổ là"), fieldtype: "Select", reqd: 1,
					options: "Hao hụt tự nhiên\nHao hụt bất thường", description: m.thong_bao}],
				(c) => goi({...v, ...c}), __("Chưa có định mức"));
				return;
			}
			const ds = Array.isArray(m.phieu) ? m.phieu : (m.phieu ? [m.phieu] : []);
			if (!ds.length) {
				frappe.msgprint(__("Kho dở dang không còn tồn trên sổ."));
				return;
			}
			let html = `<p>${__("Phiếu xuất nháp")}: ${kh_aph.b0112.lien_ket(ds)}</p>`;
			if (m.chi_tiet && m.chi_tiet.length) {
				html += `<table class="table table-bordered table-sm"><tr><th>${__("Nguyên liệu")}</th><th>${__("Còn trên sổ")}</th>`
					+ `<th>${__("Đã ghi tiêu hao")}</th><th>${__("Định mức")}</th><th>${__("Tự nhiên (15488)")}</th><th>${__("Vượt (6322)")}</th></tr>`
					+ m.chi_tiet.map((c) => `<tr><td>${frappe.utils.escape_html(c.item_code)}</td><td>${format_number(c.con_lai)}</td>`
						+ `<td>${format_number(c.da_dung)}</td><td>${format_number(c.dinh_muc)}</td><td>${format_number(c.tu_nhien)}</td>`
						+ `<td>${format_number(c.bat_thuong)}</td></tr>`).join("") + "</table>";
			}
			if (m.bat_thuong && m.bat_thuong.length) {
				html += `<p>${__("Cần kế toán xem")}: ${frappe.utils.escape_html(m.bat_thuong.map((b) => b.join(" / ")).join("; "))}</p>`;
			}
			frappe.msgprint({title: __("Quyết toán dở dang"), message: html, indicator: "blue"});
		});
	frappe.prompt([
		{fieldname: "xuong", label: __("Xưởng (trung tâm chi phí)"), fieldtype: "Link", options: "Cost Center", reqd: 1,
			get_query: () => ({filters: {company: frm.doc.company, kh_aph_loai_ttcp: "Xưởng sản xuất", is_group: 0}})},
		{fieldname: "ly_do", label: __("Lý do (dừng chuyền ngày…, ca…)"), fieldtype: "Small Text", reqd: 1},
		{fieldname: "ngay", label: __("Ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
		{fieldname: "gio", label: __("Giờ"), fieldtype: "Time", default: frappe.datetime.now_time()},
	], goi, __("Quyết toán dở dang về 0 (R076)"));
};

kh_aph.b0112.kiem_ke = (frm) => {
	const d = new frappe.ui.Dialog({
		title: __("Kiểm kê có mốc thời gian (R054–R056)"),
		size: "large",
		fields: [
			{fieldname: "ngay", label: __("Ngày kiểm"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1},
			{fieldname: "gio", label: __("Giờ chốt số"), fieldtype: "Time", default: frappe.datetime.now_time(), reqd: 1},
			{fieldname: "lay", label: __("Lấy số sổ tại mốc"), fieldtype: "Button"},
			{fieldname: "dong", label: __("Kết quả đếm"), fieldtype: "Table", cannot_add_rows: false, in_place_edit: true, data: [],
				fields: [
					{fieldname: "item_code", label: __("Mã hàng"), fieldtype: "Link", options: "Item", in_list_view: 1, reqd: 1},
					{fieldname: "sl_so", label: __("Số sổ"), fieldtype: "Float", in_list_view: 1, read_only: 1},
					{fieldname: "sl_thuc_te", label: __("Thực tế"), fieldtype: "Float", in_list_view: 1, reqd: 1},
				]},
			{fieldname: "ly_do", label: __("Lý do chênh lệch (bắt buộc khi vượt ngưỡng)"), fieldtype: "Small Text"},
		],
		primary_action_label: __("Lập phiếu nháp"),
		primary_action(v) {
			frappe.call({method: "kh_aph.kho_chuan.ghi_kiem_ke", freeze: true,
				args: {kho: frm.doc.name, ngay: v.ngay, gio: v.gio, ly_do: v.ly_do,
					dong: JSON.stringify((v.dong || []).map((r) => ({item_code: r.item_code, sl_thuc_te: r.sl_thuc_te})))}})
				.then((r) => {
					d.hide();
					const m = r.message || {};
					frappe.msgprint(m.khop ? __("Thực tế khớp sổ, không cần phiếu.")
						: __("Phiếu nháp") + ": " + kh_aph.b0112.lien_ket(m.phieu)
						+ "<br>" + __("Bước xử lý chênh lệch tiếp theo chờ kế toán trưởng chốt."));
				});
		},
	});
	d.fields_dict.lay.$input.on("click", () => {
		const v = d.get_values(true);
		frappe.call({method: "kh_aph.kho_chuan.so_sach", args: {kho: frm.doc.name, ngay: v.ngay, gio: v.gio}}).then((r) => {
			d.fields_dict.dong.df.data = (r.message || []).map((x) => ({item_code: x.item_code, sl_so: x.sl_so, sl_thuc_te: x.sl_so}));
			d.fields_dict.dong.grid.refresh();
		});
	});
	d.show();
};

frappe.ui.form.on("Warehouse", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.is_group) return;
		const do_dang = frm.doc.kh_aph_loai_kho === "Dở dang dây chuyền" || frm.doc.kh_aph_kho_bon;
		if (do_dang && kh_aph.b0112.on("factory_costing")) {
			frm.add_custom_button(__("Quyết toán dở dang về 0"), () => kh_aph.b0112.quyet_toan(frm), __("Kho"));
		}
		if (kh_aph.b0112.on("kho_chuan")) {
			frm.add_custom_button(__("Kiểm kê có mốc"), () => kh_aph.b0112.kiem_ke(frm), __("Kho"));
		}
	},
});
