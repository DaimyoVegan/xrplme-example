#!/usr/bin/env python3
"""
V3 AUDIT — Complete re-test with correct endpoint paths.
Uses systemctl show to get port (no file permission issues).
"""
import subprocess
import json
import re
import os
import time

print("=" * 80)
print("V3 SERVICE STATUS — CORRECTED (full names in paths)")
print("=" * 80)

# Map slug to full country name for endpoint paths
SLUG_TO_FULL = {
    "au": "australia", "br": "brasil", "brunei": "brunei", "canada": "canada",
    "ch": "switzerland", "de": "germany", "fr": "france", "hongkong": "hong-kong",
    "id": "indonesia", "india": "india", "italy": "italy", "japan": "japan",
    "korea": "korea", "laos": "laos", "mo": "macau", "mx": "mexico",
    "my": "malaysia", "myanmar": "myanmar", "nl": "netherlands", "nz": "new-zealand",
    "papua-new-guinea": "papua-new-guinea", "ph": "philippines", "sg": "singapore",
    "thailand": "thailand", "timor-leste": "timor-leste", "tw": "taiwan",
    "uae": "uae", "uk": "uk", "usa": "usa", "vietnam": "vietnam",
}

# Get port from systemctl show or ExecStart
def get_port(svc_name):
    result = subprocess.run(["systemctl", "show", svc_name, "-p", "ExecStart"],
                           capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if '=' in line:
            _, v = line.split('=', 1)
            m = re.search(r'--port\s+(\d+)', v)
            if m:
                return m.group(1)
    return '?'

# Get all active services
result = subprocess.run(["bash", "-c", "ls /etc/systemd/system/*bot-api.service 2>/dev/null | grep -v bak"],
                       capture_output=True, text=True)
services = [os.path.basename(f.strip()) for f in result.stdout.strip().split('\n') if f.strip()]

live_count = 0
raw_failed = []
all_data = []

for svc_name in sorted(services):
    slug = svc_name.replace('-bot-api.service', '')
    full_name = SLUG_TO_FULL.get(slug, slug)
    port = get_port(svc_name)
    
    # Get service properties
    result = subprocess.run(["systemctl", "show", svc_name,
        "-p", "ActiveState", "-p", "SubState", "-p", "MainPID", "-p", "UnitFileState"],
        capture_output=True, text=True)
    fields = {}
    for line in result.stdout.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    
    active = fields.get('ActiveState', 'unknown')
    pid = fields.get('MainPID', '0')
    enabled = fields.get('UnitFileState', '?')
    
    # Health check
    health_ok = False
    health_code = '?'
    if port != '?':
        try:
            r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                              f"http://127.0.0.1:{port}/health"],
                              capture_output=True, text=True, timeout=3)
            health_code = r.stdout
            health_ok = (r.stdout == "200")
        except:
            health_code = 'ERR'
    
    # Raw 402 with correct full name
    raw_402 = False
    raw_amount = '?'
    if port != '?':
        try:
            r = subprocess.run(["curl", "-s", "-X", "POST",
                              f"http://127.0.0.1:{port}/api/v1/{full_name}/bot",
                              "-H", "Content-Type: application/json",
                              "-d", '{"message":"audit"}'],
                              capture_output=True, text=True, timeout=3)
            if r.stdout.startswith('{') and 'x402Version' in r.stdout:
                d = json.loads(r.stdout)
                a = d.get('accepts', [{}])[0]
                raw_amount = a.get('amount', '?')
                raw_402 = (d.get('x402Version') == 2)
        except:
            pass
    
    # AI 402
    ai_402 = False
    ai_amount = '?'
    if port != '?':
        try:
            r = subprocess.run(["curl", "-s", "-X", "POST",
                              f"http://127.0.0.1:{port}/api/v1/{full_name}/bot/ai",
                              "-H", "Content-Type: application/json",
                              "-d", '{"message":"audit"}'],
                              capture_output=True, text=True, timeout=3)
            if r.stdout.startswith('{') and 'x402Version' in r.stdout:
                d = json.loads(r.stdout)
                a = d.get('accepts', [{}])[0]
                ai_amount = a.get('amount', '?')
                ai_402 = (d.get('x402Version') == 2)
        except:
            pass
    
    # Classification
    if health_ok and raw_402 and ai_402:
        classification = "LIVE"
        live_count += 1
    elif health_ok and not raw_402:
        classification = "RAW_FAILED"
        raw_failed.append(f"{slug} ({full_name}, port {port})")
    else:
        classification = "UNKNOWN"
    
    all_data.append({
        'service': svc_name, 'slug': slug, 'full_name': full_name, 'port': port,
        'active': active, 'pid': pid, 'enabled': enabled,
        'health': health_code, 'raw_402': raw_402, 'ai_402': ai_402,
        'raw_amount': raw_amount, 'ai_amount': ai_amount, 'classification': classification
    })
    
    print(f"  {svc_name:<35} {slug:<18} {full_name:<18} port={port:<6} health={health_code:<4} raw={'✓' if raw_402 else '✗'}:{raw_amount} ai={'✓' if ai_402 else '✗'}:{ai_amount} → {classification}")
    
    time.sleep(0.3)

# Summary
print(f"\n--- Classification ---")
print(f"  LIVE: {live_count}/{len(services)}")
print(f"  RAW_FAILED: {len(raw_failed)}")
for r in raw_failed:
    print(f"    {r}")

# Price consistency
raw_prices = set(d['raw_amount'] for d in all_data if d['raw_402'])
ai_prices = set(d['ai_amount'] for d in all_data if d['ai_402'])
print(f"\n  Raw prices: {raw_prices} {'✓ uniform' if len(raw_prices) == 1 else '✗ inconsistent'}")
print(f"  AI prices: {ai_prices} {'✓ uniform' if len(ai_prices) == 1 else '✗ inconsistent'}")

print(f"\n{'=' * 80}")
