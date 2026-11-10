#!/usr/bin/env python3
"""Fix country_builder.py syntax errors on VPS."""
import subprocess

FIX_SCRIPT = """
import re

with open("/opt/xrplme/thoughts/api/country_builder.py", "r") as f:
    content = f.read()

# Fix 1: Multi-line print f-strings that Python 3.12 doesn't like
# Pattern: print(f"\n<some text...>")
content = re.sub(
    r'print\\(f\\"\\n(.+?)\\"\\)',
    lambda m: f'print(f"{m.group(1)}")',
    content
)

# Fix 2: Also fix the multi-line pattern where f-string spans lines
content = content.replace(
    'print(f\\"\\nResearching data sources for {country_code}...\\")',
    'print(f"Researching data sources for {country_code}...")'
)

# Also fix similar patterns in other print statements
content = content.replace(
    'print(f\\"\\nGenerating scraper for {country_name}...\\")',
    'print(f"Generating scraper for {country_name}...")'
)
content = content.replace(
    'print(f\\"\\nGenerating bot server for {country_name} on port {port}...\\")',
    'print(f"Generating bot server for {country_name} on port {port}...")'
)
content = content.replace(
    'print(f\\"\\nAdding nginx routes for {country_code}...\\")',
    'print(f"Adding nginx routes for {country_code}...")'
)
content = content.replace(
    'print(f\\"\\nStarting bot server for {country_code} on port {port}...\\")',
    'print(f"Starting bot server for {country_code} on port {port}...")'
)
content = content.replace(
    'print(f\\"\\nTesting endpoints for {country_code}...\\")',
    'print(f"Testing endpoints for {country_code}...")'
)

with open("/opt/xrplme/thoughts/api/country_builder.py", "w") as f:
    f.write(content)

print("Fixed country_builder.py syntax errors")
"""

result = subprocess.run(
    ["ssh", "xrplme-vps", f"python3 << 'SCRIPT'\n{FIX_SCRIPT}\nSCRIPT"],
    capture_output=True, text=True, timeout=10
)
print(f"stderr: {result.stderr.strip()[:300]}")
print(f"stdout: {result.stdout.strip()}")
