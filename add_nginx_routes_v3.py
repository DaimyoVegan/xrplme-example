#!/usr/bin/env python3
"""Add nginx routes for 5 new APAC countries - writes to temp file."""
import os
import re
import json

NGINX_CONF = "/etc/nginx/sites-available/xrplme-online-https"

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
for m in re.finditer(r'location\s*=\s*/wc/v1/(\S+)/bot', content):
    existing.add(m.group(1))

routes_to_add = []
for slug, port, display in COUNTRIES:
    if slug in existing:
        print(f"  {slug}: ALREADY has nginx routes (skipping)")
        continue
    routes_to_add.append((slug, port, display))

if not routes_to_add:
    print("All 5 APAC countries already have nginx routes!")
else:
    print(f"Adding routes for: {[r[0] for r in routes_to_add]}")
    
    route_blocks = []
    for slug, port, display in routes_to_add:
        block = f"""
    # {display}
    location = /wc/v1/{slug}/bot {{
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:{port}/api/v1/{slug}/bot;
    }}
    location = /wc/v1/{slug}/bot/ai {{
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:{port}/api/v1/{slug}/bot/ai;
    }}
    location = /wc/v1/{slug}/health {{
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
        new_content = '\n'.join(lines)
        with open("/tmp/nginx_config_new.conf", "w") as f:
            f.write(new_content)
        print(f"  Written to /tmp/nginx_config_new.conf")
        print(f"  Original size: {len(content)} bytes")
        print(f"  New size: {len(new_content)} bytes")
    else:
        print("  ERROR: Could not find insertion point")

# Verify
print("\n=== Verification ===")
with open("/tmp/nginx_config_new.conf", "r") as f:
    new_content = f.read()

for slug, port, display in COUNTRIES:
    if f"wc/v1/{slug}/bot" in new_content:
        print(f"  {display} ({slug}): nginx route ADDED")
    else:
        print(f"  {display} ({slug}): nginx route NOT FOUND")

# Save results as JSON for the shell script to read
results = {"output_file": "/tmp/nginx_config_new.conf", "countries_added": [r[0] for r in routes_to_add]}
with open("/tmp/nginx_route_results.json", "w") as f:
    json.dump(results, f)
