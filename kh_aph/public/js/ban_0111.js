// kh_aph 0.11.1 — thao tác ngắn bằng Dialog (docs/kien-truc-giao-dien.md). Chỉ hiện khi cờ tương ứng bật (frappe.boot.kh_aph).
frappe.provide("kh_aph.b0111");
kh_aph.b0111.on = (co) => !!(frappe.boot.kh_aph && frappe.boot.kh_aph[co]);

frappe.ui.form.on("Delivery Note", {
	refresh(frm) {
		if (!kh_aph.b0111.on("sales_adjust") || frm.doc.docstatus !== 1 || frm.doc.is_return) return;
		if (frm.doc.kh_aph_delivery_state && frm.doc.kh_aph_delivery_state !== "Đang giao") return;
		frm.add_custom_button(__("Xe quay về (lập phiếu trả lại nháp)"), () =>
			frappe.call({method: "kh_aph.sales_adjust.xe_quay_ve", args: {delivery_note: frm.doc.name}, freeze: true})
				.then((r) => frappe.set_route("Form", "Delivery Note", r.message.phieu_tra)), __("Điều chỉnh giao"));
		frm.add_custom_button(__("Chuyển sang khách khác"), () =>
			frappe.prompt([{fieldname: "sales_order", label: __("Đơn của khách mới"), fieldtype: "Link", options: "Sales Order", reqd: 1,
				get_query: () => ({filters: {docstatus: 1, company: frm.doc.company, customer: ["!=", frm.doc.customer]}})}],
			(v) => frappe.call({method: "kh_aph.sales_adjust.chuyen_khach", args: {delivery_note: frm.doc.name, ...v}, freeze: true})
				.then((r) => frappe.msgprint(__("Đã lập nháp: phiếu trả lại {0}, phiếu giao mới {1}. Sửa lượng thực tế rồi ghi sổ.",
					[r.message.phieu_tra, r.message.phieu_giao_moi]))), __("Chuyển sang khách khác")), __("Điều chỉnh giao"));
	},
});

frappe.ui.form.on("APH Shared Sales Order", {
	refresh(frm) {
		if (!kh_aph.b0111.on("sales_adjust") || frm.doc.docstatus !== 1 || frm.doc.kh_aph_dong_luc) return;
		frm.add_custom_button(__("Đóng phần chưa giao"), () =>
			frappe.prompt([{fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1}],
				(v) => frappe.call({method: "kh_aph.sales_adjust.dong_phan_chua_giao", args: {shared_order: frm.doc.name, ...v}, freeze: true})
					.then(() => frm.reload_doc()), __("Đóng phần chưa giao")));
	},
});
// Nút quyết toán dở dang trên Warehouse chuyển sang public/js/ban_0112.js (0.11.2: kho loại Dở dang dây chuyền).
