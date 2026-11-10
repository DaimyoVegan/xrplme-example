#!/usr/bin/env python3
"""Verify 402 responses for all 5 new countries - runs on VPS"""
import json
import requests

# The 5 new countries with their bot ports
COUNTRIES = [
    ("Malaysia", "malaysia", 8106, "my"),
    ("Indonesia", "indonesia", 8107, "id"),
    ("Taiwan", "taiwan", 8108, "tw"),
    ("Macau", "macau", 8109, "mo"),
    ("New Zealand", "newzealand", 8110, "nz"),
]

DEDAK_ADDR = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

print("=== Public URL 402 verification ===")
for display, country, port, slug in COUNTRIES:
    url = f"https://xrplme.online/wc/v1/{slug}/bot"
    try:
        resp = requests.post(url, json={"message": "test", "session_id": "verify"}, timeout=10)
        
        if resp.status_code == 402:
            data = resp.json()
            payment = data.get("accepts", [{}])[0]
            pay_to = payment.get("payTo") or payment.get("pay_to", "N/A")
            amount = payment.get("amount", "?")
            invoice = payment.get("extra", {}).get("invoiceId", "") or payment.get("invoiceId", "")
            
            is_ded = pay_to == DEDAK_ADDR
            print(f"  {display}: HTTP 402, payTo={pay_to[:25]}..., amount={amount} drops, Ded={is_ded}")
        else:
            print(f"  {display}: HTTP {resp.status_code} - UNEXPECTED")
    except Exception as e:
        print(f"  {display}: ERROR - {e}")

print("\n=== Backend health verification ===")
for display, country, port, slug in COUNTRIES:
    # Check health via backend directly
    health_url = f"http://127.0.0.1:{port}/health"
    try:
        resp = requests.get(health_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  {display}: HEALTHY, data_records={data.get('data_records')}, last_updated={data.get('last_updated', '?')[:19]}")
        else:
            print(f"  {display}: Health check FAILED (HTTP {resp.status_code})")
    except Exception as e:
        print(f"  {display}: ERROR - {e}")

print("\n=== Data file content sample ===")
for display, country, port, slug in COUNTRIES:
    datafile = f"/opt/xrplme/thoughts/api/{slug}-agent-full/publication/latest_valid.json"
    try:
        with open(datafile, "r") as f:
            data = json.load(f)
        
        # Show sample facts
        sample_facts = []
        for r in data.get("records", [])[:3]:
            facts = r.get("facts_extracted", [])
            for fact in facts[:1]:
                if len(fact) > 20:
                    sample_facts.append(fact[:100])
                    break
        
        print(f"  {display}: {data.get('record_count', '?')} records, {len(data.get('records', []))} actual")
        for sf in sample_facts[:2]:
            print(f"    -> {sf}")
    except Exception as e:
        print(f"  {display}: ERROR - {e}")
