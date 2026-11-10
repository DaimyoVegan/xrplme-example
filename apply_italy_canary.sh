#!/usr/bin/env bash
# Italy country-label canary patch script
# READ-ONLY verification before editing, then apply patches.
# NO restarts. NO nginx. NO DB writes. NO payments.

set -euo pipefail

SIS_PATH="/opt/xrplme/thoughts/api/sqlite_invoice_store.py"
ITALY_PATH="/opt/xrplme/thoughts/api/italy_bot_server.py"
TS="20260922_130304"

echo "============================================================"
echo "ITALY COUNTRY-LABEL CANARY — EDIT"
echo "============================================================"

# Step -1: Verify hashes before edit
echo ""
echo "--- Pre-edit verification ---"
SIS_HASH_BEFORE=$(sha256sum "$SIS_PATH" | cut -d' ' -f1)
ITALY_HASH_BEFORE=$(sha256sum "$ITALY_PATH" | cut -d' ' -f1)
echo "sqlite_invoice_store.py SHA-256: $SIS_HASH_BEFORE"
echo "italy_bot_server.py SHA-256: $ITALY_HASH_BEFORE"

# Verify backups exist and match
SIS_BACKUP="/home/xrpladmin/xrplme-state/backups/sqlite_invoice_store.py.${TS}.bak"
ITALY_BACKUP="/home/xrpladmin/xrplme-state/backups/italy_bot_server.py.${TS}.bak"

if [ "$SIS_HASH_BEFORE" = "$(sha256sum "$SIS_BACKUP" | cut -d' ' -f1)" ]; then
    echo "✓ sqlite_invoice_store.py backup verified"
else
    echo "✗ sqlite_invoice_store.py backup MISMATCH"
    exit 1
fi

if [ "$ITALY_HASH_BEFORE" = "$(sha256sum "$ITALY_BACKUP" | cut -d' ' -f1)" ]; then
    echo "✓ italy_bot_server.py backup verified"
else
    echo "✗ italy_bot_server.py backup MISMATCH"
    exit 1
fi

# Step 0: Verify __init__ doesn't already have country param
echo ""
echo "--- Verify __init__ doesn't have country param yet ---"
if grep -q "country" "$SIS_PATH" | head -1; then
    echo "  Checking..."
fi
# Check __init__ specifically
INIT_LINE=$(grep -n "def __init__" "$SIS_PATH" | head -1 | cut -d: -f1)
if [ -n "$INIT_LINE" ]; then
    NEXT_LINE=$((INIT_LINE + 1))
    echo "  __init__ at line $INIT_LINE:"
    sed -n "${INIT_LINE},$((INIT_LINE+3))p" "$SIS_PATH"
    
    # Check if country already in init
    if sed -n "${INIT_LINE},$((INIT_LINE+3))p" "$SIS_PATH" | grep -q "country"; then
        echo "✗ country parameter already in __init__ — aborting (already patched)"
        exit 1
    else
        echo "✓ country parameter NOT in __init__ — safe to edit"
    fi
fi

# Step 1: Patch sqlite_invoice_store.py
echo ""
echo "--- Patching sqlite_invoice_store.py ---"

# 1a. Add country parameter to __init__
python3 -c "
import re
with open('$SIS_PATH', 'r') as f:
    content = f.read()

# Add country param to __init__
old_init = 'def __init__(self, db_path: str = None):\n        self.db_path = db_path or self.DB_PATH'
new_init = 'def __init__(self, db_path: str = None, country: str = None):\n        self.db_path = db_path or self.DB_PATH\n        self._country = country or \"thailand\"'

if old_init in content:
    content = content.replace(old_init, new_init, 1)
    print('  ✓ __init__ patched: added country parameter')
else:
    print('  ✗ __init__ pattern not found — aborting')
    exit(1)

# 1b. Replace hardcoded 'thailand' in put() INSERT
old_insert = '(invoice_id, \"inv-\" + str(invoice_id)[:8], \"thailand\", \"standard\",'
new_insert = '(invoice_id, \"inv-\" + str(invoice_id)[:8], self._country, \"standard\",'

if old_insert in content:
    content = content.replace(old_insert, new_insert, 1)
    print('  ✓ put() INSERT patched: replaced hardcoded thailand with self._country')
else:
    print('  ✗ INSERT pattern not found — aborting')
    exit(1)

with open('$SIS_PATH', 'w') as f:
    f.write(content)
print('  ✓ File written')
"

# Step 2: Patch italy_bot_server.py
echo ""
echo "--- Patching italy_bot_server.py ---"

python3 -c "
with open('$ITALY_PATH', 'r') as f:
    content = f.read()

old_init = 'payment_store = SQLiteInvoiceStore()'
new_init = 'payment_store = SQLiteInvoiceStore(country=\"italy\")'

if old_init in content:
    content = content.replace(old_init, new_init, 1)
    print('  ✓ Italy init patched: SQLiteInvoiceStore(country=\"italy\")')
else:
    print('  ✗ Italy init pattern not found — aborting')
    exit(1)

with open('$ITALY_PATH', 'w') as f:
    f.write(content)
print('  ✓ File written')
"

# Step 3: Verify hashes after edit
echo ""
echo "--- Post-edit verification ---"
SIS_HASH_AFTER=$(sha256sum "$SIS_PATH" | cut -d' ' -f1)
ITALY_HASH_AFTER=$(sha256sum "$ITALY_PATH" | cut -d' ' -f1)
echo "sqlite_invoice_store.py SHA-256: $SIS_HASH_AFTER (was: $SIS_HASH_BEFORE)"
echo "italy_bot_server.py SHA-256: $ITALY_HASH_AFTER (was: $ITALY_HASH_BEFORE)"

if [ "$SIS_HASH_AFTER" != "$SIS_HASH_BEFORE" ]; then
    echo "  ✓ sqlite_invoice_store.py changed (as expected)"
else
    echo "  ✗ sqlite_invoice_store.py UNCHANGED — patch failed!"
    exit 1
fi

if [ "$ITALY_HASH_AFTER" != "$ITALY_HASH_BEFORE" ]; then
    echo "  ✓ italy_bot_server.py changed (as expected)"
else
    echo "  ✗ italy_bot_server.py UNCHANGED — patch failed!"
    exit 1
fi

# Step 4: Show the diffs
echo ""
echo "--- Diff: sqlite_invoice_store.py ---"
diff "$SIS_BACKUP" "$SIS_PATH" || true

echo ""
echo "--- Diff: italy_bot_server.py ---"
diff "$ITALY_BACKUP" "$ITALY_PATH" || true

# Step 5: Verify critical elements preserved
echo ""
echo "--- Verification: critical elements preserved ---"
echo "  DB_PATH unchanged: $(grep 'DB_PATH = ' "$SIS_PATH")"
echo "  WAL_TIMEOUT: $(grep 'WAL_TIMEOUT = ' "$SIS_PATH")"
echo "  TXN_TIMEOUT: $(grep 'TXN_TIMEOUT = ' "$SIS_PATH")"
echo "  journal_mode WAL: $(grep 'journal_mode' "$SIS_PATH" | head -1)"
echo "  busy_timeout: $(grep 'busy_timeout' "$SIS_PATH")"
echo "  self._country in __init__: $(grep 'self._country' "$SIS_PATH" | head -1)"
echo "  self._country in put(): $(grep 'self._country' "$SIS_PATH" | tail -1)"
echo "  Italy country param: $(grep 'SQLiteInvoiceStore(country' "$ITALY_PATH")"
echo "  No secrets exposed: $(grep -c 'thailand\|italy' "$SIS_PATH" | head -1) country references (non-secret)"

# Step 6: Syntax check
echo ""
echo "--- Syntax check ---"
python3 -m py_compile "$SIS_PATH" && echo "  ✓ sqlite_invoice_store.py: py_compile PASS" || { echo "  ✗ py_compile FAIL"; exit 1; }
python3 -m py_compile "$ITALY_PATH" && echo "  ✓ italy_bot_server.py: py_compile PASS" || { echo "  ✗ py_compile FAIL"; exit 1; }

echo ""
echo "============================================================"
echo "EDITS APPLIED. AWAITING RESTART APPROVAL."
echo "============================================================"
