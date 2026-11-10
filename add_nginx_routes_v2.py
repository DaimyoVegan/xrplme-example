#!/usr/bin/env python3
"""Add nginx routes for 5 new APAC countries to xrplme-online-https config."""
import os
import re

NGINX_CONF = "/etc/nginx/sites-available/xrplme-online-https"
# Also check the alternative config name
ALT_CONF = "/etc/nginx/sites-available/api-xrplme-https"

COUNTRIES = [
    ("brunei", 8111, "Brunei"),
    ("laos", 8112, "Laos"),
    ("myanmar", 8113, "Myanmar"),
    ("timor-leste", 8114, "Timor-Leste"),
    ("papua-new-guinea", 8115, "Papua New Guinea"),
]

# Read the nginx config
for conf_path in [NGINX_CONF, ALT_CONF]:
    if os.path.exists(conf_path):
        NGINX_CONF = conf_path
        break

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
    print(f"\nAdding nginx routes for: {[r[0] for r in routes_to_add]}")
    
    # Build the route block
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
    
    # Find insertion point: before the last } in the file (server block close)
    lines = content.split('\n')
    inserted = False
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == '}':
            # This is likely the server block closing brace
            # Insert before it
            lines.insert(i, all_routes)
            inserted = True
            break
    
    if inserted:
        # Write backup
        with open(NGINX_CONF + ".bak", "w") as f:
            f.write(content)
        
        # Write new config
        new_content = '\n'.join(lines)
        with open(NGINX_CONF, "w") as f:
            f.write(new_content)
        
        print(f"\n  Nginx config updated: {NGINX_CONF}")
        print(f"  Backup saved: {NGINX_CONF}.bak")
    else:
        print("  ERROR: Could not find insertion point")

# Verify
print("\n=== Verification ===")
with open(NGINX_CONF, "r") as f:
    new_content = f.read()

for slug, port, display in COUNTRIES:
    if f"wc/v1/{slug}/bot" in new_content:
        print(f"  {display} ({slug}): nginx route ADDED")
    else:
        print(f"  {display} ({slug}): nginx route NOT FOUND")

print(f"\nFile size: {os.path.getsize(NGINX_CONF)} bytes")
