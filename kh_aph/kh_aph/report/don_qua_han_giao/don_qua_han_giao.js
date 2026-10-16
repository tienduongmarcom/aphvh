// 0.11.3: Đơn quá hạn giao (Q189–Q190).
frappe.query_reports["Don qua han giao"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company"},
		{fieldname: "customer", label: __("Khách"), fieldtype: "Link", options: "Customer"},
		{fieldname: "ngay", label: __("Tính đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
	],
};
