// kh_aph 0.11.4 — xác nhận công nợ (Customer), khóa / mở khóa kỳ (Company). Chỉ hiện khi cờ quan_tri bật.
frappe.provide("kh_aph.b0114");
kh_aph.b0114.on = () => !!(frappe.boot.kh_aph && frappe.boot.kh_aph.quan_tri);

frappe.ui.form.on("Customer", {
	refresh(frm) {
		if (!kh_aph.b0114.on() || frm.is_new()) return;
		frm.add_custom_button(__("Ghi nhận xác nhận công nợ"), () =>
			frappe.prompt([
				{fieldname: "ngay", label: __("Xác nhận đến ngày"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
				{fieldname: "so_du_xac_nhan", label: __("Số dư khách xác nhận"), fieldtype: "Currency", reqd: 1},
				{fieldname: "ghi_chu", label: __("Ghi chú (biên bản, người ký)"), fieldtype: "Small Text"},
			], (v) => frappe.call({method: "kh_aph.quan_tri.ghi_nhan_xac_nhan", args: {customer: frm.doc.name, ...v}, freeze: true})
				.then((r) => {
					frappe.msgprint(__("Sổ: {0}. Khách xác nhận: {1}. Chênh: {2}.",
						[format_currency(r.message.so_du_so), format_currency(r.message.so_du_xac_nhan), format_currency(r.message.chenh_lech)]));
					frm.reload_doc();
				}), __("Xác nhận công nợ")), __("Công nợ"));
	},
});

frappe.ui.form.on("Company", {
	refresh(frm) {
		if (!kh_aph.b0114.on() || frm.is_new()) return;
		const hoi = (method, tieu_de) => frappe.prompt([
			{fieldname: "thang", label: __("Tháng (YYYY-MM)"), fieldtype: "Data", reqd: 1, default: frappe.datetime.add_months(frappe.datetime.get_today(), -1).slice(0, 7),
				description: __("Chỉ khóa được tháng đã kết thúc (ERPNext).")},
			{fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1},
		], (v) => frappe.call({method, args: {company: frm.doc.name, ...v}, freeze: true})
			.then((r) => frappe.show_alert({message: r.message.ky, indicator: "green"})), tieu_de);
		frm.add_custom_button(__("Khóa kỳ"), () => hoi("kh_aph.quan_tri.khoa_ky", __("Khóa kỳ kế toán")), __("Kỳ kế toán"));
		frm.add_custom_button(__("Mở khóa kỳ"), () => hoi("kh_aph.quan_tri.mo_khoa_ky", __("Mở khóa kỳ kế toán")), __("Kỳ kế toán"));
	},
});
