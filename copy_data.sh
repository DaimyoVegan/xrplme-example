#!/bin/bash
# Copy data files from {country}-agent-full to {slug}-agent-full
# (Bot servers read from short slug directories)
set -e

echo "=== Copying data files to correct directories ==="

# Map: country_full -> slug
declare -A SLUGS=(
  ["malaysia"]="my"
  ["indonesia"]="id"
  ["taiwan"]="tw"
  ["macau"]="mo"
  ["newzealand"]="nz"
)

for country in "${!SLUGS[@]}"; do
  slug="${SLUGS[$country]}"
  
  src="/opt/xrplme/thoughts/api/${country}-agent-full/publication/latest_valid.json"
  dst="/opt/xrplme/thoughts/api/${slug}-agent-full/publication/latest_valid.json"
  
  echo "--- $country -> $slug ---"
  
  if [ -f "$src" ]; then
    mkdir -p "/opt/xrplme/thoughts/api/${slug}-agent-full/publication"
    cp "$src" "$dst"
    
    # Also copy other files
    cp /opt/xrplme/thoughts/api/${country}-agent-full/publication/latest_valid_candidate.json \
       /opt/xrplme/thoughts/api/${slug}-agent-full/publication/latest_valid_candidate.json 2>/dev/null || true
    cp /opt/xrplme/thoughts/api/${country}-agent-full/publication/scrape_report.json \
       /opt/xrplme/thoughts/api/${slug}-agent-full/publication/scrape_report.json 2>/dev/null || true
    
    echo "  Copied: $src -> $dst"
    echo "  Source records: $(python3 -c "import json; print(json.load(open('$src'))['record_count'])")"
    echo "  Dest records: $(python3 -c "import json; print(json.load(open('$dst'))['record_count'])")"
  else
    echo "  WARNING: Source file not found at $src"
  fi
done

echo ""
echo "=== Verify bot server can read data ==="
for country in malaysia indonesia taiwan macau newzealand; do
  slug="${SLUGS[$country]}"
  dst="/opt/xrplme/thoughts/api/${slug}-agent-full/publication/latest_valid.json"
  if [ -f "$dst" ]; then
    size=$(stat -c%s "$dst")
    records=$(python3 -c "import json; print(json.load(open('$dst'))['record_count'])")
    echo "  $country: $dst ($size bytes, $records records) - OK"
  else
    echo "  $country: MISSING at $dst"
  fi
done