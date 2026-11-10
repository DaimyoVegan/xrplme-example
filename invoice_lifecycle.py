#!/usr/bin/env python3
"""
V3 Invoice-Store Investigation — READ ONLY (Part 2)
2. Invoice lifecycle analysis from source code
3. SQLite database schema inspection
4. _InMemoryInvoiceStore source analysis
"""
import os
import re
import sqlite3
import hashlib

API_DIR = "/opt/xrplme/thoughts/api"
DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
SIS_PATH = f"{API_DIR}/sqlite_invoice_store.py"

print("=" * 80)
print("2. INVOICE LIFECYCLE ANALYSIS")
print("=" * 80)

# Read the SQLiteInvoiceStore source
with open(SIS_PATH) as f:
    sis_content = f.read()

print(f"\nSQLiteInvoiceStore source: {SIS_PATH} ({os.path.getsize(SIS_PATH)} bytes)")
print(f"SHA-256: {hashlib.sha256(sis_content.encode()).hexdigest()}")

# Extract key methods
methods = re.findall(r'def (\w+)\(.*?\):', sis_content)
print(f"\nMethods found: {methods}")

# Invoice ID generation
print("\n--- Invoice ID generation ---")
m = re.search(r'def (\w+_invoice_id|create_invoice|store_invoice).*?(?=\n    def )', sis_content, re.DOTALL)
if m:
    method_text = m.group(0)[:500]
    print(f"Method: {m.group(1)}")
    # Show key parts
    for pattern in ['invoice_id', 'token_hex', 'hashlib', 'uuid', 'sha256']:
        if pattern in method_text:
            matches = re.findall(rf'{pattern}.*?\n', method_text)
            for match in matches[:3]:
                print(f"  {match.strip()}")
    # Also search the whole file for invoice_id generation
    for i, line in enumerate(sis_content.split('\n')):
        if any(p in line for p in ['token_hex', 'uuid4', 'sha256(', 'hash(', 'invoice_id =', 'str(uuid']):
            print(f"  L{i+1}: {line.strip()}")

# Invoice status tracking
print("\n--- Invoice status tracking ---")
status_patterns = ['INVOICE_STATUS', 'paid', 'expired', 'pending', 'refunded', 'InvoiceStatus']
for pattern in status_patterns:
    if pattern in sis_content:
        # Find lines with this pattern
        for i, line in enumerate(sis_content.split('\n')):
            if pattern in line:
                print(f"  L{i+1}: {line.strip()[:120]}")

# Payment verification
print("\n--- Payment verification ---")
verify_patterns = ['verify_payment', 'payment_proof', 'proof', 'HMAC', 'hmac', 'signature', 'claim', 'verify_invoice']
for pattern in verify_patterns:
    matches = [(i+1, line.strip()[:120]) for i, line in enumerate(sis_content.split('\n')) if pattern in line]
    if matches:
        print(f"  '{pattern}' found in {len(matches)} lines:")
        for ln, text in matches[:3]:
            print(f"    L{ln}: {text}")

# Replay protection
print("\n--- Replay protection ---")
replay_patterns = ['used_tx', 'replay', 'tx_hash', 'claim', 'consume']
for pattern in replay_patterns:
    matches = [(i+1, line.strip()[:120]) for i, line in enumerate(sis_content.split('\n')) if pattern.lower() in line.lower()]
    if matches:
        print(f"  '{pattern}' found in {len(matches)} lines:")
        for ln, text in matches[:3]:
            print(f"    L{ln}: {text}")

# _InMemoryInvoiceStore analysis
print("\n\n--- _InMemoryInvoiceStore (x402_xrpl library default) ---")
inmem_path = "/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/server/fastapi.py"
if os.path.exists(inmem_path):
    with open(inmem_path) as f:
        inmem_content = f.read()
    # Find class definition
    m = re.search(r'class _InMemoryInvoiceStore.*?(?=\nclass |\ndef )', inmem_content, re.DOTALL)
    if m:
        print(f"Found _InMemoryInvoiceStore class ({len(m.group(0))} chars)")
        # Show key methods
        for line in m.group(0).split('\n'):
            line = line.strip()
            if any(kw in line for kw in ['def ', 'self.', 'dict', 'store', 'put', 'get', 'consume', 'token', 'uuid']):
                print(f"  {line[:120]}")
    else:
        print("  Class not found in fastapi.py")
        # Search in __init__.py
        for root, dirs, files in os.walk("/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/"):
            for fname in files:
                fpath = os.path.join(root, fname)
                with open(fpath) as f:
                    c = f.read()
                if 'InMemoryInvoiceStore' in c or 'invoice_store' in c:
                    print(f"  Found in: {fpath}")
                    for i, line in enumerate(c.split('\n')):
                        if 'InMemoryInvoiceStore' in line or 'invoice_store' in line:
                            print(f"    L{i+1}: {line.strip()[:120]}")
else:
    print(f"  Path not found: {inmem_path}")

# Now the SQLite database
print("\n\n" + "=" * 80)
print("3. SQLITE DATABASE READ-ONLY INSPECTION")
print("=" * 80)

print(f"\nDatabase: {DB_PATH}")
if os.path.exists(DB_PATH):
    print(f"File size: {os.path.getsize(DB_PATH)} bytes")
    
    # Read-only connection
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"\nTables ({len(tables)}):")
    
    table_names = []
    for name, sql in tables:
        table_names.append(name)
        cursor.execute(f"SELECT COUNT(*) FROM {name}")
        count = cursor.fetchone()[0]
        print(f"\n  Table: {name} ({count} rows)")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({name})")
        cols = cursor.fetchall()
        col_names = [col[1] for col in cols]
        print(f"  Columns ({len(cols)}):")
        for col in cols:
            cid, name, ctype, notnull, default, pk = col
            pk_marker = " ⚡PK" if pk else ""
            print(f"    {name} ({ctype}){pk_marker}")
    
    # Check for indexes
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    indexes = cursor.fetchall()
    if indexes:
        print(f"\nIndexes ({len(indexes)}):")
        for name, tbl in indexes:
            print(f"  {name} on {tbl}")
    
    # Check invoice ID uniqueness
    if 'invoices' in table_names:
        cursor.execute("SELECT COUNT(DISTINCT invoice_id) FROM invoices")
        distinct_inv = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total_inv = cursor.fetchone()[0]
        print(f"\nInvoice uniqueness: {distinct_inv} distinct / {total_inv} total")
    
    # Check country distribution
    if 'invoices' in table_names:
        cursor.execute("SELECT country, COUNT(*) FROM invoices GROUP BY country ORDER BY COUNT(*) DESC")
        country_counts = cursor.fetchall()
        print(f"\nInvoice count by country:")
        for country, count in country_counts:
            print(f"  {country}: {count}")
    
    # Check proof storage
    if 'invoices' in table_names:
        cursor.execute("PRAGMA table_info(invoices)")
        cols = [col[1] for col in cursor.fetchall()]
        print(f"\nInvoice columns: {cols}")
        has_proof = any('proof' in c.lower() for c in cols)
        has_used_tx = 'used_tx_registry' in table_names
        has_digest = any('digest' in c.lower() for c in cols)
        print(f"  Payment proof stored: {has_proof}")
        print(f"  Digest column exists: {has_digest}")
        print(f"  used_tx_registry table: {has_used_tx}")
    
    # Check used_tx_registry
    if 'used_tx_registry' in table_names:
        cursor.execute("SELECT COUNT(*) FROM used_tx_registry")
        count = cursor.fetchone()[0]
        print(f"\nused_tx_registry: {count} entries")
        cursor.execute("PRAGMA table_info(used_tx_registry)")
        cols = [col[1] for col in cursor.fetchall()]
        print(f"  Columns: {cols}")
    
    # Check timestamps
    if 'invoices' in table_names:
        cursor.execute(f"SELECT {', '.join([c for c in cols if 'time' in c.lower() or 'date' in c.lower() or 'expir' in c.lower()])} FROM invoices LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"  Timestamp columns: {[c for c in cols if 'time' in c.lower() or 'date' in c.lower() or 'expir' in c.lower()]}")
    
    # Check status values
    if 'invoices' in table_names:
        cursor.execute("SELECT status, COUNT(*) FROM invoices GROUP BY status")
        statuses = cursor.fetchall()
        if statuses:
            print(f"\n  Invoice statuses:")
            for status, count in statuses:
                print(f"    {status}: {count}")
    
    conn.close()
    
    # Database file metadata
    print(f"\n  DB file SHA-256: {hashlib.sha256(open(DB_PATH, 'rb').read()).hexdigest()}")
    print(f"  DB file owner UID: {os.stat(DB_PATH).st_uid}")
    print(f"  DB file mode: {oct(os.stat(DB_PATH).st_mode & 0o777)}")
else:
    print("  Database NOT FOUND")
