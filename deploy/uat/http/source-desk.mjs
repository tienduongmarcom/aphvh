// CI-only native Desk test using the runner's Chrome and Node WebSocket CDP.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {setTimeout as pause} from 'node:timers/promises';
if (process.env.GITHUB_ACTIONS !== 'true') throw Error('Disposable GitHub UAT only');
const state = JSON.parse(fs.readFileSync(fs.readFileSync(path.join(os.homedir(), 'APHVH_HTTP_UAT_STATE_PATH.txt'), 'utf8').trim(), 'utf8'));
if (state.site !== 'aphvh-web-uat' || state.container !== 'aphvh-p0-web-uat' || state.port !== 18091) throw Error('Wrong UAT');
const [source, warehouse] = process.argv.slice(2);
if (!source || !warehouse) throw Error('Expected source order and target warehouse');
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
    await command('Page.navigate',{url:base+'/desk/aph-source-change/new-aph-source-change-1'});
    await until('!!window.cur_frm && cur_frm.doctype === "APH Source Change" && cur_frm.doc.docstatus === 0');
    await evaluate('(async()=>{await cur_frm.set_value("source_order",'+JSON.stringify(source)+');return true;})()');
    await until('!!cur_frm.custom_buttons["Chọn phần chưa giao"]');
    await evaluate('cur_frm.custom_buttons["Chọn phần chưa giao"].trigger("click");true');
    await until('!!window.cur_dialog && cur_dialog.fields_dict.line && cur_dialog.$wrapper.is(":visible")');
    await evaluate('(async()=>{const d=cur_dialog;await d.set_value("line",d.fields_dict.line.df.options.split("\\n")[0]);await d.set_value("qty",25);await d.set_value("warehouse",'+JSON.stringify(warehouse)+');await d.set_value("reason","UAT native Desk đổi nguồn nguyên bao");d.get_primary_btn().trigger("click");return true;})()');
    await until('!!cur_frm.doc.source_row && cur_frm.doc.qty === 25 && !!cur_frm.doc.target_warehouse');
    await evaluate('(async()=>{await cur_frm.save();return true;})()');
    await evaluate('(async()=>{await cur_frm.save("Submit");return true;})()');
    await until('cur_frm.doc.docstatus === 1 && !!cur_frm.doc.target_order');
    const change=await evaluate('({name:cur_frm.doc.name,target_order:cur_frm.doc.target_order,source_row:cur_frm.doc.source_row,qty:cur_frm.doc.qty,closed_source:cur_frm.doc.closed_source})');
    if(change.qty!==25 || !change.closed_source)throw Error('Full source transfer not preserved: '+JSON.stringify(change));
    console.log(JSON.stringify({case:'NATIVE_DESK_SOURCE_CHANGE_FULL',status:'PASS',change}));

} finally {
    if(ws)ws.close();
    chrome.kill('SIGTERM');await pause(250);
    try{fs.rmSync(profile,{recursive:true,force:true});}catch{}
}
