#!/usr/bin/env python3
"""Read Italy and Thailand bot server source code for diff planning."""
import os

print("=" * 80)
print("ITALY BOT SERVER (current, non-standard)")
print("=" * 80)
with open("/opt/xrplme/thoughts/api/italy_bot_server.py") as f:
    print(f"Size: {os.path.getsize('/opt/xrplme/thoughts/api/italy_bot_server.py')} bytes")
    print(f.read())

print("\n" + "=" * 80)
print("THAILAND BOT SERVER (reference, standard x402 v2)")
print("=" * 80)
with open("/opt/xrplme/thoughts/api/thailand_bot_server.py") as f:
    content = f.read()
    print(f"Size: {os.path.getsize('/opt/xrplme/thoughts/api/thailand_bot_server.py')} bytes")
    # Print just the payment-related parts
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in ["x402", "require_x402", "requirex402options", 
            "payment", "invoice", "proof", "digest", "hmac", "source_tag", "sourceTag",
            "xrp", "drops", "exact", "resource", "extension"]):
            print(f"  L{i+1}: {line}")
