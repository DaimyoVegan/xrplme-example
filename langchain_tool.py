"""
LangChain Tool: Query xrplme.online country agents via x402 payment.

This example shows how to wrap xrplme.online as a LangChain tool that
automatically handles the x402 payment flow:

  1. Agent invokes the tool with a query
  2. Tool sends the query to xrplme.online
  3. Server returns 402 with payment details
  4. Tool signs and submits XRP payment via t54 facilitator
  5. Tool retries the request with payment signature
  6. Server returns the data
  7. Tool returns data to the agent

Prerequisites:
  pip install langchain requests x402-xrpl

Usage:
  from langchain.agents import AgentExecutor, initialize_agent
  from langchain.llms import OpenAI
  from langchain_tool import XRPLMECountryTool

  llm = OpenAI(temperature=0)
  tools = [XRPLMECountryTool(country="thailand")]
  agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)
  agent.run("What are Thailand's business registration requirements?")

Note: The x402-xrpl package requires Rust for compilation. If you cannot
install it locally, see python_example.py for a manual payment flow.
"""

import requests
import json
import os
from typing import Optional

try:
    from x402_xrpl import X402Client, FacilitatorClient
    HAS_X402 = True
except ImportError:
    HAS_X402 = False

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun


# --- xrplme client wrapper ---

class XRPLMEClient:
    """Low-level client for xrplme.online x402 payment endpoints."""

    BASE_URL = "https://xrplme.online/wc/v1"

    def __init__(self, pay_to="razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"):
        self.pay_to = pay_to
        self.facilitator = FacilitatorClient(url=os.environ.get(
            "XRPLME_FACILITATOR_URL", "https://xrpl-facilitator-mainnet.t54.ai"
        )) if HAS_X402 else None

    def check_health(self, country: str) -> dict:
        """Check if a country endpoint is healthy."""
        resp = requests.get(f"{self.BASE_URL}/{country}/health", timeout=5)
        return resp.json() if resp.status_code == 200 else {"status": "down"}

    def query(self, country: str, question: str, endpoint: str = "bot") -> dict:
        """
        Query a country endpoint with automatic x402 payment.

        Flow:
        1. POST query -> get 402 with invoice details
        2. Sign XRP payment via facilitator
        3. POST with payment header -> get 200 with data
        """
        url = f"{self.BASE_URL}/{country}/{endpoint}"
        payload = {"message": question, "session_id": f"langchain-{country}"}

        # Step 1: Send query, get 402
        resp = requests.post(url, json=payload, timeout=15)

        if resp.status_code != 402:
            if resp.status_code == 200:
                return resp.json()
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
            # Fallback: manual payment instructions
            return {
                "error": "x402-xrpl not installed",
                "payment_required": {
                    "amount_xrp": amount / 1_000_000,
                    "pay_to": self.pay_to,
                    "invoice_id": invoice_id,
                    "payment_url": data.get("resource", {}).get("url", ""),
                },
                "instructions": "Pay via Xaman/Joey wallet, then retry the query.",
            }

        # Step 4: Retry with payment header
        retry_headers = {**headers, **x402_headers}
        retry_headers["Content-Type"] = "application/json"

        resp2 = requests.post(url, json=payload, headers=retry_headers, timeout=15)
        if resp2.status_code == 200:
            return resp2.json()
        return {"error": f"Payment retry failed: HTTP {resp2.status_code}"}


# --- LangChain Tool wrapper ---

class XRPLMECountryTool(BaseTool):
    """
    LangChain tool for querying xrplme.online country agents.

    Automatically handles x402 payment flow. Set XRPLME_PAYMENT_WALLET_SEED
    environment variable for automatic payment signing.

    Example:
        tool = XRPLMECountryTool(country="thailand")
        tool.run("What are Thailand's business registration requirements?")
    """

    name = "xrplme_country_query"
    description = (
        "Query a specific country's economic/regulatory data via xrplme.online. "
        "Returns source-backed factual data or AI-enhanced analysis. "
        "Requires x402 payment (0.1 XRP for facts, 0.5 XRP for AI analysis). "
        "Input format: 'question' or 'question | endpoint=bot/ai' to specify endpoint."
    )

    def __init__(self, country: str = "thailand", endpoint: str = "bot"):
        super().__init__()
        self.country = country
        self.endpoint = endpoint
        self.client = XRPLMEClient()

    def _parse_input(self, query: str) -> tuple:
        """Parse query for inline endpoint override."""
        if "|" in query and "endpoint=" in query:
            parts = query.rsplit("|", 1)
            q = parts[0].strip()
            ep = parts[1].replace("endpoint=", "").strip()
            return q, ep
        return query, self.endpoint

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        question, endpoint = self._parse_input(query)

        try:
            data = self.client.query(self.country, question, endpoint)
            if "error" in data:
                return json.dumps(data, indent=2)
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error querying xrplme: {e}"

    def _arun(self, query: str):
        raise NotImplementedError("Async not supported")


# --- Usage example ---

if __name__ == "__main__":
    # Example 1: Basic query
    client = XRPLMEClient()

    print("Checking health...")
    health = client.check_health("thailand")
    print(f"  Status: {health.get('status')}")
    print(f"  Records: {health.get('data_records')}")

    # Example 2: Query (will trigger 402 payment flow)
    print("\nQuerying Thailand business registration...")
    result = client.query(
        "thailand",
        "What are Thailand business registration requirements?",
        "bot"
    )
    print(json.dumps(result, indent=2))

    # Example 3: AI-enhanced query (0.5 XRP)
    print("\nQuerying Japan regulatory comparison...")
    result = client.query(
        "japan",
        "Compare Japan's crypto regulations with Singapore's",
        "bot/ai"
    )
    print(json.dumps(result, indent=2))
