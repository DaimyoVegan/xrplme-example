#!/usr/bin/env python3
"""
V3 PREPARE: Website text corrections (24→30 countries)
READ + PREPARE ONLY. No deployment until explicit approval.
"""
import subprocess
import hashlib
import os
import re
import time
from datetime import datetime

VPS = "xrplme-vps"
REMOTE_WEB = "/var/www/xrplme.online"
LOCAL_PREP = "/data/data/com.termux/files/home/xrplme-example/website_prep"
FILES = ["index.html", "status.html"]

os.makedirs(LOCAL_PREP, exist_ok=True)

print("=" * 80)
print("V3 PREPARE — WEBSITE TEXT CORRECTIONS (24 → 30 COUNTRIES)")
print("=" * 80)

# Step 1: Fetch current files from VPS + compute SHA-256
print("\n--- Step 1: Fetch current files + compute SHA-256 ---")
original_hashes = {}
for fname in FILES:
    remote_path = f"{REMOTE_WEB}/{fname}"
    local_orig = os.path.join(LOCAL_PREP, f"{fname}.orig")
    
    # Fetch file
    subprocess.run(["scp", f"{VPS}:{remote_path}", local_orig],
                   check=True, capture_output=True)
    
    # Compute hash
    with open(local_orig, 'rb') as f:
        content = f.read()
    h = hashlib.sha256(content).hexdigest()
    original_hashes[fname] = h
    print(f"  {fname}: {len(content)} bytes, SHA-256: {h}")

# Step 1b: Check owner and permissions
print("\n--- Step 1b: Owner and permissions ---")
for fname in FILES:
    r = subprocess.run(["ssh", VPS, f"stat -c '%U:%G %a' {REMOTE_WEB}/{fname}"],
                      capture_output=True, text=True)
    print(f"  {fname}: {r.stdout.strip()}")

# Step 2: Create timestamped backups ON THE VPS
print("\n--- Step 2: Create timestamped backups on VPS ---")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_hashes = {}
for fname in FILES:
    remote_orig = f"{REMOTE_WEB}/{fname}"
    remote_bak = f"{REMOTE_WEB}/{fname}.bak.{timestamp}"
    
    # Create backup
    result = subprocess.run(["ssh", VPS, f"cp {remote_orig} {remote_bak}"],
                           capture_output=True, text=True)
    if result.returncode == 0:
        # Hash the backup
        r = subprocess.run(["ssh", VPS, f"sha256sum {remote_bak}"],
                          capture_output=True, text=True)
        backup_hash = r.stdout.strip().split()[0]
        backup_hashes[fname] = (remote_bak, backup_hash)
        print(f"  {fname} → {remote_bak}")
        print(f"    SHA-256: {backup_hash}")
    else:
        print(f"  ERROR creating backup for {fname}: {result.stderr}")

# Step 3: Apply changes locally (on tablet)
print("\n--- Step 3: Apply changes (local staging) ---")
prepared_hashes = {}
diffs = []

for fname in FILES:
    local_orig = os.path.join(LOCAL_PREP, f"{fname}.orig")
    local_prep = os.path.join(LOCAL_PREP, fname)
    
    with open(local_orig, 'r') as f:
        content = f.read()
    
    # Find all occurrences of "24 countries"
    occurrences = [(m.start(), m.group()) for m in re.finditer(r'24 countries', content)]
    print(f"  {fname}: found {len(occurrences)} occurrences of '24 countries'")
    
    # Replace all
    new_content = content.replace("24 countries", "30 countries")
    
    # Verify exactly 5 total replacements across both files
    actual_replacements = len(content) - len(new_content)
    # Since "24 countries" = 13 chars, "30 countries" = 13 chars, length check won't work
    replacement_count = content.count("24 countries")
    
    with open(local_prep, 'w') as f:
        f.write(new_content)
    
    # Compute hash
    with open(local_prep, 'rb') as f:
        prepared_hash = hashlib.sha256(f.read()).hexdigest()
    prepared_hashes[fname] = prepared_hash
    
    # Generate diff
    r = subprocess.run(["diff", "-u", local_orig, local_prep],
                      capture_output=True, text=True)
    diffs.append(r.stdout)
    print(f"    Replacements: {replacement_count}")
    print(f"    SHA-256 (prepared): {prepared_hash}")

# Step 4: Show all diffs
print("\n--- Step 4: Unified Diffs ---")
for fname, diff in zip(FILES, diffs):
    print(f"\n  === {fname} ===")
    for line in diff.split('\n'):
        print(f"  {line}")

# Step 5: Summary
print("\n--- Step 5: Verification Summary ---")
total_replacements = sum(open(f"{LOCAL_PREP}/{f}.orig", 'r').read().count("24 countries") for f in FILES)
print(f"  Total '24 countries' → '30 countries' replacements: {total_replacements}")
print(f"  Expected: 5 (3 in index.html, 2 in status.html)")
print(f"  Match: {'✓ YES' if total_replacements == 5 else '✗ NO — MISMATCH'}")

print(f"\n  File hashes:")
for fname in FILES:
    orig = original_hashes[fname]
    prep = prepared_hashes[fname]
    match = original_hashes[fname] == backup_hashes[fname][1]
    print(f"    {fname}:")
    print(f"      Original SHA-256:  {orig}")
    print(f"      Backup SHA-256:    {backup_hashes[fname][1]}")
    print(f"      Original==Backup:  {'✓' if match else '✗'}")
    print(f"      Prepared SHA-256:  {prep}")

print(f"\n  File permissions (must remain unchanged):")
for fname in FILES:
    r = subprocess.run(["ssh", VPS, f"stat -c '%U:%G %a' {REMOTE_WEB}/{fname}"],
                      capture_output=True, text=True)
    print(f"    {fname}: {r.stdout.strip()}")

# Verify no other text changed
print(f"\n  Content change verification:")
for fname in FILES:
    with open(f"{LOCAL_PREP}/{fname}.orig", 'r') as f:
        orig = f.read()
    with open(f"{LOCAL_PREP}/{fname}", 'r') as f:
        prep = f.read()
    # Check that only "24 countries" → "30 countries" changed
    orig_lines = orig.split('\n')
    prep_lines = prep.split('\n')
    changed_lines = []
    for i, (o, p) in enumerate(zip(orig_lines, prep_lines)):
        if o != p:
            changed_lines.append((i+1, o, p))
    print(f"    {fname}: {len(changed_lines)} lines changed")
    for lineno, old, new in changed_lines:
        print(f"      L{lineno}: '{old[:60]}...' → '{new[:60]}...'")

print(f"\n{'=' * 80}")
print("WEBSITE TEXT CHANGES PREPARED ONLY.")
print("NO FILES DEPLOYED.")
print("NO SERVICES RESTARTED.")
print("NO NGINX RELOADED.")
print("NO DATABASE WRITES.")
print("NO PAYMENT PERFORMED.")
print(f"{'=' * 80}")
