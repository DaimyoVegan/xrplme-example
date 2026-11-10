#!/bin/bash
# Step 4: PREPARE api-docs.html for user deployment
# File is www-data owned, xrpladmin cannot write without sudo password

echo "=== api-docs.html Italy update prepared ==="
echo ""
echo "Prepared file: /tmp/api-docs-italy.html"
echo "Target: /var/www/xrplme.online/api-docs.html"
echo ""
echo "The target file is owned by www-data:www-data (644) — xrpladmin cannot write to it."
echo "Sudo requires password — not available in this session."
echo ""
echo "To deploy, run this command as root or with sudo:"
echo "  sudo cp /tmp/api-docs-italy.html /var/www/xrplme.online/api-docs.html"
echo ""
echo "=== Current state (unchanged) ==="
ls -la /var/www/xrplme.online/api-docs.html
echo "SHA-256: $(sha256sum /var/www/xrplme.online/api-docs.html | cut -d' ' -f1)"
echo ""
echo "=== Prepared file details ==="
ls -la /tmp/api-docs-italy.html
echo "SHA-256: $(sha256sum /tmp/api-docs-italy.html | cut -d' ' -f1)"
echo ""
echo "=== Diff summary (backup vs prepared) ==="
diff /home/xrpladmin/xrplme-state/backups/api-docs.html.20260922_073619.bak /tmp/api-docs-italy.html
echo ""
echo "=== Italy in prepared file ==="
grep 'option.*value="italy"' /tmp/api-docs-italy.html
grep "Country codes:" /tmp/api-docs-italy.html | grep -o "hong_kong, italy"
