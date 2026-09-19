"""
LlamaIndex Integration: Querying xrplme.online country agents via x4002 payment.

This example shows how to use xrplme.online as a LlamaIndex tool that
automatically handles the x402 payment flow for AI agents.

Prerequisites:
  pip install llama-index requests x402-xrpl

Usage:
  from llama_index.agent import AgentChat
  from llama_index.llms import OpenAI
  from llama_index_integration import XRPLMETool

  llm = OpenAI(model="gpt-4")
  tools = [XRPLMETool(country="thailand")]
  agent = AgentChat.from_tools(tools, llm=llm, verbose=True)
  agent.chat("What are Thailand's business registration requirements?")

The tool automatically:
  1. Sends the AI agent's query to the country endpoint
  2. Handles the 402 payment response (signs XRP via t54 facilitator)
  3. Retries with payment header
  4. Returns the data to the agent

For manual payment flow (without x402-xrpl), see python_example.py.
"""

import requests
import json
import os
from typing import Optional, Dict, Any, List

try:
    from x402_xrpl import FacilitatorClient
    HAS_X402 = True
except ImportError:
    HAS_X402 = False

from llama_index.core.tools import FunctionTool


class XRPLMEToolkit:
    """
    Toolkit for querying xrplme.online country agents via x402 payment.
    """

    BASE_URL = "https://xrplme.online/wc/v1"

    def __init__(self, pay_to="razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"):
        self.pay_to = pay_to
        self.facilitator = FacilitatorClient(url=os.environ.get(
            "XRPLME_FACILITATOR_URL", "https://xrpl-facilitator-mainnet.t54.ai"
        )) if HAS_X402 else None

    def check_health(self, country: str) -> Dict[str, Any]:
        """Check if a country endpoint is healthy (free, no payment)."""
        resp = requests.get(f"{self.BASE_URL}/{country}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return {"status": "unhealthy", "http_code": resp.status_code}

    def query_country(self, country: str, question: str,
                      endpoint: str = "bot",
                      session_id: str = "llamaindex-001") -> Dict[str, Any]:
        """
        Query a country endpoint with x402 auto-payment.

        Args:
            country: Country slug (e.g., "thailand", "japan", "hong_kong")
            question: The query to ask the country agent
            endpoint: "bot" (0.1 XRP) or "bot/ai" (0.5 XRP)
            session_id: Unique session identifier for payment tracking

        Returns:
            Dict with query results or payment instructions
        """
        url = f"{self.BASE_URL}/{country}/{endpoint}"
        payload = {"message": question, "session_id": session_id}

        # Step 1: Send query — expect 402
        resp = requests.post(url, json=payload, timeout=15)

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code != 402:
            return {"error": f"HTTP {resp.status_code}", "detail": resp.text}

        # Step 2: Parse payment details
        data = resp.json()
        payment = data["accepts"][0]
        invoice_id = payment["extra"]["invoiceId"]
        amount = int(payment["amount"])
        headers = resp.headers

        # Step 3: Sign payment via facilitator
        if self.facilitator:
            x402_headers = self.facilitator.pay(
                amount=amount,
                pay_to=self.pay_to,
                invoice_id=invoice_id,
            )
        else:
            # Fallback: return instructions for manual payment
            return {
                "payment_required": True,
                "amount_xrp": amount / 1_000_000,
                "pay_to": self.pay_to,
                "invoice_id": invoice_id,
                "payment_url": data.get("resource", {}).get("url", ""),
                "instructions": "Pay via Xaman/Joey wallet, then re-invoke this tool.",
            }

        # Step 4: Retry with payment-signed header
        retry_headers = {**headers, **x402_headers, "Content-Type": "application/json"}
        resp2 = requests.post(url, json=payload, headers=retry_headers, timeout=15)

        if resp2.status_code == 200:
            return resp2.json()
        return {"error": f"Payment retry failed: HTTP {resp2.status_code}"}


def get_xrplme_tools(countries: List[str] = None, endpoint: str = "bot") -> List[FunctionTool]:
    """
    Get LlamaIndex FunctionTools for querying xrplme country agents.

    Args:
        countries: List of country slugs to include (default: all 24)
        endpoint: "bot" (0.1 XRP) or "bot/ai" (0.5 XRP)

    Returns:
        List of LlamaIndex FunctionTool instances
    """
    toolkit = XRPLMEToolkit()

    if countries is None:
        countries = [
            "thailand", "vietnam", "japan", "korea", "india", "usa", "canada",
            "uae", "uk", "philippines", "singapore", "australia", "germany",
            "france", "brazil", "mexico", "switzerland", "netherlands",
            "hong_kong", "malaysia", "indonesia", "taiwan", "macau", "newzealand",
        ]

    tools = []
    for country in countries:
        tool = FunctionTool(
            fn=toolkit.query_country,
            name=f"query_{country}",
            description=(
                f"Query {country}'s economic/regulatory data via xrplme.online. "
                f"x402 payment: {0.1 if endpoint == 'bot' else 0.5} XRP. "
                f"AI agent sends query, pays automatically, and receives source-backed data."
            ),
            fn_kwargs={
                "country": {"type": "string", "description": f"Country slug: {country}"},
                "question": {"type": "string", "description": "The question to ask the country agent"},
                "endpoint": {"type": "string", "default": endpoint},
            },
        )
        tools.append(tool)

    return tools


# --- Usage examples ---

if __name__ == "__main__":
    toolkit = XRPLMEToolkit()

    # Example 1: Check all countries' health
    print("=== Country Health Check ===")
    for country in [
        "thailand", "vietnam", "japan", "korea", "india", "usa",
        "singapore", "philippines", "hong_kong", "malaysia", "taiwan",
    ]:
        health = toolkit.check_health(country)
        status = health.get("status", "down")
        records = health.get("data_records", "?")
        print(f"  {country:<18} {status:<8} records={records}")

    # Example 2: Query a country (triggers x402 payment)
    print("\n=== Thailand Business Registration ===")
    result = toolkit.query_country(
        country="thailand",
        question="What are Thailand business registration requirements?",
        endpoint="bot",
    )
    print(json.dumps(result, indent=2))

    # Example 3: AI-enhanced query (0.5 XRP)
    print("\n=== Japan vs Singapore Crypto Comparison ===")
    result = toolkit.query_country(
        country="japan",
        question="Compare Japan's crypto regulations with Singapore's",
        endpoint="bot/ai",
    )
    print(json.dumps(result, indent=2))

    # Example 4: Use with LlamaIndex Agent
    print("\n=== LlamaIndex Agent Example ===")
    print("  from llama_index.agent import AgentChat")
    print("  from llama_index.llms import OpenAI")
    print("  from llama_index_integration import get_xrplme_tools")
    print("")
    print("  llm = OpenAI(model='gpt-4')")
    print("  tools = get_xrplme_tools(countries=['thailand', 'japan', 'hong_kong'])")
    print("  agent = AgentChat.from_tools(tools, llm=llm, verbose=True)")
    print("  agent.chat('What are Thailand business registration requirements?')")
