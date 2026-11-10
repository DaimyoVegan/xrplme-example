#!/bin/bash
# Step 5: Validation
echo "=== Step 5: VALIDATION ==="
echo ""
echo "--- 5a. Python syntax check ---"
echo "Checking italy_bot_server.py..."
/home/xrpladmin/thailand_bot_venv/bin/python -m py_compile /opt/xrplme/thoughts/api/italy_bot_server.py 2>&1
echo "Exit code: $?"
echo ""

echo "--- 5b. Nginx config test ---"
nginx -t 2>&1
echo "Exit code: $?"
echo ""

echo "--- 5c. File change verification ---"
echo "1. italy_bot_server.py:"
echo "   Old SHA-256: 09912e6f58eef99128648af0e27feb24dcfb18d121bd74351f40ba869ab5282d"
echo "   New SHA-256: $(sha256sum /opt/xrplme/thoughts/api/italy_bot_server.py | cut -d' ' -f1)"
echo "   Size: $(wc -c < /opt/xrplme/thoughts/api/italy_bot_server.py) bytes"
echo ""
echo "2. api-xrplme-https:"
echo "   Old SHA-256: 0a6cae29da3c5bc42618b95ac7e4578b3fc2c1f83db02a25d39cc53fbc7917c0"
echo "   New SHA-256: $(sha256sum /etc/nginx/sites-available/api-xrplme-https | cut -d' ' -f1)"
echo "   Size: $(wc -c < /etc/nginx/sites-available/api-xrplme-https) bytes"
echo ""
echo "3. api-docs.html:"
echo "   Old SHA-256: 3ea8b766aedde36f16130a017a09649126e14e1cb2c225ae5296fb1376e1a367"
echo "   Current SHA-256: $(sha256sum /var/www/xrplme.online/api-docs.html | cut -d' ' -f1)"
echo "   (NOT deployed — www-data owned, sudo password required)"
echo "   Prepared: /tmp/api-docs-italy.html"
echo "   Prepared SHA-256: $(sha256sum /tmp/api-docs-italy.html | cut -d' ' -f1)"
echo ""

echo "--- 5d. Diff summary ---"
echo "1. italy_bot_server.py (backup → new):"
diff /home/xrpladmin/xrplme-state/backups/italy_bot_server.py.20260922_073619.bak /opt/xrplme/thoughts/api/italy_bot_server.py | head -5
echo "   (Full replacement — 3526 → ~12K bytes)"
echo ""
echo "2. api-xrplme-https (backup → new):"
diff /home/xrpladmin/xrplme-state/backups/api-xrplme-https.20260922_073619.bak /etc/nginx/sites-available/api-xrplme-https
echo ""
echo "3. api-docs.html (backup → prepared):"
diff /home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak /tmp/api-docs-italy.html
