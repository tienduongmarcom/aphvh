frappe.query_reports["Ton kho so luong"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Công ty"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "warehouse",
			label: __("Kho"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: () => ({ filters: { company: frappe.query_report.get_filter_value("company") } }),
		},
		{ fieldname: "item_group", label: __("Nhóm hàng"), fieldtype: "Link", options: "Item Group" },
		{ fieldname: "item_code", label: __("Mã hàng"), fieldtype: "Link", options: "Item" },
		{ fieldname: "show_zero", label: __("Hiện cả mã tồn 0"), fieldtype: "Check" },
	],
};
