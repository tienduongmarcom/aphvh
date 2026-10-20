// NM02–04: ghi sản xuất / đóng gói thành phẩm / đổi bao một lần theo lượng (không hiện giá).
frappe.provide("kh_aph.production");
if (!kh_aph.production.open) {
    kh_aph.production.open = function(company) {
        if (!company) return frappe.msgprint("Chọn đơn vị trước.");
        frappe.call({method: "kh_aph.factory_production.context", args: {company}, callback(r) {
            const ctx = r.message;
            if (!ctx) return;
            const request_id = frappe.utils.get_random(32);
            const dialog = new frappe.ui.Dialog({title: "Ghi sản xuất / đóng gói", size: "large", primary_action_label: "Xác nhận ghi kho",
                fields: [
                    {fieldname: "kind", label: "Việc cần ghi", fieldtype: "Select", reqd: 1, default: "san_xuat",
                        options: [{value: "san_xuat", label: "Sản xuất (lấy từ dở dang dây chuyền)"},
                                  {value: "dong_goi", label: "Đóng gói thành phẩm"}, {value: "doi_bao", label: "Đổi bao, đóng gói lại"}]},
                    {fieldname: "posting_date", label: "Ngày", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
                    {fieldname: "line", label: "Dây chuyền (kho dở dang)", fieldtype: "Select", depends_on: "eval:doc.kind=='san_xuat'",
                        options: [""].concat(ctx.lines.map(l => ({value: l.warehouse, label: (l.line ? l.line + " · " : "") + l.warehouse}))),
                        change() { load_wip(); }},
                    {fieldname: "workshop", label: "Xưởng", fieldtype: "Select", depends_on: "eval:doc.kind=='san_xuat'",
                        options: [""].concat(ctx.workshops)},
                    {fieldname: "inputs", label: "Đầu vào thực dùng (kg)", fieldtype: "Table", fields: [
                        {fieldname: "item_code", label: "Mã hàng", fieldtype: "Link", options: "Item", in_list_view: 1, reqd: 1},
                        {fieldname: "warehouse", label: "Lấy từ kho", fieldtype: "Link", options: "Warehouse", in_list_view: 1, reqd: 1,
                            get_query: () => ({filters: {company, is_group: 0, disabled: 0}})},
                        {fieldname: "available", label: "Đang có", fieldtype: "Float", read_only: 1, in_list_view: 1},
                        {fieldname: "qty", label: "Thực dùng", fieldtype: "Float", in_list_view: 1}]},
                    {fieldname: "outputs", label: "Đầu ra cân thực tế (kg)", fieldtype: "Table", fields: [
                        {fieldname: "item_code", label: "Mã hàng", fieldtype: "Link", options: "Item", in_list_view: 1, reqd: 1},
                        {fieldname: "warehouse", label: "Vào kho", fieldtype: "Link", options: "Warehouse", in_list_view: 1, reqd: 1,
                            get_query: () => ({filters: {company, is_group: 0, disabled: 0}})},
                        {fieldname: "qty", label: "Kg / lượng", fieldtype: "Float", in_list_view: 1, reqd: 1}]},
                    {fieldname: "note", label: "Ghi chú / lý do hao hụt hoặc lệch kg", fieldtype: "Small Text"},
                    {fieldname: "confirm_difference", label: "Xác nhận lệch kg là đúng thực tế (đóng gói/đổi bao)", fieldtype: "Check",
                        depends_on: "eval:doc.kind!='san_xuat'"},
                    {fieldtype: "HTML", options: "<p class='text-muted'>Sản xuất: chỉ ghi phần nguyên liệu đã dùng, phần còn lại vẫn ở dở dang. Đầu vào nhiều hơn đầu ra cần ghi lý do hao hụt. Đóng gói/đổi bao giữ nguyên kg.</p>"}
                ],
                primary_action(v) {
                    const ins = (v.inputs || []).filter(x => Number(x.qty) > 0).map(x => ({item_code: x.item_code, warehouse: x.warehouse, qty: x.qty}));
                    const outs = (v.outputs || []).filter(x => Number(x.qty) > 0).map(x => ({item_code: x.item_code, warehouse: x.warehouse, qty: x.qty}));
                    if (!ins.length || !outs.length) return frappe.msgprint("Nhập ít nhất một dòng đầu vào và một dòng đầu ra.");
                    const kg_in = ins.reduce((s, x) => s + Number(x.qty), 0), kg_out = outs.reduce((s, x) => s + Number(x.qty), 0);
                    const msg = `Ghi ${ins.length} dòng vào (${format_number(kg_in)}) và ${outs.length} dòng ra (${format_number(kg_out)}). Thao tác này ghi kho. Bấm lại trong cùng cửa sổ sẽ mở phiếu đã tạo.`;
                    frappe.confirm(msg, () => {
                        dialog.get_primary_btn().prop("disabled", true);
                        frappe.call({method: "kh_aph.factory_production.record", freeze: true, args: {kind: v.kind, company, request_id,
                            posting_date: v.posting_date, inputs: JSON.stringify(ins), outputs: JSON.stringify(outs),
                            workshop: v.workshop || "", note: v.note || "", confirm_difference: v.confirm_difference ? 1 : 0},
                            callback(res) {
                                if (!res.message?.name) return;
                                dialog.hide();
                                frappe.show_alert({message: "Đã ghi: " + res.message.name, indicator: "green"});
                                frappe.set_route("Form", "Stock Entry", res.message.name);
                            }}).always(() => dialog.get_primary_btn().prop("disabled", false));
                    });
                }});
            function load_wip() {
                const line = dialog.get_value("line");
                if (!line) return;
                frappe.call({method: "kh_aph.factory_production.wip", args: {warehouse: line}, callback(w) {
                    dialog.fields_dict.inputs.df.data = (w.message || []).map(x => ({item_code: x.item_code, warehouse: line, available: x.qty, qty: 0}));
                    dialog.fields_dict.inputs.grid.refresh();
                }});
            }
            dialog.show();
        }});
    };
}
