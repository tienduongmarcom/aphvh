// UX-3: tìm khách theo SĐT/MST/tên gọi tắt ngay trên danh sách khách, rồi thu tiền hoặc mở khách.
frappe.listview_settings["Customer"] = frappe.listview_settings["Customer"] || {};
(function(settings) {
    const old = settings.onload;
    settings.onload = function(list) {
        if (old) old(list);
        if (!frappe.boot?.kh_aph?.ux_task_first) return;
        list.page.add_inner_button("Tìm khách (SĐT, MST, tên)", () =>
            kh_aph.ux.tim_khach(c => frappe.set_route("Form", "Customer", c)));
        list.page.add_inner_button("Ghi nhận khách trả tiền", () => kh_aph.ux.thu_tien(null));
    };
})(frappe.listview_settings["Customer"]);
