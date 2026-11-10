#!/usr/bin/env python3
"""
Check how x402_xrpl library calls create_invoice with country parameter.
Also check what default country is used.
"""
import re

# Read the x402_xrpl fastapi.py to see how create_invoice is called
fpath = "/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/server/fastapi.py"
with open(fpath) as f:
    content = f.read()

# Find where create_invoice is called
print("=== Where create_invoice is called in x402_xrpl library ===")
for i, line in enumerate(content.split('\n')):
    if 'create_invoice' in line or 'country' in line or 'invoice_store' in line:
        if 'self' not in line or 'def' in line or 'create' in line:
            print(f"  L{i+1}: {line.strip()[:150]}")

# Find the country parameter in RequireX402Options
print("\n=== RequireX402Options country field ===")
m = re.search(r'class RequireX402Options.*?(?=\nclass |\Z)', content, re.DOTALL)
if m:
    opts = m.group(0)
    for line in opts.split('\n'):
        if 'country' in line.lower():
            print(f"  {line.strip()}")

# Find where the middleware creates invoices
print("\n=== Invoice creation in middleware ===")
# Search for the pattern of create_invoice call
for i, line in enumerate(content.split('\n')):
    if 'create_invoice' in line or '.put(' in line or 'invoice_id' in line:
        if 'def ' not in line and 'class ' not in line:
            print(f"  L{i+1}: {line.strip()[:150]}")

# Check RequireX402Options for country field
print("\n=== Full RequireX402Options dataclass ===")
m = re.search(r'@dataclass\nclass RequireX402Options:.*?(?=\n@|\nclass |\Z)', content, re.DOTALL)
if m:
    print(m.group(0)[:2000])
