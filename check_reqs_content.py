#!/usr/bin/env python3
"""Check if path/country info is accessible from reqs in put() context."""
import re

FASTAPI_PATH = "/home/xrpladmin/thailand_bot_venv/lib/python3.12/site-packages/x402_xrpl/server/fastapi.py"
with open(FASTAPI_PATH) as f:
    content = f.read()

# Find PaymentRequirements definition
m = re.search(r'class PaymentRequirements.*?(?=\nclass |\n@|\Z)', content, re.DOTALL)
if m:
    print("=== PaymentRequirements dataclass ===")
    print(m.group(0)[:500])

# Find where PaymentRequirements is constructed (look for where extra/path is set)
print(f"\n=== Where PaymentRequirements is created ===")
for i, line in enumerate(content.split('\n')):
    if 'PaymentRequirements(' in line and 'class' not in line:
        print(f"  L{i+1}: {line.strip()[:150]}")

# Check if path is stored in extra or as a separate field
print(f"\n=== Path in PaymentRequirements/extra ===")
for i, line in enumerate(content.split('\n')):
    if 'path' in line.lower() and ('extra' in line.lower() or 'req' in line.lower() or 'Payment' in line):
        print(f"  L{i+1}: {line.strip()[:120]}")

# Look at the specific area around L848
lines = content.split('\n')
print(f"\n=== Context around L848 (path=path) ===")
for i in range(840, min(860, len(lines))):
    print(f"  L{i+1}: {lines[i].rstrip()[:120]}")

# Check what reqs contains at put() call site (L563)
print(f"\n=== reqs construction before put() call ===")
for i in range(540, 565):
    if i < len(lines):
        print(f"  L{i+1}: {lines[i].rstrip()[:120]}")

# Check if there's any country field anywhere
print(f"\n=== Any 'country' field in x402_xrpl ===")
for i, line in enumerate(content.split('\n')):
    if 'country' in line.lower():
        print(f"  L{i+1}: {line.strip()[:120]}")
