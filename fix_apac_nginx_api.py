#!/usr/bin/env python3
"""Add nginx /api/v1/ routes for 5 APAC countries to api-xrplme-https."""
import os
import re

NGINX_CONF = "/etc/nginx/sites-available/api-xrplme-https"

COUNTRIES = [
    ("brunei", 8111, "Brunei"),
    ("laos", 8112, "Laos"),
    ("myanmar", 8113, "Myanmar"),
    ("timor-leste", 8114, "Timor-Leste"),
    ("papua-new-guinea", 8115, "Papua New Guinea"),
]

with open(NGINX_CONF, "r") as f:
    content = f.read()

# Check which countries already have routes
existing = set()
for m in re.finditer(r'location\s*=\s*/api/v1/(\S+)/bot', content):
    existing.add(m.group(1))

routes_to_add = []
for slug, port, display in COUNTRIES:
    if slug in existing:
        print(f"  {slug}: ALREADY has /api/v1/ routes (skipping)")
        continue
    routes_to_add.append((slug, port, display))

if not routes_to_add:
    print("All 5 APAC countries already have /api/v1/ routes!")
else:
    print(f"\nAdding /api/v1/ routes for: {[r[0] for r in routes_to_add]}")
    
    route_blocks = []
    for slug, port, display in routes_to_add:
        block = f"""
    # {display}
    location = /api/v1/{slug}/bot {{
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:{port}/api/v1/{slug}/bot;
    }}
    location = /api/v1/{slug}/bot/ai {{
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:{port}/api/v1/{slug}/bot/ai;
    }}
    location = /api/v1/{slug}/health {{
        proxy_pass http://127.0.0.1:{port}/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}"""
        route_blocks.append(block)
    
    all_routes = "\n".join(route_blocks)
    
    lines = content.split('\n')
    inserted = False
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == '}':
            lines.insert(i, all_routes)
            inserted = True
            break
    
    if inserted:
        # Write to temp file for user to apply with sudo
        temp_path = "/tmp/nginx_config_apac_api_routes.conf"
        with open(temp_path, "w") as f:
            f.write('\n'.join(lines))
        
        print(f"  Written to: {temp_path}")
        print(f"  Original size: {len(content)} bytes")
        print(f"  New size: {len(chr(10).join(lines))} bytes")
        
        # Verify all 5 are present
        new_content = '\n'.join(lines)
        for slug, port, display in COUNTRIES:
            if f"api/v1/{slug}/bot" in new_content:
                print(f"  VERIFIED: {slug} routes present")
            else:
                print(f"  MISSING: {slug} routes")
        
        print(f"\nApply with:")
        print(f"  sudo cp {temp_path} {NGINX_CONF}")
        print(f"  sudo nginx -t && sudo nginx -s reload")
    else:
        print("  ERROR: Could not find insertion point")
