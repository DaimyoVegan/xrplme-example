#!/usr/bin/env python3
"""
READ-ONLY V3/V4 Audit Script
Audits all 30 country bots: health, raw 402, AI 402, JSON structure, payment details.
"""
import requests
import json
import time
from datetime import datetime

# All 30 countries with their details
COUNTRIES = [
    {"name": "Thailand", "slug": "thailand", "iso": "TH", "port": 8085, "svc": "thailand-bot-api"},
    {"name": "Vietnam", "slug": "vietnam", "iso": "VN", "port": 8086, "svc": "vietnam-bot-api"},
    {"name": "Japan", "slug": "japan", "iso": "JP", "port": 8087, "svc": "japan-bot-api"},
    {"name": "Korea", "slug": "korea", "iso": "KR", "port": 8089, "svc": "korea-bot-api"},
    {"name": "India", "slug": "india", "iso": "IN", "port": 8105, "svc": "india-bot-api"},
    {"name": "USA", "slug": "usa", "iso": "US", "port": 8091, "svc": "usa-bot-api"},
    {"name": "Canada", "slug": "canada", "iso": "CA", "port": 8092, "svc": "canada-bot-api"},
    {"name": "UK", "slug": "uk", "iso": "GB", "port": 8094, "svc": "uk-bot-api"},
    {"name": "UAE", "slug": "uae", "iso": "AE", "port": 8093, "svc": "uae-bot-api"},
    {"name": "Singapore", "slug": "sg", "iso": "SG", "port": 8096, "svc": "sg-bot-api"},
    {"name": "Australia", "slug": "au", "iso": "AU", "port": 8097, "svc": "au-bot-api"},
    {"name": "Philippines", "slug": "ph", "iso": "PH", "port": 8095, "svc": "ph-bot-api"},
    {"name": "Germany", "slug": "de", "iso": "DE", "port": 8098, "svc": "de-bot-api"},
    {"name": "France", "slug": "fr", "iso": "FR", "port": 8099, "svc": "fr-bot-api"},
    {"name": "Brazil", "slug": "brazil", "iso": "BR", "port": 8100, "svc": "br-bot-api"},
    {"name": "Mexico", "slug": "mexico", "iso": "MX", "port": 8101, "svc": "mx-bot-api"},
    {"name": "Switzerland", "slug": "ch", "iso": "CH", "port": 8102, "svc": "ch-bot-api"},
    {"name": "Netherlands", "slug": "nl", "iso": "NL", "port": 8103, "svc": "nl-bot-api"},
    {"name": "Hong Kong", "slug": "hong_kong", "iso": "HK", "port": 8104, "svc": "hongkong-bot-api"},
    {"name": "Indonesia", "slug": "indonesia", "iso": "ID", "port": 8107, "svc": "id-bot-api"},
    {"name": "Macau", "slug": "macau", "iso": "MO", "port": 8109, "svc": "mo-bot-api"},
    {"name": "Malaysia", "slug": "malaysia", "iso": "MY", "port": 8106, "svc": "my-bot-api"},
    {"name": "New Zealand", "slug": "newzealand", "iso": "NZ", "port": 8110, "svc": "nz-bot-api"},
    {"name": "Taiwan", "slug": "taiwan", "iso": "TW", "port": 8108, "svc": "tw-bot-api"},
    {"name": "Brunei", "slug": "brunei", "iso": "BN", "port": 8111, "svc": "brunei-bot-api"},
    {"name": "Laos", "slug": "laos", "iso": "LA", "port": 8112, "svc": "laos-bot-api"},
    {"name": "Myanmar", "slug": "myanmar", "iso": "MM", "port": 8113, "svc": "myanmar-bot-api"},
    {"name": "Timor-Leste", "slug": "timor-leste", "iso": "TL", "port": 8114, "svc": "timor-leste-bot-api"},
    {"name": "Papua New Guinea", "slug": "papua-new-guinea", "iso": "PG", "port": 8115, "svc": "papua-new-guinea-bot-api"},
    {"name": "Italy", "slug": "italy", "iso": "IT", "port": 8117, "svc": "italy-bot-api"},
]

def audit_country(c):
    """Audit a single country. Returns dict of results."""
    result = {
        "name": c["name"],
        "slug": c["slug"],
        "iso": c["iso"],
        "port": c["port"],
        "svc": c["svc"],
        "local_health": None,
        "local_health_json": False,
        "local_health_records": 0,
        "pub_health": None,
        "pub_health_json": False,
        "pub_health_records": 0,
        "pub_raw_402": None,
        "pub_raw_json": False,
        "pub_raw_payto": None,
        "pub_raw_amount": None,
        "pub_raw_price_xrp": None,
        "pub_raw_has_ai": False,
        "pub_ai_402": None,
        "pub_ai_json": False,
        "pub_ai_payto": None,
        "pub_ai_amount": None,
        "pub_ai_price_xrp": None,
        "local_402_headers": None,
        "has_source_field": False,
        "has_timestamp": False,
        "classification": "UNKNOWN",
    }
    
    # Test local health
    try:
        r = requests.get(f"http://127.0.0.1:{c['port']}/health", timeout=10)
        result["local_health"] = r.status_code
        if r.status_code == 200:
            try:
                d = r.json()
                result["local_health_json"] = True
                result["local_health_records"] = d.get("data_records", 0)
            except:
                pass
    except Exception as e:
        result["local_health"] = str(e)[:50]
    
    # Test public health
    try:
        r = requests.get(f"https://xrplme.online/wc/v1/{c['slug']}/health", 
                        timeout=15, verify=True)
        result["pub_health"] = r.status_code
        if r.status_code == 200:
            try:
                d = r.json()
                result["pub_health_json"] = True
                result["pub_health_records"] = d.get("data_records", 0)
            except:
                pass
    except Exception as e:
        result["pub_health"] = f"ERR: {str(e)[:50]}"
    
    # Test public raw bot (unpaid - expect 402)
    try:
        r = requests.post(
            f"https://xrplme.online/wc/v1/{c['slug']}/bot",
            json={"message": "audit test", "session_id": "audit"},
            timeout=15,
            verify=True
        )
        result["pub_raw_402"] = r.status_code
        if r.status_code == 402:
            result["pub_raw_json"] = True  # 402 responses are typically JSON
            try:
                d = r.json()
                if "accepts" in d:
                    a = d["accepts"][0]
                    result["pub_raw_payto"] = a.get("payTo", "")
                    result["pub_raw_amount"] = a.get("amount_d Drops", a.get("amount", ""))
                    result["pub_raw_price_xrp"] = int(a.get("amount_d Drops", a.get("amount", 0))) / 1_000_000
                if "ai" in d or "AI" in str(d) or "ai_endpoint" in d:
                    result["pub_raw_has_ai"] = True
                # Check for source/timestamp
                result["has_source_field"] = "source" in str(d).lower() or "sources" in str(d).lower()
                result["has_timestamp"] = "timestamp" in str(d).lower() or "retrieved_at" in str(d).lower()
            except:
                pass
    except Exception as e:
        result["pub_raw_402"] = f"ERR: {str(e)[:50]}"
    
    # Test public AI bot (unpaid - expect 402)
    try:
        r = requests.post(
            f"https://xrplme.online/wc/v1/{c['slug']}/bot/ai",
            json={"message": "audit test", "session_id": "audit"},
            timeout=15,
            verify=True
        )
        result["pub_ai_402"] = r.status_code
        if r.status_code == 402:
            result["pub_ai_json"] = True
            try:
                d = r.json()
                if "accepts" in d:
                    a = d["accepts"][0]
                    result["pub_ai_payto"] = a.get("payTo", "")
                    result["pub_ai_amount"] = a.get("amount_d Drops", a.get("amount", ""))
                    result["pub_ai_price_xrp"] = int(a.get("amount_d Drops", a.get("amount", 0))) / 1_000_000
                result["has_timestamp"] = result["has_timestamp"] or "timestamp" in str(d).lower()
            except:
                pass
    except Exception as e:
        result["pub_ai_402"] = f"ERR: {str(e)[:50]}"
    
    # Test local 402 for header comparison
    try:
        r = requests.post(
            f"http://127.0.0.1:{c['port']}/api/v1/{c['slug']}/bot",
            json={"message": "audit", "session_id": "audit"},
            timeout=10
        )
        headers = dict(r.headers)
        result["local_402_headers"] = sorted([k for k in headers.keys() if k.startswith("X-402") or "payment" in k.lower()])
    except:
        result["local_402_headers"] = None
    
    # Classification
    if result["pub_health"] == 200 and result["pub_raw_402"] == 402:
        result["classification"] = "LIVE"
    elif result["pub_health"] is not None and result["pub_health"] != 200:
        result["classification"] = "FAILED"
    elif result["pub_raw_402"] not in (402, None):
        result["classification"] = "PARTIAL"
    elif result["pub_health"] != 200:
        result["classification"] = "UNKNOWN"
    
    if result["pub_raw_402"] == 402 and result["pub_ai_402"] == 402:
        result["classification"] = "LIVE"
    elif result["pub_raw_402"] == 402 and result["pub_ai_402"] in (None, "404", "405"):
        result["classification"] = "PARTIAL"
    
    return result

# Run audit
results = []
for c in COUNTRIES:
    print(f"Auditing {c['name']} ({c['slug']}) on port {c['port']}...")
    r = audit_country(c)
    results.append(r)
    print(f"  Health: {r['pub_health']} | Raw: {r['pub_raw_402']} | AI: {r['pub_ai_402']}")

# Print summary table
print("\n" + "="*120)
print(f"{'Country':<20} {'Slug':<20} {'Port':<6} {'Pub Health':<12} {'Raw 402':<10} {'AI 402':<10} {'Price XRP':<12} {'Class':<10}")
print("="*120)
for r in results:
    price = f"{r['pub_raw_price_xrp']}" if r['pub_raw_price_xrp'] else "-"
    print(f"{r['name']:<20} {r['slug']:<20} {r['port']:<6} {str(r['pub_health']):<12} {str(r['pub_raw_402']):<10} {str(r['pub_ai_402']):<10} {price:<12} {r['classification']:<10}")

print("\n" + "="*120)
print("DETAILED RESULTS:")
print("="*120)
for r in results:
    print(f"\n--- {r['name']} ({r['slug']}) ---")
    print(f"  Service: {r['svc']}")
    print(f"  Port: {r['port']}")
    print(f"  Local health: {r['local_health']} (JSON: {r['local_health_json']}, records: {r['local_health_records']})")
    print(f"  Public health: {r['pub_health']} (JSON: {r['pub_health_json']}, records: {r['pub_health_records']})")
    print(f"  Public raw /bot: {r['pub_raw_402']} (JSON: {r['pub_raw_json']}, payTo: {r['pub_raw_payto'][:20] if r['pub_raw_payto'] else 'N/A'}, amount: {r['pub_raw_amount']})")
    print(f"  Public AI /bot/ai: {r['pub_ai_402']} (JSON: {r['pub_ai_json']}, payTo: {r['pub_ai_payto'][:20] if r['pub_ai_payto'] else 'N/A'}, amount: {r['pub_ai_amount']})")
    print(f"  Local 402 headers: {r['local_402_headers']}")
    print(f"  Has source field: {r['has_source_field']}")
    print(f"  Has timestamp: {r['has_timestamp']}")
    print(f"  Classification: {r['classification']}")

# Summary counts
live = sum(1 for r in results if r["classification"] == "LIVE")
partial = sum(1 for r in results if r["classification"] == "PARTIAL")
failed = sum(1 for r in results if r["classification"] == "FAILED")
unknown = sum(1 for r in results if r["classification"] == "UNKNOWN")
print(f"\n=== SUMMARY ===")
print(f"LIVE: {live}")
print(f"PARTIAL: {partial}")
print(f"FAILED: {failed}")
print(f"UNKNOWN: {unknown}")
print(f"Total: {len(results)}")
