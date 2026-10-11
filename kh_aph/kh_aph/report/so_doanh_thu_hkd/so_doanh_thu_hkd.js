frappe.query_reports["So doanh thu HKD"] = {
	filters: [
		{ fieldname: "company", label: "Hộ kinh doanh", fieldtype: "Link", options: "Company", reqd: 1,
		  default: frappe.defaults.get_user_default("Company") },
		{ fieldname: "mau_so", label: "Mẫu sổ", fieldtype: "Select", reqd: 1, default: "S2a-HKD",
		  options: "S1a-HKD\nS2a-HKD\nS2b-HKD" },
		{ fieldname: "from_date", label: "Từ ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.year_start() },
		{ fieldname: "to_date", label: "Đến ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "pham_vi", label: "Phạm vi", fieldtype: "Select", default: "Tất cả", options: "Tất cả\nChỉ bán có hóa đơn" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.kieu && data.kieu !== "ct") value = `<b>${value}</b>`;
		return value;
	},
};
