#!/usr/bin/env python3
"""Check APAC + Italy payment format and source code."""
import requests
import json

# APAC + Italy countries
apac = [("brunei", 8111), ("laos", 8112), ("myanmar", 8113), 
        ("timor-leste", 8114), ("papua-new-guinea", 8115), ("italy", 8117)]

print("APAC + Italy 402 Response Format Comparison")
print("=" * 80)
for slug, port in apac:
    try:
        r = requests.post(
            f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
            json={"message": "test"},
            timeout=10
        )
        d = r.json()
        print(f"\n--- {slug} (port {port}) ---")
        print(f"  Status: {r.status_code}")
        print(f"  x402Version: {d.get('x402Version', 'MISSING')}")
        print(f"  scheme: {d.get('accepts', [{}])[0].get('scheme', 'N/A')}")
        print(f"  has resource: {'resource' in d}")
        print(f"  has extensions: {'extensions' in d}")
        
        # Check headers
        pay_hdrs = [k for k in r.headers.keys() if 'payment' in k.lower() or 'x402' in k.lower()]
        print(f"  Payment headers: {pay_hdrs}")
        
        if d.get('accepts'):
            a = d['accepts'][0]
            extra = a.get('extra', {})
            print(f"  amount: {a.get('amount')}")
            print(f"  sourceTag: {extra.get('sourceTag', 'MISSING')}")
            print(f"  invoiceId: {extra.get('invoiceId', 'MISSING')}")
            print(f"  country: {extra.get('country', 'MISSING')}")
            
    except Exception as e:
        print(f"\n--- {slug} ---")
        print(f"  ERROR: {e}")

# Compare with Thailand (reference, 24 existing countries)
print("\n" + "=" * 80)
print("Thailand (reference) 402 Response Format")
print("=" * 80)
for slug, port in [("thailand", 8085), ("brazil", 8100)]:
    r = requests.post(
        f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
        json={"message": "test"},
        timeout=10
    )
    d = r.json()
    print(f"\n--- {slug} (port {port}) ---")
    print(f"  Status: {r.status_code}")
    print(f"  x402Version: {d.get('x402Version', 'MISSING')}")
    print(f"  scheme: {d.get('accepts', [{}])[0].get('scheme', 'N/A')}")
    print(f"  has resource: {'resource' in d}")
    print(f"  has extensions: {'extensions' in d}")
    pay_hdrs = [k for k in r.headers.keys() if 'payment' in k.lower() or 'x402' in k.lower()]
    print(f"  Payment headers: {pay_hdrs}")
    a = d['accepts'][0]
    extra = a.get('extra', {})
    print(f"  amount: {a.get('amount')}")
    print(f"  sourceTag: {extra.get('sourceTag', 'MISSING')}")
    print(f"  invoiceId length: {len(extra.get('invoiceId', ''))}")
    print(f"  invoiceId: {extra.get('invoiceId', 'MISSING')}")

# Check source code imports
print("\n" + "=" * 80)
print("Source Code Import Comparison")
print("=" * 80)
for f in ["thailand_bot_server.py", "italy_bot_server.py", "brunei_bot_server.py"]:
    path = f"/opt/xrplme/thoughts/api/{f}"
    try:
        with open(path) as fh:
            content = fh.read()
        has_x402_lib = "from x402_xrpl" in content
        has_custom = "get_invoice_id" in content
        has_sqlite = "SQLiteInvoiceStore" in content
        print(f"  {f}:")
        print(f"    x402_xrpl library: {has_x402_lib}")
        print(f"    Custom invoice: {has_custom}")
        print(f"    SQLiteInvoiceStore: {has_sqlite}")
    except:
        print(f"  {f}: CANNOT READ")

# Check nginx AI routes
print("\n" + "=" * 80)
print("nginx AI route check for 4 PARTIAL countries")
print("=" * 80)
for slug in ["uae", "singapore", "france", "timor-leste"]:
    r = requests.options(f"https://xrplme.online/wc/v1/{slug}/bot/ai", timeout=10, verify=False)
    print(f"  {slug}/bot/ai OPTIONS: {r.status_code} Allow={r.headers.get('allow', 'N/A')}")

# Get health record counts for all countries
print("\n" + "=" * 80)
print("Health Record Counts")
print("=" * 80)
all_countries = [
    ("thailand", 8085), ("vietnam", 8086), ("japan", 8087), ("korea", 8089),
    ("india", 8105), ("usa", 8091), ("canada", 8092), ("uk", 8094),
    ("uae", 8093), ("singapore", 8096), ("australia", 8097), ("philippines", 8095),
    ("germany", 8098), ("france", 8099), ("brazil", 8100), ("mexico", 8101),
    ("switzerland", 8102), ("netherlands", 8103), ("hong_kong", 8104),
    ("indonesia", 8107), ("macau", 8109), ("malaysia", 8106), ("newzealand", 8110),
    ("taiwan", 8108), ("brunei", 8111), ("laos", 8112), ("myanmar", 8113),
    ("timor-leste", 8114), ("papua-new-guinea", 8115), ("italy", 8117),
]
for slug, port in all_countries:
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        d = r.json()
        records = d.get("data_records", "N/A")
        ts = d.get("timestamp", "MISSING")
        lu = d.get("last_updated", "MISSING")
        print(f"  {slug:<20} records={records:<5} timestamp={ts[:10] if ts != 'MISSING' else 'MISSING'} last_updated={lu[:10] if lu != 'MISSING' else 'MISSING'}")
    except Exception as e:
        print(f"  {slug:<20} ERROR: {str(e)[:30]}")
