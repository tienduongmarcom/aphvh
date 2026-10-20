// Lượt 0.13 (cờ kh_aph_kho_van_hanh): hàng không giao được → chuyển kho khác; sửa số lượng nhập sai.
frappe.ui.form.on("Delivery Note", {
	refresh(frm) {
		if (!(frappe.boot.kh_aph || {}).kho_van_hanh || frm.doc.docstatus !== 1 || frm.doc.is_return) return;
		if (frm.doc.kh_aph_delivery_state === "Đang giao") {
			frm.add_custom_button(__("Chuyển kho khác"), () => frappe.prompt(
				{fieldname: "warehouse", label: __("Kho nhận lại hàng"), fieldtype: "Link", options: "Warehouse", reqd: 1,
					get_query: () => ({filters: {company: frm.doc.company, is_group: 0}})},
				(v) => frappe.call({method: "kh_aph.kho_van_hanh.chuyen_kho_khac",
					args: {delivery_note: frm.doc.name, warehouse: v.warehouse}, freeze: true,
					callback: (r) => frappe.set_route("Form", "Delivery Note", r.message.phieu_tra)}),
				__("Hàng không giao được")), __("Hàng không giao được"));
		}
		if (frappe.user.has_role("Accounts Manager")) {
			frm.add_custom_button(__("Sửa số lượng nhập sai"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Sửa số lượng nhập sai (hủy và lập lại chứng từ)"),
					fields: [
						{fieldname: "dong", fieldtype: "Table", cannot_add_rows: true, in_place_edit: true,
							data: frm.doc.items.map((r) => ({name_dong: r.name, item_code: r.item_code, qty: r.qty})),
							fields: [
								{fieldname: "name_dong", fieldtype: "Data", hidden: 1},
								{fieldname: "item_code", label: __("Mặt hàng"), fieldtype: "Data", read_only: 1, in_list_view: 1},
								{fieldname: "qty", label: __("Số lượng đúng"), fieldtype: "Float", in_list_view: 1, reqd: 1},
							]},
						{fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1},
					],
					primary_action_label: __("Hủy và lập lại"),
					primary_action(v) {
						const sl = {};
						(v.dong || []).forEach((r) => { sl[r.name_dong] = r.qty; });
						frappe.call({method: "kh_aph.kho_van_hanh.sua_so_luong",
							args: {delivery_note: frm.doc.name, so_luong: sl, ly_do: v.ly_do}, freeze: true,
							callback: (r) => { d.hide(); frappe.set_route("Form", "Delivery Note", r.message.phieu_moi); }});
					},
				});
				d.show();
			}, __("Hàng không giao được"));
		}
	},
});
