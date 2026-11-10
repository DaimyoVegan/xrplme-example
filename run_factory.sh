#!/bin/bash
# Generate all 5 new APAC countries using country_factory.py
set -e
cd /opt/xrplme/thoughts/api

COUNTRIES=(
  "brunei|brunei_sources.json"
  "laos|laos_sources.json"
  "myanmar|myanmar_sources.json"
  "timor-leste|timor-leste_sources.json"
  "papua-new-guinea|papua-new-guinea_sources.json"
)

for entry in "${COUNTRIES[@]}"; do
  IFS="|" read -r country sources <<< "$entry"
  echo ""
  echo "========================================"
  echo "Generating: $country (sources: $sources)"
  echo "========================================"
  python3 country_factory.py generate \
    --country "$country" \
    --sources "/tmp/${sources}" \
    --record-target 20 \
    2>&1 || echo "FAILED for $country"
done

echo ""
echo "========================================"
echo "Generation complete. Checking results:"
echo "========================================"
for entry in "${COUNTRIES[@]}"; do
  IFS="|" read -r country sources <<< "$entry"
  dir="/opt/xrplme/thoughts/api/${country}-agent-full"
  if [ -d "$dir" ]; then
    echo "  $country: CREATED"
    ls "$dir"/*.py 2>/dev/null | while read f; do echo "    $(basename $f)"; done
  else
    echo "  $country: NOT CREATED"
  fi
done
