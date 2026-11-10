#!/usr/bin/env python3
"""Fix nginx config: move Italy routes to HTTPS server block."""
import subprocess
import os

NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"

# Read current config
result = subprocess.run(
    ["ssh", "xrplme-vps", f"cat {NGINX_CONFIG}"],
    capture_output=True, text=True, timeout=10
)
content = result.stdout

# Find and remove misplaced Italy routes
misplaced_start = content.find("# HTTP -> HTTPS redirect for xrplme.online")
port80_pos = content.find("server {", misplaced_start) if misplaced_start >= 0 else -1

if misplaced_start >= 0 and port80_pos >= 0:
    content = content[:misplaced_start] + content[port80_pos:]
    print("Removed misplaced Italy routes")

# Find the PPG health location block end
ppg_pos = content.find("wc/v1/papua-new-guinea/health")
if ppg_pos >= 0:
    # Find the closing } of this location block
    # Search from ppg_pos for the closing brace
    depth = 0
    insert_after = -1
    for i in range(ppg_pos, min(ppg_pos + 300, len(content))):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                insert_after = i + 1
                break
    
    if insert_after > 0:
        # Build Italy routes
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
        final_content = content[:insert_after] + italy_routes + content[insert_after:]
        
        # Write to local file
        out_path = os.path.expanduser("~/nginx_final.conf")
        with open(out_path, "w") as f:
            f.write(final_content)
        
        print(f"Config size: {len(final_content)} bytes")
        
        # Verify positions
        ret_301_pos = final_content.find("return 301")
        italy_pos = final_content.find("wc/v1/italy/bot")
        print(f"Italy route position: {italy_pos}")
        print(f"return 301 position: {ret_301_pos}")
        if italy_pos > 0 and italy_pos < ret_301_pos:
            print("OK: Italy routes in HTTPS block (before port 80 redirect)")
        else:
            print("FAIL: Still in wrong place")
        
        # Count routes
        print(f"Italy routes: {final_content.count('wc/v1/italy/')}")
        print(f"Brunei routes: {final_content.count('wc/v1/brunei/')}")
        print(f"Thailand routes: {final_content.count('wc/v1/thailand/')}")
        
        # Upload to VPS
        subprocess.run(["scp", out_path, "xrplme-vps:/tmp/nginx_final.conf"],
                      capture_output=True, text=True, timeout=10)
        print("Uploaded to VPS: /tmp/nginx_final.conf")
        print("Apply: sudo cp /tmp/nginx_final.conf /etc/nginx/sites-available/xrplme-online-https && sudo nginx -t && sudo nginx -s reload")
    else:
        print("ERROR: Could not find PPG block closing brace")
else:
    print("ERROR: Could not find misplaced Italy routes")
