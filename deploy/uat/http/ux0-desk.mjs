// CI-only native Desk test using the runner's Chrome and Node WebSocket CDP.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {setTimeout as pause} from 'node:timers/promises';
if (process.env.GITHUB_ACTIONS !== 'true') throw Error('Disposable GitHub UAT only');
const state = JSON.parse(fs.readFileSync(fs.readFileSync(path.join(os.homedir(), 'APHVH_HTTP_UAT_STATE_PATH.txt'), 'utf8').trim(), 'utf8'));
if (state.site !== 'aphvh-web-uat' || state.container !== 'aphvh-p0-web-uat' || state.port !== 18091) throw Error('Wrong UAT');
const [source] = process.argv.slice(2);
if (!source) throw Error("Thiếu dữ liệu UX-0");
const base = 'http://127.0.0.1:18091';
let cookies;
if (false) {
    // Cookie phiên nhân sự giả chỉ qua stdin, không lưu hoặc đưa lên log/argv.
    cookies = JSON.parse(fs.readFileSync(0, 'utf8')).cookies;
    if (!Array.isArray(cookies) || !cookies.length || cookies.some(c => c.url !== base)) throw Error('Wrong disposable browser session');
} else {
    const login = await fetch(base + '/api/method/login', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({usr:'Administrator',pwd:state.admin_password})});
    if (!login.ok || (await login.json()).message !== 'Logged In') throw Error('UAT browser login failed');
    cookies = login.headers.getSetCookie().map(s => s.split(';')[0]).map(s => {let n=s.indexOf('=');return {name:s.slice(0,n),value:s.slice(n+1),url:base}});
}
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'aphvh-ux0-'));
const chrome = spawn('google-chrome', ['--headless','--no-sandbox','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--remote-debugging-address=127.0.0.1','--remote-debugging-port=19231','--user-data-dir='+profile,'about:blank'], {stdio:'ignore'});
let ws, sequence=0;
let lostResponse = null;
const waiting=new Map();
const diagnostics=[];
try {
    let tab;
    for(let i=0;i<50;i++) {try {tab=(await (await fetch('http://127.0.0.1:19231/json/list')).json()).find(t=>t.type==='page');if(tab)break;} catch {} await pause(200);}
    if(!tab)throw Error('Chrome did not start');
    ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise((ok,no)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',no,{once:true});});
    ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')diagnostics.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.method==='Network.responseReceived'&&m.params.response.status>=400)diagnostics.push(m.params.response.status+' '+m.params.response.url.slice(0,180));if(m.method==='Fetch.requestPaused'){if(!lostResponse&&m.params.responseStatusCode===200){lostResponse=m.params;command('Fetch.failRequest',{requestId:m.params.requestId,errorReason:'Aborted'}).catch(e=>diagnostics.push(e.message));}else command('Fetch.continueRequest',{requestId:m.params.requestId}).catch(e=>diagnostics.push(e.message));}const p=waiting.get(m.id);if(p){waiting.delete(m.id);clearTimeout(p.timer);m.error?p.no(Error(m.error.message)):p.ok(m.result);}});
    const command=(method,params={})=>new Promise((ok,no)=>{const id=++sequence;const timer=setTimeout(()=>{waiting.delete(id);no(Error('CDP timeout: '+method));},30000);waiting.set(id,{ok,no,timer});ws.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const r=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result?.value;};
    const until=async expression=>{for(let i=0;i<180;i++){if(await evaluate(expression))return;await pause(350);}throw Error('Desk condition not met: '+expression+'; state='+JSON.stringify(await evaluate('({url:location.href,frappe:!!window.frappe,user:window.frappe?.session?.user,doctype:window.cur_frm?.doctype})'))+'; errors='+JSON.stringify(diagnostics.slice(-8)));};
    await command('Page.enable');await command('Runtime.enable');await command('Network.enable');await command('Network.setCookies',{cookies});
    // UX-0: số đo MÁY (số thao tác, số màn hình, thời gian chạy) trên cùng dữ liệu UAT, đường A = Desk hiện tại, B = UX-01.
    // Không thay người thật: thời gian đọc/suy nghĩ, số lần hỏi, bấm nhầm đo ở nghiệm thu cuối. Chỉ mở tới hộp thao tác rồi đóng, không ghi.
    const data = JSON.parse(source);
    await command('Emulation.setDeviceMetricsOverride',{width:1366,height:900,deviceScaleFactor:1,mobile:false});
    await command('Page.navigate',{url:base+'/desk'});
    await until('!!window.frappe?.router && !!frappe.boot?.kh_aph');
    if(!await evaluate('!!frappe.boot.kh_aph.ux_task_first'))throw Error('Cờ UX chưa bật trên UAT');
    await evaluate('window.__ux={screens:0};frappe.router.on("change",()=>window.__ux.screens++);true');
    const ket={};
    const route=async (args,cho)=>{await evaluate(`frappe.set_route(...${JSON.stringify(args)});true`);await until(cho);return 1;};
    const nut=async label=>{
        // Nút trong nhóm cần mở menu trước: tính 2 thao tác.
        const nhom=await evaluate(`(()=>{const b=cur_frm.custom_buttons[${JSON.stringify(label)}];if(!b||!b.length)return -1;return b.closest('.dropdown-menu').length?2:1;})()`);
        if(nhom<0)throw Error('Không thấy nút '+label+' trên '+await evaluate('cur_frm.doctype'));
        await evaluate(`cur_frm.custom_buttons[${JSON.stringify(label)}].trigger("click");true`);return nhom;};
    const banner=async ()=>{await until('!!document.querySelector("[id^=kh-aph-viec-] button.btn-primary")');
        await evaluate('document.querySelector("[id^=kh-aph-viec-] button.btn-primary").click();true');return 1;};
    const xong=async ()=>{await until('!!window.cur_dialog && cur_dialog.$wrapper.is(":visible") || !!document.querySelector(".modal.show")');
        await evaluate('cur_dialog?.hide();$(".modal.show").modal("hide");true');await pause(400);};
    const do_=async (ten,buoc)=>{await evaluate('window.__ux.screens=0;true');const t0=Date.now();let thao_tac=0;
        for(const b of buoc)thao_tac+=await b();return {thao_tac,man_hinh:await evaluate('window.__ux.screens'),ms:Date.now()-t0};};
    const vao=t=>route(['Workspaces',t],`frappe.get_route()[0]==='Workspaces' && !!document.querySelector('.shortcut-widget-box')`);
    const form=(dt,n)=>route(['Form',dt,n],`!!window.cur_frm && cur_frm.doc.name===${JSON.stringify(n)} && frappe.request.ajax_count===0`);
    const list=dt=>route(['List',dt],`frappe.get_route()[0]==='List' && frappe.get_route()[1]===${JSON.stringify(dt)}`);
    const report=r=>route(['query-report',r],`frappe.get_route()[0]==='query-report' && !!frappe.query_report && frappe.request.ajax_count===0`);
    if(data.order){
        ket.T01={A:await do_('A',[()=>vao('Trung tâm Bán hàng'),()=>list('APH Shared Sales Order'),()=>form('APH Shared Sales Order',data.order),()=>nut('Lập phiếu xuất & In'),async()=>{await xong();return 0;}]),
                 B:await do_('B',[()=>vao('Việc bán hàng'),()=>list('APH Shared Sales Order'),()=>form('APH Shared Sales Order',data.order),banner,async()=>{await xong();return 0;}])};
    }
    ket.T02={A:await do_('A',[()=>vao('Trung tâm Bán hàng'),()=>list('Sales Invoice'),()=>form('Sales Invoice',data.invoice),()=>nut('Thu tiền'),async()=>{await xong();return 0;}]),
             B:await do_('B',[()=>vao('Việc tiền và công nợ'),()=>list('Sales Invoice'),()=>form('Sales Invoice',data.invoice),banner,async()=>{await xong();return 0;}])};
    const shot=await command('Page.captureScreenshot',{format:'png'});fs.writeFileSync('ux-buoc-tiep.png',Buffer.from(shot.data,'base64'));
    ket.T03={A:await do_('A',[()=>vao('Trung tâm Bán hàng'),()=>report('Tong hop ban hang theo khach')]),
             B:await do_('B',[()=>vao('Việc bán hàng'),()=>report('Tong hop ban hang theo khach')])};
    await vao('Việc bán hàng');
    const shot2=await command('Page.captureScreenshot',{format:'png'});fs.writeFileSync('ux-viec-ban-hang.png',Buffer.from(shot2.data,'base64'));
    console.log(JSON.stringify({case:'DESK_UX0_BASELINE',status:'PASS',detail:{loai_so_do:'máy, không phải người thật',ket_qua:ket,
        don:data.order||'không có đơn còn hàng: T01 chưa đo'}}));
} catch (exc) {
    console.error(String(exc && exc.stack || exc)); console.error(JSON.stringify(diagnostics.slice(-10)));
    process.exitCode = 1;
} finally {
    try { ws?.close(); } catch {}
    chrome.kill('SIGKILL');
    fs.rmSync(profile, {recursive:true, force:true});
}
