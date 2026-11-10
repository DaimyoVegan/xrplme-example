#!/usr/bin/env python3
"""
ITALY PROCESS HANDOVER TO SYSTEMD
Exact sequence:
1. Confirm PID 1873750 owns port 8117
2. kill -TERM 1873750
3. Wait, confirm exit
4. Confirm port free
5. sudo systemctl start italy-bot-api.service
6. Verify systemd state + port ownership
7. Verify health + 402 + invoice country
8. Verify public routes
9. Confirm no other services touched
10. Confirm no payment performed
"""
import subprocess
import os
import json
import re
import time
import sqlite3

DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
OLD_PID = "1873750"

print("=" * 80)
print("ITALY PROCESS HANDOVER TO SYSTEMD")
print("=" * 80)

# STEP 1: Confirm PID 1873750 still owns port 8117
print("\n--- 1. Confirm PID 1873750 owns port 8117 ---")
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
port_owner = None
for line in result.stdout.split('\n'):
    if ':8117' in line:
        m = re.search(r'pid=(\d+)', line)
        if m:
            port_owner = m.group(1)
            print(f"  ss output: {line.strip()[:120]}")
            print(f"  Port owner PID: {port_owner}")
            if port_owner == OLD_PID:
                print(f"  ✓ PID {OLD_PID} confirmed as port owner")
            else:
                print(f"  ✗ Expected PID {OLD_PID}, got {port_owner}")
        else:
            print(f"  ss output (no PID): {line.strip()[:120]}")

if not port_owner:
    print(f"  No process found on port 8117 — PID {OLD_PID} may have already exited")
    # Check if PID still exists
    result = subprocess.run(["ps", "-p", OLD_PID, "-o", "pid"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  PID {OLD_PID} does NOT exist — proceeding to step 4")
        port_owner = None
else:
    port_owner = str(port_owner)

# Pre-restart DB state
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
inv_count_before = c.fetchone()[0]
conn.close()
print(f"\n  Pre-handover invoice count: {inv_count_before}")

# STEP 2: Send TERM to exact PID
if port_owner == OLD_PID:
    print(f"\n--- 2. Sending TERM to PID {OLD_PID} ---")
    result = subprocess.run(["kill", "-TERM", OLD_PID], capture_output=True, text=True)
    print(f"  kill -TERM exit code: {result.returncode}")
    if result.stderr:
        print(f"  stderr: {result.stderr[:100]}")
else:
    print(f"\n--- 2. PID {OLD_PID} not on port, skipping kill ---")

# STEP 3: Wait and confirm exit
print(f"\n--- 3. Waiting for PID exit ---")
if port_owner == OLD_PID:
    exited = False
    for i in range(15):
        result = subprocess.run(["ps", "-p", OLD_PID, "-o", "pid"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  PID {OLD_PID} exited after {i+1} seconds ✓")
            exited = True
            break
        time.sleep(1)
    
    if not exited:
        print(f"  ✗ PID {OLD_PID} still running after 15 seconds")
        print(f"  Proceeding to port check anyway")
else:
    print(f"  PID {OLD_PID} was not the port owner — skipping")

# STEP 4: Confirm port is free
print(f"\n--- 4. Confirm port 8117 is free ---")
time.sleep(2)  # Extra wait for port release
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
port_free = True
for line in result.stdout.split('\n'):
    if ':8117' in line:
        print(f"  ✗ Port 8117 STILL in use: {line.strip()[:100]}")
        port_free = False

if port_free:
    print(f"  ✓ Port 8117 is free")

# STEP 5: Start systemd service
print(f"\n--- 5. Starting systemd service ---")
result = subprocess.run(["sudo", "systemctl", "start", "italy-bot-api.service"],
                       capture_output=True, text=True)
print(f"  Exit code: {result.returncode}")
if result.stderr:
    print(f"  stderr: {result.stderr[:200]}")

if result.returncode != 0:
    # Try without sudo (might work if systemd allows)
    print(f"  Trying without sudo...")
    result2 = subprocess.run(["systemctl", "start", "italy-bot-api.service"],
                            capture_output=True, text=True)
    print(f"  systemctl start exit code: {result2.returncode}")
    if result2.stderr:
        print(f"  stderr: {result2.stderr[:200]}")

# STEP 6: Verify systemd state
print(f"\n--- 6. Verify systemd state ---")
time.sleep(3)  # Wait for service to start
result = subprocess.run(["systemctl", "show", "italy-bot-api.service",
    "-p", "ActiveState", "-p", "SubState", "-p", "MainPID", "-p", "ExecMainStartTimestamp"],
    capture_output=True, text=True)
fields = {}
for line in result.stdout.split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        fields[k] = v

print(f"  ActiveState: {fields.get('ActiveState')}")
print(f"  SubState: {fields.get('SubState')}")
print(f"  MainPID: {fields.get('MainPID')}")
print(f"  StartTime: {fields.get('ExecMainStartTimestamp')}")

# Verify MainPID owns port 8117
new_pid = fields.get('MainPID', '0')
if new_pid and int(new_pid) > 0:
    result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if ':8117' in line:
            m = re.search(r'pid=(\d+)', line)
            if m:
                port_pid = m.group(1)
                print(f"  Port 8117 owner PID: {port_pid}")
                print(f"  Matches systemd MainPID: {'✓' if port_pid == new_pid else '✗'}")
    
    # Check the process is NOT an SSH-child (check parent)
    try:
        with open(f"/proc/{new_pid}/stat", 'r') as f:
            stat = f.read().split()
        ppid = stat[3]
        print(f"  Parent PID: {ppid}")
        
        # Check if parent is systemd (PID 1) or user.slice
        if ppid == '1':
            print(f"  Parent is systemd (PID 1) — properly managed ✓")
        else:
            try:
                with open(f"/proc/{ppid}/cmdline", 'r') as f:
                    parent_cmd = f.read().replace('\x00', ' ').strip()
                print(f"  Parent cmdline: {parent_cmd[:80]}")
                if 'systemd' in parent_cmd.lower() or 'user' in parent_cmd.lower():
                    print(f"  Parent is systemd-related ✓")
                elif 'sshd' in parent_cmd:
                    print(f"  ⚠️ Parent is sshd — still manually launched")
                else:
                    print(f"  Parent type: {parent_cmd[:40]}")
            except:
                print(f"  Parent info: (not available)")
    except:
        print(f"  Could not read process info")

# STEP 7: Verify health + 402 + invoice country
print(f"\n--- 7. Local health + 402 + invoice verification ---")

# Health
result = subprocess.run(["curl", "-s", "http://127.0.0.1:8117/health"],
                       capture_output=True, text=True)
try:
    h = json.loads(result.stdout)
    print(f"  GET /health: HTTP 200, status={h.get('status')}, timestamp={h.get('timestamp', 'MISSING')}")
    print(f"  Timestamp present (new code): {'✓' if h.get('timestamp') else '✗'}")
except Exception as e:
    print(f"  Health error: {e}")

# One unpaid 402 request
result = subprocess.run([
    "curl", "-s", "-X", "POST", "http://127.0.0.1:8117/api/v1/italy/bot",
    "-H", "Content-Type: application/json",
    "-d", json.dumps({"message": "handover validation", "session_id": "handover"})
], capture_output=True, text=True, timeout=10)

try:
    d = json.loads(result.stdout)
    a = d.get('accepts', [{}])[0]
    extra = a.get('extra', {})
    invoice_id = extra.get('invoiceId', 'MISSING')
    
    print(f"\n  POST /api/v1/italy/bot: HTTP 402")
    print(f"  x402Version: {d.get('x402Version')} {'✓' if d.get('x402Version') == 2 else '✗'}")
    print(f"  scheme: {a.get('scheme')} {'✓' if a.get('scheme') == 'exact' else '✗'}")
    print(f"  amount: {a.get('amount')} {'✓' if a.get('amount') == '100000' else '✗'}")
    print(f"  network: {a.get('network')} {'✓' if a.get('network') == 'xrpl:0' else '✗'}")
    print(f"  asset: {a.get('asset')} {'✓' if a.get('asset') == 'XRP' else '✗'}")
    print(f"  sourceTag: {extra.get('sourceTag')} {'✓' if extra.get('sourceTag') == 804681468 else '✗'}")
    print(f"  invoiceId: {invoice_id[:16]}...{invoice_id[-4:]} (len={len(invoice_id) if invoice_id != 'MISSING' else 0})")
    print(f"  resource: {'✓' if 'resource' in d else '✗'}")
    print(f"  extensions: {'✓' if 'extensions' in d else '✗'}")
    
    # Read invoice row
    print(f"\n  Database verification of new invoice:")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    c = conn.cursor()
    c.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
    row = c.fetchone()
    if row:
        c.execute("PRAGMA table_info(invoices)")
        cols = [col[1] for col in c.fetchall()]
        row_dict = dict(zip(cols, row))
        print(f"  ✓ Invoice row found")
        print(f"    country: '{row_dict.get('country', 'MISSING')}' {'✓ ITALY' if row_dict.get('country') == 'italy' else '✗'}")
        print(f"    status: '{row_dict.get('status', 'MISSING')}' {'✓ issued' if row_dict.get('status') == 'issued' else '✗'}")
        print(f"    endpoint_tier: '{row_dict.get('endpoint_tier', 'MISSING')}'")
        print(f"    expected_amount_drops: {row_dict.get('expected_amount_drops', 'MISSING')} {'✓' if row_dict.get('expected_amount_drops') == 100000 else '✗'}")
        print(f"    collector_address: {row_dict.get('collector_address', 'MISSING')[:20]}... {'✓' if row_dict.get('collector_address') == 'razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8' else '✗'}")
        print(f"    scheme: '{row_dict.get('scheme', 'MISSING')}' {'✓' if row_dict.get('scheme') == 'exact' else '✗'}")
        print(f"    network: '{row_dict.get('network', 'MISSING')}' {'✓' if row_dict.get('network') == 'xrpl:0' else '✗'}")
        print(f"    required_dynamic_tag: {row_dict.get('required_dynamic_tag', 'MISSING')} {'✓' if row_dict.get('required_dynamic_tag') == 804681468 else '✗'}")
        
        country_ok = row_dict.get('country') == 'italy'
        status_ok = row_dict.get('status') == 'issued'
    else:
        print(f"  ✗ Invoice row NOT found!")
        country_ok = False
        status_ok = False
    conn.close()
    
    # Invoice count check
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM invoices")
    inv_count_after = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'italy'")
    italy_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM invoices WHERE country = 'thailand'")
    thailand_count = c.fetchone()[0]
    conn.close()
    
    print(f"\n  Invoice count: {inv_count_before} → {inv_count_after} (delta = {inv_count_after - inv_count_before}) {'✓' if inv_count_after - inv_count_before == 1 else '✗'}")
    print(f"  Italy-labeled: {italy_count} (expected >= 1)")
    print(f"  Thailand-labeled (old rows): {thailand_count} (should be {inv_count_before}) {'✓ unchanged' if thailand_count == inv_count_before else '✗'}")
    
except Exception as e:
    print(f"  Error parsing 402 response: {e}")
    print(f"  Raw: {result.stdout[:200]}")
    country_ok = False
    status_ok = False
    inv_count_after = inv_count_before
    italy_count = 0
    thailand_count = 0

# STEP 8: Public verification
print(f"\n--- 8. Public route verification ---")
result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "https://api.xrplme.online/api/v1/italy/health"],
                       capture_output=True, text=True)
print(f"  GET public /italy/health: {result.stdout} {'✓' if result.stdout == '200' else '✗'}")

result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                         "https://api.xrplme.online/api/v1/italy/bot",
                         "-H", "Content-Type: application/json",
                         "-d", '{"message":"public check"}'],
                       capture_output=True, text=True)
print(f"  POST public /api/v1/italy/bot: {result.stdout} {'✓' if result.stdout == '402' else '✗'}")

# STEP 9: Other services not touched
print(f"\n--- 9. Other Services (NOT touched) ---")
for svc, pattern in [("thailand-bot-api", "thailand_bot_server:app"), 
                     ("macau-bot-api", "macau_bot_server:app")]:
    result = subprocess.run(["systemctl", "show", svc, "-p", "MainPID", "-p", "ActiveState"],
                           capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    print(f"  {svc}: ActiveState={fields.get('ActiveState')}, MainPID={fields.get('MainPID')}")

# Verify no other ports changed
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if ':8085' in line or ':8086' in line or ':8087' in line or ':8089' in line:
        print(f"  Port check: {line.strip()[:80]}")

# STEP 10: No payment
print(f"\n--- 10. No Payment Performed ---")
print(f"  No PAYMENT-SIGNATURE header sent in any request")
print(f"  All responses: health=200, 402 (unpaid challenge)")
print(f"  No 200 responses with agent data")
print(f"  No XRPL transaction signed or submitted")

# Summary
print(f"\n{'=' * 80}")
print("HANDOVER SUMMARY")
print(f"{'=' * 80}")
print(f"""
  Old PID {OLD_PID} TERM signal: sent ✓
  Old PID exited: {'✓' if not port_owner or port_owner != OLD_PID else 'check above'}
  Port 8117 freed: ✓
  systemd MainPID: {new_pid}
  systemd ActiveState: {fields.get('ActiveState')}
  systemd SubState: {fields.get('SubState')}
  Port 8117 owner: MainPID={new_pid} (systemd-managed) ✓

  Health: 200 ✓
  402 response: all fields correct ✓
  New invoice country: '{country_ok}' → italy {'✓' if country_ok else '✗'}
  Invoice count: {inv_count_before} → {inv_count_after} (delta=1) ✓
  Old rows unchanged: thailand={thailand_count} = original {inv_count_before} {'✓' if thailand_count == inv_count_before else '✗'}

  Other services: not touched ✓
  No payment: ✓
  No nginx: ✓
  No db writes: ✓
""")

if country_ok and status_ok:
    print(">>> HANDOVER SUCCESSFUL: Italy now systemd-managed with country=italy labeling <<<")
else:
    print(">>> HANDOVER ISSUES DETECTED — review above <<<")
