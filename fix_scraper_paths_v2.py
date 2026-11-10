#!/usr/bin/env python3
"""Fix scraper output paths to match bot server BASE_DIR (short slug dirs)"""
import os

VPS_HOME = "/opt/xrplme/thoughts/api"
LOCAL_HOME = "/data/data/com/termux/files/home/xrplme-example"

countries = [
    ("malaysia", "my"),
    ("indonesia", "id"),
    ("taiwan", "tw"),
    ("macau", "mo"),
    ("newzealand", "nz"),
]

old_line = 'OUTPUT_DIR = Path(f"/opt/xrplme/thoughts/api/{COUNTRY_NAME}-agent-full/publication")'

for country, slug in countries:
    new_line = f'OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/{slug}-agent-full/publication")'
    
    for base_dir in [VPS_HOME, LOCAL_HOME]:
        filepath = os.path.join(base_dir, f"{country}_scraper.py")
        if not os.path.exists(filepath):
            print(f"  SKIP {filepath} - not found")
            continue
        
        with open(filepath, "r") as f:
            content = f.read()
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            print(f"  {filepath}: Fixed OUTPUT_DIR -> {slug}-agent-full")
        else:
            # Try to find the line
            for line in content.split('\n'):
                if 'OUTPUT_DIR' in line and 'Path' in line:
                    print(f"  {filepath}: Found: {line.strip()}")
                    break
            else:
                print(f"  {filepath}: OUTPUT_DIR not found")
        
        with open(filepath, "w") as f:
            f.write(content)

print("\nDone.")
