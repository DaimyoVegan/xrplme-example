#!/usr/bin/env python3
"""Final verification of all country endpoints."""
import requests

COUNTRIES = [
    ("Australia", "australia", 8097),
    ("Brazil", "brazil", 8100),
    ("Brunei", "brunei", 8111),
    ("Canada", "canada", 8092),
    ("Switzerland", "switzerland", 8102),
    ("Germany", "germany", 8098),
    ("France", "france", 8099),
    ("Hong Kong", "hong_kong", 8104),
    ("Indonesia", "indonesia", 8107),
    ("India", "india", 8105),
    ("Italy", "italy", 8117),
    ("Japan", "japan", 8087),
    ("Korea", "korea", 8089),
    ("Laos", "laos", 8112),
    ("Macau", "macau", 8109),
    ("Mexico", "mexico", 8101),
    ("Malaysia", "malaysia", 6106),
    ("Myanmar", "myanmar", 8113),
    ("Netherlands", "netherlands", 8103),
    ("New Zealand", "newzealand", 8110),
    ("Papua New Guinea", "papua-new-guinea", 8115),
    ("Philippines", "philippines", 8096),
    ("Singapore", "singapore", 8095),
    ("Taiwan", "taiwan", 8108),
    ("Thailand", "thailand", 8085),
    ("Timor-Leste", "timor-leste", 8114),
    ("UAE", "uae", 8093),
    ("UK", "uk", 8094),
    ("USA", "usa", 8091),
    ("Vietnam", "vietnam", 8086),
]

X402_COLLECTOR = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

print("=" * 80)
print("COMPLETE COUNTRY BOT VERIFICATION")
print("=" * 80)

health_ok = 0
bot_ok = 0
total = 0

for display, slug, port in COUNTRIES:
    total += 1
    # Check health endpoint
    h_url = f"https://xrplme.online/wc/v1/{slug}/health"
    try:
        h_resp = requests.get(h_url, timeout=10)
        h_status = h_resp.status_code
    except:
        h_status = 0
    
    # Check 402 bot endpoint
    b_url = f"https://xrplme.online/wc/v1/{slug}/bot"
    try:
        b_resp = requests.post(b_url, json={"message": "test", "session_id": "verify"}, timeout=10)
        b_status = b_resp.status_code
        if b_status == 402:
            try:
                b_data = b_resp.json()
                pay_to = b_data.get("accepts", [{}])[0].get("payTo", "")
                amount = b_data.get("accepts", [{}])[0].get("amount", "")
                ded_ok = "✅" if pay_to == X402_COLLECTOR else "❌"
                bot_ok += 1
                b_info = f"402 {ded_ok} payTo={pay_to[:20]}... amount={amount}"
            except:
                b_info = f"402 (no JSON)"
                bot_ok += 1
        else:
            b_info = f"HTTP {b_status}"
    except Exception as e:
        b_info = f"ERROR: {str(e)[:50]}"
    
    if h_status == 200:
        health_ok += 1
    
    h_ok = "✅" if h_status == 200 else "❌"
    print(f"  {h_ok} {display} ({slug}, port {port}):")
    print(f"    Health: {h_status} | Bot: {b_info}")

print(f"\n{'='*80}")
print(f"RESULTS: {health_ok}/{total} health OK, {bot_ok}/{total} 402 OK")
print(f"{'='*80}")
