frappe.ui.form.on("APH Pending Receipt", {
    refresh(frm) {
        if (!frappe.boot?.kh_aph?.quantity_valuation_mvp || frm.doc.docstatus !== 1
            || frm.doc.purchase_receipt || frm.doc.status !== "Chờ định giá") return;
        const admin = frappe.session.user === "Administrator";
        const roles = frappe.user_roles || [];
        if (!admin && (!roles.includes("Accounts Manager") || roles.includes("APH Không xem giá vốn"))) return;
        frm.add_custom_button("Chốt giá nhập", () => {
            if (frm.is_dirty()) return frappe.msgprint("Lưu phiếu trước khi chốt giá.");
            const dialog = new frappe.ui.Dialog({
                title: "Chốt giá nhập theo kg", primary_action_label: "Chốt giá và nhập kho",
                fields: [
                    {fieldname: "rates", label: "Giá từng dòng", fieldtype: "Table", cannot_add_rows: true, cannot_delete_rows: true,
                     data: frm.doc.items.map(r => ({source_row: r.name, item_code: r.item_code, qty: r.qty, rate: 0})),
                     fields: [
                        {fieldname: "source_row", fieldtype: "Data", hidden: 1, read_only: 1},
                        {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", read_only: 1, in_list_view: 1},
                        {fieldname: "qty", label: "Số kg", fieldtype: "Float", read_only: 1, in_list_view: 1},
                        {fieldname: "rate", label: "Giá/kg (VND)", fieldtype: "Currency", reqd: 1, in_list_view: 1}
                     ]},
                    {fieldname: "reason", label: "Lý do chốt giá", fieldtype: "Small Text", reqd: 1}
                ],
                async primary_action(values) {
                    const rates = {};
                    for (const row of values.rates || []) {
                        if (!Number.isFinite(Number(row.rate)) || Number(row.rate) <= 0)
                            return frappe.msgprint("Mỗi dòng cần giá/kg lớn hơn 0.");
                        rates[row.source_row] = Number(row.rate);
                    }
                    dialog.get_primary_btn().prop("disabled", true);
                    try {
                        await frappe.call({method: "kh_aph.pending_valuation.finalize", args: {
                            name: frm.doc.name, rates: JSON.stringify(rates), reason: values.reason
                        }, freeze: true, freeze_message: "Đang chốt giá và nhập kho…"});
                        dialog.hide();
                        await frm.reload_doc();
                    } finally {dialog.get_primary_btn().prop("disabled", false);}
                }
            });
            dialog.show();
        });
    }
});
