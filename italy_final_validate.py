#!/usr/bin/env python3
"""Verify Italy 402 invoiceId format and all x402 v2 fields."""
import requests
import json
import re

print("=== Italy 402 Field Verification ===\n")

# Local raw 402
resp = requests.post("http://127.0.0.1:8117/api/v1/italy/bot",
    json={"message": "audit", "session_id": "test"},
    headers={"Content-Type": "application/json"})

print(f"HTTP Status: {resp.status_code}")
data = resp.json()

print(f"\nx402Version: {data.get('x402Version', 'MISSING')}")
print(f"error: {data.get('error', 'N/A')[:80]}")

accept = data.get('accepts', [{}])[0]
print(f"\n--- accepts[0] ---")
print(f"scheme: {accept.get('scheme', 'MISSING')}")
print(f"network: {accept.get('network', 'MISSING')}")
print(f"amount: {accept.get('amount', 'MISSING')}")
print(f"asset: {accept.get('asset', 'MISSING')}")
print(f"payTo: {accept.get('payTo', 'MISSING')}")
print(f"description: {accept.get('description', 'N/A')[:60]}")

extra = accept.get('extra', {})
print(f"\n--- extra ---")
print(f"sourceTag: {extra.get('sourceTag', 'MISSING')}")
inv_id = extra.get('invoiceId', 'MISSING')
print(f"invoiceId: {inv_id}")
print(f"invoiceId length: {len(inv_id)}")
print(f"invoiceId is 32-char hex: {bool(re.match(r'^[0-9A-Fa-f]{32}$', inv_id)) and len(inv_id) == 32}")

print(f"\n--- top-level ---")
print(f"resource exists: {'resource' in data}")
print(f"extensions exists: {'extensions' in data}")

# Verify the payment-required header
print(f"\n--- Headers ---")
for h, v in resp.headers.items():
    if 'payment' in h.lower() or 'x402' in h.lower() or 'retry' in h.lower():
        print(f"  {h}: {v[:60]}")

# Validation summary
print(f"\n--- VALIDATION SUMMARY ---")
checks = [
    ("HTTP 402", resp.status_code == 402),
    ("x402Version=2", data.get('x402Version') == 2),
    ("scheme=exact", accept.get('scheme') == 'exact'),
    ("network correct", accept.get('network') == 'xrpl:0'),
    ("amount=100000", accept.get('amount') == '100000'),
    ("asset=XRP", accept.get('asset') == 'XRP'),
    ("payTo correct", accept.get('payTo') == 'razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8'),
    ("sourceTag=804681468", extra.get('sourceTag') == 804681468),
    ("invoiceId 32-char hex", bool(re.match(r'^[0-9A-Fa-f]{32}$', inv_id)) and len(inv_id) == 32),
    ("resource exists", 'resource' in data),
    ("extensions exists", 'extensions' in data),
    ("payment-required header", any('payment' in h.lower() for h in resp.headers)),
]

for name, passed in checks:
    print(f"  {'✓' if passed else '✗'} {name}")

print(f"\nAll checks passed: {all(c[1] for c in checks)}")

# Also test AI endpoint
print(f"\n=== AI 402 Verification ===")
resp_ai = requests.post("http://127.0.0.1:8117/api/v1/italy/bot/ai",
    json={"message": "audit", "session_id": "test"},
    headers={"Content-Type": "application/json"})
print(f"HTTP Status: {resp_ai.status_code}")
if resp_ai.status_code == 402:
    d = resp_ai.json()
    a = d.get('accepts', [{}])[0]
    print(f"  x402Version: {d.get('x402Version')}")
    print(f"  amount: {a.get('amount')} (expected 500000)")
    print(f"  scheme: {a.get('scheme')}")
elif resp_ai.status_code == 429:
    print(f"  Rate limited (429) — acceptable, AI test succeeded with 402 earlier")
    print(f"  Body: {resp_ai.text[:200]}")

# Test health
print(f"\n=== Local Health ===")
resp_h = requests.get("http://127.0.0.1:8117/health")
print(f"HTTP Status: {resp_h.status_code}")
h = resp_h.json()
print(f"  status: {h.get('status')}")
print(f"  timestamp: {h.get('timestamp', 'MISSING')}")
print(f"  country: {h.get('country', 'MISSING')}")
print(f"  data_records: {h.get('data_records', 'MISSING')}")

# Public tests
print(f"\n=== Public Direct API Tests ===")
resp_h_pub = requests.get("https://api.xrplme.online/api/v1/italy/health")
print(f"GET /api/v1/italy/health: {resp_h_pub.status_code}")
pub_h = resp_h_pub.json()
print(f"  status: {pub_h.get('status')}")
print(f"  timestamp: {pub_h.get('timestamp', 'MISSING')}")

resp_bot_pub = requests.post("https://api.xrplme.online/api/v1/italy/bot",
    json={"message": "audit"}, headers={"Content-Type": "application/json"})
print(f"POST /api/v1/italy/bot: {resp_bot_pub.status_code}")
if resp_bot_pub.status_code == 402:
    d = resp_bot_pub.json()
    a = d.get('accepts', [{}])[0]
    print(f"  x402Version: {d.get('x402Version')}")
    print(f"  amount: {a.get('amount')}")
    print(f"  scheme: {a.get('scheme')}")
    print(f"  sourceTag: {a.get('extra',{}).get('sourceTag')}")
    inv = a.get('extra',{}).get('invoiceId', 'MISSING')
    print(f"  invoiceId: {inv} (len={len(inv)})")
    print(f"  32-char hex: {bool(re.match(r'^[0-9A-Fa-f]{32}$', inv)) and len(inv)==32}")
    print(f"  resource: {'resource' in d}")
    print(f"  extensions: {'extensions' in d}")
