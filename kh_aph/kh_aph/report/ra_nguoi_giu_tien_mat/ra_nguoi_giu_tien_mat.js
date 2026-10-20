frappe.query_reports["Ra nguoi giu tien mat"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
			default: frappe.defaults.get_user_default("Company")},
		{fieldname: "from_date", label: __("Từ ngày"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
		{fieldname: "to_date", label: __("Đến ngày"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
	],
};
