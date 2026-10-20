// 0.4.1 — mở bảng tổng hợp bán hàng của khách trên cả APH, VH, HKD Minh Khang (chỉ xem, in cho khách).
frappe.ui.form.on("Customer", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button("Tổng hợp bán hàng theo khách", () => {
			frappe.set_route("query-report", "Tong hop ban hang theo khach", { customer: frm.doc.name });
		});
	},
});
