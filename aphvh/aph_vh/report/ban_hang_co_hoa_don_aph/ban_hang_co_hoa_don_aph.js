frappe.query_reports["Ban hang co hoa don APH"] = {
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
			fieldname: "date_basis",
			label: __("Lọc theo"),
			fieldtype: "Select",
			options: "Ngày hạch toán\nNgày hóa đơn điện tử",
			default: "Ngày hạch toán",
		},
		{
			fieldname: "from_date",
			label: __("Từ ngày"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("Đến ngày"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
		},
		{ fieldname: "customer", label: __("Khách hàng"), fieldtype: "Link", options: "Customer" },
		{
			fieldname: "status",
			label: __("Số hóa đơn"),
			fieldtype: "Select",
			options: "\nĐã ghi số hóa đơn\nChưa ghi số hóa đơn",
		},
	],
};
