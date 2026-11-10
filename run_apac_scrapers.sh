#!/bin/bash
# Run scrapers for all 5 new APAC countries
cd /opt/xrplme/thoughts/api

COUNTRIES=(
    "brunei|brunei_scraper.py"
    "laos|laos_scraper.py"
    "myanmar|myanmar_scraper.py"
    "timor-leste|timor_leste_scraper.py"
    "papua-new-guinea|papua_new_guinea_scraper.py"
)

for entry in "${COUNTRIES[@]}"; do
    IFS="|" read -r name scraper <<< "$entry"
    echo ""
    echo "=== Running scraper: $name ==="
    python3 "${scraper}" 2>&1 || echo "FAILED: $scraper"
done

echo ""
echo "=== Verify data files ==="
for entry in "${COUNTRIES[@]}"; do
    IFS="|" read -r name scraper <<< "$entry"
    mod=$(echo "$name" | tr '-' '_')
    datafile="/opt/xrplme/thoughts/api/${mod}-agent-full/publication/latest_valid.json"
    if [ -f "$datafile" ]; then
        records=$(python3 -c "import json; print(json.load(open('$datafile')).get('record_count',0))" 2>/dev/null || echo "0")
        size=$(stat -c%s "$datafile")
        echo "  $name: $size bytes, $records records"
    else
        echo "  $name: NO DATA FILE"
    fi
done
