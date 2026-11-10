#!/usr/bin/env python3
"""Create systemd service files for 5 new APAC countries."""
import os

VENV_PYTHON = "/home/xrpladmin/thailand_bot_venv/bin/python"
API_ROOT = "/opt/xrplme/thoughts/api"

COUNTRIES = [
    {"service": "brunei-bot-api",  "module": "brunei",           "display": "Brunei",          "port": 8111},
    {"service": "laos-bot-api",    "module": "laos",             "display": "Laos",            "port": 8112},
    {"service": "myanmar-bot-api", "module": "myanmar",          "display": "Myanmar",         "port": 8113},
    {"service": "tl-bot-api",      "module": "timor_leste",      "display": "Timor-Leste",     "port": 8114},
    {"service": "pg-bot-api",      "module": "papua_new_guinea",  "display": "Papua New Guinea", "port": 8115},
]

template = """[Unit]
Description={display} Bot x402 FastAPI
After=network.target

[Service]
Type=exec
User=xrpladmin
Group=xrplme
WorkingDirectory={api_root}
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH={api_root}"

ExecStart={venv_python} -m uvicorn {module}_bot_server:app --host 127.0.0.1 --port {port}

NoNewPrivileges=true
PrivateTmp=true
ProtectHome=false
ProtectSystem=strict
ReadWritePaths={api_root} /home/xrpladmin/thailand_bot_venv

Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
"""

out_dir = os.path.expanduser("~/xrplme-example/services")
os.makedirs(out_dir, exist_ok=True)

for c in COUNTRIES:
    content = template.format(
        display=c["display"],
        api_root=API_ROOT,
        venv_python=VENV_PYTHON,
        module=c["module"],
        port=c["port"],
    )
    path = os.path.join(out_dir, f"{c['service']}.service")
    with open(path, "w") as f:
        f.write(content)
    print(f"Created: {path}")

print(f"\nAll 5 service files in {out_dir}")
