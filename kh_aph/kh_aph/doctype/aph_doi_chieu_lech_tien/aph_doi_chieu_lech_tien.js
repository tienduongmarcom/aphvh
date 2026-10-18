frappe.ui.form.on("APH Doi chieu lech tien", {
  setup(frm) {
    frm.set_query("verification", "proofs", (doc, cdt, cdn) => ({filters: {company: doc.company, account: locals[cdt][cdn].account, docstatus: 1}}));
    frm.set_query("shift", "proofs", (doc, cdt, cdn) => {
      const row = locals[cdt][cdn];
      return {filters: {company: doc.company, account: row.account, holder: row.holder, verification: row.verification, docstatus: 1, difference: 0}};
    });
  },
  refresh(frm) {
    const invoke = async method => {
      await frappe.call({method: "kh_aph.cash_issue." + method, args: {name: frm.doc.name}, freeze: true});
      await frm.reload_doc();
    };
    if (frm.doc.docstatus === 0 && !frm.is_new() && !frm.is_dirty()) frm.add_custom_button(__("Chốt đối chiếu lệch"), () => invoke("confirm"));
    if (frm.doc.docstatus === 1) frm.add_custom_button(__("Mở lại vụ lệch"), () => frappe.confirm(__("Mở lại sẽ chặn giao ra cho đến khi đối chiếu lại. Giữ nguyên số đếm và chứng từ cũ?"), () => invoke("reopen")));
    frm.set_intro(__("Lưu nháp để có các phía cần đối chiếu. Chọn xác minh mới và ca khớp của từng người, ghi kết quả và tệp căn cứ riêng tư rồi xác nhận. Hồ sơ không tự sửa sổ; hủy hồ sơ đã xác nhận sẽ mở lại vụ lệch."));
  }
});
