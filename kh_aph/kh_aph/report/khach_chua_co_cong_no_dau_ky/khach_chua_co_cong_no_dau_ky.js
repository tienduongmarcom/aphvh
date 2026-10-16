// Lượt 0.13: khách đã giao dịch sau ngày đầu kỳ mà chưa có công nợ đầu kỳ — ưu tiên tổng hợp từ sổ giấy.
frappe.query_reports["Khach chua co cong no dau ky"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
			default: frappe.defaults.get_user_default("Company")},
		{fieldname: "ngay", label: __("Ngày đầu kỳ"), fieldtype: "Date"},
	],
	onload(report) {
		frappe.call("kh_aph.dau_ky.ngay_dau_ky").then((r) => {
			if (r.message && !report.get_filter_value("ngay")) report.set_filter_value("ngay", r.message);
		});
	},
};
