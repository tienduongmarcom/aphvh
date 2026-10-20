frappe.ui.form.on("APH Chot ca tien", {
  setup(frm) {
    frm.set_query("account", () => ({filters: {company: frm.doc.company, account_type: "Cash", is_group: 0, disabled: 0, account_currency: "VND"}}));
  },
  onload(frm) {
    if (frm.is_new() && !frm.doc.holder) frm.set_value("holder", frappe.session.user);
  },
  refresh(frm) {
    frm.set_intro(__("Chốt ca lưu số kiểm đếm; không ghi thêm thu/chi hoặc công nợ. Lưu nháp để kiểm số phải có trước khi xác nhận."));
    const manager = frappe.session.user === "Administrator" || (frappe.user_roles.some(r => ["Accounts Manager", "System Manager"].includes(r)) && !frappe.user_roles.some(r => ["APH Không xem giá vốn", "Kế toán nhà máy"].includes(r)));
    if (frm.doc.docstatus === 1 && frm.doc.difference && frm.doc.issue_state !== "Đã đối chiếu" && manager) {
      frm.add_custom_button(__("Đối chiếu lệch tiền"), () => frappe.new_doc("APH Doi chieu lech tien", {source_type: frm.doctype, source_name: frm.doc.name}));
    }
    if (frm.doc.docstatus === 0 && !frm.is_new() && !frm.is_dirty()) {
      frm.add_custom_button(__("Chốt ca của tôi"), async () => {
        await frappe.call({method: "kh_aph.cash_closing.close", args: {name: frm.doc.name}, freeze: true});
        await frm.reload_doc();
      });
    }
    if (frm.doc.docstatus === 1) {
      frm.add_custom_button(__("Đối chiếu số hiện tại"), async () => {
        const {message} = await frappe.call({method: "kh_aph.cash_closing.current", args: {company: frm.doc.company, account: frm.doc.account}});
        frappe.msgprint(__("Tiền phải có của bạn hiện tại: {0}. Số chốt cũ vẫn giữ nguyên.", [format_currency(message.expected_amount, "VND")]));
      });
    }
  }
});
