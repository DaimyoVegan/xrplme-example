#!/usr/bin/env python3
"""Create systemd service files for 6 missing countries and start them."""
import os
import subprocess

VPS_API_ROOT = "/opt/xrplme/thoughts/api"
VENV_PYTHON = "/home/xrpladmin/thailand_bot_venv/bin/python"

COUNTRIES = [
    {"slug": "bn", "country": "brunei", "module": "brunei_bot_server", "port": 8111, "display": "Brunei"},
    {"slug": "la", "country": "laos", "module": "laos_bot_server", "port": 8112, "display": "Laos"},
    {"slug": "mm", "country": "myanmar", "module": "myanmar_bot_server", "port": 8113, "display": "Myanmar"},
    {"slug": "tl", "country": "timor-leste", "module": "timor_leste_bot_server", "port": 8114, "display": "Timor-Leste"},
    {"slug": "pg", "country": "papua-new-guinea", "module": "papua_new_guinea_bot_server", "port": 8115, "display": "Papua New Guinea"},
    {"slug": "it", "country": "italy", "module": "italy_bot_server", "port": 8117, "display": "Italy"},
]

def ssh_run(cmd, timeout=15):
    result = subprocess.run(["ssh", "xrplme-vps", cmd], capture_output=True, text=True, timeout=timeout)
    return result.stdout, result.stderr, result.returncode

def create_service_file(svc):
    service = f"""[Unit]
Description={svc['display']} Bot x402 FastAPI
After=network.target

[Service]
Type=exec
User=xrpladmin
Group=xrplme
WorkingDirectory={VPS_API_ROOT}
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH={VPS_API_ROOT}"

ExecStart={VENV_PYTHON} -m uvicorn {svc['module']}:app --host 127.0.0.1 --port {svc['port']}


Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
"""
    
    # Write to local temp file
    local_path = os.path.expanduser(f"~/{svc['slug']}_bot-api.service")
    with open(local_path, "w") as f:
        f.write(service)
    
    # SCP to VPS /etc/systemd/system/ (writable by xrpladmin)
    vps_path = f"/etc/systemd/system/{svc['slug']}-bot-api.service"
    result = subprocess.run(
        ["scp", local_path, f"xrplme-vps:{vps_path}"],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode == 0:
        print(f"  ✅ {svc['display']}: service file installed at {vps_path}")
        os.unlink(local_path)
        return True
    else:
        print(f"  ❌ {svc['display']}: scp failed: {result.stderr.strip()[:100]}")
        os.unlink(local_path)
        return False

def restart_service(svc):
    # We can't use daemon-reload (needs sudo), but we can restart
    # The service file was already there from a template or we use direct restart
    # Check if service exists
    out, err, rc = ssh_run(f"systemctl is-enabled {svc['slug']}-bot-api 2>&1", timeout=5)
    print(f"  Service {svc['slug']}-bot-api: enabled={out.strip()}")
    
    # Try to restart - this works for existing services via NOPASSWD sudoers
    # But for new services, we need daemon-reload first
    # Since we can't daemon-reload, let's try direct restart
    out, err, rc = ssh_run(f"systemctl restart {svc['slug']}-bot-api 2>&1", timeout=10)
    if rc != 0:
        # Try with sudo
        out, err, rc = ssh_run(f"sudo systemctl restart {svc['slug']}-bot-api 2>&1", timeout=10)
        if rc != 0:
            print(f"  ❌ {svc['display']}: restart failed: {err.strip()[:200] or out.strip()[:200]}")
            return False
    print(f"  ✅ {svc['display']}: restarted")
    return True

print("Creating systemd service files for 6 countries...")
print()

for svc in COUNTRIES:
    print(f"[{svc['display']}] (port {svc['port']})")
    
    # Create service file
    if not create_service_file(svc):
        continue
    
    # Try to restart
    if restart_service(svc):
        # Wait for startup
        import time
        time.sleep(3)
        
        # Verify health
        out, err, rc = ssh_run(f"curl -s http://127.0.0.1:{svc['port']}/health 2>&1", timeout=5)
        try:
            import json
            d = json.loads(out)
            records = d.get("data_records", d.get("record_count", 0))
            print(f"  Health: ✅ records={records}, country={d.get('country')}")
        except:
            print(f"  Health: ❌ failed - {out[:100]}")
    
    print()

# Final verification
print("\n=== Final Status ===")
all_ok = True
for svc in COUNTRIES:
    out, _, _ = ssh_run(f"systemctl is-active {svc['slug']}-bot-api 2>&1", timeout=5)
    status = out.strip()
    out2, _, _ = ssh_run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{svc['port']}/health", timeout=5)
    http_code = out2.strip()
    ok = "✅" if status == "active" and http_code == "200" else "❌"
    if ok == "❌":
        all_ok = False
    print(f"  {ok} {svc['display']}: systemctl={status}, health={http_code}")

# Also restart Japan
print("\n=== Fixing Japan ===")
out, err, rc = ssh_run("sudo systemctl restart japan-bot-api 2>&1", timeout=10)
if rc == 0:
    import time
    time.sleep(3)
    out2, _, _ = ssh_run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8087/health", timeout=5)
    print(f"  Japan: systemctl=active, health={out2.strip()}")
else:
    print(f"  Japan restart failed: {err.strip()[:100]}")
