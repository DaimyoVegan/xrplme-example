#!/usr/bin/env python3
"""
Add missing nginx routes for 5 countries: Indonesia, Macau, Malaysia, New Zealand, Taiwan
Also update api-docs.html dropdown.
"""
import os
import subprocess

NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"
API_DOCS = "/var/www/xrplme.online/api-docs.html"

# Countries to add to nginx (slug, port, display_name)
MISSING_COUNTRIES = [
    {"slug": "indonesia", "port": 8107, "display": "Indonesia"},
    {"slug": "macau", "port": 8109, "display": "Macau"},
    {"slug": "malaysia", "port": 8106, "display": "Malaysia"},
    {"slug": "newzealand", "port": 8110, "display": "New Zealand"},
    {"slug": "taiwan", "port": 8108, "display": "Taiwan"},
]

def ssh_run(cmd, timeout=15):
    r = subprocess.run(["ssh", "xrplme-vps", cmd], capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr, r.returncode

def ssh_cat(path):
    out, _, _ = ssh_run(f"cat {path}", timeout=10)
    return out

def ssh_scp(local_path, remote_path):
    result = subprocess.run(["scp", local_path, f"xrplme-vps:{remote_path}"],
                          capture_output=True, text=True, timeout=10)
    return result.returncode == 0

def generate_route_block(slug, port, display):
    """Generate nginx location blocks matching the Thailand pattern."""
    return f"""    # {display}
    location = /wc/v1/{slug}/bot {{
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:{port}/api/v1/{slug}/bot;
    }}

    location = /wc/v1/{slug}/bot/ai {{
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:{port}/api/v1/{slug}/bot/ai;
    }}

    location = /wc/v1/{slug}/health {{
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:{port}/health;
    }}
"""

# 1. Read current nginx config
print("Reading current nginx config...")
config = ssh_cat(NGINX_CONFIG)
if not config:
    print("ERROR: Could not read nginx config")
    exit(1)

# 2. Find insertion point: after the last health block, before try_files
# Look for the pattern: last country health block + try_files
insertion_marker = "        # Try to serve file, then directory, then fall back to 404"
marker_pos = config.find(insertion_marker)

if marker_pos == -1:
    print("ERROR: Could not find insertion marker")
    exit(1)

# Find the closing } of the location / block (which is right before the marker)
# We need to insert before the "try_files" line and its }
# The structure is:
#     }  <- closing of last country location
#         # Try to serve file...
#         try_files $uri $uri/ /index.html;
#     }  <- closing of location /

# Go back to find the } before try_files
block_start = config.rfind("    }", 0, marker_pos)
insert_pos = config.find("\n", block_start) + 1

print(f"Inserting at position {insert_pos} (before 'try_files')")

# 3. Generate route blocks and insert
route_blocks = ""
for country in MISSING_COUNTRIES:
    block = generate_route_block(country["slug"], country["port"], country["display"])
    route_blocks += block

# Insert the new routes
new_config = config[:insert_pos] + route_blocks + config[insert_pos:]

# 4. Write to local file, SCP to VPS
local_path = os.path.expanduser("~/nginx_missing_routes.conf")
with open(local_path, "w") as f:
    f.write(new_config)

print(f"\nGenerated config: {len(new_config)} bytes (was {len(config)})")

# Verify the new countries are in the config
for c in MISSING_COUNTRIES:
    count = new_config.count(f"/wc/v1/{c['slug']}/bot")
    print(f"  {c['display']}: {count} route references")

# 5. Upload to VPS /etc/nginx/sites-available/xrplme-online-https
vps_path = "/etc/nginx/sites-available/xrplme-online-https"
if ssh_scp(local_path, vps_path):
    print(f"\n✅ Uploaded new config to VPS: {vps_path}")
else:
    print(f"\n❌ Failed to upload config")
    exit(1)

# 6. Verify on VPS
print("\n=== Verification ===")
for c in MISSING_COUNTRIES:
    out, _, _ = ssh_run(f"grep -c 'wc/v1/{c['slug']}/bot' {vps_path}", timeout=5)
    print(f"  {c['display']}: {out.strip()} route references on VPS")

# 7. Update api-docs.html
print("\n--- Updating api-docs.html ---")
api_docs = ssh_cat(API_DOCS)
if api_docs:
    for c in MISSING_COUNTRIES:
        option = f'<option value="{c["slug"]}">{c["display"]}</option>'
        if f'value="{c["slug"]}"' not in api_docs:
            # Insert after the last option in the select
            last_option = api_docs.rfind("</option>")
            if last_option > 0:
                insert_pos = api_docs.find("\n", last_option) + 1
                api_docs = api_docs[:insert_pos] + f"        {option}\n" + api_docs[insert_pos:]
            print(f"  {c['display']}: option added")
        else:
            print(f"  {c['display']}: already present")
    
    # Also add hong_kong if missing
    if 'value="hong_kong"' not in api_docs:
        last_option = api_docs.rfind("</option>")
        if last_option > 0:
            insert_pos = api_docs.find("\n", last_option) + 1
            api_docs = api_docs[:insert_pos] + '        <option value="hong_kong">Hong Kong</option>\n' + api_docs[insert_pos:]
        print("  Hong Kong: option added to api-docs.html")
    
    # Write updated api-docs
    docs_path = os.path.expanduser("~/api-docs-updated.html")
    with open(docs_path, "w") as f:
        f.write(api_docs)
    
    if ssh_scp(docs_path, API_DOCS):
        print(f"✅ Uploaded updated api-docs.html")
    else:
        print(f"❌ Failed to upload api-docs.html")
else:
    print("❌ Could not read api-docs.html")

# 8. Cleanup
os.unlink(local_path)

print("\n=== NEXT STEP ===")
print("The user needs to run:")
print("  sudo nginx -t && sudo nginx -s reload")
