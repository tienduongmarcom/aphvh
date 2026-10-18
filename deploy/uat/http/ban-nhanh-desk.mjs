// CI-only native Desk test using the runner's Chrome and Node WebSocket CDP.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {setTimeout as pause} from 'node:timers/promises';
if (process.env.GITHUB_ACTIONS !== 'true') throw Error('Disposable GitHub UAT only');
const state = JSON.parse(fs.readFileSync(fs.readFileSync(path.join(os.homedir(), 'APHVH_HTTP_UAT_STATE_PATH.txt'), 'utf8').trim(), 'utf8'));
if (state.site !== 'aphvh-web-uat' || state.container !== 'aphvh-p0-web-uat' || state.port !== 18091) throw Error('Wrong UAT');
const [source, mode] = process.argv.slice(2);
if (!source) throw Error('Thiếu mã đơn chung UAT');
const base = 'http://127.0.0.1:18091';
const login = await fetch(base + '/api/method/login', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({usr:'Administrator',pwd:state.admin_password})});
if (!login.ok || (await login.json()).message !== 'Logged In') throw Error('UAT browser login failed');
const cookies = login.headers.getSetCookie().map(s => s.split(';')[0]).map(s => {let n=s.indexOf('=');return {name:s.slice(0,n),value:s.slice(n+1),url:base}});
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'aphvh-desk-uat-'));
const chrome = spawn('google-chrome', ['--headless','--no-sandbox','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--remote-debugging-address=127.0.0.1','--remote-debugging-port=19229','--user-data-dir='+profile,'about:blank'], {stdio:'ignore'});
let ws, sequence=0;
let lostResponse = null;
const waiting=new Map();
const diagnostics=[];
try {
    let tab;
    for(let i=0;i<50;i++) {try {tab=(await (await fetch('http://127.0.0.1:19229/json/list')).json()).find(t=>t.type==='page');if(tab)break;} catch {} await pause(200);}
    if(!tab)throw Error('Chrome did not start');
    ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise((ok,no)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',no,{once:true});});
    ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')diagnostics.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.method==='Network.responseReceived'&&m.params.response.status>=400)diagnostics.push(m.params.response.status+' '+m.params.response.url.slice(0,180));if(m.method==='Fetch.requestPaused'){if(!lostResponse&&m.params.responseStatusCode===200){lostResponse=m.params;command('Fetch.failRequest',{requestId:m.params.requestId,errorReason:'Aborted'}).catch(e=>diagnostics.push(e.message));}else command('Fetch.continueRequest',{requestId:m.params.requestId}).catch(e=>diagnostics.push(e.message));}const p=waiting.get(m.id);if(p){waiting.delete(m.id);clearTimeout(p.timer);m.error?p.no(Error(m.error.message)):p.ok(m.result);}});
    const command=(method,params={})=>new Promise((ok,no)=>{const id=++sequence;const timer=setTimeout(()=>{waiting.delete(id);no(Error('CDP timeout: '+method));},30000);waiting.set(id,{ok,no,timer});ws.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const r=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result?.value;};
    const until=async expression=>{for(let i=0;i<180;i++){if(await evaluate(expression))return;await pause(350);}throw Error('Desk condition not met: '+expression+'; state='+JSON.stringify(await evaluate('({url:location.href,frappe:!!window.frappe,user:window.frappe?.session?.user,doctype:window.cur_frm?.doctype})'))+'; errors='+JSON.stringify(diagnostics.slice(-8)));};
    await command('Page.enable');await command('Runtime.enable');await command('Network.enable');await command('Network.setCookies',{cookies});
    if (mode === 'xuat-ngay') {
        await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
        await command('Page.navigate',{url:base+'/desk/aph-shared-sales-order/'+encodeURIComponent(source)});
        await until('!!window.cur_frm && !!cur_frm.custom_buttons["Lập phiếu xuất & In"]');
        await evaluate('cur_frm.custom_buttons["Lập phiếu xuất & In"].trigger("click");true');
        await until('!!window.cur_dialog && !!cur_dialog.fields_dict.dispatch_now');
        await evaluate('(async()=>{window.__fastDialog=cur_dialog;await cur_dialog.set_value("delivery_method","Khách đến lấy");await cur_dialog.set_value("recipient","Khách tự lấy UAT");await cur_dialog.set_value("dispatch_now",1);await cur_dialog.set_value("dispatcher","Kho UAT trình duyệt");cur_dialog.fields_dict.rows.df.data[0].qty=2;cur_dialog.fields_dict.rows.grid.refresh();return true;})()');
        await command('Fetch.enable',{patterns:[{urlPattern:'*kh_aph.ban_nhanh.create_and_dispatch*',requestStage:'Response'}]});
        await evaluate('__fastDialog.get_primary_btn().trigger("click");true');
        for(let i=0;i<300&&!lostResponse;i++)await pause(100);
        if(!lostResponse)throw Error('Không chặn được phản hồi sau commit');
        await until('!__fastDialog.get_primary_btn().prop("disabled")');
        const requestId=new URLSearchParams(lostResponse.request.postData).get('request_id');
        if(!requestId)throw Error('Thiếu token của yêu cầu đã chặn phản hồi');
        await evaluate('frappe.msg_dialog?.hide();true');
        const notes = await evaluate(`frappe.call({method:'frappe.client.get_list',args:{doctype:'Delivery Note',filters:{kh_aph_don_chung_xuat:${JSON.stringify(source)},kh_aph_dot_xuat:${JSON.stringify(requestId)}},fields:['name','docstatus','kh_aph_delivery_state'],limit_page_length:0}}).then(r=>r.message)`);
        if(notes.length!==1||notes[0].docstatus!==1||notes[0].kh_aph_delivery_state!=='Khách đã nhận')throw Error('Yêu cầu bị mất phản hồi chưa commit đúng: '+JSON.stringify(notes));
        const ledgerCounts = () => evaluate(`Promise.all(['Delivery Note','Sales Invoice','GL Entry','Stock Ledger Entry'].map(doctype=>frappe.call({method:'frappe.client.get_list',args:{doctype,fields:['name'],limit_page_length:0}}).then(r=>r.message.length)))`);
        const before=await ledgerCounts();
        await command('Fetch.disable');
        await evaluate('__fastDialog.get_primary_btn().trigger("click");true');
        await until('!__fastDialog.$wrapper.is(":visible")');
        const after=await ledgerCounts();
        if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Thử lại sau mất phản hồi đã ghi sổ lần nữa');
        const screenshot=await command('Page.captureScreenshot',{format:'png'});
        fs.writeFileSync('xuat-ngay-retry.png',Buffer.from(screenshot.data,'base64'));
        console.log(JSON.stringify({case:'NATIVE_DESK_XUAT_NGAY_LOST_RESPONSE',status:'PASS',detail:{response_dropped_after_200:true,committed_note:notes[0].name,same_dialog_retry:true,ledger_unchanged:true}}));
    } else if (mode === 'chenh-lech') {
        await command('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
        await command('Page.navigate',{url:base+'/desk/delivery-note/'+encodeURIComponent(source)});
        await until('!!window.cur_frm && cur_frm.doctype === "Delivery Note" && cur_frm.doc.kh_aph_chenh_lech_state === "Đang xử lý"');
        await until('!!cur_frm.custom_buttons["Chốt xử lý chênh lệch"]');
        await evaluate('cur_frm.custom_buttons["Chốt xử lý chênh lệch"].trigger("click");true');
        await until('!!window.cur_dialog && !!cur_dialog.fields_dict.cach_xu_ly && cur_dialog.$wrapper.is(":visible")');
        await evaluate('cur_dialog.set_value("cach_xu_ly", "Phiếu trả hàng");true');
        const view = await evaluate('({state:cur_frm.doc.kh_aph_chenh_lech_state,assignee:cur_frm.doc.kh_aph_chenh_lech_phu_trach,title:cur_dialog.title,required:cur_dialog.fields_dict.ket_qua.df.reqd,returnVisible:cur_dialog.fields_dict.phieu_tra.$wrapper.is(":visible"),options:cur_dialog.fields_dict.cach_xu_ly.df.options})');
        if(!view.assignee || !view.required || !view.returnVisible || !view.options.includes('Hóa đơn giảm'))throw Error('Sai Dialog chênh lệch: '+JSON.stringify(view));
        const screenshot=await command('Page.captureScreenshot',{format:'png'});
        fs.writeFileSync('chenh-lech-giao-nhan.png',Buffer.from(screenshot.data,'base64'));
        console.log(JSON.stringify({case:'NATIVE_DESK_CHENH_LECH',status:'PASS',detail:view}));
    } else if (mode === 'ho-so') {
        await command('Page.navigate',{url:base+'/desk/delivery-note/'+encodeURIComponent(source)});
        await until('!!window.cur_frm && cur_frm.doctype === "Delivery Note" && cur_frm.doc.docstatus === 1');
        await until('!!cur_frm.custom_buttons["Đối chiếu bản ký"]');
        const view = await evaluate('({file:cur_frm.doc.kh_aph_ban_ky,reviewer:cur_frm.doc.kh_aph_doi_chieu_boi,section:cur_frm.fields_dict.kh_aph_ho_so_giao_nhan.$wrapper.is(":visible"),remove:!!cur_frm.custom_buttons["Gỡ bản ký khỏi phiếu"]})');
        if(!view.file?.startsWith('/private/files/') || view.reviewer || !view.section || !view.remove)throw Error('Sai hồ sơ trên form: '+JSON.stringify(view));
        const screenshot=await command('Page.captureScreenshot',{format:'png'});
        fs.writeFileSync('ho-so-giao-nhan.png',Buffer.from(screenshot.data,'base64'));
        console.log(JSON.stringify({case:'NATIVE_DESK_HO_SO_GIAO_NHAN',status:'PASS',detail:view}));
    } else {
    await command('Page.navigate',{url:base+'/desk/aph-shared-sales-order/'+encodeURIComponent(source)});
    await until('!!window.cur_frm && cur_frm.doctype === "APH Shared Sales Order" && cur_frm.doc.docstatus === 1');
    await until('!!cur_frm.custom_buttons["Lập phiếu xuất & In"]');
    await evaluate('cur_frm.custom_buttons["Lập phiếu xuất & In"].trigger("click");true');
    await until('!!window.cur_dialog && cur_dialog.fields_dict.rows && cur_dialog.$wrapper.is(":visible")');
    const view=await evaluate('({title:cur_dialog.title,rows:cur_dialog.fields_dict.rows.df.data.map(r=>({qty:r.qty,remaining:r.remaining_qty,draft:r.draft_qty})),button:cur_dialog.get_primary_btn().text(),deliveryFields:["delivery_method","recipient","phone","driver_name","vehicle_no","shipping_address_name"].map(k=>({name:k,visible:!!cur_dialog.fields_dict[k]?.$wrapper.is(":visible")})),method:cur_dialog.get_value("delivery_method"),recipientRequired:cur_dialog.fields_dict.recipient.df.reqd})');
    if(view.rows.length!==1 || view.rows[0].qty!==0 || view.rows[0].remaining!==15 || view.rows[0].draft!==5)throw Error('Sai lượng trên Dialog: '+JSON.stringify(view));
    if(!view.button.includes('Lập phiếu'))throw Error('Thiếu hành động chính');
    if(view.deliveryFields.length!==6 || view.deliveryFields.some(f=>!f.visible) || view.method!=="Vận chuyển" || !view.recipientRequired)throw Error('Thiếu thông tin giao nhận trong Dialog: '+JSON.stringify(view));
    const screenshot=await command('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync('ban-nhanh-dialog.png',Buffer.from(screenshot.data,'base64'));
    console.log(JSON.stringify({case:'NATIVE_DESK_BAN_NHANH_DIALOG',status:'PASS',detail:view}));

    }

} finally {
    if(ws)ws.close();
    chrome.kill('SIGTERM');await pause(250);
    try{fs.rmSync(profile,{recursive:true,force:true});}catch{}
}
