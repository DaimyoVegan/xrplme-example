#!/usr/bin/env python3
"""
V3 AUDIT — Source/Data Quality + Website Files
READ-ONLY: no changes.
"""
import subprocess
import os
import re
import json

print("=" * 80)
print("V3 SOURCE & DATA AUDIT")
print("=" * 80)

# Source data directories
DATA_DIR = "/home/xrpladmin/xrplme.data"
print(f"\n--- Data directory: {DATA_DIR} ---")
if os.path.exists(DATA_DIR):
    result = subprocess.run(["ls", "-la", DATA_DIR], capture_output=True, text=True)
    print(f"  Contents:")
    for line in result.stdout.split('\n')[1:]:  # Skip header
        if line.strip():
            print(f"  {line.rstrip()[:120]}")
    
    # Check each country's data
    print(f"\n--- Country Data Directory ---")
    entries = sorted(os.listdir(DATA_DIR))
    for entry in entries:
        entry_path = os.path.join(DATA_DIR, entry)
        if os.path.isdir(entry_path):
            files = os.listdir(entry_path)
            print(f"\n  {entry}/ ({len(files)} files):")
            for f in sorted(files):
                fpath = os.path.join(entry_path, f)
                stat = os.stat(fpath)
                print(f"    {f} ({stat.st_size} bytes)")
            
            # Check for data files
            for f in files:
                if f.endswith('.json') or f.endswith('.csv') or f.endswith('.jsonl'):
                    fpath = os.path.join(entry_path, f)
                    try:
                        with open(fpath) as fh:
                            content = fh.read()
                        # Try to get basic stats
                        if f.endswith('.json'):
                            try:
                                data = json.loads(content)
                                if isinstance(data, list):
                                    print(f"    → {f}: {len(data)} records, type=list")
                                    if data and isinstance(data[0], dict):
                                        print(f"      keys: {sorted(data[0].keys())[:10]}")
                                elif isinstance(data, dict):
                                    print(f"    → {f}: {len(data)} top-level keys, type=dict")
                                    print(f"      keys: {sorted(data.keys())[:10]}")
                            except:
                                print(f"    → {f}: not valid JSON, {len(content)} chars")
                        elif f.endswith('.csv'):
                            lines = content.strip().split('\n')
                            print(f"    → {f}: {len(lines)} lines (incl header)")
                            if lines:
                                print(f"      header: {lines[0][:80]}")
                    except Exception as e:
                        print(f"    → {f}: error reading: {e}")
else:
    print(f"  Directory not found: {DATA_DIR}")
    
# Check for other data directories
print(f"\n--- Other data directories ---")
for path in ["/home/xrpladmin/xrplme.data", "/opt/xrplme/data", "/opt/xrplme/thoughts/data"]:
    if os.path.exists(path):
        print(f"  {path}: exists")
        result = subprocess.run(["ls", "-la", path], capture_output=True, text=True)
        for line in result.stdout.split('\n')[1:]:
            if line.strip():
                print(f"    {line.rstrip()[:100]}")
    else:
        print(f"  {path}: not found")

# Check bot server source files for data loading
print(f"\n--- Source code data references ---")
api_dir = "/opt/xrplme/thoughts/api"
if os.path.exists(api_dir):
    for f in sorted(os.listdir(api_dir)):
        if f.endswith('_bot_server.py'):
            fpath = os.path.join(api_dir, f)
            with open(fpath) as fh:
                content = fh.read()
            # Find data file references
            data_refs = re.findall(r'(?:open|json\.load|DATA|data).*?[\'\"]([^\'\"]*\.(json|csv|jsonl))[\'\"]', content, re.IGNORECASE)
            if data_refs:
                print(f"\n  {f}:")
                for ref in data_refs[:5]:
                    print(f"    → {ref[0]}")
            # Find data_dir references
            dir_refs = re.findall(r'(?:DATA_DIR|data_dir|BASE_DIR).*[\'\"]([^\'\"]+)[\'\"]', content, re.IGNORECASE)
            if dir_refs:
                print(f"  {f}:")
                for ref in dir_refs[:3]:
                    print(f"    → {ref}")

# Website files
print(f"\n{'=' * 80}")
print("V3 WEBSITE AUDIT")
print(f"{'=' * 80}")

WEB_DIR = "/var/www/xrplme.online"
if os.path.exists(WEB_DIR):
    print(f"\n--- Website directory: {WEB_DIR} ---")
    result = subprocess.run(["ls", "-la", WEB_DIR], capture_output=True, text=True)
    print(f"  Contents:")
    for line in result.stdout.split('\n')[1:]:
        if line.strip():
            print(f"    {line.rstrip()[:120]}")
    
    # Search for claim strings
    search_terms = [
        "24 countries", "30 countries", "real-time", "regulation",
        "MPP", "MCP", "Stripe", "Ripple", "official",
        "100k", "500k", "100000", "500000",
        "v3", "V3", "x402"
    ]
    
    print(f"\n--- Website Content Search ---")
    for term in search_terms:
        result = subprocess.run(["grep", "-rn", "-i", term, WEB_DIR],
                               capture_output=True, text=True)
        if result.stdout.strip():
            print(f"\n  '{term}':")
            for line in result.stdout.split('\n'):
                if line.strip():
                    # Truncate file path
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        fname = os.path.basename(parts[0])
                        lineno = parts[1]
                        content = parts[2].strip()[:100]
                        print(f"    {fname}:{lineno}: {content}")
    
    # Check specific files
    target_files = [
        "index.html", "agents.html", "api-docs.html", "docs-products.html",
        "v3test.html", "test-v3.html", "homepage-test.html", "directory_site_index.html"
    ]
    
    print(f"\n--- Target File Checks ---")
    for fname in target_files:
        fpath = os.path.join(WEB_DIR, fname)
        if os.path.exists(fpath):
            stat = os.stat(fpath)
            content = open(fpath).read()
            print(f"  {fname}: EXISTS ({stat.st_size} bytes)")
        else:
            print(f"  {fname}: NOT FOUND")
            
else:
    print(f"  Website directory not found: {WEB_DIR}")

# Also check /var/www/
print(f"\n--- /var/www contents ---")
result = subprocess.run(["ls", "-la", "/var/www/"], capture_output=True, text=True)
print(f"  {result.stdout}")

result = subprocess.run(["find", "/var/www/", "-name", "*.html", "-maxdepth", "3"],
                       capture_output=True, text=True)
print(f"\n--- HTML files under /var/www ---")
for line in result.stdout.split('\n'):
    if line.strip():
        print(f"  {os.path.basename(line.strip())}: {os.path.getsize(line.strip())} bytes")

print(f"\n{'=' * 80}")
print("SOURCE & WEBSITE AUDIT COMPLETE")
print(f"{'=' * 80}")
