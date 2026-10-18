FIXTURE_CODE = r"""
import json, sys, uuid, frappe
from frappe.utils import today
from frappe.utils.password import update_password
from kh_aph.constants import INV_FLAG, INV_NO, ROLE_FACTORY, ROLE_NO_COST
frappe.init(site="aphvh-web-uat", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect(); frappe.set_user("Administrator")
payload = json.load(sys.stdin)
p = "UAT-0112-" + uuid.uuid4().hex[:6]
co = frappe.get_doc("Company", frappe.db.get_value("Company", {"abbr": "APH"}, "name"))
vh = frappe.db.get_value("Company", {"abbr": "VH"}, "name")
def acc(n, c=None): return frappe.db.get_value("Account", {"company": c or co.name, "account_number": n, "is_group": 0}, "name")
# Kho cũ ngoài cây chuẩn: bộ dựng chỉ được báo, không sửa/xóa.
root_wh = frappe.db.get_value("Warehouse", {"company": co.name, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name")
kho_cu = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": p + "-KHO-CU", "company": co.name, "is_group": 0, "parent_warehouse": root_wh}).insert().name
from kh_aph.kho_chuan import dung
khach = "/home/frappe/frappe-bench/apps/kh_aph/khach/aph-vh/khach.json"
lan1 = dung(khach, "aphvh-web-uat"); lan2 = dung(khach, "aphvh-web-uat")
root_cc = frappe.db.get_value("Cost Center", {"company": co.name, "is_group": 1}, "name")
def cc(ten): return frappe.get_doc({"doctype": "Cost Center", "cost_center_name": p + "-" + ten, "company": co.name, "parent_cost_center": root_cc, "kh_aph_loai_ttcp": "Xưởng sản xuất"}).insert().name
cc_pt, cc_dau = cc("PT"), cc("DAU")
for u in ("Thùng", "Gói"):
    if not frappe.db.exists("UOM", u): frappe.get_doc({"doctype": "UOM", "uom_name": u, "must_be_whole_number": 1}).insert()
cha_bb = frappe.db.get_value("Item Group", {"name": ["like", "VT -%"], "is_group": 1}, "name") or "NL - Nguyên liệu"
def grp(ten, cha, **kw): return frappe.get_doc({"doctype": "Item Group", "item_group_name": p + "-" + ten, "parent_item_group": cha, "is_group": 0, **kw}).insert().name
g_nl, g_tp, g_hh, g_bb = grp("NL", "NL - Nguyên liệu"), grp("TP", "TP - Thành phẩm"), grp("HH", "HH - Hàng hóa"), grp("BB", cha_bb, kh_aph_bao_bi=1)
customer = frappe.get_doc({"doctype": "Customer", "customer_name": p, "customer_type": "Company", "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"), "territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"), INV_FLAG: INV_NO}).insert()
tax = frappe.get_doc({"doctype": "Item Tax Template", "title": p + "-10", "company": co.name, "taxes": [{"tax_type": acc("33311"), "tax_rate": 10}]}).insert()
items = {}
for label, g, uom, w in (("bot", g_nl, "Kg", None), ("banh", g_tp, "Kg", None), ("thung", g_tp, "Thùng", 18), ("tui", g_bb, "Kg", None),
                         ("vo", g_bb, "Nos", None), ("dau", g_nl, "Kg", None), ("dausach", g_tp, "Kg", None), ("xa", g_hh, "Kg", None),
                         ("goi", g_hh, "Gói", 0.5), ("tuinho", g_bb, "Nos", None)):
    d = {"doctype": "Item", "item_code": p + "-" + label, "item_name": p + "-" + label, "item_group": g, "stock_uom": uom, "is_stock_item": 1,
         "valuation_method": "Moving Average", "taxes": [{"item_tax_template": tax.name, "tax_category": customer.tax_category}]}
    if w: d.update(weight_per_unit=w, weight_uom="Kg")
    items[label] = frappe.get_doc(d).insert().name
K = lambda t, ab="APH": f"{t} - {ab}"
def sr(c, rows):
    d = frappe.get_doc({"doctype": "Stock Reconciliation", "company": c, "purpose": "Opening Stock", "expense_account": acc("9990", c),
                        "items": [{"item_code": items[i], "warehouse": w, "qty": q, "valuation_rate": r} for i, w, q, r in rows]})
    d.insert(); d.submit()
sr(co.name, [("bot", K("Kho nguyên liệu"), 1000, 20000), ("dau", K("Kho nguyên liệu"), 500, 30000),
             ("tui", K("Kho vật tư - bao bì - phụ tùng"), 100, 50000), ("vo", K("Kho vật tư - bao bì - phụ tùng"), 100, 5000),
             ("tuinho", K("Kho vật tư - bao bì - phụ tùng"), 1000, 300), ("xa", K("Kho chờ đóng gói"), 50, 40000)])
sr(vh, [("xa", K("Gửi tại Nhà máy Phú Thọ", "VH"), 50, 42000)])
# Định mức phồng tôm (file 2026: 1 mẻ 160 kg bột ra 180 kg bánh khô); tỷ lệ cho phép mặc định 0.
# Mã túi dùng ở hai BOM với hai quy cách khác nhau: báo cáo rà soát phải bắt được.
bom = frappe.get_doc({"doctype": "BOM", "item": items["banh"], "company": co.name, "quantity": 180, "is_default": 1, "is_active": 1,
                      "items": [{"item_code": items["bot"], "qty": 160}]})
bom.insert(); bom.submit()
bom2 = frappe.get_doc({"doctype": "BOM", "item": items["thung"], "company": co.name, "quantity": 1, "is_default": 1, "is_active": 1,
                       "items": [{"item_code": items["banh"], "qty": 18}, {"item_code": items["tui"], "qty": 0.2, "description": "Túi PP 18 kg"},
                                 {"item_code": items["vo"], "qty": 1}]})
bom2.insert(); bom2.submit()
bom3 = frappe.get_doc({"doctype": "BOM", "item": items["goi"], "company": co.name, "quantity": 1, "is_default": 1, "is_active": 1,
                       "items": [{"item_code": items["xa"], "qty": 0.5}, {"item_code": items["tui"], "qty": 0.01, "description": "Túi PP gói 500 g"}]})
bom3.insert(); bom3.submit()
def user(ten, roles):
    u = frappe.get_doc({"doctype": "User", "email": (p + "-" + ten).lower() + "@example.invalid", "first_name": p + " " + ten, "enabled": 1,
                        "user_type": "System User", "send_welcome_email": 0, "roles": [{"role": r} for r in roles]})
    u.flags.no_welcome_mail = True; u.insert(); update_password(u.name, payload["password"]); return u.name
dung_u = user("dung", [ROLE_FACTORY, ROLE_NO_COST, "Sales User"])
ktt = user("ktt", ["Accounts Manager", "Accounts User", "Sales User", "Stock Manager", "Stock User"])
ban = user("ban", ["Nhân viên bán hàng", "Sales User"])
frappe.db.commit()
w = lambda n: frappe.db.get_value("Warehouse", n, ["kh_aph_loai_kho", "kh_aph_day_chuyen", "warehouse_type"], as_dict=True)
print("FIXTURE_JSON:" + json.dumps({"p": p, "company": co.name, "vh": vh, "items": items, "cc_pt": cc_pt, "cc_dau": cc_dau,
    "customer": customer.name, "tax": tax.name, "bom": bom.name, "dung": dung_u, "ktt": ktt, "ban": ban, "kho_cu": kho_cu,
    "lan1": {"tao": len(lan1["da_tao"]), "canh_bao": lan1["canh_bao"]}, "lan2": {"tao": len(lan2["da_tao"]), "canh_bao": lan2["canh_bao"]},
    "kho_pt": w(K("Dở dang dây chuyền phồng tôm")), "kho_vc": w(K("Hàng đang vận chuyển")),
    "transit_mac_dinh": frappe.db.get_value("Company", co.name, "default_in_transit_warehouse"),
    "acc": {n: acc(n) for n in ("15488", "6322", "1381", "3381")}, "date": today()}, ensure_ascii=False, default=str))
frappe.destroy()
"""

"""Ca HTTP bản 0.11.2 trên site UAT dùng một lần, bắt buộc khôi phục CSDL sau khi chạy (cùng khung với bộ 0.11.1)."""
import json, os, secrets, subprocess, uuid, time
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order","Purchase Receipt","Stock Reconciliation","BOM","UOM","Landed Cost Voucher","Journal Entry","Cost Center","Account","APH Phieu quy nha may","APH Khoan muc chi nha may","APH Shared Sales Order"]
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
restore_path="/tmp/aphvh-http-0112-"+uuid.uuid4().hex+".sql.gz"
run(["docker","cp",str(backup),BACKEND+":"+restore_path])
# Verify destination before committing fixtures.
run(["docker","exec",BACKEND,"test","-s",restore_path])
restore_record=source.parent/"b0112_uat_restore.json"
restore_record.write_text(json.dumps({"site":SITE,"backup":str(backup),"backend_path":restore_path,"before":before},indent=2))
os.chmod(restore_record,0o600)
try:
    raw=inner(FIXTURE_CODE,json.dumps({"password":factory_password}))
    fixture=json.loads(next(x[13:] for x in raw.splitlines() if x.startswith("FIXTURE_JSON:")))
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import b0112_cases
    b0112_cases.chay(admin,lambda user:session(user,factory_password),fixture,emit)
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
    emit("HTTP_0112_RUNNER","FAIL",detail)
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
print("Bộ ca HTTP 0.11.2 chạy xong; người dùng thật và tải lớn nằm ngoài phạm vi bộ này.")
