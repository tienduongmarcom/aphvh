// Lượt 0.14: sổ quỹ tiền mặt / sổ tiền gửi ngân hàng, tồn sau từng phiếu. In: nút In của báo cáo (có chữ ký).
frappe.query_reports["So quy va tien gui"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
		 default: frappe.defaults.get_user_default("Company")},
		{fieldname: "account", label: __("Tài khoản tiền"), fieldtype: "Link", options: "Account", reqd: 1,
		 get_query: () => ({filters: {company: frappe.query_report.get_filter_value("company"), is_group: 0,
		                             account_type: ["in", ["Cash", "Bank"]]}})},
		{fieldname: "tu_ngay", label: __("Từ ngày"), fieldtype: "Date", default: frappe.datetime.month_start()},
		{fieldname: "den_ngay", label: __("Đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
	],
};
