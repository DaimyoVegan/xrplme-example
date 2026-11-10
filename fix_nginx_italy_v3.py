#!/usr/bin/env python3
"""Fix nginx config: move Italy routes to HTTPS server block."""
import subprocess
import os

NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"
OUT_PATH = os.path.expanduser("~/nginx_final.conf")

# Read current VPS config
result = subprocess.run(
    ["ssh", "xrplme-vps", f"cat {NGINX_CONFIG}"],
    capture_output=True, text=True, timeout=10
)
content = result.stdout

# Find the misplaced Italy routes block
# It's between "# HTTP -> HTTPS redirect" and "server {"
misplaced_start = content.find("# HTTP -> HTTPS redirect for xrplme.online")
if misplaced_start < 0:
    print("Could not find misplaced section")
    exit(1)

# The Italy routes are between "# HTTP ->" and "server {"
# Extract everything up to "# HTTP ->" (HTTPS server block content)
# Then skip the Italy routes
# Then add Italy routes inside the HTTPS block

# Find "server {" that comes after "# HTTP ->" (the port 80 server)
port80_pos = content.find("server {", misplaced_start)

# Italy routes are between misplaced_start and port80_pos
italy_block = content[misplaced_start:port80_pos]

# Remove the misplaced Italy block from the content
content_without_italy = content[:misplaced_start] + content[port80_pos:]

# Now insert Italy routes inside the HTTPS server block
# Find the last country route (papua-new-guinea health) in the content
# and insert after its closing brace
pg_health = "proxy_pass http://127.0.0.1:8117/health;"
# Wait - find the papua-new-guinea health block specifically
pg_block_end = content_without_italy.find("proxy_set_header X-Forwarded-Proto $scheme;\n    }\n\n    # Italy")
# If Italy not found (we removed it), look for PPG health block ending
# Find the PPG health location end
ppg_pos = content_without_italy.find("wc/v1/papua-new-guinea/health")
if ppg_pos < 0:
    # Try without hyphen
    ppg_pos = content_without_italy.find("wc/v1/papua")
    
if ppg_pos >= 0:
    # Find the closing } of the papua-new-guinea health location
    # Look for } followed by \n    \n    # (next country)
    search_from = ppg_pos
    depth = 0
    insert_after = -1
    for i in range(ppg_pos, min(ppg_pos + 200, len(content_without_italy))):
        if content_without_italy[i] == '{':
            depth += 1
        elif content_without_italy[i] == '}':
            depth -= 1
            if depth == 0:
                insert_after = i + 1
                break
    
    if insert_after > 0:
        # Insert Italy routes after the PPG health block closing brace
        italy_routes = """
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
        final_content = content_without_italy[:insert_after] + italy_routes + content_without_italy[insert_after:]
        
        # Write to local file
        with open(OUT_PATH, "w") as f:
            f.write(final_content)
        
        print(f"Config size: {len(final_content)} bytes")
        
        # Verify positions
        ret_301_pos = final_content.find("return 301")
        italy_pos = final_content.find("wc/v1/italy/bot")
        print(f"Italy route position: {italy_pos}")
        print(f"return 301 position: {ret_301_pos}")
        if italy_pos > 0 and italy_pos < ret_301_pos:
            print("✅ Italy routes in HTTPS block (before port 80 redirect)")
        else:
            print("❌ Still in wrong place")
        
        # Count routes
        print(f"Italy routes: {final_content.count('wc/v1/italy/')}")
        print(f"Brunei routes: {final_content.count('wc/v1/brunei/')}")
        print(f"Thailand routes: {final_content.count('wc/v1/thailand/')}")
        
        # Upload to VPS
        subprocess.run(["scp", OUT_PATH, "xrplme-vps:/tmp/nginx_final.conf"],
                      capture_output=True, text=True, timeout=10)
        print("Uploaded to VPS: /tmp/nginx_final.conf")
        print("Apply: sudo cp /tmp/nginx_final.conf /etc/nginx/sites-available/xrplme-online-https && sudo nginx -t && sudo nginx -s reload")
else:
    print("ERROR: Could not find papua-new-guinea block")
