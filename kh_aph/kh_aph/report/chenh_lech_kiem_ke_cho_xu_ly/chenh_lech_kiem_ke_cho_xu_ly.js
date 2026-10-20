// Lượt 0.13: xử lý chênh lệch kiểm kê bước 2 theo vụ. Lập bút toán nháp; kế toán trưởng xem và xác nhận.
frappe.query_reports["Chenh lech kiem ke cho xu ly"] = {
	filters: [{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company"}],
	onload(report) {
		report.page.add_inner_button(__("Xử lý chênh lệch"), () => {
			const vu = (report.data || []).map((r) => r.bien_ban);
			if (!vu.length) return frappe.msgprint(__("Không có vụ chờ xử lý"));
			const d = new frappe.ui.Dialog({
				title: __("Xử lý chênh lệch kiểm kê"),
				size: "large",
				fields: [
					{fieldname: "bien_ban", label: __("Vụ"), fieldtype: "Select", options: vu, reqd: 1},
					{fieldname: "dong", fieldtype: "Table", in_place_edit: true, fields: [
						{fieldname: "phuong_an", label: __("Phương án"), fieldtype: "Select", in_list_view: 1, reqd: 1, options: [
							"Thiếu: ghi giá vốn (hao hụt)", "Thiếu: cá nhân bồi thường",
							"Thừa: trả lại người khác", "Thừa: không rõ chủ, ghi thu nhập khác"]},
						{fieldname: "so_tien", label: __("Số tiền"), fieldtype: "Currency", in_list_view: 1, reqd: 1},
						{fieldname: "party_type", label: __("Loại đối tượng"), fieldtype: "Link", options: "DocType", in_list_view: 1},
						{fieldname: "party", label: __("Đối tượng"), fieldtype: "Dynamic Link", options: "party_type", in_list_view: 1},
						{fieldname: "ghi_chu", label: __("Ghi chú / số biên bản xử lý"), fieldtype: "Data", in_list_view: 1},
					]},
				],
				primary_action_label: __("Lập bút toán nháp"),
				primary_action(v) {
					frappe.call({method: "kh_aph.kho_van_hanh.xu_ly_chenh_lech", args: {bien_ban: v.bien_ban, dong: v.dong},
						freeze: true, callback: (r) => { d.hide(); frappe.set_route("Form", "Journal Entry", r.message.but_toan); }});
				},
			});
			d.show();
		});
	},
};
