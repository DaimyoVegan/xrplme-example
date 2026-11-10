#!/usr/bin/env python3
"""Verify log format and check if country is recoverable from logs."""
import subprocess

# Show full log line format
result = subprocess.run(["head", "-1", "/home/xrpladmin/logs/country-bots/requests.log"], capture_output=True, text=True)
line = result.stdout.strip()
parts = line.split('|')
print(f"Log line: {line[:200]}")
print(f"\nFields ({len(parts)}):")
for i, p in enumerate(parts):
    print(f"  [{i}]: {p[:60]}")

# Show Italy-specific logs
print(f"\n--- Italy log entries ---")
result = subprocess.run(["grep", "italy", "/home/xrpladmin/logs/country-bots/requests.log"], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')
print(f"Count: {len(lines)}")
if lines:
    for line in lines[:3]:
        print(f"  {line[:150]}")

# Check if COUNTRY_NAME variable is used in logging
print(f"\n--- Log line construction in italy_bot_server.py ---")
result = subprocess.run(["grep", "-n", "_log_line\|_country\|_endpoint\|_country_name\|COUNTRY", "/opt/xrplme/thoughts/api/italy_bot_server.py"], capture_output=True, text=True)
for line in result.stdout.strip().split('\n'):
    if line:
        print(f"  {line}")

# Check what _country is set to
print(f"\n--- Country in log context ---")
result = subprocess.run(["sed -n '180,190p'", "/opt/xrplme/thoughts/api/italy_bot_server.py"], capture_output=True, text=True)
print(result.stdout)
