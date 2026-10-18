import traceback
import json, os, secrets, subprocess, uuid, time
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order","Purchase Receipt","Purchase Invoice","Landed Cost Voucher","Repost Item Valuation","APH Pending Receipt","APH Pending Receipt Item","APH Bag Movement","APH Shared Sales Order","APH Shared Sales Order Item","Custom Field","Version","BOM","Work Order","Journal Entry","Account","APH Funds Route","APH Funds Receipt","APH Funds Action","Comment"]
root_secret=""
token_secret=""
factory_password=secrets.token_urlsafe(32)
def run(args,input=None):
    p=subprocess.run(args,input=input,text=True,capture_output=True)
    if p.returncode:
        message=(p.stdout+p.stderr)[-3500:]
        for secret in (root_secret,factory_password,token_secret,state.get("admin_password","")):
            if secret: message=message.replace(secret,"[REDACTED]")
        raise RuntimeError(message)
    return p.stdout

def inner(code,input=None):
    return run(["docker","exec","-i","-w",ROOT+"/sites",WEB,ROOT+"/env/bin/python","-c",code],input)

snapshot_code='''import json,frappe
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
try:
 print("SNAPSHOT:"+json.dumps({"counts":{dt:frappe.db.count(dt) for dt in TRACKED},"series":frappe.db.sql("SELECT name,current FROM `tabSeries` ORDER BY name")}))
finally:frappe.destroy()
'''.replace('for dt in TRACKED','for dt in '+repr(TRACKED))
def snapshot():
    raw=inner(snapshot_code)
    return json.loads(next(x[9:] for x in raw.splitlines() if x.startswith("SNAPSHOT:")))
def session(user,password):
    op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(method,args=None):
        data=urllib.parse.urlencode(args).encode() if args is not None else None
        req=urllib.request.Request("http://127.0.0.1:18091"+method,data=data,
            headers={"Host":SITE,"X-Frappe-Site-Name":SITE})
        with op.open(req,timeout=30) as res:return json.load(res)
    call("/api/method/login",{"usr":user,"pwd":password})
    assert call("/api/method/frappe.auth.get_logged_user")["message"]==user
    return call

def emit(case,status,detail):
    print(json.dumps({"case":case,"status":status,"detail":detail},ensure_ascii=False),flush=True)

state=json.loads(Path((Path.home()/"APHVH_HTTP_UAT_STATE_PATH.txt").read_text().strip()).read_text())
assert state["site"]==SITE and state["container"]==WEB and state["port"]==18091
info=json.loads(run(["docker","inspect",WEB]))[0]
assert info["HostConfig"]["PortBindings"]["8000/tcp"]==[{"HostIp":"127.0.0.1","HostPort":"18091"}]
source=Path(next(m["Source"] for m in info["Mounts"] if m["Destination"]==ROOT+"/sites"))
assert source==Path(state["sites_directory"]) and not (source/"frontend").exists()
assert source.parent.name.startswith("aphvh-http-uat-")
env=dict(x.split("=",1) for x in json.loads(run(["docker","inspect",DB]))[0]["Config"]["Env"] if "=" in x)
root_secret=env.get("MARIADB_ROOT_PASSWORD") or env.get("MYSQL_ROOT_PASSWORD")
if not root_secret:
    file=env.get("MARIADB_ROOT_PASSWORD_FILE") or env.get("MYSQL_ROOT_PASSWORD_FILE")
    if file:root_secret=run(["docker","exec",DB,"cat",file]).rstrip("\n")
assert root_secret,"No restore credential; no fixture created"
before=snapshot()
for dt in ("Customer","Item","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry"):
    assert before["counts"][dt]==0,dt+" not blank"
admin=session("Administrator",state["admin_password"])
run(["docker","exec","-w",ROOT,WEB,"bench","--site",SITE,"backup"])
backup_dir=source/SITE/"private"/"backups"
backup=max(backup_dir.glob("*-database.sql.gz"),key=lambda p:p.stat().st_mtime)
assert backup.stat().st_size>0
restore_path="/tmp/aphvh-http-cost-"+uuid.uuid4().hex+".sql.gz"
run(["docker","cp",str(backup),BACKEND+":"+restore_path])
# Verify destination before committing fixtures.
run(["docker","exec",BACKEND,"test","-s",restore_path])
restore_record=source.parent/"funds_uat_restore.json"
restore_record.write_text(json.dumps({"site":SITE,"backup":str(backup),"backend_path":restore_path,"before":before},indent=2))
os.chmod(restore_record,0o600)
try:
    fixture_code = "import json,sys,uuid,frappe\nfrom frappe.utils import today\nfrom frappe.utils.password import update_password\nfrom kh_aph.constants import INV_FLAG,INV_NO,ROLE_FACTORY,ROLE_NO_COST,IG_FIXED_RATE\nfrappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')\np='UAT-INV-'+uuid.uuid4().hex[:8]; payload=json.load(sys.stdin)\ncompanies={a:frappe.get_doc('Company',frappe.db.get_value('Company',{'abbr':a},'name')) for a in ('APH','VH','MK','TL')}\nwarehouses={}\nfor a,co in companies.items():\n warehouses[a]=frappe.get_doc({'doctype':'Warehouse','warehouse_name':p+'-'+a,'company':co.name,'is_group':0,'parent_warehouse':frappe.db.get_value('Warehouse',{'company':co.name,'is_group':1},'name'),'account':co.default_inventory_account}).insert().name\ngroup=frappe.get_doc({'doctype':'Item Group','item_group_name':p,'parent_item_group':'HH - Hàng hóa','is_group':0}).insert().name\nfixed=frappe.get_doc({'doctype':'Item Group','item_group_name':p+'-FIXED','parent_item_group':'HH - Hàng hóa','is_group':0,IG_FIXED_RATE:1}).insert().name\nsupplier=frappe.get_doc({'doctype':'Supplier','supplier_name':p,'supplier_type':'Company','supplier_group':frappe.db.get_value('Supplier Group',{'is_group':0},'name')}).insert().name\ncustomer=frappe.get_doc({'doctype':'Customer','customer_name':p,'customer_type':'Company','customer_group':frappe.db.get_value('Customer Group',{'is_group':0},'name'),'territory':frappe.db.get_value('Territory',{'is_group':0},'name'),INV_FLAG:INV_NO}).insert()\ntaxes=[]\nfor a in ('APH','VH'):\n co=companies[a];tax=frappe.get_doc({'doctype':'Item Tax Template','title':p+'-'+a+'-10','company':co.name,'taxes':[{'tax_type':frappe.db.get_value('Account',{'company':co.name,'account_number':'33311','is_group':0},'name'),'tax_rate':10}]}).insert()\n taxes.append({'item_tax_template':tax.name,'tax_category':customer.tax_category})\nitems={}\nfor label,weight in [('trade',0),('raw',25),('fg',10),('by',5),('fixed',5)]:\n item=frappe.get_doc({'doctype':'Item','item_code':p+'-'+label,'item_name':p+'-'+label,'item_group':fixed if label=='fixed' else group,'stock_uom':'Kg','is_stock_item':1,'valuation_method':'Moving Average','kh_aph_kg_per_bag':weight,'taxes':taxes,'item_defaults':[{'company':co.name,'default_warehouse':warehouses[a],'income_account':co.default_income_account,'expense_account':co.default_expense_account,'buying_cost_center':co.cost_center,'selling_cost_center':co.cost_center} for a,co in companies.items()]}).insert()\n items[label]=item.name\nu=frappe.get_doc({'doctype':'User','email':p.lower()+'@example.invalid','first_name':'Dũng UAT kho','enabled':1,'user_type':'System User','send_welcome_email':0,'roles':[{'role':ROLE_FACTORY},{'role':ROLE_NO_COST}]});u.flags.no_welcome_mail=True;u.insert();update_password(u.name,payload['password'])\n\ndef make_account(label,co,root,account_type=''):\n parent=frappe.db.get_value('Account',{'company':co,'root_type':root,'is_group':1,'parent_account':['is','not set']},'name')\n return frappe.get_doc({'doctype':'Account','account_name':p+'-'+label,'company':co,'root_type':root,'report_type':'Balance Sheet','parent_account':parent,'account_currency':'VND','account_type':account_type,'is_group':0}).insert().name\nbank=make_account('BANK',companies['APH'].name,'Asset','Bank')\nholding=make_account('HOLDING',companies['APH'].name,'Liability')\ndue=make_account('DUE-APH',companies['TL'].name,'Asset')\nowner_bank=make_account('OWNER-BANK',companies['TL'].name,'Asset','Bank')\nau=frappe.get_doc({'doctype':'User','email':p.lower()+'-au@example.invalid','first_name':'UAT Accounts User','enabled':1,'user_type':'System User','send_welcome_email':0,'roles':[{'role':'Accounts User'}]});au.flags.no_welcome_mail=True;au.insert();update_password(au.name,payload['password'])\nu.append('roles',{'role':'Accounts Manager'});u.save()\nfrappe.db.commit();print('FIXTURE:'+json.dumps({'owner_bank':owner_bank,'bank':bank,'holding':holding,'due':due,'accounts_user':au.name,'ref':p+'-BANKREF','adjustments':{a:co.stock_adjustment_account for a,co in companies.items()},'companies':{a:co.name for a,co in companies.items()},'wh':warehouses,'items':items,'supplier':supplier,'customer':customer.name,'user':u.name,'date':today(),'expense':companies['APH'].default_expense_account,'adjustment':companies['APH'].stock_adjustment_account,'cc':companies['APH'].cost_center,'ccs':{a:co.cost_center for a,co in companies.items()},'price_list':frappe.db.get_value('Price List',{'selling':1,'enabled':1},'name')}));frappe.destroy()\n"
    raw=inner(fixture_code,json.dumps({'password':factory_password}))
    f=json.loads(next(l[8:] for l in raw.splitlines() if l.startswith('FIXTURE:')))
    factory=session(f['user'],factory_password)
    def rpc(method,args=None,caller=None):return (caller or admin)('/api/method/'+method,args)['message']
    def get(dt,name):return rpc('frappe.client.get',{'doctype':dt,'name':name})
    def insert(doc,caller=None):return rpc('frappe.client.insert',{'doc':json.dumps(doc)},caller)
    def submit(doc,caller=None):return rpc('frappe.client.submit',{'doc':json.dumps(doc)},caller)
    def cancel(dt,name):return rpc('frappe.client.cancel',{'doctype':dt,'name':name})
    def deny(action):
        try: action()
        except urllib.error.HTTPError as exc:
            error=json.loads(exc.read())
            assert error.get('exc_type') in ('ValidationError','PermissionError','NegativeStockError','LinkExistsError','MandatoryError','DuplicateEntryError','UniqueValidationError'),error
            return error.get('exc_type')
        raise AssertionError('Expected rejection')
    def route(owner=None):
        return submit(insert({'doctype':'APH Funds Route','receiving_company':f['companies']['APH'],
            'owner_company':owner,'holding_account':f['holding'],
            'due_from_account':f['due'] if owner==f['companies']['TL'] else None,'reason':'UAT explicit approved account mapping'}))
    common_route=route()
    tl_route=route(f['companies']['TL'])
    def shared(qty_aph,qty_tl):
        rows=[{'item_code':f['items']['trade'],'warehouse':f['wh'][a],'qty':q,'rate':20000}
              for a,q in [('APH',qty_aph),('TL',qty_tl)] if q]
        return submit(insert({'doctype':'APH Shared Sales Order','customer':f['customer'],
            'transaction_date':f['date'],'delivery_date':f['date'],'selling_price_list':f['price_list'],'currency':'VND','items':rows}))
    def dispatch(order,abbr,qty):
        so=rpc('frappe.client.get_list',{'doctype':'Sales Order','filters':json.dumps({'kh_aph_shared_order':order['name'],'company':f['companies'][abbr],'docstatus':1}),'fields':json.dumps(['name'])})[0]['name']
        dn=rpc('erpnext.selling.doctype.sales_order.sales_order.make_delivery_note',{'source_name':so})
        for r in dn['items']:r['qty']=qty
        dn=submit(insert(dn))
        si=rpc('frappe.client.get_list',{'doctype':'Sales Invoice Item','parent':'Sales Invoice','filters':json.dumps({'delivery_note':dn['name']}),'fields':json.dumps(['parent'])})[0]['parent']
        return get('Sales Invoice',si)
    for a in ('APH','TL'):
        submit(insert({'doctype':'Stock Entry','purpose':'Material Receipt','stock_entry_type':'Material Receipt',
            'company':f['companies'][a],'posting_date':f['date'],'items':[{'item_code':f['items']['trade'],
            'qty':100,'uom':'Kg','stock_uom':'Kg','conversion_factor':1,'t_warehouse':f['wh'][a],
            'basic_rate':10000,'expense_account':f['adjustments'][a],'cost_center':f['ccs'][a]}]}))
    old=shared(1,0);old_si=dispatch(old,'APH',1)
    main=shared(4,2);second=shared(1,1)
    aph_si=dispatch(main,'APH',1);tl_si=dispatch(main,'TL',1)
    receipt_doc={'doctype':'APH Funds Receipt','company':f['companies']['APH'],'posting_date':f['date'],
        'bank_account':f['bank'],'route':common_route['name'],'amount':100000,'external_reference':f['ref'],
        'reason':'UAT actual bank receipt, unknown payer'}
    receipt=submit(insert(receipt_doc))
    def ledger():
        raw=inner('''import json,sys,frappe
from kh_aph.global_credit import balance_for
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')
f=json.load(sys.stdin);out={}
for key in ('bank','holding','due','owner_bank'):
 out[key]=float(frappe.db.sql('SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry` WHERE account=%s AND is_cancelled=0',f[key])[0][0])
out['credit_balance']=str(balance_for(f['customer']))
out['counts']={dt:frappe.db.count(dt) for dt in ('Journal Entry','GL Entry','Payment Ledger Entry','APH Funds Receipt','APH Funds Action')}
print('LEDGER:'+json.dumps(out));frappe.destroy()
''',json.dumps(f))
        return json.loads(next(l[7:] for l in raw.splitlines() if l.startswith('LEDGER:')))
    def near(value,target):assert abs(float(value)-target)<.05,(value,target)
    near(ledger()['bank'],100000);near(ledger()['holding'],-100000)
    near(get('Sales Invoice',old_si['name'])['outstanding_amount'],20000)
    near(ledger()['credit_balance'],60000)
    emit('HTTP_FUNDS_UNKNOWN_ACTUAL_CASH','PASS','One bank receipt, holding liability; no old debt or anonymous credit-limit deduction')
    snapshot0=ledger();deny(lambda:submit(insert(receipt_doc)));assert ledger()==snapshot0
    emit('HTTP_FUNDS_RECEIPT_DUPLICATE','PASS','Duplicate stable bank reference rejected without cash/ledger changes')
    # Không cho cùng khoản thực thu đi thêm qua JE chuẩn hoặc ngược lại.
    snap_cross=ledger()
    def native_doc(reference):
        return {'doctype':'Journal Entry','company':f['companies']['APH'],'posting_date':f['date'],
            'cheque_no':reference,'cheque_date':f['date'],'accounts':[
                {'account':f['bank'],'debit_in_account_currency':1},
                {'account':f['holding'],'credit_in_account_currency':1}]}
    deny(lambda:insert(native_doc(f['ref'])))
    assert ledger()==snap_cross
    draft=insert(native_doc(f['ref']+'-native-first'))
    deny(lambda:insert({**receipt_doc,'external_reference':f['ref']+'-native-first'}))
    admin('/api/method/frappe.client.delete',{'doctype':'Journal Entry','name':draft['name']})
    assert ledger()==snap_cross
    emit('HTTP_FUNDS_CROSS_SOURCE_DUPLICATE','PASS','Native JE and Funds Receipt share one bank reference guard; no ledger drift')
    def action(kind,amount,**kw):
        return rpc('kh_aph.funds.create_action',{'values':json.dumps({'receipt':receipt['name'],'action_type':kind,
            'amount':amount,'posting_date':f['date'],'reason':'UAT explicit agreement',**kw})})
    deny(lambda:action('Giữ cọc',10000,shared_order=main['name']))
    ui_raw=run(['node','--experimental-websocket',str(Path(__file__).with_name('funds-desk.mjs')),receipt['name'],f['customer'],main['name']])
    ui=json.loads(next(l for l in ui_raw.splitlines() if l.startswith('{') and 'NATIVE_FUNDS_IDENTIFY_AND_FIGURES' in l))
    assert ui['status']=='PASS',ui
    admin=session('Administrator',state['admin_password'])
    emit('NATIVE_FUNDS_IDENTIFY_AND_FIGURES','PASS',ui['figures'])
    near(ledger()['credit_balance'],-40000);near(get('Sales Invoice',old_si['name'])['outstanding_amount'],20000)
    emit('HTTP_FUNDS_IDENTIFY_NO_OLD_DEBT_ALLOCATION','PASS','Verified unspent cash reduces global exposure only; old invoice remains unpaid')
    reserve=action('Giữ cọc',30000,shared_order=main['name'])
    source=action('Giữ cọc',20000,shared_order=main['name'],source_company=f['companies']['TL'])
    pos=rpc('kh_aph.funds.receipt_position',{'name':receipt['name']});near(pos['reserved'],50000);near(pos['available'],50000)
    emit('HTTP_FUNDS_COMMON_AND_SOURCE_DEPOSIT','PASS','Common/source reservations keep cash, old debt and bank untouched')
    snap=ledger();deny(lambda:action('Hoàn tiền',60000,bank_account=f['bank'],external_reference=f['ref']+'-too-much'));assert ledger()==snap
    emit('HTTP_FUNDS_OVERSPEND_GUARD','PASS','Reserved cash cannot be consumed as free cash')
    snap=ledger();deny(lambda:action('Cấn hóa đơn',10000,invoice=tl_si['name'],source_reservation=source['name']));assert ledger()==snap
    emit('HTTP_FUNDS_CROSS_COMPANY_NEEDS_ROUTE','PASS','No owner ledger or bank changes without approved route')
    alloc_tl=action('Cấn hóa đơn',10000,invoice=tl_si['name'],source_reservation=source['name'],route=tl_route['name'])
    near(get('Sales Invoice',tl_si['name'])['outstanding_amount'],10000)
    near(ledger()['bank'],100000);near(ledger()['holding'],-100000);near(ledger()['due'],10000)
    near(get('Sales Invoice',old_si['name'])['outstanding_amount'],20000)
    emit('HTTP_FUNDS_APH_RECEIVES_TL_PLANNED','PASS','TL debt reduced via due-from APH; no second bank posting, APH held TL money remains a liability')
    alloc_aph=action('Cấn hóa đơn',5000,invoice=aph_si['name'],source_reservation=reserve['name'])
    near(get('Sales Invoice',aph_si['name'])['outstanding_amount'],15000);near(ledger()['holding'],-95000)
    near(ledger()['credit_balance'],-40000)
    emit('HTTP_FUNDS_PARTIAL_OWN_COMPANY_ALLOCATION','PASS','Only chosen invoice reduced; unspent cash counted once in global exposure')
    settled=action('Trả tiền thu hộ',10000,source_allocation=alloc_tl['name'],bank_account=f['bank'],owner_bank_account=f['owner_bank'],external_reference=f['ref']+'-settle',owner_external_reference=f['ref']+'-owner-received')
    near(ledger()['bank'],90000);near(ledger()['owner_bank'],10000);near(ledger()['holding'],-85000);near(ledger()['due'],0)
    near(get('Sales Invoice',tl_si['name'])['outstanding_amount'],10000)
    snap=ledger();deny(lambda:cancel('APH Funds Action',alloc_tl['name']));assert ledger()==snap
    emit('HTTP_FUNDS_OWNER_ACTUAL_SETTLEMENT','PASS','Approved actual source/owner cash posted once; held liability and due-from clear; customer debt not reduced twice')
    moved=action('Chuyển cọc',5000,source_reservation=source['name'],shared_order=second['name'],source_company=f['companies']['TL'])
    released=action('Giải phóng cọc',10000,source_reservation=reserve['name'])
    refunded=action('Hoàn tiền',5000,source_reservation=moved['name'],bank_account=f['bank'],external_reference=f['ref']+'-refund')
    near(ledger()['bank'],85000);near(ledger()['holding'],-80000);near(ledger()['due'],0)
    near(ledger()['credit_balance'],-35000)
    figures=rpc('kh_aph.funds.shared_financials',{'name':main['name']})
    near(figures['remaining_to_pay'],85000);near(figures['dispatched_debt'],25000);near(figures['undelivered_value'],80000);near(figures['reserved_deposit'],20000)
    emit('HTTP_FUNDS_TRANSFER_RELEASE_REFUND_THREE_FIGURES','PASS',figures)
    snap=ledger();deny(lambda:action('Hoàn tiền',1000,bank_account=f['bank'],external_reference=f['ref']+'-refund'));assert ledger()==snap
    emit('HTTP_FUNDS_REFUND_DUPLICATE','PASS','Repeat payout reference rejected without another bank movement')
    snap=ledger();deny(lambda:cancel('APH Funds Receipt',receipt['name']));deny(lambda:cancel('Journal Entry',receipt['journal_entry']));assert ledger()==snap
    emit('HTTP_FUNDS_NATIVE_CANCEL_BYPASS','PASS','Direct JE and receipt cancellation blocked while plans remain')
    user=session(f['accounts_user'],factory_password)
    draft=insert({'doctype':'APH Funds Action','receipt':receipt['name'],'action_type':'Giải phóng cọc','amount':1,
        'source_reservation':reserve['name'],'posting_date':f['date'],'reason':'UAT unauthorized approval'},user)
    snap=ledger();deny(lambda:submit(draft,user));assert ledger()==snap
    emit('HTTP_FUNDS_UNAUTHORIZED_APPROVAL','PASS','Accounts User cannot approve plan')
    dung=session(f['user'],factory_password)
    deny(lambda:rpc('kh_aph.funds.receipt_position',{'name':receipt['name']},dung))
    emit('HTTP_FUNDS_DUNG_ROLE_COMBINATION','PASS','Explicit no-cost profile plus Accounts Manager cannot use financial control endpoints')
    rows=[{'external_reference':f['ref'],'amount':100000,'posting_date':f['date']},
          {'external_reference':f['ref']+'-unknown','amount':20000,'posting_date':f['date']}]
    snap=ledger();matches=rpc('kh_aph.funds.reconcile_rows',{'company_name':f['companies']['APH'],'bank_account':f['bank'],'rows':json.dumps(rows)});assert ledger()==snap
    assert [r['status'] for r in matches]==['Khớp','Chưa ghi thực thu'],matches
    deny(lambda:rpc('kh_aph.funds.reconcile_rows',{'company_name':f['companies']['APH'],'bank_account':f['bank'],'rows':json.dumps([rows[0],rows[0]])}))
    emit('HTTP_FUNDS_BANK_RECONCILIATION_READ_ONLY','PASS','Stable reference matched; unknown/duplicate classified without booking cash twice')
    from concurrent.futures import ThreadPoolExecutor
    candidates=[insert({'doctype':'APH Funds Action','receipt':receipt['name'],'action_type':'Hoàn tiền','amount':45000,
        'bank_account':f['bank'],'external_reference':f['ref']+'-race-'+str(i),'posting_date':f['date'],'reason':'UAT concurrent free-cash refund'}) for i in range(2)]
    clients=[session('Administrator',state['admin_password']) for _ in candidates]
    def race(pair):
        doc,client=pair
        try:return {'ok':True,'name':submit(doc,client)['name']}
        except urllib.error.HTTPError as exc:
            err=json.loads(exc.read());assert err.get('exc_type') in ('ValidationError','QueryDeadlockError'),err
            return {'ok':False,'type':err['exc_type']}
    with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(race,zip(candidates,clients)))
    assert sum(r['ok'] for r in result)==1,result
    winner=next(r['name'] for r in result if r['ok'])
    admin=session('Administrator',state['admin_password'])
    near(ledger()['bank'],40000);near(ledger()['holding'],-35000);near(ledger()['due'],0)
    emit('HTTP_FUNDS_CONCURRENT_NO_OVERSPEND','PASS',result)
    for doc in [winner,settled['name'],refunded['name'],released['name'],moved['name'],alloc_aph['name'],alloc_tl['name'],source['name'],reserve['name']]:cancel('APH Funds Action',doc)
    near(ledger()['bank'],100000);near(ledger()['holding'],-100000);near(ledger()['due'],0)
    near(get('Sales Invoice',aph_si['name'])['outstanding_amount'],20000);near(get('Sales Invoice',tl_si['name'])['outstanding_amount'],20000)
    cancel('APH Funds Receipt',receipt['name']);near(ledger()['bank'],0);near(ledger()['holding'],0);near(ledger()['due'],0)
    emit('HTTP_FUNDS_CANCEL_REVERSE','PASS','Chosen invoices restored, due-from and actual bank/holding postings reversed; old debt unchanged')
except Exception as exc:
    detail={'type':type(exc).__name__,'error':str(exc)[-2500:]}
    if isinstance(exc,urllib.error.HTTPError):
        try:
            payload=json.loads(exc.read());detail['response']={k:payload.get(k) for k in ('exc_type','exception','_server_messages')}
        except Exception:pass
    detail['traceback']=traceback.format_exc()[-2500:]
    emit('HTTP_FUNDS_RUNNER','FAIL',detail)
finally:
    # Stop only UAT web so no request can write during restoration.
    run(["docker","stop",WEB])
    try:
        run(["docker","exec","-w",ROOT,BACKEND,"bench","--site",SITE,"restore",restore_path,"--db-root-password",root_secret])
    finally:
        run(["docker","start",WEB])
    inner('''import frappe
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
try:
 frappe.connect();frappe.clear_cache()
finally:frappe.destroy()
''')
    run(["docker","restart",WEB])
    after=snapshot()
    assert before==after,"Baseline counts or Series differ after restore"
    emit("HTTP_UAT_RESTORE","PASS",{"counts":after["counts"],"series_restored":True})
print("CI HTTP suite completed; actual user identities and wider stress are outside this test.")
