// Một bộ giấy từ chứng từ đã ghi; không tự tạo khoản thu hoặc ghi kho.
frappe.provide("kh_aph.statement");
kh_aph.statement.open = async function(frm) {
    const customer = frm.doctype === "Customer" ? frm.doc.name :
        (frm.doctype === "Payment Entry" ? frm.doc.party : frm.doc.customer);
    const companies = await frappe.db.get_list("Company", {fields: ["name"], filters: {default_currency: "VND"}, limit: 0});
    const initial = frm.doctype === "Customer" ? [] : [{voucher_type: frm.doctype, voucher: frm.doc.name}];
    const request_id = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
    const dialog = new frappe.ui.Dialog({title: "Đối soát & In bộ giấy", size: "large", fields: [
        {fieldname: "customer", label: "Khách hàng", fieldtype: "Link", options: "Customer", default: customer, read_only: 1},
        {fieldname: "companies", label: "Phạm vi đơn vị", fieldtype: "MultiSelectPills", options: companies.map(c => c.name),
            default: companies.map(c => c.name), reqd: 1},
        {fieldname: "sources", label: "Chứng từ đã ghi của lượt này", fieldtype: "Table", in_place_edit: true, data: initial,
            fields: [
                {fieldname: "voucher_type", label: "Loại chứng từ", fieldtype: "Link", options: "DocType", reqd: 1,
                    in_list_view: 1, columns: 4, get_query: () => ({filters: {name: ["in", ["Delivery Note", "Sales Invoice", "Payment Entry", "Journal Entry", "APH Funds Receipt", "APH Funds Action"]]}})},
                {fieldname: "voucher", label: "Số chứng từ", fieldtype: "Dynamic Link", options: "voucher_type", reqd: 1, in_list_view: 1, columns: 6},
            ]},
        {fieldname: "supersedes", label: "Bổ sung cho biên bản trước (nếu có)", fieldtype: "Link", options: "Bien ban doi soat no",
            get_query: () => ({filters: {customer}})},
        {fieldtype: "HTML", options: "<p>Chọn đúng phiếu giao, thu/chi hoặc giảm nợ của lượt này. Bộ giấy lưu số tại mốc lập; in lại giữ bản đã cấp. Không tự cấn tiền giữa các đơn vị.</p>"},
    ], primary_action_label: "Lập & mở bộ giấy", async primary_action(values) {
        if (!values.sources?.length) return frappe.msgprint("Chọn chứng từ của lượt cần ký.");
        dialog.disable_primary_action();
        const preview = window.open("about:blank", "_blank");
        try {
            const result = await frappe.call({method: "kh_aph.debt_statement.create", args: {
                customer, companies: JSON.stringify(values.companies),
                vouchers: JSON.stringify(values.sources.map(r => ({doctype: r.voucher_type, name: r.voucher}))),
                request_id, supersedes: values.supersedes || null}, freeze: true});
            if (preview) preview.location.href = result.message.file_url;
            dialog.hide();
            frappe.set_route("Form", "Bien ban doi soat no", result.message.name);
        } catch (error) {
            if (preview) preview.close();
            throw error;
        } finally {dialog.enable_primary_action();}
    }});
    dialog.show();
    await dialog.set_value("companies", companies.map(c => c.name));
};

for (const doctype of ["Customer", "Delivery Note", "Payment Entry", "APH Funds Receipt", "APH Funds Action"]) {
    frappe.ui.form.on(doctype, {refresh(frm) {
        if (!frappe.boot?.kh_aph?.quan_tri || frm.is_new() ||
            (frappe.session.user !== "Administrator" && (frappe.boot?.kh_aph?.price_restricted ||
                (frappe.user_roles || []).includes("APH Không xem giá vốn"))) ||
            (doctype !== "Customer" && frm.doc.docstatus !== 1) ||
            (doctype === "Payment Entry" && frm.doc.party_type !== "Customer") ||
            (["APH Funds Receipt", "APH Funds Action"].includes(doctype) && !frm.doc.customer) ||
            !frappe.model.can_create("Bien ban doi soat no")) return;
        frm.add_custom_button("Đối soát & In bộ giấy", () => kh_aph.statement.open(frm));
        const customer = doctype === "Customer" ? frm.doc.name :
            (doctype === "Payment Entry" ? frm.doc.party : frm.doc.customer);
        frm.add_custom_button("Biên bản đã lưu", () => frappe.set_route("List", "Bien ban doi soat no", {customer}));
    }});
}

frappe.ui.form.on("Bien ban doi soat no", {refresh(frm) {
    if (frm.doc.bundle_file) {
        const open = () => window.open(frm.doc.bundle_file, "_blank", "noopener");
        frm.add_custom_button("Mở bộ giấy đã cấp", open);
        frm.page.set_primary_action("Mở bộ giấy đã cấp", open);
    }
    if (frm.doc.signed_file) frm.add_custom_button("Mở bản đã ký", () => window.open(frm.doc.signed_file, "_blank", "noopener"));
    if (frm.is_new()) {
        frm.page.set_primary_action("Chọn khách hàng", () => frappe.prompt({fieldname: "customer", label: "Khách hàng",
            fieldtype: "Link", options: "Customer", reqd: 1}, values =>
                kh_aph.statement.open({doctype: "Customer", doc: {name: values.customer}}),
            "Lập biên bản đối soát", "Tiếp tục"));
        return;
    }
    frm.add_custom_button("Lưu bản ký / giấy gốc", () => {
        const dialog = new frappe.ui.Dialog({title: "Lưu bản ký công nợ", fields: [
            {fieldname: "signer", label: "Người ký công nợ", fieldtype: "Data", reqd: 1, default: frm.doc.signer},
            {fieldname: "authority", label: "Tư cách ký nợ", fieldtype: "Select", options: "\nKhách hàng\nĐược ủy quyền ký nợ", reqd: 1, default: frm.doc.signature_authority},
            {fieldname: "authorization", label: "Căn cứ khách giao quyền ký nợ riêng", fieldtype: "Small Text", default: frm.doc.authorization,
                mandatory_depends_on: 'eval:doc.authority=="Được ủy quyền ký nợ"'},
            {fieldname: "file", label: "Tệp đã đính kèm biên bản (nếu có)", fieldtype: "Link", options: "File",
                get_query: () => ({filters: {attached_to_doctype: frm.doctype, attached_to_name: frm.doc.name, is_private: 1}})},
            {fieldname: "location", label: "Vị trí giữ giấy gốc", fieldtype: "Data", default: frm.doc.original_location,
                description: "Có thể lưu giấy gốc trước rồi bổ sung ảnh sau."},
        ], primary_action_label: "Lưu bản ký", async primary_action(values) {
            dialog.disable_primary_action();
            try {
                let file_url = null;
                if (values.file) file_url = (await frappe.db.get_value("File", values.file, "file_url")).message.file_url;
                await frappe.call({method: "kh_aph.debt_statement.record_signature", args: {name: frm.doc.name,
                    modified: frm.doc.modified, signer: values.signer, authority: values.authority,
                    authorization: values.authorization || "", file_url, location: values.location || ""}, freeze: true});
                dialog.hide();
                await frm.reload_doc();
            } finally {dialog.enable_primary_action();}
        }});
        dialog.show();
    });
}});
