#!/usr/bin/env python3
"""
Audit ALL VPS country bots: systemd services, nginx routes, listening ports, HTTP responses.
"""
import subprocess
import json
import os

def ssh(cmd, timeout=30):
    r = subprocess.run(["ssh", "xrplme-vps", cmd], capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr, r.returncode

# 1. Get all country bot processes
print("=" * 80)
print("VPS COUNTRY BOT AUDIT")
print("=" * 80)

# List all systemd services related to bots
print("\n1. SYSTEMD SERVICES")
print("-" * 80)
out, err, rc = ssh("systemctl list-units --all '*bot*' --no-legend 2>/dev/null || systemctl list-unit-files '*bot*' 2>/dev/null", timeout=10)
if out:
    for line in out.strip().split('\n'):
        if line.strip():
            print(f"  {line}")

# Also check service files
out2, _, _ = ssh("ls /etc/systemd/system/*bot* 2>/dev/null; ls /tmp/*-bot-api.service 2>/dev/null", timeout=5)
print(f"\n  Service files found:\n{out2}")

# 2. Check listening ports
print("\n2. LISTENING PORTS (bot ports)")
print("-" * 80)
out, err, rc = ssh("ss -tlnp | grep -E '8[0-9]{3}' | sort -t: -k2 -n", timeout=10)
for line in out.strip().split('\n'):
    if line.strip():
        print(f"  {line}")

# 3. Check all country bot service statuses
print("\n3. SERVICE STATUSES")
print("-" * 80)
bots_to_check = [
    "thailand", "vietnam", "japan", "korea", "india", "usa", "canada", "uae", "uk",
    "philippines", "singapore", "australia", "germany", "france", "brazil", "mexico",
    "switzerland", "netherlands", "hongkong", "hong_kong", "macau", "malaysia", "newzealand",
    "brunei", "laos", "myanmar", "timor-leste", "papua-new-guinea"
]

for bot in bots_to_check:
    # Check if service file exists
    service_variants = [f"{bot}-bot-api.service", f"{bot.replace('-','').replace('_','')}-bot-api.service"]
    for svc in service_variants:
        out, err, rc = ssh(f"systemctl status {svc} 2>&1 | head -5", timeout=5)
        if rc != 0 and "Unit" not in out and "not loaded" not in out:
            continue
        if "could not be found" in out or "not loaded" in out:
            continue
        print(f"\n  {bot} ({svc}):")
        for line in out.strip().split('\n')[:5]:
            print(f"    {line}")
        break

# 4. Check process status for each port
print("\n4. PROCESS STATUS BY PORT")
print("-" * 80)
ports = [8085, 8086, 8087, 8089, 8090, 8091, 8092, 8093, 8094, 8088,
         8097, 8098, 8099, 8100, 8101, 8102, 8103, 8105, 8106, 8107, 8108, 8109, 8110,
         8111, 8112, 8113, 8114, 8115, 8117]

for port in sorted(ports):
    out, _, _ = ssh(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{port}/health 2>&1; echo", timeout=5)
    status = out.strip()
    if status and status != "000":
        print(f"  Port {port}: HTTP {status}")

# 5. Nginx routes
print("\n5. NGINX ROUTES (wc/v1/*)")
print("-" * 80)
out, _, _ = ssh("grep -c 'wc/v1/' /etc/nginx/sites-available/xrplme-online-https 2>/dev/null", timeout=5)
print(f"  Total wc/v1/ routes: {out.strip()}")

out, _, _ = ssh("grep 'location = /wc/v1/' /etc/nginx/sites-available/xrplme-online-https | sed 's/location = /wc/v1//; s/ {.*//' | tr -d ' '", timeout=5)
countries = [c for c in out.strip().split('\n') if c]
print(f"  Countries with routes: {len(countries)}")
for c in countries:
    print(f"    /wc/v1/{c}/bot")

# 6. Check which countries have bot servers but no systemd service
print("\n6. MISSING SYSTEMD SERVICES")
print("-" * 80)
out, _, _ = ssh("ls /opt/xrplme/thoughts/api/*_bot_server.py 2>/dev/null | sed 's/.*\\/\\/\\///; s/_bot_server.py//' | sort", timeout=5)
bot_modules = [m for m in out.strip().split('\n') if m]

out2, _, _ = ssh("ls /etc/systemd/system/*bot-api.service 2>/dev/null | sed 's/.*\\/\\/\\///; s/-bot-api.service//' | sort 2>/dev/null; ls /tmp/*-bot-api.service 2>/dev/null | sed 's/.*\\/\\/\\///; s/-bot-api.service//' | sort", timeout=5)
service_names = [s.replace('-', '_') for s in out2.strip().split('\n') if s]

for m in bot_modules:
    if m not in [s.replace('-', '_') for s in service_names]:
        # Check if it's a known country
        display = m.replace('_', ' ').title()
        print(f"  {display} ({m}): NO systemd service")

# 7. Check failing services
print("\n7. FAILING/INACTIVE SERVICES")
print("-" * 80)
for svc in ["japan-bot-api", "korea-bot-api", "macau-bot-api", "malaysia-bot-api", "newzealand-bot-api", "thailand-bot-api", "vietnam-bot-api"]:
    out, err, rc = ssh(f"systemctl is-active {svc} 2>&1; systemctl status {svc} --no-pager 2>&1 | head -3", timeout=5)
    status = out.strip().split('\n')[0] if out.strip() else "unknown"
    details = out.strip().split('\n')[1:3] if len(out.strip().split('\n')) > 1 else []
    print(f"  {svc}: {status}")
    for d in details:
        if d.strip():
            print(f"    {d.strip()}")
