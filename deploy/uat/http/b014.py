FIXTURE_CODE = r"""
import json, sys, uuid, frappe
from frappe.utils import today
from frappe.utils.password import update_password
from kh_aph.constants import INV_FLAG, INV_YES, ROLE_FACTORY, ROLE_NO_COST
frappe.init(site="aphvh-web-uat", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect(); frappe.set_user("Administrator")
payload = json.load(sys.stdin)
p = "UAT-014-" + uuid.uuid4().hex[:6]
aph = frappe.db.get_value("Company", {"abbr": "APH"}, "name")
def acc(n, c=None): return frappe.db.get_value("Account", {"company": c or aph, "account_number": n, "is_group": 0}, "name")
from kh_aph.kho_chuan import dung
dung("/home/frappe/frappe-bench/apps/kh_aph/khach/aph-vh/khach.json", "aphvh-web-uat")
from kh_aph import tien_vay
cfg = {"khach_hang": "UAT", "cong_ty": [{"ten": "x", "abbr": a, "thong_tu": 99} for a in ("APH", "VH")],
       "ngan_hang": [{"don_vi": "APH", "ngan_hang": "ACB", "so_cuoi": "1111"}, {"don_vi": "APH", "ngan_hang": "ACB", "so_cuoi": "2222", "loai_tien": "USD"},
                     {"don_vi": "VH", "ngan_hang": "MB", "so_cuoi": "3333"}]}
nh1 = tien_vay.dung_ngan_hang(cfg=cfg); nh2 = tien_vay.dung_ngan_hang(cfg=cfg)
cg = frappe.db.get_value("Customer Group", {"is_group": 0}, "name"); te = frappe.db.get_value("Territory", {"is_group": 0}, "name")
def kh(ten): return frappe.get_doc({"doctype": "Customer", "customer_name": p + "-" + ten, "customer_type": "Company",
    "customer_group": cg, "territory": te, INV_FLAG: INV_YES}).insert().name
kh1, kh2 = kh("KH1"), kh("KH2")
ncc = frappe.get_doc({"doctype": "Supplier", "supplier_name": p + "-NCC", "supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0})}).insert().name
g = frappe.get_doc({"doctype": "Item Group", "item_group_name": p + "-HH", "parent_item_group": "HH - Hàng hóa", "is_group": 0}).insert().name
t_aph = frappe.get_doc({"doctype": "Item Tax Template", "title": f"{p}-10", "company": aph,
    "taxes": [{"tax_type": acc("33311"), "tax_rate": 10}]}).insert().name
A = frappe.get_doc({"doctype": "Item", "item_code": p + "-A", "item_name": p + "-A", "item_group": g,
    "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average", "taxes": [{"item_tax_template": t_aph}]}).insert().name
kho = "Kho bán hàng Hà Nội - APH"
sr = frappe.get_doc({"doctype": "Stock Reconciliation", "company": aph, "purpose": "Opening Stock", "expense_account": acc("9990"),
    "items": [{"item_code": A, "warehouse": kho, "qty": 1000, "valuation_rate": 20000}]}); sr.insert(); sr.submit()
pl = frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name")
def user(ten, roles):
    u = frappe.get_doc({"doctype": "User", "email": (p + "-" + ten).lower() + "@example.invalid", "first_name": p + " " + ten, "enabled": 1,
                        "user_type": "System User", "send_welcome_email": 0, "roles": [{"role": r} for r in roles]})
    u.flags.no_welcome_mail = True; u.insert(); update_password(u.name, payload["password"]); return u.name
ktt = user("ktt", ["Accounts Manager", "Accounts User", "Sales User", "Sales Manager", "Stock Manager", "Stock User", "System Manager", "Item Manager"])
ktt2 = user("ktt2", ["Accounts User", "Sales User", "Stock User"])
ktbh = user("ktbh", ["Kế toán bán hàng", "Sales User", "Stock User"])
ktbh_no_submit = user("ktbh-no-submit", ["Kế toán bán hàng", "Accounts User"])
tp = user("tp", ["Sales Manager", "Sales User"])
nvbh = user("nvbh", ["Sales Manager", "Sales User", "Stock User"])
dung_u = user("dung", [ROLE_FACTORY, ROLE_NO_COST, "Accounts Manager", "Sales User", "Stock User"])
# Nguồn và tài khoản có phạm vi hẹp để kiểm facade nhiều kho/pháp nhân.
vh = frappe.db.get_value("Company", {"abbr": "VH"}, "name")
def wh_test(suffix, company):
    parent = frappe.db.get_value("Warehouse", {"company": company, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name")
    return frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p + suffix,
                          "company": company, "parent_warehouse": parent, "is_group": 0}).insert().name
kho2, kho_vh = wh_test("-APH2", aph), wh_test("-VH", vh)
t_vh = frappe.get_doc({"doctype": "Item Tax Template", "title": p + "-VH10", "company": vh,
    "taxes": [{"tax_type": acc("33311", vh), "tax_rate": 10}]}).insert().name
B = frappe.get_doc({"doctype": "Item", "item_code": p + "-B", "item_name": p + "-B", "item_group": g,
    "stock_uom": "Kg", "is_stock_item": 1, "valuation_method": "Moving Average",
    "taxes": [{"item_tax_template": t_vh}]}).insert().name
scope_co = user("scope-co", ["Kế toán bán hàng", "Sales User", "Stock User", "Accounts Manager", "Accounts User"])
scope_wh = user("scope-wh", ["Kế toán bán hàng", "Sales User", "Stock User"])
frappe.get_doc({"doctype": "User Permission", "user": scope_co, "allow": "Company", "for_value": aph,
                "apply_to_all_doctypes": 1}).insert()
# Kho mặc định của Company là cấu hình chung, không phải kho nguồn trên đơn/phiếu.
# Giới hạn kho trên đúng các DocType cần xử lý; không cấp thêm kho ngoài phạm vi.
for target in ("Warehouse", "Sales Order", "Delivery Note", "APH Shared Sales Order"):
    frappe.get_doc({"doctype": "User Permission", "user": scope_wh, "allow": "Warehouse", "for_value": kho,
                    "apply_to_all_doctypes": 0, "applicable_for": target}).insert()
ss = frappe.get_doc("Selling Settings")
ss.set("kh_aph_nguoi_duyet_gia_san", [{"user": tp, "muc": 0, "tu_duyet": 0}])
ss.save()
gd = frappe.db.get_value("Gender", {}, "name")
nv = frappe.get_doc({"doctype": "Employee", "first_name": p + " Giám đốc", "gender": gd, "date_of_birth": "1980-01-01",
                     "date_of_joining": "2020-01-01", "company": aph, "status": "Active"}).insert().name
frappe.db.commit()
bank = frappe.db.get_value("Account", {"company": aph, "account_name": "ACB 1111"}, "name")
print("FIXTURE_JSON:" + json.dumps({"p": p, "aph": aph, "kh1": kh1, "kh2": kh2, "ncc": ncc, "A": A, "kho": kho, "t_aph": t_aph, "pl": pl,
    "ktt": ktt, "ktt2": ktt2, "ktbh": ktbh, "ktbh_no_submit": ktbh_no_submit, "tp": tp, "nvbh": nvbh, "dung": dung_u, "nv": nv, "date": today(),
    "vh": vh, "B": B, "kho2": kho2, "kho_vh": kho_vh, "scope_co": scope_co, "scope_wh": scope_wh,
    "nh": [nh1, nh2], "usd": frappe.db.get_value("Account", {"company": aph, "account_name": "ACB 2222 USD"}, ["name", "account_currency", "parent_account"]),
    "bank_account": frappe.db.get_value("Bank Account", {"account": bank}),
    "bank_vh": frappe.db.get_value("Account", {"company": vh, "account_name": "MB 3333"}, "name"),
    "acc": {"holding": acc("3388"), "tien": acc("1111"), "bank": bank, "vay": acc("3411"), "cp": acc("6422"), "lai": acc("6351"), "lai_tra": acc("3352")}},
    ensure_ascii=False, default=str))
frappe.destroy()
"""

"""Ca HTTP bản 0.14 trên site UAT dùng một lần, bắt buộc khôi phục CSDL sau khi chạy (cùng khung với bộ 0.11.1)."""
import json, os, secrets, subprocess, uuid, time
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["APH Xac minh quy","APH Chot ca tien","APH Phan bo quy","User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order","Purchase Receipt","Stock Reconciliation","BOM","UOM","Landed Cost Voucher","Journal Entry","Cost Center","Account","APH Phieu quy nha may","APH Khoan muc chi nha may","APH Shared Sales Order","Address","Payment Entry","Payment Ledger Entry","APH Hoa don ngoai","Payment Terms Template","Accounting Period","APH De nghi so lieu","APH So du dau ky nguon","APH Gia san","Material Request","APH Khe uoc vay","Employee","Bank","Bank Account","File","Workspace","APH Hoa don ngoai","Stock Closing Entry","Stock Closing Balance","User Permission"]
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
restore_path="/tmp/aphvh-http-014-"+uuid.uuid4().hex+".sql.gz"
run(["docker","cp",str(backup),BACKEND+":"+restore_path])
# Verify destination before committing fixtures.
run(["docker","exec",BACKEND,"test","-s",restore_path])
restore_record=source.parent/"b014_uat_restore.json"
restore_record.write_text(json.dumps({"site":SITE,"backup":str(backup),"backend_path":restore_path,"before":before},indent=2))
os.chmod(restore_record,0o600)
try:
    raw=inner(FIXTURE_CODE,json.dumps({"password":factory_password}))
    fixture=json.loads(next(x[13:] for x in raw.splitlines() if x.startswith("FIXTURE_JSON:")))
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import b014_cases
    b014_cases.chay(admin,lambda user:session(user,factory_password),fixture,emit)
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
    emit("HTTP_014_RUNNER","FAIL",detail)
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
print("Bộ ca HTTP 0.14 chạy xong; người dùng thật và tải lớn nằm ngoài phạm vi bộ này.")
