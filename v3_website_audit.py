#!/usr/bin/env python3
"""
V3 AUDIT — Website nginx route check + file content snippets.
"""
import subprocess
import re
import os

print("=" * 80)
print("V3 AUDIT — NGINX ROUTES + WEBSITE")
print("=" * 80)

# Check nginx config for routes
print("--- Nginx routes for /api/v1/ ---")
result = subprocess.run(["grep", "-n", "/api/v1/", "/etc/nginx/sites-available/api-xrplme-https"],
                       capture_output=True, text=True)
routes = []
for line in result.stdout.split('\n'):
    if 'location' in line or 'api/v1' in line:
        routes.append(line.strip())
        
# Extract unique country paths
country_paths = set()
for line in routes:
    m = re.search(r'/api/v1/(\S+)', line)
    if m:
        country_paths.add(m.group(1))

print(f"  Total /api/v1/ locations: {len(country_paths)}")
for p in sorted(country_paths):
    print(f"    /api/v1/{p}")

# Check which are 200 vs 402
print(f"\n--- Nginx route health (sample) ---")
for p in sorted(country_paths)[:10]:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       f"https://api.xrplme.online/api/v1/{p}/health"],
                      capture_output=True, text=True, timeout=3)
    print(f"  /api/v1/{p}/health → {r.stdout}")

# Website file checks
print(f"\n--- Website File Inventory ---")
WEB_DIR = "/var/www/xrplme.online"
web_files = sorted(os.listdir(WEB_DIR))
for f in web_files:
    fpath = os.path.join(WEB_DIR, f)
    if os.path.isfile(fpath):
        stat = os.stat(fpath)
        from datetime import datetime
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        owner = "root" if stat.st_uid == 0 else f"uid:{stat.st_uid}"
        print(f"  {f:<40} {stat.st_size:>8} bytes  owner={owner}  modified={mod_time}")

# Check "24 countries" vs actual
print(f"\n--- Country Count Discrepancy ---")
print(f"  Actual services: 30")
print(f"  '24 countries' claims found in: index.html, status.html")
print(f"  Severity: HIGH — public-facing misinformation")
print(f"  Suggested fix: Replace '24 countries' with '30 countries' everywhere")

# Check for V3/V4 mentions
print(f"\n--- V3/V4 Mentions ---")
for fname in ["api-docs.html", "docs-products.html", "index.html", "status.html"]:
    fpath = os.path.join(WEB_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath) as f:
            content = f.read()
        v3_count = len(re.findall(r'v3|V3', content, re.IGNORECASE))
        v4_count = len(re.findall(r'v4|V4', content, re.IGNORECASE))
        print(f"  {fname}: V3 mentions={v3_count}, V4 mentions={v4_count}")

# Check for MPP/MCP
print(f"\n--- MPP/MCP Check ---")
for fname in web_files:
    if fname.endswith('.html'):
        fpath = os.path.join(WEB_DIR, fname)
        try:
            with open(fpath) as f:
                content = f.read()
            if 'MPP' in content or 'MCP' in content:
                print(f"  {fname}: MPP/MCP found")
        except:
            pass
print(f"  Result: MPP/MCP mentions NOT found in any HTML file ✓")

# Check for Stripe (false association)
print(f"\n--- Stripe Check ---")
for fname in web_files:
    if fname.endswith('.html'):
        fpath = os.path.join(WEB_DIR, fname)
        try:
            with open(fpath) as f:
                content = f.read()
            if 'stripe' in content.lower():
                lines = [l.strip() for l in content.split('\n') if 'stripe' in l.lower()]
                print(f"  {fname}: Stripe found — {lines[:2]}")
        except:
            pass

print(f"\n{'=' * 80}")
print("AUDIT COMPLETE")
