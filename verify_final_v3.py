#!/usr/bin/env python3
"""Verify all 5 APAC countries on VPS via direct curl + public URL."""
import json
import subprocess

APAC = [
    ("Brunei", "brunei", 8111, "brunei"),
    ("Laos", "laos", 8112, "laos"),
    ("Myanmar", "myanmar", 8113, "myanmar"),
    ("Timor-Leste", "timor-leste", 8114, "timor-leste"),
    ("Papua New Guinea", "papua-new-guinea", 8115, "papua-new-guinea"),
]

DEDAK = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

print("=== APAC COUNTRIES — FINAL VERIFICATION ===\n")

# Direct health checks
print("1. HEALTH (localhost)")
for display, slug, port, api_slug in APAC:
    out, err, rc = ssh_curl(f"http://127.0.0.1:{port}/health")
    try:
        d = json.loads(out)
        recs = d.get("data_records", 0)
        print(f"  {display}: HTTP 200, records={recs}, country={d.get('country')}")
    except:
        print(f"  {display}: FAILED - {out[:80]}")

print()

# Direct bot 402 checks
print("2. BOT 402 (localhost)")
for display, slug, port, api_slug in APAC:
    out, err, rc = ssh_curl(f"http://127.0.0.1:{port}/api/v1/{api_slug}/bot", method="POST")
    code = out.strip()[:3]  # get HTTP code from output
    if code == "402":
        try:
            d = json.loads(out)
            p = d.get("accepts", [{}])[0]
            pt = p.get("payTo") or p.get("pay_to", "")
            amt = p.get("amount", "")
            is_ded = "YES" if pt == DEDAK else "NO"
            print(f"  {display}: HTTP 402, payTo={pt[:16]}..., amt={amt}, Ded={is_ded}")
        except:
            print(f"  {display}: HTTP 402 (JSON parse issue)")
    else:
        print(f"  {display}: HTTP {code} - UNEXPECTED")

print()

# Data files
print("3. DATA FILES")
for display, slug, port, api_slug in APAC:
    path = f"/opt/xrplme/thoughts/api/{slug.replace('-', '_')}-agent-full/publication/latest_valid.json"
    out, err, rc = ssh_run(f"wc -c {path} 2>&1")
    size = out.strip().split()[0] if out.strip() else "N/A"
    print(f"  {display}: {size} bytes - {path}")


def ssh_curl(url, method="GET"):
    if method == "POST":
        cmd = f'curl -s -X POST "{url}" -H "Content-Type: application/json" -d \'{{"message":"test","session_id":"t"}}\''
    else:
        cmd = f'curl -s "{url}"'
    result = subprocess.run(
        ["ssh", "xrplme-vps", cmd],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout, result.stderr, result.returncode


def ssh_run(cmd):
    result = subprocess.run(
        ["ssh", "xrplme-vps", cmd],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout, result.stderr, result.returncode


if __name__ == "__main__":
    pass
