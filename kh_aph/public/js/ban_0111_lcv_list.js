// kh_aph 0.11.1 — Phân bổ chi phí sản xuất cuối tháng (R079): tạo chứng từ NHÁP, kế toán xem rồi tự ghi sổ.
frappe.listview_settings["Landed Cost Voucher"] = Object.assign(frappe.listview_settings["Landed Cost Voucher"] || {}, {
	onload(listview) {
		if (!(frappe.boot.kh_aph && frappe.boot.kh_aph.factory_costing)) return;
		listview.page.add_inner_button(__("Phân bổ chi phí sản xuất tháng"), () =>
			frappe.prompt([
				{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
					default: frappe.defaults.get_user_default("Company")},
				{fieldname: "thang", label: __("Tháng (YYYY-MM)"), fieldtype: "Data", reqd: 1,
					default: frappe.datetime.get_today().slice(0, 7)},
			], (v) => frappe.call({method: "kh_aph.factory_costing.phan_bo_thang", args: v, freeze: true}).then((r) => {
				const m = r.message, dong = [];
				for (const [x, ten] of Object.entries(m.lcv || {})) dong.push(`${x}: ${ten}`);
				if (m.but_toan_chung) dong.push(__("Nhà máy chung → 6323: {0}", [m.but_toan_chung]));
				for (const b of m.bo_qua || []) dong.push(`<i>${b[0]}${b[1] ? " / " + b[1] : ""}: ${b[2]}</i>`);
				frappe.msgprint(dong.join("<br>") || __("Không có số dư cần phân bổ"), __("Chứng từ nháp kỳ {0}", [m.ky]));
				listview.refresh();
			}), __("Phân bổ chi phí sản xuất cuối tháng")));
	},
});
