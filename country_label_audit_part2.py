#!/usr/bin/env python3
"""READ-ONLY: Country-recovery feasibility from logs."""
import os
import sqlite3
import subprocess

DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"
log_path = "/home/xrpladmin/logs/country-bots/requests.log"

print("--- 4. Country-Recovery Feasibility ---")
print("  Checking if logs can help reconstruct country for historical invoices:")

if os.path.exists(log_path):
    result = subprocess.run(["wc", "-l", log_path], capture_output=True, text=True)
    print(f"  Log file: {log_path}")
    print(f"  Log lines: {result.stdout.strip()}")

    result = subprocess.run(["head", "-3", log_path], capture_output=True, text=True)
    print(f"\n  Log format (first 3 lines):")
    for line in result.stdout.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 4:
            print(f"    ts={parts[0]} | country={parts[2][:20]} | endpoint={parts[3][:20]} | ...")

    result = subprocess.run(["tail", "-3", log_path], capture_output=True, text=True)
    print(f"\n  Last 3 log lines:")
    for line in result.stdout.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 4:
            print(f"    ts={parts[0]} | country={parts[2][:20]} | endpoint={parts[3][:20]} | ...")

    result = subprocess.run(["grep", "-c", "italy", log_path], capture_output=True, text=True)
    print(f"\n  Italy log entries: {result.stdout.strip()}")

    result = subprocess.run(["cut", "-d|", "-f3", log_path], capture_output=True, text=True)
    countries_in_log = {}
    for c in result.stdout.strip().split('\n'):
        c = c.strip()
        if c:
            countries_in_log[c] = countries_in_log.get(c, 0) + 1
    print(f"\n  Countries in log:")
    for country, count in sorted(countries_in_log.items()):
        print(f"    {country}: {count}")
else:
    print(f"  Log file not found at {log_path}")
    result = subprocess.run(["find", "/home/xrpladmin/logs", "-name", "*.log", "-type", "f"],
                           capture_output=True, text=True)
    if result.stdout:
        print(f"  Found log files:")
        for f in result.stdout.strip().split('\n'):
            print(f"    {f} ({os.path.getsize(f)} bytes)")

print(f"\n--- Database metadata ---")
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
c = conn.cursor()

c.execute("SELECT DISTINCT country, endpoint_tier FROM invoices")
combos = c.fetchall()
print(f"\n  All country/endpoint_tier combinations in invoices:")
for combo in combos:
    print(f"    {combo[0]} / {combo[1]}")

c.execute("SELECT country, COUNT(*) FROM used_tx_registry GROUP BY country")
print(f"\n  used_tx_registry country distribution:")
for row in c.fetchall():
    print(f"    {row[0]}: {row[1]}")

c.execute("SELECT DISTINCT country FROM used_tx_registry ORDER BY country")
utx_countries = c.fetchall()
print(f"\n  Countries in used_tx_registry: {[r[0] for r in utx_countries]}")

c.execute("SELECT request_body_hash FROM invoices ORDER BY issued_at DESC LIMIT 3")
print(f"\n  Request body hash sample:")
for row in c.fetchall():
    h = row[0]
    print(f"    {h[:32]}... (len={len(h)})")

conn.close()

print(f"\n  Recovery assessment:")
print(f"    Request body hash = SHA256(json.dumps(PaymentRequirements)) — one-way")
print(f"    Dict contains 'path' but hash cannot be reversed")
print(f"    Log file DOES contain country name per entry")
print(f"    Can cross-reference: invoice issued_at timestamp ↔ log timestamps")
print(f"    Log format: ts|status|country|endpoint|method|status|ip|amount|has_pay_sig|hash|latency|resp_size")

print(f"\n--- 6. Canary Recommendation ---")
print(f"  Country: italy-bot-api")
print(f"  Reason: Already running new x402 v2 code, low traffic, isolated")
print(f"  Steps:")
print(f"    1. Backup: cp /opt/xrplme/thoughts/api/sqlite_invoice_store.py /home/xrpladmin/xrplme-state/backups/sqlite_invoice_store.py.20260922.bak")
print(f"    2. Add country: str = None parameter to put() method signature")
print(f"    3. Replace hardcoded country string with parameter (defaults to thailand)")
print(f"    4. py_compile the file")
print(f"    5. Restart only italy-bot-api")
print(f"    6. Request 402, verify invoice in DB has country=italy")
print(f"    7. Verify old invoices still readable")
print(f"    8. Monitor logs")
print(f"    9. Rollback if needed")

print(f"\n{'=' * 80}")
print("AUDIT COMPLETE")
print(f"{'=' * 80}")
