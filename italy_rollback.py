#!/usr/bin/env python3
"""ROLLBACK: Start Italy as manual process (same as the canary approach)."""
import subprocess
import os
import time
import json

print("ITALY ROLLBACK — starting manual uvicorn process")
print("=" * 60)

# Start the process directly
result = subprocess.Popen(
    ["/home/xrpladmin/thailand_bot_venv/bin/python", "-m", "uvicorn",
     "italy_bot_server:app", "--host", "127.0.0.1", "--port", "8117"],
    cwd="/opt/xrplme/thoughts/api",
    env={**os.environ, "PYTHONPATH": "/opt/xrplme/thoughts/api"},
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True  # detach
)

print(f"  Starting PID: {result.pid}")
print(f"  Waiting for service to come up...")
time.sleep(5)

# Verify health
r = subprocess.run(["curl", "-s", "http://127.0.0.1:8117/health"],
                   capture_output=True, text=True)
print(f"  Health: {r.stdout[:100]}")

# Verify 402
r = subprocess.run(["curl", "-s", "-X", "POST", "http://127.0.0.1:8117/api/v1/italy/bot",
                   "-H", "Content-Type: application/json",
                   "-d", json.dumps({"message": "rollback check"})],
                   capture_output=True, text=True)
try:
    d = json.loads(r.stdout)
    a = d.get('accepts', [{}])[0]
    extra = a.get('extra', {})
    print(f"  402: x402Version={d.get('x402Version')}, amount={a.get('amount')}, invoiceId={extra.get('invoiceId', 'MISSING')[:16]}...")
except:
    print(f"  402 raw: {r.stdout[:100]}")

# Verify port ownership
r = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
for line in r.stdout.split('\n'):
    if ':8117' in line:
        print(f"  Port 8117: {line.strip()[:80]}")

print(f"\n  ⚠️ NOTE: This process is manually launched (not systemd).")
print(f"  To restore systemd management, run: sudo systemctl start italy-bot-api.service")
print(f"  (requires password — Italy is NOT in NOPASSWD sudoers)")
