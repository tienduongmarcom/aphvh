// NM01c: nhận chuyến chuyển đến theo lượng thực nhận; dùng chung cho phiếu chuyển và báo cáo số lượng.
frappe.provide("kh_aph.transfer_in");
if (!kh_aph.transfer_in.open) {
    kh_aph.transfer_in.open = function(stock_entry) {
        frappe.call({method: "kh_aph.factory_transfer.preview", args: {stock_entry}, freeze: true, callback(r) {
            const source = r.message;
            if (!source || source.stock_entry !== stock_entry) return;
            const request_id = frappe.utils.get_random(32);
            const dialog = new frappe.ui.Dialog({title: "Nhận chuyến chuyển đến", primary_action_label: "Xác nhận nhận vào kho",
                fields: [
                    {fieldtype: "HTML", options: `<p>${frappe.utils.escape_html(source.company)} · chuyển đi ngày ${frappe.utils.escape_html(source.sent_date)}</p><p>Nhập đúng kg và số bao thực nhận. Lượng thiếu vẫn nằm ở kho đang vận chuyển chờ đối soát; không nhận vượt lượng đã chuyển.</p>`},
                    {fieldname: "received_date", label: "Ngày nhận thực tế", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
                    {fieldname: "receiver", label: "Người thực nhận/ký tại kho", fieldtype: "Data", reqd: 1},
                    {fieldname: "note", label: "Ghi chú (thiếu, hỏng, xe…)", fieldtype: "Small Text"},
                    {fieldname: "items", label: "Kg và số bao thực nhận", fieldtype: "Table", cannot_add_rows: true, cannot_delete_rows: true,
                        data: source.items, fields: [
                            {fieldname: "source_row", fieldtype: "Data", hidden: 1, read_only: 1},
                            {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", read_only: 1, in_list_view: 1},
                            {fieldname: "warehouse", label: "Kho nhận", fieldtype: "Link", options: "Warehouse", in_list_view: 1,
                                get_query: () => ({filters: {company: source.company, is_group: 0, disabled: 0, warehouse_type: ["!=", "Transit"]}})},
                            {fieldname: "remaining", label: "Còn trên đường (kg)", fieldtype: "Float", read_only: 1, in_list_view: 1},
                            {fieldname: "qty", label: "Kg thực nhận", fieldtype: "Float", in_list_view: 1},
                            {fieldname: "bags", label: "Số bao thực nhận", fieldtype: "Int", in_list_view: 1},
                            {fieldname: "kg_per_bag", label: "Kg/bao", fieldtype: "Float", read_only: 1}
                        ]}
                ],
                primary_action(values) {
                    const rows = (values.items || []).filter(x => Number(x.qty) > 0).map(x => ({source_row: x.source_row,
                        warehouse: x.warehouse || "", qty: x.qty, bags: x.bags || 0}));
                    if (!rows.length) return frappe.msgprint("Nhập kg thực nhận ít nhất một dòng.");
                    if (rows.some(x => !x.warehouse)) return frappe.msgprint("Chọn kho nhận cho các dòng có kg thực nhận.");
                    frappe.confirm("Xác nhận lượng thực nhận? Thao tác này ghi nhập kho. Bấm lại trong cùng cửa sổ sẽ mở phiếu đã tạo.", () => {
                        dialog.get_primary_btn().prop("disabled", true);
                        frappe.call({method: "kh_aph.factory_transfer.receive", args: {stock_entry: source.stock_entry, request_id,
                            rows: JSON.stringify(rows), received_date: values.received_date, receiver: values.receiver, note: values.note || ""},
                            freeze: true, callback(res) {
                                if (!res.message?.name) return;
                                dialog.hide();
                                frappe.show_alert({message: "Đã nhận vào kho: " + res.message.name, indicator: "green"});
                                frappe.set_route("Form", "Stock Entry", res.message.name);
                            }}).always(() => dialog.get_primary_btn().prop("disabled", false));
                    });
                }});
            dialog.show();
        }});
    };
    kh_aph.transfer_in.send = function(company, suggestion = null) {
        if (!company) return frappe.msgprint("Chọn đơn vị trước.");
        const request_id = frappe.utils.get_random(32);
        const dialog = new frappe.ui.Dialog({title: "Chuyển hàng đi (cùng đơn vị)", primary_action_label: "Chuẩn bị phiếu & In",
            fields: [
                {fieldname: "sent_date", label: "Ngày chuyển", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
                {fieldtype: "HTML", options: suggestion ? `<p>Gom cho đơn ${frappe.utils.escape_html(suggestion.shared_order)}. Lượng gợi ý là phần chưa giao/chưa lập phiếu xuất, không phải lượng thiếu tồn hoặc giữ chỗ. Chọn kho thực lấy và kiểm lại lượng cần chuyển. Nếu đổi nơi giao khách, đổi nguồn phần chưa giao trên đơn trước.</p>` : ""},
                {fieldname: "destination", label: "Kho nhận dự kiến", fieldtype: "Link", options: "Warehouse", reqd: 1, default: suggestion?.destination, read_only: !!suggestion,
                    get_query: () => ({query: "kh_aph.factory_transfer.destination_query", filters: {company}})},
                {fieldname: "carrier", label: "Người / xe chở", fieldtype: "Data", reqd: 1},
                {fieldname: "note", label: "Ghi chú (chuyển về kho nào…)", fieldtype: "Small Text", default: suggestion ? "Gom cho đơn " + suggestion.shared_order : ""},
                {fieldname: "items", label: "Hàng chuyển", fieldtype: "Table", data: suggestion?.items || [], cannot_add_rows: !!suggestion, fields: [
                    {fieldname: "item_code", label: "Mã hàng", fieldtype: "Link", options: "Item", reqd: 1, in_list_view: 1, read_only: !!suggestion},
                    {fieldname: "item_name", label: "Tên hàng", fieldtype: "Data", read_only: 1, in_list_view: 1,
                        fetch_from: "item_code.item_name"},
                    {fieldname: "warehouse", label: "Từ kho", fieldtype: "Link", options: "Warehouse", reqd: 1, in_list_view: 1,
                        get_query: () => ({filters: {company, is_group: 0, disabled: 0, warehouse_type: ["!=", "Transit"]}})},
                    {fieldname: "qty", label: "Kg", fieldtype: "Float", reqd: 1, in_list_view: 1},
                    {fieldname: "bags", label: "Số bao", fieldtype: "Int", in_list_view: 1}]}
            ],
            primary_action(v) {
                const rows = (v.items || []).filter(x => Number(x.qty) > 0).map(x => ({item_code: x.item_code, warehouse: x.warehouse, qty: x.qty, bags: x.bags || 0}));
                if (!rows.length) return frappe.msgprint("Nhập ít nhất một dòng hàng chuyển.");
                const printWindow = window.open("", "_blank");
                dialog.get_primary_btn().prop("disabled", true);
                    frappe.call({method: "kh_aph.factory_transfer.send", freeze: true, args: {company, request_id, rows: JSON.stringify(rows),
                        sent_date: v.sent_date, carrier: v.carrier, note: v.note || "", prepare_only: 1, destination: v.destination}, callback(res) {
                            if (!res.message?.name) { printWindow?.close(); return; }
                            const url = `/printview?doctype=Stock%20Entry&name=${encodeURIComponent(res.message.name)}&format=${encodeURIComponent("Phiếu kho")}&no_letterhead=1`;
                            if (printWindow) printWindow.location = url;
                            dialog.hide(); frappe.set_route("Form", "Stock Entry", res.message.name);
                            frappe.show_alert({message: "Đã chuẩn bị phiếu. Kiểm lượng thực giao rồi xác nhận xuất trên phiếu.", indicator: "blue"});
                        }}).fail(() => printWindow?.close()).always(() => dialog.get_primary_btn().prop("disabled", false));
            }});
        dialog.show();
    };
    kh_aph.transfer_in.pick = function(company) {
        if (!company) return frappe.msgprint("Chọn đơn vị nhận hàng trước.");
        frappe.call({method: "kh_aph.factory_transfer.incoming", args: {company}, callback(r) {
            if (!r.message?.length) return frappe.msgprint("Không có chuyến đang trên đường trong phạm vi quyền.");
            const dialog = new frappe.ui.Dialog({title: "Chọn chuyến đang trên đường", fields: [
                {fieldname: "stock_entry", label: "Phiếu chuyển đi", fieldtype: "Select", reqd: 1,
                    options: r.message.map(x => ({value: x.name, label: x.name + " · " + x.posting_date}))}
            ], primary_action_label: "Nhập lượng thực nhận", primary_action(values) {
                dialog.hide(); kh_aph.transfer_in.open(values.stock_entry);
            }});
            dialog.show();
        }});
    };
}
if (frappe.ui.form?.on && !kh_aph.transfer_in.form_registered) {
    kh_aph.transfer_in.form_registered = true;
    frappe.ui.form.on("Stock Entry", {refresh(frm) {
        const d = frm.doc;
        if (!(frappe.boot?.kh_aph?.factory_receiving || frappe.boot?.kh_aph?.warehouse_transfer) || d.docstatus !== 1 || d.purpose !== "Material Transfer"
            || !d.add_to_transit || d.outgoing_stock_entry || Number(d.per_transferred || 0) >= 100) return;
        frm.add_custom_button("Nhận chuyến về kho", () => kh_aph.transfer_in.open(d.name)).addClass("btn-primary");
    }});
}

// Chỉ gợi ý từ đơn; phiếu chuyển vẫn dùng cùng API/native controller và quyền kho.
if (frappe.ui.form?.on && !kh_aph.transfer_in.order_registered) {
    kh_aph.transfer_in.order_registered = true;
    frappe.ui.form.on("APH Shared Sales Order", {refresh(frm) {
        if (!frappe.boot?.kh_aph?.warehouse_transfer || frm.doc.docstatus !== 1 ||
            !frappe.model.can_create("Stock Entry")) return;
        frm.add_custom_button("Gom hàng cho đơn", async () => {
            const response = await frappe.call({method: "kh_aph.order_transfer.preview", args: {shared_order: frm.doc.name}, freeze: true});
            const source = response.message;
            if (!source.groups.length) return frappe.msgprint("Đơn đã giao hoặc đã lập phiếu xuất hết lượng.");
            const open = index => kh_aph.transfer_in.send(source.groups[index].company,
                {...source.groups[index], shared_order: source.shared_order});
            if (source.groups.length === 1) return open(0);
            frappe.prompt({fieldname: "group", label: "Đơn vị và kho giao khách", fieldtype: "Select", reqd: 1,
                options: source.groups.map((g, i) => ({value: String(i), label: g.company + " · " + g.destination}))},
                value => open(Number(value.group)), "Chọn nơi cần gom hàng", "Tiếp tục");
        }, "Chuẩn bị giao");
    }});
}
