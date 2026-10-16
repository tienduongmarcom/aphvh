// Lượt 0.14 (cờ kh_aph_trung_tam_ban): duyệt giá dưới sàn trên đơn chung; in lại phiếu xuất kho kèm số hóa đơn MISA.
(function () {
	const bat = () => (frappe.boot.kh_aph || {}).trung_tam_ban;

	frappe.ui.form.on("APH Shared Sales Order", {
		refresh(frm) {
			if (!bat() || !(frappe.boot.kh_aph || {}).gia_san) return;
			if (frm.doc.docstatus !== 0 || frm.is_new() || !frm.doc.kh_aph_duoi_san || frm.doc.kh_aph_duyet_san_boi) return;
			frm.dashboard.set_headline_alert(__("Có dòng dưới giá sàn, cần duyệt trước khi xác nhận"), "orange");
			frm.add_custom_button(__("Duyệt giá dưới sàn"), () => {
				frappe.call({method: "kh_aph.trung_tam_ban.xem_duoi_san_chung", args: {name: frm.doc.name}}).then((r) => {
					const m = r.message || {};
					if (!m.duoc_duyet) return frappe.msgprint(__("Dòng {0} dưới giá sàn. Bạn không có quyền duyệt; báo người duyệt.",
						[(m.dong || []).map((x) => x.idx).join(", ")]));
					frappe.prompt({fieldname: "ly_do", label: __("Lý do"), fieldtype: "Small Text", reqd: 1,
						description: (m.dong || []).map((x) => `Dòng ${x.idx} ${x.item_code} (${x.company}): thấp hơn sàn ${x.phan_tram}%`).join("<br>")},
					(v) => frappe.call({method: "kh_aph.trung_tam_ban.duyet_don_chung", args: {name: frm.doc.name, ly_do: v.ly_do},
						callback: () => frm.reload_doc()}), __("Duyệt giá dưới sàn"));
				});
			});
		},
	});

	frappe.ui.form.on("Delivery Note", {
		refresh(frm) {
			if (!bat() || frm.doc.docstatus !== 1 || frm.doc.is_return) return;
			frm.add_custom_button(__("In lại phiếu xuất kho"), () => frappe.call({method: "kh_aph.trung_tam_ban.in_lai",
				args: {delivery_note: frm.doc.name}}).then((r) => {
				const w = window.open("", "_blank");
				w.document.write(r.message.html);
				w.document.close();
				w.focus();
				setTimeout(() => w.print(), 600);
				frm.reload_doc();
			}), __("Quầy bán hàng"));
		},
	});
})();
