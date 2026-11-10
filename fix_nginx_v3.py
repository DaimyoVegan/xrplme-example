#!/usr/bin/env python3
"""Fix nginx config: insert APAC routes in the correct server block (HTTPS, not port 80 redirect)."""
import os, re

CONF = "/etc/nginx/sites-available/xrplme-online-https"
OUT = "/tmp/nginx_apac_routes_fixed.conf"

with open(CONF, "r") as f:
    content = f.read()

APAC = [
    ("brunei", 8111, "Brunei"),
    ("laos", 8112, "Laos"),
    ("myanmar", 8113, "Myanmar"),
    ("timor-leste", 8114, "Timor-Leste"),
    ("papua-new-guinea", 8115, "Papua New Guinea"),
]

# 1. Remove any existing APAC routes (from the broken insertion)
# Find patterns like "    # Brunei" followed by location blocks
for slug, port, display in APAC:
    # Remove the incorrectly placed route blocks
    pattern = rf"""
    # {display}
    location = /wc/v1/{slug}/bot \{
        include /etc/nginx/x402-api-std\.conf;
        proxy_pass http://127\.0\.0\.1:{port}/api/v1/{slug}/bot;
    \}}
    location = /wc/v1/{slug}/bot/ai \{
        include /etc/nginx/x402-api-ai\.conf;
        proxy_pass http://127\.0\.0\.1:{port}/api/v1/{slug}/bot/ai;
    \}}
    location = /wc/v1/{slug}/health \{
        proxy_pass http://127\.0\.0\.1:{port}/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    \}\}"""
    content = re.sub(pattern, "", content, flags=re.MULTILINE)

# 2. Insert APAC routes before the "return 301" server block 
# (which is the port 80 redirect block — we want routes in the HTTPS block before this)
# The correct insertion point is before "server {" that contains "listen 80"
insert_point = content.rfind("\n    server {\n        listen 80;")
if insert_point == -1:
    # Try another pattern
    insert_point = content.find("\nserver {\n    listen 80;")

if insert_point == -1:
    print("ERROR: Could not find port 80 redirect server block")
    # Fallback: insert before the last "server {" 
    servers = [m.start() for m in re.finditer(r'server\s*\{', content)]
    if len(servers) >= 2:
        insert_point = servers[-1]
    else:
        print("ERROR: No suitable insertion point")
else:
    # Insert before the blank line + server block
    while insert_point > 0 and content[insert_point - 1] in ['\n', ' ']:
        insert_point -= 1
    if insert_point > 0:
        insert_point += 1  # After the newline

routes = []
for slug, port, display in APAC:
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

route_text = "\n".join(routes)

# Insert at the right position
new_content = content[:insert_point] + route_text + "\n" + content[insert_point:]

with open(OUT, "w") as f:
    f.write(new_content)

print(f"Written: {OUT} ({os.path.getsize(OUT)} bytes)")

# Verify
for slug, port, display in APAC:
    count = new_content.count(f"wc/v1/{slug}/bot")
    status = "VERIFIED" if count >= 2 else f"MISSING ({count})"
    print(f"  {slug}: {status}")

# Check server blocks
servers = new_content.count("server {")
print(f"\nServer blocks: {servers}")

# Check the routes are in the HTTPS block (before listen 80)
listen_80_pos = new_content.find("listen 80")
brunei_pos = new_content.find("wc/v1/brunei/bot")
if brunei_pos < listen_80_pos:
    print("Routes are in HTTPS block (before listen 80) ✅")
else:
    print("Routes are AFTER listen 80 (still in wrong block!) ❌")

print(f"\nApply: sudo cp {OUT} {CONF} && sudo nginx -t && sudo nginx -s reload")
