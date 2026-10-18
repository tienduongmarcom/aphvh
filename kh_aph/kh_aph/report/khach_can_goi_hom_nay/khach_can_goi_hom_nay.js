// Lượt 0.13: danh sách gọi thu nợ hôm nay. Bấm "Ghi cuộc gọi" để lưu kết quả và ngày hẹn trả.
frappe.query_reports["Khach can goi hom nay"] = {
	filters: [{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company"}],
	onload(report) {
		report.page.add_inner_button(__("Ghi cuộc gọi"), () => {
			const d = new frappe.ui.Dialog({
				title: __("Ghi cuộc gọi thu nợ"),
				fields: [
					{fieldname: "customer", label: __("Khách"), fieldtype: "Link", options: "Customer", reqd: 1},
					{fieldname: "ket_qua", label: __("Kết quả"), fieldtype: "Small Text", reqd: 1},
					{fieldname: "hen_tra", label: __("Hẹn trả ngày"), fieldtype: "Date"},
				],
				primary_action_label: __("Lưu"),
				primary_action(v) {
					frappe.call({method: "kh_aph.ban_quay.ghi_cuoc_goi", args: v, callback: () => { d.hide(); report.refresh(); }});
				},
			});
			d.show();
		});
	},
};
