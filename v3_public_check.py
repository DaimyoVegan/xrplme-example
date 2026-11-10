#!/usr/bin/env python3
"""V3 Audit — Public 402 checks via Python."""
import subprocess
import json

print("=== Public 402 checks (sample) ===")
for country in ["thailand", "italy", "usa", "singapore", "japan", "korea", "india"]:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "-X", "POST", f"https://api.xrplme.online/api/v1/{country}/bot",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"message": "audit"})],
                      capture_output=True, text=True, timeout=5)
    print(f"  /api/v1/{country}/bot → {r.stdout}")

# wc/v1/ routes
print("\n=== wc/v1/ routes ===")
for country in ["italy", "thailand"]:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "-X", "POST", f"https://xrplme.online/wc/v1/{country}/bot",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"message": "audit"})],
                      capture_output=True, text=True, timeout=5)
    print(f"  wc/v1/{country}/bot → {r.stdout}")

# Public AI 402 check
print("\n=== Public AI 402 checks (sample) ===")
for country in ["thailand", "italy", "usa"]:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "-X", "POST", f"https://api.xrplme.online/api/v1/{country}/bot/ai",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"message": "audit"})],
                      capture_output=True, text=True, timeout=5)
    print(f"  /api/v1/{country}/bot/ai → {r.stdout}")
