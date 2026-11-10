#!/bin/bash
# Generate 4 scrapers from malaysia_scraper.py template
set -e
cd ~/xrplme-example

COUNTRIES=(
  "indonesia|ID|ID|indonesia|ID|Indonesia|INDONESIA"
  "taiwan|TW|TW|taiwan|TW|Taiwan|TAIWAN"
  "macau|MO|MO|macao|MO|Macau|MACAU"
  "newzealand|NZ|NZ|new-zealand|NZ|New Zealand|NEW ZEALAND"
)

for entry in "${COUNTRIES[@]}"; do
  IFS='|' read -r name code wb_code te_slug imf_code display upper <<< "$entry"
  
  cp malaysia_scraper.py "${name}_scraper.py"
  
  # Simple text replacements
  sed -i "s/Malaysia/$display/g" "${name}_scraper.py"
  sed -i "s/malaysia/$name/g" "${name}_scraper.py"
  sed -i "s/\"MY\"/\"$code\"/g" "${name}_scraper.py"
  sed -i "s/tradingeconomics.com\/$name\//tradingeconomics.com\/$te_slug\//" "${name}_scraper.py"
  sed -i "s/NEWZEALAND/NEW ZEALAND/g" "${name}_scraper.py"
  
  # Check syntax
  python3 -m py_compile "${name}_scraper.py"
  
  echo "=== ${name}_scraper.py ==="
  echo "  Country: $display ($code)"
  echo "  WB: $wb_code, TE: $te_slug, IMF: $imf_code"
  echo "  Syntax: OK"
  grep -c "\[${upper}\]" "${name}_scraper.py}"
  echo "  [${upper}] refs: $(grep -c "\[${upper}\]" "${name}_scraper.py")"
  echo "  Pay_to check: $(grep -c 'payTo\|pay_to' "${name}_scraper.py}")"
done

echo ""
echo "=== All scrapers created ==="
ls -la ~/xrplme-example/*_scraper.py
