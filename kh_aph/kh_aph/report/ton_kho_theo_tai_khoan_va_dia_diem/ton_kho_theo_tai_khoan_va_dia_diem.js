frappe.query_reports["Ton kho theo tai khoan va dia diem"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Công ty"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{ fieldname: "den_ngay", label: __("Đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today() },
		{
			fieldname: "chi_tk",
			label: __("Chỉ tài khoản"),
			fieldtype: "Link",
			options: "Account",
			get_query: () => ({ filters: { company: frappe.query_report.get_filter_value("company"), account_type: "Stock" } }),
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && (data.kieu === "tong_tk" || data.kieu === "tong")) value = `<b>${value}</b>`;
		if (data && column.fieldname === "chenh_lech" && data.chenh_lech) value = `<span style="color:#c0392b">${value}</span>`;
		return value;
	},
};
