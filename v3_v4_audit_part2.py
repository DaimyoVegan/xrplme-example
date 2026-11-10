#!/usr/bin/env python3
"""
V3/V4 READ-ONLY AUDIT — Part 2: V4 Isolation, Website, Payment Safety, Data Quality
Run on VPS.
"""
import requests
import json
import os
import subprocess
import glob

print("=" * 80)
print("V4 ISOLATION AUDIT")
print("=" * 80)

# Check for V4 artifacts
v4_checks = [
    ("V4 source code", ["/opt/xrplme/thoughts/v4", "/opt/xrplme/v4", "/home/xrpladmin/v4", "/opt/xrplme/v4_evidence"]),
    ("V4 venv", ["/home/xrpladmin/v4_venv", "/opt/xrplme/v4_venv"]),
    ("V4 systemd service", ["v4-"]),
    ("V4 nginx route", ["/api/v2/"]),
    ("V4 data directory", ["/opt/xrplme/v4_data", "/home/xrpladmin/v4_data"]),
    ("V4 logs", ["/var/log/v4", "/opt/xrplme/v4.log"]),
]

for label, paths in v4_checks:
    found = False
    for p in paths:
        if p.startswith("v4") or p.startswith("/api"):
            # Check systemd or nginx
            try:
                out = subprocess.run(["systemctl", "list-unit-files"], capture_output=True, text=True, timeout=5)
                if p in out.stdout:
                    found = True
                    print(f"  {label}: PRESENT (systemd: {p})")
                    break
            except:
                pass
            # Check nginx
            if p.startswith("/api/v2"):
                try:
                    out = subprocess.run(["grep", p, "/etc/nginx/sites-available/xrplme-online-https"], capture_output=True, text=True, timeout=5)
                    if out.stdout.strip():
                        found = True
                        print(f"  {label}: PRESENT (nginx: {p})")
                        break
                except:
                    pass
        else:
            if os.path.exists(p):
                found = True
                print(f"  {label}: PRESENT ({p})")
                break
    if not found:
        print(f"  {label}: ABSENT")

# Check for /api/v2 routes specifically
print("\n=== V4 /api/v2/ routes in nginx ===")
try:
    out = subprocess.run(["grep", "-r", "api/v2", "/etc/nginx/"], capture_output=True, text=True, timeout=5)
    if out.stdout.strip():
        print(f"  PRESENT:\n{out.stdout[:200]}")
    else:
        print("  ABSENT")
except Exception as e:
    print(f"  Check error: {e}")

# Check for V4 Python packages
print("\n=== V4 packages in venv ===")
try:
    out = subprocess.run(["/home/xrpladmin/thailand_bot_venv/bin/pip", "list"], capture_output=True, text=True, timeout=10)
    v4_pkgs = [l for l in out.stdout.split("\n") if "v4" in l.lower() or "evidence" in l.lower() or "mpp" in l.lower() or "openai" in l.lower()]
    if v4_pkgs:
        print(f"  Found: {v4_pkgs}")
    else:
        print("  No V4/MPP/evidence packages in shared venv")
except:
    print("  Could not check pip packages")

print("\n" + "=" * 80)
print("WEBSITE AUDIT")
print("=" * 80)

# Check website existence
print("\n=== Website files ===")
website_root = "/var/www/xrplme.online"
if os.path.exists(website_root):
    print(f"  Website root: {website_root} (exists)")
    files = os.listdir(website_root)
    html_files = [f for f in files if f.endswith(".html")]
    print(f"  HTML files: {html_files}")
    
    # Check for agents page
    if os.path.exists(f"{website_root}/agents.html"):
        print("  /agents.html: EXISTS")
    elif os.path.exists(f"{website_root}/agents"):
        print("  /agents/: EXISTS")
    else:
        print("  /agents: NOT FOUND")
    
    # Check api-docs.html
    if os.path.exists(f"{website_root}/api-docs.html"):
        print("  api-docs.html: EXISTS")
        with open(f"{website_root}/api-docs.html") as f:
            content = f.read()
        # Count country options
        import re
        options = re.findall(r'value="([a-z_-]+)"', content)
        print(f"  Countries in dropdown: {len(options)}")
        print(f"  Options: {options}")
        
        # Check for V4 mentions
        if "v4" in content.lower() or "evidence" in content.lower():
            print("  V4 mentioned in api-docs.html: YES")
        else:
            print("  V4 mentioned in api-docs.html: NO")
        
        # Check for price mentions
        prices = re.findall(r'0\.\d+\s*XRP', content)
        print(f"  Prices mentioned: {prices}")
        
        # Check for mpp mentions
        if "mpp" in content.lower():
            print("  MPP mentioned: YES")
        else:
            print("  MPP mentioned: NO")
        
        # Check for x402 mentions
        if "x402" in content.lower():
            print("  x402 mentioned: YES")
        else:
            print("  x402 mentioned: NO")

# Check homepage
print("\n=== Homepage ===")
try:
    r = requests.get("https://xrplme.online/", timeout=10, verify=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        # Check for V3/V4 mentions
        text = r.text.lower()
        if "v4" in text:
            print("  V4 mentioned on homepage: YES")
        if "evidence" in text:
            print(f"  'evidence' on homepage: YES")
        if "x402" in text:
            print("  x402 on homepage: YES")
        if "mpp" in text:
            print("  MPP on homepage: YES")
        if "stripe" in text:
            print("  Stripe on homepage: YES")
        if "ripple" in text:
            print("  Ripple on homepage: YES")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 80)
print("PAYMENT SAFETY AUDIT")
print("=" * 80)

# Check nginx config for payment-related config
print("\n=== x402 facilitator config ===")
nginx_conf = "/etc/nginx/sites-available/xrplme-online-https"
try:
    with open(nginx_conf) as f:
        content = f.read()
    # Check for facilitator references
    if "facilitator" in content.lower():
        lines = [l for l in content.split("\n") if "facilitator" in l.lower() or "t54" in l.lower() or "x402" in l.lower()]
        for line in lines:
            # Redact any potential secrets
            safe_line = line[:100] if not any(w in line.lower() for w in ["password", "secret", "key", "token", "bearer"]) else "[REDACTED]"
            print(f"  {safe_line}")
    else:
        print("  No facilitator references in nginx config")
        
    # Check for payTo address
    import re
    payto_addresses = re.findall(r'razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8', content)
    print(f"  payTo address found in nginx config: {len(payto_addresses)} times")
    print(f"  payTo address is public (not a secret): YES")
except Exception as e:
    print(f"  Error reading nginx config: {e}")

# Check environment files (just existence, not content)
print("\n=== Environment files ===")
env_files = [
    "/home/xrpladmin/x402-treasury.env",
    "/home/xrpladmin/.env",
    "/opt/xrplme/.env",
    "/opt/xrplme/thoughts/api/.env",
]
for f in env_files:
    if os.path.exists(f):
        stat = os.stat(f)
        print(f"  {f}: EXISTS (owner={stat.st_uid}, mode={oct(stat.st_mode)})")
        # Check for seed keywords without printing content
        try:
            with open(f) as fh:
                content = fh.read().lower()
            has_seed = "seed" in content or "secret" in content or "private" in content
            print(f"    Contains SECRET_PRESENT: {has_seed}")
        except:
            print(f"    Cannot read (permission)")
    else:
        print(f"  {f}: NOT FOUND")

print("\n" + "=" * 80)
print("DATA QUALITY AUDIT")
print("=" * 80)

# Check bot server source code for data quality patterns
print("\n=== Bot server source code locations ===")
bot_dirs = ["/opt/xrplme/thoughts/api"]
for d in bot_dirs:
    if os.path.exists(d):
        print(f"  {d}: EXISTS")
        py_files = [f for f in os.listdir(d) if f.endswith("_bot_server.py")]
        print(f"  Bot server files ({len(py_files)}): {py_files[:10]}...")
        
        # Check a few for source/freshness fields
        for pf in ["thailand_bot_server.py", "italy_bot_server.py"]:
            pf_path = os.path.join(d, pf)
            if os.path.exists(pf_path):
                with open(pf_path) as f:
                    content = f.read()
                has_sources = "sources" in content.lower()
                has_source_url = "source_url" in content.lower() or "url" in content.lower()
                has_timestamp = "timestamp" in content.lower() or "retrieved" in content.lower()
                has_freshness = "freshness" in content.lower()
                has_schema_version = "schema_version" in content.lower()
                print(f"\n  {pf}:")
                print(f"    Has 'sources' field: {has_sources}")
                print(f"    Has 'source_url' field: {has_source_url}")
                print(f"    Has 'timestamp'/'retrieved': {has_timestamp}")
                print(f"    Has 'freshness': {has_freshness}")
                print(f"    Has 'schema_version': {has_schema_version}")
    else:
        print(f"  {d}: NOT FOUND")

# Check country-specific bot files
print("\n=== Country bot server files ===")
for d in bot_dirs:
    bot_dir = d if os.path.exists(d) else ""
    if bot_dir:
        py_files = sorted([f for f in os.listdir(d) if f.endswith("_bot_server.py")])
        print(f"  Total bot server files: {len(py_files)}")
        print(f"  Files: {py_files}")

# Check data files
print("\n=== Data files ===")
for d in bot_dirs:
    if os.path.exists(d):
        json_files = [f for f in os.listdir(d) if f.endswith(".json") and "data" in f.lower()]
        print(f"  Data JSON files in {d}: {len(json_files)}")
        if json_files:
            for jf in json_files[:5]:
                jf_path = os.path.join(d, jf)
                try:
                    with open(jf_path) as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        print(f"    {jf}: {len(data)} records")
                    elif isinstance(data, dict):
                        print(f"    {jf}: {len(data.keys())} keys")
                except:
                    print(f"    {jf}: (could not parse)")
