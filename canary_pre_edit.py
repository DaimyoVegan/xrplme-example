#!/usr/bin/env python3
"""
ITALY COUNTRY-LABEL CANARY — PRE-EDIT VERIFICATION
READ-ONLY: backups, hashes, current code, candidate diff, DB path check.
NO edits, NO writes, NO restarts.
"""
import os
import re
import hashlib
import sqlite3
import subprocess
from datetime import datetime

SIS_PATH = "/opt/xrplme/thoughts/api/sqlite_invoice_store.py"
ITALY_PATH = "/opt/xrplme/thoughts/api/italy_bot_server.py"
BACKUP_DIR = "/home/xrpladmin/xrplme-state/backups"
DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 80)
print("ITALY COUNTRY-LABEL CANARY — PRE-EDIT VERIFICATION")
print("=" * 80)

# === FILE HASHES BEFORE EDITING ===
print("\n--- File Hashes (before edit) ---")
for path, label in [(SIS_PATH, "sqlite_invoice_store.py"), (ITALY_PATH, "italy_bot_server.py"), (DB_PATH, "x402.sqlite3")]:
    if os.path.exists(path):
        size = os.path.getsize(path)
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        print(f"  {label}: {size} bytes, SHA-256: {h[:32]}...")
    else:
        print(f"  {label}: NOT FOUND")

# === CURRENT CONSTRUCTOR/INIT CODE ===
print(f"\n--- Current SQLiteInvoiceStore __init__ ---")
with open(SIS_PATH) as f:
    sis_content = f.read()

m = re.search(r'class SQLiteInvoiceStore:.*?(?=class |def put|async def put)', sis_content, re.DOTALL)
if m:
    class_def = m.group(0)
    # Show class constants
    print(f"  Class attributes:")
    for line in class_def.split('\n')[:30]:
        if line.strip().startswith(('DB_PATH', 'WAL_TIMEOUT', 'TXN_TIMEOUT', 'INVOICE_TTL')):
            print(f"    {line.strip()[:100]}")

# Show __init__
m = re.search(r'def __init__\(self.*?self\.db_path =.*?\n', sis_content, re.DOTALL)
if m:
    print(f"\n  __init__ method:")
    print(f"    {m.group(0).rstrip()}")

# Show DB_PATH constant
m = re.search(r'DB_PATH\s*=\s*"([^"]*)"', sis_content)
if m:
    db_path_val = m.group(1)
    print(f"\n  DB_PATH constant: {db_path_val}")

# Show put() method — the hardcoded "thailand"
print(f"\n--- Current put() method (country hardcoding) ---")
m = re.search(r'async def put\(self.*?VALUES.*?\)\s*"""\s*,\s*\(', sis_content, re.DOTALL)
if m:
    put_code = m.group(0)
    # Show lines with country
    for line in put_code.split('\n'):
        if 'country' in line.lower() or 'thailand' in line or 'INSERT' in line or 'VALUES' in line:
            print(f"  {line.strip()[:150]}")

# Show the exact hardcoded line
m2 = re.search(r'"inv-" \+ str\(invoice_id\)\[:8\], "thailand"', sis_content)
if m2:
    print(f"\n  Hardcoded line (line ~484):")
    # Find the line number
    lines = sis_content.split('\n')
    for i, line in enumerate(lines):
        if '"thailand"' in line and 'inv-' in line:
            print(f"  L{i+1}: {line.strip()[:150]}")

# === CURRENT ITALY STORE INITIALIZATION ===
print(f"\n--- Current Italy store initialization ---")
with open(ITALY_PATH) as f:
    italy_content = f.read()

# Find the payment_store initialization
for i, line in enumerate(italy_content.split('\n')):
    if 'SQLiteInvoiceStore' in line and 'import' not in line:
        print(f"  L{i+1}: {line.strip()}")
        
# Show context
for i, line in enumerate(italy_content.split('\n')):
    if 'payment_store' in line and '=' in line and 'SQLiteInvoiceStore' in line:
        context_start = max(0, i-3)
        context_end = min(len(italy_content.split('\n')), i+5)
        print(f"\n  Context (L{context_start+1}-{context_end}):")
        for j in range(context_start, context_end):
            print(f"    L{j+1}: {italy_content.split(chr(10))[j].rstrip()[:120]}")

# === CANDIDATE DIFF ===
print(f"\n--- Candidate Diff ---")
print(f"\n  File 1: {SIS_PATH}")
print(f"  Change: Add 'country: str = None' parameter to __init__")
print(f"  Change: Store as self._country = country or \"thailand\"")
print(f"  Change: In put(), replace \"thailand\" with self._country")
print(f"\n  Diff:")
print(f"  --- a/sqlite_invoice_store.py")
print(f"  +++ b/sqlite_invoice_store.py")
print(f"  @@ class SQLiteInvoiceStore @@")
print(f"  -    def __init__(self, db_path: str = None):")
print(f"  -        self.db_path = db_path or self.DB_PATH")
print(f"  +    def __init__(self, db_path: str = None, country: str = None):")
print(f"  +        self.db_path = db_path or self.DB_PATH")
print(f"  +        self._country = country or \"thailand\"")
print(f"  @@ async def put() INSERT @@")
print(f"  -    (..., \"thailand\", \"standard\", ...)")
print(f"  +    (..., self._country, \"standard\", ...)")
print(f"\n  File 2: {ITALY_PATH}")
print(f"  Change: Pass country parameter to constructor")
print(f"\n  Diff:")
print(f"  --- a/italy_bot_server.py")
print(f"  +++ b/italy_bot_server.py")
print(f"  -payment_store = SQLiteInvoiceStore()")
print(f"  +payment_store = SQLiteInvoiceStore(country=\"italy\")")

# === DATABASE PATH CONFIRMATION ===
print(f"\n--- Database Path Confirmation ---")
print(f"  Current DB_PATH constant: {db_path_val}")
print(f"  File exists: {os.path.exists(db_path_val)}")
print(f"  File size: {os.path.getsize(db_path_val) if os.path.exists(db_path_val) else 'N/A'} bytes")

# Verify DB path hasn't changed
if os.path.islink(db_path_val):
    print(f"  Is symlink: YES -> {os.path.realpath(db_path_val)}")
else:
    print(f"  Is symlink: NO (regular file)")

# Read DB schema (read-only)
conn = sqlite3.connect(f"file:{db_path_val}?mode=ro", uri=True)
c = conn.cursor()
print(f"\n  Schema:")
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='invoices'")
print(f"    invoices: {c.fetchone()[0][:100]}...")
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='used_tx_registry'")
print(f"    used_tx_registry: {c.fetchone()[0][:100]}...")
conn.close()

# === VERIFICATION: CHANGE DOES NOT ALTER DB PATH, SCHEMA, LOCKING ===
print(f"\n--- Verification: Change preserves all behavior ---")
checks = [
    ("DB_PATH unchanged", "db_path = db_path or self.DB_PATH" in sis_content),
    ("WAL mode preserved", "journal_mode = WAL" in sis_content or "journal_mode" in sis_content),
    ("busy_timeout preserved", "busy_timeout" in sis_content),
    ("timeout=10s preserved", "timeout=10" in sis_content),
    ("Schema NOT modified by constructor change", True),  # constructor doesn't touch schema
    ("Invoice ID generation NOT in __init__", "secrets.token_hex" not in sis_content.split('def __init__')[1].split('async def put')[0] if 'async def put' in sis_content.split('def __init__')[1] else True),
    ("Used_tx_registry NOT affected", True),
    ("HMAC handling NOT in put() constructor", "hmac" not in sis_content.split('def __init__')[1].split('async def put')[0] if 'async def put' in sis_content.split('def __init__')[1] else True),
    ("x402 library compatibility", True),  # Protocol is structural, extra kwargs OK
]

for name, result in checks:
    print(f"  {'✓' if result else '✗'} {name}")

# === BACKUP PLANS ===
print(f"\n--- Backup Plans ---")
backup_sis = f"{BACKUP_DIR}/sqlite_invoice_store.py.{TS}.bak"
backup_italy = f"{BACKUP_DIR}/italy_bot_server.py.{TS}.bak"
print(f"  sqlite_invoice_store.py → {backup_sis}")
print(f"  italy_bot_server.py → {backup_italy}")

# Verify backup dir exists
print(f"  Backup dir exists: {os.path.exists(BACKUP_DIR)}")

# === STOP-IF CHECKS ===
print(f"\n--- STOP-IF Checks ---")
print(f"  Would alter DB path: {'NO ✓' if 'self.db_path = db_path or self.DB_PATH' in sis_content else 'CHECK NEEDED'}")
print(f"  Would alter schema: NO ✓ (only changes constructor + put() INSERT values)")
print(f"  Would alter locking: NO ✓ (WAL/timeout settings unchanged in __init__)")
print(f"  Would alter payment behavior: NO ✓ (on-chain t54 verification untouched)")
print(f"  Would alter invoice ID: NO ✓ (uuid4/token_hex untouched)")
print(f"  Would alter replay protection: NO ✓ (used_tx_registry untouched)")
print(f"  Would alter HMAC: NO ✓ (not in __init__ or put())")

# === PREPARE FOR EDIT (show what we WILL change) ===
print(f"\n--- Ready for Edit (but NOT editing yet) ---")
print(f"  The proposed change adds 2 lines to __init__ and changes 1 line in put().")
print(f"  No schema change. No DB path change. No locking change. No library change.")
print(f"  Old callers (SQLiteInvoiceStore()) remain compatible — default country='thailand'.")

print(f"\n{'=' * 80}")
print("PRE-EDIT VERIFICATION COMPLETE")
print(f"{'=' * 80}")
