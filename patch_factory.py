#!/usr/bin/env python3
"""Patch country_factory.py on VPS:
1. Fix X402_COLLECTOR to Ded's address
2. Update EXISTING_PORTS to include all currently running countries
"""
import os

os.chdir("/opt/xrplme/thoughts/api")

with open("country_factory.py", "r") as f:
    content = f.read()

# Fix 1: Update X402_COLLECTOR to Ded's address
old_collector = 'X402_COLLECTOR = "rEWgGQmxAH..."'
new_collector = "X402_COLLECTOR = \"razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8\""

# Actually check what the old address is
if 'X402_COLLECTOR = "rEWgGQmx' in content:
    old_line = content.split('\n')
    for i, line in enumerate(old_line):
        if 'X402_COLLECTOR' in line:
            print(f"Found: {line.strip()}")
    
# More robust replacement
import re
content = re.sub(
    r'X402_COLLECTOR = "[^"]+"',
    f'X402_COLLECTOR = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"',
    content
)

# Fix 2: Update EXISTING_PORTS to include all currently running countries
# Current running: thailand(8085), vietnam(8086), japan(8087), korea(8089),
# india(8090), usa(8091), canada(8092), uae(8093), uk(8094), ph(8095), sg(8096),
# au(8097), de(8098), fr(8099), br(8100), mx(8101), ch(8102), nl(8103),
# hong_kong(8104), australia(8097), india(8105), malaysia(8106), indonesia(8107),
# taiwan(8108), macau(8109), newzealand(8110)
old_ports = '{EXISTING_PORTS = {\"thailand\": 8085, \"vietnam\": 8086, \"japan\": 8087, \"korea\": 8089, \"india\": 8090, \"usa\": 8091, \"canada\": 8092, \"uae\": 8093, \"uk\": 8094, \"ph\": 8095, \"sg\": 8096, \"au\": 8097, \"de\": 8098, \"fr\": 8099, \"br\": 8100, \"mx\": 8101, \"ch\": 8102, \"nl\": 8103}'
new_ports = 'EXISTING_PORTS = {\"thailand\": 8085, \"vietnam\": 8086, \"japan\": 8087, \"korea\": 8089, \"india\": 8105, \"usa\": 8091, \"canada\": 8092, \"uae\": 8093, \"uk\": 8094, \"ph\": 8095, \"sg\": 8096, \"au\": 8097, \"de\": 8098, \"fr\": 8099, \"br\": 8100, \"mx\": 8101, \"ch\": 8102, \"nl\": 8103, \"hongkong\": 8104, \"malaysia\": 8106, \"indonesia\": 8107, \"taiwan\": 8108, \"macau\": 8109, \"newzealand\": 8110}'

# Find and replace the EXISTING_PORTS line
lines = content.split('\n')
for i, line in enumerate(lines):
    if line.startswith('EXISTING_PORTS = {'):
        print(f"Old ports line: {line.strip()[:100]}...")
        # Build the new line with all 24 countries
        new_line = 'EXISTING_PORTS = {"thailand": 8085, "vietnam": 8086, "japan": 8087, "korea": 8089, "india": 8105, "usa": 8091, "canada": 8092, "uae": 8093, "uk": 8094, "philippines": 8095, "singapore": 8096, "australia": 8097, "germany": 8098, "france": 8099, "brazil": 8100, "mexico": 8101, "switzerland": 8102, "netherlands": 8103, "hongkong": 8104, "malaysia": 8106, "indonesia": 8107, "taiwan": 8108, "macau": 8109, "newzealand": 8110}'
        lines[i] = new_line
        print(f"New ports line: {new_line[:100]}...")
        break

content = '\n'.join(lines)

with open("country_factory.py", "w") as f:
    f.write(content)

print("\ncountry_factory.py patched on VPS")
