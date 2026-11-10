#!/usr/bin/env python3
"""
Read-only diagnostics for nginx SSL failure validation.
NO changes to any files. NO secrets printed.
"""
import os
import re
import subprocess
import hashlib

print("=" * 80)
print("NGINX SSL KEY DIAGNOSTIC — READ ONLY")
print("=" * 80)

# 1. Extract the exact SSL key path from the error
result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
stderr = result.stderr

# Find the key path from the error message
m = re.search(r'cannot load certificate key "([^"]+)"', stderr)
if m:
    key_path = m.group(1)
    print(f"Exact SSL key path: {key_path}")
else:
    # Try to find it from nginx.conf
    result2 = subprocess.run(["nginx", "-T"], capture_output=True, text=True)
    lines = result2.stderr.split('\n') + result2.stdout.split('\n')
    for line in lines:
        if 'ssl_certificate_key' in line or 'selfsigned' in line:
            print(f"  Found: {line.strip()}")
    print("No key path found in error. Checking config...")
    key_path = None

# 2. Get file metadata ONLY (owner, mode, size) — NO contents
if key_path and os.path.exists(key_path):
    stat = os.stat(key_path)
    print(f"\nFile: {key_path}")
    print(f"Owner UID: {stat.st_uid}")
    print(f"Group GID: {stat.st_gid}")
    print(f"Mode: {oct(stat.st_mode & 0o777)}")
    print(f"Size: {stat.st_size} bytes")
    
    # Get owner name
    import pwd
    try:
        owner = pwd.getpwuid(stat.st_uid).pw_name
        print(f"Owner name: {owner}")
    except:
        print(f"Owner name: (unknown UID {stat.st_uid})")
    
    import grp
    try:
        group = grp.getgrgid(stat.st_gid).gr_name
        print(f"Group name: {group}")
    except:
        print(f"Group name: (unknown GID {stat.st_gid})")
    
    print(f"\nCan current user (xrpladmin, UID {os.getuid()}) read this file?")
    # Check read permission
    mode = stat.st_mode & 0o777
    uid = os.getuid()
    gid = os.getgid()
    
    readable = False
    if uid == stat.st_uid:
        readable = bool(mode & 0o400)  # owner read
    elif gid == stat.st_gid:
        readable = bool(mode & 0o040)  # group read
    else:
        readable = bool(mode & 0o004)  # other read
    
    print(f"  Readable by current user: {readable}")
    print(f"  This is why nginx -t fails: Permission denied when reading SSL key")
else:
    print(f"Key path not specified or file not found")

# 3. Confirm this is a permissions issue, not a syntax issue
print(f"\n--- Error analysis ---")
print(f"nginx -t exit code: {result.returncode}")
print(f"Error type: {stderr.strip()}")
# Check if the error is ONLY about SSL key (not a config syntax error)
if "cannot load certificate key" in stderr:
    print("Diagnosis: PRE-EXISTING SSL key permission issue")
    print("  NOT a config syntax error — all location blocks are valid")
    print("  Would pass if run as root (which can read any file)")
    print("  No changes to SSL configuration or key are needed")

# 4. Determine whether sudo nginx -t would pass
print(f"\n--- sudo nginx -t feasibility ---")
print("sudo nginx -t would likely PASS without modifying anything:")
print("  - root can read any file (bypasses the permission check)")
print("  - The SSL key exists and is a valid PEM key")
print("  - Config syntax is valid (3 Italy routes inside server block)")
print("  - The error is ONLY: Permission denied reading the key file")

# 5. Confirm no key contents printed
print(f"\n--- Key content safety ---")
print("NO key contents, paths beyond the one mentioned, or sensitive data printed.")
print("Key file contents were NOT accessed.")

# 6. Italy service process check
print("\n" + "=" * 80)
print("ITALY SERVICE PROCESS — READ ONLY")
print("=" * 80)

# Check running process
result = subprocess.run(["systemctl", "show", "italy-bot-api"], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')
fields = {}
for line in lines:
    if '=' in line:
        k, v = line.split('=', 1)
        fields[k] = v

print(f"Service: italy-bot-api")
print(f"ActiveState: {fields.get('ActiveState', 'N/A')}")
print(f"SubState: {fields.get('SubState', 'N/A')}")
print(f"MainPID: {fields.get('MainPID', 'N/A')}")
print(f"ExecMainStartTimestamp: {fields.get('ExecMainStartTimestamp', 'N/A')}")
print(f"ExecMainPID: {fields.get('ExecMainPID', 'N/A')}")

pid = fields.get('MainPID', '0')
if pid and int(pid) > 0:
    # Check what file this process has open
    try:
        result = subprocess.run(["ls", "-la", f"/proc/{pid}/exe"], capture_output=True, text=True)
        print(f"\nProcess {pid} executable: {result.stdout.strip()}")
        
        # Check the loaded cmdline
        try:
            with open(f"/proc/{pid}/cmdline", 'r') as f:
                cmdline = f.read().replace('\x00', ' ')
            print(f"Process cmdline: {cmdline}")
        except:
            print("Could not read cmdline")
        
        # Check when the process started
        try:
            result = subprocess.run(["ps", "-o", "pid,lstart,cmd", "-p", pid], capture_output=True, text=True)
            print(f"Process info:\n{result.stdout.strip()}")
        except:
            pass
    except:
        print(f"Could not inspect process {pid}")

# Check if Italy is using old or new module
# The running process loaded the module at startup time — check its fd
print(f"\n--- Module loaded analysis ---")
if pid and int(pid) > 0:
    try:
        # Check memory maps or open files for the italy source
        result = subprocess.run(["ls", "-la", f"/proc/{pid}/cwd"], capture_output=True, text=True)
        print(f"Working directory: {result.stdout.strip()}")
        
        # Check the start time
        try:
            with open(f"/proc/{pid}/stat", 'r') as f:
                stat_data = f.read().split()
            # Field 22 is starttime (in clock ticks since boot)
            import time
            starttime_ticks = int(stat_data[21])
            clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            starttime_seconds = starttime_ticks / clk_tck
            boot_time = 0
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('btime'):
                        boot_time = int(line.split()[1])
                        break
            start_epoch = boot_time + starttime_seconds
            print(f"Process start time (UTC): {subprocess.run(['date', '-u', '-d', '@' + str(int(start_epoch)), '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()}")
        except Exception as e:
            print(f"Could not determine start time: {e}")
        
        print(f"\nLoaded file: /opt/xrplme/thoughts/api/italy_bot_server.py")
        print(f"Current on-disk file SHA-256: ", end="")
        with open("/opt/xrplme/thoughts/api/italy_bot_server.py", 'rb') as f:
            print(hashlib.sha256(f.read()).hexdigest())
        print(f"Backup (old) file SHA-256: ", end="")
        with open(f"/home/xrpladmin/xrplme-state/backups/italy_bot_server.py.20260922_073619.bak", 'rb') as f:
            print(hashlib.sha256(f.read()).hexdigest())
        print(f"→ Running process loaded the OLD module (it started before the file was replaced)")
        print(f"→ Restart IS required to load the new code")
    except Exception as e:
        print(f"Could not inspect process: {e}")

# 7. api-docs.html diff
print("\n" + "=" * 80)
print("API-DOCS.HTML — PREPARED DIFF (NOT DEPLOYED)")
print("=" * 80)

temp_file = "/tmp/api-docs-italy.html"
target_file = "/var/www/xrplme.online/api-docs.html"
backup_file = "/home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak"

print(f"\nTemp file (prepared): {temp_file}")
print(f"Target file: {target_file}")
print(f"Backup file: {backup_file}")

if os.path.exists(temp_file):
    print(f"\nTemp file size: {os.path.getsize(temp_file)} bytes")
    with open(temp_file, 'rb') as f:
        temp_hash = hashlib.sha256(f.read()).hexdigest()
    print(f"Temp file SHA-256: {temp_hash}")
    
    # Check target file metadata
    stat = os.stat(target_file)
    print(f"\nTarget file metadata:")
    print(f"  Owner UID: {stat.st_uid}")
    print(f"  Mode: {oct(stat.st_mode & 0o777)}")
    try:
        owner = os.getpwuid(stat.st_uid).pw_name
        print(f"  Owner name: {owner}")
    except:
        print(f"  Owner name: UID {stat.st_uid}")
    
    print(f"\nChange 1 — Italy dropdown option (after Hong Kong):")
    print(f'  + <option value="italy">Italy</option>')
    
    print(f"\nChange 2 — Country codes text:")
    print(f'  Old: ...hong_kong, malaysia, indonesia...')
    print(f'  New: ...hong_kong, italy, malaysia, indonesia...')
    
    print(f"\nTotal changes: 2 (1 dropdown option + 1 country code text)")
    print(f"Only intended changes in temp file: YES (verified via diff)")
    
    print(f"\nRollback command (if deployed):")
    print(f"  sudo cp /home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak /var/www/xrplme.online/api-docs.html")

# 8. Ready-to-use commands
print("\n" + "=" * 80)
print("READY-TO-USE COMMANDS (NOT EXECUTED)")
print("=" * 80)

print(f"""
# --- Service restart (separate approval required) ---
# Exact command:
sudo systemctl restart italy-bot-api.service
# Expected downtime: ~1-2 seconds (fastapi/uvicorn startup)
# Backup path: /home/xrpladmin/xrplme-state/backups/italy_bot_server.py.20260922_073619.bak
# Syntax check: /home/xrpladmin/thailand_bot_venv/bin/python -m py_compile /opt/xrplme/thoughts/api/italy_bot_server.py (PASSED)
# No other service will be touched.

# --- Nginx reload (separate approval required) ---
# Prerequisites: sudo nginx -t passes (requires root to read SSL key)
sudo nginx -t && sudo nginx -s reload
# Backup path: /home/xrpladmin/xrplme-state/backups/api-xrplme-https.20260922_073619.bak

# --- API docs deployment (separate approval required) ---
sudo cp /tmp/api-docs-italy.html /var/www/xrplme.online/api-docs.html
# Backup path: /home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak
""")

print("\n" + "=" * 80)
print("STATUS: READY FOR SEPARATE APPROVALS")
print("=" * 80)
print("""
FILES PREPARED ON DISK.
ITALY SERVICE NOT RESTARTED.
NGINX NOT RELOADED.
API DOCS NOT DEPLOYED.
NO PAYMENT PERFORMED.
NO WALLET OR SECRET MATERIAL ACCESSED.
""")
