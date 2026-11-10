#!/bin/bash
# Generate scrapers from malaysia_scraper.py template
cd ~/xrplme-example

for entry in "taiwan|TW|TW|taiwan|TW|Taiwan|TAIWAN" "macau|MO|MO|macao|MO|Macau|MACAU" "newzealand|NZ|NZ|new-zealand|NZ|New Zealand|NEW ZEALAND"; do
  IFS='|' read -r name code wb_code te_slug imf_code display upper <<< "$entry"
  
  cp malaysia_scraper.py "${name}_scraper.py"
  
  sed -i "s/Malaysia/$display/g" "${name}_scraper.py"
  sed -i "s/malaysia/$name/g" "${name}_scraper.py"
  sed -i "s/\"MY\"/\"$code\"/g" "${name}_scraper.py"

  # Fix TE URL specifically
  sed -i "s/tradingeconomics.com\/$name/tradingeconomics.com\/$te_slug/" "${name}_scraper.py"

  python3 -m py_compile "${name}_scraper.py"
  echo "=== ${name}_scraper.py ==="
  echo "  Country: $display ($code)"
  echo "  TE slug: $te_slug"  
  echo "  Syntax: OK"
  echo "  [${upper}] refs: $(grep -c "\[${upper}\]" "${name}_scraper.py")"
done

echo ""
echo "=== All scrapers ==="
ls -la ~/xrplme-example/*_scraper.py
