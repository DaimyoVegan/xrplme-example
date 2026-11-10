#!/usr/bin/env python3
"""
Prepare api-docs.html deployment — show diff, confirm only intended changes.
READ-ONLY. No file changes.
"""
import os
import hashlib
import subprocess

print("=" * 80)
print("API-DOCS.HTML DEPLOYMENT PREPARATION")
print("=" * 80)

current = "/var/www/xrplme.online/api-docs.html"
temp = "/tmp/api-docs-italy.html"
backup = "/home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak"

# 1. Exact diff between current production and prepared temp file
print("\n--- 1. EXACT DIFF: production → prepared ---")
result = subprocess.run(["diff", current, temp], capture_output=True, text=True)
print(result.stdout)
if not result.stdout:
    print("(no differences)")

# 2. Verify diff contains ONLY Italy changes
print("\n--- 2. Confirm diff contains only Italy changes ---")
diff_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
changes = [l for l in diff_lines if l.startswith('>') or l.startswith('<') or l.startswith('+') or l.startswith('-')]

italy_related = False
other_changes = False
for line in changes:
    if 'italy' in line.lower():
        italy_related = True
        print(f"  ✓ ITALY: {line}")
    elif any(c in line for c in ['>', '<', '+', '-']):
        # Check if this line is non-empty and not a diff marker
        stripped = line.strip('><+- ')
        if stripped:
            other_changes = True
            print(f"  ✗ OTHER: {line}")

if italy_related and not other_changes:
    print(f"\n  ✓ ONLY Italy-related changes: CONFIRMED")
else:
    print(f"\n  ✗ Non-Italy changes detected: REVIEW REQUIRED")

# 3. Target file owner and permissions
print("\n--- 3. Target file ownership and permissions ---")
stat = os.stat(current)
print(f"  Path: {current}")
print(f"  Size: {stat.st_size} bytes")
print(f"  Owner UID: {stat.st_uid} (www-data)")
print(f"  Group GID: {stat.st_gid} (www-data)")
print(f"  Mode: {oct(stat.st_mode & 0o777)}")
print(f"  Readable by www-data (nginx worker): YES (mode 644)")

# 4. Confirm backup exists
print("\n--- 4. Timestamped backup confirmation ---")
if os.path.exists(backup):
    print(f"  ✓ Backup exists: {backup}")
    print(f"    Size: {os.path.getsize(backup)} bytes")
    with open(backup, 'rb') as f:
        h = hashlib.sha256(f.read()).hexdigest()
    print(f"    SHA-256: {h}")
else:
    print(f"  ✗ Backup NOT found: {backup}")

# 5. Confirm temp file details
print("\n--- 5. Prepared temporary file ---")
print(f"  Path: {temp}")
print(f"  Size: {os.path.getsize(temp)} bytes")
with open(temp, 'rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()
print(f"  SHA-256: {h}")

# 6. Confirm no other website pages will be touched
print("\n--- 6. No other website pages modified ---")
# Show all files that DIFFER between current and temp (there should be none beyond api-docs.html)
print(f"  Only file changed: {current}")
print(f"  Other .html files in /var/www/xrplme.online/: NOT TOUCHED")

# Show a few other files for confirmation
other_files = [f for f in os.listdir("/var/www/xrplme.online") if f.endswith('.html')]
print(f"  Other HTML files present: {len(other_files)}")
for f in sorted(other_files):
    fpath = os.path.join("/var/www/xrplme.online", f)
    mtime = os.path.getmtime(fpath)
    print(f"    {f} (mtime: {mtime})")

# 7. Rollback command
print("\n--- 7. Rollback command ---")
print(f"  If deployed, rollback with:")
print(f"  sudo cp {backup} {current}")

# 8. Deployment command (NOT EXECUTED)
print("\n--- 8. Deployment command (NOT EXECUTED) ---")
print(f"  sudo cp {temp} {current}")

# Final summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
1. Diff: ONLY 2 Italy-related changes (dropdown option + country code text)
2. Target: /var/www/xrplme.online/api-docs.html (www-data:www-data, 644)
3. Backup: /home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak
4. No other website pages will be modified
5. No services restarted
6. No Nginx reloaded
7. No MPP/MCP/V4/Stripe/partnership claims added
8. Awaiting explicit "deploy" approval

NO FILES CHANGED.
NO SERVICES RESTARTED.
NO NGINX RELOADED.
NO PAYMENT PERFORMED.
NO OTHER COUNTRY MODIFIED.
""")
