#!/usr/bin/env python3
"""Check x402_xrpl default invoice store and invoice_id generation."""
import subprocess
import re

result = subprocess.run(
    ["/home/xrpladmin/thailand_bot_venv/bin/python", "-c", """
from x402_xrpl.server import RequireX402Options
import inspect

# Check the signature
sig = inspect.signature(RequireX402Options)
for name, param in sig.parameters.items():
    print(f"  {name}: default={param.default}")
"""],
    capture_output=True, text=True
)
print("RequireX402Options signature:")
print(result.stdout)
if result.stderr:
    print(f"Stderr: {result.stderr[:200]}")

# Check _InMemoryInvoiceStore
path = "/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/server/__init__.py"
with open(path) as f:
    content = f.read()

# Find _InMemoryInvoiceStore
lines = content.split("\n")
for i, line in enumerate(lines):
    if "_InMemoryInvoiceStore" in line:
        start = max(0, i-2)
        end = min(len(lines), i+20)
        print(f"\nLines {start+1}-{end}:")
        for j in range(start, end):
            print(f"  {j+1}: {lines[j]}")
        break
