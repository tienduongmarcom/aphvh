// Lượt 0.14: dư nợ vay theo khế ước. Nút "Trích lãi tháng" lập bút toán nháp Nợ 6351 / Có 3352.
frappe.query_reports["Du no vay theo khe uoc"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company"},
		{fieldname: "ngay", label: __("Đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
		{fieldname: "nhom_han", label: __("Nhóm hạn"), fieldtype: "Select",
		 options: ["", "Quá hạn", "Trong 7 ngày", "Trong 30 ngày", "Trong 90 ngày", "Sau 90 ngày"].join("\n")},
		{fieldname: "ca_da_tat_toan", label: __("Gồm khế ước đã tất toán"), fieldtype: "Check"},
	],
	onload(report) {
		report.page.add_inner_button(__("Trích lãi tháng"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Trích lãi vay tháng (bút toán nháp)"),
				fields: [
					{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
					 default: frappe.query_report.get_filter_value("company")},
					{fieldname: "den_ngay", label: __("Tháng (chọn một ngày trong tháng)"), fieldtype: "Date", reqd: 1,
					 default: frappe.datetime.get_today()},
				],
				primary_action_label: __("Lập bút toán nháp"),
				primary_action(v) {
					frappe.call({method: "kh_aph.tien_vay.trich_lai", args: v, callback: (r) => {
						d.hide();
						const m = r.message || {};
						if (m.journal_entry) frappe.set_route("Form", "Journal Entry", m.journal_entry);
						else frappe.msgprint(m.ly_do || __("Không có lãi cần trích"));
					}});
				},
			});
			d.show();
		});
	},
};
