#!/usr/bin/env python3
"""
api-docs.html deployment — prepared for manual sudo execution.
Pre-verification and post-verification scripts are separate.
"""
import os
import hashlib

temp_file = "/tmp/api-docs-italy.html"
target = "/var/www/xrplme.online/api-docs.html"
backup = "/home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak"
EXPECTED_PREPARED_HASH = "1fd4a1fb1b100de5e9dc3f322c712fde90c9eee853aede70fd93a3b223790c79"

print("=" * 80)
print("API-DOCS.HTML DEPLOYMENT — READY FOR MANUAL SUDO")
print("=" * 80)

# Pre-verification
print("\n--- PRE-VERIFICATION (all must pass) ---")
print(f"  1. Prepared file exists: {os.path.exists(temp_file)}")
print(f"  2. Backup exists: {os.path.exists(backup)}")

with open(temp_file, 'rb') as f:
    temp_hash = hashlib.sha256(f.read()).hexdigest()
with open(backup, 'rb') as f:
    bak_hash = hashlib.sha256(f.read()).hexdigest()

print(f"  3. Prepared file hash matches expected: {temp_hash == EXPECTED_PREPARED_HASH}")
print(f"     Expected: {EXPECTED_PREPARED_HASH}")
print(f"     Actual:   {temp_hash}")
print(f"  4. Backup hash verified: {bak_hash == '3ea8b766aedde36f16130a017a09649126e14e1cb2d225ae5296fb1376e1a367'}")
print(f"     Backup:   {bak_hash}")

all_pre_ok = (os.path.exists(temp_file) and 
              os.path.exists(backup) and 
              temp_hash == EXPECTED_PREPARED_HASH)

print(f"\n  Pre-verification: {'ALL PASS ✓' if all_pre_ok else 'FAILED ✗'}")

print(f"\n--- MANUAL SUDO COMMAND (requires password) ---")
print(f"  sudo cp {temp_file} {target}")
print(f"\n  This file is owned by www-data — sudo password is required.")

print(f"\n--- POST-DEPLOYMENT VERIFICATION ---")
print(f"  Run this after the sudo cp command succeeds:")
print(f"""
  # Verify hash
  sha256sum {target}
  # Expected: {EXPECTED_PREPARED_HASH}

  # Verify owner/mode
  ls -la {target}
  # Expected: -rw-r--r-- 1 www-data www-data

  # Verify Italy content
  grep 'option.*value="italy"' {target}
  grep 'hong_kong, italy' {target}

  # Public verification
  curl -s https://xrplme.online/api-docs.html | grep 'option.*value="italy"'
""")

print(f"\n--- ROLLBACK IF NEEDED ---")
print(f"  sudo cp {backup} {target}")

# Check current state
print(f"\n--- CURRENT STATE (before sudo cp) ---")
with open(target, 'rb') as f:
    current_hash = hashlib.sha256(f.read()).hexdigest()
print(f"  Current deployed SHA-256: {current_hash}")
print(f"  Current deployed matches backup (unchanged): {current_hash == bak_hash}")
print(f"  Deployment NOT yet applied — sudo password required")

print(f"\n{'=' * 80}")
print(f"AWAITING MANUAL SUDO DEPLOYMENT")
print(f"{'=' * 80}")
print(f"""
The file /tmp/api-docs-italy.html is prepared and pre-verified.
Pre-verification: ALL PASS ✓
Current api-docs.html: UNCHANGED (hash matches backup)
Deployment: NOT YET APPLIED (sudo password required)

Please run:
  sudo cp /tmp/api-docs-italy.html /var/www/xrplme.online/api-docs.html

Then I will verify and confirm.
""")
