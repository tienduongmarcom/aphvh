// 0.11.4: Lãi gộp quản trị — cộng ngang 4 đơn vị, không phải hợp nhất kế toán.
frappe.query_reports["Lai gop quan tri"] = {
	filters: [
		{fieldname: "tu_ngay", label: __("Từ ngày"), fieldtype: "Date", default: frappe.datetime.month_start()},
		{fieldname: "den_ngay", label: __("Đến ngày"), fieldtype: "Date", default: frappe.datetime.get_today()},
		{fieldname: "theo", label: __("Xem theo"), fieldtype: "Select", options: "Công ty\nKho\nMặt hàng\nKhách\nĐơn", default: "Công ty"},
		{fieldname: "company", label: __("Chỉ đơn vị"), fieldtype: "Link", options: "Company"},
	],
};
