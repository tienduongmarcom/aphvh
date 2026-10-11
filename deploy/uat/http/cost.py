FIXTURE_CODE = 'import json,sys,frappe\nfrom frappe.utils import today\nfrom frappe.utils.password import update_password\nfrom kh_aph.constants import INV_FLAG, INV_NO, ROLE_FACTORY\nfrappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")\nfrappe.connect();frappe.set_user("Administrator")\nimport uuid\npayload=json.load(sys.stdin)\nco = frappe.get_doc("Company", frappe.db.get_value("Company", {"abbr": "APH"}, "name"))\np = "UAT-P0-" + uuid.uuid4().hex[:8]\nwh = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p, "company": co.name,\n                    "is_group": 0, "parent_warehouse": frappe.db.get_value("Warehouse", {\n                        "company": co.name, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name"),\n                    "account": co.default_inventory_account}).insert().name\ngroup = frappe.get_doc({"doctype": "Item Group", "item_group_name": p,\n                       "parent_item_group": "HH - Hàng hóa", "is_group": 0}).insert().name\ncustomer = frappe.get_doc({"doctype": "Customer", "customer_name": p, "customer_type": "Company",\n                           "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),\n                           "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),\n                           INV_FLAG: INV_NO}).insert()\nvat_account = frappe.db.get_value("Account", {"company": co.name, "account_number": "33311", "is_group": 0}, "name")\ntax = frappe.get_doc({"doctype": "Item Tax Template", "title": p + "-TEST10", "company": co.name,\n                     "taxes": [{"tax_type": vat_account, "tax_rate": 10}]}).insert()\nitem = frappe.get_doc({"doctype": "Item", "item_code": p, "item_name": p, "item_group": group,\n                      "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average",\n                      "taxes": [{"item_tax_template": tax.name, "tax_category": customer.tax_category}],\n                      "item_defaults": [{"company": co.name, "default_warehouse": wh,\n                                         "income_account": co.default_income_account,\n                                         "expense_account": co.default_expense_account,\n                                         "buying_cost_center": co.cost_center,\n                                         "selling_cost_center": co.cost_center}]}).insert()\nse = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": co.name,\n                    "posting_date": today(), "items": [{"item_code": item.name, "qty": 100,\n                        "uom": "Kg", "stock_uom": "Kg", "conversion_factor": 1, "t_warehouse": wh,\n                        "basic_rate": 10000, "set_basic_rate_manually": 1,\n                        "expense_account": co.stock_adjustment_account, "cost_center": co.cost_center}]}).insert()\nse.submit()\nuser = frappe.get_doc({"doctype": "User", "email": p.lower() + "@example.invalid", "first_name": p,\n                      "enabled": 1, "user_type": "System User", "send_welcome_email": 0,\n                      "roles": [{"role": ROLE_FACTORY}]})\nuser.flags.no_welcome_mail = True\nuser.insert()\n\nupdate_password(user.name,payload["password"])\nfrappe.db.commit()\nprint("FIXTURE_JSON:"+json.dumps({"user":user.name,"stock_entry":se.name}))\nfrappe.destroy()\n'
"""HTTP cost-security test on a disposable clone, with mandatory database restoration."""
import json, os, secrets, subprocess, uuid
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
except Exception as exc:
    emit("HTTP_COST_RUNNER","FAIL",{"type":type(exc).__name__,"error":str(exc)[:1000]})
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
