#!/usr/bin/env python3
"""
V3 AUDIT — Response Schema Comparison
READ-ONLY: no payments, no modifications.
Samples: Thailand (original), Italy (canary), USA (original), 
Singapore (APAC), Taiwan (in-memory store).
"""
import subprocess
import json
import time

SAMPLES = [
    ("Thailand", "thailand", "8085"),
    ("Italy", "italy", "8117"),
    ("USA", "usa", "8091"),
    ("Singapore", "singapore", "8096"),
    ("Taiwan", "taiwan", "8108"),
]

print("=" * 80)
print("2. CANONICAL RESPONSE SCHEMA AUDIT")
print("=" * 80)

print("\n--- A. Health Response Schema ---")
for name, slug, port in SAMPLES:
    r = subprocess.run(["curl", "-s", f"http://127.0.0.1:{port}/health"],
                      capture_output=True, text=True, timeout=5)
    try:
        d = json.loads(r.stdout)
        keys = sorted(d.keys())
        print(f"\n  {name} (port {port}):")
        print(f"    Fields: {keys}")
        print(f"    Content-Type: {r.stdout[:0]}")
        # Get content-type via curl -D
        r2 = subprocess.run(["curl", "-s", "-D", "-", f"http://127.0.0.1:{port}/health",
                            "-o", "/dev/null"],
                           capture_output=True, text=True, timeout=5)
        for line in r2.stdout.split('\n'):
            if 'content-type' in line.lower():
                print(f"    {line.strip()}")
        print(f"    Values: {json.dumps(d, indent=6)}")
    except:
        print(f"  {name}: ERROR — {r.stdout[:200]}")
    time.sleep(0.5)

print("\n--- B. Raw Unpaid 402 Response ---")
for name, slug, port in SAMPLES:
    r = subprocess.run(["curl", "-s", "-D", "-", "-X", "POST",
                       f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"message": "audit schema test"})],
                      capture_output=True, text=True, timeout=5)
    
    headers = {}
    body_start = r.stdout.find('\r\n\r\n')
    if body_start == -1:
        body_start = r.stdout.find('\n\n')
    header_text = r.stdout[:body_start] if body_start > 0 else r.stdout
    body_text = r.stdout[body_start+4:] if body_start > 0 else r.stdout
    
    for line in header_text.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            headers[k.strip().lower()] = v.strip()
    
    print(f"\n  {name}:")
    print(f"    Status: {headers.get('HTTP/1.1', headers.get('HTTP/2', '?'))}")
    print(f"    Content-Type: {headers.get('content-type', '?')}")
    print(f"    Headers (x402*): {[k for k in headers if k.startswith('x402') or k.startswith('x-')]}")
    
    try:
        d = json.loads(body_text)
        print(f"    Body fields: {sorted(d.keys())}")
        if 'accepts' in d:
            print(f"    accepts: {d['accepts']}")
        if 'error' in d:
            print(f"    error: {d['error']}")
    except:
        print(f"    Body (raw): {body_text[:200]}")
    time.sleep(0.5)

print("\n--- D. AI Unpaid 402 Response ---")
for name, slug, port in SAMPLES[:3]:  # Just 3 to save time
    r = subprocess.run(["curl", "-s", "-D", "-", "-X", "POST",
                       f"http://127.0.0.1:{port}/api/v1/{slug}/bot/ai",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"message": "audit AI schema test"})],
                      capture_output=True, text=True, timeout=5)
    
    body_start = r.stdout.find('\n\n')
    body_text = r.stdout[body_start+2:] if body_start > 0 else r.stdout
    
    print(f"\n  {name}:")
    try:
        d = json.loads(body_text)
        print(f"    Body fields: {sorted(d.keys())}")
        if 'accepts' in d:
            print(f"    accepts: {d['accepts']}")
        if 'error' in d:
            print(f"    error: {d['error']}")
    except:
        print(f"    Body (raw): {body_text[:200]}")
    time.sleep(0.5)

print("\n--- E. Error Responses (invalid endpoint) ---")
r = subprocess.run(["curl", "-s", "-X", "POST",
                   "http://127.0.0.1:8085/api/v1/thailand/nonexistent",
                   "-H", "Content-Type: application/json",
                   "-d", json.dumps({"message": "test"})],
                  capture_output=True, text=True, timeout=5)
print(f"\n  Nonexistent endpoint:")
print(f"    Status: {r.stdout}")
try:
    d = json.loads(r.stdout)
    print(f"    Body fields: {sorted(d.keys())}")
    print(f"    Body: {json.dumps(d, indent=2)[:500]}")
except:
    print(f"    Raw: {r.stdout[:200]}")

print("\n" + "=" * 80)
print("SCHEMA AUDIT COMPLETE")
print("=" * 80)
