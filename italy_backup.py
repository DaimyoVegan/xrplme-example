#!/usr/bin/env python3
"""Step 1: Create timestamped backups of all 3 files to be changed."""
import os
import hashlib
import subprocess
from datetime import datetime, timezone

TS = "20260922_073619"
backup_dir = "/home/xrpladmin/xrplme-state/backups"
os.makedirs(backup_dir, exist_ok=True)

files = {
    "italy_bot_server.py": "/opt/xrplme/thoughts/api/italy_bot_server.py",
    "api-xrplme-https": "/etc/nginx/sites-available/api-xrplme-https",
    "api-docs.html": "/var/www/xrplme.online/api-docs.html",
}

print(f"UTC Timestamp: {TS}")
print(f"Backup directory: {backup_dir}")
print()

for label, source in files.items():
    backup_path = f"{backup_dir}/{label}.{TS}.bak"
    
    # Check if source exists
    if not os.path.exists(source):
        print(f"ERROR: {source} does not exist!")
        continue
    
    # Check if backup already exists
    if os.path.exists(backup_path):
        print(f"SKIP (already exists): {backup_path}")
    else:
        # Copy file
        with open(source, 'rb') as f:
            content = f.read()
        
        with open(backup_path, 'wb') as f:
            f.write(content)
        
        # Compute SHA-256 of both source and backup
        src_hash = hashlib.sha256(content).hexdigest()
        with open(backup_path, 'rb') as f:
            bak_hash = hashlib.sha256(f.read()).hexdigest()
        
        print(f"Created: {backup_path}")
        print(f"  Source: {source} ({os.path.getsize(source)} bytes)")
        print(f"  SHA-256 source: {src_hash}")
        print(f"  SHA-256 backup: {bak_hash}")
        print(f"  Match: {src_hash == bak_hash}")
    print()

# List all backups in the directory
print("All backups in directory:")
for f in sorted(os.listdir(backup_dir)):
    fpath = os.path.join(backup_dir, f)
    size = os.path.getsize(fpath)
    print(f"  {f} ({size} bytes)")
