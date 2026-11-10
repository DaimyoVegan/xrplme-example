#!/usr/bin/env python3
"""Part 3: Website deep audit + organizer + AI endpoint details."""
import requests
import json
import os
import re

print("=" * 80)
print("WEBSITE DEEP AUDIT")
print("=" * 80)

# Check homepage
print("\n=== Homepage ===")
try:
    r = requests.get("https://xrplme.online/", timeout=10, verify=False)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
    
    # Extract text content
    text = r.text[:5000]
    
    # Check for claims
    claims_patterns = [
        ("real-time stock", "real-time stock", False),
        ("compliance clearance", "compliance", False),
        ("sanctions cleared", "sanctions", False),
        ("safe to proceed", "safe to proceed", False),
        ("transaction approved", "transaction approved", False),
        ("legal advice", "legal advice", False),
        ("financial advice", "financial advice", False),
        ("official partner", "official partner", False),
    ]
    
    lower_text = text.lower()
    for label, pattern, _ in claims_patterns:
        if pattern in lower_text:
            # Find context
            idx = lower_text.index(pattern)
            start = max(0, idx - 30)
            end = min(len(text), idx + 50)
            print(f"  CLAIM FOUND '{pattern}': ...{text[start:end]}...")
    
    # Check for agent/country mentions
    agent_count = lower_text.count("agent")
    print(f"  'agent' mentions: {agent_count}")
    
    # Look for country count claims
    country_claims = re.findall(r'\d+\s*countries?', lower_text)
    print(f"  Country count claims: {country_claims}")
    
except Exception as e:
    print(f"Error: {e}")

# Check /agents page
print("\n=== /agents ===")
for path in ["/agents", "/agents.html", "/agents/index.html"]:
    try:
        url = f"https://xrplme.online{path}"
        r = requests.get(url, timeout=10, verify=False, allow_redirects=True)
        print(f"  {path}: {r.status_code} (final: {r.url})")
        if r.status_code == 200:
            lower_text = r.text.lower()
            if "v4" in lower_text:
                print(f"    V4 mentioned: YES")
            if "evidence" in lower_text:
                print(f"    'evidence' mentioned: YES")
            if "x402" in lower_text:
                print(f"    x402 mentioned: YES")
    except Exception as e:
        print(f"  {path}: ERR {str(e)[:50]}")

# Check API docs page
print("\n=== API Documentation ===")
try:
    r = requests.get("https://xrplme.online/docs-products.html", timeout=10, verify=False)
    print(f"  /docs-products: {r.status_code}")
    if r.status_code == 200:
        lower_text = r.text.lower()
        if "v4" in lower_text:
            print("    V4 mentioned: YES")
        if "pricing" in lower_text or "price" in lower_text:
            prices = re.findall(r'0\.\d+\s*xrp', lower_text)
            print(f"    Prices: {prices}")
        if "mpp" in lower_text:
            print("    MPP mentioned: YES")
        if "x402" in lower_text:
            print("    x402 mentioned: YES")
except Exception as e:
    print(f"  Error: {e}")

# Check homepage-test.html and agents-draft.html for V4 claims
print("\n=== Hidden pages ===")
for page in ["homepage-test.html", "agents-draft.html", "analytics.html"]:
    try:
        r = requests.get(f"https://xrplme.online/{page}", timeout=5, verify=False)
        if r.status_code == 200:
            lower = r.text.lower()
            v4_mention = "v4" in lower or "evidence" in lower
            print(f"  /{page}: 200, V4/evidence mentioned: {v4_mention}")
            if v4_mention:
                # Find the mention
                idx = max(lower.find("v4"), lower.find("evidence"))
                start = max(0, idx - 50)
                end = min(len(r.text), idx + 100)
                print(f"    Context: ...{r.text[start:end]}...")
    except:
        print(f"  /{page}: ERR")

# Check for broken links in api-docs.html
print("\n=== API Docs - Country coverage ===")
try:
    r = requests.get("https://xrplme.online/api-docs.html", timeout=10, verify=False)
    if r.status_code == 200:
        # Find all country options
        options = re.findall(r'value="([^"]+)"', r.text)
        print(f"  Countries in dropdown: {len(options)}")
        print(f"  Countries: {options}")
        
        # Check which are NOT in our list
        expected = ["thailand","vietnam","japan","korea","india","usa","canada","uae","uk",
                    "philippines","singapore","australia","germany","france","brazil","mexico",
                    "switzerland","netherlands","hong_kong","malaysia","indonesia","taiwan",
                    "macau","newzealand","brunei","laos","myanmar","timor-leste","papua-new-guinea","italy"]
        missing = set(expected) - set(options)
        extra = set(options) - set(expected)
        print(f"  Missing from dropdown: {missing}")
        print(f"  Extra in dropdown: {extra}")
except Exception as e:
    print(f"  Error: {e}")

# Test AI endpoint pricing and headers for representative countries
print("\n" + "=" * 80)
print("AI ENDPOINT PRICING VERIFICATION")
print("=" * 80)

test_countries = [
    ("thailand", 8085), ("italy", 8117), ("brazil", 8100),
    ("singapore", 8096), ("usa", 8091), ("hong_kong", 8104),
]

for slug, port in test_countries:
    # Raw
    r_raw = requests.post(
        f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
        json={"message": "audit"},
        timeout=10
    )
    raw_price = "N/A"
    if r_raw.status_code == 402:
        try:
            d = r_raw.json()
            a = d.get("accepts", [{}])[0]
            raw_price = int(a.get("amount", 0)) / 1_000_000
        except:
            pass
    
    # AI
    r_ai = requests.post(
        f"http://127.0.0.1:{port}/api/v1/{slug}/bot/ai",
        json={"message": "audit"},
        timeout=10
    )
    ai_price = "N/A"
    if r_ai.status_code == 402:
        try:
            d = r_ai.json()
            a = d.get("accepts", [{}])[0]
            ai_price = int(a.get("amount", 0)) / 1_000_000
        except:
            pass
    
    print(f"  {slug:<20} raw: {r_raw.status_code} ({raw_price} XRP) | AI: {r_ai.status_code} ({ai_price} XRP)")

# Organizer bot
print("\n=== Organizer Bot Audit ===")
try:
    r = requests.get("https://xrplme.online/wc/v1/organizer/health", timeout=10, verify=False)
    print(f"  /wc/v1/organizer/health: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"  Countries monitored: {d.get('countries_monitored', 'N/A')}")
        print(f"  Countries: {d.get('countries', [])}")
    r2 = requests.post("https://xrplme.online/wc/v1/organizer/bot", 
                       json={"message": "audit"}, timeout=10, verify=False)
    print(f"  /wc/v1/organizer/bot: {r2.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# Check for error response leaking internals
print("\n=== Error Response Inspection (no secrets) ===")
for slug, port in [("thailand", 8085), ("italy", 8117), ("brazil", 8100)]:
    # Test with invalid endpoint
    r = requests.post(f"http://127.0.0.1:{port}/api/v1/{slug}/bot",
                     json={"message": "audit"}, timeout=5)
    # Just check that error messages don't contain file paths
    body = r.text[:200]
    has_path = "/opt/" in body or "/home/" in body or "Traceback" in body
    print(f"  {slug}: 402 body contains paths/traceback: {has_path}")
    if has_path:
        print(f"    Body snippet: {body[:100]}")

print("\n" + "=" * 80)
print("ENVIRONMENT FILE CHECK (existence only, no content)")
print("=" * 80)
env_paths = [
    "/home/xrpladmin/x402-treasury.env",
    "/home/xrpladmin/thoughts/api/.env",
    "/opt/xrplme/thoughts/api/.env",
    "/home/chef/x402-env/x402-treasury.env",
    "/opt/xrplme/thoughts/api/x402-treasury.env",
]
for p in env_paths:
    exists = os.path.exists(p)
    if exists:
        stat = os.stat(p)
        print(f"  {p}: EXISTS (mode={oct(stat.st_mode)}, owner_uid={stat.st_uid})")
    else:
        print(f"  {p}: NOT FOUND")
