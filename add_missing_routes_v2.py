#!/usr/bin/env python3
"""
Add missing nginx routes for 5 countries and update api-docs.html.
Writes files to /tmp/ on VPS for user to apply with sudo.
"""
import os
import subprocess

VPS_NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"
VPS_API_DOCS = "/var/www/xrplme.online/api-docs.html"
VPS_TEMP_DIR = "/tmp"

# Countries to add to nginx (slug, port, display_name)
MISSING_COUNTRIES = [
    {"slug": "indonesia", "port": 8107, "display": "Indonesia"},
    {"slug": "macau", "port": 8109, "display": "Macau"},
    {"slug": "malaysia", "port": 8106, "display": "Malaysia"},
    {"slug": "newzealand", "port": 8110, "display": "New Zealand"},
    {"slug": "taiwan", "port": 8108, "display": "Taiwan"},
]

def ssh_run(cmd, timeout=30):
    r = subprocess.run(["ssh", "xrplme-vps", cmd], capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr, r.returncode

def ssh_cat(path):
    out, _, _ = ssh_run(f"cat {path}", timeout=10)
    return out

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

# 1. Read current nginx config from VPS
print("Reading nginx config from VPS...")
config = ssh_cat(VPS_NGINX_CONFIG)
if not config:
    print("ERROR: Could not read nginx config")
    exit(1)
print(f"  Current config: {len(config)} bytes")

# 2. Find insertion point: before "try_files" in the location / block
insertion_marker = "        # Try to serve file, then directory, then fall back to 404"
marker_pos = config.find(insertion_marker)
if marker_pos == -1:
    print("ERROR: Could not find insertion marker")
    exit(1)

# Go back to find the } before try_files
block_end = config.rfind("    }", 0, marker_pos)
insert_pos = config.find("\n", block_end) + 1
print(f"  Inserting at position {insert_pos}")

# 3. Generate route blocks and insert
route_blocks = ""
for country in MISSING_COUNTRIES:
    block = generate_route_block(country["slug"], country["port"], country["display"])
    route_blocks += block
    count = config.count(f"/wc/v1/{country['slug']}/bot")
    print(f"  {country['display']}: {count} existing routes (adding 2)")

new_config = config[:insert_pos] + route_blocks + config[insert_pos:]
print(f"  New config: {len(new_config)} bytes (+{len(new_config) - len(config)})")

# 4. Write to /tmp/ on VPS
nginx_tmp = f"{VPS_TEMP_DIR}/nginx_routes_missing.conf"
# Write locally, then scp
local_path = os.path.expanduser("~/nginx_routes_missing.conf")
with open(local_path, "w") as f:
    f.write(new_config)

out, err, rc = ssh_run(f"cat > {nginx_tmp}", timeout=10)
# Use scp instead
result = subprocess.run(["scp", local_path, f"xrplme-vps:{nginx_tmp}"],
                        capture_output=True, text=True, timeout=10)
os.unlink(local_path)

if result.returncode == 0:
    print(f"\n✅ nginx config saved to {nginx_tmp}")
else:
    print(f"\n❌ Failed to write nginx config: {result.stderr}")

# 5. Update api-docs.html
print("\n--- Updating api-docs.html ---")
api_docs = ssh_cat(VPS_API_DOCS)
if not api_docs:
    print("ERROR: Could not read api-docs.html")
else:
    print(f"  Current api-docs.html: {len(api_docs)} bytes")
    
    added = 0
    for c in MISSING_COUNTRIES:
        option = f'<option value="{c["slug"]}">{c["display"]}</option>'
        if f'value="{c["slug"]}"' not in api_docs:
            last_option = api_docs.rfind("</option>")
            if last_option > 0:
                insert_pos = api_docs.find("\n", last_option) + 1
                api_docs = api_docs[:insert_pos] + f"        {option}\n" + api_docs[insert_pos:]
            print(f"  {c['display']}: option added")
            added += 1
        else:
            print(f"  {c['display']}: already present")
    
    # Also add hong_kong if missing
    if 'value="hong_kong"' not in api_docs:
        last_option = api_docs.rfind("</option>")
        if last_option > 0:
            insert_pos = api_docs.find("\n", last_option) + 1
            api_docs = api_docs[:insert_pos] + '        <option value="hong_kong">Hong Kong</option>\n' + api_docs[insert_pos:]
        print("  Hong Kong: option added")
        added += 1
    
    if added > 0:
        docs_tmp = f"{VPS_TEMP_DIR}/api-docs-updated.html"
        local_docs = os.path.expanduser("~/api-docs-updated.html")
        with open(local_docs, "w") as f:
            f.write(api_docs)
        
        result = subprocess.run(["scp", local_docs, f"xrplme-vps:{docs_tmp}"],
                                capture_output=True, text=True, timeout=10)
        os.unlink(local_docs)
        
        if result.returncode == 0:
            print(f"\n✅ Updated api-docs.html saved to {docs_tmp}")
        else:
            print(f"\n❌ Failed: {result.stderr}")
    else:
        print("\n  No changes needed to api-docs.html")

print("\n=== NEXT STEP ===")
print("Run on VPS:")
print(f"  sudo cp {nginx_tmp} {VPS_NGINX_CONFIG}")
print(f"  sudo cp {VPS_TEMP_DIR}/api-docs-updated.html {VPS_API_DOCS}")
print("  sudo nginx -t && sudo nginx -s reload")
