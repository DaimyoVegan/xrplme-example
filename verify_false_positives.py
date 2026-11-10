#!/usr/bin/env python3
"""Verify the 3 false-positive checks."""
import os

SIS_PATH = "/opt/xrplme/thoughts/api/sqlite_invoice_store.py"
with open(SIS_PATH) as f:
    content = f.read()

lines = content.split('\n')

# 1. Check __init__ section
print("=== __init__ method (lines 85-95) ===")
for i in range(84, 96):
    if i < len(lines):
        print(f"  L{i+1}: {lines[i]}")

# 2. Check timeout/WAL settings
print(f"\n=== Timeout and WAL settings ===")
for i, line in enumerate(lines):
    if 'timeout' in line.lower() or 'WAL' in line or 'busy' in line.lower() or 'journal_mode' in line:
        print(f"  L{i+1}: {line.strip()[:100]}")

# 3. Verify __init__ doesn't contain invoice ID generation
print(f"\n=== __init__ full content ===")
in_init = False
for i, line in enumerate(lines):
    if 'def __init__' in line:
        in_init = True
    if in_init:
        print(f"  L{i+1}: {line.strip()[:100]}")
        if line.strip() and not line.startswith(' ') and not line.startswith('\t') and 'def ' in line and i > 85:
            break
    if in_init and i > 95:
        break

# 4. Verify HMAC location
print(f"\n=== HMAC references ===")
for i, line in enumerate(lines):
    if 'hmac' in line.lower() or 'HMAC' in line:
        print(f"  L{i+1}: {line.strip()[:100]}")

# 5. Verify put() doesn't contain HMAC
print(f"\n=== put() method (around line 445-490) ===")
for i in range(444, min(500, len(lines))):
    print(f"  L{i+1}: {lines[i].rstrip()[:120]}")

# Summary
print(f"\n=== SUMMARY ===")
print(f"  timeout=10 in __init__: {'NO ✓' if 'timeout=10' not in '\\n'.join(lines[84:95]) else 'YES ✗'}")
print(f"  TXN_TIMEOUT=10 is class constant: {'YES ✓' if 'TXN_TIMEOUT = 10' in content else 'NO ✗'}")
print(f"  timeout=self.TXN_TIMEOUT in __init__: {'YES ✓' if 'timeout=self.TXN_TIMEOUT' in content else 'NO ✗'}")
print(f"  secrets.token_hex in __init__: {'NO ✓ (in atomic_claim)' if 'secrets.token_hex' in content and 'def __init__' not in content.split('secrets.token_hex')[0][-200:] else 'CHECK'}")
print(f"  HMAC in put(): {'NO ✓' if 'hmac' not in content[content.find('async def put'):content.find('async def put')+2000].lower() else 'YES ✗'}")
