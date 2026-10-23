// Nhận trả theo phiếu gốc: dữ liệu nhập gọn, controller native vẫn sở hữu kho/nợ/tiền.
frappe.provide("kh_aph.returns");
if (!kh_aph.returns.registered) {
kh_aph.returns.registered = true;
frappe.ui.form.on("Delivery Note", {
    refresh(frm) {
        if (!frappe.boot?.kh_aph?.sales_p1 || !frappe.boot?.kh_aph?.sales_adjust || frm.doc.docstatus !== 1 ||
            !frm.doc.is_return || !frm.doc.kh_aph_ma_nhan_tra || frm.doc.kh_aph_xu_ly_tien !== "Hoàn tiền" ||
            !frm.doc.kh_aph_chung_tu_xu_ly) return;
        frm.add_custom_button("Mở phiếu hoàn tiền", async () => {
            const result = await frappe.call({method: "kh_aph.sales_return.money_document",
                args: {delivery_note: frm.doc.name}, freeze: true});
            frappe.set_route("Form", result.message.doctype, result.message.name);
        }, "Đổi / Trả");
    },
    on_submit(frm) {
        if (frappe.boot?.kh_aph?.sales_p1 && frm.doc.is_return && frm.doc.kh_aph_ma_nhan_tra &&
            frm.doc.kh_aph_xu_ly_tien === "Hoàn tiền") frm.reload_doc();
    },
});
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
            data: rows.flatMap(r => r.parts ? r.parts.filter(p => Number(p.remaining)>0).map(p => ({...r,
                part_key:p.key, has_parts:1, quality_label:`${p.key ? "Đã giảm" : "Chưa giảm"}: ${new Intl.NumberFormat("vi-VN",{maximumFractionDigits:2}).format(Number(p.net_rate))} đ/kg${p.key ? " · "+p.key : ""}`,
                remaining_qty:Number(p.remaining), qty:0, bags:0})) : [{...r,qty:0,bags:0}]), fields: [
                {fieldname: "source_row", fieldtype: "Data", hidden: 1},
                {fieldname: "part_key", fieldtype: "Data", hidden: 1},
                {fieldname: "has_parts", fieldtype: "Check", hidden: 1},
                {fieldname: "quality_label", label: "Phần hàng", fieldtype: "Data", read_only: 1, in_list_view: 1, columns: 2},
                {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", read_only: 1, in_list_view: 1, columns: 1},
                {fieldname: "item_name", label: "Tên hàng", fieldtype: "Data", read_only: 1, in_list_view: 1, columns: 2},
                {fieldname: "remaining_qty", label: "Còn được trả (kg)", fieldtype: "Float", read_only: 1, in_list_view: 1, columns: 2},
                {fieldname: "qty", label: "Nhận trả (kg)", fieldtype: "Float", in_list_view: 1, columns: 2},
                {fieldname: "bags", label: "Số bao thực nhận", fieldtype: "Int", in_list_view: 1, columns: 1},
            ]},
    ], primary_action_label: "Lập phiếu nhận trả", async primary_action(values) {
        const groups = new Map();
        for (const r of values.rows.filter(r => Number(r.qty)>0)) {
            if (!groups.has(r.source_row)) groups.set(r.source_row,{source_row:r.source_row,qty:0,bags:0,...(r.has_parts ? {parts:[]} : {})});
            const group=groups.get(r.source_row);
            group.qty+=Number(r.qty); group.bags+=Number(r.bags||0);
            if (group.parts) group.parts.push({key:r.part_key||"",qty:r.qty});
        }
        const selections = [...groups.values()];
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
    ], values => kh_aph.quality.open(values.sales_invoice), "Chọn khoản nợ cũ", "Tiếp tục"), "Đổi / Trả / Giảm giá");
}});

frappe.provide("kh_aph.quality");
kh_aph.quality.open = async function(sales_invoice, journal_entry=null) {
    const response=await frappe.call({method:"kh_aph.sales_p1.preview_quality",args:{sales_invoice,journal_entry},freeze:true});
    const dialog=new frappe.ui.Dialog({title:journal_entry ? "Phân loại khoản giảm đã ghi" : "Giảm giá theo phần hàng",size:"extra-large",fields:[
        {fieldtype:"HTML",options:journal_entry ? `<p>Bút toán ${frappe.utils.escape_html(journal_entry)} đã ghi giảm ${frappe.format(response.message.existing_amount,{fieldtype:"Currency"})}. Chỉ bổ sung phân loại lượng, không ghi giảm thêm. Chi tiết phải khớp tiền hàng và thuế đã ghi.</p>` : "<p>Chỉ nhập lượng thuộc thỏa thuận giảm. Phần hàng còn lại giữ nguyên giá; tiền giảm gồm thuế nếu có.</p>"},
        {fieldname:"reason",label:"Lý do / thỏa thuận chất lượng",fieldtype:"Small Text",reqd:1},
        {fieldname:"rows",label:"Phần hàng được giảm",fieldtype:"Table",cannot_add_rows:true,cannot_delete_rows:true,in_place_edit:true,
            data:response.message.rows.filter(r=>r.remaining_qty>0).map(r=>({...r,qty:0,amount:0})),fields:[
                {fieldname:"invoice_row",fieldtype:"Data",hidden:1},
                {fieldname:"item_code",label:"Mã hàng",fieldtype:"Data",read_only:1,in_list_view:1,columns:1},
                {fieldname:"item_name",label:"Tên hàng",fieldtype:"Data",read_only:1,in_list_view:1,columns:3},
                {fieldname:"remaining_qty",label:"Còn chưa giảm (kg)",fieldtype:"Float",read_only:1,in_list_view:1,columns:2},
                {fieldname:"qty",label:"Lượng được giảm (kg)",fieldtype:"Float",in_list_view:1,columns:2},
                {fieldname:"amount",label:"Tiền giảm phần này",fieldtype:"Currency",in_list_view:1,columns:2},
            ]},
    ],primary_action_label:journal_entry ? "Lưu phân loại" : "Lập đề nghị giảm",async primary_action(values){
        if(values.rows.some(r=>!Number.isFinite(Number(r.qty||0)) || !Number.isFinite(Number(r.amount||0)) ||
            Number(r.qty||0)<0 || Number(r.amount||0)<0 || (!Number(r.qty||0) && Number(r.amount||0)>0) ||
            (Number(r.qty||0)>0 && Number(r.amount||0)<=0))) return frappe.msgprint("Mỗi phần cần lượng và tiền giảm dương, không nhập thiếu một trong hai.");
        const selections=values.rows.filter(r=>Number(r.qty)>0).map(r=>({invoice_row:r.invoice_row,qty:r.qty,amount:r.amount}));
        if(!selections.length) return frappe.msgprint("Nhập lượng và tiền giảm của ít nhất một phần hàng.");
        dialog.disable_primary_action();
        try {
            const made=await frappe.call({method:journal_entry ? "kh_aph.sales_p1.classify_quality" : "kh_aph.sales_p1.giam_gia_sau_giao",
                args:journal_entry ? {journal_entry,selections:JSON.stringify(selections),reason:values.reason,modified:response.message.modified} :
                    {sales_invoice,so_tien:selections.reduce((sum,r)=>sum+Number(r.amount),0),ly_do:values.reason,selections:JSON.stringify(selections)},freeze:true});
            dialog.hide();
            if(window.cur_frm?.doctype==="Journal Entry" && cur_frm.doc.name===made.message.but_toan) await cur_frm.reload_doc();
            else frappe.set_route("Form","Journal Entry",made.message.but_toan);
        } finally {dialog.enable_primary_action();}
    }});
    dialog.show();
};


frappe.ui.form.on("Delivery Note", {refresh(frm) {
    if (!frappe.boot?.kh_aph?.sales_adjust || !frappe.boot?.kh_aph?.sales_p1 || frm.doc.docstatus !== 1 ||
        !frm.doc.is_return || !frm.doc.kh_aph_ma_nhan_tra || frm.doc.kh_aph_xu_ly_tien !== "Đổi hàng") return;
    frm.add_custom_button("Lập đơn hàng thay", async () => {
        const result = await frappe.call({method: "kh_aph.sales_exchange.prepare", args: {return_note: frm.doc.name}, freeze: true});
        if (result.message.existing) return frappe.set_route("Form", "APH Shared Sales Order", result.message.existing);
        frappe.show_alert({message: "Chọn mã, lượng và giá hàng thay. Đơn nháp chưa xuất kho hoặc tăng nợ.", indicator: "blue"});
        frappe.new_doc("APH Shared Sales Order", result.message.defaults);
    }, "Đổi / Trả");
}});

frappe.ui.form.on("Journal Entry",{refresh(frm){
    if(!frappe.boot?.kh_aph?.sales_p1 || frm.doc.docstatus!==1 || !frm.doc.kh_aph_giam_gia_hd ||
        frm.doc.kh_aph_phan_bo_giam || !frappe.model.can_write("Journal Entry")) return;
    frm.add_custom_button("Bổ sung phần hàng đã giảm",()=>kh_aph.quality.open(frm.doc.kh_aph_giam_gia_hd,frm.doc.name));
}});

} // Đăng ký một lần khi đi qua nhiều loại chứng từ trong cùng phiên Desk.
