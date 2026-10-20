// Một bộ nhập giao nhận theo thế hệ phiếu; không ghi đè hoặc chuyển dữ liệu lịch sử.
frappe.ui.form.on("Delivery Note", {
    refresh(frm) {
        if (!frappe.boot?.kh_aph?.ux_task_first) return;
        const current = !!frm.doc.kh_aph_cach_giao && !frm.doc.is_return;
        const legacy = ["kh_aph_hinh_thuc_giao", "kh_aph_nguoi_nhan", "kh_aph_nha_xe", "kh_aph_lai_xe", "kh_aph_bien_so_xe", "kh_aph_sdt_lai_xe"];
        const modern = ["kh_aph_cach_giao", "kh_aph_nguoi_nhan_tai_kho", "kh_aph_dien_thoai_nhan", "kh_aph_nguoi_thuc_giao", "kh_aph_ban_giao_luc", "kh_aph_ban_giao_boi"];
        frm.toggle_display(legacy, !current);
        // Phiếu cũ/phiếu trả tiếp tục đúng bộ thông tin cũ; không buộc nhập bộ mới.
        frm.toggle_display(modern, current || (frm.is_new() && !frm.doc.is_return));
        frm.toggle_display(["kh_aph_dot_xuat", "kh_aph_costing_rule"], false);
    }
});
