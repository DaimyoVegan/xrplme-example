#!/usr/bin/env python3
"""Fix the nginx config: move Italy routes to the correct server block (HTTPS)."""
import subprocess
import os

NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"
OUT = os.path.expanduser("~/nginx_italy_fixed.conf")

# Read current config via SSH
out, err, rc = subprocess.run(
    ["ssh", "xrplme-vps", f"cat {NGINX_CONFIG}"],
    capture_output=True, text=True, timeout=10
).returncode, None, None

result = subprocess.run(
    ["ssh", "xrplme-vps", f"cat {NGINX_CONFIG}"],
    capture_output=True, text=True, timeout=10
)
content = result.stdout
lines = content.split('\n')

# Find the Italy routes block (they're outside server, between 2 server blocks)
# Find line with "# Italy" that is NOT inside a server block
italy_routes = []
italy_start = None
italy_end = None
brace_depth = 0
in_http_redirect = False

for i, line in enumerate(lines):
    stripped = line.strip()
    # Track server blocks
    if 'server {' in stripped or (stripped.startswith('server') and '{' in stripped):
        brace_depth = 1
        if 'return 301' in '\n'.join(lines[i:i+3]):
            in_http_redirect = True
        else:
            in_http_redirect = False
    elif brace_depth > 0:
        brace_depth += stripped.count('{') - stripped.count('}')
        if brace_depth <= 0:
            brace_depth = 0
            in_http_redirect = False
    
    # Find Italy location blocks that are outside server blocks
    if 'location = /wc/v1/italy/' in stripped:
        if italy_start is None:
            italy_start = i - 1  # Include the "# Italy" comment if there is one
            # Go back to find comment
            while italy_start > 0 and lines[italy_start].strip().startswith('#') and 'Italy' not in lines[italy_start]:
                italy_start -= 1
            if '# Italy' in lines[italy_start]:
                italy_start = italy_start
            else:
                italy_start = i - 1
        # Find the closing brace of this location block
        depth = 0
        for j in range(i, min(i + 10, len(lines))):
            depth += lines[j].count('{') - lines[j].count('}')
            if depth <= 0:
                italy_end = j + 1
                break
        if italy_end is None:
            italy_end = i + 10
        italy_routes.extend(lines[i:italy_end])

# Remove the misplaced Italy routes
if italy_start is not None and italy_end is not None:
    removed = lines[italy_start:italy_end]
    del lines[italy_start:italy_end]
    print(f"Removed {len(removed)} lines of misplaced Italy routes")
else:
    print("Could not find misplaced Italy routes - they may have been removed already")
    # Check if Italy routes are in the correct place already
    pass

content = '\n'.join(lines)

# Now insert Italy routes before the closing "location /" block or before the last country in the HTTPS server
# Find the last country route block in the HTTPS server (before port 80 redirect)
# Strategy: find "return 301 https" and insert before the "server {" that contains it
last_country_line = -1
for i in range(len(lines) - 1, -1, -1):
    if 'proxy_pass' in lines[i]:
        last_country_line = i
        break

# Find the "}" that closes the location / block (after the last country route)
# Walk forward from last_country_line to find the closing brace of location /
insert_pos = -1
for i in range(last_country_line, len(lines)):
    if lines[i].strip() == '}':
        # Check if this is the closing of location / 
        # Look backwards for "location /"
        for j in range(i, max(0, i - 200), -1):
            if 'location /' in lines[j] and lines[j].strip().startswith('location /'):
                insert_pos = i
                break
        if insert_pos > 0:
            break

if insert_pos > 0:
    # Build Italy routes to insert
    italy_block = """\n    # Italy
    location = /wc/v1/italy/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8117/api/v1/italy/bot;
    }
    location = /wc/v1/italy/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8117/api/v1/italy/bot/ai;
    }
    location = /wc/v1/italy/health {
        proxy_pass http://127.0.0.1:8117/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""
    lines.insert(insert_pos, italy_block)
    content = '\n'.join(lines)
    print(f"Inserted Italy routes at position {insert_pos}")

# Write fixed config
with open(OUT, 'w') as f:
    f.write(content)

# Verify by copying to a local test
result = subprocess.run(
    ["ssh", "xrplme-vps", f"python3 -c \"import sys; exec(open('{OUT}').read())\""],
    capture_output=True, text=True, timeout=5
)

print(f"Fixed config written to {OUT}")
print(f"Config size: {len(content)} bytes")

# Verify Italy routes are in the right place
italy_count = content.count("wc/v1/italy/")
print(f"Italy route references: {italy_count}")

# Check position - should be before "return 301"
ret_301_pos = content.find("return 301")
italy_pos = content.find("wc/v1/italy/bot")
if italy_pos < ret_301_pos:
    print("✅ Italy routes are in the HTTPS server block (before port 80 redirect)")
else:
    print("❌ Italy routes are still in the wrong place")
