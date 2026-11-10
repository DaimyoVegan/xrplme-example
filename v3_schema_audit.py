#!/usr/bin/env python3
"""
V3 AUDIT — Response Schema Comparison
READ-ONLY: no payments, no modifications.
Compares health, 402, and error responses across 5 sample countries.
"""
import subprocess
import json
import time

print("=" * 80)
print("V3 RESPONSE SCHEMA AUDIT")
print("=" * 80)

# 5 sample countries: Thailand, Italy, original (usa), APAC (sg), in-memory (mo)
SAMPLES = [
    ("thailand", "thailand-bot-api", 8085),
    ("italy", "italy-bot-api", 8117),
    ("usa", "usa-bot-api", 8091),
    ("singapore", "sg-bot-api", 8096),
    ("macau", "mo-bot-api", 8088),
]

results = {}

for country, slug, port in SAMPLES:
    print(f"\n{'=' * 60}")
    print(f"  {country.upper()} (port {port})")
    print(f"{'=' * 60}")
    
    # Health check
    r = subprocess.run(["curl", "-s", "-w", "\n%{http_code}",
                       f"http://127.0.0.1:{port}/health"],
                      capture_output=True, text=True, timeout=5)
    body = r.stdout.rsplit('\n', 1)[0]
    code = r.stdout.rsplit('\n', 1)[1]
    try:
        h = json.loads(body)
        print(f"\n  Health (HTTP {code}):")
        print(f"    Fields: {sorted(h.keys())}")
        print(f"    Pretty: {json.dumps(h, indent=2)[:300]}")
    except:
        print(f"\n  Health (HTTP {code}): raw={body[:100]}")
    
    # Raw unpaid 402
    r = subprocess.run([
        "curl", "-s", "-w", "\n%{http_code}", "-X", "POST",
        f"http://127.0.0.1:{port}/api/v1/{country}/bot",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"message": "schema audit test"})
    ], capture_output=True, text=True, timeout=5)
    body = r.stdout.rsplit('\n', 1)[0]
    code = r.stdout.rsplit('\n', 1)[1]
    try:
        d = json.loads(body)
        a = d.get('accepts', [{}])[0]
        extra = a.get('extra', {})
        print(f"\n  Raw 402 (HTTP {code}):")
        print(f"    Top-level fields: {sorted(d.keys())}")
        print(f"    accepts[0] fields: {sorted(a.keys())}")
        print(f"    extra fields: {sorted(extra.keys())}")
        print(f"    x402Version: {d.get('x402Version')}")
        print(f"    scheme: {a.get('scheme')}")
        print(f"    amount: {a.get('amount')}")
        print(f"    network: {a.get('network')}")
        print(f"    asset: {a.get('asset')}")
        print(f"    payTo: {a.get('payTo')[:20]}...")
        print(f"    sourceTag: {extra.get('sourceTag')}")
        print(f"    invoiceId: {extra.get('invoiceId', 'MISSING')[:16]}...")
        
        # Store for comparison
        results[country] = {
            'health': h if isinstance(h, dict) else {},
            'raw_402': {
                'x402Version': d.get('x402Version'),
                'scheme': a.get('scheme'),
                'amount': a.get('amount'),
                'network': a.get('network'),
                'asset': a.get('asset'),
                'payTo': a.get('payTo'),
                'sourceTag': extra.get('sourceTag'),
                'top_fields': sorted(d.keys()),
                'accepts_fields': sorted(a.keys()),
                'extra_fields': sorted(extra.keys()),
                'resource': 'resource' in d,
                'extensions': 'extensions' in d,
            }
        }
        
        # Check for payment-specific headers
        # Get raw headers
        r2 = subprocess.run([
            "curl", "-s", "-D", "-", "-o", "/dev/null", "-X", "POST",
            f"http://127.0.0.1:{port}/api/v1/{country}/bot",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"message": "header check"})
        ], capture_output=True, text=True, timeout=5)
        headers = {}
        for line in r2.stdout.split('\n'):
            if ':' in line and 'HTTP/' in line:
                parts = line.split(':', 1)
                headers[parts[0].strip()] = parts[1].strip() if len(parts) > 1 else ''
            elif ':' in line and not line.startswith('HTTP'):
                parts = line.split(':', 1)
                headers[parts[0].strip()] = parts[1].strip()
        
        x402_headers = {k: v for k, v in headers.items() if 'x-' in k.lower() or 'payment' in k.lower() or '402' in k.lower()}
        print(f"\n    X-402 headers:")
        for hk, hv in sorted(x402_headers.items()):
            if 'token' not in hk.lower() and 'auth' not in hk.lower():
                print(f"      {hk}: {hv[:60]}")
        
        results[country]['raw_402']['headers'] = list(x402_headers.keys())
        
    except Exception as e:
        print(f"\n  Raw 402 error: {e}")
        print(f"  Body: {body[:200]}")
    
    # AI endpoint (unpaid 402)
    r = subprocess.run([
        "curl", "-s", "-w", "\n%{http_code}", "-X", "POST",
        f"http://127.0.0.1:{port}/api/v1/{country}/bot/ai",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"message": "schema audit AI test"})
    ], capture_output=True, text=True, timeout=5)
    body = r.stdout.rsplit('\n', 1)[0]
    code = r.stdout.rsplit('\n', 1)[1]
    try:
        d = json.loads(body)
        a = d.get('accepts', [{}])[0]
        extra = a.get('extra', {})
        print(f"\n  AI 402 (HTTP {code}):")
        print(f"    x402Version: {d.get('x402Version')}")
        print(f"    amount: {a.get('amount')}")
        print(f"    scheme: {a.get('scheme')}")
        print(f"    sourceTag: {extra.get('sourceTag')}")
        
        results[country]['ai_402'] = {
            'amount': a.get('amount'),
            'x402Version': d.get('x402Version'),
        }
    except Exception as e:
        print(f"\n  AI 402 error: {e}")
        print(f"  Body: {body[:200]}")
        results[country]['ai_402'] = {'error': str(e)}
    
    time.sleep(1)  # Avoid rate limits

# Schema comparison
print(f"\n{'=' * 80}")
print("SCHEMA COMPARISON")
print(f"{'=' * 80}")

# Health schema comparison
print(f"\n--- Health Schema ---")
health_fields = set()
for country in results:
    if 'health' in results[country]:
        fields = set(results[country]['health'].keys())
        print(f"  {country}: {sorted(fields)}")
        health_fields.update(fields)

print(f"\n  Union of all health fields: {sorted(health_fields)}")

# Raw 402 schema comparison
print(f"\n--- Raw 402 Schema ---")
raw_fields = set()
for country in results:
    if 'raw_402' in results[country]:
        fields = set(results[country]['raw_402']['top_fields'])
        print(f"  {country} top: {sorted(fields)}")
        raw_fields.update(fields)

# Check consistency
print(f"\n  x402Version consistency:")
versions = set()
amounts_raw = set()
amounts_ai = set()
schemes = set()
for country in results:
    if 'raw_402' in results[country]:
        versions.add(results[country]['raw_402']['x402Version'])
        amounts_raw.add(results[country]['raw_402']['amount'])
        schemes.add(results[country]['raw_402']['scheme'])
    if 'ai_402' in results[country]:
        amounts_ai.add(results[country]['ai_402']['amount'])

print(f"    x402Version values: {versions}")
print(f"    Raw amounts: {amounts_raw}")
print(f"    AI amounts: {amounts_ai}")
print(f"    Schemes: {schemes}")

print(f"\n  Field consistency:")
raw_field_sets = {}
for country in results:
    if 'raw_402' in results[country]:
        raw_field_sets[country] = set(results[country]['raw_402']['top_fields'])
        
# Check if all countries have the same top-level fields
all_same = all(fs == raw_field_sets[list(raw_field_sets.keys())[0]] for fs in raw_field_sets.values()) if raw_field_sets else False
print(f"    All countries same top-level fields: {'✓' if all_same else '✗'}")
if not all_same:
    print(f"    Differences:")
    ref = raw_field_sets[list(raw_field_sets.keys())[0]]
    for country, fields in raw_field_sets.items():
        if fields != ref:
            print(f"      {country}: only in {country}: {fields - ref}, missing: {ref - fields}")

print(f"\n  Header consistency:")
header_sets = {}
for country in results:
    if 'raw_402' in results[country] and 'headers' in results[country]['raw_402']:
        header_sets[country] = set(results[country]['raw_402']['headers'])
        
all_same_headers = all(hs == header_sets[list(header_sets.keys())[0]] for hs in header_sets.values()) if header_sets else False
print(f"    All countries same X-402 headers: {'✓' if all_same_headers else '✗'}")
if not all_same_headers:
    ref = header_sets[list(header_sets.keys())[0]]
    for country, headers in header_sets.items():
        if headers != ref:
            print(f"      {country}: only: {headers - ref}, missing: {ref - headers}")

print(f"\n{'=' * 80}")
print("SCHEMA AUDIT COMPLETE")
print(f"{'=' * 80}")
