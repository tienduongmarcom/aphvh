frappe.ui.form.on("APH Xac minh quy", {
  setup(frm) {
    frm.set_query("account", () => ({filters: {company: frm.doc.company, account_type: "Cash", is_group: 0, disabled: 0, account_currency: "VND"}}));
    frm.set_query("holder", "allocations", () => ({filters: {enabled: 1, user_type: "System User"}}));
  },
  refresh(frm) {
    frm.set_intro(__("Lưu nháp để lấy số dư sổ. Phân bổ theo tiền đã xác minh và để riêng phần chưa rõ. Xác nhận không tạo thêm số dư kế toán. Bản xác minh mới phải có căn cứ; bản cũ được giữ lại."));
  }
});
