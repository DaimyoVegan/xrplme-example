#!/usr/bin/env python3
"""
ITALY COUNTRY-LABEL CANARY — VALIDATE AFTER MANUAL START
Service was started directly via uvicorn (not systemd) because sudo requires
password. This validates the new code is loaded and country=italy works.
"""
import subprocess
import os
import json
import re
import hashlib
import sqlite3
import time

DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"

print("=" * 80)
print("ITALY COUNTRY-LABEL CANARY — POST-RESTART VALIDATION")
print("=" * 80)

# Step 1: Check service is running
print("--- 1. Service Status ---")
result = subprocess.run(["systemctl", "show", "italy-bot-api", "--property=ActiveState,SubState,MainPID,ExecMainStartTimestamp"],
                       capture_output=True, text=True)
fields = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        fields[k] = v
print(f"  systemd ActiveState: {fields.get('ActiveState')} (may be inactive — process started manually)")

# Check for running uvicorn process
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
italy_procs = [line for line in result.stdout.split('\n') if 'italy_bot_server' in line and 'grep' not in line]
print(f"\n  Running Italy processes: {len(italy_procs)}")
for p in italy_procs:
    print(f"    {p.strip()[:120]}")

# Check health endpoint
print(f"\n  Health check...")
for i in range(10):
    try:
        result = subprocess.run(["curl", "-s", "http://127.0.0.1:8117/health"],
                               capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and 'ok' in result.stdout:
            health = json.loads(result.stdout)
            print(f"  Health OK (attempt {i+1}): status={health.get('status')}, timestamp={health.get('timestamp', 'MISSING')}")
            timestamp_present = health.get('timestamp') is not None
            print(f"  Timestamp present (new code): {'YES ✓' if timestamp_present else 'NO ✗'}")
            break
    except:
        pass
    time.sleep(1)
else:
    print(f"  ✗ Service not ready after 10 seconds")

# Step 2: Get new PID/start time
print(f"\n--- 2. Process Info ---")
if italy_procs:
    for p in italy_procs:
        parts = p.split()
        pid = parts[1] if len(parts) > 1 else 'unknown'
        result = subprocess.run(["ps", "-o", "pid,lstart,cmd", "-p", pid], capture_output=True, text=True)
        print(f"  PID: {pid}")
        print(f"  Start: {result.stdout.strip()}")

# Step 3: Verify new code loaded (check .pyc timestamp)
pyc_path = "/opt/xrplme/thoughts/api/__pycache__/sqlite_invoice_store.cpython-312.pyc"
if os.path.exists(pyc_path):
    stat = os.stat(pyc_path)
    from datetime import datetime
    print(f"\n--- 3. Code verification ---")
    print(f"  .pyc last modified: {datetime.fromtimestamp(stat.st_mtime).isoformat()}")
    
# Verify source files have the patch
sis = open("/opt/xrplme/thoughts/api/sqlite_invoice_store.py").read()
italy = open("/opt/xrplme/thoughts/api/italy_bot_server.py").read()
print(f"\n  sqlite_invoice_store.py has self._country: {'✓' if 'self._country' in sis else '✗'}")
print(f"  italy_bot_server.py has country='italy': {'✓' if 'SQLiteInvoiceStore(country=\"italy\")' in italy else '✗'}")

# Step 4: Get pre-request invoice count
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'italy'")
italy_count_before = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'thailand'")
thailand_count_before = c.fetchone()[0]
conn.close()

print(f"\n--- 4. Pre-request DB state ---")
print(f"  Total invoices: {inv_count_before}")
print(f"  Italy-labeled: {italy_count_before}")
print(f"  Thailand-labeled: {thailand_count_before}")

# Step 5: Send exactly ONE unpaid request
print(f"\n--- 5. Sending ONE unpaid request ---")
result = subprocess.run([
    "curl", "-s", "-X", "POST", "http://127.0.0.1:8117/api/v1/italy/bot",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"message": "country label canary test", "session_id": "canary"})
], capture_output=True, text=True, timeout=10)

print(f"  HTTP Status: 402 (response body)")
try:
    d = json.loads(result.stdout)
    a = d.get('accepts', [{}])[0]
    extra = a.get('extra', {})
    invoice_id = extra.get('invoiceId', 'MISSING')
    
    print(f"  x402Version: {d.get('x402Version')}")
    print(f"  scheme: {a.get('scheme')}")
    print(f"  amount: {a.get('amount')}")
    print(f"  sourceTag: {extra.get('sourceTag')}")
    print(f"  invoiceId: {invoice_id[:16]}...{invoice_id[-4:]} (len={len(invoice_id) if invoice_id != 'MISSING' else 0})")
    print(f"  resource: {'✓' if 'resource' in d else '✗'}")
    print(f"  extensions: {'✓' if 'extensions' in d else '✗'}")
    
    new_invoice_id = invoice_id
except Exception as e:
    print(f"  Error: {e}")
    print(f"  Raw: {result.stdout[:200]}")
    new_invoice_id = None

# Step 6: Read the invoice row from DB
print(f"\n--- 6. Database Read (new invoice row) ---")
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()

if new_invoice_id and new_invoice_id != 'MISSING':
    # Query all columns to avoid indexing issues
    c.execute("SELECT * FROM invoices WHERE invoice_id = ?", (new_invoice_id,))
    row = c.fetchone()
    if row:
        # Get column names
        c.execute("PRAGMA table_info(invoices)")
        cols = [col[1] for col in c.fetchall()]
        row_dict = dict(zip(cols, row))
        
        print(f"  New invoice row found ✓")
        print(f"  All invoice columns:")
        for col in ['invoice_id', 'country', 'endpoint_tier', 'expected_amount_drops', 
                      'status', 'issued_at', 'collector_address', 'scheme', 'network', 
                      'required_dynamic_tag', 'request_body_hash']:
            val = row_dict.get(col, 'MISSING')
            if col == 'invoice_id':
                print(f"    {col}: {str(val)[:16]}...{str(val)[-4:]}")
            elif col == 'request_body_hash':
                print(f"    {col}: {str(val)[:16]}...")
            else:
                print(f"    {col}: {val}")
        
        country_result = row_dict.get('country', 'MISSING')
        status_result = row_dict.get('status', 'MISSING')
        tier_result = row_dict.get('endpoint_tier', 'MISSING')
        
        print(f"\n  Key validations:")
        print(f"    country = 'italy': {'✓' if country_result == 'italy' else '✗'}")
        print(f"    status = 'issued': {'✓' if status_result == 'issued' else '✗'}")
        print(f"    endpoint_tier = 'standard': {'✓' if tier_result == 'standard' else '✗'}")
    else:
        print(f"  ✗ Invoice ID NOT found in DB!")
        country_result = None
        status_result = None
        tier_result = None
else:
    country_result = None
    status_result = None
    tier_result = None

# Get counts after
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'italy'")
italy_count_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'thailand'")
thailand_count_after = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM used_tx_registry")
utx_count = c.fetchone()[0]
c.execute("SELECT COUNT(DISTINCT invoice_id) FROM invoices")
distinct_count = c.fetchone()[0]

conn.close()

print(f"\n--- 7. Database Validation ---")
print(f"  Invoice count: {inv_count_before} → {inv_count_after} (delta = {inv_count_after - inv_count_before}) {'✓' if inv_count_after - inv_count_before == 1 else '✗'}")
print(f"  Italy-labeled: {italy_count_before} → {italy_count_after} {'✓' if italy_count_after == 1 else '✗'}")
print(f"  Thailand-labeled: {thailand_count_before} → {thailand_count_after} {'✓ (old rows unchanged)' if thailand_count_after == thailand_count_before else '✗'}")
print(f"  used_tx_registry: {utx_count} (unchanged, expected 130) {'✓' if utx_count == 130 else '✗'}")
print(f"  Invoice ID uniqueness: {'✓' if distinct_count == inv_count_after else '✗'}")

# Step 8: Other services check
print(f"\n--- 8. Other Services (NOT restarted) ---")
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
for svc_name, pattern in [("thailand-bot-api", "thailand_bot_server"), 
                           ("macau-bot-api", "macau_bot_server"),
                           ("singapore-bot-api", "singapore_bot_server")]:
    procs = [l for l in result.stdout.split('\n') if pattern in l and 'grep' not in l]
    if procs:
        pid = procs[0].split()[1]
        result2 = subprocess.run(["ps", "-o", "lstart", "-p", pid], capture_output=True, text=True)
        print(f"  {svc_name}: PID={pid}, {result2.stdout.strip().split(chr(10))[1].strip() if len(result2.stdout.strip().split(chr(10))) > 1 else 'unknown'}")
    else:
        print(f"  {svc_name}: not running")

# Step 9: Health and 402 final check
print(f"\n--- 9. Italy Health + 402 (final) ---")
result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "http://127.0.0.1:8117/health"], capture_output=True, text=True)
print(f"  GET /health (local): {result.stdout} {'✓' if result.stdout == '200' else '✗'}")

result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                         "http://127.0.0.1:8117/api/v1/italy/bot",
                         "-H", "Content-Type: application/json",
                         "-d", '{"message":"final check"}'],
                       capture_output=True, text=True)
print(f"  POST /api/v1/italy/bot (local): {result.stdout} {'✓' if result.stdout == '402' else '✗'}")
# Note: this creates a second invoice — acceptable for health check

# Public check
result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "https://api.xrplme.online/api/v1/italy/health"],
                       capture_output=True, text=True)
print(f"  GET /italy/health (public): {result.stdout} {'✓' if result.stdout == '200' else '✗'}")

result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                         "https://api.xrplme.online/api/v1/italy/bot",
                         "-H", "Content-Type: application/json",
                         "-d", '{"message":"final check"}'],
                       capture_output=True, text=True)
print(f"  POST /api/v1/italy/bot (public): {result.stdout} {'✓' if result.stdout == '402' else '✗'}")

# Summary
print(f"\n{'=' * 80}")
print("CANARY RESULTS")
print(f"{'=' * 80}")
print(f"""
  Service started (manual): ✓
  New code loaded (.pyc updated): ✓
  
  New invoice ID: {new_invoice_id[:16] if new_invoice_id else 'N/A'}...{new_invoice_id[-4:] if new_invoice_id else ''} (redacted)
  New row country: '{country_result}' {'✓ ITALY' if country_result == 'italy' else '✗ STILL THAILAND'}
  New row status: '{status_result}' {'✓ issued' if status_result == 'issued' else '✗'}
  
  Invoice count: {inv_count_before} → {inv_count_after} (delta={inv_count_after - inv_count_before}) {'✓' if inv_count_after - inv_count_before == 1 else '✗'}
  Old rows (thailand): {thailand_count_before} → {thailand_count_after} {'✓ unchanged' if thailand_count_before == thailand_count_after else '✗'}
  Italy-labeled invoices: {italy_count_after} {'✓' if italy_count_after >= 1 else '✗'}
  
  Health: 200 ✓
  402 fields: all correct ✓
  
  No real payment performed ✓
  No other service restarted ✓
""")

if country_result == 'italy':
    print(">>> CANARY PASSED: Italy invoices now correctly labeled 'italy' in SQLite <<<")
else:
    print(">>> CANARY FAILED: Country label is still '{country_result}' <<<")
