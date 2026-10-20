// UX-01 PR-B: "Việc tiếp theo" trên chứng từ. Chỉ bấm hộ nút nghiệp vụ đã có (đã kiểm quyền ở server), không gọi hàm ghi mới.
// Mỗi trạng thái một việc chính; việc phụ vẫn ở các nhóm nút cũ.
frappe.provide("kh_aph.ux");
if (!kh_aph.ux.buoc_tiep) {
    kh_aph.ux.nut = function(frm, label) {
        // Frappe giữ nút tự thêm theo nhãn (kể cả trong nhóm) ở frm.custom_buttons.
        const b = frm.custom_buttons && frm.custom_buttons[label];
        return b && b.length ? b : null;
    };
    kh_aph.ux.viec = function(frm) {
        const d = frm.doc, dt = frm.doctype, co = l => kh_aph.ux.nut(frm, l);
        if (dt === "APH Shared Sales Order") {
            if (d.docstatus === 0 && frm.perm.some(p => p.submit))
                return {text: "Đơn đang nháp: kiểm tra hàng, nguồn, giá rồi xác nhận đơn.", nut: [["Kiểm tra và xác nhận đơn", () => frm.savesubmit()]]};
            if (d.docstatus === 1 && co("Lập phiếu xuất & In"))
                return {text: "Đơn đã xác nhận, còn hàng chưa lập phiếu. Lập phiếu chưa trừ kho.", nut: [["Lập phiếu xuất & In", "Lập phiếu xuất & In"]]};
        }
        if (dt === "Delivery Note" && !d.is_return) {
            if (d.docstatus === 0) {
                const nut = [["Xác nhận bàn giao vận chuyển", "Bàn giao cho người vận chuyển"], ["Xác nhận khách đến lấy", "Khách đến lấy"]].filter(x => co(x[1]));
                if (nut.length) return {text: "Phiếu chờ xuất: hàng CHƯA ra khỏi kho. Xác nhận khi hàng thực sự giao đi (ghi trừ kho và công nợ).", nut};
            }
            if (d.docstatus === 1 && d.kh_aph_delivery_state === "Đang giao" && co("Khách đã nhận"))
                return {text: "Hàng đang trên đường giao.", nut: [["Xác nhận khách đã nhận", "Khách đã nhận"]]};
            if (d.docstatus === 1 && d.kh_aph_delivery_state === "Khách đã nhận" && !d.kh_aph_ban_ky && frm.fields_dict.kh_aph_ban_ky)
                return {text: "Khách đã nhận, còn thiếu bản phiếu có chữ ký.", nut: [["Bổ sung bản ký", () => frm.scroll_to_field("kh_aph_ban_ky")]]};
            if (d.docstatus === 1 && d.kh_aph_ban_ky && !d.kh_aph_doi_chieu_boi && co("Đối chiếu bản ký"))
                return {text: "Đã có bản ký, cần đối chiếu nội dung.", nut: [["Đối chiếu bản ký", "Đối chiếu bản ký"]]};
            if (d.docstatus === 1 && ["Cần xử lý", "Đang xử lý"].includes(d.kh_aph_chenh_lech_state)) {
                const nut = [["Giao người xử lý", "Giao người xử lý"], ["Chốt xử lý chênh lệch", "Chốt xử lý chênh lệch"]].filter(x => co(x[1]));
                if (nut.length) return {text: "Có chênh lệch giao nhận đang chờ xử lý.", nut};
            }
        }
        if (dt === "Sales Invoice" && d.docstatus === 1 && !d.is_return && Number(d.outstanding_amount) > 0 && co("Thu tiền"))
            return {text: "Khách còn nợ hóa đơn này. Ghi đúng số tiền thực nhận; phần dư để chưa phân bổ, không tự cấn hóa đơn khác.",
                nut: [["Ghi nhận thanh toán", kh_aph.ux.thu_tien ? () => kh_aph.ux.thu_tien(d.customer, [d.name]) : "Thu tiền"]]};
        return null;
    };
    kh_aph.ux.buoc_tiep = function(frm) {
        if (!frappe.boot?.kh_aph?.ux_task_first || frm.is_new()) return;
        // Chạy sau các refresh khác để thấy đủ nút nghiệp vụ đã thêm.
        setTimeout(() => {
            const v = kh_aph.ux.viec(frm);
            if (!v) return;
            const id = "kh-aph-viec-" + frappe.utils.get_random(6);
            const nut = v.nut.map((x, i) => `<button class="btn btn-${i ? "default" : "primary"} btn-sm ml-2" data-i="${i}">${frappe.utils.escape_html(x[0])}</button>`).join("");
            frm.dashboard.set_headline_alert(`<div id="${id}" class="flex justify-between align-center" style="font-size:15px">
                <span><b>Bước tiếp theo:</b> ${frappe.utils.escape_html(v.text)}</span><span>${nut}</span></div>`, "blue");
            $(`#${id} button`).on("click", function() {
                const hanh_dong = v.nut[Number($(this).data("i"))][1];
                if (typeof hanh_dong === "function") return hanh_dong();
                const b = kh_aph.ux.nut(frm, hanh_dong);
                if (b) b.trigger("click"); else frappe.msgprint("Thao tác không còn khả dụng; tải lại phiếu.");
            });
        }, 0);
    };
    for (const dt of ["APH Shared Sales Order", "Delivery Note", "Sales Invoice"])
        frappe.ui.form.on(dt, {refresh: frm => kh_aph.ux.buoc_tiep(frm)});
}
