#!/bin/bash
# Upload all 5 scrapers to VPS and create publication directories
set -e

echo "=== Creating publication directories ==="
for country in malaysia indonesia taiwan macau newzealand; do
    ssh xrplme-vps "mkdir -p /opt/xrplme/thoughts/api/${country}-agent-full/publication"
    echo "  Created: /opt/xrplme/thoughts/api/${country}-agent-full/publication"
done

echo ""
echo "=== Uploading scrapers ==="
for country in malaysia indonesia taiwan macau newzealand; do
    scp ~/xrplme-example/${country}_scraper.py xrplme-vps:/opt/xrplme/thoughts/api/${country}_scraper.py
    echo "  Uploaded: ${country}_scraper.py"
done

echo ""
echo "=== Running scrapers ==="
for country in malaysia indonesia taiwan macau newzealand; do
    echo ""
    echo "--- Running ${country}_scraper.py ---"
    ssh xrplme-vps "cd /opt/xrplme/thoughts/api && python3 ${country}_scraper.py" 2>&1
    echo "--- Done: ${country} ---"
done

echo ""
echo "=== Verifying data files ==="
for country in malaysia indonesia taiwan macau newzealand; do
    datafile="/opt/xrplme/thoughts/api/${country}-agent-full/publication/latest_valid.json"
    if [ -f "$datafile" ]; then
        size=$(stat -c%s "$datafile")
        records=$(python3 -c "import json; print(json.load(open('$datafile'))['record_count'])" 2>/dev/null || echo "0")
        echo "  $country: $datafile ($size bytes, $records records)"
    else
        echo "  $country: NO DATA FILE FOUND"
    fi
done
