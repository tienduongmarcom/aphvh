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
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry"]
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
    second=submit("Delivery Note",fixture["dn2"])
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
