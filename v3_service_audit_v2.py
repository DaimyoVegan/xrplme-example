#!/usr/bin/env python3
"""V3 AUDIT — Service Status Only (fixed import)."""
import subprocess
import os
import re
import json
import time

print("=" * 80)
print("V3 SERVICE STATUS AUDIT — ALL 30 COUNTRIES")
print("=" * 80)

result = subprocess.run(["bash", "-c", "ls /etc/systemd/system/*bot-api.service 2>/dev/null"],
                       capture_output=True, text=True)
active_services = [os.path.basename(f.strip()) for f in result.stdout.strip().split('\n') 
                   if f.strip() and 'bak' not in f]
print(f"\nActive (non-backup) services: {len(active_services)}")

# Get all listening ports first
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
port_pids = {}
for line in result.stdout.split('\n'):
    m = re.search(r'127\.0\.0\.1:(\d+).*pid=(\d+)', line)
    if m:
        port_pids[m.group(1)] = m.group(2)

categories = {"LIVE": [], "DOWN": [], "ROUTE_FAILED": [], "RESTART_FAILED": []}

print(f"\n{'Service':<35} {'Slug':<20} {'Status':<12} {'PID':<8} {'Port':<6} {'Health':<8} {'Enabled':<10}")
print("-" * 110)

for svc in sorted(active_services):
    result = subprocess.run(["systemctl", "show", svc,
        "-p", "ActiveState", "-p", "SubState", "-p", "MainPID",
        "-p", "ExecStart", "-p", "UnitFileState", "-p", "ExecMainStartTimestamp"],
        capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    
    main_pid = fields.get('MainPID', '0')
    active = fields.get('ActiveState', 'unknown')
    sub = fields.get('SubState', 'unknown')
    enabled = fields.get('UnitFileState', 'unknown')
    exec_start = fields.get('ExecStart', '')
    port_match = re.search(r'--port\s+(\d+)', exec_start)
    port = port_match.group(1) if port_match else '?'
    
    slug = svc.replace('-bot-api.service', '')
    pid_str = main_pid
    
    # Check health
    health_ok = False
    http_code = '?'
    if port != '?' and int(main_pid) > 0:
        result = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                                 f"http://127.0.0.1:{port}/health"],
                               capture_output=True, text=True, timeout=3)
        http_code = result.stdout
        health_ok = result.stdout == "200"
    
    # Determine classification
    if active == "active" and sub == "running" and health_ok:
        status = "LIVE"
    elif active == "active" and sub == "running" and not health_ok:
        status = "DOWN"
    elif active == "inactive":
        status = "RESTART_FAILED"
    else:
        status = "UNKNOWN"
    
    categories[status].append(f"{slug} (port {port}, PID {pid_str})")
    
    print(f"{svc:<35} {slug:<20} {status:<12} {pid_str:<8} {port:<6} {http_code:<8} {enabled:<10}")

print(f"\n--- Classification Summary ---")
for cat in ["LIVE", "DOWN", "RESTART_FAILED", "UNKNOWN"]:
    count = len(categories[cat])
    print(f"  {cat}: {count}")
    for s in categories[cat]:
        print(f"    {s}")

# Verify port ownership matches PID
print(f"\n--- Port-to-PID Ownership Check ---")
mismatches = 0
for svc in sorted(active_services):
    result = subprocess.run(["systemctl", "show", svc, "-p", "MainPID", "-p", "ExecStart"],
                           capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    main_pid = fields.get('MainPID', '0')
    exec_start = fields.get('ExecStart', '')
    port_match = re.search(r'--port\s+(\d+)', exec_start)
    port = port_match.group(1) if port_match else '?'
    
    if port != '?' and int(main_pid) > 0:
        actual_pid = port_pids.get(port, 'none')
        if actual_pid != main_pid:
            print(f"  MISMATCH: {svc} — systemd PID={main_pid}, port {port} owner={actual_pid}")
            mismatches += 1

print(f"\n  Total mismatches: {mismatches}")

print(f"\n{'=' * 80}")
print("SERVICE STATUS AUDIT COMPLETE")
print(f"{'=' * 80}")
