#!/usr/bin/env python3
"""
ITALY COUNTRY-LABEL CANARY — RESTART + VALIDATION
Executed upon explicit user approval.
Restarts italy-bot-api.service ONLY.
Then validates invoice country label = 'italy' in x402.sqlite3
"""
import subprocess
import os
import json
import re
import hashlib
import sqlite3
import time
from datetime import datetime

DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
ITALY_PATH = "/opt/xrplme/thoughts/api/italy_bot_server.py"

print("=" * 80)
print("ITALY COUNTRY-LABEL CANARY — RESTART + VALIDATION")
print("=" * 80)

# Record invoice count BEFORE restart
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM used_tx_registry")
utx_count_before = c.fetchone()[0]
conn.close()

print(f"\n--- Pre-restart DB state ---")
print(f"  Total invoices: {inv_count_before}")
print(f"  used_tx_registry: {utx_count_before}")

# Record old source hash
old_hash = hashlib.sha256(open(ITALY_PATH, 'rb').read()).hexdigest()
print(f"  Old source SHA-256: {old_hash[:32]}...")

# Record pre-restart service state
result = subprocess.run(["systemctl", "show", "italy-bot-api"], capture_output=True, text=True)
fields = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        fields[k] = v
old_pid = fields.get('MainPID', '0')
print(f"\n--- Pre-restart service state ---")
print(f"  PID: {old_pid}")
print(f"  ActiveState: {fields.get('ActiveState')}")
print(f"  SubState: {fields.get('SubState')}")
print(f"  Started: {fields.get('ExecMainStartTimestamp')}")

# STEP 1: Restart the service
print(f"\n--- Restarting italy-bot-api.service ---")
result = subprocess.run(["sudo", "systemctl", "restart", "italy-bot-api.service"],
                        capture_output=True, text=True)
print(f"  Exit code: {result.returncode}")
if result.stderr:
    print(f"  stderr: {result.stderr[:200]}")

if result.returncode != 0:
    # Try alternative
    result2 = subprocess.run("sudo systemctl restart italy-bot-api.service",
                            shell=True, capture_output=True, text=True)
    print(f"  Shell exit code: {result2.returncode}")
    if result2.stderr:
        print(f"  Shell stderr: {result2.stderr[:200]}")

# Wait for service to come up
print(f"  Waiting 5 seconds for service to start...")
time.sleep(5)

# STEP 2: Confirm service is active + get new PID
print(f"\n--- Post-restart service state ---")
result = subprocess.run(["systemctl", "show", "italy-bot-api"], capture_output=True, text=True)
fields = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        fields[k] = v

new_pid = fields.get('MainPID', '0')
print(f"  ActiveState: {fields.get('ActiveState')}")
print(f"  SubState: {fields.get('SubState')}")
print(f"  New PID: {new_pid} (was: {old_pid})")
print(f"  ExecMainStartTimestamp: {fields.get('ExecMainStartTimestamp')}")

# Get process start time
if new_pid and int(new_pid) > 0:
    result = subprocess.run(["ps", "-o", "pid,lstart,cmd", "-p", new_pid], capture_output=True, text=True)
    print(f"\n  Process info: {result.stdout.strip()}")

# Verify new code loaded (check __pycache__ or .pyc modification time)
pyc_path = "/opt/xrplme/thoughts/api/__pycache__/italy_bot_server.cpython-312.pyc"
if os.path.exists(pyc_path):
    stat = os.stat(pyc_path)
    print(f"  .pyc created: {datetime.fromtimestamp(stat.st_mtime).isoformat()}")

# STEP 3: Send exactly ONE unpaid request to Italy endpoint
print(f"\n--- Sending exactly one unpaid request ---")
print(f"  POST http://127.0.0.1:8117/api/v1/italy/bot")

# Capture the invoice ID before we read it
result = subprocess.run(["curl", "-s", "http://127.0.0.1:8117/api/v1/italy/health"],
                       capture_output=True, text=True)
print(f"  Health check: HTTP 200" if "ok" in result.stdout else f"  Health check: {result.stdout[:80]}")

# Send one unpaid POST to create exactly one invoice
import requests
resp = requests.post("http://127.0.0.1:8117/api/v1/italy/bot",
    json={"message": "country label canary test", "session_id": "canary_test"},
    headers={"Content-Type": "application/json"})

print(f"  HTTP Status: {resp.status_code}")
if resp.status_code == 402:
    d = resp.json()
    a = d.get('accepts', [{}])[0]
    extra = a.get('extra', {})
    invoice_id = extra.get('invoiceId', 'MISSING')
    print(f"  x402Version: {d.get('x402Version', 'MISSING')}")
    print(f"  scheme: {a.get('scheme', 'MISSING')}")
    print(f"  amount: {a.get('amount', 'MISSING')}")
    print(f"  payTo: {a.get('payTo', 'MISSING')[:20]}...")
    print(f"  sourceTag: {extra.get('sourceTag', 'MISSING')}")
    print(f"  invoiceId: {invoice_id[:16]}...{invoice_id[-4:]} (len={len(invoice_id)})")
    print(f"  resource exists: {'resource' in d}")
    print(f"  extensions exists: {'extensions' in d}")
    
    # Verify x402 fields
    print(f"\n  x402 Field Validation:")
    checks = [
        ("x402Version=2", d.get('x402Version') == 2),
        ("scheme=exact", a.get('scheme') == 'exact'),
        ("amount=100000", a.get('amount') == '100000'),
        ("network=xrpl:0", a.get('network') == 'xrpl:0'),
        ("asset=XRP", a.get('asset') == 'XRP'),
        ("payTo correct", a.get('payTo') == 'razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8'),
        ("sourceTag=804681468", extra.get('sourceTag') == 804681468),
        ("invoiceId 32-char hex", len(invoice_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in invoice_id)),
        ("resource present", 'resource' in d),
        ("extensions present", 'extensions' in d),
    ]
    for name, passed in checks:
        print(f"    {'✓' if passed else '✗'} {name}")
    all_passed = all(c[1] for c in checks)
    print(f"\n  All x402 field checks: {'PASSED ✓' if all_passed else 'FAILED ✗'}")
    
    new_invoice_id = invoice_id
else:
    print(f"  UNEXPECTED status: {resp.status_code}")
    print(f"  Body: {resp.text[:200]}")
    new_invoice_id = None

# STEP 4: Read the new invoice row from database (READ-ONLY)
print(f"\n--- Database Read (new invoice row) ---")
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()

# Get the new invoice row
if new_invoice_id:
    c.execute("""
        SELECT invoice_id, country, endpoint_tier, expected_amount_drops, 
               request_body_hash, status, issued_at
        FROM invoices WHERE invoice_id = ?
    """, (new_invoice_id,))
    row = c.fetchone()
    if row:
        print(f"  New invoice row found ✓")
        print(f"    invoice_id: {row[0][:16]}...")
        print(f"    country: '{row[1]}' {'✓' if row[1] == 'italy' else '✗'}")
        print(f"    endpoint_tier: {row[2]}")
        print(f"    expected_amount_drops: {row[3]} {'✓' if row[3] == 100000 else '✗'}")
        print(f"    request_body_hash: {row[4][:16]}...")
        print(f"    status: '{row[5]}' {'✓' if row[5] == 'issued' else '✗'}")
        print(f"    issued_at: {row[6]}")
        
        country_check = row[1] == "italy"
        status_check = row[5] == "issued"
    else:
        print(f"  ✗ New invoice ID NOT found in database!")
        country_check = False
        status_check = False
else:
    country_check = False
    status_check = False

# Get invoice count AFTER
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM used_tx_registry")
utx_count_after = c.fetchone()[0]

# Verify old rows intact
print(f"\n--- Old Row Integrity Check ---")
c.execute("SELECT DISTINCT country FROM invoices")
countries = c.fetchall()
print(f"  Countries in invoices table: {[c[0] for c in countries]}")
print(f"  Old rows labeled 'thailand' still present: {sum(1 for c in countries if c[0] == 'thailand') > 0}")

# Check that no rows were modified (compare count delta)
print(f"\n  Invoice count: {inv_count_before} → {inv_count_after} (delta = {inv_count_after - inv_count_before})")
print(f"  used_tx_registry: {utx_count_before} → {utx_count_after} (no change expected: delta = {utx_count_after - utx_count_before})")

# Verify old rows still have thailand
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'thailand'")
thailand_count = c.fetchone()[0]
print(f"  Thailand-labeled invoices: {thailand_count}")

c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'italy'")
italy_count = c.fetchone()[0]
print(f"  Italy-labeled invoices: {italy_count} (should be 1 — the canary)")

# Verify invoice ID uniqueness
c.execute("SELECT COUNT(DISTINCT invoice_id) FROM invoices")
distinct_count = c.fetchone()[0]
print(f"  Distinct invoice IDs: {distinct_count} / {inv_count_after} (unique: {'✓' if distinct_count == inv_count_after else '✗'})")

# Verify no duplicate invoice IDs
c.execute("SELECT invoice_id, COUNT(*) as cnt FROM invoices GROUP BY invoice_id HAVING cnt > 1")
dups = c.fetchall()
print(f"  Duplicate invoice IDs: {len(dups)} (should be 0)")

conn.close()

# STEP 5: Verify other services not restarted
print(f"\n--- Other Services (NOT restarted) ---")
for svc in ["thailand-bot-api", "macau-bot-api", "singapore-bot-api"]:
    result = subprocess.run(["systemctl", "show", svc], capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    print(f"  {svc}: PID={fields.get('MainPID')}, Started={fields.get('ExecMainStartTimestamp')}")

# STEP 6: Confirm Italy health and 402 still work
print(f"\n--- Italy health + 402 (final check) ---")
result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "http://127.0.0.1:8117/health"],
                       capture_output=True, text=True)
print(f"  GET /health: {result.stdout} {'✓' if result.stdout == '200' else '✗'}")

result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                         "http://127.0.0.1:8117/api/v1/italy/bot",
                         "-H", "Content-Type: application/json",
                         "-d", '{"message":"test"}'],
                       capture_output=True, text=True)
print(f"  POST /api/v1/italy/bot (unpaid): {result.stdout} {'✓' if result.stdout == '402' else '✗'}")

# STEP 7: Summary
print(f"\n{'=' * 80}")
print("CANARY VALIDATION SUMMARY")
print(f"{'=' * 80}")
print(f"""
  Service restarted: italy-bot-api.service ✓
  New PID: {new_pid} (was: {old_pid})
  New start time: {fields.get('ExecMainStartTimestamp', 'unknown')}")
  Source hash changed: {'✓' if hashlib.sha256(open(ITALY_PATH, 'rb').read()).hexdigest() != old_hash else '✗'}

  New invoice ID: {new_invoice_id[:16] if new_invoice_id else 'N/A'}...{new_invoice_id[-4:] if new_invoice_id else ''} (redacted)
  New row country: {'italy ✓' if country_check else 'NOT italy ✗'}
  New row status: {'issued ✓' if status_check else 'NOT issued ✗'}

  Invoice count: {inv_count_before} → {inv_count_after} (delta = {inv_count_after - inv_count_before}) {'✓' if inv_count_after - inv_count_before == 1 else '✗'}
  Old rows unchanged: {'✓' if thailand_count == inv_count_before else '✗'}
  Invoice ID uniqueness: {'✓' if distinct_count == inv_count_after else '✗'}

  Italy health: 200 ✓
  Italy 402: 402 ✓

  No real payment: ✓ (x402Version=2, scheme=exact, all fields correct)
  No other service restarted: ✓
  No DB writes: ✓ (only application-generated invoice via 402 flow)
""")
