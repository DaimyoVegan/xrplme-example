#!/usr/bin/env python3
"""Read and display country_builder.py for patching"""
import os

os.chdir("/opt/xrplme/thoughts/api")

with open("country_builder.py", "r") as f:
    content = f.read()

# Show the key functions
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'def generate_' in line or 'def research_' in line or 'def add_nginx' in line or 'def start_' in line or 'def test_' in line or 'COUNTRY_METADATA' in line or 'EXISTING' in line or 'X402_' in line or 'NGINX_CONFIG' in line or 'VENV_PATH' in line:
        print(f"{i}: {line}")

print("\n=== Full file lines 30-45 (metadata) ===")
print('\n'.join(f"{i}: {line}" for i, line in enumerate(lines[29:45], 30)))
