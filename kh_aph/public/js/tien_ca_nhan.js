// Dialog chỉ đọc số của session; không xin quyền GL hoặc lấy chứng từ nguồn.
(function () {
	frappe.provide("kh_aph");
	if (kh_aph.personal_cash_dialog) return;
	kh_aph.personal_cash_dialog = function (company) {
		let loading = false, generation = 0, company_generation = 0;
		const output = ["expected_amount", "reserved_amount", "available_amount", "status", "checked_at"];
		let d;
		const clear = () => {if (d) output.forEach(key => d.set_value(key, null));};
		d = new frappe.ui.Dialog({title: __("Tiền tôi đang giữ"), fields: [
			{fieldtype: "HTML", options: __("Số tiền theo trách nhiệm đã xác minh của chính bạn. Phần chưa xác minh được kế toán xử lý riêng. Đây là màn hình xem, không ghi thu hoặc bàn giao.")},
			{fieldname: "company", label: __("Đơn vị"), fieldtype: "Link", options: "Company", reqd: 1,
				onchange() {
					if (!d) return;
					const selected = d.get_value("company"), request = ++company_generation;
					++generation;
					clear(); d.set_value("account", ""); d.set_df_property("account", "options", "");
					if (!selected) return;
					frappe.call({method: "kh_aph.personal_cash.accounts", args: {company: selected}}).then(r => {
						if (request !== company_generation || d.get_value("company") !== selected) return;
						const accounts = r.message || [];
						d.set_df_property("account", "options", ["", ...accounts].join("\n"));
						if (accounts.length === 1) d.set_value("account", accounts[0]);
					});
				}},
			{fieldname: "account", label: __("Quỹ tiền mặt"), fieldtype: "Select", options: "", reqd: 1, onchange() {++generation; clear();}},
			{fieldname: "expected_amount", label: __("Tiền theo trách nhiệm"), fieldtype: "Currency", options: "VND", read_only: 1},
			{fieldname: "reserved_amount", label: __("Đang giữ chỗ bàn giao"), fieldtype: "Currency", options: "VND", read_only: 1},
			{fieldname: "available_amount", label: __("Còn khả dụng để bàn giao"), fieldtype: "Currency", options: "VND", read_only: 1},
			{fieldname: "status", label: __("Tình trạng"), fieldtype: "Data", read_only: 1},
			{fieldname: "checked_at", label: __("Kiểm tra lúc"), fieldtype: "Datetime", read_only: 1}
		], primary_action_label: __("Xem số tiền"), primary_action(values) {
			if (loading) return;
			loading = true; clear();
			d.get_primary_btn().prop("disabled", true);
			const request = generation;
			frappe.call({method: "kh_aph.personal_cash.current", args: {company: values.company, account: values.account}, freeze: true}).then(r => {
				if (request !== generation || values.account !== d.get_value("account")) return;
				const data = r.message;
				d.set_values({expected_amount: data.expected_amount, reserved_amount: data.reserved_amount,
					available_amount: data.available_amount, checked_at: data.checked_at,
					status: data.disputed ? __("Cần đối chiếu trước khi giao tiền") : __("Đã đối chiếu theo mốc xác minh")});
			}).always(() => {loading = false; d.get_primary_btn().prop("disabled", false);});
		}});
		d.show();
		if (company) d.set_value("company", company);
	};
	["Customer", "APH Phieu quy nha may"].forEach(doctype => frappe.ui.form.on(doctype, {
		refresh(frm) {
			if (!(frappe.boot.kh_aph || {}).cash_closing) return;
			if (frappe.session.user !== "Administrator" && !["Accounts User", "Accounts Manager", "System Manager", "Kế toán bán hàng", "Kế toán nhà máy"].some(role => frappe.user.has_role(role))) return;
			frm.add_custom_button(__("Tiền tôi đang giữ"), () => kh_aph.personal_cash_dialog(
				frm.doc.company || frappe.defaults.get_user_default("Company")));
		}
	}));
})();

// Chốt ca dùng cùng snapshot chuẩn, hai bước xem số rồi tự xác nhận.
(function () {
  if(kh_aph.personal_shift_dialog)return;
  function shift(company) {
    const request_id=Array.from(crypto.getRandomValues(new Uint8Array(16)), n=>n.toString(16).padStart(2,"0")).join("");
    let generation=0, loading=false, d;
    d=new frappe.ui.Dialog({title:__("Chốt ca tiền của tôi"),fields:[
      {fieldtype:"HTML",options:__("Nhập số thực đếm. Hệ thống tính số phải có; chốt ca không ghi thu hoặc bàn giao tiền.")},
      {fieldname:"company",label:__("Đơn vị"),fieldtype:"Link",options:"Company",reqd:1,onchange(){
        if(!d)return;const selected=d.get_value("company"), id=++generation;
        d.set_value("account","");d.set_df_property("account","options","");
        if(selected)frappe.call({method:"kh_aph.personal_cash.accounts",args:{company:selected}}).then(r=>{if(id!==generation)return;d.set_df_property("account","options",["",...r.message].join("\n"));if(r.message.length===1)d.set_value("account",r.message[0]);});
      }},
      {fieldname:"account",label:__("Quỹ tiền mặt"),fieldtype:"Select",reqd:1},
      {fieldname:"counted_amount",label:__("Tiền thực đếm"),fieldtype:"Currency",options:"VND",reqd:1},
      {fieldname:"reason",label:__("Ghi chú / lý do lệch"),fieldtype:"Small Text"},
      {fieldname:"assignee",label:__("Người xử lý khi lệch"),fieldtype:"Link",options:"User"},
      {fieldname:"due_date",label:__("Hạn xử lý khi lệch"),fieldtype:"Date"}
    ],primary_action_label:__("Kiểm số trước khi chốt"),primary_action(values){
      if(loading)return;loading=true;d.get_primary_btn().prop("disabled",true);
      frappe.call({method:"kh_aph.personal_cash.prepare_shift",args:{...values,request_id},freeze:true}).then(r=>{
        const v=r.message;
        if(v.docstatus===1){d.hide();frappe.msgprint(__("Ca này đã chốt: ")+v.name);return;}
        frappe.confirm(frappe.utils.escape_html(values.company)+"<br>"+frappe.utils.escape_html(values.account)+"<br>"+__("Phải có: ")+format_currency(v.expected_amount,"VND")+"<br>"+__("Thực đếm: ")+format_currency(v.counted_amount,"VND")+"<br>"+__("Chênh lệch: ")+format_currency(v.difference,"VND"),()=>frappe.call({method:"kh_aph.personal_cash.confirm_shift",args:{name:v.name},freeze:true}).then(()=>{d.hide();frappe.msgprint(__("Đã chốt ca: ")+v.name);}));
      }).always(()=>{loading=false;d.get_primary_btn().prop("disabled",false);});
    }});d.show();if(company)d.set_value("company",company);
  }
  kh_aph.personal_shift_dialog=shift;
  ["Customer","APH Phieu quy nha may"].forEach(doctype=>frappe.ui.form.on(doctype,{refresh(frm){
    if((frappe.boot.kh_aph||{}).factory_handover && (frappe.session.user==="Administrator" || ["Accounts User","Accounts Manager","System Manager","Kế toán bán hàng","Kế toán nhà máy"].some(role=>frappe.user.has_role(role)))) frm.add_custom_button(__("Chốt ca tiền của tôi"),()=>shift(frm.doc.company||frappe.defaults.get_user_default("Company")));
  }}));
})();
