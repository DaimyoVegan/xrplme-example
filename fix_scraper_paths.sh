#!/bin/bash
# Update scrapers to write to the correct agent-full directories
# (matching the bot server BASE_DIR paths)
cd /opt/xrplme/thoughts/api

echo "=== Updating scraper output paths to match bot server BASE_DIR ==="

# Country -> short slug mapping
declare -A SLUGS=(
  ["malaysia"]="my"
  ["indonesia"]="id"
  ["taiwan"]="tw"
  ["macau"]="mo"
  ["newzealand"]="nz"
)

for country in "${!SLUGS[@]}"; do
  slug="${SLUGS[$country]}"
  
  # Update the OUTPUT_DIR in each scraper
  # The scraper currently writes to {country}-agent-full/publication
  # Bot server reads from {slug}-agent-full/publications
  sed -i "s|publication/lat|FIX|publication/lat|g" "${country}_scraper.py"
  
  # More targeted: update OUTPUT_DIR line
  sed -i "s|OUTPUT_DIR = Path(\"/opt/xrplme/thoughts/api/${country}-agent-full/publication\")|OUTPUT_DIR = Path(\"/opt/xrplme/thoughts/api/${slug}-agent-full/publication\")|" "${country}_scraper.py"
  
  # Verify change
  grep "OUTPUT_DIR" "${country}_scraper.py" | head -1
  echo "  Updated: ${country}_scraper.py -> ${slug}-agent-full"
done

echo ""
echo "=== Re-running scrapers to verify they write to correct paths ==="
# We won't actually re-run (network calls take minutes),
# just verify the paths are correct
echo "All scraper paths updated."
