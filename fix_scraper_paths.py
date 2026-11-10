#!/usr/bin/env python3
"""Fix scraper output paths to match bot server BASE_DIR (short slug dirs)"""
import os

os.chdir("/opt/xrplme/thoughts/api")

countries = [
    ("malaysia", "my"),
    ("indonesia", "id"),
    ("taiwan", "tw"),
    ("macau", "mo"),
    ("newzealand", "nz"),
]

for country, slug in countries:
    filepath = f"{country}_scraper.py"
    with open(filepath, "r") as f:
        content = f.read()
    
    # Add AGENT_DIR variable after COUNTRY_NAME line
    # Change OUTPUT_DIR to use AGENT_DIR instead of COUNTRY_NAME
    old_line = 'OUTPUT_DIR = Path(f"/opt/xrplme/thoughts/api/{COUNTRY_NAME}-agent-full/publication")'
    new_line = f'OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/{slug}-agent-full/publication")'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print(f"  {country}: Fixed OUTPUT_DIR -> {slug}-agent-full")
    else:
        print(f"  {country}: WARNING - OUTPUT_DIR pattern not found!")
        # Show what it looks like
        for line in content.split('\n'):
            if 'OUTPUT_DIR' in line:
                print(f"    Found: {line.strip()}")
    
    with open(filepath, "w") as f:
        f.write(content)

# Also update local copies
os.chdir(os.path.expanduser("~/xrplme-example"))
for country, slug in countries:
    filepath = f"{country}_scraper.py"
    with open(filepath, "r") as f:
        content = f.read()
    
    old_line = 'OUTPUT_DIR = Path(f"/opt/xrplme/thoughts/api/{COUNTRY_NAME}-agent-full/publication")'
    new_line = f'OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/{slug}-agent-full/publication")'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print(f"  local {country}: Fixed OUTPUT_DIR -> {slug}-agent-full")
    
    with open(filepath, "w") as f:
        f.write(content)

print("\nAll scraper paths fixed.")
