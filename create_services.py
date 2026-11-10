#!/usr/bin/env python3
"""Create and deploy systemd service files for all country bots."""
import os

VPS_API_ROOT = "/opt/xrplme/thoughts/api"
VENV_PYTHON = "/home/xrpladmin/thailand_bot_venv/bin/python"

COUNTRIES = [
    {"slug": "brunei", "port": 8111, "display": "Brunei"},
    {"slug": "laos", "port": 8112, "display": "Laos"},
    {"slug": "myanmar", "port": 8113, "display": "Myanmar"},
    {"slug": "timor-leste", "port": 8114, "display": "Timor-Leste"},
    {"slug": "timor_leste", "module": "timor_leste", "port": 8114, "display": "Timor-Leste"},
    {"slug": "papua-new-guinea", "module": "papua_new_guinea", "port": 8115, "display": "Papua New Guinea"},
    {"slug": "papua_new_guinea", "module": "papua_new_guinea", "port": 8115, "display": "Papua New Guinea"},
    {"slug": "italy", "port": 8117, "display": "Italy"},
]

# Deduplicate by module name
seen = set()
services = []
for c in COUNTRIES:
    slug = c["slug"].replace('-', '_')
    if slug in seen:
        continue
    seen.add(slug)
    module = slug
    module_dash = slug.replace('_', '-')
    port = c["port"]
    display = c["display"]
    
    service = f"""[Unit]
Description={display} Bot x402 FastAPI
After=network.target

[Service]
Type=exec
User=xrpladmin
Group=xrplme
WorkingDirectory={VPS_API_ROOT}
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH={VPS_API_ROOT}"

ExecStart={VENV_PYTHON} -m uvicorn {module}_bot_server:app --host 127.0.0.1 --port {port}

NoNewPrivileges=true
PrivateTmp=true
ProtectHome=false
ProtectSystem=strict
ReadWritePaths={VPS_API_ROOT} {VENV_PYTHON}/../

Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
"""
    
    service_name = f"{module}-bot-api"
    service_path = os.path.expanduser(f"~/services/{service_name}.service")
    
    services.append({
        "name": service_name,
        "slug": module_dash,
        "module": module,
        "port": port,
        "display": display,
        "content": service,
        "path": service_path,
    })

# Write all service files locally
os.makedirs(os.path.expanduser("~/services"), exist_ok=True)
for svc in services:
    with open(svc["path"], "w") as f:
        f.write(svc["content"])
    print(f"Created: {svc['path']} ({svc['display']}, port {svc['port']})")

# Upload to VPS and restart
for svc in services:
    # Upload service file to VPS
    import subprocess
    subprocess.run(
        ["scp", svc["path"], f"xrplme-vps:/tmp/{svc['name']}.service"],
        capture_output=True, text=True, timeout=10
    )
    
    # Install and restart via SSH
    cmd = f"""sudo cp /tmp/{svc['name']}.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable {svc['name']}
    sudo systemctl restart {svc['name']}
    """
    
    result = subprocess.run(
        ["ssh", "xrplme-vps", cmd],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"  ✅ {svc['display']}: service installed and restarted")
    else:
        print(f"  ❌ {svc['display']}: {result.stderr.strip()[:100]}")

# Verify all are running
print("\n=== Verification ===")
for svc in services:
    result = subprocess.run(
        ["ssh", "xrplme-vps", f"systemctl is-active {svc['name']}"],
        capture_output=True, text=True, timeout=5
    )
    status = result.stdout.strip()
    print(f"  {svc['display']} ({svc['port']}): {status}")
