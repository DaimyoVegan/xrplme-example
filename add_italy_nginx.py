#!/usr/bin/env python3
"""
Step 3: Add Italy routes to api-xrplme-https nginx config.
Insert after the papua-new-guinea routes, before the closing } of the server block.
"""
import os
import hashlib

nginx_file = "/etc/nginx/sites-available/api-xrplme-https"
backup_file = "/home/xrpladmin/xrplme-state/backups/api-xrplme-https.20260922_073619.bak"

# Read the current config
with open(nginx_file) as f:
    content = f.read()

# First, check if Italy is already present
if "api/v1/italy/bot" in content:
    print("Italy routes already present in api-xrplme-https — skipping")
else:
    print("Italy routes NOT found — adding them")
    
    # Find the insertion point: after the last country's health route, before the closing }
    # Let's find what comes after the last country routes
    # We need to find the last location block before the closing }
    
    # Strategy: find the closing } of the server block
    # The server block ends with a final }
    # We want to insert before it
    
    # Find all location blocks and their positions
    lines = content.split('\n')
    
    # Find the last country (papua-new-guinea) and its routes
    # Then find the closing } after all country routes
    
    # Find the line with the closing } of the server block
    # It's the last } in the file
    last_brace_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == '}':
            last_brace_idx = i
            break
    
    if last_brace_idx is None:
        print("ERROR: Could not find closing } of server block")
    else:
        print(f"Found closing }} at line {last_brace_idx + 1}")
        print(f"Lines around it:")
        for i in range(max(0, last_brace_idx - 5), last_brace_idx + 1):
            print(f"  L{i+1}: {lines[i]}")
        
        # Build the Italy routes
        italy_routes = """    # Italy (port 8117) — standard pattern matching Macau etc
    location = /api/v1/italy/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:8117;
    }

    location = /api/v1/italy/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:8117;
    }

    location = /api/v1/italy/health {
        proxy_pass http://127.0.0.1:8117/health;
        include /etc/nginx/x402-api-std.conf;
    }
"""
        
        # Insert before the closing }
        lines.insert(last_brace_idx, italy_routes.rstrip("\n"))
        
        # Write the new content
        new_content = '\n'.join(lines)
        
        # Verify the change is correct
        if "api/v1/italy/bot" in new_content:
            print("\nItaly routes added successfully")
            
            # Write to file
            with open(nginx_file, 'w') as f:
                f.write(new_content)
            
            print(f"File written: {nginx_file}")
            print(f"Old size: {os.path.getsize(backup_file)} bytes")
            print(f"New size: {os.path.getsize(nginx_file)} bytes")
            
            # Compute new SHA-256
            with open(nginx_file, 'rb') as f:
                new_hash = hashlib.sha256(f.read()).hexdigest()
            print(f"New SHA-256: {new_hash}")
            
            with open(backup_file, 'rb') as f:
                old_hash = hashlib.sha256(f.read()).hexdigest()
            print(f"Old SHA-256: {old_hash}")
            print(f"Changed: {new_hash != old_hash}")
            
            # Show diff
            import subprocess
            result = subprocess.run(
                ["diff", backup_file, nginx_file],
                capture_output=True, text=True
            )
            print(f"\nDiff (backup → new):")
            print(result.stdout)
        else:
            print("ERROR: Italy routes not found in modified content")
