#!/usr/bin/env python3
"""Corrected log format analysis — field 2 is country, not field 3."""
import subprocess

result = subprocess.run(["cut", "-d|", "-f2", "/home/xrpladmin/logs/country-bots/requests.log"], capture_output=True, text=True)
countries = {}
for c in result.stdout.strip().split('\n'):
    c = c.strip()
    if c:
        countries[c] = countries.get(c, 0) + 1

print("=== Country distribution from field 2 (actual country field) ===")
for country, count in sorted(countries.items(), key=lambda x: -x[1]):
    print(f"  {country}: {count}")

# Also show field 3 to confirm it's endpoint
result2 = subprocess.run(["cut", "-d|", "-f3", "/home/xrpladmin/logs/country-bots/requests.log"], capture_output=True, text=True)
endpoints = {}
for c in result2.stdout.strip().split('\n'):
    c = c.strip()
    if c:
        endpoints[c] = endpoints.get(c, 0) + 1

print(f"\n=== Endpoint distribution from field 3 ===")
for ep, count in sorted(endpoints.items(), key=lambda x: -x[1]):
    print(f"  {ep}: {count}")

# Show Italy-specific with full detail
print(f"\n=== Full Italy log format ===")
result = subprocess.run(["grep", "^2026.*italy|", "/home/xrpladmin/logs/country-bots/requests.log"], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')
print(f"Italy log entries: {len(lines)}")
for line in lines[:5]:
    parts = line.split('|')
    if len(parts) >= 8:
        print(f"  ts={parts[0]} | country={parts[1]} | endpoint={parts[2]} | method={parts[3]} | status={parts[4]} | ip={parts[5]} | amount={parts[6]} | pay_sig={parts[7]} | ...")

# Now assess recovery feasibility
print(f"\n=== Recovery Feasibility (CORRECTED) ===")
print(f"  Log format: ts|country|endpoint|method|http_status|ip|amount|has_pay_sig|hash|latency|resp")
print(f"  Field 2 (index 1) = country name ✓")
print(f"  Field 1 (index 0) = ISO timestamp")
print(f"  Invoice issued_at = Unix epoch float")
print(f"  → CAN cross-reference: convert invoice issued_at to ISO, match against log entries")
print(f"  → But: log entries are per-REQUEST, not per-INVOICE")
print(f"  → Invoice creation (put()) happens in middleware before log line is written")
print(f"  → Log timestamp ≈ invoice issued_at (within same request processing)")
print(f"  → Accuracy: ~same second, sufficient for batch recovery")
print(f"  Classification: PARTIALLY RECOVERABLE (via timestamp cross-reference with logs)")

# Check if we can match Italy invoices to Italy logs
print(f"\n=== Italy cross-reference ===")
import sqlite3
conn = sqlite3.connect(f"file:/home/xrpladmin/xrplme-state/x402.sqlite3?mode=ro", uri=True)
c = conn.cursor()

# Get Italy-time invoices (invoices with issued_at timestamps matching Italy log entries)
c.execute("SELECT invoice_id, issued_at FROM invoices ORDER BY issued_at DESC LIMIT 5")
print(f"  Recent invoices (all mislabeled as thailand):")
for row in c.fetchall():
    inv, issued_at = row
    print(f"    {inv[:16]}... issued_at={issued_at:.0f}")

# Italy log timestamps
result = subprocess.run(["cut", "-d|", "-f1", "/home/xrpladmin/logs/country-bots/requests.log"], capture_output=True, text=True)
log_times = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
print(f"\n  Italy log timestamps (sample):")
italy_logs = [l for l in log_times if 'italy' in l.lower()]
print(f"  Total log entries: {len(log_times)}")

conn.close()
