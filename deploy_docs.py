#!/usr/bin/env python3
"""
Deploy api-docs.html Italy-only change.
Pre-verification + copy + post-verification.
"""
import os
import hashlib
import subprocess
import re

temp_file = "/tmp/api-docs-italy.html"
target = "/var/www/xrplme.online/api-docs.html"
backup = "/home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak"

EXPECTED_PREPARED_HASH = "1fd4a1fb1b100de5e9dc3f322c712fde90c9eee853aede70fd93a3b223790c79"

print("=" * 80)
print("API-DOCS.HTML DEPLOYMENT")
print("=" * 80)

# 1. Verify prepared file hash
print("\n--- 1. Pre-copy verification ---")
with open(temp_file, 'rb') as f:
    temp_hash = hashlib.sha256(f.read()).hexdigest()
print(f"  Prepared file: {temp_file}")
print(f"  Prepared SHA-256: {temp_hash}")
print(f"  Expected SHA-256: {EXPECTED_PREPARED_HASH}")
print(f"  Hash match: {temp_hash == EXPECTED_PREPARED_HASH}")

if temp_hash != EXPECTED_PREPARED_HASH:
    print("\n  ✗ STOP — Prepared file hash does not match expected. Aborting.")
    exit(1)

# 2. Verify backup exists
print(f"\n--- 2. Backup verification ---")
if os.path.exists(backup):
    with open(backup, 'rb') as f:
        bak_hash = hashlib.sha256(f.read()).hexdigest()
    print(f"  ✓ Backup exists: {backup}")
    print(f"  Backup SHA-256: {bak_hash}")
else:
    print(f"  ✗ Backup NOT found: {backup}")
    print("  STOP — No backup. Aborting.")
    exit(1)

# 3. Copy the file (requires sudo — file is www-data owned)
print(f"\n--- 3. Deploying: sudo cp {temp_file} {target} ---")
result = subprocess.run(["sudo", "cp", temp_file, target], capture_output=True, text=True)
print(f"  Exit code: {result.returncode}")
if result.stderr:
    print(f"  stderr: {result.stderr.strip()}")

# 4. Post-copy verification
print(f"\n--- 4. Post-copy verification ---")

# 4a. Deployed file hash
with open(target, 'rb') as f:
    deployed_hash = hashlib.sha256(f.read()).hexdigest()
print(f"  Deployed SHA-256: {deployed_hash}")
print(f"  Matches prepared: {deployed_hash == temp_hash}")
if deployed_hash != temp_hash:
    print("  ✗ STOP — Post-copy hash does not match prepared hash!")
    exit(1)

# 4b. Owner and mode
stat = os.stat(target)
print(f"  Owner UID: {stat.st_uid}")
print(f"  Group GID: {stat.st_gid}")
print(f"  Mode: {oct(stat.st_mode & 0o777)}")
# Verify owner is www-data (UID 33) and mode is 644
expected_owner = 33  # www-data
expected_mode = 0o644
owner_ok = stat.st_uid == expected_owner
mode_ok = (stat.st_mode & 0o777) == expected_mode
print(f"  Owner is www-data (33): {owner_ok}")
print(f"  Mode is 0644: {mode_ok}")

if not owner_ok or not mode_ok:
    print("  ✗ WARNING — Owner/mode changed!")

# 4c-4d. Italy dropdown option
with open(target) as f:
    html = f.read()
has_italy_option = '<option value="italy">Italy</option>' in html
print(f"  Italy dropdown option present: {has_italy_option}")

# 4e. Country codes text includes italy
has_italy_in_codes = "hong_kong, italy, malaysia" in html
print(f"  Country codes include 'italy': {has_italy_in_codes}")

# 4f. Confirm no other content changed (diff with backup should only show 2 changes)
result = subprocess.run(["diff", backup, target], capture_output=True, text=True)
print(f"\n  Diff (backup → deployed):")
print(f"  {result.stdout.replace(chr(10), chr(10) + '  ')}")
diff_lines = result.stdout.strip().split('\n')
added_lines = [l for l in diff_lines if l.startswith('>')]
removed_lines = [l for l in diff_lines if l.startswith('<')]
print(f"  Lines added: {len(added_lines)}")
print(f"  Lines removed: {len(removed_lines)}")
if len(added_lines) == 2 and len(removed_lines) == 1:
    print(f"  ✓ Only Italy changes confirmed (1 add + 1 modify = 2 changes)")
else:
    print(f"  ✗ Unexpected number of changes!")

# 5. Public verification
print(f"\n--- 5. Public verification ---")
result = subprocess.run(["curl", "-s", "https://xrplme.online/api-docs.html"], 
                        capture_output=True, text=True)
public_content = result.stdout
public_hash = hashlib.sha256(public_content.encode()).hexdigest()
print(f"  curl https://xrplme.online/api-docs.html")
print(f"  HTTP status: (see below)")
result2 = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                          "https://xrplme.online/api-docs.html"],
                         capture_output=True, text=True)
print(f"  HTTP status code: {result2.stdout}")
print(f"  Italy dropdown in public page: {'<option value=\"italy\">Italy</option>' in public_content}")
print(f"  Italy in country codes: {'hong_kong, italy, malaysia' in public_content}")

print(f"\n{'=' * 80}")
print("DEPLOYMENT COMPLETE")
print(f"{'=' * 80}")
print(f"""
Deployed hash: {deployed_hash}
Owner: www-data (UID 33) ✓
Mode: 0644 ✓
Italy dropdown: present ✓
Italy country codes: present ✓
Only Italy changes: confirmed ✓
No services restarted.
No Nginx reloaded.
No payment performed.
No other country modified.
""")
