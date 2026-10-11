import traceback
import json, os, secrets, subprocess, uuid, time
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order","Purchase Receipt","Purchase Invoice","Landed Cost Voucher","Repost Item Valuation","APH Pending Receipt","APH Pending Receipt Item","APH Bag Movement","APH Shared Sales Order","APH Shared Sales Order Item","Custom Field","Version"]
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
restore_record=source.parent/"cost_uat_restore.json"
restore_record.write_text(json.dumps({"site":SITE,"backup":str(backup),"backend_path":restore_path,"before":before},indent=2))
os.chmod(restore_record,0o600)
try:
    # Fixture masters only; all business documents below go through authenticated HTTP.
    fixture_code = '''import json,sys,uuid,frappe
from frappe.utils import today
from frappe.utils.password import update_password
from kh_aph.constants import INV_FLAG,INV_NO,ROLE_FACTORY,ROLE_NO_COST,IG_FIXED_RATE
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')
p='UAT-INV-'+uuid.uuid4().hex[:8]; payload=json.load(sys.stdin)
companies={a:frappe.get_doc('Company',frappe.db.get_value('Company',{'abbr':a},'name')) for a in ('APH','VH','MK','TL')}
warehouses={}
for a,co in companies.items():
 warehouses[a]=frappe.get_doc({'doctype':'Warehouse','warehouse_name':p+'-'+a,'company':co.name,'is_group':0,'parent_warehouse':frappe.db.get_value('Warehouse',{'company':co.name,'is_group':1},'name'),'account':co.default_inventory_account}).insert().name
group=frappe.get_doc({'doctype':'Item Group','item_group_name':p,'parent_item_group':'HH - Hàng hóa','is_group':0}).insert().name
fixed=frappe.get_doc({'doctype':'Item Group','item_group_name':p+'-FIXED','parent_item_group':'HH - Hàng hóa','is_group':0,IG_FIXED_RATE:1}).insert().name
supplier=frappe.get_doc({'doctype':'Supplier','supplier_name':p,'supplier_type':'Company','supplier_group':frappe.db.get_value('Supplier Group',{'is_group':0},'name')}).insert().name
customer=frappe.get_doc({'doctype':'Customer','customer_name':p,'customer_type':'Company','customer_group':frappe.db.get_value('Customer Group',{'is_group':0},'name'),'territory':frappe.db.get_value('Territory',{'is_group':0},'name'),INV_FLAG:INV_NO}).insert()
taxes=[]
for a in ('APH','VH'):
 co=companies[a];tax=frappe.get_doc({'doctype':'Item Tax Template','title':p+'-'+a+'-10','company':co.name,'taxes':[{'tax_type':frappe.db.get_value('Account',{'company':co.name,'account_number':'33311','is_group':0},'name'),'tax_rate':10}]}).insert()
 taxes.append({'item_tax_template':tax.name,'tax_category':customer.tax_category})
items={}
for label,weight in [('trade',25),('raw',25),('fg',10),('by',5),('fixed',5)]:
 item=frappe.get_doc({'doctype':'Item','item_code':p+'-'+label,'item_name':p+'-'+label,'item_group':fixed if label=='fixed' else group,'stock_uom':'Kg','is_stock_item':1,'valuation_method':'Moving Average','kh_aph_kg_per_bag':weight,'taxes':taxes,'item_defaults':[{'company':co.name,'default_warehouse':warehouses[a],'income_account':co.default_income_account,'expense_account':co.default_expense_account,'buying_cost_center':co.cost_center,'selling_cost_center':co.cost_center} for a,co in companies.items()]}).insert()
 items[label]=item.name
u=frappe.get_doc({'doctype':'User','email':p.lower()+'@example.invalid','first_name':'Dũng UAT kho','enabled':1,'user_type':'System User','send_welcome_email':0,'roles':[{'role':ROLE_FACTORY},{'role':ROLE_NO_COST}]});u.flags.no_welcome_mail=True;u.insert();update_password(u.name,payload['password'])
frappe.db.commit();print('FIXTURE:'+json.dumps({'companies':{a:co.name for a,co in companies.items()},'wh':warehouses,'items':items,'supplier':supplier,'customer':customer.name,'user':u.name,'date':today(),'expense':companies['APH'].default_expense_account,'adjustment':companies['APH'].stock_adjustment_account,'cc':companies['APH'].cost_center,'price_list':frappe.db.get_value('Price List',{'selling':1,'enabled':1},'name')}));frappe.destroy()
'''
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
            assert error.get('exc_type') in ('ValidationError','PermissionError','NegativeStockError','LinkExistsError','MandatoryError'),error
            return error.get('exc_type')
        raise AssertionError('Expected rejection')
    oracle_code='''import json,sys,frappe
from kh_aph.bag_stock import balance
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
f=json.load(sys.stdin);out={}
for a,wh in f['wh'].items():
 out[a]={}
 for label,item in f['items'].items():
  row=frappe.db.get_value('Bin',{'item_code':item,'warehouse':wh},['actual_qty','valuation_rate','stock_value'],as_dict=True) or {}
  out[a][label]={**row,'bags':balance(item,wh)}
out['counts']={dt:frappe.db.count(dt) for dt in ('Purchase Receipt','Stock Ledger Entry','GL Entry','APH Bag Movement')}
out['customer_debt']=float(frappe.db.sql("SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry` WHERE party_type='Customer' AND party=%s AND is_cancelled=0",f['customer'])[0][0])
print('ORACLE:'+json.dumps(out,default=str));frappe.destroy()
'''
    def oracle():
        raw=inner(oracle_code,json.dumps(f))
        return json.loads(next(l[7:] for l in raw.splitlines() if l.startswith('ORACLE:')))
    def near(actual,expected):assert abs(float(actual or 0)-expected)<0.05,(actual,expected)
    def stock(a,label,qty,bags,rate=None):
        result=oracle()[a][label];near(result.get('actual_qty'),qty);near(result['bags'],bags)
        if rate is not None:near(result.get('valuation_rate'),rate)
        return result
    def row(label,qty,bags,rate=None,a='APH'):
        d={'item_code':f['items'][label],'warehouse':f['wh'][a],'qty':qty,'kh_aph_bags':bags,'uom':'Kg','conversion_factor':1,'cost_center':f['cc']}
        if rate is not None:d['rate']=rate
        return d
    def receipt(label,qty,bags,rate,a='APH'):
        return submit(insert({'doctype':'Purchase Receipt','company':f['companies'][a],'supplier':f['supplier'],'posting_date':f['date'],'currency':'VND','conversion_rate':1,'items':[row(label,qty,bags,rate,a)]}))
    pending=submit(insert({'doctype':'APH Pending Receipt','company':f['companies']['APH'],'supplier':f['supplier'],'received_date':f['date'],'items':[row('trade',100,4)]}))
    initial=oracle();assert initial['counts']['Stock Ledger Entry']==initial['counts']['GL Entry']==0,initial
    stock('APH','trade',0,0)
    report=rpc('frappe.desk.query_report.run',{'report_name':'Ton kho so luong','filters':json.dumps({'item_code':f['items']['trade']})},factory)
    assert any(float(r.get('pending_kg',0))==100 and float(r.get('actual_qty',0))==0 for r in report['result']),report
    emit('HTTP_PENDING_EXCLUDED_FROM_AVAILABLE','PASS',{'pending_kg':100,'available_kg':0,'sle':0,'gl':0})
    args={'name':pending['name'],'rates':json.dumps({pending['items'][0]['name']:10000}),'reason':'UAT chốt giá/kg'}
    deny(lambda:rpc('kh_aph.pending_valuation.finalize',args,factory));assert oracle()==initial
    zero={**args,'rates':json.dumps({pending['items'][0]['name']:0})}
    deny(lambda:rpc('kh_aph.pending_valuation.finalize',zero));assert oracle()==initial
    emit('HTTP_PENDING_PRICE_AND_ROLE_GUARDS','PASS','Factory and zero price rejected; no ledger written')
    pr1=rpc('kh_aph.pending_valuation.finalize',args)
    stock('APH','trade',100,4,10000)
    same=oracle();assert rpc('kh_aph.pending_valuation.finalize',args)==pr1 and oracle()==same
    emit('HTTP_PENDING_FINALIZE_ATOMIC_REPEAT','PASS',{'qty_kg':100,'bags':4,'ma':10000,'receipt':pr1})
    pr2=receipt('trade',50,2,20000)
    stock('APH','trade',150,6,13333.3333333333)
    vhpr=receipt('trade',50,2,5000,'VH')
    stock('VH','trade',50,2,5000);stock('APH','trade',150,6,13333.3333333333)
    emit('HTTP_MOVING_AVERAGE_PER_WAREHOUSE','PASS',{'APH_qty':150,'APH_ma':13333.3333333333,'VH_ma':5000})
    shared=submit(insert({'doctype':'APH Shared Sales Order','customer':f['customer'],'transaction_date':f['date'],'delivery_date':f['date'],'selling_price_list':f['price_list'],'currency':'VND','items':[{**row('trade',75,3,20000),'line_id':'bag-line'}]}))
    so_name=rpc('frappe.client.get_list',{'doctype':'Sales Order','filters':json.dumps({'kh_aph_shared_order':shared['name']}),'fields':json.dumps(['name'])})[0]['name']
    so=get('Sales Order',so_name);assert so['items'][0]['qty']==75 and so['items'][0]['kh_aph_bags']==3
    assert so['items'][0]['kh_aph_bag_rate']==500000 and so['grand_total']==1500000,so
    emit('HTTP_SHARED_BAG_PRICE_PER_KG','PASS',{'bags':3,'kg':75,'rate_kg':20000,'rate_bag':500000,'total':1500000})
    dn=rpc('erpnext.selling.doctype.sales_order.sales_order.make_delivery_note',{'source_name':so_name})
    dn['items'][0].update(qty=50,kh_aph_bags=1)
    baseline=oracle();deny(lambda:insert(dn));assert oracle()==baseline
    dn['items'][0].update(qty=25,kh_aph_bags=1)
    dn=submit(insert(dn))
    stock('APH','trade',125,5,13333.3333333333);near(oracle()['customer_debt'],500000)
    emit('HTTP_PARTIAL_DISPATCH_BAG_LEDGER','PASS',{'kg':125,'bags':5,'debt':500000,'mismatch_rejected':True})
    ret=rpc('erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return',{'source_name':dn['name']})
    ret['items'][0].update(qty=-25,kh_aph_bags=-1)
    ret=submit(insert(ret));stock('APH','trade',150,6);near(oracle()['customer_debt'],0)
    emit('HTTP_RETURN_RESTORES_BAGS_KG_DEBT','PASS',{'kg':150,'bags':6,'debt':0})
    def lcv(receipts,amount):
        doc={'doctype':'Landed Cost Voucher','company':f['companies']['APH'],'posting_date':f['date'],'distribute_charges_based_on':'Distribute Manually','kh_aph_by_kg':1,'purchase_receipts':[{'receipt_document_type':'Purchase Receipt','receipt_document':r} for r in receipts],'taxes':[{'expense_account':f['expense'],'description':'UAT chi phí chuyến theo kg','amount':amount}]}
        return submit(insert(doc))
    landed=lcv([pr1,pr2['name']],150000)
    charges=sorted(float(r['applicable_charges']) for r in landed['items']);assert charges==[50000,100000],landed
    # Run the actual pinned ERPNext repost function and require completion, not queued status.
    repost_code='''import frappe,json
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import execute_reposting_entry
for attempt in range(15):
 names=frappe.get_all('Repost Item Valuation',filters={'docstatus':1,'status':['in',['Queued','In Progress']]},pluck='name',order_by='creation')
 if not names:break
 for name in names:execute_reposting_entry(name)
failed=frappe.get_all('Repost Item Valuation',filters={'docstatus':1,'status':['not in',['Completed','Skipped']]},fields=['name','status','error_log'])
assert not failed,failed
frappe.db.commit();print('REPOST:'+json.dumps(frappe.get_all('Repost Item Valuation',fields=['name','status']),default=str));frappe.destroy()
'''
    def repost():return inner(repost_code)
    repost();stock('APH','trade',150,6,14333.3333333333);stock('VH','trade',50,2,5000)
    emit('HTTP_LANDED_COST_KG_AND_REPOST','PASS',{'charges':charges,'APH_ma':14333.3333333333,'VH_ma':5000})
    raw_pr=receipt('raw',100,4,10000)
    def production():
        rows=[]
        for label,qty,bags,source in [('raw',100,4,True),('fg',70,7,False),('by',20,4,False),('fixed',5,1,False)]:
            d={'item_code':f['items'][label],'qty':qty,'kh_aph_bags':bags,'uom':'Kg','conversion_factor':1,'cost_center':f['cc'],'expense_account':f['adjustment'],'s_warehouse' if source else 't_warehouse':f['wh']['APH']}
            if label=='fixed':d.update(basic_rate=5000,set_basic_rate_manually=1)
            rows.append(d)
        return {'doctype':'Stock Entry','stock_entry_type':'Đóng gói theo kg','company':f['companies']['APH'],'posting_date':f['date'],'items':rows,'additional_costs':[{'expense_account':f['expense'],'description':'UAT chi phí sản xuất','amount':90000}]}
    prod=submit(insert(production()))
    assert prod['kh_aph_costing_rule']=='kg-v3',prod
    near(prod['total_incoming_value'],1090000);stock('APH','raw',0,0);stock('APH','fg',70,7);stock('APH','by',20,4);stock('APH','fixed',5,1,5000)
    by_item={r['item_code']:r for r in prod['items']}
    near(by_item[f['items']['fg']]['additional_cost'],70000);near(by_item[f['items']['by']]['additional_cost'],20000);near(by_item[f['items']['fixed']]['additional_cost'],0)
    emit('HTTP_PRODUCTION_KG_BYPRODUCT_ADDITIONAL_COST','PASS',{'input_value':1000000,'additional_cost':90000,'output_value':1090000,'fg_kg':70,'byproduct_kg':20,'fixed_kg':5,'natural_weight_loss':5})
    baseline=oracle();deny(lambda:cancel('Purchase Receipt',raw_pr['name']));assert oracle()==baseline
    forged={'doctype':'APH Bag Movement','item_code':f['items']['raw'],'warehouse':f['wh']['APH'],'bags':999}
    deny(lambda:insert(forged));assert oracle()==baseline
    emit('HTTP_BAG_HISTORY_AND_CANCEL_GUARDS','PASS','Consumed input cancellation and direct bag-ledger injection rejected')
    raw_lcv=lcv([raw_pr['name']],100000);repost()
    recalculated=get('Stock Entry',prod['name'])
    near(recalculated['total_incoming_value'],1190000)
    stock('APH','fixed',5,1,5000)
    near(sum(float(oracle()['APH'][label].get('stock_value',0)) for label in ('fg','by','fixed')),1190000)
    emit('HTTP_PRODUCTION_INPUT_COST_REPOST','PASS',{'late_raw_cost':100000,'reposted_output_value':1190000,'fixed_byproduct_rate':5000})
    cancel('Landed Cost Voucher',raw_lcv['name']);repost()
    cancel('Stock Entry',prod['name']);stock('APH','raw',100,4,10000)
    for label in ('fg','by','fixed'):stock('APH',label,0,0)
    emit('HTTP_PRODUCTION_CANCEL_REVERSE','PASS',{'raw_kg':100,'raw_bags':4,'output_kg':0,'output_bags':0})
except Exception as exc:
    detail={'type':type(exc).__name__,'error':str(exc)[-2500:]}
    if isinstance(exc,urllib.error.HTTPError):
        try:
            payload=json.loads(exc.read());detail['response']={k:payload.get(k) for k in ('exc_type','exception','_server_messages')}
        except Exception:pass
    detail['traceback']=traceback.format_exc()[-2500:]
    emit('HTTP_INVENTORY_RUNNER','FAIL',detail)
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
