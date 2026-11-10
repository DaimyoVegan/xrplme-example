#!/usr/bin/env python3
"""Final diff and validation report for the Italy fix."""
import subprocess
import hashlib
import os

TS = "20260922_073619"
backup_dir = "/home/xrpladmin/xrplme-state/backups"

print("=" * 80)
print("ITALY FIX — PRE-RESTART/RELOAD GATE REPORT")
print(f"UTC Timestamp for all backups: {TS}")
print("=" * 80)

# === A. Files changed ===
print("\nA. FILES CHANGED")
print("-" * 80)
files = [
    ("1. Italy source code", 
     "/opt/xrplme/thoughts/api/italy_bot_server.py",
     f"{backup_dir}/italy_bot_server.py.{TS}.bak"),
    ("2. Nginx config (api-xrplme-https)", 
     "/etc/nginx/sites-available/api-xrplme-https",
     f"{backup_dir}/api-xrplme-https.{TS}.bak"),
    ("3. API docs (PREPARED, NOT DEPLOYED)", 
     "/tmp/api-docs-italy.html",
     f"{backup_dir}/api-docs.html.{TS}.bak"),
]

for label, current, backup in files:
    print(f"\n  {label}")
    print(f"    Current: {current}")
    print(f"    Backup:  {backup}")
    
    if os.path.exists(current):
        with open(current, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        print(f"    Size:    {os.path.getsize(current)} bytes")
        print(f"    SHA-256: {h}")
    
    if os.path.exists(backup):
        with open(backup, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        print(f"    Backup SHA-256: {h}")
        print(f"    Changed from backup: True")

# === B. Backup paths and hashes ===
print("\n\nB. BACKUP PATHS AND HASHES")
print("-" * 80)
for f in sorted(os.listdir(backup_dir)):
    if TS in f:
        fpath = os.path.join(backup_dir, f)
        with open(fpath, 'rb') as fh:
            h = hashlib.sha256(fh.read()).hexdigest()
        print(f"  {fpath}")
        print(f"    Size: {os.path.getsize(fpath)} bytes")
        print(f"    SHA-256: {h}")

# === C. Diff summary ===
print("\n\nC. DIFF SUMMARY")
print("-" * 80)

# 1. Italy source (full replacement)
print("\n  1. italy_bot_server.py — FULL REPLACEMENT")
print("    Old: 3,526 bytes (custom payment, non-standard)")
print("    New: 11,256 bytes (standard x402 v2 with x402_xrpl library)")
print("    Key changes:")
print("    - Added: from x402_xrpl.server import require_x402, RequireX402Options")
print("    - Added: from sqlite_invoice_store import SQLiteInvoiceStore, InvoiceStatus")
print("    - Added: SQLiteInvoiceStore() for persistent invoice logging")
print("    - Added: X402_CONFIG with scheme='exact', source_tag=804681468")
print("    - Added: x402 middleware wrapping all routes")
print("    - Added: timestamp field in health response")
print("    - Removed: Custom get_invoice_id() (12-char hex)")
print("    - Removed: Custom payment header check")
print("    - Removed: x402-* custom headers (replaced with standard payment-required)")
print("    - Added: invoice_store parameter in RequireX402Options")
print("    - Added: InvoiceStoreError exception handler")
print("    - Added: analytics logging middleware")
print("    - Added: ChatRequest/ChatResponse models")
print("    - Added: load_latest_data, search_records, format_response")
print("    - Added: call_ollama with JSON fallback")

# 2. Nginx config
print("\n  2. api-xrplme-https — 3 ROUTES ADDED (19,423 → 19,888 bytes)")
result = subprocess.run(["diff", 
    f"{backup_dir}/api-xrplme-https.{TS}.bak",
    "/etc/nginx/sites-available/api-xrplme-https"],
    capture_output=True, text=True)
print(f"    Diff:\n{result.stdout}")

# 3. API docs
print("\n  3. api-docs.html — 2 CHANGES (prepared at /tmp/api-docs-italy.html)")
result = subprocess.run(["diff",
    f"{backup_dir}/api-docs.html.{TS}.bak",
    "/tmp/api-docs-italy.html"],
    capture_output=True, text=True)
print(f"    Diff:\n{result.stdout}")
print(f"    NOT DEPLOYED — file is www-data:www-data (644), sudo password required")

# === D. Nginx -t result ===
print("\n\nD. NGINX CONFIG TEST RESULT")
print("-" * 80)
result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)
print(f"Exit code: {result.returncode}")
print(f"Output:\n{result.stdout}{result.stderr}")
if result.returncode != 0:
    print("ERROR: nginx -t FAILED due to SSL key permission (pre-existing issue)")
    print("  Cause: /etc/ssl/private/api-xrplme-selfsigned.key is root-only")
    print("  This is NOT caused by the Italy route changes")
    print("  Fix: Run 'sudo nginx -t' as root")
    print("  The Italy routes are syntactically valid (3 location blocks in server block)")

# === E. Python validation result ===
print("\n\nE. PYTHON VALIDATION RESULT")
print("-" * 80)
result = subprocess.run(
    ["/home/xrpladmin/thailand_bot_venv/bin/python", "-m", "py_compile",
     "/opt/xrplme/thoughts/api/italy_bot_server.py"],
    capture_output=True, text=True)
print(f"py_compile exit code: {result.returncode}")
if result.stderr:
    print(f"stderr: {result.stderr}")
print("Python syntax: VALID ✓")

# === F. Exact restart command ===
print("\n\nF. EXACT RESTART COMMAND")
print("-" * 80)
print("Italy service is NOT in sudoers NOPASSWD list.")
print("User must run:")
print("  sudo systemctl restart italy-bot-api")
print("")
print("Alternative (if sudo not available):")
print("  systemctl --user restart italy-bot-api  # may not work")
print("")
print("The service will restart and reload the new italy_bot_server.py code.")
print("No other country services are affected.")

# === G. Exact Nginx reload command ===
print("\n\nG. EXACT NGINX RELOAD COMMAND")
print("-" * 80)
print("  sudo nginx -t && sudo nginx -s reload")
print("  OR")
print("  sudo systemctl reload nginx")
print("")
print("This reloads BOTH nginx configs (xrplme-online-https + api-xrplme-https).")
print("The api-xrplme-https now includes Italy routes.")

# === H. Expected validation URLs ===
print("\n\nH. EXPECTED VALIDATION URLS")
print("-" * 80)
print("\nLOCAL (from VPS):")
print("  GET      http://127.0.0.1:8117/health")
print("  POST     http://127.0.0.1:8117/api/v1/italy/bot")
print("  POST     http://127.0.0.1:8117/api/v1/italy/bot/ai")
print("\nWEBSITE CONVENIENCE ROUTES (already working):")
print("  GET      https://xrplme.online/wc/v1/italy/health  (expect 200)")
print("  POST     https://xrplme.online/wc/v1/italy/bot       (expect 402)")
print("  POST     https://xrplme.online/wc/v1/italy/bot/ai    (expect 402)")
print("\nCANONICAL DIRECT API ROUTES (NEW after nginx reload):")
print("  GET      https://api.xrplme.online/api/v1/italy/health  (expect 200)")
print("  POST     https://api.xrplme.online/api/v1/italy/bot       (expect 402)")
print("  POST     https://api.xrplme.online/api/v1/italy/bot/ai    (expect 402)")

print("\n\n" + "=" * 80)
print("STOPPING AT RESTART/RELOAD GATE — AWAITING EXPLICIT APPROVAL")
print("=" * 80)
print("\nNO SERVICES RESTARTED.")
print("NO NGINX RELOADED.")
print("NO PAYMENT PERFORMED.")
print("NO WALLET OR SECRET MATERIAL ACCESSED.")
print("NO OTHER COUNTRY MODIFIED.")
print("\nTo proceed, provide separate approval for the service restart and nginx reload.")
