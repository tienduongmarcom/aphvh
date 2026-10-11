// Shared child handlers: kg remains the stock UOM; server validates every save.
frappe.provide("kh_aph.quantity");
if (!kh_aph.quantity.registered) {
    kh_aph.quantity.registered = true;
    const enabled = () => !!frappe.boot?.kh_aph?.quantity_valuation_mvp;
    const recalc = async (frm, cdt, cdn) => {
        if (!enabled() || frm.doc.docstatus !== 0) return;
        const row = locals[cdt]?.[cdn];
        if (!row || !Number(row.kh_aph_kg_per_bag) || !Number(row.kh_aph_bags)) return;
        const bags = Number(row.kh_aph_bags), weight = Number(row.kh_aph_kg_per_bag);
        if (!Number.isInteger(bags) || !Number.isFinite(weight) || weight <= 0) {
            frappe.msgprint("Số bao cần là số nguyên; kg/bao phải lớn hơn 0.");
            return;
        }
        await frappe.model.set_value(cdt, cdn, "qty", bags * weight);
        if (["Sales Order", "APH Shared Sales Order"].includes(frm.doctype)) {
            await frappe.model.set_value(cdt, cdn, "kh_aph_bag_rate", Number(row.rate || 0) * weight);
        }
    };
    const item = async (frm, cdt, cdn) => {
        if (!enabled() || frm.doc.docstatus !== 0) return;
        const row = locals[cdt]?.[cdn];
        if (!row?.item_code) return;
        // Preserve snapshots of mapped rows; the server remains authoritative.
        if (row.so_detail || row.sales_order_item || row.dn_detail || row.purchase_receipt_item) return;
        const selected = row.item_code;
        const response = await frappe.db.get_value("Item", selected, "kh_aph_kg_per_bag");
        if (locals[cdt]?.[cdn]?.item_code !== selected) return;
        await frappe.model.set_value(cdt, cdn, "kh_aph_kg_per_bag", Number(response.message?.kh_aph_kg_per_bag || 0));
        await recalc(frm, cdt, cdn);
    };
    for (const dt of ["Stock Entry Detail", "Purchase Receipt Item", "Purchase Invoice Item", "Sales Order Item", "Delivery Note Item", "Sales Invoice Item", "APH Shared Sales Order Item", "APH Pending Receipt Item"]) {
        frappe.ui.form.on(dt, {kh_aph_bags: recalc, kh_aph_kg_per_bag: recalc, rate: recalc, item_code: item});
    }
}

// Preview shared-order row/total amounts; the server recalculates on save.
frappe.ui.form.on("APH Shared Sales Order Item", {
    async qty(frm, cdt, cdn) {
        if (!frappe.boot?.kh_aph?.quantity_valuation_mvp || frm.doc.docstatus !== 0) return;
        const row = locals[cdt]?.[cdn];
        if (row) await frappe.model.set_value(cdt, cdn, "amount", Number(row.qty || 0) * Number(row.rate || 0));
        await frm.set_value("net_total", (frm.doc.items || []).reduce((sum, r) => sum + Number(r.qty || 0) * Number(r.rate || 0), 0));
    },
    async rate(frm, cdt, cdn) {
        if (!frappe.boot?.kh_aph?.quantity_valuation_mvp || frm.doc.docstatus !== 0) return;
        const row = locals[cdt]?.[cdn];
        if (row) await frappe.model.set_value(cdt, cdn, "amount", Number(row.qty || 0) * Number(row.rate || 0));
        await frm.set_value("net_total", (frm.doc.items || []).reduce((sum, r) => sum + Number(r.qty || 0) * Number(r.rate || 0), 0));
    },
    async items_remove(frm) {
        if (frappe.boot?.kh_aph?.quantity_valuation_mvp && frm.doc.docstatus === 0)
            await frm.set_value("net_total", (frm.doc.items || []).reduce((sum, r) => sum + Number(r.qty || 0) * Number(r.rate || 0), 0));
    }
});
