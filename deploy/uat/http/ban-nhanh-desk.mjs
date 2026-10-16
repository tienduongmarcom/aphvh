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
if (!source) throw Error('Thiếu mã đơn chung UAT');
const base = 'http://127.0.0.1:18091';
const login = await fetch(base + '/api/method/login', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({usr:'Administrator',pwd:state.admin_password})});
if (!login.ok || (await login.json()).message !== 'Logged In') throw Error('UAT browser login failed');
const cookies = login.headers.getSetCookie().map(s => s.split(';')[0]).map(s => {let n=s.indexOf('=');return {name:s.slice(0,n),value:s.slice(n+1),url:base}});
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'aphvh-desk-uat-'));
const chrome = spawn('google-chrome', ['--headless','--no-sandbox','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--remote-debugging-address=127.0.0.1','--remote-debugging-port=19229','--user-data-dir='+profile,'about:blank'], {stdio:'ignore'});
let ws, sequence=0;
const waiting=new Map();
const diagnostics=[];
try {
    let tab;
    for(let i=0;i<50;i++) {try {tab=(await (await fetch('http://127.0.0.1:19229/json/list')).json()).find(t=>t.type==='page');if(tab)break;} catch {} await pause(200);}
    if(!tab)throw Error('Chrome did not start');
    ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise((ok,no)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',no,{once:true});});
    ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')diagnostics.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);if(m.method==='Network.responseReceived'&&m.params.response.status>=400)diagnostics.push(m.params.response.status+' '+m.params.response.url.slice(0,180));const p=waiting.get(m.id);if(p){waiting.delete(m.id);clearTimeout(p.timer);m.error?p.no(Error(m.error.message)):p.ok(m.result);}});
    const command=(method,params={})=>new Promise((ok,no)=>{const id=++sequence;const timer=setTimeout(()=>{waiting.delete(id);no(Error('CDP timeout: '+method));},30000);waiting.set(id,{ok,no,timer});ws.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const r=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result?.value;};
    const until=async expression=>{for(let i=0;i<180;i++){if(await evaluate(expression))return;await pause(350);}throw Error('Desk condition not met: '+expression+'; state='+JSON.stringify(await evaluate('({url:location.href,frappe:!!window.frappe,user:window.frappe?.session?.user,doctype:window.cur_frm?.doctype})'))+'; errors='+JSON.stringify(diagnostics.slice(-8)));};
    await command('Page.enable');await command('Runtime.enable');await command('Network.enable');await command('Network.setCookies',{cookies});
    await command('Page.navigate',{url:base+'/desk/aph-shared-sales-order/'+encodeURIComponent(source)});
    await until('!!window.cur_frm && cur_frm.doctype === "APH Shared Sales Order" && cur_frm.doc.docstatus === 1');
    await until('!!cur_frm.custom_buttons["Lập phiếu xuất & In"]');
    await evaluate('cur_frm.custom_buttons["Lập phiếu xuất & In"].trigger("click");true');
    await until('!!window.cur_dialog && cur_dialog.fields_dict.rows && cur_dialog.$wrapper.is(":visible")');
    const view=await evaluate('({title:cur_dialog.title,rows:cur_dialog.fields_dict.rows.df.data.map(r=>({qty:r.qty,remaining:r.remaining_qty,draft:r.draft_qty})),button:cur_dialog.get_primary_btn().text()})');
    if(view.rows.length!==1 || view.rows[0].qty!==0 || view.rows[0].remaining!==15 || view.rows[0].draft!==5)throw Error('Sai lượng trên Dialog: '+JSON.stringify(view));
    if(!view.button.includes('Lập phiếu'))throw Error('Thiếu hành động chính');
    const screenshot=await command('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync('ban-nhanh-dialog.png',Buffer.from(screenshot.data,'base64'));
    console.log(JSON.stringify({case:'NATIVE_DESK_BAN_NHANH_DIALOG',status:'PASS',detail:view}));

} finally {
    if(ws)ws.close();
    chrome.kill('SIGTERM');await pause(250);
    try{fs.rmSync(profile,{recursive:true,force:true});}catch{}
}
