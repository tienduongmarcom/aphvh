// 0.11.3: hàng đợi hóa đơn chờ xuất trên MISA (R093–R098). Chọn dòng chưa ai nhận → "Nhận xử lý".
frappe.query_reports["Hoa don cho xuat"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị phát hành"), fieldtype: "Link", options: "Company"},
		{fieldname: "chi_chua_nhan", label: __("Chỉ hóa đơn chưa ai nhận"), fieldtype: "Check", default: 1},
	],
	get_datatable_options(options) {
		return Object.assign(options, {checkboxColumn: true});
	},
	onload(report) {
		report.page.add_inner_button(__("Nhận xử lý các hóa đơn đã chọn"), () => {
			const rows = report.datatable.rowmanager.getCheckedRows().map((i) => report.data[i]).filter((r) => r && !r.ho_so);
			if (!rows.length) {
				frappe.msgprint(__("Chọn hóa đơn chưa có người xử lý."));
				return;
			}
			frappe.call({method: "kh_aph.sales_p1.nhan_xu_ly", args: {sales_invoices: JSON.stringify(rows.map((r) => r.name))}, freeze: true})
				.then((r) => frappe.set_route("Form", "APH Hoa don ngoai", r.message.ho_so));
		});
	},
};
