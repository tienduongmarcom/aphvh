frappe.ui.form.on("APH Source Change", {
    setup(frm) {
        frm.set_query("source_order",()=>({filters:{docstatus:1,...(frm.doc.shared_order?{kh_aph_shared_order:frm.doc.shared_order}:{kh_aph_shared_order:["is","set"]})}}));
        frm.set_query("target_warehouse",()=>({filters:{is_group:0,disabled:0}}));
    },
    refresh(frm) {
        if(frm.doc.docstatus!==0 || !frm.doc.source_order)return;
        frm.add_custom_button("Chọn phần chưa giao",async()=>{
            const response=await frappe.call({method:"frappe.client.get",args:{doctype:"Sales Order",name:frm.doc.source_order}});
            const rows=response.message.items.filter(r=>Number(r.qty)>Number(r.delivered_qty));
            if(!rows.length)return frappe.msgprint("Nguồn không còn lượng chưa giao.");
            frappe.prompt([
                {fieldname:"line",label:"Dòng chưa giao",fieldtype:"Select",reqd:1,options:rows.map((r,i)=>(i+1)+" · "+r.item_code+" · "+r.warehouse+" · còn "+(Number(r.qty)-Number(r.delivered_qty))+" kg").join("\n")},
                {fieldname:"qty",label:"Lượng chuyển nguồn (kg)",fieldtype:"Float",reqd:1},
                {fieldname:"warehouse",label:"Kho mới",fieldtype:"Link",options:"Warehouse",reqd:1},
                {fieldname:"reason",label:"Lý do đổi nguồn",fieldtype:"Small Text",reqd:1}
            ],async values=>{
                const row=rows[Number(values.line.split(" · ")[0])-1];
                await frm.set_value({source_row:row.name,source_item:row.item_code,qty:values.qty,target_warehouse:values.warehouse,reason:values.reason});
            },"Đổi nguồn phần chưa giao","Chọn");
        });
    },
    source_order(frm){frm.trigger("refresh");}
});
