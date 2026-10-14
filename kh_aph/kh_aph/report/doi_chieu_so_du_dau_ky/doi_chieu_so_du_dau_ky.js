// 0.12.1: Đối chiếu số dư đầu kỳ. Nút "Chốt số dư đầu kỳ" khóa tháng đầu kỳ khi bốn loại đã khớp.
frappe.query_reports["Doi chieu so du dau ky"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
			default: frappe.defaults.get_user_default("Company")},
		{fieldname: "ngay", label: __("Ngày đầu kỳ"), fieldtype: "Date", default: "2026-09-30"},
	],
	onload(report) {
		report.page.add_inner_button(__("Chốt số dư đầu kỳ"), () => {
			const f = report.get_values();
			frappe.prompt({fieldname: "ly_do", label: __("Lý do / ghi chú chốt"), fieldtype: "Small Text", reqd: 1},
				(v) => frappe.call({
					method: "kh_aph.dau_ky.chot_dau_ky",
					args: {company: f.company, ngay: f.ngay, ly_do: v.ly_do},
					freeze: true,
					callback: (r) => { frappe.msgprint(__("Đã chốt và khóa kỳ {0}", [r.message.ky])); report.refresh(); },
				}), __("Chốt số dư đầu kỳ"), __("Chốt"));
		});
	},
};
