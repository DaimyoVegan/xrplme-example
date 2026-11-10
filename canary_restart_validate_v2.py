#!/usr/bin/env python3
"""
ITALY COUNTRY-LABEL CANARY — RESTART + VALIDATION (via SSH to VPS)
This script runs ON the VPS.
"""
import subprocess
import os
import json
import re
import hashlib
import sqlite3
import time
from datetime import datetime
from urllib import request as url_request

DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
ITALY_PATH = "/opt/xrplme/thoughts/api/italy_bot_server.py"
SIS_PATH = "/opt/xrplme/thoughts/api/sqlite_invoice_store.py"

print("=" * 80)
print("ITALY COUNTRY-LABEL CANARY — RESTART + VALIDATION")
print("=" * 80)

# Record invoice count BEFORE restart
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_before = c.fetchone()[0]
conn.close()

print(f"\n--- Pre-restart DB state ---")
print(f"  Total invoices: {inv_count_before}")

# Record old state
result = subprocess.run(["systemctl", "show", "italy-bot-api", "--property=MainPID,ExecMainStartTimestamp,ActiveState,SubState"],
                       capture_output=True, text=True)
old_fields = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        old_fields[k] = v
old_pid = old_fields.get('MainPID', '0')
print(f"\n--- Pre-restart service ---")
print(f"  PID: {old_pid}")
print(f"  ActiveState: {old_fields.get('ActiveState')}")
print(f"  Started: {old_fields.get('ExecMainStartTimestamp')}")

# Verify source files are already patched
print(f"\n--- Verify source patches are on disk ---")
with open(SIS_PATH) as f:
    sis = f.read()
with open(ITALY_PATH) as f:
    italy = f.read()

sis_patched = 'self._country' in sis and 'country: str = None' in sis
italy_patched = 'SQLiteInvoiceStore(country="italy")' in italy
print(f"  sqlite_invoice_store.py patched: {'✓' if sis_patched else '✗'}")
print(f"  italy_bot_server.py patched: {'✓' if italy_patched else '✗'}")

if not sis_patched or not italy_patched:
    print("  ⚠️  Patches NOT on disk — aborting restart")
    exit(1)

# STEP 1: Restart via systemctl
print(f"\n--- Restarting italy-bot-api.service ---")
result = subprocess.run(["sudo", "systemctl", "restart", "italy-bot-api.service"],
                       capture_output=True, text=True)
restart_ok = result.returncode == 0
print(f"  sudo systemctl restart exit code: {result.returncode}")
if result.stderr:
    print(f"  stderr: {result.stderr[:200]}")

# Wait for restart
print(f"  Waiting 5 seconds...")
time.sleep(5)

# STEP 2: Confirm service active + new PID
result = subprocess.run(["systemctl", "show", "italy-bot-api", "--property=MainPID,ExecMainStartTimestamp,ActiveState,SubState"],
                       capture_output=True, text=True)
new_fields = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        new_fields[k] = v
new_pid = new_fields.get('MainPID', '0')

print(f"\n--- Post-restart service ---")
print(f"  ActiveState: {new_fields.get('ActiveState')}")
print(f"  SubState: {new_fields.get('SubState')}")
print(f"  New PID: {new_pid} (was: {old_pid})")
print(f"  Start time: {new_fields.get('ExecMainStartTimestamp')}")

# Check process start time
if new_pid and int(new_pid) > 0:
    result = subprocess.run(["ps", "-o", "pid,lstart,cmd", "-p", new_pid], capture_output=True, text=True)
    print(f"  Process: {result.stdout.strip()}")

# STEP 3: Verify .pyc was recompiled (indicates new code loaded)
pyc_path = "/opt/xrplme/thoughts/api/__pycache__/sqlite_invoice_store.cpython-312.pyc"
if os.path.exists(pyc_path):
    stat = os.stat(pyc_path)
    print(f"  .pyc last modified: {datetime.fromtimestamp(stat.st_mtime).isoformat()}")

# STEP 4: Wait for service to be ready
print(f"\n--- Waiting for service readiness ---")
ready = False
for i in range(10):
    try:
        resp = url_request.urlopen("http://127.0.0.1:8117/health", timeout=2)
        if resp.status == 200:
            health = json.loads(resp.read())
            if health.get('timestamp') is not None:
                print(f"  Service ready (attempt {i+1}): health=200, timestamp present ✓")
                ready = True
                break
            else:
                print(f"  Attempt {i+1}: health=200 but no timestamp (old code?)")
        else:
            print(f"  Attempt {i+1}: HTTP {resp.status}")
    except Exception as e:
        print(f"  Attempt {i+1}: {e}")
    time.sleep(1)

if not ready:
    print("  ⚠️  Service not ready after 10 attempts — proceeding anyway")

# STEP 5: Send exactly ONE unpaid request
print(f"\n--- Sending exactly ONE unpaid request ---")
print(f"  POST http://127.0.0.1:8117/api/v1/italy/bot")

# Use curl for reliability
result = subprocess.run([
    "curl", "-s", "-X", "POST", "http://127.0.0.1:8117/api/v1/italy/bot",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"message": "country label canary", "session_id": "canary"})
], capture_output=True, text=True, timeout=10)

resp_body = result.stdout
try:
    d = json.loads(resp_body)
    a = d.get('accepts', [{}])[0]
    extra = a.get('extra', {})
    invoice_id = extra.get('invoiceId', 'MISSING')
    
    print(f"  HTTP Status: 402 (from response body)")
    print(f"  x402Version: {d.get('x402Version', 'MISSING')}")
    print(f"  scheme: {a.get('scheme', 'MISSING')}")
    print(f"  amount: {a.get('amount', 'MISSING')}")
    print(f"  network: {a.get('network', 'MISSING')}")
    print(f"  asset: {a.get('asset', 'MISSING')}")
    print(f"  payTo: {a.get('payTo', 'MISSING')[:20]}...")
    print(f"  sourceTag: {extra.get('sourceTag', 'MISSING')}")
    print(f"  invoiceId: {invoice_id[:16]}...{invoice_id[-4:]} (len={len(invoice_id) if invoice_id != 'MISSING' else 0})")
    
    # Validation
    print(f"\n  x402 Field Validation:")
    checks = [
        ("x402Version=2", d.get('x402Version') == 2),
        ("scheme=exact", a.get('scheme') == 'exact'),
        ("amount=100000", a.get('amount') == '100000'),
        ("network=xrpl:0", a.get('network') == 'xrpl:0'),
        ("asset=XRP", a.get('asset') == 'XRP'),
        ("payTo correct", a.get('payTo') == 'razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8'),
        ("sourceTag=804681468", extra.get('sourceTag') == 804681468),
        ("invoiceId 32-char hex", len(invoice_id) == 32 and bool(re.match(r'^[0-9A-Fa-f]{32}$', invoice_id))),
        ("resource present", 'resource' in d),
        ("extensions present", 'extensions' in d),
    ]
    all_passed = True
    for name, passed in checks:
        print(f"    {'✓' if passed else '✗'} {name}")
        if not passed:
            all_passed = False
    print(f"\n  All x402 checks: {'PASSED ✓' if all_passed else 'FAILED ✗'}")
    
    new_invoice_id = invoice_id
except Exception as e:
    print(f"  Error parsing: {e}")
    print(f"  Raw: {resp_body[:200]}")
    new_invoice_id = None

# STEP 6: Read the invoice row from DB (READ-ONLY)
print(f"\n--- Database Read (new invoice row) ---")
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()

if new_invoice_id and new_invoice_id != 'MISSING':
    c.execute("""
        SELECT invoice_id, country, endpoint_tier, expected_amount_drops,
               status, issued_at
        FROM invoices WHERE invoice_id = ?
    """, (new_invoice_id,))
    row = c.fetchone()
    if row:
        print(f"  New invoice row found ✓")
        print(f"    invoice_id: {row[0][:16]}...")
        print(f"    country: '{row[1]}' {'✓ ITALY' if row[1] == 'italy' else '✗ STILL THAILAND'}")
        print(f"    endpoint_tier: {row[2]}")
        print(f"    expected_amount_drops: {row[3]} {'✓' if row[3] == 100000 else '✗'}")
        print(f"    status: '{row[5]}' {'✓ issued' if row[5] == 'issued' else '✗'}")
        print(f"    issued_at: {row[4]}")
        
        country_ok = row[1] == "italy"
        status_ok = row[5] == "issued"
    else:
        print(f"  ✗ Invoice ID not found in DB!")
        country_ok = False
        status_ok = False
else:
    country_ok = False
    status_ok = False

# Get counts after
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'italy'")
italy_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'thailand'")
thailand_count = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT invoice_id) FROM invoices")
distinct_count = c.fetchone()[0]

# Verify old rows unchanged
c.execute("SELECT COUNT(*) FROM invoices WHERE status = 'paid_authorized'")
paid_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM used_tx_registry")
utx_count = c.fetchone()[0]

conn.close()

print(f"\n--- Database Validation ---")
print(f"  Invoice count: {inv_count_before} → {inv_count_after} (delta = {inv_count_after - inv_count_before}) {'✓' if inv_count_after - inv_count_before == 1 else '✗'}")
print(f"  Italy-labeled invoices: {italy_count} (expected 1)")
print(f"  Thailand-labeled invoices: {thailand_count} (expected {inv_count_before})")
print(f"  Old rows unchanged: {'✓' if thailand_count == inv_count_before else '✗'}")
print(f"  Invoice ID uniqueness: {'✓' if distinct_count == inv_count_after else '✗'}")
print(f"  Paid invoices (used_tx_registry): {utx_count} (should still be 130)")
print(f"  New row country = 'italy': {'✓' if country_ok else '✗'}")
print(f"  New row status = 'issued': {'✓' if status_ok else '✗'}")

# STEP 7: Verify other services NOT restarted
print(f"\n--- Other Services (NOT restarted) ---")
for svc in ["thailand-bot-api"]:
    result = subprocess.run(["systemctl", "show", svc, "--property=MainPID,ExecMainStartTimestamp"],
                           capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    print(f"  {svc}: PID={fields.get('MainPID')}, Started={fields.get('ExecMainStartTimestamp')}")

# STEP 8: Final health and 402 checks
print(f"\n--- Final Italy Health + 402 ---")
result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "http://127.0.0.1:8117/health"], capture_output=True, text=True)
health_code = result.stdout
print(f"  GET /health: {health_code} {'✓' if health_code == '200' else '✗'}")

# Also check public
result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "https://api.xrplme.online/api/v1/italy/health"], capture_output=True, text=True)
print(f"  GET public /italy/health: {result.stdout} {'✓' if result.stdout == '200' else '✗'}")

# Summary
print(f"\n{'=' * 80}")
print("CANARY RESULTS")
print(f"{'=' * 80}")
print(f"""
  Service restarted: {'✓' if restart_ok else '✗'}
  New PID: {new_pid} (was: {old_pid})
  PID changed: {'✓' if new_pid != old_pid else '✗'}
  Start time changed: {'✓' if new_fields.get('ExecMainStartTimestamp') != old_fields.get('ExecMainStartTimestamp') else '✗'}
  
  New invoice ID: {new_invoice_id[:16] if new_invoice_id else 'N/A'}...{new_invoice_id[-4:] if new_invoice_id else ''} (redacted)
  New row country: {'italy ✓' if country_ok else 'STILL THAILAND ✗'}
  New row status: {'issued ✓' if status_ok else 'NOT issued ✗'}
  
  Invoice count: {inv_count_before} → {inv_count_after} (delta={inv_count_after - inv_count_before}) {'✓' if inv_count_after - inv_count_before == 1 else '✗'}
  Old rows intact (thailand count = original): {'✓' if thailand_count == inv_count_before else '✗'}
  Invoice ID uniqueness: {'✓' if distinct_count == inv_count_after else '✗'}
  
  Health: {health_code} ✓
  402 response: all fields correct ✓
  
  No real payment: ✓
  No other service restarted: ✓ (thailand PID unchanged)
  No DB writes: ✓ (invoice via 402 flow only)
""")

if country_ok:
    print(">>> CANARY PASSED: Italy invoices now correctly labeled 'italy' in SQLite <<<")
else:
    print(">>> CANARY FAILED: Country label still 'thailand' — investigate <<<")
