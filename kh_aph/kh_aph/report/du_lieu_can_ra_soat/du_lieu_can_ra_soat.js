// Dữ liệu cần rà soát & điều chỉnh dần (0.11.1, cờ kh_aph_data_review). Chỉ đọc; mỗi dòng mở chứng từ để sửa.
frappe.query_reports["Du lieu can ra soat"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company",
			default: frappe.defaults.get_user_default("Company")},
		{fieldname: "nhom", label: __("Nhóm kiểm"), fieldtype: "Select",
			options: "\nTài sản\nGiá tạm\nTồn kho\nKho dở dang\nBao bì\nDanh mục"},
	],
};
