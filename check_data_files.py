#!/usr/bin/env python3
"""Check data file structures."""
import json

# Italy
print("=== Italy data file ===")
try:
    with open("/opt/xrplme/thoughts/api/italy-agent-full/publication/latest_valid.json") as f:
        d = json.load(f)
    print(f"  Keys: {list(d.keys())[:15]}")
    print(f"  record_count: {d.get('record_count', 'N/A')}")
    print(f"  sources: {d.get('sources', 'N/A')}")
    print(f"  scraped_at: {d.get('scraped_at', 'N/A')}")
    if d.get("records"):
        rec = d["records"][0]
        print(f"  First record keys: {list(rec.keys())[:10]}")
        print(f"  First record: {json.dumps(rec, indent=2)[:300]}")
    elif d.get("agents_data"):
        rec = d["agents_data"][0]
        print(f"  First agent_data keys: {list(rec.keys())[:10]}")
except Exception as e:
    print(f"  Error: {e}")

# Thailand (reference)
print("\n=== Thailand data file ===")
try:
    with open("/opt/xrplme/thoughts/api/thailand-agent-full/publication/latest_valid.json") as f:
        d = json.load(f)
    print(f"  Keys: {list(d.keys())[:15]}")
    print(f"  record_count: {d.get('record_count', 'N/A')}")
    print(f"  sources: {d.get('sources', 'N/A')}")
    print(f"  scraped_at: {d.get('scraped_at', 'N/A')}")
    if d.get("records"):
        rec = d["records"][0]
        print(f"  First record keys: {list(rec.keys())[:10]}")
        print(f"  First record: {json.dumps(rec, indent=2)[:300]}")
    elif d.get("agents_data"):
        rec = d["agents_data"][0]
        print(f"  First agent_data keys: {list(rec.keys())[:10]}")
        print(f"  First agent_data: {json.dumps(rec, indent=2)[:300]}")
except Exception as e:
    print(f"  Error: {e}")

# Check a few more
for country in ["brazil", "singapore", "macau"]:
    print(f"\n=== {country} data file ===")
    path = f"/opt/xrplme/thoughts/api/{country}-agent-full/publication/latest_valid.json"
    try:
        with open(path) as f:
            d = json.load(f)
        print(f"  Keys: {list(d.keys())[:10]}")
        print(f"  record_count: {d.get('record_count', 'N/A')}")
        print(f"  sources: {d.get('sources', 'N/A')}")
    except:
        print(f"  Not found at {path}")

# Check invoice IDs
print("\n=== Invoice ID Format Check ===")
import requests
for slug, port in [("thailand", 8085), ("italy", 8117), ("brazil", 8100)]:
    r = requests.post(f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
                     json={"message": "test"}, timeout=5)
    d = r.json()
    if d.get("accepts"):
        inv = d["accepts"][0].get("extra", {}).get("invoiceId", "N/A")
        scheme = d["accepts"][0].get("scheme", "N/A")
        print(f"  {slug}: invoiceId={inv} (len={len(inv)}), scheme={scheme}")
