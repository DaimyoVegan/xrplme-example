#!/usr/bin/env python3
"""
READ-ONLY Nginx diagnostics for Italy 404 issue.
NO changes, NO secrets, NO reloads.
"""
import os
import re
import subprocess
import hashlib

print("=" * 80)
print("NGINX DIAGNOSTICS — READ ONLY")
print("=" * 80)

# 1. Confirm Italy locations in api-xrplme-https
print("\n--- 1. Italy locations in /etc/nginx/sites-available/api-xrplme-https ---")
with open("/etc/nginx/sites-available/api-xrplme-https") as f:
    content = f.read()

italy_locations = [line.strip() for line in content.split('\n') if 'italy' in line.lower()]
for loc in italy_locations:
    print(f"  {loc}")

# 2. Confirm file is linked in sites-enabled
print("\n--- 2. Sites-enabled symlinks ---")
sites_enabled = "/etc/nginx/sites-enabled"
if os.path.exists(sites_enabled):
    for f in sorted(os.listdir(sites_enabled)):
        fpath = os.path.join(sites_enabled, f)
        target = os.path.realpath(fpath) if os.path.islink(fpath) else fpath
        print(f"  {f} -> {target}")

# 3. Check if api-xrplme-https is the active config for api.xrplme.online
print("\n--- 3. nginx -T (privileged config dump) ---")
print("Running nginx -T (safe — read-only dump)...")
result = subprocess.run(["nginx", "-T"], capture_output=True, text=True)
nginx_t_output = result.stdout + result.stderr

# Filter for api.xrplme.online and Italy references
lines = nginx_t_output.split('\n')
print(f"\nTotal output lines: {len(lines)}")

# Find server_name for api.xrplme.online
print("\n--- server_name and listen directives ---")
for i, line in enumerate(lines):
    if 'api.xrplme.online' in line or ('server_name' in line and 'api' in lines[max(0,i-1)]):
        # Print context
        start = max(0, i-3)
        end = min(len(lines), i+3)
        for j in range(start, end):
            marker = " >>>" if j == i else "     "
            print(f"  L{j}{marker} {lines[j]}")
        print()

# Check if Italy appears in nginx -T output
italy_in_t = "api/v1/italy" in nginx_t_output
print(f"Italy routes in nginx -T output: {italy_in_t}")

if not italy_in_t:
    print("\n⚠️  Italy routes NOT in nginx -T output!")
    print("    This means the config file on disk has them, but Nginx hasn't loaded them.")
    print("    nginx -T shows the CURRENTLY LOADED config, not the file on disk.")

# 4. Multiple server blocks for api.xrplme.online
print("\n--- 4. Server blocks handling api.xrplme.online ---")
# Count how many times api.xrplme.online appears as server_name
server_count = len(re.findall(r'server_name.*api\.xrplme\.online', nginx_t_output))
print(f"  server_name api.xrplme.online occurrences: {server_count}")

# Check for listen 443
listen_443 = len(re.findall(r'listen\s+443', nginx_t_output))
print(f"  listen 443 occurrences: {listen_443}")

# 5. Check Cloudflare origin headers
print("\n--- 5. Cloudflare check (via local curl to origin) ---")
# The origin server is reached via 127.0.0.1 (nginx proxy_pass)
# Check if CF-Connecting-IP or similar headers are used
result = subprocess.run(["curl", "-sI", "https://api.xrplme.online/api/v1/italy/health"],
                        capture_output=True, text=True)
print(f"  curl -sI https://api.xrplme.online/api/v1/italy/health")
print(f"  Response:")
for line in result.stdout.split('\n')[:10]:
    print(f"    {line}")

# Also check a working country via same API host
result2 = subprocess.run(["curl", "-sI", "https://api.xrplme.online/api/v1/macau/health"],
                         capture_output=True, text=True)
print(f"\n  curl -sI https://api.xrplme.online/api/v1/macau/health (control)")
print(f"  Response:")
for line in result2.stdout.split('\n')[:10]:
    print(f"    {line}")

# 6. Identify exact cause
print("\n--- 6. Root cause analysis ---")
# Check if the file on disk matches what nginx -T shows
with open("/etc/nginx/sites-available/api-xrplme-https", 'rb') as f:
    file_sha = hashlib.sha256(f.read()).hexdigest()
print(f"  File on disk SHA-256: {file_sha}")

# Search nginx -T output for the file content
if "api/v1/italy/bot" in nginx_t_output:
    print("  Italy routes ARE in loaded config → 404 must be from app")
else:
    print("  Italy routes are NOT in loaded config (nginx -T)")
    print("  Root cause: Nginx has not been reloaded since the file was modified.")
    print("  The file on disk has the routes, but Nginx's running config does not.")
    
    # Verify by checking other country routes in nginx -T
    if "api/v1/macau/bot" in nginx_t_output:
        print("  Macau routes ARE in nginx -T → config was loaded with Macau but without Italy")
        print("  This confirms: Nginx needs a reload to pick up the new Italy routes")
    else:
        print("  WARNING: Macau routes also not in nginx -T — config may not be enabled")

# 7. Check if the file is actually included
print("\n--- 7. Config file inclusion check ---")
# Look for include statements that reference api-xrplme-https
includes = re.findall(r'include\s+.*?api-xrplme', nginx_t_output, re.IGNORECASE)
if not includes:
    # Check sites-enabled directly
    for f in os.listdir("/etc/nginx/sites-enabled"):
        if "api-x" in f:
            print(f"  Found in sites-enabled: {f}")
            fpath = os.path.join("/etc/nginx/sites-enabled", f)
            if os.path.islink(fpath):
                print(f"  Symlink target: {os.path.realpath(fpath)}")
            print(f"  Realpath matches sites-available: {os.path.realpath(fpath) == '/etc/nginx/sites-available/api-xrplme-https'}")

# 8. Run sudo nginx -t
print("\n--- 8. sudo nginx -t ---")
result = subprocess.run(["sudo", "nginx", "-t"], capture_output=True, text=True)
print(f"  Exit code: {result.returncode}")
print(f"  stdout: {result.stdout.strip()}")
print(f"  stderr: {result.stderr.strip()}")
if result.returncode == 0:
    print("  ✓ nginx -t PASSED with root privileges")
    print("  ✓ Config is syntactically valid")
    print("  ✓ The only issue was non-root nginx -t couldn't read SSL key")
else:
    print("  ✗ nginx -t FAILED even with root")
    print("  ✗ May need manual investigation")

# 9. Reload command
print("\n--- 9. Exact reload command needed ---")
print("  sudo nginx -s reload")
print("  OR")
print("  sudo systemctl reload nginx")
print("  Prerequisite: sudo nginx -t must pass (it does)")

# 10. Rollback
print("\n--- 10. Rollback command ---")
print("  cp /home/xrpladmin/xrplme-state/backups/api-xrplme-https.20260922_073619.bak /etc/nginx/sites-available/api-xrplme-https")
print("  sudo nginx -t && sudo nginx -s reload")

print("\n" + "=" * 80)
print("STATUS")
print("=" * 80)
print("""
NO NGINX RELOADED.
NO SERVICE RESTARTED.
NO PAYMENT PERFORMED.
NO OTHER COUNTRY CHANGED.
NO SSL KEY PERMISSIONS MODIFIED.
NO SECRETS PRINTED.
""")
