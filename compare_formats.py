#!/usr/bin/env python3
"""Compare 402 + health structure: Italy (new format) vs Thailand (reference)"""
import requests
import json

def test(port, slug, endpoint):
    url = f"http://127.0.0.1:{port}/api/v1/{slug}/{endpoint}"
    r = requests.post(url, json={"message": "audit", "session_id": "audit"}, timeout=10)
    return r.status_code, dict(r.headers), r.json()

print("=== Thailand (reference) raw 402 ===")
code, hdrs, d = test(8085, "thailand", "bot")
print(f"Status: {code}")
print(f"x402Version: {d.get('x402Version', 'MISSING')}")
a = d.get("accepts", [{}])[0]
print(f"  amount: {a.get('amount', 'N/A')}")
print(f"  asset: {a.get('asset', 'N/A')}")
print(f"  payTo: {a.get('payTo', 'N/A')[:30]}")
print(f"  scheme: {a.get('scheme', 'N/A')}")
print(f"  sourceTag: {a.get('extra', {}).get('sourceTag', 'MISSING')}")
print(f"  invoiceId: {a.get('extra', {}).get('invoiceId', 'MISSING')}")
print(f"  resource: {'resource' in d}")
print(f"  extensions: {'extensions' in d}")
print(f"  payment-required header: {'payment-required' in hdrs}")
print(f"  Headers: {sorted([k for k in hdrs if 'payment' in k.lower() or 'x402' in k.lower()])}")

print("\n=== Thailand AI 402 ===")
code, hdrs, d = test(8085, "thailand", "bot/ai")
a = d.get("accepts", [{}])[0]
print(f"Status: {code}")
print(f"  amount: {a.get('amount', 'N/A')}")
print(f"  scheme: {a.get('scheme', 'N/A')}")
print(f"  sourceTag: {a.get('extra', {}).get('sourceTag', 'MISSING')}")
print(f"  invoiceId: {a.get('extra', {}).get('invoiceId', 'MISSING')}")
print(f"  resource: {'resource' in d}")
print(f"  extensions: {'extensions' in d}")

print("\n=== Thailand health ===")
r = requests.get("http://127.0.0.1:8085/health", timeout=10)
d = r.json()
print(f"Status: {r.status_code}")
print(f"Fields: {sorted(d.keys())}")
print(f"  data_records: {d.get('data_records')}")
print(f"  has timestamp: {'timestamp' in d}")
print(f"  has last_updated: {'last_updated' in d}")

print("\n=== Italy (new format) raw 402 ===")
code, hdrs, d = test(8117, "italy", "bot")
print(f"Status: {code}")
print(f"x402Version: {d.get('x402Version', 'MISSING')}")
a = d.get("accepts", [{}])[0]
print(f"  amount: {a.get('amount', 'N/A')}")
print(f"  scheme: {a.get('scheme', 'N/A')}")
print(f"  sourceTag: {a.get('extra', {}).get('sourceTag', 'MISSING')}")
print(f"  invoiceId: {a.get('extra', {}).get('invoiceId', 'MISSING')}")
print(f"  country: {a.get('extra', {}).get('country', 'MISSING')}")
print(f"  resource: {'resource' in d}")
print(f"  extensions: {'extensions' in d}")
print(f"  message: {d.get('message', 'N/A')[:60]}")
print(f"  Headers: {sorted([k for k in hdrs if 'payment' in k.lower() or 'x402' in k.lower()])}")

print("\n=== Italy health ===")
r = requests.get("http://127.0.0.1:8117/health", timeout=10)
d = r.json()
print(f"Status: {r.status_code}")
print(f"Fields: {sorted(d.keys())}")
print(f"  data_records: {d.get('data_records')}")
print(f"  has timestamp: {'timestamp' in d}")
print(f"  has last_updated: {'last_updated' in d}")
print(f"  has sources: {'sources' in d}")
print(f"  sources: {d.get('sources', [])}")
