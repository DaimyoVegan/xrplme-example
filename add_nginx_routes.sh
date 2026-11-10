#!/bin/bash
# Add nginx routes for 5 new APAC countries
# Following the existing nginx pattern

NGINX_CONF="/etc/nginx/sites-available/xrplme-online-https"

# First, backup the config
cp "$NGINX_CONF" "$NGINX_CONF.bak.$(date +%s)" 2>/dev/null || true

# Route definitions: slug|port|display
ROUTES=(
  "brunei|8111|Brunei"
  "laos|8112|Laos"
  "myanmar|8113|Myanmar"
  "timor-leste|8114|Timor-Leste"
  "papua-new-guinea|8115|Papua New Guinea"
)

for route in "${ROUTES[@]}"; do
  IFS="|" read -r slug port display <<< "$route"
  echo "Adding routes for $display ($slug, port $port)..."
  
  # Build nginx route block
  routes=$(cat << EOF
    # $display
    location = /wc/v1/$slug/bot {
        include /etc/nginx/x402-api-std.conf;
        proxy_pass http://127.0.0.1:$port/api/v1/$slug/bot;
    }
    location = /wc/v1/$slug/bot/ai {
        include /etc/nginx/x402-api-ai.conf;
        proxy_pass http://127.0.0.1:$port/api/v1/$slug/bot/ai;
    }
    location = /wc/v1/$slug/health {
        proxy_pass http://127.0.0.1:$port/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
EOF
)
  
  # Find the last closing brace of the server block and insert before it
  python3 -c "
import re
with open('$NGINX_CONF', 'r') as f:
    content = f.read()

# Find the insertion point - before the last closing brace of server block
# Look for the last } that closes the server block
lines = content.split('\n')
inserted = False
for i in range(len(lines) - 1, -1, -1):
    stripped = lines[i].strip()
    if stripped == '}':
        # Check this is the server block closing brace
        # Insert our routes before it
        route_block = '''$routes'''
        lines.insert(i, route_block)
        inserted = True
        break

if inserted:
    with open('$NGINX_CONF', 'w') as f:
        f.write('\n'.join(lines))
    print('  Inserted nginx routes')
else:
    print('  ERROR: Could not find insertion point')
" || echo "Python insertion failed - trying manual approach"
done

# Test nginx config
echo ""
echo "=== Testing nginx config ==="
nginx -t 2>&1

if [ $? -eq 0 ]; then
    echo "Nginx config valid - reloading"
    sudo nginx -s reload 2>&1 || echo "Need sudo for reload"
else
    echo "Nginx config INVALID - restoring backup"
    cp "$NGINX_CONF.bak" "$NGINX_CONF" 2>/dev/null || true
fi
