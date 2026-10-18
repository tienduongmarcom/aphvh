// kh_aph 0.11.3 — thao tác ngắn bằng Dialog (docs/kien-truc-giao-dien.md). Chỉ hiện khi cờ sales_p1 bật.
frappe.provide("kh_aph.b0113");
kh_aph.b0113.on = () => !!(frappe.boot.kh_aph && frappe.boot.kh_aph.sales_p1);

frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		if (!kh_aph.b0113.on() || frm.doc.docstatus !== 1 || ["Closed", "Completed"].includes(frm.doc.status)) return;
		frm.add_custom_button(__("Gia hạn thanh toán"), () =>
			frappe.prompt([
				{fieldname: "han_moi", label: __("Hạn mới"), fieldtype: "Date", reqd: 1, default: frm.doc.kh_aph_han_thanh_toan},
				{fieldname: "ly_do", label: __("Lý do gia hạn"), fieldtype: "Small Text", reqd: 1},
			], (v) => frappe.call({method: "kh_aph.sales_p1.gia_han_thanh_toan", args: {sales_order: frm.doc.name, ...v}, freeze: true})
				.then((r) => {
					frappe.show_alert({message: __("Đã gia hạn; cập nhật {0} hóa đơn còn nợ", [(r.message.hoa_don_cap_nhat || []).length]), indicator: "green"});
					frm.reload_doc();
				}), __("Gia hạn thanh toán (Q166–Q168)")), __("Công nợ"));
	},
});

frappe.ui.form.on("Delivery Note", {
	refresh(frm) {
		if (!kh_aph.b0113.on() || frm.doc.docstatus !== 1 || frm.doc.is_return) return;
		if (frm.doc.kh_aph_delivery_state && frm.doc.kh_aph_delivery_state !== "Đang giao") return;
		frm.add_custom_button(__("Đổi địa chỉ giao"), () =>
			frappe.prompt([
				{fieldname: "dia_chi", label: __("Địa chỉ mới"), fieldtype: "Link", options: "Address", reqd: 1,
					get_query: () => ({query: "frappe.contacts.doctype.address.address.address_query",
						filters: {link_doctype: "Customer", link_name: frm.doc.customer}})},
				{fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1},
			], (v) => frappe.call({method: "kh_aph.sales_p1.doi_dia_chi_giao", args: {delivery_note: frm.doc.name, ...v}, freeze: true})
				.then(() => frm.reload_doc()), __("Đổi địa chỉ khi đang giao (Q180)")), __("Điều chỉnh giao"));
	},
});

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (!kh_aph.b0113.on() || frm.doc.docstatus !== 1 || frm.doc.is_return) return;
		if (frm.doc.outstanding_amount > 0) {
			frm.add_custom_button(__("Giảm giá sau giao"), () =>
				frappe.prompt([
					{fieldname: "so_tien", label: __("Tổng tiền khách được giảm (gồm thuế nếu hóa đơn có thuế)"), fieldtype: "Currency", reqd: 1},
					{fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1},
				], (v) => frappe.call({method: "kh_aph.sales_p1.giam_gia_sau_giao", args: {sales_invoice: frm.doc.name, ...v}, freeze: true})
					.then((r) => frappe.set_route("Form", "Journal Entry", r.message.but_toan)), __("Giảm giá sau giao (R026)")), __("Điều chỉnh"));
		}
		if (frm.doc.kh_aph_xuat_hoa_don === "Có" && !frm.doc.kh_aph_hd_so) {
			frm.add_custom_button(__("Nhận xử lý hóa đơn MISA"), () =>
				frappe.call({method: "kh_aph.sales_p1.nhan_xu_ly", args: {sales_invoices: JSON.stringify([frm.doc.name])}, freeze: true})
					.then((r) => frappe.set_route("Form", "APH Hoa don ngoai", r.message.ho_so)), __("Hóa đơn MISA"));
		}
	},
});
