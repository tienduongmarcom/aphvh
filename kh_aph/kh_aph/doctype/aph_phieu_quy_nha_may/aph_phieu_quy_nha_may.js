frappe.ui.form.on("APH Phieu quy nha may", {
  refresh(frm) {
    const enabled = !!(frappe.boot.kh_aph || {}).factory_handover;
    const is_transfer = frm.doc.loai === "Bàn giao tiền";
    const caller = frappe.session.user;
    const call = (method, args) => frappe.call({method, args, freeze:true});
    const destination = (done) => call("kh_aph.factory_handover.destinations", {company:frm.doc.company}).then(r => {
      frappe.prompt([{fieldname:"account",label:__("Quỹ/ngân hàng nhận"),fieldtype:"Select",options:["",...r.message].join("\n"),reqd:1,default:frm.doc.tai_khoan_nhan}], v => done(v.account), __("Chọn quỹ nhận trước khi gửi"));
    });
    if (enabled && is_transfer && frm.doc.docstatus === 0) {
      frm.add_custom_button(__("Chọn quỹ nhận"), () => destination(account => frm.set_value("tai_khoan_nhan", account)));
    }
    if (enabled && is_transfer && frm.doc.docstatus === 1 && !frm.doc.ban_giao_tien && frm.doc.trang_thai === "Chờ nhận" && frm.doc.kh_aph_nguoi_giu_tien === caller) {
      frm.add_custom_button(__("Chuyển tiếp và giữ chỗ"), () => destination(account => call("kh_aph.factory_handover.connect_pending", {name:frm.doc.name,tai_khoan_nhan:account}).then(() => frm.reload_doc())));
    }
    if (frm.doc.docstatus === 1 && is_transfer && frm.doc.trang_thai === "Chờ nhận" && frm.doc.nguoi_nhan === caller) {
      frm.add_custom_button(__("Xác nhận đã nhận tiền"), () => {
        const dialog = new frappe.ui.Dialog({title:__("Nhận tiền bàn giao"),fields:[
          {fieldname:"so_thuc_nhan",label:__("Số tiền đếm được"),fieldtype:"Currency",options:"VND",reqd:1,default:frm.doc.tong_tien},
          {fieldname:"tai_khoan_nhan",label:__("Quỹ/tài khoản nhận"),fieldtype:enabled?"Data":"Link",options:enabled?undefined:"Account",reqd:1,default:frm.doc.tai_khoan_nhan,read_only:!!frm.doc.ban_giao_tien,
            get_query:()=>({filters:{company:frm.doc.company,account_type:["in",["Cash","Bank"]],is_group:0}})},
          {fieldname:"reason",label:__("Lý do khi chênh lệch"),fieldtype:"Small Text"},
          {fieldname:"assignee",label:__("Người xử lý lệch"),fieldtype:"Link",options:"User"},
          {fieldname:"due_date",label:__("Hạn xử lý"),fieldtype:"Date"}
        ],primary_action_label:__("Xác nhận số thực nhận"),primary_action(v) {
          dialog.get_primary_btn().prop("disabled",true);
          call("kh_aph.factory_cash.xac_nhan_nhan",{name:frm.doc.name,...v}).then(()=>{dialog.hide();return frm.reload_doc();}).always(()=>dialog.get_primary_btn().prop("disabled",false));
        }});dialog.show();
      });
    }
    if (enabled && frm.doc.docstatus === 1 && frm.doc.ban_giao_tien) {
      call("kh_aph.factory_handover.status",{name:frm.doc.name}).then(r=>{
        const value=r.message;
        if (["Chờ nhận","Vượt nguồn cần xử lý"].includes(value.status) && value.from_holder===caller) {
          frm.add_custom_button(__("Hủy đề nghị bàn giao"),()=>frappe.confirm(__("Giải phóng giữ chỗ và giữ lịch sử đề nghị?"),()=>call("kh_aph.cash_handover.cancel",{name:value.root}).then(()=>frm.reload_doc())));
        }
        if (["Đã nhận","Có chênh lệch"].includes(value.status) && value.received_amount>0 && value.to_holder===caller && value.issue_state!=="Chờ xử lý" && !value.reverse) {
          frm.add_custom_button(__("Hoàn toàn bộ bàn giao"),()=>{
            const request_id=Array.from(crypto.getRandomValues(new Uint8Array(16)), n=>n.toString(16).padStart(2,"0")).join("");
            const d=new frappe.ui.Dialog({title:__("Hoàn tiền về người giao"),fields:[{fieldname:"reason",label:__("Lý do hoàn"),fieldtype:"Small Text",reqd:1}],primary_action_label:__("Gửi phiếu hoàn"),primary_action(v){
              d.get_primary_btn().prop("disabled",true);
              call("kh_aph.cash_handover.create_reverse",{name:value.root,request_id,reason:v.reason}).then(()=>{d.hide();return frm.reload_doc();}).always(()=>d.get_primary_btn().prop("disabled",false));
            }});d.show();
          });
        }
        if (value.reverse?.status==="Chờ nhận" && value.reverse.to_holder===caller) {
          frm.add_custom_button(__("Xác nhận nhận lại tiền hoàn"),()=>frappe.confirm(__("Xác nhận đã đếm đủ số tiền hoàn: ")+format_currency(value.reverse.amount,"VND"),()=>call("kh_aph.cash_handover.receive",{name:value.reverse.name,amount:value.reverse.amount}).then(()=>frm.reload_doc())));
        }
      });
    }
  }
});
