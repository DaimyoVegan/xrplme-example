#!/usr/bin/env python3
"""Add /wc/v1/ routes for 5 APAC countries to xrplme-online-https config."""
import os, re

CONF = "/etc/nginx/sites-available/xrplme-online-https"
OUT = "/tmp/nginx_apac_wc_routes.conf"

with open(CONF, "r") as f:
    content = f.read()

APAC = [
    ("brunei", 8111, "Brunei"),
    ("laos", 8112, "Laos"),
    ("myanmar", 8113, "Myanmar"),
    ("timor-leste", 8114, "Timor-Leste"),
    ("papua-new-guinea", 8115, "Papua New Guinea"),
]

# Check existing routes
existing = set()
for m in re.finditer(r'location\s*=\s*/wc/v1/(\S+)/bot', content):
    existing.add(m.group(1))
print(f"Existing /wc/v1/ routes: {sorted(existing)}")

routes = []
for slug, port, display in APAC:
    if slug in existing:
        print(f"  SKIP {slug}: already has /wc/v1/ route")
        continue
    routes.append(f"""
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
    }}""")

if routes:
    all_routes = "\n".join(routes)
    lines = content.split('\n')
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == '}':
            lines.insert(i, all_routes)
            break
    with open(OUT, "w") as f:
        f.write('\n'.join(lines))
    print(f"Written: {OUT} ({len(lines)} lines, {os.path.getsize(OUT)} bytes)")
    print(f"Apply: sudo cp {OUT} {CONF} && sudo nginx -t && sudo nginx -s reload")

    # Verify
    with open(OUT, "r") as f:
        new_content = f.read()
    for slug, port, display in APAC:
        if f"wc/v1/{slug}/bot" in new_content:
            print(f"  VERIFIED: {slug}")
        else:
            print(f"  MISSING: {slug}")
else:
    print("All 5 APAC countries already have /wc/v1/ routes!")
