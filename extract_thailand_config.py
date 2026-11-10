#!/usr/bin/env python3
"""Extract Thailand's key payment config and middleware setup."""
import re

with open("/opt/xrplme/thoughts/api/thailand_bot_server.py") as f:
    content = f.read()
    lines = content.split("\n")

print("=== Thailand X402_CONFIG (lines 58-75) ===")
for i in range(57, 75):
    if i < len(lines):
        print(f"  L{i+1}: {lines[i]}")

print("\n=== Thailand middleware + route setup (lines 850-950) ===")
for i in range(849, 950):
    if i < len(lines):
        print(f"  L{i+1}: {lines[i]}")

print("\n=== Italy full source (for replacement reference) ===")
with open("/opt/xrplme/thoughts/api/italy_bot_server.py") as f:
    print(f.read())
