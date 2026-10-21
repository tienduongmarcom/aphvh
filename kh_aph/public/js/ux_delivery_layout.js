// Một bộ nhập giao nhận theo thế hệ phiếu; không ghi đè hoặc chuyển dữ liệu lịch sử.
(() => {
    function show_delivery_fields(frm) {
        if (!frappe.boot?.kh_aph?.ux_task_first) return;
        const current = !frm.doc.is_return && (!!frm.doc.kh_aph_cach_giao || frm.is_new());
        const legacy = ["kh_aph_hinh_thuc_giao", "kh_aph_nguoi_nhan", "kh_aph_nha_xe", "kh_aph_lai_xe", "kh_aph_bien_so_xe", "kh_aph_sdt_lai_xe"];
        const modern = ["kh_aph_cach_giao", "kh_aph_nguoi_nhan_tai_kho", "kh_aph_dien_thoai_nhan", "kh_aph_nguoi_thuc_giao", "kh_aph_ban_giao_luc", "kh_aph_ban_giao_boi"];
        frm.toggle_display(legacy, !current);
        // Phiếu cũ/phiếu trả tiếp tục đúng bộ thông tin cũ; không buộc nhập bộ mới.
        frm.toggle_display(modern, current);
        const ship = current && frm.doc.kh_aph_cach_giao === "Vận chuyển";
        frm.toggle_display(["kh_aph_nha_xe_dot", "kh_aph_sdt_nha_xe_dot", "kh_aph_can_ky_khach"], ship);
        frm.toggle_display("kh_aph_chi_dinh_nhan", current && frm.doc.kh_aph_cach_giao === "Xe khách đến lấy");
        frm.toggle_display(["kh_aph_nguon_bao_nhan", "kh_aph_ngay_khach_nhan"], ship && frm.doc.docstatus === 1);
        frm.toggle_display(["kh_aph_dot_xuat"], false);
    }
    frappe.ui.form.on("Delivery Note", {
        refresh: show_delivery_fields,
        kh_aph_cach_giao: show_delivery_fields,
        is_return: show_delivery_fields,
    });
})();
