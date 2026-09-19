/**
 * JavaScript example: Querying xrplme.online country agents via x402 payment.
 *
 * Usage in browser:
 *   Include this script, then call:
 *   queryXRPLME("What are Thailand's requirements?", "thailand", "bot")
 *
 * Usage in Node.js:
 *   const { queryXRPLME, checkHealth } = require('./javascript_example.js');
 *
 * The x402 payment flow:
 *   1. Send a POST query to the endpoint
 *   2. If 402, display payment details (amount, pay_to, invoice_id)
 *   3. User pays via Xaman/Joey wallet
 *   4. Resend the same query to receive data
 *
 * For automated x402 payment signing, see langchain_tool.py and
 * llama_index_integration.py.
 */

const BASE_URL = "https://xrplme.online/wc/v1";

const COUNTRIES = [
  "thailand", "vietnam", "japan", "korea", "india", "usa", "canada",
  "uae", "uk", "philippines", "singapore", "australia", "germany",
  "france", "brazil", "mexico", "switzerland", "netherlands",
  "hong_kong", "malaysia", "indonesia", "taiwan", "macau", "newzealand",
];

const PRICES = {
  "bot": 0.1,
  "bot/ai": 0.5,
};

/**
 * Check the health of a country endpoint (no payment required).
 * @param {string} country - Country slug (e.g., "thailand")
 * @returns {Promise<Object|null>}
 */
async function checkHealth(country) {
  try {
    const resp = await fetch(`${BASE_URL}/${country}/health`);
    if (resp.status === 200) {
      const data = await resp.json();
      console.log(`[HEALTH] ${country}: ${data.status}`);
      console.log(`  Records: ${data.data_records}`);
      return data;
    } else {
      console.log(`[HEALTH] ${country}: HTTP ${resp.status}`);
      return null;
    }
  } catch (err) {
    console.error(`[HEALTH] ${country}: ${err.message}`);
    return null;
  }
}

/**
 * Query a country endpoint via x402 payment.
 *
 * @param {string} query - The query message
 * @param {string} country - Country slug (default: "thailand")
 * @param {string} endpoint - "bot" (0.1 XRP) or "bot/ai" (0.5 XRP)
 * @param {string} sessionId - Unique session ID for payment tracking
 * @returns {Promise<Object|null>} Query result or null
 */
async function queryXRPLME(query, country = "thailand", endpoint = "bot", sessionId = "js-example") {
  const url = `${BASE_URL}/${country}/${endpoint}`;
  const payload = {
    message: query,
    session_id: `${sessionId}-${country}`,
  };

  console.log(`\n>>> Querying: ${country} / ${endpoint} (${PRICES[endpoint]} XRP)`);
  console.log(`    Query: ${query}`);
  console.log(`    URL: ${url}`);

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (resp.status === 402) {
      const data = await resp.json();
      const payment = data.accepts[0];
      const amountDrops = payment.amount;
      const amountXRP = amountDrops / 1_000_000;
      const payTo = payment.payTo || payment.pay_to || "N/A";
      const invoiceId = payment.extra?.invoiceId || payment.invoiceId || "";

      console.log("\n    [402 PAYMENT REQUIRED]");
      console.log(`    Amount: ${amountDrops} drops (${amountXRP} XRP)`);
      console.log(`    Pay to: ${payTo}`);
      console.log(`    Invoice ID: ${invoiceId}`);

      if (data.resource?.url) {
        console.log(`    Payment URL: ${data.resource.url}`);
      }

      console.log("\n    --- ACTION REQUIRED ---");
      console.log("    1. Open Xaman or Joey wallet");
      console.log(`    2. Send ${amountXRP} XRP to: ${payTo}`);
      console.log(`    3. Use Invoice ID: ${invoiceId}`);
      console.log("    4. Re-run to retrieve the data");

      return { paymentRequired: true, amount: amountXRP, payTo, invoiceId };
    }

    if (resp.status === 200) {
      const data = await resp.json();
      console.log(`\n    [200 SUCCESS]`);
      console.log(`    ${JSON.stringify(data, null, 2)}`);
      return data;
    }

    console.error(`    [ERROR] HTTP ${resp.status}: ${resp.statusText}`);
    return null;
  } catch (err) {
    console.error(`    [ERROR] ${err.message}`);
    return null;
  }
}

/**
 * List all countries and their health status.
 */
async function listCountries() {
  console.log("\n=== Available Countries (24) ===\n");
  for (const country of COUNTRIES) {
    await checkHealth(country);
  }
}

// Export for Node.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = { queryXRPLME, checkHealth, listCountries, COUNTRIES, PRICES };
}

// Browser usage example:
// queryXRPLME("What are Thailand's VAT rates?", "thailand", "bot");
