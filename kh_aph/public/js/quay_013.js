// Lượt 0.13 (cờ kh_aph_gia_san): giá sàn, thu tiền nhanh, in phiếu xuất kho 2 liên, đối soát công nợ, ghi cuộc gọi thu nợ.
(function () {
	const bat = () => (frappe.boot.kh_aph || {}).gia_san;

	function thu_tien(company, customer, hoa_don) {
        if (frappe.boot?.kh_aph?.ux_task_first && kh_aph.ux?.thu_tien)
            return kh_aph.ux.thu_tien(customer, hoa_don || [], company);
		const request_id = [...crypto.getRandomValues(new Uint8Array(16))].map(v => v.toString(16).padStart(2, "0")).join("");
		let sending = false;
		const d = new frappe.ui.Dialog({
			title: __("Thu tiền"),
			fields: [
				{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1, default: company},
				{fieldname: "customer", label: __("Khách"), fieldtype: "Link", options: "Customer", reqd: 1, default: customer},
				{fieldname: "tien_mat", label: __("Tiền mặt"), fieldtype: "Currency"},
				{fieldname: "nguoi_giu_tien", label: __("Người thực giữ tiền mặt"), fieldtype: "Link", options: "User",
					hidden: !frappe.boot.kh_aph?.cash_custody, depends_on: "eval:doc.tien_mat>0",
					description: __("Để trống là chưa xác minh; không mặc định người lập phiếu.")},
				{fieldname: "chuyen_khoan", label: __("Chuyển khoản"), fieldtype: "Currency"},
				{fieldname: "tk_ngan_hang", label: __("Tài khoản ngân hàng nhận"), fieldtype: "Link", options: "Account",
					depends_on: "eval:doc.chuyen_khoan>0",
					get_query: () => ({filters: {company: d.get_value("company"), account_type: "Bank", is_group: 0}})},
				{fieldname: "ma_gd", label: __("Mã giao dịch / nội dung chuyển khoản"), fieldtype: "Data", depends_on: "eval:doc.chuyen_khoan>0"},
				{fieldname: "ghi_chu", label: __("Ghi chú"), fieldtype: "Data"},
			],
			primary_action_label: __("Ghi phiếu thu"),
			primary_action(v) {
				if (sending) return;
				sending = true;
				d.get_primary_btn().prop("disabled", true);
				frappe.call({method: "kh_aph.ban_quay.thu_tien", args: {...v, request_id, hoa_don: hoa_don || []}, freeze: true,
					callback: (r) => {
						d.hide();
						(r.message.phieu_thu || []).forEach((pe) => window.open(
							`/printview?doctype=Payment%20Entry&name=${encodeURIComponent(pe)}&format=${encodeURIComponent("Phiếu thu chi")}&trigger_print=1`));
						frappe.show_alert({message: __("Đã ghi {0}", [r.message.phieu_thu.join(", ")]), indicator: "green"});
					}}).always(() => {
						sending = false;
						d.get_primary_btn().prop("disabled", false);
					});
			},
		});
		d.show();
	}

	function in_doi_soat(customer) {
		window.open(`/printview?doctype=Customer&name=${encodeURIComponent(customer)}&format=${encodeURIComponent("Biên bản đối soát công nợ")}&trigger_print=1`);
	}

	function nut_gia_san(frm) {
		if (frm.doc.docstatus !== 0 || frm.is_new() || !frm.doc.kh_aph_duoi_san || frm.doc.kh_aph_duyet_san_boi) return;
		frm.dashboard.set_headline_alert(__("Có dòng dưới giá sàn, cần duyệt trước khi xác nhận"), "orange");
		frm.add_custom_button(__("Duyệt giá dưới sàn"), () => {
			frappe.call({method: "kh_aph.ban_quay.xem_duoi_san", args: {doctype: frm.doctype, name: frm.doc.name}}).then((r) => {
				const m = r.message || {};
				if (!m.duoc_duyet) return frappe.msgprint(__("Dòng {0} dưới giá sàn. Bạn không có quyền duyệt; báo người duyệt.",
					[(m.dong || []).map((x) => x.idx).join(", ")]));
				frappe.prompt({fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1,
					description: (m.dong || []).map((x) => `Dòng ${x.idx} ${x.item_code}: thấp hơn sàn ${x.phan_tram}%`).join("<br>")},
				(v) => frappe.call({method: "kh_aph.ban_quay.duyet_gia_san", args: {doctype: frm.doctype, name: frm.doc.name, ly_do: v.ly_do},
					callback: () => frm.reload_doc()}), __("Duyệt giá dưới sàn"));
			});
		});
	}

	["Sales Order", "Sales Invoice"].forEach((dt) => frappe.ui.form.on(dt, {refresh(frm) { if (bat()) nut_gia_san(frm); }}));

	frappe.ui.form.on("Sales Invoice", {
		refresh(frm) {
			if (bat() && frm.doc.docstatus === 1 && !frm.doc.is_return && frm.doc.outstanding_amount > 0) {
				frm.add_custom_button(__("Thu tiền"), () => thu_tien(frm.doc.company, frm.doc.customer, [frm.doc.name]), __("Quầy bán hàng"));
			}
		},
	});

	frappe.ui.form.on("Delivery Note", {
		refresh(frm) {
			if (!bat() || frm.is_new() || frm.doc.is_return) return;
			if (!frappe.boot?.kh_aph?.ux_task_first) frm.add_custom_button(__("In phiếu xuất kho 2 liên"), () => frappe.call({method: "kh_aph.ban_quay.in_hai_lien",
				args: {delivery_note: frm.doc.name}}).then((r) => {
				const w = window.open("", "_blank");
				w.document.write(r.message);
				w.document.close();
				w.focus();
				setTimeout(() => w.print(), 600);
			}), __("Quầy bán hàng"));
			if (frm.doc.docstatus === 1) {
				frappe.db.get_list("Sales Invoice Item", {filters: {delivery_note: frm.doc.name, docstatus: 1}, fields: ["parent"], limit: 20})
					.then((rows) => {
						const hd = [...new Set((rows || []).map((x) => x.parent))];
						frm.add_custom_button(__("Thu tiền"), () => thu_tien(frm.doc.company, frm.doc.customer, hd), __("Quầy bán hàng"));
					});
				frm.add_custom_button(__("In đối soát công nợ"), () => in_doi_soat(frm.doc.customer), __("Quầy bán hàng"));
			}
		},
	});

	frappe.ui.form.on("Customer", {
		refresh(frm) {
			if (!bat() || frm.is_new()) return;
			if (!frappe.boot?.kh_aph?.ux_task_first) frm.add_custom_button(__("Thu tiền"), () => thu_tien(frappe.defaults.get_user_default("Company"), frm.doc.name, []), __("Quầy bán hàng"));
			frm.add_custom_button(__("In đối soát công nợ"), () => in_doi_soat(frm.doc.name), __("Quầy bán hàng"));
			frm.add_custom_button(__("Ghi cuộc gọi thu nợ"), () => frappe.prompt([
				{fieldname: "ket_qua", label: __("Kết quả"), fieldtype: "Small Text", reqd: 1},
				{fieldname: "hen_tra", label: __("Hẹn trả ngày"), fieldtype: "Date"},
			], (v) => frappe.call({method: "kh_aph.ban_quay.ghi_cuoc_goi", args: {customer: frm.doc.name, ...v},
				callback: () => frm.reload_doc()}), __("Ghi cuộc gọi thu nợ")), __("Quầy bán hàng"));
		},
	});
})();
