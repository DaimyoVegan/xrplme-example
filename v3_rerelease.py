#!/usr/bin/env python3
"""
V3 AUDIT — Re-test RAW_FAILED countries with correct endpoint paths.
READ-ONLY.
"""
import subprocess
import json
import re
import os
import time

print("=" * 80)
print("V3 AUDIT — RAW_FAILED COUNTRY RE-TEST")
print("=" * 80)

# Map slug to full country name for correct endpoint paths
# Based on the actual route definitions in each bot server
SLUG_TO_FULL = {
    "au": "australia",
    "br": "brasil",
    "brunei": "brunei",
    "canada": "canada",
    "ch": "switzerland",
    "de": "germany",
    "fr": "france",
    "hongkong": "hong-kong",
    "id": "indonesia",
    "india": "india",
    "italy": "italy",
    "japan": "japan",
    "korea": "korea",
    "laos": "laos",
    "mo": "macau",
    "mx": "mexico",
    "my": "malaysia",
    "myanmar": "myanmar",
    "nl": "netherlands",
    "nz": "new-zealand",
    "papua-new-guinea": "papua-new-guinea",
    "ph": "philippines",
    "sg": "singapore",
    "thailand": "thailand",
    "timor-leste": "timor-leste",
    "tw": "taiwan",
    "uae": "uae",
    "uk": "uk",
    "usa": "usa",
    "vietnam": "vietnam",
}

# Get active services
result = subprocess.run(["bash", "-c", "ls /etc/systemd/system/*bot-api.service 2>/dev/null"],
                       capture_output=True, text=True)
services = [f.strip() for f in result.stdout.strip().split('\n') if f.strip() and 'bak' not in f]

live_count = 0
raw_failed = []

for svc_file in sorted(services):
    svc_name = os.path.basename(svc_file)
    slug = svc_name.replace('-bot-api.service', '')
    
    # Get port from service file
    with open(svc_file) as f:
        content = f.read()
    port_match = re.search(r'--port\s+(\d+)', content)
    port = port_match.group(1) if port_match else '?'
    
    if port == '?':
        continue
    
    # Get full country name for endpoint
    full_name = SLUG_TO_FULL.get(slug, slug.replace('-', ''))
    
    # Test health
    r = subprocess.run(["curl", "-s", f"http://127.0.0.1:{port}/health"],
                      capture_output=True, text=True, timeout=3)
    health_ok = '"ok"' in r.stdout
    
    if not health_ok:
        continue
    
    # Test raw 402 with correct full name path
    url = f"http://127.0.0.1:{port}/api/v1/{full_name}/bot"
    r = subprocess.run(["curl", "-s", "-X", "POST", url,
                       "-H", "Content-Type: application/json",
                       "-d", '{"message":"audit re-test"}'],
                      capture_output=True, text=True, timeout=3)
    raw_402 = False
    x402_version = None
    raw_amount = None
    if r.stdout.startswith('{') and 'x402Version' in r.stdout:
        try:
            d = json.loads(r.stdout)
            x402_version = d.get('x402Version')
            a = d.get('accepts', [{}])[0]
            raw_amount = a.get('amount')
            raw_402 = True
        except:
            pass
    
    # Test AI 402
    url_ai = f"http://127.0.0.1:{port}/api/v1/{full_name}/bot/ai"
    r = subprocess.run(["curl", "-s", "-X", "POST", url_ai,
                       "-H", "Content-Type: application/json",
                       "-d", '{"message":"audit AI re-test"}'],
                      capture_output=True, text=True, timeout=3)
    ai_402 = False
    ai_amount = None
    if r.stdout.startswith('{') and 'x402Version' in r.stdout:
        try:
            d = json.loads(r.stdout)
            a = d.get('accepts', [{}])[0]
            ai_amount = a.get('amount')
            ai_402 = True
        except:
            pass
    
    alive = "LIVE" if health_ok and raw_402 and ai_402 else "RAW_FAILED"
    if alive == "LIVE":
        live_count += 1
    else:
        raw_failed.append(f"{slug} (path: /api/v1/{full_name}/bot, health={health_ok}, raw={raw_402}, ai={ai_402})")
    
    status_icon = "✓" if alive == "LIVE" else "✗"
    print(f"  {svc_name:<35} port={port:<6} health={'✓' if health_ok else '✗'} raw={'✓' if raw_402 else '✗'}{f'({raw_amount})' if raw_amount else ''} ai={'✓' if ai_402 else '✗'}{f'({ai_amount})' if ai_amount else ''} {status_icon} {alive}")
    
    time.sleep(0.3)  # Rate limiting

print(f"\n--- Corrected Classification ---")
print(f"  LIVE: {live_count}")
print(f"  RAW_FAILED: {len(raw_failed)}")
for r in raw_failed:
    print(f"    {r}")

# Now also check the actual route paths from source files
print(f"\n--- Route Path Verification from Source ---")
api_dir = "/opt/xrplme/thoughts/api"
for svc_file in sorted(services)[:5]:  # Check first 5
    svc_name = os.path.basename(svc_file)
    slug = svc_name.replace('-bot-api.service', '')
    bot_file = f"{slug.replace('-', '_')}_bot_server.py"
    bot_path = os.path.join(api_dir, bot_file)
    if os.path.exists(bot_path):
        with open(bot_path) as f:
            content = f.read()
        routes = re.findall(r'@app\.(?:get|post)\(["\']([^"\']+)["\']', content)
        x402_routes = re.findall(r'path=["\']([^"\']+)["\']', content)
        print(f"  {bot_file}: routes={routes[:5]}, x402_paths={x402_routes[:3]}")

print(f"\n{'=' * 80}")
print("AUDIT COMPLETE")
