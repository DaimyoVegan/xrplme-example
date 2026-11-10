#!/usr/bin/env python3
"""
V3 FINAL AUDIT — Source data counts + website inconsistency check
"""
import os
import json
import re

print("=" * 80)
print("V3 AUDIT — SOURCE DATA & WEBSITE INCONSISTENCIES")
print("=" * 80)

# 1. Source data for all 30 countries
print("\n--- 1. Source Data Directory Summary ---")
base_dir = "/opt/xrplme/thoughts/api"
agent_dirs = []
for entry in sorted(os.listdir(base_dir)):
    full_path = os.path.join(base_dir, entry)
    if os.path.isdir(full_path) and ('agent' in entry.lower()):
        agent_dirs.append((entry, full_path))

print(f"Total agent directories: {len(agent_dirs)}")
print(f"\n{'Directory':<35} {'record_count':<15} {'updated_at':<30} {'sources':<40}")
print("-" * 120)

total_records = 0
stale_sources = []
no_license = []

for dirname, dirpath in agent_dirs:
    latest_path = os.path.join(dirpath, "publication", "latest_valid.json")
    if os.path.exists(latest_path):
        try:
            with open(latest_path) as f:
                data = json.load(f)
            count = data.get("record_count", 0)
            updated = data.get("updated_at", "unknown")
            sources = data.get("sources", [])
            source_names = ", ".join(sources)[:40]
            print(f"{dirname:<35} {count:<15} {updated:<30} {source_names:<40}")
            total_records += count
            
            # Check for licensing terms
            records = data.get("records", [])
            has_license = False
            for rec in records:
                lic = rec.get("license", "") or rec.get("license_url", "") or rec.get("terms_url", "")
                if lic:
                    has_license = True
                    break
            if not has_license and records:
                no_license.append(dirname)
            
            # Check staleness
            if isinstance(updated, str) and updated != "unknown":
                # Check if older than 7 days
                from datetime import datetime
                try:
                    updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    age_days = (datetime.now(updated_dt.tzinfo) - updated_dt).days
                    if age_days > 7:
                        stale_sources.append((dirname, age_days))
                except:
                    pass
        except Exception as e:
            print(f"{dirname:<35} ERROR: {e}")
    else:
        print(f"{dirname:<35} NO latest_valid.json")

print(f"\nTotal records across all countries: {total_records}")
print(f"\nStale sources (>7 days old):")
for d, days in stale_sources:
    print(f"  {d}: {days} days stale")
print(f"\nSources without license/terms documentation: {len(no_license)}")
for d in no_license:
    print(f"  {d}")

# Check for duplicate directory names
print(f"\n--- Duplicate Directory Check ---")
dir_names = [d[0] for d in agent_dirs]
from collections import Counter
name_counts = Counter(dir_names)
# Check for variations
for name, count in name_counts.items():
    if count > 1:
        print(f"  Duplicate: {name} ({count}x)")
    # Check for near-duplicates
for d in dir_names:
    if 'png' in d.lower() or 'papua' in d.lower():
        print(f"  Note: '{d}' — check for duplicates")

# Check specific duplicates
if 'papua-new-guinea-agent-full' in dir_names and 'papua_new_guinea-agent-full' in dir_names:
    print(f"  ⚠️  DUPLICATE: 'papua-new-guinea-agent-full' AND 'papua_new_guinea-agent-full' both exist")
    # Check which one the service actually uses
    print(f"  Checking service file for PNG data path...")

# 2. Website inconsistencies
print(f"\n{'=' * 80}")
print("WEBSITE INCONSISTENCY AUDIT")
print(f"{'=' * 80}")

WEB_DIR = "/var/www/xrplme.online"

# Check "24 countries" claims
print(f"\n--- '24 countries' claims (actual: {len(agent_dirs)} countries) ---")
for fname in ["index.html", "status.html", "api-docs.html"]:
    fpath = os.path.join(WEB_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath) as f:
            content = f.read()
        matches = [(i+1, line.strip()[:100]) for i, line in enumerate(content.split('\n')) 
                   if '24 countries' in line.lower() or '24-country' in line.lower()]
        if matches:
            print(f"\n  {fname}:")
            for lineno, line in matches:
                print(f"    L{lineno}: {line}")

# Check for "30 countries" claims
print(f"\n--- '30 countries' claims ---")
for fname in os.listdir(WEB_DIR):
    if fname.endswith('.html'):
        fpath = os.path.join(WEB_DIR, fname)
        try:
            with open(fpath) as f:
                content = f.read()
            if '30 countries' in content.lower() or '30-country' in content.lower():
                matches = [(i+1, line.strip()[:100]) for i, line in enumerate(content.split('\n')) 
                           if '30' in line.lower() and 'countr' in line.lower()]
                if matches:
                    print(f"\n  {fname}:")
                    for lineno, line in matches:
                        print(f"    L{lineno}: {line}")
        except:
            pass

# Check for MPP/MCP mentions
print(f"\n--- MPP/MCP claims ---")
for fname in os.listdir(WEB_DIR):
    if fname.endswith('.html'):
        fpath = os.path.join(WEB_DIR, fname)
        try:
            with open(fpath) as f:
                content = f.read()
            for term in ['MPP', 'MCP', 'Ripple']:
                if term.lower() in content.lower():
                    matches = [(i+1, line.strip()[:120]) for i, line in enumerate(content.split('\n')) 
                               if term.lower() in line.lower()]
                    if matches:
                        print(f"\n  {fname} — '{term}':")
                        for lineno, line in matches[:3]:
                            print(f"    L{lineno}: {line}")
        except:
            pass

# Check directory_site_index.html (root-owned 600)
print(f"\n--- directory_site_index.html ---")
fpath = os.path.join(WEB_DIR, "directory_site_index.html")
stat = os.stat(fpath)
print(f"  Owner: UID {stat.st_uid}, GID {stat.st_gid}, mode: {oct(stat.st_mode)}")
# Can't read it directly (600 root), but check if it's referenced elsewhere
for fname in os.listdir(WEB_DIR):
    if fname.endswith('.html'):
        fpath2 = os.path.join(WEB_DIR, fname)
        try:
            with open(fpath2) as f:
                content = f.read()
            if 'directory_site_index' in content:
                print(f"  Referenced in {fname}: found")
        except:
            pass

# Check agents.html country count
print(f"\n--- agents.html country count ---")
fpath = os.path.join(WEB_DIR, "agents.html")
with open(fpath) as f:
    content = f.read()
agent_entries = re.findall(r'\.row-name|\.row-desc|country-card|agent-card', content)
print(f"  Pattern match count: {len(agent_entries)}")
# Count agent entries by looking for country names
countries_mentioned = re.findall(r'>(thailand|vietnam|japan|korea|singapore|malaysia|indonesia|taiwan|hong.?kong|macau|philippines|india|usa|canada|uae|uk|germany|france|netherlands|switzerland|italy|mexico|brasil|brunei|myanmar|laos|timor.?lace|nepal|bhutan|australia|new.?zealand|papua)\b', content, re.IGNORECASE)
print(f"  Country mentions found: {len(countries_mentioned)}")
print(f"  Unique: {sorted(set(c.lower() for c in countries_mentioned))}")

# Count country cards in agents.html
cards = re.findall(r'row-link|row-name|row-desc', content)
print(f"  Total card elements (row-link+row-name+row-desc): {len(cards)}")
links = re.findall(r'href=["\']([^"\']+)["\']', content)
country_links = [l for l in links if '/docs' in l or '/agent' in l or '/country' in l or l.startswith('/') and 'bot' in l]
print(f"  Country-related links: {len(country_links)}")

# Count agent entries more precisely
agent_blocks = re.findall(r'\.row-desc', content)
print(f"  .row-desc blocks: {len(agent_blocks)}")

# Check for country slugs in links
country_links = re.findall(r'href=["\'](/(?:api/v1|wc/v1)/[a-z-]+)', content)
print(f"  API endpoints linked: {len(country_links)}")

print(f"\n{'=' * 80}")
print("AUDIT COMPLETE")
print(f"{'=' * 80}")
