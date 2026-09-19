"""
Python example: Querying xrplme.online country agents via x402 payment.

Prerequisites:
  pip install requests

Usage:
  python python_example.py [country] [query]

Examples:
  python python_example.py
  python python_example.py thailand "What are Thailand's business registration requirements?"
  python python_example.py japan "What is Japan's current interest rate?"

This example shows the x402 payment flow:
  1. Send a query to the endpoint
  2. If 402 is returned, the script displays payment details
  3. Pay the XRP invoice via Xaman/Joey wallet
  4. Re-run the script to receive the data (server checks invoice status)

For full x402 payment automation, see langchain_tool.py and
llama_index_integration.py which use the x402 framework for
automatic payment signing and retry.
"""

import requests
import json
import sys

BASE_URL = "https://xrplme.online/wc/v1"

# All 24 supported countries
COUNTRIES = [
    "thailand", "vietnam", "japan", "korea", "india", "usa", "canada",
    "uae", "uk", "philippines", "singapore", "australia", "germany",
    "france", "brazil", "mexico", "switzerland", "netherlands",
    "hong_kong", "malaysia", "indonesia", "taiwan", "macau", "newzealand",
]

# Pricing (in XRP)
PRICES = {
    "bot": 0.1,       # Standard API
    "bot/ai": 0.5,    # AI Enhanced API
}


def check_health(country):
    """Check if a country endpoint is healthy (no payment required)."""
    url = f"{BASE_URL}/{country}/health"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        print(f"  [HEALTH] {country}: {data.get('status', 'unknown')}")
        print(f"    Records: {data.get('data_records', '?')}")
        return True
    else:
        print(f"  [HEALTH] {country}: HTTP {resp.status_code}")
        return False


def query_country(country, query, endpoint="bot"):
    """
    Send a query to a country endpoint.

    If the server returns 402, payment details are displayed and the
    user is instructed to pay via Xaman/Joey wallet, then re-run the query.

    After payment, re-running the same query (same session_id) will
    return the data.
    """
    url = f"{BASE_URL}/{country}/{endpoint}"
    payload = {
        "message": query,
        "session_id": f"py-example-{country}",
    }

    print(f"\n>>> Querying: {country} / {endpoint} ({PRICES.get(endpoint, '?')} XRP)")
    print(f"    Query: {query}")
    print(f"    URL: {url}")

    try:
        resp = requests.post(url, json=payload, timeout=15)
    except requests.exceptions.Timeout:
        print("    ERROR: Request timed out (server may be slow to process)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"    ERROR: {e}")
        return None

    if resp.status_code == 402:
        try:
            data = resp.json()
            payment = data.get("accepts", [{}])[0]
            amount_drops = payment.get("amount", 0)
            amount_xrp = amount_drops / 1_000_000 if amount_drops else 0
            pay_to = payment.get("payTo") or payment.get("pay_to", "N/A")

            print("\n    [402 PAYMENT REQUIRED]")
            print(f"    Amount: {amount_drops} drops ({amount_xrp} XRP)")
            print(f"    Pay to: {pay_to}")

            invoice_id = ""
            if "extra" in payment:
                invoice_id = payment["extra"].get("invoiceId", "")
            if not invoice_id:
                invoice_id = payment.get("invoiceId", "")
            print(f"    Invoice ID: {invoice_id}")

            if data.get("resource") and data["resource"].get("url"):
                print(f"    Payment URL: {data['resource']['url']}")

            print("\n    --- ACTION REQUIRED ---")
            print("    1. Open Xaman or Joey wallet")
            print(f"    2. Send {amount_xrp} XRP to: {pay_to}")
            print(f"    3. Use Invoice ID: {invoice_id}")
            print("    4. Re-run this script to retrieve the data")
            return None
        except (json.JSONDecodeError, KeyError, IndexError):
            print("    [402] Could not parse payment details")
            print(f"    Raw response: {resp.text[:500]}")
            return None

    elif resp.status_code == 200:
        try:
            data = resp.json()
            print(f"\n    [200 SUCCESS] Response length: {len(json.dumps(data))} chars")
            print(f"\n    {json.dumps(data, indent=2)}")
            return data
        except json.JSONDecodeError:
            print(f"\n    [200 SUCCESS] Non-JSON response:")
            print(f"    {resp.text[:500]}")
            return resp.text
    else:
        print(f"    [ERROR] HTTP {resp.status_code}")
        print(f"    {resp.text[:500]}")
        return None


def list_countries():
    """List all available countries and check their health."""
    print("\n=== Available Countries (24) ===")
    print(f"{'Country':<18} {'Health':<8} {'Records':>8}")
    print("-" * 40)

    for country in COUNTRIES:
        try:
            resp = requests.get(f"{BASE_URL}/{country}/health", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "?")
                records = data.get("data_records", "?")
                print(f"{country:<18} {status:<8} {records:>8}")
            else:
                print(f"{country:<18} {'DOWN':<8} {'?':>8}")
        except Exception:
            print(f"{country:<18} {'DOWN':<8} {'?':>8}")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "list":
        list_countries()
        return

    query = "What are Thailand\'s business registration requirements?"
    country = "thailand"
    endpoint = "bot"

    if len(args) >= 1 and args[0] in COUNTRIES:
        country = args[0]
    if len(args) >= 2:
        query = args[1]
    if len(args) >= 3:
        endpoint = args[2]

    # Check health first (free, no payment)
    check_health(country)

    # Send the query (will get 402 if no payment yet)
    query_country(country, query, endpoint)


if __name__ == "__main__":
    main()
