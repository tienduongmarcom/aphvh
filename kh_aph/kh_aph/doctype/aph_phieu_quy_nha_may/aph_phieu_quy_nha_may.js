frappe.ui.form.on("APH Phieu quy nha may", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.loai === "Bàn giao tiền" && frm.doc.trang_thai === "Chờ nhận") {
			frm.add_custom_button(__("Xác nhận đã nhận tiền"), () => {
				frappe.prompt([
					{fieldname: "so_thuc_nhan", label: __("Số tiền đếm được"), fieldtype: "Currency", reqd: 1, default: frm.doc.tong_tien},
					{fieldname: "tai_khoan_nhan", label: __("Quỹ/tài khoản nhận"), fieldtype: "Link", options: "Account", reqd: 1,
					 get_query: () => ({filters: {company: frm.doc.company, account_type: ["in", ["Cash", "Bank"]], is_group: 0}})},
				], (v) => frappe.call({method: "kh_aph.factory_cash.xac_nhan_nhan", args: {name: frm.doc.name, ...v}, freeze: true})
					.then(() => frm.reload_doc()), __("Nhận tiền bàn giao"));
			});
		}
	},
});
