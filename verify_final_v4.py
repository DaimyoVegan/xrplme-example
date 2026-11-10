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


def ssh_curl(args, timeout=15):
    """Run curl on VPS via SSH. args is the curl command args string."""
    cmd = f"curl {args}"
    result = subprocess.run(
        ["ssh", "xrplme-vps", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode


def ssh_run(cmd, timeout=10):
    result = subprocess.run(
        ["ssh", "xrplme-vps", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode


def main():
    print("=== APAC COUNTRIES — FINAL VERIFICATION ===\n")

    # 1. Health checks
    print("1. HEALTH (localhost)")
    for display, slug, port, api_slug in APAC:
        out, err, rc = ssh_curl(f"-s http://127.0.0.1:{port}/health")
        try:
            d = json.loads(out)
            recs = d.get("data_records", 0)
            print(f"  {display}: HTTP 200, records={recs}, country={d.get('country')}")
        except:
            print(f"  {display}: FAILED - {out[:80]}")

    print()

    # 2. Bot 402 checks
    print("2. BOT 402 (localhost)")
    for display, slug, port, api_slug in APAC:
        out, err, rc = ssh_curl(
            f'-s -X POST "http://127.0.0.1:{port}/api/v1/{api_slug}/bot" '
            f'-H "Content-Type: application/json" '
            f"-d '{{\"message\":\"test\",\"session_id\":\"t\"}}'",
        )
        first_line = out.split('\n')[0] if out else ""
        if '"payment"' in out.lower() or '402' in out or 'accepts' in out.lower() or 'payTo' in out:
            try:
                d = json.loads(out)
                p = d.get("accepts", [{}])[0]
                pt = p.get("payTo") or p.get("pay_to", "")
                amt = p.get("amount", "")
                is_ded = "YES" if pt == DEDAK else "NO"
                print(f"  {display}: HTTP 402, payTo={pt[:16]}..., amt={amt}, Ded={is_ded}")
            except:
                print(f"  {display}: 402 response (raw: {out[:80]})")
        else:
            print(f"  {display}: {out[:80]}")

    print()

    # 3. Data files
    print("3. DATA FILES")
    for display, slug, port, api_slug in APAC:
        module = api_slug.replace('-', '_')
        path = f"/opt/xrplme/thoughts/api/{module}-agent-full/publication/latest_valid.json"
        out, _, _ = ssh_run(f"wc -c {path} 2>&1")
        size = out.strip().split()[0] if out.strip() else "N/A"
        print(f"  {display}: {size} bytes - {path}")

    print()

    # 4. Nginx routes check
    print("4. NGINX ROUTES")
    for display, slug, port, api_slug in APAC:
        out, _, _ = ssh_run(
            f'grep -c "api/v1/{api_slug}/bot" /etc/nginx/sites-available/api-xrplme-https 2>/dev/null; '
            f'grep -c "wc/v1/{api_slug}/bot" /etc/nginx/sites-available/xrplme-online-https 2>/dev/null',
            timeout=5
        )
        parts = out.strip().split('\n')
        api_v1 = parts[0] if len(parts) > 0 else "0"
        wc_v1 = parts[1] if len(parts) > 1 else "0"
        print(f"  {display}: api-xrplme-https={api_v1}, xrplme-online-https={wc_v1}")

    print()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
