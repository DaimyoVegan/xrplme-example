#!/usr/bin/env python3
"""Fix nginx config: move APAC routes into the main HTTPS server block."""
import os, re

CONF = "/etc/nginx/sites-available/xrplme-online-https"
OUT = "/tmp/nginx_apac_routes_fixed.conf"

with open(CONF, "r") as f:
    content = f.read()

# Remove the incorrectly placed APAC routes (they're in the port 80 redirect block)
# Find and remove lines from "# Brunei" through the end of the papua-new-guinea health block
# that are AFTER the "return 301" line

lines = content.split('\n')
new_lines = []
skip = False
for i, line in enumerate(lines):
    if 'return 301 https://$host$request_uri;' in line:
        new_lines.append(line)
        skip = False  # Don't skip, but the APAC routes after it should be removed
        continue
    
    # Skip lines that are the incorrectly inserted APAC routes
    if 'location = /wc/v1/brunei/bot' in line or \
       'location = /wc/v1/laos/bot' in line or \
       'location = /wc/v1/myanmar/bot' in line or \
       'location = /wc/v1/timor-leste/bot' in line or \
       'location = /wc/v1/papua-new-guinea/bot' in line:
        skip = True
        continue
    
    if skip:
        if line.strip() == '}' or (line.strip().startswith('#') and 'Brunei' in line) or \
           line.strip().startswith('location') or line.strip().startswith('proxy_') or \
           line.strip().startswith('include') or line.strip() == '' or \
           line.strip().startswith('proxy_set_header'):
            continue
        else:
            skip = False
            new_lines.append(line)
    else:
        new_lines.append(line)

# Now find the correct insertion point in the main server block
# Find the last location block before the server block closes
content = '\n'.join(new_lines)

# Find the main server block (starts at line 13, the first "server {")
# We want to insert before the closing } of that server block
# Find all "location = /wc/v1/..." blocks and insert after the last one
last_location = -1
for m in re.finditer(r'location\s*=\s*/wc/v1/\S+/health', content):
    last_location = m.end()
    
if last_location > 0:
    # Insert after the last health location block's closing }
    # Find the closing } of this block
    after_location = content[last_location:]
    # Find the next standalone }
    brace_match = re.search(r'^\s*\}', after_location, re.MULTILINE)
    if brace_match:
        insert_pos = last_location + brace_match.end()
else:
    # Fallback: insert before the last } in the main server block
    # The main server block closes before "server {" at line 517
    lines2 = content.split('\n')
    for i in range(len(lines2) - 1, -1, -1):
        if lines2[i].strip() == '}':
            if i > 0 and 'server' in lines2[i-1] and '{' in lines2[i-1]:
                # This is a server block closing brace - skip it
                continue
            insert_pos = sum(len(l) + 1 for l in lines2[:i])
            break

APAC_ROUTES = """
    # Brunei
    location = /wc/v1/brunei/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8111/api/v1/brunei/bot;
    }
    location = /wc/v1/brunei/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8111/api/v1/brunei/bot/ai;
    }
    location = /wc/v1/brunei/health {
        proxy_pass http://127.0.0.1:8111/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Laos
    location = /wc/v1/laos/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8112/api/v1/laos/bot;
    }
    location = /wc/v1/laos/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8112/api/v1/laos/bot/ai;
    }
    location = /wc/v1/laos/health {
        proxy_pass http://127.0.0.1:8112/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Myanmar
    location = /wc/v1/myanmar/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8113/api/v1/myanmar/bot;
    }
    location = /wc/v1/myanmar/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8113/api/v1/myanmar/bot/ai;
    }
    location = /wc/v1/myanmar/health {
        proxy_pass http://127.0.0.1:8113/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Timor-Leste
    location = /wc/v1/timor-leste/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8114/api/v1/timor-leste/bot;
    }
    location = /wc/v1/timor-leste/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8114/api/v1/timor-leste/bot/ai;
    }
    location = /wc/v1/timor-leste/health {
        proxy_pass http://127.0.0.1:8114/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Papua New Guinea
    location = /wc/v1/papua-new-guinea/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8115/api/v1/papua-new-guinea/bot;
    }
    location = /wc/v1/papua-new-guinea/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8115/api/v1/papua-new-guinea/bot/ai;
    }
    location = /wc/v1/papua-new-guinea/health {
        proxy_pass http://127.0.0.1:8115/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""

# Simple approach: just insert before the second "server {" block
# (which is the port 80 redirect block)
lines2 = content.split('\n')
inserted = False
for i in range(len(lines2) - 1, -1, -1):
    if lines2[i].strip() == 'server' and i + 1 < len(lines2) and '{' in lines2[i + 1]:
        # This is a "server {" line - insert before it
        lines2.insert(i, APAC_ROUTES.strip().split('\n'))
        inserted = True
        break

if not inserted:
    # Fallback: insert before the last } of the first server block
    # Find "return 301" and the server block that contains it
    for i in range(len(lines2) - 1, -1, -1):
        if 'return 301 https' in lines2[i]:
            # Insert before this server block starts
            # Walk back to find "server {"
            for j in range(i - 1, -1, -1):
                if lines2[j].strip() == 'server' and j + 1 < len(lines2) and '{' in lines2[j + 1]:
                    lines2 = lines2[:j] + APAC_ROUTES.strip().split('\n') + lines2[j:]
                    inserted = True
                    break
            break

with open(OUT, "w") as f:
    f.write('\n'.join(lines2))

print(f"Written: {OUT}")
print(f"Size: {os.path.getsize(OUT)} bytes")

# Verify
with open(OUT, "r") as f:
    new_content = f.read()
for slug in ["brunei", "laos", "myanmar", "timor-leste", "papua-new-guinea"]:
    if f"wc/v1/{slug}/bot" in new_content:
        print(f"  VERIFIED: {slug}")
    else:
        print(f"  MISSING: {slug}")

# Count server blocks
servers = new_content.count("server {")
print(f"\nServer blocks: {servers}")
print(f"Apply: sudo cp {OUT} {CONF}")
