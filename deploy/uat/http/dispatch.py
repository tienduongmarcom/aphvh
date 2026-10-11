FIXTURE_CODE = 'import json,sys,frappe\nfrom frappe.utils import today,add_days\nfrom frappe.utils.password import update_password\nfrom kh_aph.constants import INV_FLAG, INV_NO, ROLE_FACTORY\nfrappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")\nfrappe.connect();frappe.set_user("Administrator")\nimport uuid\npayload=json.load(sys.stdin)\nco = frappe.get_doc("Company", frappe.db.get_value("Company", {"abbr": "APH"}, "name"))\np = "UAT-P0-" + uuid.uuid4().hex[:8]\nwh = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p, "company": co.name,\n                    "is_group": 0, "parent_warehouse": frappe.db.get_value("Warehouse", {\n                        "company": co.name, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name"),\n                    "account": co.default_inventory_account}).insert().name\ngroup = frappe.get_doc({"doctype": "Item Group", "item_group_name": p,\n                       "parent_item_group": "HH - Hàng hóa", "is_group": 0}).insert().name\ncustomer = frappe.get_doc({"doctype": "Customer", "customer_name": p, "customer_type": "Company",\n                           "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),\n                           "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),\n                           INV_FLAG: INV_NO}).insert()\nvat_account = frappe.db.get_value("Account", {"company": co.name, "account_number": "33311", "is_group": 0}, "name")\ntax = frappe.get_doc({"doctype": "Item Tax Template", "title": p + "-TEST10", "company": co.name,\n                     "taxes": [{"tax_type": vat_account, "tax_rate": 10}]}).insert()\nitem = frappe.get_doc({"doctype": "Item", "item_code": p, "item_name": p, "item_group": group,\n                      "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average",\n                      "taxes": [{"item_tax_template": tax.name, "tax_category": customer.tax_category}],\n                      "item_defaults": [{"company": co.name, "default_warehouse": wh,\n                                         "income_account": co.default_income_account,\n                                         "expense_account": co.default_expense_account,\n                                         "buying_cost_center": co.cost_center,\n                                         "selling_cost_center": co.cost_center}]}).insert()\nse = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": co.name,\n                    "posting_date": today(), "items": [{"item_code": item.name, "qty": 100,\n                        "uom": "Kg", "stock_uom": "Kg", "conversion_factor": 1, "t_warehouse": wh,\n                        "basic_rate": 10000, "set_basic_rate_manually": 1,\n                        "expense_account": co.stock_adjustment_account, "cost_center": co.cost_center}]}).insert()\nse.submit()\nuser = frappe.get_doc({"doctype": "User", "email": p.lower() + "@example.invalid", "first_name": p,\n                      "enabled": 1, "user_type": "System User", "send_welcome_email": 0,\n                      "roles": [{"role": ROLE_FACTORY}]})\nuser.flags.no_welcome_mail = True\nuser.insert()\n\nupdate_password(user.name,payload["password"])\nso = frappe.get_doc({"doctype": "Sales Order", "company": co.name, "customer": customer.name,\n                    "transaction_date": today(), "delivery_date": add_days(today(), 1),\n                    "selling_price_list": frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name"),\n                    "currency": "VND", "conversion_rate": 1, "order_type": "Sales", INV_FLAG: INV_NO,\n                    "items": [{"item_code": item.name, "qty": 10, "uom": "Kg", "conversion_factor": 1,\n                               "rate": 20000, "warehouse": wh, "item_tax_template": tax.name,\n                               "delivery_date": add_days(today(), 1)}]}).insert()\nso.submit()\nfrom erpnext.selling.doctype.sales_order.sales_order import make_delivery_note\n\ndn = make_delivery_note(so.name)\ndn.posting_date = today()\ndn.set(INV_FLAG, INV_NO)\nfor row in dn.items:\n    row.qty = 4\ndn.insert()\ndn1=dn.name\ndn=make_delivery_note(so.name)\ndn.posting_date=today()\ndn.set(INV_FLAG,INV_NO)\nfor row in dn.items:row.qty=2\ndn.insert()\ndn2=dn.name\nfrappe.db.commit()\nprint("FIXTURE_JSON:"+json.dumps({"user":user.name,"stock_entry":se.name,"dn1":dn1,"dn2":dn2,"customer":customer.name,"company":co.name,"item":item.name,"warehouse":wh}))\nfrappe.destroy()\n'
"""HTTP dispatch accounting test on a disposable clone, with mandatory database restoration."""
import json, os, secrets, subprocess, uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","APH Credit Release","APH Shared Sales Order","APH Shared Sales Order Item","Custom Field","Version","User Permission"]
root_secret=""
factory_password=secrets.token_urlsafe(32)
def run(args,input=None):
    p=subprocess.run(args,input=input,text=True,capture_output=True)
    if p.returncode:
        message=(p.stdout+p.stderr)[-3500:]
        for secret in (root_secret,factory_password,state.get("admin_password","")):
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
    def getdoc(dt,name):
        return admin("/api/method/frappe.client.get?"+urllib.parse.urlencode({"doctype":dt,"name":name}))["message"]
    def submit(dt,name):
        return admin("/api/method/frappe.client.submit",{"doc":json.dumps(getdoc(dt,name))})["message"]
    def cancel(dt,name):
        return admin("/api/method/frappe.client.cancel",{"doctype":dt,"name":name})
    oracle_code='''import json,sys,frappe
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
try:
 f=json.load(sys.stdin)
 debt=frappe.db.sql("SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry` WHERE party_type='Customer' AND party=%s AND company=%s AND is_cancelled=0",(f["customer"],f["company"]))[0][0]
 qty=frappe.db.get_value("Bin",{"item_code":f["item"],"warehouse":f["warehouse"]},"actual_qty")
 invoices=frappe.get_all("Sales Invoice",fields=["name","docstatus","update_stock","grand_total","outstanding_amount","is_return","return_against"])
 print("ORACLE:"+json.dumps({"debt":float(debt),"stock_kg":float(qty),"invoices":invoices},default=str))
finally:frappe.destroy()
'''
    def oracle():
        raw=inner(oracle_code,json.dumps(fixture))
        return json.loads(next(x[7:] for x in raw.splitlines() if x.startswith("ORACLE:")))
    def check(expected_debt,expected_qty,invoice_count):
        result=oracle()
        assert abs(result["debt"]-expected_debt)<0.01,str(result)
        assert result["stock_kg"]==expected_qty,str(result)
        active=[x for x in result["invoices"] if x["docstatus"]==1]
        assert len(active)==invoice_count,str(result)
        assert all(x["update_stock"]==0 for x in active),"SI posted stock again"
        return result
    initial=getdoc("Delivery Note",fixture["dn1"])
    assert initial["docstatus"]==0
    calls=[session("Administrator",state["admin_password"]) for _ in range(2)]
    barrier=threading.Barrier(2)
    def simultaneous(call):
        barrier.wait(timeout=15)
        try:
            result=call("/api/method/frappe.client.submit",{"doc":json.dumps(initial)})["message"]
            assert result["docstatus"]==1
            return {"status":"submitted"}
        except urllib.error.HTTPError as exc:
            error=json.loads(exc.read())
            kind=error.get("exc_type")
            assert kind in ("TimestampMismatchError","ValidationError","QueryDeadlockError","DeadlockError"),kind
            if kind=="ValidationError":
                text=error.get("exception","")+error.get("_server_messages","")
                assert "submitted" in text.lower(),"Unexpected submit validation"
            return {"status":"rejected","type":kind}
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes=list(executor.map(simultaneous,calls))
    assert any(r["status"]=="submitted" for r in outcomes),outcomes
    ledger=check(80000,96,1)
    assert getdoc("Delivery Note",fixture["dn1"])["docstatus"]==1
    emit("HTTP_CONCURRENT_SAME_DN","PASS",{"requests":outcomes,"ledger":ledger})
    emit("HTTP_DISPATCH_DEBT","PASS",ledger)
    dispatched=getdoc("Delivery Note",fixture["dn1"])
    assert dispatched['kh_aph_delivery_state']=='Đang giao'
    assert dispatched['kh_aph_delivery_actor']=='Administrator' and dispatched['kh_aph_delivery_at']
    emit('HTTP_DELIVERY_HANDOFF_STATE','PASS','Submitted dispatch stamped actor/time')
    receipt=admin('/api/method/kh_aph.delivery_status.confirm',{'name':fixture['dn1'],'action':'receive'})['message']
    assert receipt['kh_aph_delivery_state']=='Khách đã nhận'
    check(80000,96,1)
    emit('HTTP_DELIVERY_RECEIPT_NO_REPOST','PASS','Receipt leaves stock/debt unchanged')
    history_code="""import json,sys,frappe
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()
try:
 name=json.load(sys.stdin)['name']
 versions=frappe.get_all('Version',filters={'ref_doctype':'Delivery Note','docname':name},fields=['owner','data'])
 assert any(v.owner=='Administrator' and any(c[0]=='kh_aph_delivery_state' and c[1]=='Đang giao' and c[2]=='Khách đã nhận' for c in json.loads(v.data).get('changed',[])) for v in versions), 'Receipt transition missing from Version history'
 print('HISTORY_VERIFIED')
finally:frappe.destroy()
"""
    assert 'HISTORY_VERIFIED' in inner(history_code,json.dumps({'name':fixture['dn1']}))
    emit('HTTP_DELIVERY_RECEIPT_HISTORY','PASS','Version records previous/new state and actor')
    again=admin('/api/method/kh_aph.delivery_status.confirm',{'name':fixture['dn1'],'action':'receive'})['message']
    assert again['kh_aph_delivery_at']==receipt['kh_aph_delivery_at']
    check(80000,96,1)
    emit('HTTP_DELIVERY_RECEIPT_REPEAT','PASS','Repeated receipt preserves timestamp and ledger')
    forged=dict(receipt);forged['kh_aph_delivery_state']='Chờ xuất'
    forged['flags']={'kh_aph_delivery_transition':True}
    try:
        admin('/api/method/frappe.client.save',{'doc':json.dumps(forged)})
        raise AssertionError('Direct status edit accepted')
    except urllib.error.HTTPError as exc:
        error=json.loads(exc.read());assert error.get('exc_type')=='ValidationError',error
    assert getdoc('Delivery Note',fixture['dn1'])['kh_aph_delivery_state']=='Khách đã nhận'
    emit('HTTP_DELIVERY_STATE_EDIT_DENIED','PASS','Direct status rollback rejected')
    assert getdoc('Delivery Note',fixture['dn2'])['kh_aph_delivery_state']=='Chờ xuất'
    try:
        admin('/api/method/kh_aph.delivery_status.confirm',{'name':fixture['dn2'],'action':'receive'})
        raise AssertionError('Draft receipt accepted')
    except urllib.error.HTTPError as exc:
        error=json.loads(exc.read());assert error.get('exc_type')=='ValidationError',error
    check(80000,96,1)
    emit('HTTP_DELIVERY_DRAFT_RECEIPT_DENIED','PASS','Cannot receive before dispatch')
    second=admin('/api/method/kh_aph.delivery_status.confirm',{'name':fixture['dn2'],'action':'pickup'})['message']
    assert second['kh_aph_delivery_state']=='Khách đã nhận'
    emit('HTTP_DELIVERY_PICKUP_STATE','PASS','Pickup goes directly from waiting to received')
    repeated=admin('/api/method/kh_aph.delivery_status.confirm',{'name':fixture['dn2'],'action':'pickup'})['message']
    assert repeated['kh_aph_delivery_at']==second['kh_aph_delivery_at']
    check(120000,94,2)
    emit('HTTP_DELIVERY_PICKUP_REPEAT','PASS','Pickup repeat creates no additional invoice')
    assert second["docstatus"]==1
    emit("HTTP_DISPATCH_SECOND_BATCH","PASS",check(120000,94,2))
    return_code='import json,sys,frappe\nfrom frappe.utils import today\nfrom erpnext.stock.doctype.delivery_note.delivery_note import make_sales_return\nfrappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")\nfrappe.connect();frappe.set_user("Administrator")\ntry:\n f=json.load(sys.stdin)\n ret=make_sales_return(f["dn1"])\n ret.posting_date=today();ret.issue_credit_note=0\n for row in ret.items:\n  row.qty=-1;row.warehouse=f["warehouse"]\n ret.insert();frappe.db.commit()\n print("RETURN_JSON:"+json.dumps({"name":ret.name}))\nfinally:frappe.destroy()\n'
    raw=inner(return_code,json.dumps(fixture))
    return_name=json.loads(next(x[12:] for x in raw.splitlines() if x.startswith("RETURN_JSON:")))["name"]
    returned=submit("Delivery Note",return_name)
    assert returned["docstatus"]==1 and returned["is_return"]
    return_ledger=check(100000,95,3)
    credits=[i for i in return_ledger["invoices"] if i["docstatus"]==1 and i["is_return"]]
    assert len(credits)==1 and credits[0]["return_against"],"Credit not linked to original SI"
    assert float(credits[0]["grand_total"])==-20000,"Credit amount wrong"
    emit("HTTP_PARTIAL_RETURN","PASS",return_ledger)
    cancel("Sales Invoice",credits[0]["name"])
    cancel("Delivery Note",return_name)
    emit("HTTP_RETURN_CANCEL","PASS",check(120000,94,2))
    baseline=oracle()
    try:
        cancel("Delivery Note",fixture["dn1"])
        raise AssertionError("DN cancellation accepted while SI submitted")
    except urllib.error.HTTPError as exc:
        error=json.loads(exc.read())
        assert error.get("exc_type")=="ValidationError",str(error.get("exc_type"))
        messages=error.get("_server_messages","")+error.get("exception","")
        assert "Sales Invoice" in messages and "already been submitted" in messages,"Unexpected cancellation guard"
    assert oracle()==baseline,"Rejected cancellation changed ledger or stock"
    assert getdoc("Delivery Note",fixture["dn1"])["docstatus"]==1
    emit("HTTP_CANCEL_LINK_GUARD","PASS","Cancellation rejected; stock and debt unchanged")
    for inv in baseline["invoices"]:
        if inv["docstatus"]==1:cancel("Sales Invoice",inv["name"])
    cancel("Delivery Note",fixture["dn2"])
    cancel("Delivery Note",fixture["dn1"])
    emit("HTTP_CANCEL_REVERSE","PASS",check(0,100,0))
    # Independent high-risk HTTP regression after the ordinary dispatch reversal.
    risk_code = '''import json,sys,frappe
from frappe.utils.password import update_password
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect();frappe.set_user("Administrator")
f=json.load(sys.stdin)
try:
 c=frappe.get_doc("Customer",f["customer"])
 c.kh_aph_credit_high_risk=1;c.kh_aph_global_credit_limit=70000;c.save()
 names={}
 for label,role in (("accounts","Accounts User"),("chief","Accounts Manager")):
  email=f["user"].replace("@","-"+label+"@")
  u=frappe.get_doc({"doctype":"User","email":email,"first_name":"CI "+label,"enabled":1,"user_type":"System User","send_welcome_email":0,"roles":[{"role":role}]}).insert()
  update_password(u.name,f["password"]);names[label]=u.name
 so=frappe.db.get_value("Sales Order Item",{"item_code":f["item"]},"parent")
 dn=make_delivery_note(so)
 for row in dn.items:row.qty=.75
 dn.insert();frappe.db.commit()
 names.update(dn=dn.name,so=so)
 print("RISK_JSON:"+json.dumps(names))
finally:frappe.destroy()
'''
    raw=inner(risk_code,json.dumps({**fixture,"password":factory_password}))
    risk=json.loads(next(x[10:] for x in raw.splitlines() if x.startswith("RISK_JSON:")))
    accounts=session(risk["accounts"],factory_password)
    chief=session(risk["chief"],factory_password)
    def denied(call, method, args, expected=("PermissionError","ValidationError")):
        try:
            call(method,args)
        except urllib.error.HTTPError as exc:
            error=json.loads(exc.read())
            assert error.get("exc_type") in expected,error
            return error
        raise AssertionError("Request unexpectedly succeeded: "+method)
    def reject_submit(label):
        base=oracle();snap=snapshot()
        denied(admin,"/api/method/frappe.client.submit",{"doc":json.dumps(getdoc("Delivery Note",risk["dn"]))},("ValidationError",))
        assert oracle()==base and snapshot()==snap
        assert getdoc("Delivery Note",risk["dn"])["docstatus"]==0
        emit(label,"PASS","Draft retained; stock/debt/counts/series unchanged")
    reject_submit("HTTP_HIGH_RISK_NO_APPROVAL")
    direct_code='''import sys,json,frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect();frappe.set_user("Administrator")
try:
 f=json.load(sys.stdin);si=make_sales_invoice(f["so"])
 for row in si.items:row.qty=.25;row.delivery_note=None;row.dn_detail=None
 si.update_stock=0;si.insert();frappe.db.commit()
 print("DIRECT_JSON:"+json.dumps({"name":si.name}))
finally:frappe.destroy()
'''
    raw=inner(direct_code,json.dumps(risk))
    direct=json.loads(next(x[12:] for x in raw.splitlines() if x.startswith("DIRECT_JSON:")))["name"]
    base=oracle();snap=snapshot()
    err=denied(admin,"/api/method/frappe.client.submit",{"doc":json.dumps(getdoc("Sales Invoice",direct))},("ValidationError",))
    assert "hóa đơn tăng công nợ phải gắn phiếu giao" in (err.get("exception","")+err.get("_server_messages","")),err
    assert oracle()==base and snapshot()==snap
    emit("HTTP_SECURITY_DIRECT_SI_BLOCKED","PASS","No debt/stock/counts/series change")
    admin("/api/method/frappe.client.delete",{"doctype":"Sales Invoice","name":direct})
    for field,value in (("kh_aph_credit_high_risk",1),("kh_aph_global_credit_limit",70000)):
        base=oracle();snap=snapshot()
        denied(accounts,"/api/method/frappe.client.set_value",{"doctype":"Customer","name":fixture["customer"],"fieldname":field,"value":0})
        assert float(getdoc("Customer",fixture["customer"])[field])==value
        assert oracle()==base and snapshot()==snap
        emit("HTTP_SECURITY_CUSTOMER_"+field,"PASS","Unauthorized control edit denied")
    snap=snapshot()
    denied(accounts,"/api/method/frappe.client.insert",{"doc":json.dumps({"doctype":"APH Credit Release","delivery_note":risk["dn"],"reason":"forged","approved_by":"Administrator","fingerprint":"forged"})})
    assert snapshot()==snap
    emit("HTTP_SECURITY_GENERIC_APPROVAL_FORGERY_DENIED","PASS","No forged record")
    snap=snapshot()
    denied(accounts,"/api/method/kh_aph.credit_release.approve",{"delivery_note":risk["dn"],"reason":"unauthorized"})
    assert snapshot()==snap
    emit("HTTP_HIGH_RISK_UNAUTHORIZED_APPROVAL","PASS","No approval created")
    def approve():
        return chief("/api/method/kh_aph.credit_release.approve",{"delivery_note":risk["dn"],"reason":"CI chief verified approval"})["message"]
    approval=approve()
    assert approval["approved_by"]==risk["chief"]
    baseline=snapshot();saved_release=getdoc("APH Credit Release",approval["name"])
    for label,client in (("CHIEF",chief),("ADMIN",admin)):
        denied(client,"/api/method/frappe.client.delete",{"doctype":"APH Credit Release","name":approval["name"]},("PermissionError",))
        assert snapshot()==baseline and getdoc("APH Credit Release",approval["name"])==saved_release
        emit("HTTP_APPROVAL_DELETE_"+label+"_DENIED","PASS","Approval retained; counts and series unchanged")
    emit("HTTP_HIGH_RISK_CHIEF_APPROVAL","PASS",{"approved_by":approval["approved_by"]})
    dn=getdoc("Delivery Note",risk["dn"])
    dn["items"][0]["qty"]=.5
    admin("/api/method/frappe.client.save",{"doc":json.dumps(dn)})
    reject_submit("HTTP_HIGH_RISK_CHANGED_QTY_INVALIDATES_APPROVAL")
    snap=snapshot()
    denied(accounts,"/api/method/kh_aph.credit_release.revoke",{"approval":approval["name"],"reason":"unauthorized"})
    assert snapshot()==snap
    emit("HTTP_HIGH_RISK_UNAUTHORIZED_REVOKE","PASS","No audit edit")
    approval=approve()
    chief("/api/method/kh_aph.credit_release.revoke",{"approval":approval["name"],"reason":"CI revoked before dispatch"})
    assert getdoc("APH Credit Release",approval["name"])["revoked_at"]
    emit("HTTP_HIGH_RISK_CHIEF_REVOKE","PASS","Chief revocation stamped")
    reject_submit("HTTP_HIGH_RISK_REVOKED_APPROVAL_BLOCKS")
    approval=approve()
    emit("HTTP_HIGH_RISK_CHIEF_REAPPROVAL","PASS",{"approved_by":approval["approved_by"]})
    submit("Delivery Note",risk["dn"])
    emit("HTTP_HIGH_RISK_APPROVED_DISPATCH","PASS",check(10000,99.5,1))
    base=oracle();snap=snapshot()
    denied(chief,"/api/method/kh_aph.credit_release.revoke",{"approval":approval["name"],"reason":"too late"},("ValidationError",))
    assert oracle()==base and snapshot()==snap
    emit("HTTP_HIGH_RISK_REVOKE_AFTER_DISPATCH_DENIED","PASS","Audit/stock/debt unchanged")
    for inv in oracle()["invoices"]:
        if inv["docstatus"]==1:cancel("Sales Invoice",inv["name"])
    cancel("Delivery Note",risk["dn"])
    emit("HTTP_HIGH_RISK_DISPATCH_REVERSE","PASS",check(0,100,0))
    race_code='''import json,sys,frappe
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
frappe.connect();frappe.set_user("Administrator")
try:
 f=json.load(sys.stdin);dn=make_delivery_note(f["so"])
 for row in dn.items:row.qty=.5
 dn.insert();frappe.db.commit();print("RACE_JSON:"+json.dumps({"name":dn.name}))
finally:frappe.destroy()
'''
    raw=inner(race_code,json.dumps(risk))
    risk["dn"]=json.loads(next(x[10:] for x in raw.splitlines() if x.startswith("RACE_JSON:")))["name"]
    approval=approve();race_doc=getdoc("Delivery Note",risk["dn"])
    gate=threading.Barrier(2)
    def race(action):
        gate.wait(timeout=20)
        try:
            if action=="submit":admin("/api/method/frappe.client.submit",{"doc":json.dumps(race_doc)})
            else:chief("/api/method/kh_aph.credit_release.revoke",{"approval":approval["name"],"reason":"Concurrent CI revoke"})
            return {"action":action,"status":"ok"}
        except urllib.error.HTTPError as exc:
            err=json.loads(exc.read());kind=err.get("exc_type")
            assert kind in ("ValidationError","QueryDeadlockError","DeadlockError"),err
            return {"action":action,"status":"rejected","type":kind}
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(race,("submit","revoke")))
    assert any(o["status"]=="ok" for o in outcomes),outcomes
    posted=getdoc("Delivery Note",risk["dn"])["docstatus"]==1
    revoked=bool(getdoc("APH Credit Release",approval["name"]).get("revoked_at"))
    assert not (posted and revoked),"Dispatch and revocation both took effect"
    if posted:
        assert not revoked;result=check(10000,99.5,1)
    else:
        assert revoked;result=check(0,100,0)
    emit("HTTP_CONCURRENT_REVOKE_DISPATCH","PASS",{"requests":outcomes,"posted":posted,"revoked":revoked,"ledger":result})
    if posted:
        for inv in oracle()["invoices"]:
            if inv["docstatus"]==1:cancel("Sales Invoice",inv["name"])
        cancel("Delivery Note",risk["dn"])
        check(0,100,0)
    slip_fixture_code="""import json,sys,frappe,uuid
from frappe.utils import today,add_days
from frappe.utils.password import update_password
from kh_aph.constants import INV_FLAG,INV_NO
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites')
frappe.connect();frappe.set_user('Administrator')
try:
 f=json.load(sys.stdin)
 customer=frappe.get_doc('Customer',f['customer']);customer.kh_aph_credit_high_risk=0;customer.save()
 rows=[];sources=[];names={};prefix='CI-4CO-'+uuid.uuid4().hex[:8]
 for label,role in [('warehouse','Thủ kho bán hàng'),('sales','Nhân viên bán hàng')]:
  email=prefix.lower()+'-'+label+'@example.invalid'
  user=frappe.get_doc({'doctype':'User','email':email,'first_name':label,'enabled':1,'user_type':'System User','send_welcome_email':0,'roles':[{'role':role}]}).insert()
  update_password(user.name,f['password']);names[label]=user.name
 for abbr in ['APH','VH','MK','TL']:
  co=frappe.get_doc('Company',frappe.db.get_value('Company',{'abbr':abbr},'name'))
  if abbr=='APH':wh=f['warehouse'];item=f['item']
  else:
   wh=frappe.get_doc({'doctype':'Warehouse','warehouse_name':prefix+'-'+abbr,'company':co.name,'is_group':0,
    'parent_warehouse':frappe.db.get_value('Warehouse',{'company':co.name,'is_group':1},'name'),'account':co.default_inventory_account}).insert().name
   taxes=[]
   if abbr=='VH':
    account=frappe.db.get_value('Account',{'company':co.name,'account_number':'33311','is_group':0},'name')
    tax=frappe.get_doc({'doctype':'Item Tax Template','title':prefix+'-VH10','company':co.name,'taxes':[{'tax_type':account,'tax_rate':10}]}).insert()
    taxes=[{'item_tax_template':tax.name,'tax_category':customer.tax_category}]
   item=frappe.get_doc({'doctype':'Item','item_code':prefix+'-'+abbr,'item_name':prefix+'-'+abbr,'item_group':frappe.db.get_value('Item',f['item'],'item_group'),
    'stock_uom':'Kg','is_stock_item':1,'valuation_method':'Moving Average','taxes':taxes,
    'item_defaults':[{'company':co.name,'default_warehouse':wh,'income_account':co.default_income_account,'expense_account':co.default_expense_account,'buying_cost_center':co.cost_center,'selling_cost_center':co.cost_center}]}).insert().name
   stock=frappe.get_doc({'doctype':'Stock Entry','stock_entry_type':'Material Receipt','company':co.name,'posting_date':today(),
    'items':[{'item_code':item,'qty':10,'uom':'Kg','stock_uom':'Kg','conversion_factor':1,'t_warehouse':wh,'basic_rate':10000,'set_basic_rate_manually':1,'expense_account':co.stock_adjustment_account,'cost_center':co.cost_center}]}).insert();stock.submit()
  rows.append({'item_code':item,'warehouse':wh,'qty':1,'rate':20000})
  sources.append({'abbr':abbr,'company':co.name,'item':item,'warehouse':wh})
 shared=frappe.get_doc({'doctype':'APH Shared Sales Order','customer':f['customer'],
  'transaction_date':today(),'delivery_date':add_days(today(),1),'currency':'VND',
  'selling_price_list':frappe.db.get_value('Price List',{'selling':1,'enabled':1},'name'),'items':rows}).insert()
 shared.submit();notes=[]
 for source in sources:
  so=frappe.db.get_value('Sales Order',{'kh_aph_shared_order':shared.name,'company':source['company']},'name')
  source['notes']=[]
  for i in range(2):
   dn=make_delivery_note(so)
   for row in dn.items:row.qty=.25
   dn.insert();notes.append(dn.name);source['notes'].append(dn.name)
 names.update(shared=shared.name,notes=notes,sources=sources)
 frappe.db.commit();print('SLIP_JSON:'+json.dumps(names))
finally:frappe.destroy()
"""
    raw=inner(slip_fixture_code,json.dumps({**fixture,"password":factory_password}))
    slip=json.loads(next(x[10:] for x in raw.splitlines() if x.startswith('SLIP_JSON:')))
    warehouse=session(slip['warehouse'],factory_password)
    sales=session(slip['sales'],factory_password)
    for source in slip['sources']:
        for name,action in zip(source['notes'],('handoff','pickup')):
            result=warehouse('/api/method/kh_aph.delivery_status.confirm',{'name':name,'action':action})['message']
            assert result['kh_aph_delivery_actor']==slip['warehouse']
            assert result['kh_aph_delivery_state']==('Đang giao' if action=='handoff' else 'Khách đã nhận')
        received=sales('/api/method/kh_aph.delivery_status.confirm',{'name':source['notes'][0],'action':'receive'})['message']
        assert received['kh_aph_delivery_actor']==slip['sales'] and received['kh_aph_delivery_state']=='Khách đã nhận'
    emit('HTTP_EMPLOYEE_FOUR_COMPANY_HANDOFF_PICKUP','PASS','Warehouse role submits all four company batches')
    emit('HTTP_SALES_RECEIPT_ONLY','PASS','Read-only sales role confirms receipt with own actor stamp')
    before_print=check(10000,99.5,8)
    denied(sales,'/api/method/frappe.client.save',{'doc':json.dumps(getdoc('Delivery Note',slip['notes'][0]))},('PermissionError',))
    assert oracle()==before_print
    emit('HTTP_SALES_GENERIC_WRITE_DENIED','PASS','Receipt capability does not grant generic document write')
    denied(accounts,'/api/method/kh_aph.delivery_status.confirm',{'name':slip['notes'][0],'action':'receive'},('PermissionError',))
    emit('HTTP_UNAUTHORIZED_RECEIPT_DENIED','PASS','Unrelated read-only role cannot confirm receipt')
    available=admin('/api/method/kh_aph.delivery_slip.deliveries?'+urllib.parse.urlencode({'shared_order':slip['shared']}))['message']
    assert {n['name'] for n in available}==set(slip['notes']),available
    emit('HTTP_SLIP_SELECT_BATCHES','PASS','Only submitted deliveries of selected shared order listed')
    printed=admin('/api/method/kh_aph.delivery_slip.consolidated',{'shared_order':slip['shared'],'delivery_notes':json.dumps(slip['notes'])})['message']
    assert all(n in printed['html'] for n in slip['notes']) and fixture['warehouse'] in printed['html']
    assert 'basic_rate' not in printed['html'] and 'valuation_rate' not in printed['html']
    emit('HTTP_SLIP_CONSOLIDATED','PASS','Eight batches from four companies include source/quantity; no cost fields')
    single=admin('/api/method/kh_aph.delivery_slip.consolidated',{'shared_order':slip['shared'],'delivery_notes':json.dumps(slip['notes'][:1])})['message']
    assert slip['notes'][0] in single['html'] and slip['notes'][1] not in single['html']
    emit('HTTP_SLIP_SINGLE_SELECTION','PASS','Selected batch only printed')
    try:
        admin('/api/method/kh_aph.delivery_slip.consolidated',{'shared_order':slip['shared'],'delivery_notes':json.dumps([fixture['dn1']])})
        raise AssertionError('Unrelated canceled delivery accepted')
    except urllib.error.HTTPError as exc:
        error=json.loads(exc.read());assert error.get('exc_type')=='ValidationError',error
    emit('HTTP_SLIP_UNRELATED_DENIED','PASS','Unrelated/canceled delivery rejected')
    assert oracle()==before_print,'Printing changed accounting or stock'
    emit('HTTP_SLIP_READ_ONLY','PASS','All print/list requests left stock/debt unchanged')
    employee_print=warehouse('/api/method/kh_aph.delivery_slip.consolidated',{'shared_order':slip['shared'],'delivery_notes':json.dumps(slip['notes'])})['message']
    assert employee_print['html']==printed['html']
    assert all(source['company'] in printed['html'] and source['warehouse'] in printed['html'] for source in slip['sources'])
    emit('HTTP_SLIP_FOUR_COMPANY_EMPLOYEE','PASS','Warehouse role prints all four company sources without cost')
    Path('shared-four-company-slip.html').write_text(printed['html'])
    scope_code="""import json,sys,frappe
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect();frappe.set_user('Administrator')
try:
 f=json.load(sys.stdin)
 frappe.get_doc({'doctype':'User Permission','user':f['user'],'allow':'Company','for_value':f['company'],'apply_to_all_doctypes':1}).insert()
 frappe.db.commit();frappe.clear_cache(user=f['user'])
finally:frappe.destroy()
"""
    aph=next(x for x in slip['sources'] if x['abbr']=='APH')
    vh=next(x for x in slip['sources'] if x['abbr']=='VH')
    inner(scope_code,json.dumps({'user':slip['warehouse'],'company':aph['company']}))
    scoped=session(slip['warehouse'],factory_password)
    baseline=oracle()
    denied(scoped,'/api/method/kh_aph.delivery_status.confirm',{'name':vh['notes'][0],'action':'receive'},('PermissionError',))
    denied(scoped,'/api/method/kh_aph.delivery_slip.consolidated',{'shared_order':slip['shared'],'delivery_notes':json.dumps(vh['notes'])},('PermissionError',))
    allowed=scoped('/api/method/kh_aph.delivery_slip.deliveries?'+urllib.parse.urlencode({'shared_order':slip['shared']}))['message']
    assert {n['name'] for n in allowed}==set(aph['notes']),allowed
    scoped('/api/method/kh_aph.delivery_slip.consolidated',{'shared_order':slip['shared'],'delivery_notes':json.dumps(aph['notes'])})
    assert oracle()==baseline
    emit('HTTP_COMPANY_SCOPE_RECEIPT_PRINT','PASS','APH-only user cannot confirm/print VH; listing limited to APH; ledgers unchanged')
    multi_code="""import json,sys,frappe
frappe.init(site='aphvh-web-uat',sites_path='/home/frappe/frappe-bench/sites');frappe.connect()
try:
 f=json.load(sys.stdin);rows=[]
 for source in f['sources']:
  qty=frappe.db.get_value('Bin',{'item_code':source['item'],'warehouse':source['warehouse']},'actual_qty')
  debt=frappe.db.sql("SELECT COALESCE(SUM(debit-credit),0) FROM `tabGL Entry` WHERE party_type='Customer' AND party=%s AND company=%s AND is_cancelled=0",(f['customer'],source['company']))[0][0]
  assert float(qty)==(99.5 if source['abbr']=='APH' else 9.5) and float(debt)==10000,(source,qty,debt)
  rows.append({'abbr':source['abbr'],'stock_kg':float(qty),'debt':float(debt)})
 print('MULTI:'+json.dumps(rows))
finally:frappe.destroy()
"""
    raw=inner(multi_code,json.dumps({**slip,'customer':fixture['customer']}))
    emit('HTTP_FOUR_COMPANY_EMPLOYEE_STOCK_DEBT','PASS',json.loads(next(l[6:] for l in raw.splitlines() if l.startswith('MULTI:'))))
except Exception as exc:
    emit("HTTP_DISPATCH_RUNNER","FAIL",{"type":type(exc).__name__,"error":str(exc)[:1000]})
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
