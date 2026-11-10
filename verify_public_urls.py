#!/usr/bin/env python3
"""Verify public URL access for 5 APAC countries + check nginx routes."""
import requests
import subprocess

APAC = [
    ("brunei", 8111, "brunei"),
    ("laos", 8112, "laos"),
    ("myanmar", 8113, "myanmar"),
    ("timor-leste", 8114, "timor-leste"),
    ("papua-new-guinea", 8115, "papua-new-guinea"),
]

print("=== NGINX ROUTE CHECK ===\n")

# Check existing nginx config for these countries
result = subprocess.run(
    ["grep", "-c", "wc/v1/brunei/bot"],
    capture_output=True, text=True, cwd="/etc/nginx/sites-available/xrplme-online-https"
)

import os
nginx_conf = "/etc/nginx/sites-available/xrplme-online-https"

for slug, port, name in APAC:
    try:
        result = subprocess.run(
            ["grep", f"wc/v1/{slug}/bot"],
            capture_output=True, text=True
        )
        if result.stdout:
            print(f"  {slug}: nginx route EXISTS")
        else:
            print(f"  {slug}: nginx route MISSING")
    except:
        print(f"  {slug}: can't check")

print("\n=== PUBLIC URL 402 CHECK ===\n")

DEDAK = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

for slug, port, name in APAC:
    url = f"https://xrplme.online/wc/v1/{slug}/bot"
    try:
        r = requests.post(url, json={"message": "test", "session_id": "t"}, timeout=10)
        if r.status_code == 402:
            d = r.json()
            p = d.get("accepts", [{}])[0]
            pt = p.get("payTo") or p.get("pay_to", "")
            amt = p.get("amount", "")
            is_ded = "YES" if pt == DEDAK else "NO"
            print(f"  {slug}: HTTP 402, payTo={pt[:20]}..., amount={amt}, Ded={is_ded}")
        else:
            print(f"  {slug}: HTTP {r.status_code} - UNEXPECTED")
    except Exception as e:
        print(f"  {slug}: PUBLIC URL ERROR - {e}")

print("\n=== HEALTH VIA PUBLIC URL ===\n")

for slug, port, name in APAC:
    url = f"https://xrplme.online/wc/v1/{slug}/health"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and "application/json" in r.headers.get("content-type", ""):
            d = r.json()
            print(f"  {slug}: HTTP 200, records={d.get('data_records')}, country={d.get('country')}")
        elif r.status_code == 404:
            print(f"  {slug}: HTTP 404 (health route not in nginx)")
        else:
            ctype = r.headers.get("content-type", "unknown")
            print(f"  {slug}: HTTP {r.status_code}, content-type={ctype}")
    except Exception as e:
        print(f"  {slug}: ERROR - {e}")
