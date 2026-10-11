// CI-only native Desk test using the runner's Chrome and Node WebSocket CDP.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {setTimeout as pause} from 'node:timers/promises';
if (process.env.GITHUB_ACTIONS !== 'true') throw Error('Disposable GitHub UAT only');
const state = JSON.parse(fs.readFileSync(fs.readFileSync(path.join(os.homedir(), 'APHVH_HTTP_UAT_STATE_PATH.txt'), 'utf8').trim(), 'utf8'));
if (state.site !== 'aphvh-web-uat' || state.container !== 'aphvh-p0-web-uat' || state.port !== 18091) throw Error('Wrong UAT');
const [pending, item] = process.argv.slice(2);
if (!pending || !item) throw Error('Expected pending receipt and item fixture');
const base = 'http://127.0.0.1:18091';
const login = await fetch(base + '/api/method/login', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({usr:'Administrator',pwd:state.admin_password})});
if (!login.ok || (await login.json()).message !== 'Logged In') throw Error('UAT browser login failed');
const cookies = login.headers.getSetCookie().map(s => s.split(';')[0]).map(s => {let n=s.indexOf('=');return {name:s.slice(0,n),value:s.slice(n+1),url:base}});
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'aphvh-desk-uat-'));
const chrome = spawn('google-chrome', ['--headless','--no-sandbox','--disable-dev-shm-usage','--no-first-run','--no-default-browser-check','--remote-debugging-address=127.0.0.1','--remote-debugging-port=19229','--user-data-dir='+profile,'about:blank'], {stdio:'ignore'});
let ws, sequence=0;
const waiting=new Map();
try {
    let tab;
    for(let i=0;i<50;i++) {try {tab=(await (await fetch('http://127.0.0.1:19229/json/list')).json()).find(t=>t.type==='page');if(tab)break;} catch {} await pause(200);}
    if(!tab)throw Error('Chrome did not start');
    ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise((ok,no)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',no,{once:true});});
    ws.addEventListener('message',e=>{const m=JSON.parse(e.data);const p=waiting.get(m.id);if(p){waiting.delete(m.id);clearTimeout(p.timer);m.error?p.no(Error(m.error.message)):p.ok(m.result);}});
    const command=(method,params={})=>new Promise((ok,no)=>{const id=++sequence;const timer=setTimeout(()=>{waiting.delete(id);no(Error('CDP timeout: '+method));},30000);waiting.set(id,{ok,no,timer});ws.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const r=await command('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result?.value;};
    const until=async expression=>{for(let i=0;i<180;i++){if(await evaluate(expression))return;await pause(350);}throw Error('Desk condition not met: '+expression);};
    await command('Page.enable');await command('Network.enable');await command('Network.setCookies',{cookies});
    await command('Page.navigate',{url:base+'/desk/aph-pending-receipt/'+encodeURIComponent(pending)});
    await until('!!window.cur_frm && cur_frm.doctype === "APH Pending Receipt" && cur_frm.doc.docstatus === 1 && !!cur_frm.custom_buttons["Chốt giá nhập"]');
    if(!(await evaluate('!!frappe.boot.kh_aph.quantity_valuation_mvp')))throw Error('Quantity boot flag missing');
    await evaluate('cur_frm.custom_buttons["Chốt giá nhập"].trigger("click");true');
    await until('!!window.cur_dialog && cur_dialog.fields_dict.rates && cur_dialog.$wrapper.is(":visible")');
    await evaluate('(async()=>{for(const r of cur_dialog.fields_dict.rates.df.data)r.rate=10000;cur_dialog.fields_dict.rates.grid.refresh();await cur_dialog.set_value("reason","UAT native Desk chốt giá");cur_dialog.get_primary_btn().trigger("click");return true;})()');
    await until('!!cur_frm.doc.purchase_receipt && cur_frm.doc.status === "Đã định giá"');
    const receipt=await evaluate('cur_frm.doc.purchase_receipt');
    await evaluate('frappe.new_doc("APH Shared Sales Order");true');
    await until('!!window.cur_frm && cur_frm.doctype === "APH Shared Sales Order" && cur_frm.doc.docstatus === 0 && !!cur_frm.fields_dict.items');
    const quantity=await evaluate('(async()=>{const r=cur_frm.add_child("items");await frappe.model.set_value(r.doctype,r.name,"item_code",'+JSON.stringify(item)+');await frappe.model.set_value(r.doctype,r.name,"rate",20000);await frappe.model.set_value(r.doctype,r.name,"kh_aph_bags",3);cur_frm.refresh_field("items");return {qty:r.qty,bags:r.kh_aph_bags,weight:r.kh_aph_kg_per_bag,rate_bag:r.kh_aph_bag_rate,grid:cur_frm.fields_dict.items.$wrapper.text().includes("75")};})()');
    if(quantity.qty!==75 || quantity.rate_bag!==500000 || quantity.weight!==25 || !quantity.grid)throw Error('Desk bag conversion failed: '+JSON.stringify(quantity));
    console.log(JSON.stringify({case:'NATIVE_DESK_FINALIZE_AND_BAG_PREVIEW',status:'PASS',receipt,quantity}));
} finally {
    if(ws)ws.close();
    chrome.kill('SIGTERM');await pause(250);
    try{fs.rmSync(profile,{recursive:true,force:true});}catch{}
}
