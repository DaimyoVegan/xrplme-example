#!/usr/bin/env python3
"""Compare 402 response structure across countries."""
import requests
import json

COUNTRIES = [
    ("thailand", 8085), ("vietnam", 8086), ("japan", 8087), ("korea", 8089),
    ("india", 8105), ("usa", 8091), ("canada", 8092), ("uk", 8094),
    ("uae", 8093), ("singapore", 8096), ("australia", 8097),
    ("philippines", 8095), ("germany", 8098), ("france", 8099),
    ("brazil", 8100), ("mexico", 8101), ("switzerland", 8102),
    ("netherlands", 8103), ("hong_kong", 8104), ("indonesia", 8107),
    ("macau", 8109), ("malaysia", 8106), ("newzealand", 8110),
    ("taiwan", 8108), ("brunei", 8111), ("laos", 8112),
    ("myanmar", 8113), ("timor-leste", 8114), ("papua-new-guinea", 8115),
    ("italy", 8117),
]

print(f"{'Country':<22} {'x402Ver':<8} {'amount':<10} {'asset':<6} {'payTo[:20]':<22} {'has_res':<8} {'has_ext':<8} {'hdr':<8}")
print("="*110)

for slug, port in COUNTRIES:
    try:
        r = requests.post(
            f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
            json={"message": "audit", "session_id": "audit"},
            timeout=10,
        )
        try:
            d = r.json()
        except:
            d = {}
        
        ver = d.get("x402Version", "MISSING")
        accepts = d.get("accepts", [])
        amount = "N/A"
        asset = "N/A"
        payto = "N/A"
        if accepts:
            a = accepts[0]
            amount = a.get("amount", "N/A")
            asset = a.get("asset", "N/A")
            payto = (a.get("payTo", "N/A") or "N/A")[:20]
        
        has_res = "resource" in d
        has_ext = "extensions" in d
        headers = dict(r.headers)
        has_pay_hdr = "payment-required" in headers or "Payment-Required" in headers
        
        print(f"{slug:<22} {str(ver):<8} {str(amount):<10} {str(asset):<6} {str(payto):<22} {str(has_res):<8} {str(has_ext):<8} {str(has_pay_hdr):<8}")
    except Exception as e:
        print(f"{slug:<22} ERROR: {str(e)[:40]}")
