#!/usr/bin/env python3
"""Verify Italy invoices in SQLite."""
import sqlite3, re

conn = sqlite3.connect("/home/xrpladmin/xrplme-state/x402.sqlite3")
c = conn.cursor()

print("=== Recent invoices (last 5) ===")
c.execute("SELECT invoice_id, country, endpoint_tier, expected_amount_drops, status, issued_at FROM invoices ORDER BY issued_at DESC LIMIT 5")
for r in c.fetchall():
    print(f"  id={r[0][:16]}... country={r[1]} tier={r[2]} amount={r[3]} status={r[4]} ts={r[5]:.0f}")

print(f"\n=== Invoice uniqueness ===")
c.execute("SELECT COUNT(DISTINCT invoice_id) FROM invoices")
distinct = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM invoices")
total = c.fetchone()[0]
print(f"  Distinct: {distinct} / Total: {total}")

print(f"\n=== used_tx_registry ===")
c.execute("SELECT COUNT(*) FROM used_tx_registry")
print(f"  Entries: {c.fetchone()[0]}")

print(f"\n=== Invoice ID format check ===")
c.execute("SELECT invoice_id FROM invoices ORDER BY issued_at DESC LIMIT 5")
for r in c.fetchall():
    inv = r[0]
    is_hex_32 = bool(re.match(r'^[0-9a-f]{32}$', inv)) and len(inv) == 32
    print(f"  {inv} (len={len(inv)}, 32-char hex: {is_hex_32})")

print(f"\n=== Country distribution ===")
c.execute("SELECT country, COUNT(*) FROM invoices GROUP BY country ORDER BY COUNT(*) DESC")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
