#!/usr/bin/env python3
"""
V3 CONSISTENCY AUDIT — Phase 1: Service Status
READ-ONLY: no changes, no restarts, no payments.
"""
import subprocess
import json
import re
import time
import os

DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"

# 30 countries with their expected service names and ports
COUNTRIES = [
    ("thailand", "thailand-bot-api", 8085),
    ("vietnam", "vietnam-bot-api", 8089),
    ("japan", "japan-bot-api", 8090),
    ("korea", "korea-bot-api", 8092),
    ("singapore", "singapore-bot-api", 8087),
    ("malaysia", "malaysia-bot-api", 8094),
    ("indonesia", "indonesia-bot-api", 8093),
    ("taiwan", "taiwan-bot-api", 8091),
    ("hong-kong", "hong-kong-bot-api", 8095),
    ("macau", "macau-bot-api", 8088),
    ("philippines", "philippines-bot-api", 8096),
    ("india", "india-bot-api", 8090),  # Note: may conflict with japan
    ("new-zealand", "new-zealand-bot-api", 8097),
    ("australia", "australia-bot-api", 8098),
    ("canada", "canada-bot-api", 8099),
    ("usa", "usa-bot-api", 8100),
    ("uk", "uk-bot-api", 8101),
    ("germany", "germany-bot-api", 8102),
    ("france", "france-bot-api", 8103),
    ("netherlands", "netherlands-bot-api", 8104),
    ("switzerland", "switzerland-bot-api", 8105),
    ("italy", "italy-bot-api", 8117),
    ("uae", "uae-bot-api", 8106),
    ("mexico", "mexico-bot-api", 8107),
    ("brasil", "brasil-bot-api", 8108),
    ("myanmar", "myanmar-bot-api", 8109),
    ("cambodia", "cambodia-bot-api", 8110),
    ("laos", "laos-bot-api", 8111),
    ("vietnam-hcm", "vietnam-hcm-bot-api", 8112),  # Maybe?
    ("china", "china-bot-api", 8113),
]

print("=" * 80)
print("V3 SERVICE STATUS AUDIT")
print("=" * 80)

# First: discover actual service files
result = subprocess.run(["bash", "-c", "ls /etc/systemd/system/*bot-api.service 2>/dev/null"],
                       capture_output=True, text=True)
actual_services = [os.path.basename(f.strip()) for f in result.stdout.strip().split('\n') if f.strip()]
print(f"\nDiscovered {len(actual_services)} bot-api services:")
for s in sorted(actual_services):
    print(f"  {s}")

# Also check for other patterns
result2 = subprocess.run(["bash", "-c", "ls /etc/systemd/system/*country*bot* 2>/dev/null; ls /etc/systemd/system/*bot* 2>/dev/null"],
                        capture_output=True, text=True)
all_services = set()
for line in (result.stdout + result2.stdout).strip().split('\n'):
    if line.strip() and 'bot' in line.lower():
        all_services.add(os.path.basename(line.strip()))

print(f"\nAll bot-related services: {len(all_services)}")

# Get service properties for each
services_info = []
for svc in sorted(all_services):
    result = subprocess.run(["systemctl", "show", svc,
        "-p", "ActiveState", "-p", "SubState", "-p", "MainPID",
        "-p", "ExecMainStartTimestamp", "-p", "ExecStart",
        "-p", "UnitFileState"],
        capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    
    main_pid = fields.get('MainPID', '0')
    active = fields.get('ActiveState', 'unknown')
    sub = fields.get('SubState', 'unknown')
    
    # Try to find port from ExecStart
    exec_start = fields.get('ExecStart', '')
    port_match = re.search(r'--port\s+(\d+)', exec_start)
    port = port_match.group(1) if port_match else '?'
    
    # Check if PID owns the port
    port_owner = '?'
    if main_pid != '0':
        result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if f':{port}' in line and f'pid={main_pid}' in line:
                port_owner = main_pid
                break
    
    services_info.append({
        'service': svc,
        'slug': svc.replace('-bot-api', '').replace('-service', ''),
        'active': active,
        'sub': sub,
        'pid': main_pid,
        'port': port,
        'start_time': fields.get('ExecMainStartTimestamp', ''),
        'enabled': fields.get('UnitFileState', ''),
        'port_owner_match': port_owner == main_pid
    })
    
    print(f"\n  {svc}:")
    print(f"    Active: {active}/{sub}, PID: {main_pid}, Port: {port}")
    print(f"    Started: {fields.get('ExecMainStartTimestamp', 'unknown')}")
    print(f"    Enabled: {fields.get('UnitFileState', 'unknown')}")
    print(f"    Port owner: {'✓' if port_owner == main_pid else '✗'}")

# Get all listening ports
print(f"\n--- All Listening Ports ---")
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if '127.0.0.1' in line or '0.0.0.0' in line:
        if line.strip():
            print(f"  {line.strip()[:120]}")

# Get DB stats
print(f"\n--- Database Stats ---")
import sqlite3
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
total = c.fetchone()[0]
c.execute("SELECT country, COUNT(*) FROM invoices GROUP BY country ORDER BY COUNT(*) DESC")
countries_in_db = c.fetchall()
print(f"  Total invoices: {total}")
print(f"  Country distribution:")
for country, count in countries_in_db:
    print(f"    {country}: {count} invoices")
c.execute("SELECT DISTINCT endpoint_tier FROM invoices")
tiers = [r[0] for r in c.fetchall()]
print(f"  Endpoint tiers: {tiers}")
c.execute("SELECT scheme, network, asset, COUNT(*) FROM invoices GROUP BY scheme, network, asset")
schemes = c.fetchall()
print(f"  Payment schemes:")
for s in schemes:
    print(f"    {s[0]}/{s[1]}/{s[2]}: {s[3]} invoices")
conn.close()

print(f"\n{'=' * 80}")
print("SERVICE STATUS AUDIT COMPLETE")
print(f"{'=' * 80}")
