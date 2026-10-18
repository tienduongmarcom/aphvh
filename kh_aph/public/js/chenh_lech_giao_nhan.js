// Chênh lệch trên phiếu giao nguồn; mọi quyền và chuyển trạng thái kiểm lại tại server.
(function () {
	const state = "kh_aph_chenh_lech_state";
	const group = __("Chênh lệch giao nhận");
	function dialog(frm, title, action, fields) {
		if (frm.is_dirty()) return frappe.msgprint(__("Lưu phiếu trước khi xử lý chênh lệch"));
		const d = new frappe.ui.Dialog({title: __(title), fields, primary_action_label: __("Xác nhận"),
			primary_action(values) {
				if (action === "resolve") {
					if (values.cach_xu_ly !== "Phiếu trả hàng") values.phieu_tra = "";
					if (values.cach_xu_ly !== "Hóa đơn giảm") values.hoa_don_giam = "";
				}
				d.get_primary_btn().prop("disabled", true);
				frappe.call({method: "kh_aph.delivery_issue.cap_nhat", freeze: true,
					args: {name: frm.doc.name, modified: frm.doc.modified, action, values: JSON.stringify(values)}
				}).then(() => {d.hide(); return frm.reload_doc();}).finally(() => d.get_primary_btn().prop("disabled", false));
			}});
		d.show();
	}
	frappe.ui.form.on("Delivery Note", {
		refresh(frm) {
			const visible = !!(frappe.boot.kh_aph || {}).trung_tam_ban && frm.doc.docstatus === 1 && !frm.doc.is_return;
			Object.keys(frm.fields_dict).filter(k => k.startsWith("kh_aph_chenh_lech_")).forEach(k =>
				frm.toggle_display(k, visible && (k === state || !!frm.doc[state])));
			if (!visible) return;
			if (!frm.perm[0] || !frm.perm[0].write) return;
			const current = frm.doc[state];
			if (current !== "Đã xử lý") {
				frm.add_custom_button(__("Ghi nhận chênh lệch"), () => dialog(frm, "Ghi nhận chênh lệch", "report", [
					{fieldname: "noi_dung", label: __("Nội dung chênh lệch"), fieldtype: "Small Text", reqd: 1,
						default: frm.doc.kh_aph_chenh_lech_noi_dung,
						description: __("Ghi lượng/bao, hiện tượng và việc cần xác minh. Thao tác này không điều chỉnh kho hoặc công nợ.")}
				]), group);
			}
			const chief = frappe.session.user === "Administrator" || frappe.user.has_role("Accounts Manager");
			if (!chief || !current) return;
			if (current === "Đã xử lý") {
				frm.add_custom_button(__("Mở lại chênh lệch"), () => dialog(frm, "Mở lại chênh lệch", "reopen", [
					{fieldname: "ly_do", label: __("Lý do mở lại"), fieldtype: "Small Text", reqd: 1}
				]), group);
				return;
			}
			frm.add_custom_button(__("Giao người xử lý"), () => dialog(frm, "Giao người xử lý chênh lệch", "assign", [
				{fieldname: "nguoi_phu_trach", label: __("Người phụ trách"), fieldtype: "Link", options: "User", reqd: 1,
					default: frm.doc.kh_aph_chenh_lech_phu_trach, get_query: () => ({filters: {enabled: 1, user_type: "System User"}})},
				{fieldname: "han_xu_ly", label: __("Hạn xử lý"), fieldtype: "Date", reqd: 1, default: frm.doc.kh_aph_chenh_lech_han}
			]), group);
			if (current !== "Đang xử lý") return;
			frm.add_custom_button(__("Chốt xử lý chênh lệch"), () => dialog(frm, "Chốt xử lý chênh lệch", "resolve", [
				{fieldname: "ket_qua", label: __("Kết quả xác minh và xử lý"), fieldtype: "Small Text", reqd: 1},
				{fieldname: "cach_xu_ly", label: __("Cách xử lý"), fieldtype: "Select", reqd: 1,
					options: "\nĐối chiếu, không điều chỉnh sổ\nPhiếu trả hàng\nHóa đơn giảm",
					description: __("Chọn chứng từ chuẩn đã ghi sổ. Không tạo trả hàng nếu hàng không thực nhập lại kho; trường hợp khác giữ hồ sơ mở để xử lý đúng nghiệp vụ.")},
				{fieldname: "phieu_tra", label: __("Phiếu trả hàng"), fieldtype: "Link", options: "Delivery Note",
					depends_on: "eval:doc.cach_xu_ly=='Phiếu trả hàng'", mandatory_depends_on: "eval:doc.cach_xu_ly=='Phiếu trả hàng'",
					get_query: () => ({filters: {docstatus: 1, is_return: 1, return_against: frm.doc.name, company: frm.doc.company, customer: frm.doc.customer}})},
				{fieldname: "hoa_don_giam", label: __("Hóa đơn giảm"), fieldtype: "Link", options: "Sales Invoice",
					depends_on: "eval:doc.cach_xu_ly=='Hóa đơn giảm'", mandatory_depends_on: "eval:doc.cach_xu_ly=='Hóa đơn giảm'",
					get_query: () => ({filters: {docstatus: 1, is_return: 1, update_stock: 0, company: frm.doc.company, customer: frm.doc.customer}})}
			]), group);
		},
	});
})();
