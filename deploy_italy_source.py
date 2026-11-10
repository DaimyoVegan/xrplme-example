#!/usr/bin/env python3
"""Deploy the new italy_bot_server.py to the VPS."""
import os
import subprocess
import hashlib

# The new file was generated on VPS at /tmp/italy_bot_server_new.py
# We need to deploy it to /opt/xrplme/thoughts/api/italy_bot_server.py

source = "/tmp/italy_bot_server_new.py"
target = "/opt/xrplme/thoughts/api/italy_bot_server.py"

# Verify the source exists and is valid
print(f"Source: {source}")
print(f"Target: {target}")

# Get source hash
with open(source, 'rb') as f:
    src_hash = hashlib.sha256(f.read()).hexdigest()
print(f"Source SHA-256: {src_hash}")
print(f"Source size: {os.path.getsize(source)} bytes")

# Get backup hash for comparison
backup = "/home/xrpladmin/xrplme-state/backups/italy_bot_server.py.20260922_073619.bak"
with open(backup, 'rb') as f:
    bak_hash = hashlib.sha256(f.read()).hexdigest()
print(f"Backup SHA-256: {bak_hash}")
print(f"Source differs from backup: {src_hash != bak_hash}")

# Deploy: copy source to target
print(f"\nDeploying...")
result = subprocess.run(["cp", source, target], capture_output=True, text=True)
print(f"Copy exit code: {result.returncode}")
if result.stderr:
    print(f"Copy stderr: {result.stderr}")

# Verify deployment
with open(target, 'rb') as f:
    tgt_hash = hashlib.sha256(f.read()).hexdigest()
print(f"Target SHA-256: {tgt_hash}")
print(f"Target size: {os.path.getsize(target)} bytes")
print(f"Deployment verified: {src_hash == tgt_hash}")

# Run Python syntax check
print(f"\nRunning py_compile...")
result = subprocess.run(
    ["/home/xrpladmin/thailand_bot_venv/bin/python", "-m", "py_compile", target],
    capture_output=True, text=True
)
print(f"Compile exit code: {result.returncode}")
if result.stdout:
    print(f"stdout: {result.stdout}")
if result.stderr:
    print(f"stderr: {result.stderr}")

# Quick content verification
print(f"\nContent checks:")
with open(target) as f:
    content = f.read()
checks = [
    ('from x402_xrpl.server import require_x402', 'x402_xrpl import'),
    ('from sqlite_invoice_store import SQLiteInvoiceStore', 'SQLiteInvoiceStore import'),
    ('payment_store = SQLiteInvoiceStore()', 'SQLiteInvoiceStore init'),
    ('source_tag=804681468', 'source_tag'),
    ('"scheme": "exact"', 'scheme exact'),
    ('"amount": "100000"', 'raw amount 100000'),
    ('"amount": "500000"', 'AI amount 500000'),
    ('"pay_to": "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"', 'collector address'),
    ('"/api/v1/italy/bot"', 'Italy route'),
    ('COUNTRY_NAME = "italy"', 'country name'),
    ('port=8117', 'port 8117'),
    ('"timestamp"', 'timestamp field in health'),
    ('payment_hmac_secret', 'HMAC secret reference'),
]
for pattern, desc in checks:
    found = pattern in content
    print(f"  {'✓' if found else '✗'} {desc}")

# Check NO secrets
bad = [
    ('XRP_seed=', 'seed variable'),
    ('mnemonic', 'mnemonic'),
    ('private_key', 'private_key'),
    ('x402-treasury', 'treasury env reference'),
]
for pattern, desc in bad:
    found = pattern in content
    print(f"  {'✗ FOUND!' if found else '✓ absent'} {desc}")
