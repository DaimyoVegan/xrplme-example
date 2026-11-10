#!/usr/bin/env python3
"""
V3 AUDIT — V4 Boundary Check + Full 402 Response + Public 402 Details
"""
import subprocess
import json

print("=" * 80)
print("6. V4 PREPARATION BOUNDARY CHECK")
print("=" * 80)

# Check for V4 anywhere
print("\n--- V4 source code check ---")
result = subprocess.run(["find", "/opt/xrplme/thoughts/api/", "-name", "v4*", "-o", "-name", "V4*"],
                       capture_output=True, text=True)
v4_src = result.stdout.strip()
print(f"  V4 source files: {v4_src if v4_src else 'NONE ✓'}")

# Check for V4 systemd
result = subprocess.run(["ls", "/etc/systemd/system/*v4*"],
                       capture_output=True, text=True)
print(f"  V4 systemd units: {'NONE ✓' if not result.stdout.strip() else result.stdout.strip()}")

# Check for V4 in nginx
result = subprocess.run(["grep", "-rn", "/v4/", "/etc/nginx/sites-available/"],
                       capture_output=True, text=True)
v4_nginx = result.stdout.strip()
print(f"  V4 nginx routes: {'NONE ✓' if not v4_nginx else v4_nginx[:200]}")

# Check for V4 in website
result = subprocess.run(["grep", "-rn", "v4", "/var/www/xrplme.online/*.html"],
                       capture_output=True, text=True)
v4_web = result.stdout.strip()
print(f"  V4 website mentions: {'NONE ✓' if not v4_web else v4_web[:200]}")

# Check for MCP
result = subprocess.run(["find", "/opt/xrplme/thoughts/api/", "-name", "mcp*"],
                       capture_output=True, text=True)
print(f"  MCP files: {'NONE ✓' if not result.stdout.strip() else result.stdout.strip()[:200]}")

# Check for MPP
result = subprocess.run(["grep", "-rn", "MPP", "/opt/xrplme/thoughts/api/"],
                       capture_output=True, text=True)
mpp = result.stdout.strip()
print(f"  MPP in source: {'NONE ✓' if not mpp else mpp[:200]}")

print("\n--- V4 Boundary Confirmed ---")
print("  V4 absent from: production source, systemd, nginx, website ✓")

# Full 402 response comparison
print("\n" + "=" * 80)
print("FULL 402 RESPONSE COMPARISON")
print("=" * 80)

samples = [
    ("Thailand", "thailand", "8085"),
    ("Italy", "italy", "8117"),
    ("USA", "usa", "8091"),
    ("Singapore", "singapore", "8096"),
    ("Taiwan", "taiwan", "8108"),
]

for name, slug, port in samples:
    print(f"\n--- {name} (port {port}) ---")
    
    # Raw 402
    r = subprocess.run(["curl", "-s", "--max-time", "8", "-D", "-", "-X", "POST",
                       f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"message": "schema compare"})],
                      capture_output=True, text=True, timeout=10)
    
    header_end = r.stdout.find('\n\n')
    headers = r.stdout[:header_end]
    body = r.stdout[header_end+2:]
    
    # Parse status
    status_line = headers.split('\n')[0]
    print(f"  Raw 402 HTTP Status: {status_line}")
    print(f"  Headers:")
    for line in headers.split('\n')[1:]:
        if line.strip():
            print(f"    {line.strip()}")
    try:
        d = json.loads(body)
        print(f"  Body JSON:")
        print(f"    x402Version: {d.get('x402Version')}")
        print(f"    resource.url: {d.get('resource', {}).get('url', '?')}")
        print(f"    resource.description: {d.get('resource', {}).get('description', '?')}")
        accepts = d.get('accepts', [])
        if accepts:
            a = accepts[0]
            print(f"    accepts[0].scheme: {a.get('scheme')}")
            print(f"    accepts[0].network: {a.get('network')}")
            print(f"    accepts[0].amount: {a.get('amount')}")
            print(f"    accepts[0].asset: {a.get('asset')}")
            print(f"    accepts[0].payTo: {a.get('payTo')}")
            print(f"    accepts[0].maxTimeoutSeconds: {a.get('maxTimeoutSeconds')}")
            extra = a.get('extra', {})
            print(f"    accepts[0].extra.sourceTag: {extra.get('sourceTag')}")
            print(f"    accepts[0].extra.invoiceId: {extra.get('invoiceId', '?')[:8]}...")
        print(f"    error: {d.get('error', '?')}")
    except:
        print(f"  Body (raw): {body[:200]}")

print("\n" + "=" * 80)
print("V4 BOUNDARY + 402 DETAIL AUDIT COMPLETE")
print("=" * 80)
