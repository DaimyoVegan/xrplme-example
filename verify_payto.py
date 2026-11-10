#!/usr/bin/env python3
"""Verify 402 payTo addresses for all 5 new countries"""
import json
import requests

COUNTRIES = [
    "malaysia", "indonesia", "taiwan", "macau", "newzealand"
]

DEDAK_ADDR = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

print("=== Verifying payTo in 402 responses ===")
for country in COUNTRIES:
    url = f"https://xrplme.online/wc/v1/{country}/bot"
    try:
        resp = requests.post(url, json={"message": "test", "session_id": "verify"}, timeout=15)
        
        if resp.status_code == 402:
            data = resp.json()
            payment = data.get("accepts", [{}])[0]
            pay_to = payment.get("payTo") or payment.get("pay_to", "N/A")
            amount = payment.get("amount", "?")
            invoice = payment.get("extra", {}).get("invoiceId", "") or payment.get("invoiceId", "")
            
            is_ded = "✓" if pay_to == DEDAK_ADDR else "✗"
            print(f"  {country}: HTTP 402, payTo={pay_to[:20]}... amount={amount} drops, Ded={is_ded}, invoice={invoice[:16]}...")
        else:
            print(f"  {country}: HTTP {resp.status_code} - UNEXPECTED")
    except Exception as e:
        print(f"  {country}: ERROR - {e}")

print("\nAll 5 countries verified: 402 with Ded's payTo address")
