#!/usr/bin/env python3
"""
READ-ONLY AUDIT: ITALY PROCESS OWNERSHIP
NO kills, NO restarts, NO edits, NO nginx, NO db writes, NO payments, NO secrets
"""
import os
import re
import subprocess
import sqlite3
import hashlib

print("=" * 80)
print("READ-ONLY PROCESS AUDIT: ITALY")
print("=" * 80)

# 1. PORT AND PROCESS
print("\n--- 1. Port and Process ---")

# Find PID owning port 8117
result = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True)
port_pids = []
for line in result.stdout.split('\n'):
    if ':8117' in line:
        print(f"  ss output: {line.strip()[:120]}")
        # Extract PID
        m = re.search(r'pid=(\d+)', line)
        if m:
            port_pids.append(m.group(1))

# Alternative: use lsof
result = subprocess.run(["lsof", "-i", ":8117"], capture_output=True, text=True)
if result.stdout:
    print(f"  lsof output:")
    for line in result.stdout.split('\n'):
        if line.strip():
            print(f"    {line.strip()[:120]}")
            m = re.search(r'(\d+)', line.split()[-1] if line.split()[-1].isdigit() else '')
            # Try to extract PID from lsof format
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                if parts[1] not in port_pids:
                    port_pids.append(parts[1])

if port_pids:
    for pid in set(port_pids):
        pid = str(pid)
        print(f"\n  PID {pid} details:")
        # Command line
        try:
            with open(f"/proc/{pid}/cmdline", 'r') as f:
                cmdline = f.read().replace('\x00', ' ').strip()
            print(f"    cmdline: {cmdline[:150]}")
        except:
            print(f"    cmdline: (not available)")
        
        # Parent PID
        try:
            with open(f"/proc/{pid}/stat", 'r') as f:
                stat = f.read().split()
            ppid = stat[3]
            print(f"    Parent PID (PPID): {ppid}")
        except:
            print(f"    PPID: (not available)")
        
        # Start time
        try:
            with open(f"/proc/{pid}/stat", 'r') as f:
                stat = f.read().split()
            # field 22 is starttime in clock ticks
            starttime_ticks = int(stat[21])
            import time
            clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            starttime_sec = starttime_ticks / clk_tck
            boot_time = 0
            try:
                with open("/proc/stat", 'r') as f:
                    for line in f:
                        if line.startswith('btime'):
                            boot_time = int(line.split()[1])
                            break
            except:
                pass
            start_epoch = boot_time + starttime_sec
            from datetime import datetime
            start_human = datetime.fromtimestamp(start_epoch).isoformat()
            print(f"    Start time: {start_human} (epoch: {start_epoch:.0f})")
        except Exception as e:
            print(f"    Start time: (error: {e})")
        
        # Working directory
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
            print(f"    Working dir: {cwd}")
        except:
            print(f"    Working dir: (not available)")
        
        # Effective user
        try:
            with open(f"/proc/{pid}/status", 'r') as f:
                for line in f:
                    if line.startswith('Uid:'):
                        print(f"    Uid line: {line.strip()}")
                    if line.startswith('Gid:'):
                        print(f"    Gid line: {line.strip()}")
        except:
            print(f"    Uid/Gid: (not available)")
        
        # Python executable
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
            print(f"    Executable: {exe}")
        except:
            print(f"    Executable: (not available)")
        
        # Imported modules (check if sqlite_invoice_store is loaded)
        try:
            result = subprocess.run(["grep", "-i", "sqlite_invoice_store\|italy_bot_server", 
                                   f"/proc/{pid}/maps"], capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[:5]:  # Show first 5 matches
                    print(f"    Maps: {line[:120]}")
                if len(lines) > 5:
                    print(f"    ... and {len(lines)-5} more")
        except:
            print(f"    Maps: (not available)")
else:
    print("  No process found owning port 8117")
    # Try fuser
    result = subprocess.run(["fuser", "8117/tcp"], capture_output=True, text=True)
    print(f"  fuser output: {result.stdout} {result.stderr}")

# 2. SYSTEMD STATE
print("\n--- 2. Systemd State ---")
result = subprocess.run(["systemctl", "show", "italy-bot-api.service",
    "-p", "ActiveState", "-p", "SubState", "-p", "MainPID", "-p", "ExecMainPID",
    "-p", "ExecStart", "-p", "FragmentPath", "-p", "WorkingDirectory",
    "-p", "User", "-p", "Restart", "-p", "EnvironmentFiles", "-p", "ExecMainStartTimestamp",
    "-p", "ExecMainExitTimestamp"], capture_output=True, text=True)
print(f"  systemctl show output:")
for line in result.stdout.strip().split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        print(f"    {k}: {v}")

# Also get status
result = subprocess.run(["systemctl", "status", "italy-bot-api.service", "--no-pager"],
                       capture_output=True, text=True)
print(f"\n  systemctl status:")
for line in result.stdout.strip().split('\n'):
    print(f"    {line.rstrip()[:120]}")

# 3. DUPLICATE PROCESS CHECK
print("\n--- 3. Duplicate Process Check ---")
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
all_procs = result.stdout

italy_procs = [line for line in all_procs.split('\n') 
               if 'italy_bot_server' in line and 'grep' not in line]
all_italy_procs = [line for line in all_procs.split('\n') 
                   if 'italy' in line.lower() and 'grep' not in line and 'bash' not in line]

print(f"  Italy bot server processes: {len(italy_procs)}")
for p in italy_procs:
    parts = p.split()
    print(f"    PID={parts[1]} USER={parts[0]} CMD={p.strip()[:120]}")

print(f"\n  All processes mentioning 'italy': {len(all_italy_procs)}")
for p in all_italy_procs:
    print(f"    {p.strip()[:120]}")

# Check port ownership
print(f"\n  Port 8117 ownership:")
if port_pids:
    for pid in set(port_pids):
        pid = str(pid)
        print(f"    Port 8117 owned by PID {pid}")
        # Check if this PID is in systemd MainPID
        systemd_pid = result.stdout.split('\n')[0]  # Not reliable, use the show output
else:
    print(f"    No PID found for port 8117")

# 4. BOOT AND FAILURE BEHAVIOR
print("\n--- 4. Boot and Failure Behavior ---")
result = subprocess.run(["systemctl", "is-enabled", "italy-bot-api.service"],
                       capture_output=True, text=True)
print(f"  is-enabled: {result.stdout.strip()}")

result = subprocess.run(["systemctl", "show", "italy-bot-api.service",
    "-p", "Restart", "-p", "RestartSec", "-p", "StartLimitBurst", "-p", "StartLimitIntervalSec"],
    capture_output=True, text=True)
for line in result.stdout.strip().split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        print(f"  {k}: {v}")

# Check if service file has WantedBy
result = subprocess.run(["systemctl", "show", "italy-bot-api.service", "-p", "FragmentPath", "-p", "UnitFileState"],
                       capture_output=True, text=True)
print(f"\n  Unit file state:")
for line in result.stdout.strip().split('\n'):
    if '=' in line:
        k, v = line.split('=', 1)
        print(f"    {k}: {v}")

# Check for symlinks (enabled)
result = subprocess.run(["ls", "-la", "/etc/systemd/system/multi-user.target.wants/italy-bot-api.service"],
                       capture_output=True, text=True)
print(f"\n  Enabled symlink: {result.stdout.strip()}" if result.stdout.strip() else "  Enabled symlink: (not found)")

# 5. SAFE RECONCILIATION PLAN
print("\n--- 5. Safe Reconciliation Plan ---")

# Determine the port-owning PID
port_pid = None
if port_pids:
    port_pid = set(port_pids)

# Get systemd MainPID
systemd_main_pid = None
result = subprocess.run(["systemctl", "show", "italy-bot-api.service", "-p", "MainPID"],
                       capture_output=True, text=True)
if '=' in result.stdout:
    systemd_main_pid = result.stdout.strip().split('=')[1]

print(f"  systemd MainPID: {systemd_main_pid}")
print(f"  Port 8117 owner PID: {port_pid}")

if port_pid:
    port_pid_str = str(list(port_pid)[0]) if len(port_pid) == 1 else str(port_pid)
    systemd_pid_str = str(systemd_main_pid)
    
    if port_pid and systemd_main_pid and port_pid_str != systemd_pid_str:
        print(f"\n  ⚠️  MISMATCH: systemd PID ({systemd_pid_str}) != port owner ({port_pid_str})")
        print(f"  The port is owned by a manually started process, NOT by systemd")
        
        # Get parent PID of the port owner
        if list(port_pid)[0]:
            ppid = None
            try:
                with open(f"/proc/{list(port_pid)[0]}/stat", 'r') as f:
                    stat = f.read().split()
                ppid = stat[3]
            except:
                pass
            
            print(f"\n  Port owner parent PID: {ppid}")
            if ppid == '0' or ppid == '1':
                print(f"  Parent is init/systemd — process was orphaned (PPID 1)")
                print(f"  This means the process was started via setsid/nohup and detached")
            elif ppid:
                # Check if parent is our SSH session
                try:
                    with open(f"/proc/{ppid}/cmdline", 'r') as f:
                        parent_cmd = f.read().replace('\x00', ' ').strip()
                    print(f"  Parent cmdline: {parent_cmd[:100]}")
                except:
                    print(f"  Parent cmdline: (not available)")
    elif port_pid and systemd_main_pid and port_pid_str == systemd_pid_str:
        print(f"\n  ✓ systemd and port owner are the SAME PID — service is properly managed")
    else:
        print(f"\n  ? Cannot determine — systemd PID: {systemd_main_pid}, port PID: {port_pid}")

print(f"\n  Reconciliation Options:")
print(f"    A. Stop manual process, start systemd service:")
print(f"       Command: pkill -f 'italy_bot_server:app'; sudo systemctl start italy-bot-api")
print(f"       Downtime: ~2-5 seconds (process kill + service start)")
print(f"       Risk: Port collision if kill fails before start")
print(f"       Rollback: If service fails to start, restart manual process")
print(f"       Health: curl http://127.0.0.1:8117/health → 200")
print(f"       402: curl -X POST http://127.0.0.1:8117/api/v1/italy/bot → 402")
print(f"")
print(f"    B. Update systemd unit with manual start as fallback:")
print(f"       Command: (requires editing systemd unit — blocked by user)")
print(f"")
print(f"    C. Leave manual process temporarily with monitoring:")
print(f"       Command: No action — monitor via curl health checks")
print(f"       Risk: Process dies on SSH session disconnect or reboot")
print(f"       Not sustainable for production")
print(f"")
print(f"    D. Recommended: A (stop manual, start systemd)")
print(f"       1. Verify manual process is healthy")
print(f"       2. Kill manual process (pkill -f 'italy_bot_server:app')")
print(f"       3. Wait for port release (1-2 seconds)")
print(f"       4. Start systemd: sudo systemctl start italy-bot-api")
print(f"       5. Verify: systemctl status italy-bot-api (active=active)")
print(f"       6. Verify: curl http://127.0.0.1:8117/health → 200")
print(f"       7. Verify: curl -X POST .../italy/bot → 402")
print(f"       8. Rollback: If step 4 fails, restart manual process:")
print(f"          cd /opt/xrplme/thoughts/api && PYTHONPATH=/opt/xrplme/thoughts/api \\")
print(f"          /home/xrpladmin/thailand_bot_venv/bin/python -m uvicorn italy_bot_server:app --host 127.0.0.1 --port 8117 &")
print(f"       9. Only Italy affected — no other service touched")

print(f"\n{'=' * 80}")
print("AUDIT COMPLETE")
print(f"{'=' * 80}")
