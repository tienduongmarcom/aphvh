// 0.11.4: Khách chưa xác nhận công nợ (R039).
frappe.query_reports["Khach chua xac nhan cong no"] = {
	filters: [{fieldname: "so_ngay", label: __("Quá số ngày"), fieldtype: "Int"}],
};
