frappe.query_reports["So ke toan HKD"] = {
	filters: [
		{ fieldname: "company", label: "Hộ kinh doanh", fieldtype: "Link", options: "Company", reqd: 1,
		  default: frappe.defaults.get_user_default("Company") },
		{ fieldname: "mau_so", label: "Mẫu sổ", fieldtype: "Select", reqd: 1, default: "S2c-HKD",
		  options: "S2c-HKD\nS2d-HKD\nS2e-HKD" },
		{ fieldname: "from_date", label: "Từ ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.month_start() },
		{ fieldname: "to_date", label: "Đến ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "thue_suat_tncn", label: "Thuế suất TNCN (%) – S2c", fieldtype: "Float", default: 20,
		  depends_on: "eval:doc.mau_so=='S2c-HKD'" },
		{ fieldname: "item_code", label: "Mặt hàng – S2d", fieldtype: "Link", options: "Item",
		  depends_on: "eval:doc.mau_so=='S2d-HKD'" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.kieu && data.kieu !== "ct") value = `<b>${value}</b>`;
		return value;
	},
};
