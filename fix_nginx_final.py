#!/usr/bin/env python3
"""Fix nginx config for Italy - simpler approach."""
import subprocess
import os

NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"

# Read current config via SSH
result = subprocess.run(
    ["ssh", "xrplme-vps", f"cat {NGINX_CONFIG}"],
    capture_output=True, text=True, timeout=10
)
content = result.stdout

# Check if Italy routes are already removed (not present)
if "wc/v1/italy/" not in content:
    print("Italy routes were already removed (from earlier failed attempt)")
    # Read the current config - it has the syntax error
    # The misplaced routes were removed but left dangling content
    
    # Check if there's a broken section
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if i >= 525 and i <= 540:
            print(f"  Line {i+1}: {line[:80]}")
    
# We need to restore from a clean backup and insert correctly
# Let's just re-apply the APAC + Italy routes from scratch
# Read the APAC config from the earlier temp file
result2 = subprocess.run(
    ["ssh", "xrplme-vps", "cat /tmp/nginx_apac_wc_routes.conf"],
    capture_output=True, text=True, timeout=10
)
apac_content = result2.stdout

# Check if APAC routes config has all 20 countries' routes
# We need to add Italy routes to THIS content
italy_block = """
    # Italy
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

# The APAC config already has all existing countries + APAC countries
# Just add Italy routes in the same pattern
# Find the PPG (papua-new-guinea) block and add after it
if "wc/v1/italy/" not in apac_content:
    # Find the last country route block (PPG) in the config
    pg_health = "wc/v1/papua-new-guinea/health"
    if pg_health in apac_content:
        # Find the closing } after papua-new-guinea/health location
        pg_idx = apac_content.find(pg_health)
        # Find the next } after this
        close_idx = apac_content.find('\n    }', pg_idx)
        if close_idx > 0:
            # Insert Italy routes after the papua-new-guinea health block
            apac_content = apac_content[:close_idx + 8] + italy_block + apac_content[close_idx + 8:]
            print("Inserted Italy routes after papua-new-guinea")
    
    # Write to local file
    out_path = os.path.expanduser("~/nginx_final.conf")
    with open(out_path, "w") as f:
        f.write(apac_content)
    
    print(f"Config size: {len(apac_content)} bytes")
    print(f"Written to: {out_path}")
    
    # Verify
    italy_count = apac_content.count("wc/v1/italy/")
    brunei_count = apac_content.count("wc/v1/brunei/")
    thailand_count = apac_content.count("wc/v1/thailand/")
    print(f"Italy route references: {italy_count}")
    print(f"Brunei route references: {brunei_count}")
    print(f"Thailand route references: {thailand_count}")
    
    # Verify position (before return 301)
    ret_301_pos = apac_content.find("return 301")
    italy_pos = apac_content.find("wc/v1/italy/bot")
    if italy_pos > 0 and italy_pos < ret_301_pos:
        print("✅ Italy routes are in the HTTPS server block (before port 80 redirect)")
    else:
        print(f"❌ Italy routes are NOT in the right place (italy_pos={italy_pos}, ret_301_pos={ret_301_pos})")
else:
    print("Italy routes already present in APAC config")
