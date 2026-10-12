"""GitHub-hosted UAT only: starts disposable HTTP/backend containers."""
import json, os, subprocess, time
from pathlib import Path
import urllib.request, urllib.parse, http.cookiejar
assert os.environ.get('GITHUB_ACTIONS') == 'true', 'CI only; never run on production VM'
ROOT='/home/frappe/frappe-bench';SITE='aphvh-web-uat';WEB='aphvh-p0-web-uat'
source=Path(os.environ['UAT_SITE_ROOT'])/'sites'
assert source.parent.name.startswith('aphvh-http-uat-')
assert (source/SITE/'site_config.json').exists() and not (source/'frontend').exists()
mount=str(source)+':'+ROOT+'/sites'
subprocess.run(['docker','run','-d','--name','erp-aph-vh-backend-1','--network','aphvh-uat-net','-v',mount,'--entrypoint','bash','aphvh-uat:verification','-ec','exec sleep infinity'],check=True)
# Set inside the disposable container as the site owner (host runner UID differs).
subprocess.run(['docker','exec','-w',ROOT,'erp-aph-vh-backend-1','bench','--site',SITE,'set-config','developer_mode','1'],check=True)
subprocess.run(['docker','run','-d','--name',WEB,'--network','aphvh-uat-net','-v',mount,'-p','127.0.0.1:18091:8000','--workdir',ROOT+'/sites','--entrypoint',ROOT+'/env/bin/gunicorn','aphvh-uat:verification','--bind','0.0.0.0:8000','--workers','1','--threads','2','--timeout','120','kh_aph.uat_wsgi:application'],check=True)
state=source.parent/'state.json'
state.write_text(json.dumps({'site':SITE,'container':WEB,'port':18091,'sites_directory':str(source),'admin_password':'uat-fixture-only'}))
state.chmod(0o600)
pointer=Path.home()/'APHVH_HTTP_UAT_STATE_PATH.txt';pointer.write_text(str(state));pointer.chmod(0o600)
for attempt in range(60):
 try:
  op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
  req=urllib.request.Request('http://127.0.0.1:18091/api/method/login',data=urllib.parse.urlencode({'usr':'Administrator','pwd':'uat-fixture-only'}).encode(),headers={'Host':SITE})
  with op.open(req,timeout=5) as response:result=json.load(response)
  assert result.get('message')=='Logged In',result
  print(json.dumps({'case':'FRESH_HTTP_LOGIN','status':'PASS','site':SITE}));break
 except Exception:
  if attempt==59:raise
  time.sleep(1)

# Fail early on native Desk boot before the longer business suites.
try:
 with op.open(urllib.request.Request('http://127.0.0.1:18091/desk',headers={'Host':SITE}),timeout=60) as response:
  html=response.read().decode()
  assert response.status==200 and 'frappe' in html,'Native Desk HTML missing'
 print(json.dumps({'case':'NATIVE_DESK_BOOT','status':'PASS'}))
except Exception as exc:
 # Frappe website renderer embeds the exception in developer-mode HTML.
 # Strip markup and print only the traceback from this disposable Admin fixture.
 if isinstance(exc,urllib.error.HTTPError):
  import re,html
  page=html.unescape(exc.read().decode(errors='replace'))
  clean=re.sub(r'<[^>]+>',' ',page)
  index=clean.find('Traceback')
  if index>=0:print(clean[index:index+16000].replace('uat-fixture-only','[REDACTED]'),flush=True)
 result=subprocess.run(['docker','logs',WEB],text=True,capture_output=True)
 print((result.stdout+result.stderr)[-18000:].replace('uat-fixture-only','[REDACTED]'),flush=True)
 raise
