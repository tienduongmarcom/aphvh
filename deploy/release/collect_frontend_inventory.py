"""Read-only VM preflight; run from a checked-out release directory.

No shell interpolation, no environment/config secrets and no database writes.
Does not create backups or change running containers.
"""
import json
import subprocess
from pathlib import Path

BACKEND = "erp-aph-vh-backend-1"
FRONTEND = "erp-aph-vh-frontend-1"
ROOT = "/home/frappe/frappe-bench"

def run(args, data=None):
    result = subprocess.run(args, input=data, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("Read-only preflight failed: " + result.stderr[-1500:])
    return result.stdout

containers = json.loads(run(["docker", "inspect", BACKEND, FRONTEND]))
metadata = []
for container in containers:
    labels = container["Config"].get("Labels") or {}
    metadata.append({"name": container["Name"].lstrip("/"), "image": container["Image"],
        "image_reference": container["Config"]["Image"],
        "state": container["State"]["Status"],
        "ports": container["HostConfig"].get("PortBindings"),
        "compose": {k: v for k, v in labels.items() if k.startswith("com.docker.compose.")
            and k in ("com.docker.compose.project", "com.docker.compose.service",
                "com.docker.compose.project.working_dir", "com.docker.compose.project.config_files")},
        "mounts": [{k: m.get(k) for k in ("Type", "Name", "Source", "Destination", "RW")}
            for m in container["Mounts"]]})
code = Path(__file__).with_name("frontend_preflight.py").read_text()
output = run(["docker", "exec", "-i", "-w", ROOT + "/sites", BACKEND,
    ROOT + "/env/bin/python", "-"], code)
site = json.loads(output.strip())
assert site["site"] == "frontend" and site["read_only"] is True
print(json.dumps({"containers": metadata, "site": site,
    "deployment": "NOT_EXECUTED", "business_acceptance": "NOT_TESTED"},
    ensure_ascii=False, default=str))
