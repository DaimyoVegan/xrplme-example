#!/usr/bin/env python3
"""Comprehensive verification of all 5 APAC countries."""
import json
import os
import requests

APAC = [
    ("Brunei", "brunei", 8111, "brunei"),
    ("Laos", "laos", 8112, "laos"),
    ("Myanmar", "myanmar", 8113, "myanmar"),
    ("Timor-Leste", "timor_leste", 8114, "timor-leste"),
    ("Papua New Guinea", "papua_new_guinea", 8115, "papua-new-guinea"),
]

DEDAK = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

print("=== APAC COUNTRIES VERIFICATION ===\n")

# 1. Health endpoints
print("1. HEALTH ENDPOINTS")
for display, module, port, slug in APAC:
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        d = r.json()
        records = d.get("data_records", 0)
        country = d.get("country", "?")
        updated = d.get("last_updated", "?")[:19]
        print(f"  {display}: HTTP {r.status_code}, records={records}, country={country}, updated={updated}")
    except Exception as e:
        print(f"  {display}: FAILED - {e}")

print()

# 2. Bot 402 responses
print("2. BOT ENDPOINTS (expect 402)")
for display, module, port, slug in APAC:
    try:
        r = requests.post(
            f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
            json={"message": "test", "session_id": "t"},
            timeout=5
        )
        if r.status_code == 402:
            d = r.json()
            p = d.get("accepts", [{}])[0]
            pt = p.get("payTo") or p.get("pay_to", "")
            amt = p.get("amount", "")
            inv = p.get("extra", {}).get("invoiceId", "") or p.get("invoiceId", "")
            is_ded = "YES" if pt == DEDAK else "NO"
            print(f"  {display}: HTTP 402, payTo={pt[:20]}..., amount={amt}, Ded={is_ded}, invoice={inv[:12]}")
        else:
            print(f"  {display}: HTTP {r.status_code} - UNEXPECTED")
    except Exception as e:
        print(f"  {display}: ERROR - {e}")

print()

# 3. Data files
print("3. DATA FILES")
for display, module, port, slug in APAC:
    path = f"/opt/xrplme/thoughts/api/{module}-agent-full/publication/latest_valid.json"
    try:
        size = os.path.getsize(path)
        with open(path) as f:
            d = json.load(f)
        records = d.get("record_count", 0)
        print(f"  {display}: {path} ({records} records, {size} bytes)")
    except Exception as e:
        print(f"  {display}: FILE NOT FOUND - {e}")

print()
print("=== ALL CHECKS COMPLETE ===")
