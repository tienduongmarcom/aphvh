frappe.ui.form.on("APH Funds Receipt", {
    refresh(frm) {
        if (!frappe.boot?.kh_aph?.funds_workflow || frm.doc.docstatus !== 1 || frm.doc.customer) return;
        if (frappe.session.user !== "Administrator" && !frappe.user_roles.includes("Accounts Manager")) return;
        frm.add_custom_button("Xác minh khách", () => frappe.prompt([
            {fieldname:"customer",label:"Khách đã xác minh",fieldtype:"Link",options:"Customer",reqd:1},
            {fieldname:"reason",label:"Căn cứ xác minh",fieldtype:"Small Text",reqd:1}
        ], async values => {
            await frappe.call({method:"kh_aph.funds.identify_receipt",args:{name:frm.doc.name,...values},freeze:true});
            await frm.reload_doc();
        }, "Xác minh tiền thực nhận", "Xác minh"));
    }
});
