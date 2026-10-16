// Lượt 0.14: công nợ với giám đốc (thu / chi hộ qua tài khoản cá nhân). Nút "Thu / chi hộ" lập bút toán nháp.
frappe.query_reports["Cong no voi giam doc"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company"},
		{fieldname: "nhan_vien", label: __("Người"), fieldtype: "Link", options: "Employee"},
		{fieldname: "den_ngay", label: __("Đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
	],
	onload(report) {
		report.page.add_inner_button(__("Thu / chi hộ"), () => kh_aph_thu_chi_ho_dialog(() => report.refresh()));
	},
};
window.kh_aph_thu_chi_ho_dialog = window.kh_aph_thu_chi_ho_dialog || function (sau) {
	const d = new frappe.ui.Dialog({
		title: __("Thu / chi hộ qua tài khoản cá nhân"),
		fields: [
			{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
			 default: frappe.defaults.get_user_default("Company")},
			{fieldname: "loai", label: __("Loại"), fieldtype: "Select", reqd: 1, options: [
				"Giám đốc thu hộ tiền khách", "Giám đốc chi hộ trả nhà cung cấp", "Giám đốc chi hộ chi phí",
				"Giám đốc nộp lại tiền thu hộ", "Công ty hoàn tiền chi hộ"].join("\n")},
			{fieldname: "nhan_vien", label: __("Người thu / chi hộ"), fieldtype: "Link", options: "Employee", reqd: 1},
			{fieldname: "khach", label: __("Khách"), fieldtype: "Link", options: "Customer",
			 depends_on: "eval:doc.loai=='Giám đốc thu hộ tiền khách'"},
			{fieldname: "nha_cung_cap", label: __("Nhà cung cấp"), fieldtype: "Link", options: "Supplier",
			 depends_on: "eval:doc.loai=='Giám đốc chi hộ trả nhà cung cấp'"},
			{fieldname: "tk_doi_ung", label: __("Tài khoản đối ứng (chi phí / tiền)"), fieldtype: "Link", options: "Account",
			 depends_on: "eval:['Giám đốc chi hộ chi phí','Giám đốc nộp lại tiền thu hộ','Công ty hoàn tiền chi hộ'].includes(doc.loai)",
			 get_query: () => ({filters: {company: d.get_value("company"), is_group: 0}})},
			{fieldname: "so_tien", label: __("Số tiền"), fieldtype: "Currency", reqd: 1},
			{fieldname: "ngay", label: __("Ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
			{fieldname: "noi_dung", label: __("Nội dung"), fieldtype: "Small Text", reqd: 1},
		],
		primary_action_label: __("Lập bút toán nháp"),
		primary_action(v) {
			frappe.call({method: "kh_aph.tien_vay.thu_chi_ho", args: v, callback: (r) => {
				d.hide();
				frappe.show_alert({message: __("Đã lập bút toán nháp {0}, kiểm rồi xác nhận", [r.message.journal_entry]), indicator: "green"});
				sau && sau();
			}});
		},
	});
	d.show();
};
