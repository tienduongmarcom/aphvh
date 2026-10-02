frappe.query_reports["Cong no don tong APH"] = {
	filters: [
		{ fieldname: "customer", label: "Khách hàng", fieldtype: "Link", options: "Customer" },
		{ fieldname: "from_date", label: "Từ ngày", fieldtype: "Date", default: frappe.datetime.add_months(frappe.datetime.get_today(), -3) },
		{ fieldname: "to_date", label: "Đến ngày", fieldtype: "Date", default: frappe.datetime.get_today() },
		{ fieldname: "chi_con_no", label: "Chỉ đơn còn phải thu", fieldtype: "Check", default: 1 },
	],
};
