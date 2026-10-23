FIXTURE_CODE = r"""
import json, sys, uuid, frappe
from frappe.utils import today
from frappe.utils.password import update_password
from kh_aph.constants import INV_FLAG, INV_YES, ROLE_FACTORY, ROLE_NO_COST
frappe.init(site="aphvh-web-uat", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect(); frappe.set_user("Administrator")
payload = json.load(sys.stdin)
p = "UAT-0114-" + uuid.uuid4().hex[:6]
aph = frappe.db.get_value("Company", {"abbr": "APH"}, "name")
vh = frappe.db.get_value("Company", {"abbr": "VH"}, "name")
def acc(n, c): return frappe.db.get_value("Account", {"company": c, "account_number": n, "is_group": 0}, "name")
from kh_aph.kho_chuan import dung
dung("/home/frappe/frappe-bench/apps/kh_aph/khach/aph-vh/khach.json", "aphvh-web-uat")
def tpl(days):
    pt = frappe.get_doc({"doctype": "Payment Term", "payment_term_name": f"{p}-{days}N", "invoice_portion": 100,
                         "due_date_based_on": "Day(s) after invoice date", "credit_days": days}).insert().name
    return frappe.get_doc({"doctype": "Payment Terms Template", "template_name": f"{p}-{days}N",
        "terms": [{"payment_term": pt, "invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date",
                   "credit_days": days}]}).insert().name
t5, t20 = tpl(5), tpl(20)
cg = frappe.db.get_value("Customer Group", {"is_group": 0}, "name"); te = frappe.db.get_value("Territory", {"is_group": 0}, "name")
def kh(ten, terms=None, name=None): return frappe.get_doc({"doctype": "Customer", "customer_name": name or (p + "-" + ten),
    "customer_type": "Company", "customer_group": cg, "territory": te, INV_FLAG: INV_YES, "payment_terms": terms}).insert().name
kh0, kh1, kh2 = kh("KH0"), kh("KH1", t5), kh("KH2", t20)
noi_bo = kh("NB", name=vh)  # khách trùng tên đơn vị VH: khoản nội bộ, dòng tiền phải loại
def thue(c): return frappe.get_doc({"doctype": "Item Tax Template", "title": f"{p}-10", "company": c,
    "taxes": [{"tax_type": acc("33311", c), "tax_rate": 10}]}).insert().name
t_aph, t_vh = thue(aph), thue(vh)
g = frappe.get_doc({"doctype": "Item Group", "item_group_name": p + "-HH", "parent_item_group": "HH - Hàng hóa", "is_group": 0}).insert().name
A = frappe.get_doc({"doctype": "Item", "item_code": p + "-A", "item_name": p + "-A", "item_group": g, "stock_uom": "Kg",
    "is_stock_item": 1, "valuation_method": "Moving Average", "taxes": [{"item_tax_template": t_aph}, {"item_tax_template": t_vh}]}).insert().name
kho, khov = "Kho bán hàng Hà Nội - APH", "Kho bán hàng Hà Nội - VH"
for c, w in ((aph, kho), (vh, khov)):
    d = frappe.get_doc({"doctype": "Stock Reconciliation", "company": c, "purpose": "Opening Stock", "expense_account": acc("9990", c),
        "items": [{"item_code": A, "warehouse": w, "qty": 1000, "valuation_rate": 20000}]}); d.insert(); d.submit()
pl = frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name")
def user(ten, roles):
    u = frappe.get_doc({"doctype": "User", "email": (p + "-" + ten).lower() + "@example.invalid", "first_name": p + " " + ten, "enabled": 1,
                        "user_type": "System User", "send_welcome_email": 0, "roles": [{"role": r} for r in roles]})
    u.flags.no_welcome_mail = True; u.insert(); update_password(u.name, payload["password"]); return u.name
ktt = user("ktt", ["Accounts Manager", "Accounts User", "Sales User", "Sales Manager", "Stock Manager", "Stock User"])
ceo = user("ceo", ["Xem báo cáo điều hành"])
ceo_cost_denied = user("ceo-no-cost", ["Xem báo cáo điều hành", ROLE_NO_COST])
ktt2 = user("ktt2", ["Accounts User", "Sales User", "Stock User"])
ban = user("ban", ["Nhân viên bán hàng", "Sales User"])
dung_u = user("dung", [ROLE_FACTORY, ROLE_NO_COST, "Sales User"])
scope_aph=user("scope-aph", ["Accounts Manager", "Accounts User", "Stock Manager", "Stock User"])
frappe.get_doc({"doctype": "User Permission", "user": scope_aph, "allow": "Company", "for_value": aph,
                "apply_to_all_doctypes": 1}).insert()
frappe.db.commit()
cp = acc("6421", aph) or frappe.db.get_value("Account", {"company": aph, "root_type": "Expense", "is_group": 0}, "name")
print("FIXTURE_JSON:" + json.dumps({"p": p, "aph": aph, "vh": vh, "kh0": kh0, "kh1": kh1, "kh2": kh2, "noi_bo": noi_bo,
    "A": A, "t_aph": t_aph, "t_vh": t_vh, "kho": kho, "khov": khov, "pl": pl, "scope_aph": scope_aph, "ktt": ktt, "ktt2": ktt2, "ban": ban,
    "dung": dung_u, "ceo": ceo, "ceo_cost_denied": ceo_cost_denied, "date": today(), "acc": {"cp": cp, "tien": acc("1111", aph)}}, ensure_ascii=False, default=str))
frappe.destroy()
"""

"""Ca HTTP bản 0.11.4 trên site UAT dùng một lần, bắt buộc khôi phục CSDL sau khi chạy (cùng khung với bộ 0.11.1)."""
import json, os, secrets, subprocess, uuid
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order","Purchase Receipt","Stock Reconciliation","BOM","UOM","Landed Cost Voucher","Journal Entry","Cost Center","Account","APH Phieu quy nha may","APH Khoan muc chi nha may","APH Shared Sales Order","Address","Payment Entry","Payment Ledger Entry","APH Hoa don ngoai","Payment Terms Template","Accounting Period","User Permission"]
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
restore_path="/tmp/aphvh-http-0114-"+uuid.uuid4().hex+".sql.gz"
run(["docker","cp",str(backup),BACKEND+":"+restore_path])
# Verify destination before committing fixtures.
run(["docker","exec",BACKEND,"test","-s",restore_path])
restore_record=source.parent/"b0114_uat_restore.json"
restore_record.write_text(json.dumps({"site":SITE,"backup":str(backup),"backend_path":restore_path,"before":before},indent=2))
os.chmod(restore_record,0o600)
try:
    raw=inner(FIXTURE_CODE,json.dumps({"password":factory_password}))
    fixture=json.loads(next(x[13:] for x in raw.splitlines() if x.startswith("FIXTURE_JSON:")))
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import b0114_cases
    b0114_cases.chay(admin,lambda user:session(user,factory_password),fixture,emit)
except Exception as exc:
    detail={"type":type(exc).__name__,"error":str(exc)[-2500:]}
    if isinstance(exc,urllib.error.HTTPError):
        body=exc.read().decode(errors='replace')
        for secret in (factory_password,token_secret,state.get('admin_password','')):
            if secret:body=body.replace(secret,'[REDACTED]')
        try:
            data=json.loads(body);detail['http_error']={k:data.get(k) for k in ('exc_type','exception','_server_messages')}
        except ValueError:detail['http_error']=body[:1000]
    import traceback
    detail["trace"]="".join(traceback.format_exc().splitlines(True)[-12:])[-2000:]
    emit("HTTP_0114_RUNNER","FAIL",detail)
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
print("Bộ ca HTTP 0.11.4 chạy xong; người dùng thật và tải lớn nằm ngoài phạm vi bộ này.")
