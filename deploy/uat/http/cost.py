FIXTURE_CODE = 'import json,sys,frappe\nfrom frappe.utils import today\nfrom frappe.utils.password import update_password\nfrom kh_aph.constants import INV_FLAG, INV_NO, ROLE_FACTORY, ROLE_NO_COST\nfrappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")\nfrappe.connect();frappe.set_user("Administrator")\nimport uuid\npayload=json.load(sys.stdin)\nco = frappe.get_doc("Company", frappe.db.get_value("Company", {"abbr": "APH"}, "name"))\np = "UAT-P0-" + uuid.uuid4().hex[:8]\nwh = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p, "company": co.name,\n                    "is_group": 0, "parent_warehouse": frappe.db.get_value("Warehouse", {\n                        "company": co.name, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name"),\n                    "account": co.default_inventory_account}).insert().name\ngroup = frappe.get_doc({"doctype": "Item Group", "item_group_name": p,\n                       "parent_item_group": "HH - Hàng hóa", "is_group": 0}).insert().name\ncustomer = frappe.get_doc({"doctype": "Customer", "customer_name": p, "customer_type": "Company",\n                           "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),\n                           "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),\n                           INV_FLAG: INV_NO}).insert()\nvat_account = frappe.db.get_value("Account", {"company": co.name, "account_number": "33311", "is_group": 0}, "name")\ntax = frappe.get_doc({"doctype": "Item Tax Template", "title": p + "-TEST10", "company": co.name,\n                     "taxes": [{"tax_type": vat_account, "tax_rate": 10}]}).insert()\nitem = frappe.get_doc({"doctype": "Item", "item_code": p, "item_name": p, "item_group": group,\n                      "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average",\n                      "taxes": [{"item_tax_template": tax.name, "tax_category": customer.tax_category}],\n                      "item_defaults": [{"company": co.name, "default_warehouse": wh,\n                                         "income_account": co.default_income_account,\n                                         "expense_account": co.default_expense_account,\n                                         "buying_cost_center": co.cost_center,\n                                         "selling_cost_center": co.cost_center}]}).insert()\nsupplier=frappe.get_doc({\'doctype\':\'Supplier\',\'supplier_name\':p,\'supplier_type\':\'Company\',\n \'supplier_group\':frappe.db.get_value(\'Supplier Group\',{\'is_group\':0},\'name\')}).insert()\npo=frappe.get_doc({\'doctype\':\'Purchase Order\',\'supplier\':supplier.name,\'company\':co.name,\n \'transaction_date\':today(),\'schedule_date\':today(),\'items\':[{\'item_code\':item.name,\'qty\':1,\n \'uom\':\'Kg\',\'conversion_factor\':1,\'schedule_date\':today(),\'rate\':12345}]}).insert()\nse = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": co.name,\n                    "posting_date": today(), "items": [{"item_code": item.name, "qty": 100,\n                        "uom": "Kg", "stock_uom": "Kg", "conversion_factor": 1, "t_warehouse": wh,\n                        "basic_rate": 10000, "set_basic_rate_manually": 1,\n                        "expense_account": co.stock_adjustment_account, "cost_center": co.cost_center}]}).insert()\nse.submit()\nuser = frappe.get_doc({"doctype": "User", "email": p.lower() + "@example.invalid", "first_name": "Dũng giả lập UAT",\n                      "enabled": 1, "user_type": "System User", "send_welcome_email": 0,\n                      "roles": [{"role": ROLE_FACTORY}, {"role": ROLE_NO_COST}]})\nuser.flags.no_welcome_mail = True\nuser.insert()\n\nupdate_password(user.name,payload["password"])\nfrappe.db.commit()\nprint("FIXTURE_JSON:"+json.dumps({"user":user.name,"stock_entry":se.name,"item":item.name,"warehouse":wh,"company":co.name,"purchase_order":po.name}))\nfrappe.destroy()\n'
"""HTTP cost-security test on a disposable clone, with mandatory database restoration."""
import json, os, secrets, subprocess, uuid, time
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order"]
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
    raw=inner(FIXTURE_CODE,json.dumps({"password":factory_password}))
    fixture=json.loads(next(x[13:] for x in raw.splitlines() if x.startswith("FIXTURE_JSON:")))
    restricted=session(fixture["user"],factory_password)
    for label,path in (("HTTP_COST_CLIENT_GET","/api/method/frappe.client.get?"+urllib.parse.urlencode({"doctype":"Stock Entry","name":fixture["stock_entry"]})),("HTTP_COST_V2","/api/v2/document/Stock%20Entry/"+urllib.parse.quote(fixture["stock_entry"],safe=""))):
        data=restricted(path)
        doc=data.get("message",data.get("data"))
        assert doc and len(doc["items"])==1,"Fixture row missing"
        row=doc["items"][0]
        assert float(row["qty"])==100,"Quantity not preserved"
        for field in ("basic_rate","basic_amount","valuation_rate","amount"):
            assert row.get(field) in (None,"",0),"Cost exposed: "+field
        emit(label,"PASS",{"quantity":100,"cost_visible":False})
    query={"doctype":"Stock Entry Detail","parent":"Stock Entry","filters":json.dumps({"parent":fixture["stock_entry"]}),"fields":json.dumps(["name","qty"])}
    rows=restricted("/api/method/frappe.client.get_list?"+urllib.parse.urlencode(query))["message"]
    assert len(rows)==1 and float(rows[0]["qty"])==100,"Quantity query missing fixture"
    query["fields"]=json.dumps(["qty","basic_rate"])
    try:
        rows=restricted("/api/method/frappe.client.get_list?"+urllib.parse.urlencode(query))["message"]
        assert rows and all(r.get("basic_rate") in (None,"",0) for r in rows),"Child query exposed cost or returned no fixture"
    except urllib.error.HTTPError as exc:
        error=json.loads(exc.read())
        assert exc.code==403 and error.get("exc_type")=="PermissionError","Unexpected query error"
    emit("HTTP_COST_CHILD_QUERY","PASS","Quantity verified; cost masked or permission denied")
    data=admin("/api/method/frappe.client.get?"+urllib.parse.urlencode({"doctype":"Stock Entry","name":fixture["stock_entry"]}))["message"]
    assert float(data["items"][0]["basic_rate"])==10000
    emit("HTTP_COST_ADMIN","PASS",{"basic_rate":10000})
    # Named Dũng simulation: explicit deny survives ordinary operational role unions.
    def denied(call, method, args):
        try:
            call(method,args)
        except urllib.error.HTTPError as exc:
            error=json.loads(exc.read())
            assert exc.code==403 and error.get("exc_type")=="PermissionError",str(error)[:400]
        else:
            raise AssertionError("Cost endpoint did not deny: "+method)
    role_code = """import json,sys,frappe
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites')
try:
 frappe.connect();frappe.set_user('Administrator')
 from kh_aph.constants import ROLE_FACTORY,ROLE_NO_COST
 payload=json.load(sys.stdin);u=frappe.get_doc('User',payload['user'])
 u.set('roles',[{'role':r} for r in [ROLE_FACTORY,ROLE_NO_COST]+payload['roles']])
 u.save();frappe.db.commit();frappe.clear_cache(user=u.name)
 print('PROFILE:'+json.dumps({'user':u.name,'roles':frappe.get_roles(u.name)}))
finally:frappe.destroy()
"""
    for label,roles in (("factory",[]),("sales_manager",["Sales Manager"]),
                        ("accounts_user",["Accounts User"]),("accounts_manager",["Accounts Manager"]),
                        ("stock_manager",["Stock Manager"])):
        raw=inner(role_code,json.dumps({"user":fixture["user"],"roles":roles}))
        measured=json.loads(next(x[8:] for x in raw.splitlines() if x.startswith("PROFILE:")))
        actor=session(fixture["user"],factory_password)
        for path in ("/api/method/frappe.client.get?"+urllib.parse.urlencode({"doctype":"Stock Entry","name":fixture["stock_entry"]}),
                     "/api/v2/document/Stock%20Entry/"+urllib.parse.quote(fixture["stock_entry"],safe="")):
            data=actor(path);doc=data.get("message",data.get("data"));row=doc["items"][0]
            assert float(row["qty"])==100 and row.get("basic_rate") in (None,"",0),str(row)[:400]
        buying=actor('/api/method/frappe.client.get',{'doctype':'Purchase Order','name':fixture['purchase_order']})['message']
        assert float(buying['items'][0]['qty'])==1 and buying['items'][0].get('rate') in (None,'',0),"Buying price exposed via role union"
        buying_control=admin('/api/method/frappe.client.get',{'doctype':'Purchase Order','name':fixture['purchase_order']})['message']
        assert float(buying_control['items'][0]['rate'])==12345
        denied(actor,'/api/method/frappe.client.get_list',{'doctype':'Purchase Order Item','parent':'Purchase Order','fields':json.dumps(['qty','rate']),'filters':json.dumps({'parent':fixture['purchase_order']})})
        denied(actor,'/api/method/frappe.client.get_value',{'doctype':'Purchase Order Item','parent':'Purchase Order','fieldname':json.dumps(['qty','rate']),'filters':json.dumps({'parent':fixture['purchase_order']})})
        denied(actor,'/api/method/frappe.client.get',{'doctype':'Purchase Order Item','name':buying_control['items'][0]['name']})
        q={"doctype":"Stock Entry Detail","parent":"Stock Entry","filters":json.dumps({"parent":fixture["stock_entry"]}),"fieldname":json.dumps(["qty","basic_rate"])}
        values=actor("/api/method/frappe.client.get_value",q)["message"]
        assert float(values['qty'])==100 and values.get('basic_rate') in (None,'',0)
        denied(actor,"/api/method/frappe.client.get_list",{"doctype":"Stock Entry Detail","parent":"Stock Entry","fields":json.dumps(["qty","basic_rate"]),"group_by":"basic_rate"})
        denied(actor,"/api/method/frappe.client.get_list",{"doctype":"Stock Entry Detail","parent":"Stock Entry","fields":json.dumps(["qty"]),"filters":json.dumps({"basic_rate":10000})})
        rate_args={'item_code':fixture['item'],'warehouse':fixture['warehouse'],'with_valuation_rate':1}
        balance=admin('/api/method/erpnext.stock.utils.get_stock_balance',rate_args)['message']
        assert float(balance[0])==100 and float(balance[1])==10000,str(balance)
        denied(actor,'/api/method/erpnext.stock.utils.get_stock_balance',rate_args)
        denied(actor,'/api/method/erpnext.stock.utils.get_incoming_rate',{'args':json.dumps({'item_code':fixture['item'],'warehouse':fixture['warehouse'],'qty':1})})
        for dt in ("Bin","Stock Ledger Entry","GL Entry"):
            denied(actor,"/api/method/frappe.client.get_list",{"doctype":dt,"fields":json.dumps(["name"])})
        for report in ("Stock Ledger","Stock Balance","Ton kho theo tai khoan va dia diem"):
            denied(actor,"/api/method/frappe.desk.query_report.run",{"report_name":report,"filters":json.dumps({"company":fixture["company"]})})
        denied(actor,"/api/method/frappe.core.doctype.data_export.exporter.export_data",{"doctype":"Stock Entry","file_type":"CSV"})
        denied(actor,"/api/method/erpnext.controllers.stock_controller.show_stock_ledger_preview",{"company":fixture["company"],"doctype":"Stock Entry","docname":fixture["stock_entry"]})
        emit("HTTP_DUNG_PROFILE_"+label.upper(),"PASS",{"user":fixture["user"],"roles":measured["roles"],"quantity":100,"cost_visible":False,"query_report_export_preview":"denied or masked"})
    # API key authentication must enforce the same policy as cookie authentication.
    token_code="""import json,sys,frappe
from frappe.utils.password import get_decrypted_password,set_encrypted_password
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites')
try:
 frappe.connect();frappe.set_user('Administrator');user=json.load(sys.stdin)['user']
 keys={'api_key':frappe.generate_hash(length=15),'api_secret':frappe.generate_hash(length=15)}
 frappe.db.set_value('User',user,'api_key',keys['api_key'])
 set_encrypted_password('User',user,keys['api_secret'],fieldname='api_secret')
 frappe.db.commit()
 assert frappe.db.get_value('User',user,'api_key')==keys['api_key']
 assert get_decrypted_password('User',user,'api_secret')==keys['api_secret']
 frappe.clear_cache()
 print('KEYS:'+json.dumps(keys))
finally:frappe.destroy()
"""
    raw=inner(token_code,json.dumps({'user':fixture['user']}))
    token_keys=json.loads(next(x[5:] for x in raw.splitlines() if x.startswith('KEYS:')))
    token_secret=token_keys['api_secret']
    # The first encrypted fixture field can initialize encryption_key after the
    # HTTP worker cached site_config. Reload only the disposable UAT worker.
    run(['docker','restart',WEB])
    for attempt in range(40):
        try:
            admin=session('Administrator',state['admin_password'])
            actor=session(fixture['user'],factory_password)
            break
        except (urllib.error.URLError,ConnectionError):
            if attempt==39:raise
            time.sleep(0.5)
    def token_call(method,args):
        req=urllib.request.Request("http://127.0.0.1:18091"+method,data=urllib.parse.urlencode(args).encode(),
            headers={"Host":SITE,"X-Frappe-Site-Name":SITE,"Authorization":"token "+token_keys['api_key']+":"+token_secret})
        with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
    doc=token_call('/api/method/frappe.client.get',{"doctype":"Stock Entry","name":fixture['stock_entry']})['message']
    assert float(doc['items'][0]['qty'])==100 and doc['items'][0].get('basic_rate') in (None,'',0)
    denied(token_call,'/api/method/frappe.desk.query_report.run',{"report_name":"Stock Ledger","filters":json.dumps({"company":fixture['company']})})
    emit('HTTP_DUNG_API_TOKEN','PASS',{'quantity':100,'cost_visible':False,'stock_ledger_denied':True})
    # Controller helper returns an untyped cost dict: mask it as well as docs.
    helper_args={"dt":"Stock Entry","dn":fixture['stock_entry'],"method":"get_item_details",
                 "args":json.dumps({"item_code":fixture['item'],"warehouse":fixture['warehouse'],"s_warehouse":fixture['warehouse'],"company":fixture['company'],"qty":1})}
    helper_admin=admin('/api/method/run_doc_method',helper_args)['message']
    helper_dung=actor('/api/method/run_doc_method',helper_args)['message']
    assert float(helper_admin['basic_rate'])==10000,str(helper_admin)[:400]
    assert helper_dung.get('basic_rate') in (None,'',0),"Controller helper exposed cost"
    denied(actor,'/api/method/run_doc_method',{**helper_args,'as_csv':1})
    emit('HTTP_DUNG_CONTROLLER_HELPER','PASS',{'admin_rate':10000,'dung_cost_visible':False,'csv_denied':True})
    # Stock operation under the base Dũng profile, not Administrator.
    inner(role_code,json.dumps({"user":fixture["user"],"roles":[]}))
    actor=session(fixture["user"],factory_password)
    issue={"doctype":"Stock Entry","stock_entry_type":"Material Issue","company":fixture["company"],
           "items":[{"item_code":fixture["item"],"qty":2,"uom":"Kg","stock_uom":"Kg","conversion_factor":1,"s_warehouse":fixture["warehouse"]}]}
    created=actor("/api/method/frappe.client.insert",{"doc":json.dumps(issue)})["message"]
    assert created["items"][0].get("basic_rate") in (None,"",0),"Insert response exposed cost"
    submitted=actor("/api/method/frappe.client.submit",{"doc":json.dumps(created)})["message"]
    assert submitted['docstatus']==1 and submitted['items'][0].get('basic_rate') in (None,'',0)
    control=admin("/api/method/frappe.client.get",{"doctype":"Stock Entry","name":created["name"]})['message']
    assert float(control['items'][0]['basic_rate'])==10000 and float(control['items'][0]['qty'])==2
    qty=admin("/api/method/frappe.client.get_value",{"doctype":"Bin","filters":json.dumps({"item_code":fixture["item"],"warehouse":fixture["warehouse"]}),"fieldname":"actual_qty"})['message']
    assert float(qty['actual_qty'])==98,str(qty)
    report=actor('/api/method/frappe.desk.query_report.run',{"report_name":"Ton kho so luong","filters":json.dumps({"company":fixture['company']}),"ignore_prepared_report":1})['message']
    assert report.get('result'),"Dũng quantity report returned no stock"
    assert 'valuation_rate' not in json.dumps(report) and 'stock_value' not in json.dumps(report),"Quantity report exposed cost columns"
    emit("HTTP_DUNG_QUANTITY_OPERATION","PASS",{"actor":fixture['user'],"submitted_qty":2,"remaining_kg":98,"admin_rate":10000,"insert_submit_cost_visible":False})
    # Probe template prints cost explicitly; before_print must mask it for Dũng.
    print_code="""import json,sys,frappe
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites')
try:
 frappe.connect();frappe.set_user('Administrator');p=json.load(sys.stdin)
 f=frappe.get_doc({'doctype':'Print Format','name':'UAT Dung Cost Probe','doc_type':'Stock Entry','custom_format':1,'print_format_type':'Jinja','html':'<div>PROBE_QTY={{ doc.items[0].qty }};PROBE_COST={{ doc.items[0].basic_rate }}</div>'}).insert()
 frappe.db.commit();print('FORMAT:'+f.name)
finally:frappe.destroy()
"""
    raw=inner(print_code,'{}');fmt=next(x[7:] for x in raw.splitlines() if x.startswith('FORMAT:'))
    args={"doc":"Stock Entry","name":fixture['stock_entry'],"print_format":fmt,"no_letterhead":1}
    a=admin('/api/method/frappe.www.printview.get_html_and_style',args)['message']['html']
    d=actor('/api/method/frappe.www.printview.get_html_and_style',args)['message']['html']
    assert 'PROBE_COST=10000' in a and 'PROBE_COST=10000' not in d and 'PROBE_QTY=100' in d
    emit('HTTP_DUNG_PRINT','PASS',{'admin_probe_cost':10000,'dung_cost_visible':False,'quantity':100})
    # 0.11.0: lối in/xem trước bỏ qua bước xóa giá phải bị chặn với người bị ẩn giá (kh_aph.print_guard).
    se_doc=admin("/api/method/frappe.client.get?"+urllib.parse.urlencode({"doctype":"Stock Entry","name":fixture["stock_entry"]}))["message"]
    bypass=(("frappe.utils.weasyprint.download_pdf",{"doctype":"Stock Entry","name":fixture["stock_entry"],"print_format":fmt}),
            ("frappe.utils.weasyprint_legacy.download_pdf",{"doctype":"Purchase Order","name":fixture["purchase_order"],"print_format":fmt}),
            ("frappe.utils.print_format_generator.get_formatted_field_values",{"doctype":"Purchase Order","name":fixture["purchase_order"]}),
            ("frappe.utils.print_format_generator.check_conditions",{"doctype":"Purchase Order","name":fixture["purchase_order"],"conditions":json.dumps(["doc.items[0].rate > 12000"])}),
            ("frappe.desk.doc_preview.get_preview",{"doctype":"Stock Entry Detail","name":se_doc["items"][0]["name"]}))
    for method,margs in bypass:
        denied(actor,"/api/method/"+method,margs)
    admin_control="endpoint_absent"
    try:
        v=admin("/api/method/frappe.utils.print_format_generator.get_formatted_field_values",{"doctype":"Purchase Order","name":fixture["purchase_order"]})["message"]
        import re
        assert re.search(r"12\D?345",json.dumps(v,ensure_ascii=False)),"Admin control did not show purchase rate"
        admin_control="purchase_rate_visible_to_admin"
    except urllib.error.HTTPError:
        pass
    emit('HTTP_PRINT_BYPASS_DENIED','PASS',{'denied':[m for m,_ in bypass],'admin_control':admin_control})
except Exception as exc:
    detail={"type":type(exc).__name__,"error":str(exc)[-2500:]}
    if isinstance(exc,urllib.error.HTTPError):
        body=exc.read().decode(errors='replace')
        for secret in (factory_password,token_secret,state.get('admin_password','')):
            if secret:body=body.replace(secret,'[REDACTED]')
        try:
            data=json.loads(body);detail['http_error']={k:data.get(k) for k in ('exc_type','exception','_server_messages')}
        except ValueError:detail['http_error']=body[:1000]
    emit("HTTP_COST_RUNNER","FAIL",detail)
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
