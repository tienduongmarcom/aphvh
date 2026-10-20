// Nhận nhanh dùng chung cho đơn mua và lối vào từ báo cáo số lượng.
frappe.provide("kh_aph.receiving");
if (!kh_aph.receiving.open) {
    kh_aph.receiving.open = function(purchase_order, mode = "valued") {
            frappe.call({method: "kh_aph.factory_receiving.preview", args: {purchase_order: purchase_order, mode},
                freeze: true, callback(r) {
                    const source = r.message;
                    if (!source || purchase_order !== source.purchase_order) return;
                    const request_id = frappe.utils.get_random(32);
                    const dialog = new frappe.ui.Dialog({title: "Nhận hàng theo đơn mua", primary_action_label: mode === "pending" ? "Xác nhận nhận chờ định giá" : "Xác nhận nhập kho",
                        fields: [
                            {fieldtype: "HTML", options: `<p>${frappe.utils.escape_html(source.company)} · ${frappe.utils.escape_html(source.supplier)}<br>${frappe.utils.escape_html(source.price_mode)}</p><p>Nhập đủ lượng thực nhận dùng. Lượng có vấn đề vẫn nằm trong tổng kg nhập, được ghi riêng để đàm phán giảm giá; hệ thống không tự giảm giá. Hàng chờ định giá chưa vào tồn khả dụng. Hàng lô/sê-ri dùng luồng chuẩn.</p>`},
                            {fieldname: "received_date", label: "Ngày nhận thực tế", fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today()},
                            {fieldname: "receiver", label: "Người thực nhận/ký tại kho", fieldtype: "Data", reqd: 1},
                            {fieldname: "ticket", label: "Phiếu cân (tệp riêng tư mới)", fieldtype: "Attach"},
                            {fieldname: "note", label: "Ghi chú chất lượng / đàm phán giảm giá", fieldtype: "Small Text"},
                            {fieldname: "items", label: "Nhập kg và số bao thực tế", fieldtype: "Table", cannot_add_rows: true, cannot_delete_rows: true,
                                data: source.items, fields: [
                                    {fieldname: "source_row", fieldtype: "Data", hidden: 1, read_only: 1},
                                    {fieldname: "item_code", label: "Mã hàng", fieldtype: "Data", read_only: 1, in_list_view: 1},
                                    {fieldname: "warehouse", label: "Kho nhận", fieldtype: "Link", options: "Warehouse", reqd: 1, in_list_view: 1,
                                        get_query: () => ({filters: {company: source.company, is_group: 0, disabled: 0}})},
                                    {fieldname: "remaining", label: "Còn nhận (kg)", fieldtype: "Float", read_only: 1, in_list_view: 1},
                                    {fieldname: "qty", label: "Tổng kg thực nhận", fieldtype: "Float", in_list_view: 1},
                                    {fieldname: "bags", label: "Tổng bao thực nhận", fieldtype: "Int", in_list_view: 1},
                                    {fieldname: "quality_qty", label: "Trong đó kg có vấn đề", fieldtype: "Float", in_list_view: 1},
                                    {fieldname: "kg_per_bag", label: "Kg/bao", fieldtype: "Float", read_only: 1}
                                ]}
                        ],
                        primary_action(values) {
                            if ((values.items || []).some(x => !Number.isFinite(Number(x.qty)) || Number(x.qty) < 0 ||
                                !Number.isFinite(Number(x.quality_qty)) || Number(x.quality_qty) < 0 || Number(x.quality_qty) > Number(x.qty) ||
                                !Number.isInteger(Number(x.bags)) || Number(x.bags) < 0))
                                return frappe.msgprint("Kiểm tra kg thực nhận, số bao và lượng có vấn đề từng dòng.");
                            const rows = (values.items || []).filter(x => Number(x.qty) > 0).map(x => ({source_row: x.source_row,
                                warehouse: x.warehouse, qty: x.qty, bags: x.bags || 0, quality_qty: x.quality_qty || 0}));
                            if (!rows.length) return frappe.msgprint("Nhập ít nhất một dòng thực nhận.");
                            frappe.confirm(mode === "pending" ? "Xác nhận lượng nhận chờ định giá? Hàng chưa vào tồn có thể xuất; lượng này được giữ chỗ trên đơn mua." : "Xác nhận lượng thực nhận? Thao tác này ghi nhập kho. Gửi lại trong cùng cửa sổ sẽ mở phiếu đã tạo.", () => {
                                dialog.get_primary_btn().prop("disabled", true);
                                frappe.call({method: "kh_aph.factory_receiving.receive", args: {purchase_order: source.purchase_order,
                                    request_id, mode, rows: JSON.stringify(rows), received_date: values.received_date, receiver: values.receiver,
                                    ticket: values.ticket || "", note: values.note || ""}, freeze: true,
                                    callback(r) {
                                        if (!r.message?.name) return;
                                        dialog.hide(); frappe.set_route("Form", r.message.doctype, r.message.name);
                                    }}).always(() => dialog.get_primary_btn().prop("disabled", false));
                            });
                        }
                    });
                    dialog.show();
                }});

    };
    kh_aph.receiving.pick = function(company) {
        if (!company) return frappe.msgprint("Chọn đơn vị nhận hàng trước.");
        frappe.call({method: "kh_aph.factory_receiving.orders", args: {company}, callback(r) {
            if (!r.message?.length) return frappe.msgprint("Không có đơn mua chờ nhận trong phạm vi quyền.");
            const dialog = new frappe.ui.Dialog({title: "Chọn đơn mua chờ nhận", fields: [
                {fieldname: "purchase_order", label: "Đơn mua", fieldtype: "Select", reqd: 1,
                    options: r.message.map(x => ({value: x.name, label: x.name + " · " + x.supplier}))},
                {fieldname: "mode", label: "Cách nhận", fieldtype: "Select", reqd: 1, default: "valued",
                    options: [{value: "valued", label: "Nhận theo giá đơn mua"}, {value: "pending", label: "Nhận chờ định giá (chưa vào tồn khả dụng)"}]}
            ], primary_action_label: "Nhập lượng thực nhận", primary_action(values) {
                dialog.hide(); kh_aph.receiving.open(values.purchase_order, values.mode);
            }}); dialog.show();
        }});
    };
}
if (frappe.ui.form?.on && !kh_aph.receiving.form_registered) {
    kh_aph.receiving.form_registered = true;
    frappe.ui.form.on("Purchase Order", {refresh(frm) {
        if (!frappe.boot?.kh_aph?.factory_receiving || frm.doc.docstatus !== 1) return;
        frm.add_custom_button("Nhận hàng nhà máy", () => {
            if (frm.is_dirty()) return frappe.msgprint("Lưu đơn trước khi nhận hàng.");
            kh_aph.receiving.open(frm.doc.name);
        });
        frm.add_custom_button("Nhận chờ định giá", () => {
            if (frm.is_dirty()) return frappe.msgprint("Lưu đơn trước khi nhận hàng.");
            kh_aph.receiving.open(frm.doc.name, "pending");
        });
    }});
}
