#!/usr/bin/env python3
"""
COMPLETE V3 READ-ONLY AUDIT
Run on VPS: /home/xrpladmin/thailand_bot_venv/bin/python /tmp/v3_audit_full.py
Gets ALL information from the VPS — nothing from the tablet.
"""
import requests
import json
import time
import os
import subprocess

# All 30 countries — name, slug (nginx URL), port, systemd service, ISO code
COUNTRIES = [
    {"name": "Thailand",         "slug": "thailand",          "port": 8085, "svc": "thailand-bot-api",           "iso": "TH"},
    {"name": "Vietnam",          "slug": "vietnam",           "port": 8086, "svc": "vietnam-bot-api",          "iso": "VN"},
    {"name": "Japan",            "slug": "japan",             "port": 8087, "svc": "japan-bot-api",             "iso": "JP"},
    {"name": "Korea",            "slug": "korea",             "port": 8089, "svc": "korea-bot-api",             "iso": "KR"},
    {"name": "India",            "slug": "india",             "port": 8105, "svc": "india-bot-api",             "iso": "IN"},
    {"name": "USA",              "slug": "usa",               "port": 8091, "svc": "usa-bot-api",               "iso": "US"},
    {"name": "Canada",           "slug": "canada",            "port": 8092, "svc": "canada-bot-api",            "iso": "CA"},
    {"name": "UK",               "slug": "uk",                "port": 8094, "svc": "uk-bot-api",                "iso": "GB"},
    {"name": "UAE",              "slug": "uae",               "port": 8093, "svc": "uae-bot-api",               "iso": "AE"},
    {"name": "Singapore",        "slug": "singapore",         "port": 8096, "svc": "sg-bot-api",                "iso": "SG"},
    {"name": "Australia",        "slug": "australia",         "port": 8097, "svc": "au-bot-api",                "iso": "AU"},
    {"name": "Philippines",      "slug": "philippines",       "port": 8095, "svc": "ph-bot-api",                "iso": "PH"},
    {"name": "Germany",          "slug": "germany",           "port": 8098, "svc": "de-bot-api",                "iso": "DE"},
    {"name": "France",           "slug": "france",            "port": 8099, "svc": "fr-bot-api",               "iso": "FR"},
    {"name": "Brazil",           "slug": "brazil",            "port": 8100, "svc": "br-bot-api",               "iso": "BR"},
    {"name": "Mexico",           "slug": "mexico",            "port": 8101, "svc": "mx-bot-api",               "iso": "MX"},
    {"name": "Switzerland",      "slug": "switzerland",       "port": 8102, "svc": "ch-bot-api",               "iso": "CH"},
    {"name": "Netherlands",      "slug": "netherlands",       "port": 8103, "svc": "nl-bot-api",               "iso": "NL"},
    {"name": "Hong Kong",        "slug": "hong_kong",         "port": 8104, "svc": "hongkong-bot-api",        "iso": "HK"},
    {"name": "Indonesia",        "slug": "indonesia",         "port": 8107, "svc": "id-bot-api",               "iso": "ID"},
    {"name": "Macau",            "slug": "macau",             "port": 8109, "svc": "mo-bot-api",               "iso": "MO"},
    {"name": "Malaysia",         "slug": "malaysia",          "port": 8106, "svc": "my-bot-api",               "iso": "MY"},
    {"name": "New Zealand",      "slug": "newzealand",        "port": 8110, "svc": "nz-bot-api",               "iso": "NZ"},
    {"name": "Taiwan",           "slug": "taiwan",            "port": 8108, "svc": "tw-bot-api",               "iso": "TW"},
    {"name": "Brunei",           "slug": "brunei",             "port": 8111, "svc": "brunei-bot-api",          "iso": "BN"},
    {"name": "Laos",             "slug": "laos",               "port": 8112, "svc": "laos-bot-api",            "iso": "LA"},
    {"name": "Myanmar",          "slug": "myanmar",            "port": 8113, "svc": "myanmar-bot-api",         "iso": "MM"},
    {"name": "Timor-Leste",      "slug": "timor-leste",        "port": 8114, "svc": "timor-leste-bot-api",     "iso": "TL"},
    {"name": "Papua New Guinea", "slug": "papua-new-guinea",   "port": 8115, "svc": "papua-new-guinea-bot-api","iso": "PG"},
    {"name": "Italy",            "slug": "italy",              "port": 8117, "svc": "italy-bot-api",           "iso": "IT"},
]

def get_systemd_status(svc_name):
    """Get systemd service status via systemctl show."""
    try:
        out = subprocess.run(["systemctl", "show", "-p", "ActiveState,LoadState,ExecMainStatus,MainPID,Restart", svc_name],
                           capture_output=True, text=True, timeout=5)
        props = {}
        for line in out.stdout.strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                props[k] = v
        return props
    except:
        return {"error": "N/A"}

def test_endpoint(method, url, json_data=None, timeout=10):
    """Test endpoint, return (status, json_dict, headers)."""
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout, verify=False)
        else:
            r = requests.post(url, json=json_data, timeout=timeout, verify=False)
        try:
            d = r.json()
        except:
            d = None
        return r.status_code, d, dict(r.headers)
    except Exception as e:
        return None, {"error": str(e)[:60]}, {}

print("=" * 130)
print("V3 READ-ONLY AUDIT — ALL 30 COUNTRIES")
print("=" * 130)
print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}")
print()

results = []
for c in COUNTRIES:
    slug = c["slug"]
    port = c["port"]
    base = f"https://xrplme.online/wc/v1/{slug}"
    local_base = f"http://127.0.0.1:{port}"
    
    # Systemd status
    sd = get_systemd_status(c["svc"])
    
    # Health (public + local)
    pub_h_code, pub_h_json, _ = test_endpoint("GET", f"{base}/health")
    loc_h_code, loc_h_json, _ = test_endpoint("GET", f"{local_base}/health")
    
    # Raw bot 402 (public + local)
    pub_r_code, pub_r_json, pub_r_hdrs = test_endpoint("POST", f"{base}/bot", {"message": "audit", "session_id": "audit"})
    loc_r_code, loc_r_json, loc_r_hdrs = test_endpoint("POST", f"{local_base}/api/v1/{slug}/bot", {"message": "audit", "session_id": "audit"})
    
    # AI bot 402 (public + local)
    pub_a_code, pub_a_json, pub_a_hdrs = test_endpoint("POST", f"{base}/bot/ai", {"message": "audit", "session_id": "audit"})
    
    # Parse raw 402 structure
    raw_x402ver = "N/A"
    raw_amount = "N/A"
    raw_scheme = "N/A"
    raw_payto_short = "N/A"
    raw_has_resource = False
    raw_has_ext = False
    raw_headers = []
    raw_invoice_id = "N/A"
    raw_source_tag = "N/A"
    
    if pub_r_json and isinstance(pub_r_json, dict):
        raw_x402ver = pub_r_json.get("x402Version", "MISSING")
        accepts = pub_r_json.get("accepts", [])
        if accepts:
            a = accepts[0]
            raw_amount = a.get("amount", "N/A")
            raw_scheme = a.get("scheme", "N/A")
            payto = a.get("payTo", "N/A")
            raw_payto_short = payto[:20] if payto else "N/A"
            inv = a.get("extra", {})
            raw_invoice_id = inv.get("invoiceId", "N/A")
            raw_source_tag = inv.get("sourceTag", "N/A")
        raw_has_resource = "resource" in pub_r_json
        raw_has_ext = "extensions" in pub_r_json
    if loc_r_json and isinstance(loc_r_json, dict):
        raw_headers = sorted([k for k in loc_r_hdrs if "payment" in k.lower() or "x402" in k.lower()])
    
    # Parse AI 402 structure
    ai_x402ver = "N/A"
    ai_amount = "N/A"
    ai_headers = []
    if pub_a_json and isinstance(pub_a_json, dict):
        ai_x402ver = pub_a_json.get("x402Version", "MISSING")
        accepts = pub_a_json.get("accepts", [])
        if accepts:
            ai_amount = accepts[0].get("amount", "N/A")
    if pub_a_json and isinstance(pub_a_json, dict):
        ai_headers = sorted([k for k in pub_a_hdrs if "payment" in k.lower() or "x402" in k.lower()])
    
    # Parse health structure
    health_records = "N/A"
    health_has_ts = False
    health_has_source = False
    
    if pub_h_json and isinstance(pub_h_json, dict):
        health_records = pub_h_json.get("data_records", "N/A")
        health_has_ts = "timestamp" in pub_h_json or "last_updated" in pub_h_json
        health_has_source = "sources" in pub_h_json
    
    r = {
        "name": c["name"], "slug": slug, "port": port, "svc": c["svc"], "iso": c["iso"],
        "systemd_active": sd.get("ActiveState", "N/A"),
        "systemd_load": sd.get("LoadState", "N/A"),
        "systemd_pid": sd.get("MainPID", "N/A"),
        "pub_health": pub_h_code,
        "loc_health": loc_h_code,
        "health_json": pub_h_json is not None,
        "health_records": health_records,
        "health_has_timestamp": health_has_ts,
        "health_has_source": health_has_source,
        "pub_raw_402": pub_r_code,
        "pub_ai_402": pub_a_code,
        "raw_x402ver": raw_x402ver,
        "raw_amount": raw_amount,
        "raw_scheme": raw_scheme,
        "raw_payto": raw_payto_short,
        "raw_resource": raw_has_resource,
        "raw_ext": raw_has_ext,
        "raw_headers": raw_headers,
        "raw_invoice_id": raw_invoice_id,
        "raw_source_tag": raw_source_tag,
        "ai_x402ver": ai_x402ver,
        "ai_amount": ai_amount,
        "ai_headers": ai_headers,
        "class": "LIVE" if pub_h_code == 200 and pub_r_code == 402 and pub_a_code == 402 else \
                "PARTIAL" if pub_h_code == 200 and pub_r_code == 402 else "FAILED",
    }
    results.append(r)
    time.sleep(0.2)  # Rate limiting
    print(f"  {c['name']:<22} health={pub_h_code} raw={pub_r_code} ai={pub_a_code} class={r['class']}")

# Print full table
print("\n" + "=" * 130)
print("FULL INVENTORY TABLE")
print("=" * 130)
print(f"{'Country':<22} {'Slug':<20} {'Port':<6} {'Svc':<28} {'ISO':<4} "
      f"{'H':<4} {'R':<4} {'AI':<4} {'Ver':<6} {'Price':<8} {'SrcTag':<5} {'class':<8}")
print("-" * 130)
for r in results:
    price = f"{r['raw_amount']}" if r["raw_amount"] != "N/A" else "-"
    print(f"{r['name']:<22} {r['slug']:<20} {r['port']:<6} {r['svc']:<28} {r['iso']:<4} "
          f"{str(r['pub_health']):<4} {str(r['pub_raw_402']):<4} {str(r['pub_ai_402']):<4} "
          f"{str(r['raw_x402ver']):<6} {price:<8} {str(r['raw_source_tag']):<5} {r['class']:<8}")

# Summary
print("\n" + "=" * 130)
print("SUMMARY")
print("=" * 130)
live = sum(1 for r in results if r["class"] == "LIVE")
partial = sum(1 for r in results if r["class"] == "PARTIAL")
failed = sum(1 for r in results if r["class"] == "FAILED")
print(f"LIVE (health 200 + raw 402 + AI 402): {live}/30")
print(f"PARTIAL (health 200 + raw 402, AI not 402): {partial}/30")
print(f"FAILED: {failed}/30")

# Inconsistencies
print("\n=== INCONSISTENCIES ===")
print("Countries where x402Version != 2:")
for r in results:
    if str(r["raw_x402ver"]) != "2":
        print(f"  {r['slug']}: x402Version={r['raw_x402ver']}")

print("\nCountries without sourceTag:")
for r in results:
    if str(r["raw_source_tag"]) == "N/A" or r["raw_source_tag"] != "804681468":
        print(f"  {r['slug']}: sourceTag={r['raw_source_tag']}")

print("\nCountries without resource/extensions in 402:")
for r in results:
    if not r["raw_resource"] or not r["raw_ext"]:
        print(f"  {r['slug']}: resource={r['raw_resource']}, extensions={r['raw_ext']}")

print("\nCountries using x402-* headers instead of payment-required:")
for r in results:
    if "payment-required" not in r["raw_headers"] and r["raw_headers"]:
        print(f"  {r['slug']}: headers={r['raw_headers']}")

print("\nCountries without health timestamps:")
for r in results:
    if not r["health_has_timestamp"]:
        print(f"  {r['slug']}")

print("\nCountries without health sources:")
for r in results:
    if not r["health_has_source"]:
        print(f"  {r['slug']}")

# Save
with open("/tmp/v3_audit_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to /tmp/v3_audit_results.json")
