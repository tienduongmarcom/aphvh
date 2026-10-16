"""Host-side isolated HTTP setup. No frontend source/container modification."""
import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BACKEND = "erp-aph-vh-backend-1"
DB = "erp-aph-vh-db-1"
SITE = "aphvh-web-uat"
WEB = "aphvh-p0-web-uat"
IMAGE = "aphvh-p0-web-candidate:20261010"
PORT = 18091
ROOT = "/home/frappe/frappe-bench"
root_secret = ""
admin_secret = secrets.token_urlsafe(32)


def run(args, input=None):
    proc = subprocess.run(args, input=input, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output = proc.stdout
    for secret in (root_secret, admin_secret):
        if secret:
            output = output.replace(secret, "[REDACTED]")
    print(output[-12000:], flush=True)
    if proc.returncode:
        raise RuntimeError("Previous step failed; stop without force/retry")
    return proc.stdout


def inspect(name):
    return json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]


try:
    backend = inspect(BACKEND)
    existing = subprocess.check_output(["docker", "ps", "-a", "--format", "{{.Names}}"], text=True).splitlines()
    if WEB in existing:
        sys.exit("STOP: candidate container already exists; do not overwrite")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", PORT))
    env = dict(v.split("=", 1) for v in inspect(DB)["Config"].get("Env", []) if "=" in v)
    root_secret = env.get("MARIADB_ROOT_PASSWORD") or env.get("MYSQL_ROOT_PASSWORD") or ""
    if not root_secret:
        secret_file = env.get("MARIADB_ROOT_PASSWORD_FILE") or env.get("MYSQL_ROOT_PASSWORD_FILE")
        if secret_file:
            root_secret = subprocess.check_output(["docker", "exec", DB, "cat", secret_file], text=True).rstrip("\n")
    if not root_secret:
        sys.exit("STOP: DB root credential unavailable")
    work = Path(tempfile.mkdtemp(prefix="aphvh-http-uat-"))
    os.chmod(work, 0o700)
    build = work / "build"
    app = build / "kh_aph"
    app.mkdir(parents=True)
    for module, source in HTTP_PATCH_SOURCES.items():
        (app / (module.rsplit(".", 1)[1] + ".py")).write_text(source)
    (app / "hooks.py").write_text(HTTP_HOOKS)
    (app / "uat_wsgi.py").write_text(
        'from frappe import app\napp._site = "aphvh-web-uat"\napplication = app.application\n')
    (build / "Dockerfile").write_text(
        "FROM " + backend["Config"]["Image"] + "\nUSER root\n"
        "COPY --chown=frappe:frappe kh_aph/ /home/frappe/frappe-bench/apps/kh_aph/kh_aph/\n"
        "USER frappe\nWORKDIR /home/frappe/frappe-bench/sites\n")
    print("=== BUILD ISOLATED CANDIDATE IMAGE ===", flush=True)
    run(["docker", "build", "--pull=false", "--network=none", "-t", IMAGE, str(build)])

    create = r'''
import json, secrets, subprocess, sys
from pathlib import Path
data=json.load(sys.stdin)
bench=Path("/home/frappe/frappe-bench"); sites=bench/"sites"; site="aphvh-web-uat"
if (sites/site).exists(): sys.exit("STOP: web UAT site already exists; not overwriting")
source=json.loads((sites/"frontend/site_config.json").read_text())
common=json.loads((sites/"common_site_config.json").read_text())
prefix=sites/"frontend/private/backups/20261010_195444-frontend"
files=[Path(str(prefix)+x) for x in ("-database.sql.gz","-files.tar","-private-files.tar")]
if not all(p.is_file() for p in files):sys.exit("STOP: original blank backup missing")
host=source.get("db_host") or common.get("db_host")
if not host:sys.exit("STOP: missing database host")
def run(args):
 p=subprocess.run(["bench"]+args,cwd=bench,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 out=p.stdout
 for secret in data.values():out=out.replace(secret,"[REDACTED]")
 print(out,flush=True)
 if p.returncode:sys.exit("STOP: setup step failed")
run(["new-site",site,"--db-host",str(host),"--db-port",str(source.get("db_port") or common.get("db_port") or 3306),
     "--db-root-password",data["root"],"--admin-password",data["admin"],"--mariadb-user-host-login-scope","%"])
config=sites/site/"site_config.json"; value=json.loads(config.read_text())
value.update(pause_scheduler=True,mute_emails=True,kh_aph_server_cost_guard=1,kh_aph_post_receivable_on_delivery=1)
if source.get("encryption_key"):value["encryption_key"]=source["encryption_key"]
config.write_text(json.dumps(value,indent=2))
run(["--site",site,"restore",str(files[0]),"--db-root-password",data["root"],"--admin-password",data["admin"],
     "--with-public-files",str(files[1]),"--with-private-files",str(files[2])])
run(["--site",site,"disable-scheduler"])
'''
    print("=== CREATE SEPARATE WEB UAT SITE ===", flush=True)
    run(["docker", "exec", "-i", "-w", ROOT, BACKEND, ROOT+"/env/bin/python", "-c", create],
        input=json.dumps({"root": root_secret, "admin": admin_secret}))

    sites = work / "sites"
    sites.mkdir()
    run(["docker", "cp", BACKEND+":"+ROOT+"/sites/"+SITE, str(sites/SITE)])
    # Only the UAT site is copied. Never mount the shared sites volume or frontend here.
    common_raw = subprocess.check_output(["docker", "exec", BACKEND, "cat", ROOT+"/sites/common_site_config.json"], text=True)
    common = json.loads(common_raw)
    selected = {k: common[k] for k in ("db_host", "db_port", "redis_cache", "redis_queue", "redis_socketio", "socketio_port") if k in common}
    (sites/"common_site_config.json").write_text(json.dumps(selected))
    (sites/"apps.txt").write_text("frappe\nerpnext\nlab9x\nkh_aph\n")
    run(["docker", "run", "--rm", "--user", "root", "--entrypoint", "chown",
         "--mount", "type=bind,src="+str(sites)+",dst="+ROOT+"/sites", IMAGE,
         "-R", "frappe:frappe", ROOT+"/sites"])
    networks = list(backend["NetworkSettings"]["Networks"])
    if len(networks) != 1:
        raise RuntimeError("STOP: multiple backend networks; no automatic choice")
    print("=== START LOOPBACK-ONLY WEB CANDIDATE ===", flush=True)
    run(["docker", "run", "-d", "--name", WEB, "--network", networks[0],
         "--publish", f"127.0.0.1:{PORT}:8000", "--mount", "type=bind,src="+str(sites)+",dst="+ROOT+"/sites",
         "--workdir", ROOT+"/sites", "--entrypoint", ROOT+"/env/bin/gunicorn", IMAGE,
         "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "120", "kh_aph.uat_wsgi:application"])
    setup = r'''
import json,frappe
frappe.init(site="aphvh-web-uat",sites_path="/home/frappe/frappe-bench/sites")
try:
 frappe.connect();frappe.set_user("Administrator")
 from kh_aph.server_cost_guard import apply_query_field_permissions
 print("Cost field setup:",len(apply_query_field_permissions()))
 from frappe.model.base_document import get_controller
 for dt in ("Stock Entry","Item","Sales Order","Delivery Note"):
  names=[c.__module__+"."+c.__name__ for c in get_controller(dt).__mro__]
  assert any("server_cost_guard.CostReadGuard" in name for name in names),dt+" missing actual hook"
  print("MRO",dt,json.dumps(names))
 for dt in ("Customer","Item","Sales Order","Delivery Note","Sales Invoice","GL Entry","Stock Ledger Entry"):
  count=frappe.db.count(dt);assert count==0,dt+" not blank";print(dt,count)
 frappe.db.commit()
finally:frappe.destroy()
'''
    run(["docker", "exec", "-i", "-w", ROOT+"/sites", WEB, ROOT+"/env/bin/python", "-c", setup])

    cookie = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
    base = f"http://127.0.0.1:{PORT}"
    headers = {"Host": SITE, "X-Frappe-Site-Name": SITE}
    for attempt in range(15):
        try:
            request = urllib.request.Request(base+"/api/method/ping", headers=headers)
            with opener.open(request, timeout=5) as response:
                ping = json.load(response)
            if ping.get("message") != "pong":
                raise RuntimeError("Unexpected ping response")
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 14:
                raise
            time.sleep(1)
    login = urllib.request.Request(base+"/api/method/login", headers=headers,
        data=urllib.parse.urlencode({"usr": "Administrator", "pwd": admin_secret}).encode())
    with opener.open(login, timeout=15) as response:
        json.load(response)
    with opener.open(urllib.request.Request(base+"/api/method/frappe.auth.get_logged_user", headers=headers), timeout=10) as response:
        user = json.load(response).get("message")
    if user != "Administrator":
        raise RuntimeError("HTTP login did not verify Administrator")
    state = work / "state.json"
    state.write_text(json.dumps({"site": SITE,"container": WEB,"image": IMAGE,"port": PORT,
                                 "admin_password": admin_secret,"sites_directory": str(sites)}, indent=2))
    os.chmod(state, 0o600)
    pointer = Path.home()/"APHVH_HTTP_UAT_STATE_PATH.txt"
    pointer.write_text(str(state)+"\n")
    os.chmod(pointer, 0o600)
    print(json.dumps({"case":"HTTP_CANDIDATE_READY","status":"PASS","site":SITE,
                      "container":WEB,"binding":f"127.0.0.1:{PORT}","logged_user":user,
                      "shared_app_files_changed":False,"frontend_mounted":False}, ensure_ascii=False))
    print("State saved privately on VM; do not paste state.json into chat. New business HTTP tests not yet run.")
except Exception as exc:
    message=str(exc)
    for secret in (root_secret,admin_secret):
        if secret:message=message.replace(secret,"[REDACTED]")
    print(json.dumps({"case":"HTTP_SETUP","status":"BLOCKED","type":type(exc).__name__,"error":message},ensure_ascii=False))
    sys.exit(1)
