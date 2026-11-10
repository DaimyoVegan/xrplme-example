#!/usr/bin/env python3
"""Final verification: get SHA-256 hashes of files to be backed up."""
import hashlib
import os
import subprocess
from datetime import datetime, timezone

# Generate UTC timestamp
ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
print(f"UTC_TIMESTAMP={ts}")

# Files to back up
files = {
    "italy_source": "/opt/xrplme/thoughts/api/italy_bot_server.py",
    "nginx_api": "/etc/nginx/sites-available/api-xrplme-https",
    "api_docs": "/var/www/xrplme.online/api-docs.html",
}

# Compute SHA-256
for label, path in files.items():
    if os.path.exists(path):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        print(f"{label}: {path}")
        print(f"  SHA-256: {h.hexdigest()}")
        print(f"  Size: {os.path.getsize(path)} bytes")
    else:
        print(f"{label}: {path} — NOT FOUND")

# Check backup directory
backup_dir = "/home/xrpladmin/xrplme-state/backups"
print(f"\nBackup directory: {backup_dir}")
print(f"Exists: {os.path.exists(backup_dir)}")
if os.path.exists(backup_dir):
    existing = sorted(os.listdir(backup_dir))
    print(f"Existing backups: {len(existing)}")
    for f in existing[-3:]:
        print(f"  {f}")

# Check Italy service
print(f"\nItaly service status:")
result = subprocess.run(["systemctl", "is-active", "italy-bot-api"], capture_output=True, text=True)
print(f"  is-active: {result.stdout.strip()}")
result = subprocess.run(["systemctl", "is-enabled", "italy-bot-api"], capture_output=True, text=True)
print(f"  is-enabled: {result.stdout.strip()}")

# Check what RequireX402Options accepts when invoice_store not provided
print(f"\n=== x402_xrpl default invoice store ===")
with open("/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/server/__init__.py") as f:
    content = f.read()
    # Find the _InMemoryInvoiceStore
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "_InMemoryInvoiceStore" in line and "class" in line:
            print(f"  Line {i+1}: {line}")
            for j in range(i+1, min(i+15, len(lines))):
                if lines[j].startswith("class ") or (lines[j].startswith("def ") and "    " not in lines[j]):
                    break
                print(f"  Line {j+1}: {lines[j]}")
            break

# Also check the default invoice_ttl_seconds
print(f"\n=== Default invoice_ttl_seconds ===")
for i, line in enumerate(lines):
    if "invoice_ttl_seconds" in line and "default" in line.lower():
        print(f"  Line {i+1}: {line}")
