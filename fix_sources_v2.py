#!/usr/bin/env python3
"""Fix source JSON files: extract 'sources' key to be a list"""
import json
import glob
import os

os.chdir(os.path.expanduser("~/xrplme-example"))

files = sorted(glob.glob("*_sources.json"))
for filepath in files:
    with open(filepath, "r") as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "sources" in data:
        sources_list = data["sources"]
        with open(filepath, "w") as f:
            json.dump(sources_list, f, indent=2, ensure_ascii=False)
        print(f"  Fixed: {filepath} ({len(sources_list)} sources)")
    elif isinstance(data, list):
        print(f"  Already correct: {filepath} ({len(data)} sources)")
    else:
        print(f"  UNKNOWN: {filepath}")

print("\nDone.")
