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
    const manager = frappe.session.user === "Administrator" || (frappe.user_roles.some(r => ["Accounts Manager", "System Manager"].includes(r)) && !frappe.user_roles.some(r => ["APH Không xem giá vốn", "Kế toán nhà máy"].includes(r)));
    if ([1, 2].includes(frm.doc.docstatus) && frm.doc.issue_state === "Chờ xử lý" && manager) {
      frm.add_custom_button(__("Đối chiếu lệch tiền"), () => frappe.new_doc("APH Doi chieu lech tien", {source_type: frm.doctype, source_name: frm.doc.name}));
    }
    if (frm.doc.reversal_doc) frm.add_custom_button(__("Mở phiếu hoàn"), () => frappe.set_route("Form", frm.doctype, frm.doc.reversal_doc));
    if (frm.doc.docstatus === 1 && ["Đã nhận", "Có chênh lệch"].includes(frm.doc.status) && !frm.doc.reversal_of && frm.doc.received_amount > 0 && frm.doc.to_holder === frappe.session.user && frm.doc.issue_state !== "Chờ xử lý") {
      frm.add_custom_button(__("Lập phiếu hoàn"), () => {
        const request_id = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
        const dialog = new frappe.ui.Dialog({title: __("Trả lại toàn bộ tiền đã nhận"), fields: [
          {fieldname: "reason", label: __("Lý do hoàn"), fieldtype: "Small Text", reqd: 1},
          {fieldtype: "HTML", options: __("Phiếu ngược chiều giữ nguyên giao dịch gốc. Người giao ban đầu phải xác nhận nhận lại; tiền đã dùng tiếp không được hoàn vượt nguồn.")}
        ], primary_action_label: __("Gửi phiếu hoàn"), primary_action: async values => {
          dialog.get_primary_btn().prop("disabled", true);
          try {
            const {message} = await frappe.call({method: "kh_aph.cash_handover.create_reverse", args: {name: frm.doc.name, request_id, reason: values.reason}, freeze: true});
            dialog.hide();
            await frappe.set_route("Form", frm.doctype, message.name);
          } finally { dialog.get_primary_btn().prop("disabled", false); }
        }});
        dialog.show();
      });
    }
    if (frm.doc.docstatus === 0 && !frm.is_new() && !frm.is_dirty() && frm.doc.from_holder === frappe.session.user) {
      frm.add_custom_button(__("Gửi bàn giao"), () => invoke("send"));
    }
    if (frm.doc.docstatus === 1 && ["Chờ nhận", "Vượt nguồn cần xử lý"].includes(frm.doc.status) && frm.doc.from_holder === frappe.session.user) {
      frm.add_custom_button(__("Hủy đề nghị"), () => frappe.confirm(__("Hủy đề nghị và giải phóng phần tiền giữ chỗ?"), () => invoke("cancel")));
    }
    if (frm.doc.docstatus === 1 && frm.doc.status === "Chờ nhận" && frm.doc.to_holder === frappe.session.user) {
      frm.add_custom_button(__("Xác nhận nhận tiền"), () => {
        const dialog = new frappe.ui.Dialog({title: __("Kiểm đếm tiền bàn giao"), fields: [
          {fieldname: "amount", label: __("Số tiền thực nhận"), fieldtype: "Currency", options: "VND", precision: 2, reqd: 1, default: frm.doc.requested_amount},
          {fieldname: "reason", label: __("Giải trình khi chênh lệch/vượt nguồn"), fieldtype: "Small Text"},
          {fieldname: "assignee", label: __("Người xử lý chênh lệch"), fieldtype: "Link", options: "User"},
          {fieldname: "due_date", label: __("Hạn xử lý"), fieldtype: "Date"}
        ], primary_action_label: __("Xác nhận số tiền thực nhận"), primary_action: async values => {
          dialog.get_primary_btn().prop("disabled", true);
          try { await invoke("receive", values); dialog.hide(); }
          finally { dialog.get_primary_btn().prop("disabled", false); }
        }});
        dialog.show();
      });
    }
  }
});
