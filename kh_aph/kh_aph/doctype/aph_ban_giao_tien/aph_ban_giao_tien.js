frappe.ui.form.on("APH Ban giao tien", {
  setup(frm) {
    frm.set_query("from_account", () => ({filters: {company: frm.doc.company, account_type: "Cash", account_currency: "VND", is_group: 0, disabled: 0}}));
    frm.set_query("to_account", () => ({filters: {company: frm.doc.company, account_type: ["in", ["Cash", "Bank"]], account_currency: "VND", is_group: 0, disabled: 0}}));
    frm.set_query("to_holder", () => ({filters: {enabled: 1, user_type: "System User", name: ["!=", frm.doc.from_holder]}}));
  },
  onload(frm) {
    if (frm.is_new() && !frm.doc.from_holder) frm.set_value("from_holder", frappe.session.user);
  },
  refresh(frm) {
    frm.set_intro(__("Gửi đề nghị giữ chỗ tiền nguồn. Đúng người nhận nhập số thực nhận; cùng quỹ không ghi sổ, khác quỹ/ngân hàng chỉ ghi một chuyển tiền. Khoản lệch cần xử lý riêng."));
    const invoke = async (method, args = {}) => {
      const r = await frappe.call({method: "kh_aph.cash_handover." + method, args: {name: frm.doc.name, ...args}, freeze: true});
      await frm.reload_doc();
      return r;
    };
    if (frm.doc.docstatus === 0 && !frm.is_new() && !frm.is_dirty() && frm.doc.from_holder === frappe.session.user) {
      frm.add_custom_button(__("Gửi bàn giao"), () => invoke("send"));
    }
    if (frm.doc.docstatus === 1 && ["Chờ nhận", "Vượt nguồn cần xử lý"].includes(frm.doc.status) && frm.doc.from_holder === frappe.session.user) {
      frm.add_custom_button(__("Hủy đề nghị"), () => frappe.confirm(__("Hủy đề nghị và giải phóng phần tiền giữ chỗ?"), () => invoke("cancel")));
    }
    if (frm.doc.docstatus === 1 && frm.doc.status === "Chờ nhận" && frm.doc.to_holder === frappe.session.user) {
      frm.add_custom_button(__("Xác nhận thực nhận"), () => {
        const dialog = new frappe.ui.Dialog({title: __("Kiểm đếm tiền bàn giao"), fields: [
          {fieldname: "amount", label: __("Số tiền thực nhận"), fieldtype: "Currency", options: "VND", precision: 2, reqd: 1, default: frm.doc.requested_amount},
          {fieldname: "reason", label: __("Giải trình khi chênh lệch/vượt nguồn"), fieldtype: "Small Text"},
          {fieldname: "assignee", label: __("Người xử lý chênh lệch"), fieldtype: "Link", options: "User"},
          {fieldname: "due_date", label: __("Hạn xử lý"), fieldtype: "Date"}
        ], primary_action_label: __("Xác nhận số thực nhận"), primary_action: async values => {
          dialog.get_primary_btn().prop("disabled", true);
          try { await invoke("receive", values); dialog.hide(); }
          finally { dialog.get_primary_btn().prop("disabled", false); }
        }});
        dialog.show();
      });
    }
  }
});
