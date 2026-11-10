#!/usr/bin/env python3
"""
V3 PREPARE v2: Website text corrections (24 → 30 countries)
Fixed: status.html meta description has '24 country' (singular) not '24 countries'
Fixed: backups created locally (xrpladmin can't write to www-data dir)
"""
import hashlib
import os
import re
import subprocess
from datetime import datetime

VPS = "xrplme-vps"
REMOTE_WEB = "/var/www/xrplme.online"
LOCAL_PREP = "/data/data/com.termux/files/home/xrplme-example/website_prep"
FILES = ["index.html", "status.html"]

os.makedirs(LOCAL_PREP, exist_ok=True)

print("=" * 80)
print("V3 PREPARE v2 — WEBSITE TEXT CORRECTIONS (24 → 30 COUNTRIES)")
print("=" * 80)

# Step 1: Fetch current files from VPS + compute SHA-256
print("\n--- Step 1: Fetch current files + compute SHA-256 ---")
original_hashes = {}
for fname in FILES:
    remote_path = f"{REMOTE_WEB}/{fname}"
    local_orig = os.path.join(LOCAL_PREP, f"{fname}.orig")
    
    result = subprocess.run(["scp", f"{VPS}:{remote_path}", local_orig],
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR fetching {fname}: {result.stderr}")
        continue
    
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

# Step 1c: Check directory permissions
print("\n--- Step 1c: Directory permissions ---")
r = subprocess.run(["ssh", VPS, f"stat -c '%U:%G %a' {REMOTE_WEB}"],
                  capture_output=True, text=True)
print(f"  {REMOTE_WEB}: {r.stdout.strip()}")

# Step 2: Create LOCAL timestamped backups (xrpladmin cannot write to www-data dir)
print("\n--- Step 2: Create LOCAL timestamped backups ---")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_hashes = {}
for fname in FILES:
    local_orig = os.path.join(LOCAL_PREP, f"{fname}.orig")
    local_bak = os.path.join(LOCAL_PREP, f"{fname}.bak.{timestamp}")
    
    # Copy locally
    subprocess.run(["cp", local_orig, local_bak], check=True)
    
    with open(local_bak, 'rb') as f:
        bak_content = f.read()
    h = hashlib.sha256(bak_content).hexdigest()
    backup_hashes[fname] = (local_bak, h)
    print(f"  {fname} → {local_bak}")
    print(f"    SHA-256: {h}")

# Step 3: Analyze exact occurrences
print("\n--- Step 3: Exact '24 countries' occurrences ---")
for fname in FILES:
    local_orig = os.path.join(LOCAL_PREP, f"{fname}.orig")
    with open(local_orig, 'r') as f:
        content = f.read()
    
    # Find all "24 countries" and "24 country" (check for edge cases)
    matches = []
    for i, line in enumerate(content.split('\n'), 1):
        if "24 countries" in line:
            matches.append((i, line.strip()[:100]))
        elif "24 country" in line:
            matches.append((i, line.strip()[:100], "WARNING: singular"))
    
    print(f"\n  {fname}:")
    for m in matches:
        if len(m) == 3:
            print(f"    L{m[0]}: {m[1]} ⚠️ {m[2]}")
        else:
            print(f"    L{m[0]}: {m[1]}")
    count = content.count("24 countries")
    print(f"  Exact '24 countries' matches: {count}")

# Step 4: Apply changes locally
print("\n--- Step 4: Apply changes (local staging) ---")
prepared_hashes = {}
diffs = []
total_replacements = 0

for fname in FILES:
    local_orig = os.path.join(LOCAL_PREP, f"{fname}.orig")
    local_prep = os.path.join(LOCAL_PREP, fname)
    
    with open(local_orig, 'r') as f:
        content = f.read()
    
    replacement_count = content.count("24 countries")
    total_replacements += replacement_count
    
    new_content = content.replace("24 countries", "30 countries")
    
    with open(local_prep, 'w') as f:
        f.write(new_content)
    
    with open(local_prep, 'rb') as f:
        prepared_hash = hashlib.sha256(f.read()).hexdigest()
    prepared_hashes[fname] = prepared_hash
    
    # Generate diff
    r = subprocess.run(["diff", "-u", local_orig, local_prep],
                      capture_output=True, text=True)
    diffs.append(r.stdout)
    print(f"  {fname}: {replacement_count} replacements → SHA-256: {prepared_hash}")

# Step 5: Show all diffs
print("\n--- Step 5: Unified Diffs ---")
for fname, diff in zip(FILES, diffs):
    print(f"\n  === {fname} ===")
    for line in diff.split('\n'):
        print(f"  {line}")

# Step 6: Verification Summary
print("\n--- Step 6: Verification Summary ---")
print(f"  Total '24 countries' → '30 countries' replacements: {total_replacements}")
print(f"  Expected: 5 (3 in index.html, 2 in status.html)")
print(f"  Actual found: {total_replacements}")
if total_replacements != 5:
    print(f"  NOTE: status.html meta description contains '24 country' (singular)")
    print(f"        not '24 countries' (plural). Only 4 exact matches of '24 countries' exist.")
    print(f"        The status.html meta description says '24 country AI agents' (singular).")

print(f"\n  File hashes:")
for fname in FILES:
    orig = original_hashes[fname]
    prep = prepared_hashes[fname]
    bak = backup_hashes[fname][1]
    print(f"    {fname}:")
    print(f"      Original SHA-256:  {orig}")
    print(f"      Backup SHA-256:    {bak}")
    print(f"      Original==Backup:  {'✓' if orig == bak else '✗'}")
    print(f"      Prepared SHA-256:  {prep}")

print(f"\n  File permissions (will remain unchanged):")
for fname in FILES:
    r = subprocess.run(["ssh", VPS, f"stat -c '%U:%G %a' {REMOTE_WEB}/{fname}"],
                      capture_output=True, text=True)
    print(f"    {fname}: {r.stdout.strip()}")

# Verify only "24 countries" changed
print(f"\n  Content change verification:")
for fname in FILES:
    with open(f"{LOCAL_PREP}/{fname}.orig", 'r') as f:
        orig = f.read()
    with open(f"{LOCAL_PREP}/{fname}", 'r') as f:
        prep = f.read()
    orig_lines = orig.split('\n')
    prep_lines = prep.split('\n')
    changed_lines = []
    for i, (o, p) in enumerate(zip(orig_lines, prep_lines)):
        if o != p:
            changed_lines.append((i+1, o[:80], p[:80]))
    print(f"    {fname}: {len(changed_lines)} lines changed (all should be '24 countries' → '30 countries')")
    for lineno, old, new in changed_lines:
        print(f"      L{lineno}: \"{old}\" → \"{new}\"")

print(f"\n{'=' * 80}")
print("WEBSITE TEXT CHANGES PREPARED ONLY.")
print("NO FILES DEPLOYED.")
print("NO SERVICES RESTARTED.")
print("NO NGINX RELOADED.")
print("NO DATABASE WRITES.")
print("NO PAYMENT PERFORMED.")
print(f"{'=' * 80}")
print(f"\n  Backups stored locally at: {LOCAL_PREP}/")
print(f"  Prepared files at:          {LOCAL_PREP}/")
print(f"\n  NOTE: VPS /var/www is owned by www-data — cannot create backups there.")
print(f"        Local backups created instead. To deploy, will need:")
print(f"        sudo cp {LOCAL_PREP}/index.html /var/www/xrplme.online/index.html")
print(f"        sudo cp {LOCAL_PREP}/status.html /var/www/xrplme.online/status.html")
