// 0.11.4: Dòng tiền 7 / 30 ngày.
frappe.query_reports["Dong tien 7 30 ngay"] = {
	filters: [{fieldname: "ngay", label: __("Ngày tính"), fieldtype: "Date", default: frappe.datetime.get_today()}],
};
