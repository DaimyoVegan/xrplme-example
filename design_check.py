#!/usr/bin/env python3
"""
DESIGN CHECK: Country-label fix implementation analysis.
READ-ONLY — no code changes, no writes.
"""
import os
import re
import inspect
import sqlite3
import subprocess

print("=" * 80)
print("DESIGN CHECK: COUNTRY-LABEL FIX IMPLEMENTATION")
print("=" * 80)

# 1. Check x402_xrpl library InvoiceStore protocol
print("\n--- 1. x402_xrpl InvoiceStore Protocol ---")
FASTAPI_PATH = "/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/server/fastapi.py"

with open(FASTAPI_PATH) as f:
    content = f.read()

# Find InvoiceStore protocol
m = re.search(r'class InvoiceStore.*?:.*?(?=\nclass |\Z)', content, re.DOTALL)
if m:
    print(f"InvoiceStore protocol found ({len(m.group(0))} chars):")
    print(m.group(0)[:1500])

# Find where put() is called
print(f"\n--- 2. Where put() is called in x402_xrpl ---")
put_calls = []
for i, line in enumerate(content.split('\n')):
    if 'invoice_store.put(' in line or '.put(invoice_id' in line:
        put_calls.append((i+1, line.strip()))
        
for lineno, line in put_calls:
    print(f"  L{lineno}: {line[:150]}")

# Show context around put() call
if put_calls:
    first_call_line = put_calls[0][0]
    lines = content.split('\n')
    start = max(0, first_call_line - 10)
    end = min(len(lines), first_call_line + 5)
    print(f"\n  Context around put() call (L{start}-{end}):")
    for i in range(start, end):
        print(f"    L{i+1}: {lines[i].rstrip()[:120]}")

# 3. Check how RequireX402Options is structured
print(f"\n--- 3. RequireX402Options dataclass ---")
m = re.search(r'@dataclass\nclass RequireX402Options:.*?(?=\n@|\nclass |\Z)', content, re.DOTALL)
if m:
    opts = m.group(0)
    print(f"Fields:")
    for line in opts.split('\n')[1:40]:  # skip @dataclass line
        if line.strip().startswith(('invoice_store', 'facilitator', 'path', 'country', 'amount', 'pay_to')):
            print(f"  {line.strip()[:100]}")
        elif line.strip().startswith(')'):
            break

# 4. Check if path is available in the put() context
print(f"\n--- 4. Path/country availability in put() context ---")
# The put() is called with (invoice_id, reqs) — reqs contains PaymentRequirements
# PaymentRequirements contains the 'path' field
m = re.search(r'invoice_id.*?reqs.*?ttl_seconds', content, re.DOTALL)
if m:
    # Find the full context
    idx = content.find(m.group(0))
    snippet = content[idx-50:idx+300]
    print(f"  put() call context:")
    print(f"  ...{snippet}...")

# Check PaymentRequirements structure
print(f"\n--- 5. PaymentRequirements structure ---")
m = re.search(r'class PaymentRequirements.*?:.*?(?=\nclass |\n@|\Z)', content, re.DOTALL)
if m:
    print(m.group(0)[:1000])

# 5. Check how reqs contains path
print(f"\n--- 6. Path in PaymentRequirements ---")
for i, line in enumerate(content.split('\n')):
    if '"path"' in line or "'path'" in line or 'path=' in line:
        print(f"  L{i+1}: {line.strip()[:120]}")

# 6. Check what country field exists in PaymentRequirements
print(f"\n--- 7. Country in PaymentRequirements ---")
for i, line in enumerate(content.split('\n')):
    if '"country"' in line or "'country'" in line or 'country=' in line:
        print(f"  L{i+1}: {line.strip()[:120]}")

# 7. Check if x402_xrpl library is editable or pip-installed
print(f"\n--- 8. Library installation type ---")
result = subprocess.run(["/home/xrpladmin/thailand_bot_venv/bin/pip", "show", "x402-xrpl"],
                       capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'Location:' in line or 'Editable:' in line or 'Name:' in line:
        print(f"  {line.strip()}")

# 8. Check all 18 country bot servers for import patterns
print(f"\n--- 9. Import patterns across 18 persistent country servers ---")
api_dir = "/opt/xrplme/thoughts/api"
persistent_countries = [
    "thailand", "macau", "italy", "japan", "korea", "vietnam", "usa", "canada",
    "uae", "uk", "india", "indonesia", "malaysia", "mexico", "netherlands",
    "newzealand", "taiwan", "brasil"
]

import_pattern = {}
for country in sorted(persistent_countries):
    # Find the actual filename
    for f in os.listdir(api_dir):
        if f.startswith(country.replace("-", "_").replace("_", "")) and f.endswith("_bot_server.py"):
            continue  # might match wrong
    
    # Try common filename patterns
    possible_names = [
        f"{country.replace('-', '_')}_bot_server.py",
        f"{country.replace('-', '')}_bot_server.py",
        f"{country.replace('_', '')}_bot_server.py",
    ]
    
    fpath = None
    for name in possible_names:
        p = os.path.join(api_dir, name)
        if os.path.exists(p):
            fpath = p
            break
    
    if not fpath:
        # Search more broadly
        for f in os.listdir(api_dir):
            if "bot_server.py" in f and country.replace("-", "")[:4] in f.replace("-", "")[:4]:
                fpath = os.path.join(api_dir, f)
                break
    
    if fpath:
        with open(fpath) as fh:
            fcontent = fh.read()
        
        # Extract import line for SQLiteInvoiceStore
        m = re.search(r'(from.*import.*sqlite_invoice_store|import.*SQLiteInvoiceStore)', fcontent)
        if m:
            import_line = m.group(0).strip()
            if import_line not in import_pattern:
                import_pattern[import_line] = []
            import_pattern[import_line].append(os.path.basename(fpath))
    else:
        print(f"  {country}: FILE NOT FOUND (searched {possible_names})")

print(f"\n  Import patterns:")
for pattern, files in import_pattern.items():
    print(f"    Pattern: {pattern}")
    print(f"    Used by ({len(files)}): {', '.join(f.replace('_bot_server.py', '') for f in files)}")

# 9. Check if country can be derived from path in PaymentRequirements
print(f"\n--- 10. Path field in PaymentRequirements ---")
# The X402_CONFIG has 'path' field which contains the country
# When put() is called, 'reqs' contains the PaymentRequirements with 'path'
# Let's verify by checking the x402_xrpl source

# Find where path is set in PaymentRequirements
for i, line in enumerate(content.split('\n')):
    if 'path' in line and ('extra' in line or 'req' in line or 'pay' in line):
        if not line.strip().startswith('#'):
            print(f"  L{i+1}: {line.strip()[:120]}")

# 10. Check if SQLiteInvoiceStore can be subclassed
print(f"\n--- 11. SQLiteInvoiceStore inheritance ---")
SIS_PATH = "/opt/xrplme/thoughts/api/sqlite_invoice_store.py"
with open(SIS_PATH) as f:
    sis_content = f.read()

# Check class definition
m = re.search(r'class SQLiteInvoiceStore.*?(?=\nclass |\Z)', sis_content, re.DOTALL)
if m:
    first_line = m.group(0).split('\n')[0]
    print(f"  {first_line}")
    # Check if it has __init__
    init_m = re.search(r'def __init__\(self.*?\)', m.group(0))
    if init_m:
        print(f"  __init__ signature: {init_m.group(0)}")
    
    # Check if put() uses reqs to extract path
    put_m = re.search(r'async def put\(self.*?\), reqs.*?\n(?=    async def |\Z)', m.group(0), re.DOTALL)
    if put_m:
        put_code = put_m.group(0)
        # Check if path is accessible from reqs
        for line in put_code.split('\n'):
            if 'path' in line.lower() or 'extra' in line.lower() or 'reqs' in line.lower():
                print(f"  put() L: {line.strip()[:120]}")

# Check what reqs contains
print(f"\n--- 12. What 'reqs' contains when put() is called ---")
# The x402_xrpl library calls: await invoice_store.put(invoice_id, reqs, ttl_seconds=...)
# reqs is a list of PaymentRequirements objects
# PaymentRequirements has: amount, asset, network, pay_to, scheme, extra {sourceTag, invoiceId, ...}
# It may also have 'path' in extra or as a top-level field

# Check PaymentRequirements definition
m = re.search(r'class PaymentRequirements.*?(?=\nclass |\Z)', content, re.DOTALL)
if m:
    # Look for path field
    for line in m.group(0).split('\n'):
        if 'path' in line:
            print(f"  PaymentRequirements: {line.strip()[:120]}")

# Check how extra is built
print(f"\n--- 13. How 'extra' is built in x402_xrpl ---")
for i, line in enumerate(content.split('\n')):
    if 'extra' in line and ('path' in line or 'country' in line or 'invoice' in line):
        print(f"  L{i+1}: {line.strip()[:120]}")

# 13. Check if wrapper/adapter approach is feasible
print(f"\n--- 14. Wrapper/Adapter feasibility ---")
print(f"  SQLiteInvoiceStore is a regular class (not a Protocol)")
print(f"  Can be subclassed: Yes")
print(f"  Can be wrapped: Yes (composition)")
print(f"  Country would need to be passed via constructor or method override")

# 14. Check shared module import
print(f"\n--- 15. Module sharing ---")
print(f"  All 18 country servers import from: /opt/xrplme/thoughts/api/sqlite_invoice_store.py")
print(f"  This is a shared file — all services import the SAME module")
print(f"  A change to this file affects ALL 18 services after restart")

# Check if the import is via sys.path
print(f"\n--- 16. Import mechanism ---")
result = subprocess.run(["grep", "-r", "sqlite_invoice_store", api_dir + "/italy_bot_server.py"],
                       capture_output=True, text=True)
print(f"  Italy import: {result.stdout.strip()}")

# Check sys.path
for country in ["italy", "macau", "thailand"]:
    fpath = None
    for f in os.listdir(api_dir):
        if "bot_server" in f and country.replace("-","")[:4] in f.replace("-","")[:4]:
            fpath = os.path.join(api_dir, f)
            break
    if fpath:
        result = subprocess.run(["grep", "-n", "sys.path\|insert.*path\|append.*path", fpath],
                               capture_output=True, text=True)
        print(f"  {country} sys.path: {result.stdout.strip()[:100]}")

conn = sqlite3.connect(f"file:/home/xrpladmin/xrplme-state/x402.sqlite3?mode=ro", uri=True)
conn.close()

print(f"\n{'=' * 80}")
print("DESIGN CHECK COMPLETE")
print(f"{'=' * 80}")
