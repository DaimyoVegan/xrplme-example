#!/usr/bin/env python3
"""
Create systemd service files for 6 APAC+Italy countries and start them.
Also kills nohup processes to avoid port conflicts.
"""
import os
import subprocess
import time

def ssh_run(cmd, timeout=30):
    r = subprocess.run(["ssh", "xrplme-vps", cmd], capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr, r.returncode

def ssh_scp(local_path, remote_path):
    result = subprocess.run(["scp", local_path, f"xrplme-vps:{remote_path}"],
                          capture_output=True, text=True, timeout=10)
    return result.returncode == 0

VPS_API_ROOT = "/opt/xrplme/thoughts/api"
VENV_PYTHON = "/home/xrpladmin/thailand_bot_venv/bin/python"

# Countries that need systemd service files
# (slug, module_name, port, display, service_short_code)
COUNTRIES = [
    {"slug": "bn", "module": "brunei_bot_server", "port": 8111, "display": "Brunei"},
    {"slug": "la", "module": "laos_bot_server", "port": 8112, "display": "Laos"},
    {"slug": "mm", "module": "myanmar_bot_server", "port": 8113, "display": "Myanmar"},
    {"slug": "tl", "module": "timor_leste_bot_server", "port": 8114, "display": "Timor-Leste"},
    {"slug": "pg", "module": "papua_new_guinea_bot_server", "port": 8115, "display": "Papua New Guinea"},
    {"slug": "it", "module": "italy_bot_server", "port": 8117, "display": "Italy"},
]

def generate_service_file(country):
    """Generate systemd service file. No ProtectSystem to avoid NAMESPACE errors."""
    return f"""[Unit]
Description={country['display']} Bot x402 FastAPI
After=network.target

[Service]
Type=exec
User=xrpladmin
Group=xrplme
WorkingDirectory={VPS_API_ROOT}
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH={VPS_API_ROOT}"

ExecStart={VENV_PYTHON} -m uvicorn {country['module']}:app --host 127.0.0.1 --port {country['port']}

NoNewPrivileges=true
PrivateTmp=true
ProtectHome=false
Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
"""

print("=" * 70)
print("CREATING SYSTEMD SERVICES FOR 6 COUNTRIES")
print("=" * 70)

# 1. Create service files locally
services_dir = os.path.expanduser("~/services")
os.makedirs(services_dir, exist_ok=True)

for c in COUNTRIES:
    svc_name = f"{c['slug']}-bot-api"
    content = generate_service_file(c)
    local_path = os.path.join(services_dir, f"{svc_name}.service")
    with open(local_path, "w") as f:
        f.write(content)
    print(f"  Created {svc_name}.service")

# 2. Upload service files to VPS /etc/systemd/system/ (writable by xrpladmin)
for c in COUNTRIES:
    svc_name = f"{c['slug']}-bot-api"
    local_path = os.path.join(services_dir, f"{svc_name}.service")
    vps_path = f"/etc/systemd/system/{svc_name}.service"
    
    if ssh_scp(local_path, vps_path):
        print(f"  ✅ Uploaded {svc_name}.service to VPS")
    else:
        print(f"  ❌ Failed to upload {svc_name}.service")

# 3. Kill nohup processes to free ports
print("\n--- Stopping nohup processes ---")
for c in COUNTRIES:
    port = c['port']
    out, _, rc = ssh_run(f"lsof -ti :{port} 2>/dev/null | head -1", timeout=5)
    pid = out.strip()
    if pid:
        result = ssh_run(f"kill {pid} 2>&1", timeout=5)
        print(f"  {c['display']}: killed PID {pid}")
    else:
        print(f"  {c['display']}: no process on port {port}")

time.sleep(2)

# 4. Run daemon-reload + enable + start
print("\n--- Starting systemd services ---")
print("  NOTE: daemon-reload requires password (not in NOPASSWD)")
print()

# Try systemctl daemon-reload
out, err, rc = ssh_run("sudo systemctl daemon-reload 2>&1", timeout=10)
print(f"  daemon-reload: {out.strip() or err.strip()}")

# Try enabling and starting each service
for c in COUNTRIES:
    svc_name = f"{c['slug']}-bot-api"
    
    # Try to enable
    out, err, rc = ssh_run(f"sudo systemctl enable {svc_name} 2>&1", timeout=10)
    
    # Try to start
    out2, err2, rc2 = ssh_run(f"sudo systemctl start {svc_name} 2>&1", timeout=10)
    
    status = "✅" if rc2 == 0 else "❌"
    print(f"  {status} {c['display']} ({svc_name}): start rc={rc2}")
    if rc2 != 0:
        print(f"      stderr: {err2.strip()[:100]}")

time.sleep(3)

# 5. Verify
print("\n--- Verification ---")
for c in COUNTRIES:
    svc_name = f"{c['slug']}-bot-api"
    out, _, _ = ssh_run(f"systemctl is-active {svc_name} 2>&1", timeout=5)
    svc_status = out.strip()
    
    out2, _, _ = ssh_run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{c['port']}/health", timeout=5)
    health_status = out2.strip()
    
    ok = "✅" if svc_status == "active" and health_status == "200" else "❌"
    print(f"  {ok} {c['display']}: systemctl={svc_status}, health={health_status}")

# 6. Check if services are enabled
print("\n--- Service file ownership ---")
out, _, _ = ssh_run(f"ls -la /etc/systemd/system/{{bn,la,mm,tl,pg,it}}-bot-api.service", timeout=5)
print(f"  {out.strip()}")
