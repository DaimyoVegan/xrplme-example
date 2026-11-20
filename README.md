# xrplme.online — AI Agent & Developer Tools

## Overview

**xrplme.online** is a source-backed platform providing real-time economic and
policy data for **130 countries** via x402 payment over the XRP Ledger. Each country
exposes two endpoints — a Standard API and an AI-Enhanced API — that return
structured data sourced from government APIs and official publications.

AI agents query the platform by submitting an x402 payment (HTTP 402 → pay in
XRP → retry for data). No API keys, no KYC, no subscriptions.

### Countries (91)

All 130 countries are live on every rail. The current list is at
**https://xrplme.online/countries.html**, and the slugs are enumerated at the
bottom of this file.

### Endpoints

| Endpoint | Price | Description |
|---|---|---|
| `POST /wc/v1/{country}/bot` | 1.0 XRP | Standard API — factual data from government sources |
| `POST /wc/v1/{country}/bot/ai` | 5.0 XRP | AI Enhanced API — analyzed data, comparison, recommendations |
| `POST /wc/v1/{country}/health` | FREE | Health check — returns 200 with service status |

### How x402 Payment Works

1. **Send query** — POST your query to the endpoint
2. **Receive 402** — Server returns 402 Payment Required with XRP invoice details
3. **Pay** — Send the invoice amount in XRP to the specified address via Xaman/Joey wallet
4. **Retry** — Resend the same query; server returns your data

## Quick Start

### Python

```python
import requests
import json

BASE = "https://xrplme.online/wc/v1"
COUNTRY = "thailand"   # any of the 130 countries — see slug list below
ENDPOINT = "bot"       # or "bot/ai" for AI-enhanced (5 XRP)
QUERY = "What are Thailand's business registration requirements?"

def query_xrplme(query, country=COUNTRY, endpoint=ENDPOINT):
    url = f"{BASE}/{country}/{endpoint}"
    payload = {
        "message": query,
        "session_id": "agent-session-001"
    }

    resp = requests.post(url, json=payload, timeout=15)

    if resp.status_code == 402:
        data = resp.json()
        payment = data["accepts"][0]
        print(f"Payment required: {int(payment['amount']) / 1000000} XRP")
        print(f"Pay to: {payment['payTo']}")
        print(f"Invoice ID: {payment['extra']['invoiceId']}")
        print("Pay via Xaman/Joey wallet, then call this function again.")
        return

    if resp.status_code == 200:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data

    print(f"Error {resp.status_code}: {resp.text}")
    return None

# Example
query_xrplme("What are the VAT rates in Thailand?")
```

### JavaScript / Browser

```javascript
async function queryXRPLME(query, country = "thailand", endpoint = "bot") {
  const url = `https://xrplme.online/wc/v1/${country}/${endpoint}`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: query,
      session_id: "web-session-001"
    })
  });

  if (response.status === 402) {
    const data = await response.json();
    const payment = data.accepts[0];
    console.log("Payment required:", int(payment.amount) / 1000000, "XRP");
    console.log("Pay to:", payment.payTo);
    console.log("Invoice ID:", payment.extra.invoiceId);
    // Redirect user to wallet for payment, then retry
    return;
  }

  if (response.status === 200) {
    const data = await response.json();
    console.log("Data:", data);
    return data;
  }
}

// Example
queryXRPLME("Compare Thailand vs Vietnam for tech startup");
```

### AI Agent (curl)

```bash
# Step 1: Send query (get 402 with payment details)
curl -X POST https://xrplme.online/wc/v1/thailand/bot \
  -H "Content-Type: application/json" \
  -d '{"message":"What are Thailand business registration requirements?","session_id":"agent-001"}'

# Step 2: Pay the XRP invoice (via Xaman/Joey wallet)
# Step 3: Resend the same query to get data
curl -X POST https://xrplme.online/wc/v1/thailand/bot \
  -H "Content-Type: application/json" \
  -d '{"message":"What are Thailand business registration requirements?","session_id":"agent-001"}'
```

### Health Check (Free)

```bash
curl https://xrplme.online/wc/v1/thailand/health
```

## Pricing

| Endpoint | Price | Use Case |
|---|---|---|
| `/bot` | 1.0 XRP | Factual data — scraped government sources, fast |
| `/bot/ai` | 5.0 XRP | AI-enhanced — analysis, comparison, recommendations |
| `/health` | FREE | Service status check |

## Investigate — screening and company look-up

Two more datasets on the same rails and the same payment flow.

| Endpoint | Price (XRPL / USDC) | What you get |
|---|---|---|
| `/wc/screen/bot` · `-solana` · `-evm` | 2 XRP / $2.00 | Screening: matches, programme, designation date, citation |
| `/wc/entity/lookup/bot` · `-solana` · `-evm` | 1 XRP / $1.00 | Company record: legal name, status, jurisdiction, entity ID |
| `/wc/entity/ownership/bot` · `-solana` · `-evm` | 5 XRP / $5.00 | Ownership chain to the ultimate parent, plus direct subsidiaries |

Screening takes `{"name": "..."}`. Look-up takes `{"query": "company name or entity ID"}`.
Ownership takes `{"query": "<entity ID>"}`.

Machine-readable pricing for agents: **https://xrplme.online/llms.txt**

## API Documentation

Full interactive API documentation is available at:
**https://xrplme.online/api-docs.html**

## Supported Country Slugs

albania, algeria, argentina, australia, austria, bangladesh, bhutan,
brazil, brunei, bulgaria, cambodia, canada, chile, colombia, croatia,
cyprus, czechia, denmark, egypt, estonia, finland, france, germany,
ghana, greece, guatemala, hong_kong, hungary, iceland, india, indonesia,
iran, iraq, ireland, italy, japan, kazakhstan, kenya, korea, laos,
latvia, libya, lithuania, luxembourg, macau, macedonia, malaysia,
maldives, malta, mexico, moldova, morocco, myanmar, nepal, netherlands,
newzealand, nigeria, norway, papua-new-guinea, paraguay, philippines,
poland, portugal, romania, rwanda, saudi_arabia, senegal, serbia,
singapore, slovakia, slovenia, south_africa, spain, sri_lanka, sweden,
switzerland, syria, taiwan, thailand, timor-leste, tunisia, turkey, uae,
uk, ukraine, uruguay, usa, venezuela, vietnam, yemen, mongolia,
peru, georgia, mauritius, ecuador, costa_rica, panama,
dominican_republic, belgium, israel,
armenia, kyrgyzstan, el_salvador, bahamas, bahrain, azerbaijan, uzbekistan, ethiopia, uganda, botswana, fiji, tajikistan, lebanon, mozambique, honduras, bolivia, jordan, tanzania, zambia, namibia,
pakistan, qatar, oman, kuwait, angola, cote_divoire, cameroon, zimbabwe, jamaica, trinidad_and_tobago

## License

MIT
