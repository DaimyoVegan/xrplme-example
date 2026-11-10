#!/usr/bin/env python3
"""
V3 Invoice-Store Investigation — READ ONLY (Part 1)
1. Implementation Matrix for all 30 countries
2. Invoice lifecycle analysis
3. SQLite database schema inspection
"""
import os
import re
import hashlib
import sqlite3
import subprocess

API_DIR = "/opt/xrplme/thoughts/api"
DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
HMAC_FILE = "/home/xrpladmin/xrplme-state/payment_hmac_secret"

# Country -> (service_name, port, source_file, slug)
COUNTRIES = [
    ("thailand", "thailand-bot-api.svc", 8085, "thailand_bot_server.py", "thailand"),
    ("vietnam", "vietnam-bot-api.svc", 8086, "vietnam_bot_server.py", "vietnam"),
    ("japan", "japan-bot-api.svc", 8087, "japan_bot_server.py", "japan"),
    ("korea", "korea-bot-api.svc", 8089, "korea_bot_bot_server.py", "korea") 
        if os.path.exists(f"{API_DIR}/korea_bot_bot_server.py") 
        else ("korea", "korea-bot-api.svc", 8089, "korea_bot_server.py", "korea"),
    # Need to check actual filenames
]

# Get actual filenames
actual_files = {}
for f in sorted(os.listdir(API_DIR)):
    if f.endswith('.py') and 'bot_server' in f:
        actual_files[f] = os.path.join(API_DIR, f)

# Map slug to actual file
slug_to_file = {
    "thailand": "thailand_bot_server.py",
    "vietnam": "vietnam_bot_server.py",
    "japan": "japan_bot_server.py",
    "korea": "korea_bot_server.py",
    "usa": "usa_bot_server.py",
    "canada": "canada_bot_server.py",
    "uae": "uae_bot_server.py",
    "uk": "uk_bot_server.py",
    "hongkong": "hongkong_bot_server.py",
    "philippines": "ph_bot_server.py",
    "singapore": "sg_bot_server.py",
    "australia": "au_bot_server.py",
    "germany": "de_bot_server.py",
    "france": "fr_bot_server.py",
    "indonesia": "indonesia_bot_server.py",
    "india": "india_bot_server.py",
    "malaysia": "malaysia_bot_server.py",
    "taiwan": "taiwan_bot_server.py",
    "macau": "macau_bot_server.py",
    "newzealand": "newzealand_bot_server.py",
    "brunei": "brunei_bot_server.py",
    "laos": "laos_bot_server.py",
    "myanmar": "myanmar_bot_server.py",
    "timor-leste": "timor_leste_bot_server.py",
    "papua-new-guinea": "papua_new_guinea_bot_server.py",
    "italy": "italy_bot_server.py",
    "brasil": "brazil_bot_server.py",  # slug mismatch!
    "mexico": "mexico_bot_server.py",
    "switzerland": "ch_bot_server.py",  # slug mismatch!
    "netherlands": "netherlands_bot_server.py",
}

# Port map
ports = {
    "thailand": 8085, "vietnam": 8086, "japan": 8087, "korea": 8089,
    "usa": 8091, "canada": 8092, "uae": 8093, "uk": 8094,
    "hongkong": 8095, "philippines": 8096, "singapore": 8097,
    "australia": 8098, "germany": 8099, "france": 8100,
    "brasil": 8101, "mexico": 8102, "switzerland": 8103,
    "netherlands": 8104, "indonesia": 8105, "malaysia": 8106,
    "india": 8107, "taiwan": 8108, "macau": 8109, "newzealand": 8110,
    "brunei": 8111, "laos": 8112, "myanmar": 8113, "timor-leste": 8114,
    "papua-new-guinea": 8115, "netherlands2": 8116, "italy": 8117,
}

# Service names
services = {
    "thailand": "thailand-bot-api", "vietnam": "vietnam-bot-api",
    "japan": "japan-bot-api", "korea": "korea-bot-api",
    "usa": "usa-bot-api", "canada": "canada-bot-api",
    "uae": "uae-bot-api", "uk": "uk-bot-api",
    "hongkong": "hongkong-bot-api", "philippines": "philippines-bot-api",
    "singapore": "singapore-bot-api", "australia": "australia-bot-api",
    "germany": "germany-bot-api", "france": "france-bot-api",
    "brasil": "brasil-bot-api", "mexico": "mexico-bot-api",
    "switzerland": "switzerland-bot-api", "netherlands": "netherlands-bot-api",
    "indonesia": "indonesia-bot-api", "malaysia": "malaysia-bot-api",
    "india": "india-bot-api", "taiwan": "taiwan-bot-api",
    "macau": "macau-bot-api", "newzealand": "newzealand-bot-api",
    "brunei": "brunei-bot-api", "laos": "laos-bot-api",
    "myanmar": "myanmar-bot-api", "timor-leste": "timor-leste-bot-api",
    "papua-new-guinea": "p-n-g-bot-api", "italy": "italy-bot-api",
}

print("=" * 120)
print("1. V3 30-COUNTRY INVOICE-STORE IMPLEMENTATION MATRIX")
print("=" * 120)
print()
print(f"{'Country':<20} {'Service':<28} {'Port':<7} {'Middleware':<20} {'InvoiceStore':<18} {'Persistent':<12} {'Replay':<10} {'HMAC':<8} {'Raw':<10} {'AI':<10}")
print(f"{'':20} {'':28} {'':7} {'':20} {'':18} {'':12} {'':10} {'':8} {'':10} {'':10}")
print("-" * 120)

in_memory_countries = []
sqlite_countries = []

for slug in sorted(slug_to_file.keys()):
    fname = slug_to_file[slug]
    fpath = os.path.join(API_DIR, fname)
    
    if not os.path.exists(fpath):
        print(f"{slug:<20} {'(file not found: '+fname+')':<28} {'?':<7} {'?':<20} {'?':<18} {'?':<12} {'?':<10} {'?':<8} {'?':<10} {'?':<10}")
        continue
    
    with open(fpath) as f:
        content = f.read()
    
    # Detect middleware
    has_x402_import = "from x402_xrpl.server import require_x402" in content or "from x402_xrpl" in content
    has_custom_payment = "X402_COLLECTOR" in content and not has_x402_import
    
    if has_x402_import:
        middleware = "x402_xrpl.server"
    elif has_custom_payment:
        middleware = "CUSTOM"
    elif "fastapi" in content.lower() and "payment" in content.lower():
        middleware = "CUSTOM"
    else:
        middleware = "FASTAPI-ONLY"
    
    # Detect invoice store
    has_sqlite_store = "SQLiteInvoiceStore" in content and "payment_store = SQLiteInvoiceStore()" in content
    has_sqlite_import = "from sqlite_invoice_store import SQLiteInvoiceStore" in content
    has_inmem_default = has_x402_import and not has_sqlite_store  # uses x402 default _InMemoryInvoiceStore
    
    if has_sqlite_store:
        store = "SQLiteInvoiceStore"
        persistent = "YES"
        replay = "YES"
        sqlite_countries.append(slug)
    elif has_inmem_default:
        store = "_InMemoryInv"
        persistent = "NO"
        replay = "PARTIAL"
        in_memory_countries.append(slug)
    elif has_custom_payment:
        store = "CUSTOM"
        persistent = "NO"
        replay = "NO"
        # Italy is now fixed — check
        if "require_x402" in content:
            store = "SQLiteInvoiceStore"
            persistent = "YES"
            replay = "YES"
            sqlite_countries.append(slug)
        else:
            in_memory_countries.append(slug)  # custom = not persistent
    else:
        store = "NONE"
        persistent = "NO"
        replay = "NO"
        in_memory_countries.append(slug)
    
    # HMAC secret usage
    has_hmac = "payment_hmac_secret" in content or "hmac_secret" in content.lower()
    hmac = "YES" if has_hmac else "NO"
    
    # Prices
    raw_amount = "?"
    ai_amount = "?"
    m = re.search(r'"amount":\s*"(\d+)"', content)
    if m:
        raw_amount = m.group(1)
    m = re.search(r'AI_X402_CONFIG\["amount"\]\s*=\s*"(\d+)"', content)
    if m:
        ai_amount = m.group(1)
    # Check for custom price patterns
    if "100000" in content:
        raw_amount = "100000"
    if "500000" in content:
        ai_amount = "500000"
    
    port = ports.get(slug, "?")
    service = services.get(slug, "?")
    
    print(f"{slug:<20} {service:<28} {port:<7} {middleware:<20} {store:<18} {persistent:<12} {replay:<10} {hmac:<8} {raw_amount:<10} {ai_amount:<10}")

print(f"\n{'---':<20} {'---':<28} {'':7} {'---':<20} {'---':<18} {'---':<12} {'---':<10}")
print(f"\nSQLiteInvoiceStore countries (persistent): {len(sqlite_countries)}")
print(f"  {', '.join(sorted(sqlite_countries))}")
print(f"\nInMemory/custom countries (non-persistent): {len(in_memory_countries)}")
print(f"  {', '.join(sorted(in_memory_countries))}")
