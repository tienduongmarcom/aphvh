frappe.query_reports["Tien thu ho chua xu ly"] = {
	filters: [
		{ fieldname: "company", label: __("Công ty"), fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") },
		{ fieldname: "trang_thai", label: __("Trạng thái"), fieldtype: "Select", options: "\nCần xử lý\nĐã xử lý", default: "Cần xử lý" },
		{ fieldname: "chu_hang", label: __("Chủ hàng"), fieldtype: "Data" },
		{ fieldname: "tu_ngay", label: __("Từ ngày"), fieldtype: "Date" },
		{ fieldname: "den_ngay", label: __("Đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today() },
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.kieu === "tong") value = `<b>${value}</b>`;
		if (data && column.fieldname === "so_ngay" && data.trang_thai === "Cần xử lý" && data.so_ngay > 7) value = `<span style="color:#c0392b">${value}</span>`;
		return value;
	},
};
