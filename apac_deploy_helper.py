#!/usr/bin/env python3
"""
Quick deployment helper for 5 APAC countries.
Run after: python3 country_maker.py <country>

This script helps apply the nginx routes and website updates that need sudo.
"""
import os
import json

APAC = [
    ("Brunei", "brunei", 8111, "brunei_bot_server"),
    ("Laos", "laos", 8112, "laos_bot_server"),
    ("Myanmar", "myanmar", 8113, "myanmar_bot_server"),
    ("Timor-Leste", "timor-leste", 8114, "timor_leste_bot_server"),
    ("Papua New Guinea", "papua-new-guinea", 8115, "papua_new_guinea_bot_server"),
]

DEDAK = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"

print("=" * 60)
print("APAC COUNTRIES - DEPLOYMENT STATUS")
print("=" * 60)

print("\n1. FILES GENERATED:")
for display, slug, port, module in APAC:
    bot_path = f"/opt/xrplme/thoughts/api/{module}.py"
    scraper_path = f"/opt/xrplme/thoughts/api/{slug}_scraper.py"
    data_path = f"/opt/xrplme/thoughts/api/{slug}-agent-full/publication/latest_valid.json"
    
    bot = os.path.exists(bot_path) or os.path.exists(f"/opt/xrplme/thoughts/api/{module.replace('timor_leste', 'timor-leste').replace('papua_new_guinea', 'papua-new-guinea')}_bot_server.py")
    print(f"  {display}: port={port}, module={module}")

print("\n2. PROCESSES RUNNING:")
import subprocess
result = subprocess.run(
    ["ssh", "xrplme-vps", "ss -tlnp | grep -E '811[1-5]'"],
    capture_output=True, text=True, timeout=10
)
print(result.stdout.strip() or "  (check via: ssh xrplme-vps 'ss -tlnp | grep 811'")

print("\n3. NEEDS SUDO - RUN THESE COMMANDS:")
print("  sudo cp /tmp/nginx_config_apac_routes.conf /etc/nginx/sites-available/xrplme-online-https")
print("  sudo nginx -t && sudo nginx -s reload")
print("  sudo cp /tmp/api-docs-new.html /var/www/xrplme.online/api-docs.html")

print("\n4. VERIFICATION (after sudo):")
print(f"  curl -s https://xrplme.online/wc/v1/brunei/health")
print(f"  curl -s -X POST https://xrplme.online/wc/v1/brunei/bot -H 'Content-Type: application/json' -d '{{\"message\":\"test\"}}'")
