frappe.query_reports["Ton kho so luong"] = {
	onload(report) {
        if (!frappe.boot?.kh_aph?.factory_receiving) return;
        if (frappe.session.user !== "Administrator" && !(frappe.user_roles || []).some(r =>
            ["Kế toán nhà máy", "Stock User", "Stock Manager", "Accounts Manager", "System Manager"].includes(r))) return;
        report.page.add_inner_button("Nhận hàng nhà máy", () => {
            frappe.require("form.bundle.js", () =>
                frappe.require("/assets/kh_aph/js/factory_receiving.js", () =>
                    kh_aph.receiving.pick(report.get_filter_value("company"))));
        });
    },
	filters: [
		{
			fieldname: "company",
			label: __("Công ty"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "warehouse",
			label: __("Kho"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: () => ({ filters: { company: frappe.query_report.get_filter_value("company") } }),
		},
		{ fieldname: "item_group", label: __("Nhóm hàng"), fieldtype: "Link", options: "Item Group" },
		{ fieldname: "item_code", label: __("Mã hàng"), fieldtype: "Link", options: "Item" },
		{ fieldname: "show_zero", label: __("Hiện cả mã tồn 0"), fieldtype: "Check" },
	],
};
