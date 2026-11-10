#!/usr/bin/env python3
"""Check website for broken links and V4 mentions."""
import requests
import re
from urllib.parse import urljoin

BASE = "https://xrplme.online"

# Check key pages
pages = [
    "/", "/agents", "/agents.html", "/api-docs.html",
    "/docs-products.html", "/agents-draft.html", "/homepage-test.html",
    "/analytics.html", "/v3test.html", "/test-v3.html", "/status.html",
    "/thailand-bot.html", "/japan.html", "/vietnam.html",
    "/directory_site_index.html",
]

print("=== Website Page Status ===")
for page in pages:
    try:
        r = requests.get(f"{BASE}{page}", timeout=5, verify=False)
        print(f"  {page:<30} HTTP {r.status_code}  size={len(r.content)}B")
        
        # Check for V4 mentions
        if r.status_code == 200:
            lower = r.text.lower()
            checks = []
            if "v4" in lower or "evidence layer" in lower:
                checks.append("V4")
            if "mpp" in lower:
                checks.append("MPP")
            if "stripe" in lower:
                checks.append("STRIPE")
            if "ripple" in lower:
                checks.append("RIPPLE")
            if "official partner" in lower:
                checks.append("PARTNER")
            if "sanctions" in lower and "screen" in lower:
                checks.append("SANCTIONS")
            if "real-time" in lower and ("stock" in lower or "market" in lower):
                checks.append("REALTIME-CLAIM")
            if "compliance" in lower and ("clear" in lower or "approval" in lower):
                checks.append("COMPLIANCE-CLAIM")
            if checks:
                print(f"    Flags: {', '.join(checks)}")
    except Exception as e:
        print(f"  {page:<30} ERROR: {str(e)[:40]}")

# Check api-docs.html for country coverage
print("\n=== api-docs.html country dropdown ===")
try:
    r = requests.get(f"{BASE}/api-docs.html", timeout=10, verify=False)
    options = re.findall(r'value="([a-z_-]+)"', r.text)
    print(f"  Countries in dropdown: {len(options)}")
    for opt in sorted(options):
        print(f"    {opt}")
except Exception as e:
    print(f"  Error: {e}")

# Check /agents page content
print("\n=== /agents page analysis ===")
try:
    r = requests.get(f"{BASE}/agents", timeout=10, verify=False)
    if r.status_code == 200:
        # Find any x402/402 mentions
        text = r.text
        if "402" in text:
            print("  Contains '402': YES")
        if "pay" in text.lower():
            idx = text.lower().find("pay")
            print(f"  Pay mention: ...{text[max(0,idx-20):idx+40]}...")
        if "0.1" in text:
            print("  Contains '0.1': YES (potential price mention)")
        if "0.5" in text:
            print("  Contains '0.5': YES (potential price mention)")
except Exception as e:
    print(f"  Error: {e}")

# Check docs-products.html for pricing claims
print("\n=== /docs-products.html analysis ===")
try:
    r = requests.get(f"{BASE}/docs-products.html", timeout=10, verify=False)
    if r.status_code == 200:
        lower = r.text.lower()
        # Find price mentions
        prices = re.findall(r'0\.\d+\s*xrp', lower)
        print(f"  Price mentions: {prices}")
        
        # Check for unsupported claims
        claims = []
        if "real-time" in lower and ("stock" in lower or "market data" in lower):
            claims.append("real-time stock/market claims")
        if "official" in lower and ("partner" in lower or "integration" in lower):
            claims.append("official partner claims")
        if "sanctions" in lower:
            claims.append("sanctions screening")
        if "compliance" in lower and ("clear" in lower or "approved" in lower):
            claims.append("compliance clearance claims")
        if claims:
            print(f"  Unsupported claims found: {claims}")
        else:
            print("  No unsupported claims detected")
        
        # Check for V4/agents mentions
        if "v4" in lower:
            print("  V4 mentioned: YES")
        if "evidence" in lower:
            print("  Evidence mentioned: YES")
        if "mpp" in lower:
            print("  MPP mentioned: YES")
except Exception as e:
    print(f"  Error: {e}")
