#!/usr/bin/env python3
"""
V3 Invoice-Store Investigation — READ ONLY
Inspects all 30 country bot servers for payment middleware config.
NO writes, NO changes, NO secrets printed.
"""
import os
import re
import hashlib
import sqlite3

API_DIR = "/opt/xrplme/thoughts/api"

# 30 countries with their expected source files, service names, ports
COUNTRIES = [
    ("thailand", "thailand-bot-api", 8085, "thailand_bot_server.py"),
    ("vietnam", "vietnam-bot-api", 8086, "vietnam_bot_server.py"),
    ("japan", "japan-bot-api", 8087, "japan_bot_server.py"),
    ("korea", "korea-bot-api", 8089, "korea_bot_server.py"),
    ("usa", "usa-bot-api", 8091, "usa_bot_server.py"),
    ("canada", "canada-bot-api", 8092, "canada_bot_server.py"),
    ("uae", "uae-bot-api", 8093, "uae_bot_api.py"),
    ("uk", "uk-bot-api", 8094, "uk_bot_server.py"),
    ("hongkong", "hongkong-bot-api", 8095, "hongkong_bot_server.py"),
    ("philippines", "philippines-bot-api", 8096, "philippines_bot_server.py"),
    ("singapore", "singapore-bot-api", 8097, "singapore_bot_server.py"),
    ("australia", "australia-bot-api", 8098, "australia_bot_server.py"),
    ("germany", "germany-bot-api", 8099, "germany_bot_server.py"),
    ("france", "france-bot-api", 8100, "france_bot_server.py"),
    ("indonesia", "indonesia-bot-api", 8105, "indonesia_bot_server.py"),
    ("india", "india-bot-api", 8107, "india_bot_server.py"),
    ("malaysia", "malaysia-bot-api", 8106, "malaysia_bot_server.py"),
    ("taiwan", "taiwan-bot-api", 8108, "taiwan_bot_server.py"),
    ("macau", "macau-bot-api", 8109, "macau_bot_server.py"),
    ("newzealand", "newzealand-bot-api", 8110, "newzealand_bot_server.py"),
    ("brunei", "brunei-bot-api", 8111, "brunei_bot_server.py"),
    ("laos", "laos-bot-api", 8112, "laos_bot_server.py"),
    ("myanmar", "myanmar-bot-api", 8113, "myanmar_bot_server.py"),
    ("timor-leste", "timor-leste-bot-api", 8114, "timor-leste_bot_server.py"),
    ("papua-new-guinea", "papua-new-guinea-bot-api", 8115, "p-n-g_bot_server.py"),
    ("italy", "italy-bot-api", 8117, "italy_bot_server.py"),
    ("brasil", "brasil-bot-api", 8101, "brasil_bot_server.py"),
    ("mexico", "mexico-bot-api", 8102, "mexico_bot_server.py"),
    ("switzerland", "switzerland-bot-api", 8103, "switzerland_bot_server.py"),
    ("netherlands", "netherlands-bot-api", 8116, "netherlands_bot_server.py"),
]

# Wait — let me get the actual file list from the API directory
print("Scanning API directory for all bot server files...")
files = [f for f in os.listdir(API_DIR) if f.endswith('.py') and 'bot_server' in f]
files.sort()
print(f"Found {len(files)} bot server files:")
for f in files:
    fpath = os.path.join(API_DIR, f)
    print(f"  {f} ({os.path.getsize(fpath)} bytes)")

# Also check for the sqlite_invoice_store module
sis_path = os.path.join(API_DIR, "sqlite_invoice_store.py")
print(f"\nsqlite_invoice_store.py exists: {os.path.exists(sis_path)}")
if os.path.exists(sis_path):
    print(f"  Size: {os.path.getsize(sis_path)} bytes")
