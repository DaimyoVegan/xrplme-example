#!/usr/bin/env python3
"""
Step 4: Add Italy to api-docs.html dropdown and country codes text.
"""
import os
import hashlib

docs_file = "/var/www/xrplme.online/api-docs.html"
backup_file = "/home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak"

# Read current content
with open(docs_file) as f:
    content = f.read()

# Change 1: Add Italy to dropdown after Hong Kong option
old_dropdown = '<option value="hong_kong" selected>Hong Kong</option>'
new_dropdown = '<option value="hong_kong" selected>Hong Kong</option>\n          <option value="italy">Italy</option>'

if old_dropdown in content:
    print("Change 1: Adding Italy to dropdown after Hong Kong")
    print(f"  Found: {old_dropdown}")
    content = content.replace(old_dropdown, new_dropdown, 1)
    print(f"  Result: added Italy option")
else:
    print("ERROR: Hong Kong option not found in dropdown")

# Change 2: Add "italy" to the country codes text list
old_codes = "hong_kong, malaysia, indonesia, taiwan, macau, newzealand"
new_codes = "hong_kong, italy, malaysia, indonesia, taiwan, macau, newzealand"

if old_codes in content:
    print("\nChange 2: Adding 'italy' to country codes list")
    print(f"  Found: {old_codes}")
    content = content.replace(old_codes, new_codes, 1)
    print(f"  Result: {new_codes}")
else:
    print("ERROR: Country codes text not found")

# Verify Italy is now present
if '<option value="italy">Italy</option>' in content:
    print("\n✓ Italy option added to dropdown")
else:
    print("\n✗ Italy option NOT found in content")

if "hong_kong, italy, malaysia" in content:
    print("✓ Italy added to country codes list")
else:
    print("✗ Italy NOT found in country codes list")

# Write the file
with open(docs_file, 'w') as f:
    f.write(content)

# Verify
print(f"\nFile written: {docs_file}")
print(f"New size: {os.path.getsize(docs_file)} bytes")

# Compute hashes
with open(docs_file, 'rb') as f:
    new_hash = hashlib.sha256(f.read()).hexdigest()
with open(backup_file, 'rb') as f:
    old_hash = hashlib.sha256(f.read()).hexdigest()
print(f"New SHA-256: {new_hash}")
print(f"Old SHA-256: {old_hash}")
print(f"Changed: {new_hash != old_hash}")

# Show diff
import subprocess
result = subprocess.run(["diff", backup_file, docs_file], capture_output=True, text=True)
print(f"\nDiff:")
print(result.stdout)
