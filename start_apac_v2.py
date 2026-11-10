#!/usr/bin/env nohup python3
"""Start all 5 APAC country bot servers as background processes."""
import os
import subprocess
import time
import json

os.chdir("/opt/xrplme/thoughts/api")
VENV = "/home/xrpladmin/thailand_bot_venv/bin/python"

COUNTRIES = [
    ("brunei", 8111, "Brunei"),
    ("laos", 8112, "Laos"),
    ("myanmar", 8113, "Myanmar"),
    ("timor_leste", 8114, "Timor-Leste"),
    ("papua_new_guinea", 8115, "Papua New Guinea"),
]

for module, port, display in COUNTRIES:
    log_file = f"/tmp/{module}.log"
    cmd = f"nohup {VENV} -m uvicorn {module}_bot_server:app --host 127.0.0.1 --port {port} > {log_file} 2>&1 &"
    subprocess.run(cmd, shell=True)
    time.sleep(2)
    print(f"Started: {display} (port {port}), PID check via log")

time.sleep(3)

# Verify all
import requests
for module, port, display in COUNTRIES:
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        d = r.json()
        print(f"  {display}: port={port}, records={d.get('data_records',0)}, HTTP {r.status_code}")
    except Exception as e:
        print(f"  {display}: port={port}, ERROR: {e}")
