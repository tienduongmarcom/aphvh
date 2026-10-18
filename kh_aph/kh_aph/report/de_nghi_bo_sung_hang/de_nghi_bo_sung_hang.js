// Lượt 0.13 (R057–R059): mã dưới ngưỡng đặt lại; tạo yêu cầu chuyển kho, mỗi dòng chọn kho nguồn riêng, không giữ hàng.
frappe.query_reports["De nghi bo sung hang"] = {
	filters: [
		{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company"},
		{fieldname: "warehouse", label: __("Kho nhận"), fieldtype: "Link", options: "Warehouse"},
	],
	onload(report) {
		report.page.add_inner_button(__("Tạo yêu cầu chuyển kho"), () => {
			const rows = (report.data || []).filter((r) => r.de_nghi > 0);
			if (!rows.length) return frappe.msgprint(__("Không có dòng cần bổ sung"));
			const d = new frappe.ui.Dialog({
				title: __("Yêu cầu chuyển kho (chưa xuất thì không giữ hàng)"),
				size: "extra-large",
				fields: [{fieldname: "dong", fieldtype: "Table", cannot_add_rows: false, in_place_edit: true,
					data: rows.map((r) => ({item_code: r.item_code, warehouse: r.warehouse, qty: r.de_nghi})),
					fields: [
						{fieldname: "item_code", label: __("Mặt hàng"), fieldtype: "Link", options: "Item", in_list_view: 1, reqd: 1},
						{fieldname: "warehouse", label: __("Kho nhận"), fieldtype: "Link", options: "Warehouse", in_list_view: 1, reqd: 1},
						{fieldname: "from_warehouse", label: __("Kho nguồn"), fieldtype: "Link", options: "Warehouse", in_list_view: 1, reqd: 1},
						{fieldname: "qty", label: __("Số lượng"), fieldtype: "Float", in_list_view: 1, reqd: 1},
					]}],
				primary_action_label: __("Tạo"),
				primary_action(v) {
					frappe.call({method: "kh_aph.kho_van_hanh.tao_yeu_cau_chuyen", args: {dong: v.dong}, freeze: true,
						callback: (r) => { d.hide(); frappe.msgprint(__("Đã tạo: {0}", [r.message.yeu_cau.join(", ")])); }});
				},
			});
			d.show();
		});
	},
};
