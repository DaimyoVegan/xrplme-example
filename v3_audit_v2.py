#!/usr/bin/env python3
"""
READ-ONLY V3 Audit - Round 2
Uses correct full-name slugs for all 30 countries.
"""
import requests
import json
import time

# All 30 countries with full-name slugs matching nginx routes
COUNTRIES = [
    {"name": "Thailand", "slug": "thailand", "port": 8085, "svc": "thailand-bot-api"},
    {"name": "Vietnam", "slug": "vietnam", "port": 8086, "svc": "vietnam-bot-api"},
    {"name": "Japan", "slug": "japan", "port": 8087, "svc": "japan-bot-api"},
    {"name": "Korea", "slug": "korea", "port": 8089, "svc": "korea-bot-api"},
    {"name": "India", "slug": "india", "port": 8105, "svc": "india-bot-api"},
    {"name": "USA", "slug": "usa", "port": 8091, "svc": "usa-bot-api"},
    {"name": "Canada", "slug": "canada", "port": 8092, "svc": "canada-bot-api"},
    {"name": "UK", "slug": "uk", "port": 8094, "svc": "uk-bot-api"},
    {"name": "UAE", "slug": "uae", "port": 8093, "svc": "uae-bot-api"},
    {"name": "Singapore", "slug": "singapore", "port": 8096, "svc": "sg-bot-api"},
    {"name": "Australia", "slug": "australia", "port": 8097, "svc": "au-bot-api"},
    {"name": "Philippines", "slug": "philippines", "port": 8095, "svc": "ph-bot-api"},
    {"name": "Germany", "slug": "germany", "port": 8098, "svc": "de-bot-api"},
    {"name": "France", "slug": "france", "port": 8099, "svc": "fr-bot-api"},
    {"name": "Brazil", "slug": "brazil", "port": 8100, "svc": "br-bot-api"},
    {"name": "Mexico", "slug": "mexico", "port": 8101, "svc": "mx-bot-api"},
    {"name": "Switzerland", "slug": "switzerland", "port": 8102, "svc": "ch-bot-api"},
    {"name": "Netherlands", "slug": "netherlands", "port": 8103, "svc": "nl-bot-api"},
    {"name": "Hong Kong", "slug": "hong_kong", "port": 8104, "svc": "hongkong-bot-api"},
    {"name": "Indonesia", "slug": "indonesia", "port": 8107, "svc": "id-bot-api"},
    {"name": "Macau", "slug": "macau", "port": 8109, "svc": "mo-bot-api"},
    {"name": "Malaysia", "slug": "malaysia", "port": 8106, "svc": "my-bot-api"},
    {"name": "New Zealand", "slug": "newzealand", "port": 8110, "svc": "nz-bot-api"},
    {"name": "Taiwan", "slug": "taiwan", "port": 8108, "svc": "tw-bot-api"},
    {"name": "Brunei", "slug": "brunei", "port": 8111, "svc": "brunei-bot-api"},
    {"name": "Laos", "slug": "laos", "port": 8112, "svc": "laos-bot-api"},
    {"name": "Myanmar", "slug": "myanmar", "port": 8113, "svc": "myanmar-bot-api"},
    {"name": "Timor-Leste", "slug": "timor-leste", "port": 8114, "svc": "timor-leste-bot-api"},
    {"name": "Papua New Guinea", "slug": "papua-new-guinea", "port": 8115, "svc": "papua-new-guinea-bot-api"},
    {"name": "Italy", "slug": "italy", "port": 8117, "svc": "italy-bot-api"},
]

def test_endpoint(method, url, json_body=None, timeout=10):
    """Test an endpoint and return (status_code, json_parseable, response_dict, headers)."""
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        else:
            r = requests.post(url, json=json_body, timeout=timeout)
        try:
            d = r.json()
        except:
            d = None
        return r.status_code, d is not None, d, dict(r.headers)
    except Exception as e:
        return None, False, {"error": str(e)[:60]}, {}

def audit_country(c):
    result = {
        "name": c["name"], "slug": c["slug"], "port": c["port"], "svc": c["svc"],
        "pub_health": None, "pub_health_json": False, "health_records": 0,
        "health_has_timestamp": False, "health_has_last_updated": False,
        "pub_raw_402": None, "pub_raw_json": False, "raw_payto": "", "raw_amount": None, "raw_price_xrp": None,
        "raw_invoice_id": "", "raw_has_source_tag": False,
        "pub_ai_402": None, "pub_ai_json": False, "ai_payto": "", "ai_amount": None, "ai_price_xrp": None, "ai_invoice_id": "",
        "x402_version": None, "has_resource": False, "resource_url": "",
        "has_payment_required_header": False,
        "classification": "UNKNOWN",
    }
    
    base = f"https://xrplme.online/wc/v1/{c['slug']}"
    
    # Health
    code, is_json, d, hdrs = test_endpoint("GET", f"{base}/health")
    result["pub_health"] = code
    result["pub_health_json"] = is_json
    if d and isinstance(d, dict):
        result["health_records"] = d.get("data_records", 0)
        result["health_has_timestamp"] = "timestamp" in d
        result["health_has_last_updated"] = "last_updated" in d
    
    # Raw bot (unpaid - expect 402)
    code, is_json, d, hdrs = test_endpoint("POST", f"{base}/bot", {"message": "audit", "session_id": "audit"})
    result["pub_raw_402"] = code
    result["pub_raw_json"] = is_json
    if d and isinstance(d, dict):
        result["x402_version"] = d.get("x402Version")
        result["has_resource"] = "resource" in d
        result["resource_url"] = d.get("resource", {}).get("url", "")
        if "accepts" in d and len(d["accepts"]) > 0:
            a = d["accepts"][0]
            result["raw_payto"] = a.get("payTo", "")
            result["raw_amount"] = a.get("amount", "")
            if a.get("amount"):
                result["raw_price_xrp"] = int(a["amount"]) / 1_000_000
            result["raw_invoice_id"] = a.get("extra", {}).get("invoiceId", "")
            result["raw_has_source_tag"] = "sourceTag" in a.get("extra", {})
    
    # AI bot (unpaid - expect 402)
    code, is_json, d, hdrs = test_endpoint("POST", f"{base}/bot/ai", {"message": "audit", "session_id": "audit"})
    result["pub_ai_402"] = code
    result["pub_ai_json"] = is_json
    if d and isinstance(d, dict):
        if "accepts" in d and len(d["accepts"]) > 0:
            a = d["accepts"][0]
            result["ai_payto"] = a.get("payTo", "")
            result["ai_amount"] = a.get("amount", "")
            if a.get("amount"):
                result["ai_price_xrp"] = int(a["amount"]) / 1_000_000
            result["ai_invoice_id"] = a.get("extra", {}).get("invoiceId", "")
       
    # Check payment-required header
    code, is_json, d, hdrs = test_endpoint("POST", f"{base}/bot", {"message": "audit", "session_id": "audit"})
    result["has_payment_required_header"] = "payment-required" in hdrs or "Payment-Required" in hdrs or "X-402" in str(hdrs.keys()) or "payment_required" in str(hdrs.keys())
    
    # Classification
    raw_ok = result["pub_raw_402"] == 402
    ai_ok = result["pub_ai_402"] == 402
    health_ok = result["pub_health"] == 200
    if health_ok and raw_ok and ai_ok:
        result["classification"] = "LIVE"
    elif health_ok and raw_ok and not ai_ok:
        result["classification"] = "PARTIAL"
    elif health_ok and not raw_ok:
        result["classification"] = "PARTIAL"
    elif not health_ok:
        result["classification"] = "FAILED"
    
    time.sleep(0.1)  # Rate limit avoidance
    return result

# Run audit
results = []
for c in COUNTRIES:
    r = audit_country(c)
    results.append(r)
    print(f"{r['name']:<22} health={r['pub_health']} raw={r['pub_raw_402']} ai={r['pub_ai_402']} price={r['raw_price_xrp']} class={r['classification']}")

# Summary
print(f"\n=== SUMMARY ===")
live = sum(1 for r in results if r["classification"] == "LIVE")
partial = sum(1 for r in results if r["classification"] == "PARTIAL")
failed = sum(1 for r in results if r["classification"] == "FAILED")
print(f"LIVE: {live}/30")
print(f"PARTIAL: {partial}/30")
print(f"FAILED: {failed}/30")
print(f"Total: {len(results)}")

# Inconsistency report
print("\n=== INCONSISTENCIES ===")
print("Countries with AI 429 (rate limited):")
for r in results:
    if r["pub_ai_402"] == 429:
        print(f"  {r['slug']}")
print("\nCountries with AI ERR (connection):")
for r in results:
    if r["pub_ai_402"] is None:
        print(f"  {r['slug']}")

print("\nCountries with raw price != 0.1 XRP:")
for r in results:
    if r["raw_price_xrp"] != 0.1:
        print(f"  {r['slug']}: {r['raw_price_xrp']}")

print("\nCountries without health timestamp:")
for r in results:
    if not r["health_has_timestamp"]:
        print(f"  {r['slug']}")

# Save results
with open("/tmp/v3_audit_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to /tmp/v3_audit_results.json")
