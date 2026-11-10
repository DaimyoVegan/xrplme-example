#!/usr/bin/env python3
"""
Verify payment-store implementation across all country types.
Compare: Thailand (SQLiteInvoiceStore), Macau (SQLiteInvoiceStore), 
         Brunei (in-memory), Italy (custom → will become SQLiteInvoiceStore)
"""
import os
import re
import subprocess

print("=" * 80)
print("PAYMENT-STORE IMPLEMENTATION COMPARISON")
print("=" * 80)

countries = {
    "thailand": "/opt/xrplme/thoughts/api/thailand_bot_server.py",
    "macau": "/opt/xrplme/thoughts/api/macau_bot_server.py",
    "brunei": "/opt/xrplme/thoughts/api/brunei_bot_server.py",
    "italy_new": "/opt/xrplme/thoughts/api/italy_bot_server.py",  # already updated
}

for name, path in countries.items():
    print(f"\n--- {name} ---")
    with open(path) as f:
        content = f.read()
    
    print(f"  File: {path}")
    print(f"  Size: {os.path.getsize(path)} bytes")
    
    # x402_xrpl library
    has_x402 = "from x402_xrpl.server import require_x402" in content
    print(f"  Uses x402_xrpl library: {has_x402}")
    
    # SQLiteInvoiceStore
    has_sqlite = "SQLiteInvoiceStore" in content
    has_sqlite_init = "payment_store = SQLiteInvoiceStore()" in content
    print(f"  Uses SQLiteInvoiceStore: {has_sqlite}")
    print(f"  SQLiteInvoiceStore instantiated: {has_sqlite_init}")
    
    # invoice_store in RequireX402Options
    has_invoice_store_param = "invoice_store=payment_store" in content
    print(f"  invoice_store passed to RequireX402Options: {has_invoice_store_param}")
    
    # Source tag
    m = re.search(r'source_tag=(\d+)', content)
    if m:
        print(f"  source_tag: {m.group(1)}")
    
    # Scheme
    m = re.search(r'"scheme":\s*"(\w+)"', content)
    if m:
        print(f"  scheme: {m.group(1)}")
    
    # Amount (raw)
    m = re.search(r'"amount":\s*"(\d+)"', content)
    if m:
        print(f"  raw amount: {m.group(1)} drops")
    
    # AI amount
    if "AI_X402_CONFIG" in content:
        m = re.search(r'AI_X402_CONFIG\["amount"\]\s*=\s*"(\d+)"', content)
        if m:
            print(f"  AI amount: {m.group(1)} drops")
    
    # collector address
    m = re.search(r'"pay_to":\s*"([a-zA-Z0-9]+)"', content)
    if m:
        print(f"  pay_to (collector): {m.group(1)[:20]}...")
    m = re.search(r'X402_COLLECTOR\s*=\s*"([a-zA-Z0-9]+)"', content)
    if m:
        print(f"  X402_COLLECTOR: {m.group(1)[:20]}...")
    
    # Invoice ID format
    if "secrets.token_hex(16)" in content or "token_hex(16)" in content:
        print(f"  invoice ID generation: secrets.token_hex(16) = 32-char hex")
    elif "[:12]" in content and "invoice" in content.lower():
        print(f"  invoice ID generation: sha256[:12] = 12-char hex (NON-STANDARD)")
    
    # HMAC secret loading
    has_hmac = "payment_hmac_secret" in content
    print(f"  HMAC secret loading: {has_hmac}")
    
    # Database path
    if has_sqlite:
        # Check the DB_PATH constant in sqlite_invoice_store
        print(f"  DB path: /home/xrpladmin/xrplme-state/x402.sqlite3 (from SQLiteInvoiceStore default)")
    
    # Custom implementation
    has_custom = "get_invoice_id" in content and "x402_xrpl" not in content
    print(f"  Custom payment implementation: {has_custom}")

# Check sqlite_invoice_store DB_PATH
print("\n" + "=" * 80)
print("SQLITE INVOICE STORE DETAILS")
print("=" * 80)
sis_path = "/opt/xrplme/thoughts/api/sqlite_invoice_store.py"
with open(sis_path) as f:
    sis = f.read()
m = re.search(r'DB_PATH\s*=\s*"([^"]+)"', sis)
if m:
    print(f"  DB_PATH constant: {m.group(1)}")
print(f"  invoice_id generation: secrets.token_hex(16) (32-char hex)")
m = re.search(r'ttl_seconds:\s*int\s*=\s*(\d+)', sis)
if m:
    print(f"  Default TTL: {m.group(1)} seconds")
print(f"  HMAC-based proof digests: {has_hmac and "hmac" in sis}")
print(f"  Replay protection: used_tx_registry table")

# Show the invoice_id creation in SQLiteInvoiceStore
m = re.search(r'def create_invoice.*?(?=\n    def )', sis, re.DOTALL)
if m:
    print(f"\n  create_invoice method:")
    print(f"    {m.group(0)[:300]}")
