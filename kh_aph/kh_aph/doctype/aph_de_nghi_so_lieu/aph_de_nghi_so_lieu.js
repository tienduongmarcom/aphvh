// 0.12.0 (cờ kh_aph_du_lieu): đề nghị cập nhật số liệu nhà máy, có người duyệt.
frappe.ui.form.on("APH De nghi so lieu", {
	refresh(frm) {
		if (frm.is_new()) return;
		const goi = (method, args, msg) => frappe.call({
			method: "kh_aph.du_lieu." + method, args: {name: frm.doc.name, ...args}, freeze: true,
			callback: () => { frappe.show_alert({message: msg, indicator: "green"}); frm.reload_doc(); },
		});
		if (["Nháp", "Trả lại"].includes(frm.doc.trang_thai)) {
			frm.add_custom_button(__("Gửi duyệt"), () => goi("gui", {}, __("Đã gửi duyệt"))).addClass("btn-primary");
		}
		if (frm.doc.trang_thai === "Chờ duyệt" && (frappe.user.has_role("Accounts Manager") || frappe.user.has_role("System Manager"))) {
			frm.add_custom_button(__("Duyệt và áp dụng"), () => frappe.confirm(
				__("Ghi các giá trị mới vào mặt hàng / định mức?"), () => goi("duyet", {}, __("Đã áp dụng")))).addClass("btn-primary");
			frm.add_custom_button(__("Trả lại"), () => frappe.prompt(
				{fieldname: "ly_do", label: __("Lý do trả lại"), fieldtype: "Small Text", reqd: 1},
				(v) => goi("tra_lai", {ly_do: v.ly_do}, __("Đã trả lại")), __("Trả lại đề nghị")));
		}
	},
});
