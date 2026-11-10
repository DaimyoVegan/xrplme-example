#!/usr/bin/env python3
"""
REVISED: Verify collector address, payment store design, and proxy path semantics
BEFORE proposing any implementation changes.
"""
import requests
import json
import os
import hashlib

print("=" * 80)
print("1. VERIFY COLLECTOR ADDRESS")
print("=" * 80)

# Check Thailand's source code for the collector address
print("\n--- Thailand source code (reference) ---")
with open("/opt/xrplme/thoughts/api/thailand_bot_server.py") as f:
    th_content = f.read()
# Find pay_to
if "pay_to" in th_content:
    import re
    m = re.search(r'"pay_to":\s*"([^"]+)"', th_content)
    if m:
        print(f"  X402_CONFIG[\"pay_to\"]: {m.group(1)}")
        th_pay_to = m.group(1)

# Check Macau's source code
print("\n--- Macau source code ---")
with open("/opt/xrplme/thoughts/api/macau_bot_server.py") as f:
    macau_content = f.read()
m = re.search(r'"pay_to":\s*"([^"]+)"', macau_content)
if m:
    print(f"  X402_CONFIG[\"pay_to\"]: {m.group(1)}")
    macau_pay_to = m.group(1)

# Check Italy's source code  
print("\n--- Italy source code ---")
with open("/opt/xrplme/thoughts/api/italy_bot_server.py") as f:
    it_content = f.read()
m = re.search(r'X402_COLLECTOR\s*=\s*"([^"]+)"', it_content)
if m:
    print(f"  X402_COLLECTOR: {m.group(1)}")
    it_pay_to = m.group(1)

# Check from the 402 response (what's actually served)
print("\n--- Actual 402 response payTo addresses ---")
for slug, port in [("thailand", 8085), ("macau", 8109), ("italy", 8117)]:
    try:
        r = requests.post(f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
                         json={"message": "test"}, timeout=5)
        d = r.json()
        if d.get("accepts"):
            pay_to = d["accepts"][0].get("payTo", "N/A")
            print(f"  {slug}: {pay_to}")
        elif d.get("accepts"):
            print(f"  {slug}: {d['accepts'][0]}")
        else:
            print(f"  {slug}: unexpected response: {list(d.keys())[:5]}")
    except Exception as e:
        print(f"  {slug}: ERROR - {e}")

print(f"\n  All same? {th_pay_to == macau_pay_to == it_pay_to}")

print("\n" + "=" * 80)
print("2. VERIFY PAYMENT-STORE IMPLEMENTATION")
print("=" * 80)

# Check Thailand
print("\n--- Thailand ---")
print(f"  Imports x402_xrpl: {'from x402_xrpl' in th_content}")
print(f"  Imports SQLiteInvoiceStore: {'SQLiteInvoiceStore' in th_content}")
print(f"  Uses SQLiteInvoiceStore(): {'payment_store = SQLiteInvoiceStore()' in th_content}")
# Find the SQLite path
m = re.search(r'SQLiteInvoiceStore\(([^)]*)\)', th_content)
if m:
    print(f"  SQLiteInvoiceStore() arg: {m.group(1)}")
else:
    print(f"  SQLiteInvoiceStore() arg: (no args — default path)")

# Check Macau
print("\n--- Macau ---")
print(f"  Imports x402_xrpl: {'from x402_xrpl' in macau_content}")
print(f"  Imports SQLiteInvoiceStore: {'SQLiteInvoiceStore' in macau_content}")
print(f"  Uses SQLiteInvoiceStore(): {'payment_store = SQLiteInvoiceStore()' in macau_content}")
m = re.search(r'SQLiteInvoiceStore\(([^)]*)\)', macau_content)
if m:
    print(f"  SQLiteInvoiceStore() arg: {m.group(1)}")
else:
    print(f"  SQLiteInvoiceStore() arg: (no args — default path)")

# Check Italy
print("\n--- Italy ---")
print(f"  Imports x402_xrpl: {'from x402_xrpl' in it_content}")
print(f"  Imports SQLiteInvoiceStore: {'SQLiteInvoiceStore' in it_content}")
print(f"  Current implementation: CUSTOM (no x402_xrpl library)")

# Check a country that does NOT use SQLiteInvoiceStore
# From earlier: au, ch, de, fr, hongkong, brunei, laos, myanmar, timor-leste, papua-new-guinea, ph, sg
print("\n--- brunei (does NOT use SQLiteInvoiceStore) ---")
with open("/opt/xrplme/thoughts/api/brunei_bot_server.py") as f:
    bn_content = f.read()
print(f"  Imports x402_xrpl: {'from x402_xrpl' in bn_content}")
print(f"  Imports SQLiteInvoiceStore: {'SQLiteInvoiceStore' in bn_content}")
print(f"  Uses SQLiteInvoiceStore(): {'payment_store = SQLiteInvoiceStore()' in bn_content}")
# Check how it handles invoice/store
if "invoice_store" in bn_content:
    # Find RequireX402Options
    m = re.search(r'RequireX402Options\(([^)]+)\)', bn_content, re.DOTALL)
    if m:
        print(f"  Has RequireX402Options (partial)")

# Check sqlite_invoice_store module to understand the DB path
print("\n--- sqlite_invoice_store module ---")
for path in ["/opt/xrplme/thoughts/api/sqlite_invoice_store.py", "/opt/xrplme/thoughts/api/x402/helpers/sqlite_invoice_store.py"]:
    if os.path.exists(path):
        print(f"  Found at: {path}")
        with open(path) as f:
            sis_content = f.read()
        # Find DB path
        m = re.search(r'DB_PATH\s*=\s*["\']([^"\']+)', sis_content)
        if m:
            print(f"  DB_PATH: {m.group(1)}")
        m = re.search(r'db_path\s*=\s*["\']([^"\']+)', sis_content)
        if m:
            print(f"  db_path: {m.group(1)}")
        # Find __init__
        if "__init__" in sis_content:
            print(f"  Has __init__")
        break
    else:
        # Try finding it
        pass

# Find the module
import subprocess
result = subprocess.run(["find", "/home/xrpladmin/thailand_bot_venv", "-name", "sqlite_invoice_store*"], 
                       capture_output=True, text=True)
print(f"  Module location: {result.stdout.strip()}")

print("\n" + "=" * 80)
print("3. VERIFY PUBLIC API ROUTES")
print("=" * 80)

# Check both hosts
hosts = [
    ("Website convenience", "https://xrplme.online"),
    ("Canonical direct API", "https://api.xrplme.online"),
]

routes = [
    ("health", "GET", "/wc/v1/italy/health", "/api/v1/italy/health"),
    ("raw bot", "POST", "/wc/v1/italy/bot", "/api/v1/italy/bot"),
    ("ai bot", "POST", "/wc/v1/italy/bot/ai", "/api/v1/italy/bot/ai"),
]

for host_name, host in hosts:
    print(f"\n--- {host_name}: {host} ---")
    for label, method, wc_path, api_path in routes:
        path = wc_path if "xrplme.online" in host else api_path
        try:
            if method == "GET":
                r = requests.get(f"{host}{path}", timeout=5, verify=False)
            else:
                r = requests.post(f"{host}{path}", 
                                json={"message": "audit"}, 
                                headers={"Content-Type": "application/json"},
                                timeout=5, verify=False)
            print(f"  {method} {path}")
            print(f"    Status: {r.status_code}")
            print(f"    Content-Type: {r.headers.get('content-type', 'N/A')[:50]}")
            ct = r.headers.get('content-type', '')
            if 'json' in ct or r.status_code == 402:
                try:
                    d = r.json()
                    if r.status_code == 402:
                        print(f"    x402Version: {d.get('x402Version', 'MISSING')}")
                        print(f"    scheme: {d.get('accepts',[{}])[0].get('scheme','N/A')}")
                        print(f"    amount: {d.get('accepts',[{}])[0].get('amount','N/A')}")
                        print(f"    payTo: {d.get('accepts',[{}])[0].get('payTo','N/A')[:20]}...")
                    else:
                        print(f"    JSON keys: {list(d.keys())[:5]}")
                except:
                    print(f"    Non-JSON response (len={len(r.content)})")
            else:
                print(f"    Response size: {len(r.content)}B")
        except Exception as e:
            print(f"  {method} {path} -> ERROR: {str(e)[:50]}")

print("\n" + "=" * 80)
print("4. VERIFY NGINX PROXY PATH SEMANTICS")
print("=" * 80)

# Compare Italy route with Macau route in xrplme-online-https
print("\n--- /wc/v1/italy/bot in xrplme-online-https ---")
import subprocess
result = subprocess.run(["grep", "-A3", "wc/v1/italy/bot {", "/etc/nginx/sites-available/xrplme-online-https"], 
                       capture_output=True, text=True)
print(f"  {result.stdout.strip()}")

print("\n--- /wc/v1/macau/bot in xrplme-online-https ---")
result = subprocess.run(["grep", "-A3", "wc/v1/macau/bot {", "/etc/nginx/sites-available/xrplme-online-https"], 
                       capture_output=True, text=True)
print(f"  {result.stdout.strip()}")

# Check api-xrplme-https
print("\n--- /api/v1/macau/bot in api-xrplme-https ---")
result = subprocess.run(["grep", "-A3", "api/v1/macau/bot {", "/etc/nginx/sites-available/api-xrplme-https"], 
                       capture_output=True, text=True)
print(f"  {result.stdout.strip()}")

print("\n--- /api/v1/italy/bot in api-xrplme-https ---")
result = subprocess.run(["grep", "-A3", "api/v1/italy/bot {", "/etc/nginx/sites-available/api-xrplme-https"], 
                       capture_output=True, text=True)
print(f"  {result.stdout.strip()}" if result.stdout.strip() else "  MISSING (not found)")

# Check health route pattern in api-xrplme-https
print("\n--- /api/v1/macau/health in api-xrplme-https ---")
result = subprocess.run(["grep", "-A3", "api/v1/macau/health {", "/etc/nginx/sites-available/api-xrplme-https"], 
                       capture_output=True, text=True)
print(f"  {result.stdout.strip()}")

# Check proxy_pass patterns
print("\n--- Proxy_pass patterns (api-xrplme-https) ---")
result = subprocess.run(["grep", "proxy_pass", "/etc/nginx/sites-available/api-xrplme-https"], 
                       capture_output=True, text=True)
print("  " + result.stdout.strip()[:500])

print("\n--- Proxy_pass patterns (xrplme-online-https) for Italy ---")
result = subprocess.run(["grep", "-A1", "wc/v1/italy", "/etc/nginx/sites-available/xrplme-online-https"], 
                       capture_output=True, text=True)
print(f"  {result.stdout.strip()}")

# Check if we need trailing slash
print("\n--- Check proxy_pass path format (Thailand vs Macau) ---")
result = subprocess.run(["grep", "proxy_pass.*8085", "/etc/nginx/sites-available/xrplme-online-https"], 
                       capture_output=True, text=True)
print(f"  xrplme-online-https: {result.stdout.strip()}")
result = subprocess.run(["grep", "proxy_pass.*8085", "/etc/nginx/sites-available/api-xrplme-https"], 
                       capture_output=True, text=True)
print(f"  api-xrplme-https: {result.stdout.strip()}")
