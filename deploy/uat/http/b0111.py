FIXTURE_CODE = 'import json,sys,uuid,frappe\nfrom frappe.utils import today,add_days\nfrom frappe.utils.password import update_password\nfrom kh_aph.constants import INV_FLAG, INV_NO, ROLE_FACTORY, ROLE_NO_COST\nfrappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")\nfrappe.connect();frappe.set_user("Administrator")\npayload=json.load(sys.stdin)\np="UAT-0111-"+uuid.uuid4().hex[:6]\nco=frappe.get_doc("Company",frappe.db.get_value("Company",{"abbr":"APH"},"name"))\ndef acc(n):return frappe.db.get_value("Account",{"company":co.name,"account_number":n,"is_group":0},"name")\nroot_cc=frappe.db.get_value("Cost Center",{"company":co.name,"is_group":1},"name")\ndef cc(ten,loai):return frappe.get_doc({"doctype":"Cost Center","cost_center_name":p+"-"+ten,"company":co.name,"parent_cost_center":root_cc,"kh_aph_loai_ttcp":loai}).insert().name\ncc_sc=cc("SC","Xưởng sản xuất");cc_chung=cc("CHUNG","Nhà máy chung")\nroot_wh=frappe.db.get_value("Warehouse",{"company":co.name,"is_group":1,"parent_warehouse":["is","not set"]},"name")\ndef wh(ten,bon=0):return frappe.get_doc({"doctype":"Warehouse","warehouse_name":p+"-"+ten,"company":co.name,"is_group":0,"parent_warehouse":root_wh,"account":co.default_inventory_account,"kh_aph_loai_kho":"Dở dang dây chuyền" if bon else None,"kh_aph_day_chuyen":"Đậu" if bon else None}).insert().name\nwh_nvl,wh_tp,wh_bon=wh("NVL"),wh("TP"),wh("BON",1)\ndef grp(ten,cha,**kw):return frappe.get_doc({"doctype":"Item Group","item_group_name":p+"-"+ten,"parent_item_group":cha,"is_group":0,**kw}).insert().name\ng_nl=grp("NL","NL - Nguyên liệu",kh_aph_gia_tam=1);g_tp=grp("TP","TP - Thành phẩm",kh_aph_khoa_gia_nha_may=1);g_hh=grp("HH","HH - Hàng hóa")\ncustomer=frappe.get_doc({"doctype":"Customer","customer_name":p,"customer_type":"Company","customer_group":frappe.db.get_value("Customer Group",{"is_group":0},"name"),"territory":frappe.db.get_value("Territory",{"is_group":0},"name"),INV_FLAG:INV_NO}).insert()\ntax=frappe.get_doc({"doctype":"Item Tax Template","title":p+"-10","company":co.name,"taxes":[{"tax_type":acc("33311"),"tax_rate":10}]}).insert()\nitems={}\nfor label,g,hs in (("raw",g_nl,1),("a",g_tp,1),("b",g_tp,0.7),("pp",g_hh,1),("trade",g_hh,1)):\n    items[label]=frappe.get_doc({"doctype":"Item","item_code":p+"-"+label,"item_name":p+"-"+label,"item_group":g,"stock_uom":"Kg","is_stock_item":1,"valuation_method":"Moving Average","kh_aph_he_so_gia_thanh":hs,\n        "taxes":[{"item_tax_template":tax.name,"tax_category":customer.tax_category}],\n        "item_defaults":[{"company":co.name,"default_warehouse":wh_tp,"income_account":co.default_income_account,"expense_account":co.default_expense_account,"buying_cost_center":co.cost_center,"selling_cost_center":co.cost_center}]}).insert().name\nsupplier=frappe.get_doc({"doctype":"Supplier","supplier_name":p,"supplier_type":"Company","supplier_group":frappe.db.get_value("Supplier Group",{"is_group":0},"name")}).insert().name\npl=frappe.db.get_value("Price List",{"selling":1,"enabled":1},"name")\nfrappe.get_doc({"doctype":"Item Price","item_code":items["a"],"price_list":pl,"price_list_rate":35000}).insert()\ndef user(ten,roles):\n    u=frappe.get_doc({"doctype":"User","email":(p+"-"+ten).lower()+"@example.invalid","first_name":p+" "+ten,"enabled":1,"user_type":"System User","send_welcome_email":0,"roles":[{"role":r} for r in roles]})\n    u.flags.no_welcome_mail=True;u.insert();update_password(u.name,payload["password"]);return u.name\ndung=user("dung",[ROLE_FACTORY,ROLE_NO_COST,"Sales User"]);dung2=user("dung2",[ROLE_FACTORY,ROLE_NO_COST])\nktt=user("ktt",["Accounts Manager","Accounts User","Sales User","Stock Manager","Stock User"]);ban=user("ban",["Nhân viên bán hàng","Sales User"])\nquy=frappe.get_doc({"doctype":"Account","account_name":p+"-QUY-NHA-MAY","company":co.name,"parent_account":frappe.db.get_value("Account",{"company":co.name,"account_number":"111"},"name"),"account_type":"Cash","root_type":"Asset","is_group":0}).insert().name\nfrappe.db.set_value("Company",co.name,"kh_aph_quy_nha_may",quy)\nkm=frappe.get_doc({"doctype":"APH Khoan muc chi nha may","khoan_muc":p+"-BOC-XEP","company":co.name,"account":acc("15488"),"cost_center":cc_sc}).insert().name\ndef sr(item,whs,qty,rate,gia_tam):\n    d=frappe.get_doc({"doctype":"Stock Reconciliation","company":co.name,"purpose":"Opening Stock","kh_aph_gia_tam":gia_tam,"expense_account":acc("9990"),"items":[{"item_code":item,"warehouse":whs,"qty":qty,"valuation_rate":rate}]})\n    d.insert();d.submit();return d.name\nsr_tam=sr(items["raw"],wh_nvl,10000,20000,1);sr(items["a"],wh_tp,1000,25000,0)\nso=frappe.get_doc({"doctype":"Sales Order","company":co.name,"customer":customer.name,"transaction_date":today(),"delivery_date":add_days(today(),1),"selling_price_list":pl,"currency":"VND","conversion_rate":1,"order_type":"Sales",INV_FLAG:INV_NO,\n    "items":[{"item_code":items["a"],"qty":100,"uom":"Kg","conversion_factor":1,"rate":35000,"warehouse":wh_tp,"item_tax_template":tax.name,"delivery_date":add_days(today(),1)}]}).insert()\nso.submit()\nfrom erpnext.selling.doctype.sales_order.sales_order import make_delivery_note\ndn=make_delivery_note(so.name);dn.posting_date=today();dn.set(INV_FLAG,INV_NO);dn.insert()\ncustomer2=frappe.get_doc({"doctype":"Customer","customer_name":p+"-2","customer_type":"Company","customer_group":frappe.db.get_value("Customer Group",{"is_group":0},"name"),"territory":frappe.db.get_value("Territory",{"is_group":0},"name"),INV_FLAG:INV_NO}).insert()\nfrappe.db.commit()\nprint("FIXTURE_JSON:"+json.dumps({"p":p,"company":co.name,"cc_sc":cc_sc,"cc_chung":cc_chung,"wh_nvl":wh_nvl,"wh_tp":wh_tp,"wh_bon":wh_bon,"items":items,"supplier":supplier,"customer":customer.name,"customer2":customer2.name,"pl":pl,\n    "dung":dung,"dung2":dung2,"ktt":ktt,"ban":ban,"quy":quy,"km":km,"sr_tam":sr_tam,"dn":dn.name,"tax":tax.name,"acc":{n:acc(n) for n in ("15484","6323","15488","3311","1111")},"date":today(),"month":today()[:7]}))\nfrappe.destroy()\n'
"""Ca HTTP bản 0.11.1 trên site UAT dùng một lần, bắt buộc khôi phục CSDL sau khi chạy (khung giống cost.py)."""
import json, os, secrets, subprocess, uuid, time
import http.cookiejar, urllib.request, urllib.parse, urllib.error
from pathlib import Path
WEB="aphvh-p0-web-uat"
BACKEND="erp-aph-vh-backend-1"
DB="erp-aph-vh-db-1"
SITE="aphvh-web-uat"
ROOT="/home/frappe/frappe-bench"
TRACKED=["User","Customer","Item","Item Group","Item Tax Template","Warehouse","Bin","Sales Order","Delivery Note","Sales Invoice","Stock Entry","GL Entry","Stock Ledger Entry","Property Setter","Custom DocPerm","Payment Ledger Entry","Role","Print Format","Supplier","Purchase Order","Purchase Receipt","Stock Reconciliation","Landed Cost Voucher","Journal Entry","Cost Center","Account","APH Phieu quy nha may","APH Khoan muc chi nha may","APH Shared Sales Order"]
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
restore_path="/tmp/aphvh-http-0111-"+uuid.uuid4().hex+".sql.gz"
run(["docker","cp",str(backup),BACKEND+":"+restore_path])
# Verify destination before committing fixtures.
run(["docker","exec",BACKEND,"test","-s",restore_path])
restore_record=source.parent/"b0111_uat_restore.json"
restore_record.write_text(json.dumps({"site":SITE,"backup":str(backup),"backend_path":restore_path,"before":before},indent=2))
os.chmod(restore_record,0o600)
try:
    raw=inner(FIXTURE_CODE,json.dumps({"password":factory_password}))
    fixture=json.loads(next(x[13:] for x in raw.splitlines() if x.startswith("FIXTURE_JSON:")))
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import b0111_cases
    b0111_cases.chay(admin,lambda user:session(user,factory_password),fixture,emit)
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
    emit("HTTP_0111_RUNNER","FAIL",detail)
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
print("Bộ ca HTTP 0.11.1 chạy xong; người dùng thật và tải lớn nằm ngoài phạm vi bộ này.")
