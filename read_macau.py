#!/usr/bin/env python3
"""
Read the full Macau bot server as a template for the Italy fix.
Also read the full Italy bot server.
"""
import os

print("=" * 80)
print("MACAU BOT SERVER (full — reference template)")
print("=" * 80)
with open("/opt/xrplme/thoughts/api/macau_bot_server.py") as f:
    content = f.read()
    print(f"Size: {os.path.getsize('/opt/xrplme/thoughts/api/macau_bot_server.py')} bytes")
    print(f"Total lines: {len(content.splitlines())}")
    print("---FULL CONTENT---")
    print(content)
    print("---END---")
