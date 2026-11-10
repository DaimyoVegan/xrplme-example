#!/usr/bin/env python3
"""Check invoice store for various countries and payments."""
import sqlite3

conn = sqlite3.connect("/home/xrpladmin/xrplme-state/x402.sqlite3")
cursor = conn.cursor()

# Check which countries have invoices
cursor.execute("SELECT DISTINCT country FROM invoices")
countries = cursor.fetchall()
print("Countries with invoices in x402.sqlite3:")
for c in countries:
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE country=?", (c[0],))
    count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE country=? AND status='paid_authorized'", (c[0],))
    paid = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE country=? AND status='issued'", (c[0],))
    issued = cursor.fetchone()[0]
    print(f"  {c[0]:<20} total: {count:>4} | paid: {paid:>4} | issued: {issued:>4}")

# Check if Italy has invoices
print("\n=== Italy invoices ===")
cursor.execute("SELECT * FROM invoices WHERE country='italy' LIMIT 5")
rows = cursor.fetchall()
if rows:
    cols = [d[0] for d in cursor.description]
    print(f"Columns: {cols}")
    for row in rows:
        # Only show non-secret fields
        print(f"  invoice_id: {row[0]}, country: {row[2]}, tier: {row[3]}, amount: {row[6]}, status: {row[13]}")
else:
    print("  No invoices found for Italy")

# Check if APAC countries have invoices
print("\n=== APAC invoices ===")
for country in ["brunei", "laos", "myanmar", "timor-leste", "papua-new-guinea"]:
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE country=?", (country,))
    count = cursor.fetchone()[0]
    print(f"  {country}: {count} invoices")

# Check used_tx_reg for replay protection
print("\n=== Replay protection (used_tx_registry) ===")
cursor.execute("SELECT COUNT(*) FROM used_tx_registry")
print(f"  Total registered transactions: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(DISTINCT country) FROM used_tx_registry")
print(f"  Countries with registered txs: {cursor.fetchone()[0]}")

# Check payment proof digest
print("\n=== Payment proof digest ===")
cursor.execute("SELECT payment_proof_digest FROM invoices WHERE payment_proof_digest IS NOT NULL LIMIT 3")
proofs = cursor.fetchall()
print(f"  Invoices with payment_proof_digest: {len(proofs)}")
for p in proofs[:3]:
    print(f"  Proof digest: {p[0][:20]}... (length={len(p[0])})")

conn.close()
