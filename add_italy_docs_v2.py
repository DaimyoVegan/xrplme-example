#!/usr/bin/env python3
"""
Step 4: Add Italy to api-docs.html dropdown and country codes text.
Modified to handle root-owned file: write to /tmp first, then use sudo cp.
"""
import os
import hashlib
import subprocess

docs_file = "/var/www/xrplme.online/api-docs.html"
backup_file = "/home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak"
tmp_file = "/tmp/api-docs-italy.html"

# Read from backup (which xrpladmin can read)
with open(backup_file) as f:
    content = f.read()

# Change 1: Add Italy to dropdown after Hong Kong option
old_dropdown = '<option value="hong_kong" selected>Hong Kong</option>'
new_dropdown = '<option value="hong_kong" selected>Hong Kong</option>\n          <option value="italy">Italy</option>'

changes = []
if old_dropdown in content:
    content = content.replace(old_dropdown, new_dropdown, 1)
    changes.append("Added Italy dropdown option after Hong Kong")
else:
    changes.append("ERROR: Hong Kong option not found in dropdown")

# Change 2: Add "italy" to the country codes text list
old_codes = "hong_kong, malaysia, indonesia, taiwan, macau, newzealand"
new_codes = "hong_kong, italy, malaysia, indonesia, taiwan, macau, newzealand"

if old_codes in content:
    content = content.replace(old_codes, new_codes, 1)
    changes.append("Added 'italy' to country codes text list")
else:
    changes.append("ERROR: Country codes text not found")

# Verify
if '<option value="italy">Italy</option>' in content:
    changes.append("✓ Italy option verified in content")
if "hong_kong, italy, malaysia" in content:
    changes.append("✓ Italy verified in country codes text")

# Write to temp file first
with open(tmp_file, 'w') as f:
    f.write(content)

print("Changes applied:")
for c in changes:
    print(f"  {c}")

# Compute hash of new content
new_hash = hashlib.sha256(content.encode()).hexdigest()
with open(backup_file, 'rb') as f:
    old_hash = hashlib.sha256(f.read()).hexdigest()

print(f"\nTemp file: {tmp_file}")
print(f"New size: {os.path.getsize(tmp_file)} bytes")
print(f"New SHA-256: {new_hash}")
print(f"Old SHA-256: {old_hash}")
print(f"Changed: {new_hash != old_hash}")

# Show diff
result = subprocess.run(["diff", backup_file, tmp_file], capture_output=True, text=True)
print(f"\nDiff:")
print(result.stdout)
