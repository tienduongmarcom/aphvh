// Nhận trả theo phiếu gốc: dữ liệu nhập gọn, controller native vẫn sở hữu kho/nợ/tiền.
frappe.provide("kh_aph.returns");
kh_aph.returns.open = async function(name) {
    const result = await frappe.call({method: "kh_aph.sales_return.preview", args: {delivery_note: name}, freeze: true});
    const source = result.message, rows = source.rows.filter(r => r.remaining_qty > 0);
    if (!rows.length) return frappe.msgprint("Đã nhận hoặc đã lập phiếu chờ nhận trả hết lượng giao.");
    const request_id = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
    const dialog = new frappe.ui.Dialog({title: "Nhận hàng trả lại", size: "extra-large", fields: [
        {fieldtype: "HTML", options: `<div class="alert alert-info">Phiếu gốc: ${frappe.utils.escape_html(source.name)} — ${frappe.utils.escape_html(source.company)}.<br>Nhập kg thực nhận và số bao thực nhận riêng; ví dụ trả 5kg trong bao 25kg không nhập thành 1 bao nguyên. Chưa nhận hàng thì chưa xác nhận nhập kho.</div>`},
        {fieldname: "condition", label: "Hàng nhận lại", fieldtype: "Select", options: ["Cách ly", "Bán lại được"], default: "Cách ly", reqd: 1},
        {fieldname: "settlement", label: "Xử lý tiền", fieldtype: "Select", options: ["Bù trừ công nợ", "Hoàn tiền", "Đổi hàng"], default: "Bù trừ công nợ", reqd: 1,
            description: "Phiếu hoàn/đổi được chuẩn bị nháp. Kế toán kiểm số đã trả, số còn nợ và xác nhận riêng; chưa chi tiền lúc lập phiếu này."},
        {fieldname: "reason", label: "Lý do trả", fieldtype: "Small Text", reqd: 1},
        {fieldname: "rows", label: "Hàng thực nhận trả", fieldtype: "Table", cannot_add_rows: true, cannot_delete_rows: true, in_place_edit: true,
            data: rows.map(r => ({...r, qty: 0, bags: 0})), fields: [
                {fieldname: "source_row", fieldtype: "Data", hidden: 1},
                {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", read_only: 1, in_list_view: 1, columns: 1},
                {fieldname: "item_name", label: "Tên hàng", fieldtype: "Data", read_only: 1, in_list_view: 1, columns: 3},
                {fieldname: "remaining_qty", label: "Còn được trả (kg)", fieldtype: "Float", read_only: 1, in_list_view: 1, columns: 2},
                {fieldname: "qty", label: "Nhận trả (kg)", fieldtype: "Float", in_list_view: 1, columns: 2},
                {fieldname: "bags", label: "Số bao thực nhận", fieldtype: "Int", in_list_view: 1, columns: 2},
            ]},
    ], primary_action_label: "Lập phiếu nhận trả", async primary_action(values) {
        const selections = values.rows.filter(r => Number(r.qty) > 0).map(r => ({source_row: r.source_row, qty: r.qty, bags: r.bags || 0}));
        if (!selections.length) return frappe.msgprint("Nhập lượng thực nhận trả cho ít nhất một dòng.");
        dialog.disable_primary_action();
        try {
            const made = await frappe.call({method: "kh_aph.sales_return.create_draft", args: {
                delivery_note: source.name, selections: JSON.stringify(selections), request_id,
                reason: values.reason, condition: values.condition, settlement: values.settlement}, freeze: true});
            dialog.hide();
            frappe.show_alert({message: "Đã lập phiếu nháp. Kiểm lượng, kho nhận và tiền trước khi xác nhận.", indicator: "blue"});
            frappe.set_route("Form", "Delivery Note", made.message.name);
        } finally {dialog.enable_primary_action();}
    }});
    dialog.show();
};
frappe.ui.form.on("Delivery Note", {refresh(frm) {
    if (!frappe.boot?.kh_aph?.sales_adjust || !frappe.boot?.kh_aph?.sales_p1 || frm.doc.docstatus !== 1 || frm.doc.is_return ||
        !frappe.model.can_create("Delivery Note")) return;
    frm.add_custom_button("Nhận hàng trả lại", () => kh_aph.returns.open(frm.doc.name), "Đổi / Trả");
}});
frappe.ui.form.on("Customer", {refresh(frm) {
    if (!frappe.boot?.kh_aph?.sales_adjust || !frappe.boot?.kh_aph?.sales_p1 || frm.is_new() ||
        !frappe.model.can_create("Delivery Note")) return;
    frm.add_custom_button("Nhận hàng trả lại", () => frappe.prompt({fieldname: "delivery_note", label: "Phiếu xuất gốc", fieldtype: "Link",
        options: "Delivery Note", reqd: 1, get_query: () => ({filters: {customer: frm.doc.name, docstatus: 1, is_return: 0}})},
        values => kh_aph.returns.open(values.delivery_note), "Chọn phiếu xuất cũ"), "Đổi / Trả / Giảm giá");
}});
frappe.ui.form.on("Customer", {refresh(frm) {
    if (!frappe.boot?.kh_aph?.sales_p1 || frm.is_new() || !frappe.model.can_create("Journal Entry")) return;
    frm.add_custom_button("Giảm giá đơn cũ", () => frappe.prompt([
        {fieldname: "sales_invoice", label: "Khoản phải thu của đơn cũ", fieldtype: "Link", options: "Sales Invoice", reqd: 1,
            get_query: () => ({filters: {customer: frm.doc.name, docstatus: 1, is_return: 0, outstanding_amount: [">", 0]}})},
        {fieldname: "so_tien", label: "Tổng tiền đề nghị giảm (gồm thuế nếu có)", fieldtype: "Currency", reqd: 1},
        {fieldname: "ly_do", label: "Lý do / thỏa thuận chất lượng", fieldtype: "Small Text", reqd: 1},
    ], async values => {
        const result = await frappe.call({method: "kh_aph.sales_p1.giam_gia_sau_giao", args: values, freeze: true});
        frappe.show_alert({message: "Đã mở đề nghị giảm nháp. Chưa ghi giảm công nợ; kiểm thông tin rồi xác nhận theo quyền.", indicator: "blue"});
        frappe.set_route("Form", "Journal Entry", result.message.but_toan);
    }, "Giảm giá khoản nợ cũ", "Lập đề nghị"), "Đổi / Trả / Giảm giá");
}});
