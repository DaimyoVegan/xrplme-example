#!/usr/bin/env python3
"""Fix scraper output paths on VPS to match bot server BASE_DIR"""
import os

VPS_PATH = "/opt/xrplme/thoughts/api"
LOCAL_PATH = "/data/data/com/termux/files/home/xrplme-example"

countries = [
    ("malaysia", "my"),
    ("indonesia", "id"),
    ("taiwan", "tw"),
    ("macau", "mo"),
    ("newzealand", "nz"),
]

old_line = 'OUTPUT_DIR = Path(f"/opt/xrplme/thoughts/api/{COUNTRY_NAME}-agent-full/publication")'

paths_to_check = [
    # VPS paths
    ("/opt/xrplme/thoughts/api", "VPS"),
    # Local tablet paths
    (os.path.expanduser("~/xrplme-example"), "LOCAL"),
]

for base_dir, label in paths_to_check:
    for country, slug in countries:
        filepath = os.path.join(base_dir, f"{country}_scraper.py")
        if not os.path.exists(filepath):
            continue
        
        with open(filepath, "r") as f:
            content = f.read()
        
        new_line = f'OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/{slug}-agent-full/publication")'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            with open(filepath, "w") as f:
                f.write(content)
            print(f"  [{label}] {country}_scraper.py: Fixed OUTPUT_DIR -> {slug}-agent-full")
        else:
            # Search for any OUTPUT_DIR line
            found = False
            for line in content.split('\n'):
                if 'OUTPUT_DIR' in line and 'Path' in line:
                    print(f"  [{label}] {country}_scraper.py: Found line: {line.strip()}")
                    found = True
                    break
            if not found:
                print(f"  [{label}] {country}_scraper.py: OUTPUT_DIR not found")

print("\nLocal fixes done. Now fixing VPS...")
