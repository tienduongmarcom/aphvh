frappe.query_reports["Tong hop ban hang theo khach"] = {
	filters: [
		{ fieldname: "customer", label: "Khách hàng", fieldtype: "Link", options: "Customer", reqd: 1 },
		{ fieldname: "from_date", label: "Từ ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.month_start() },
		{ fieldname: "to_date", label: "Đến ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "company", label: "Chỉ một đơn vị", fieldtype: "Link", options: "Company" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.kieu !== "chung_tu") value = `<b>${value}</b>`;
		return value;
	},
};
