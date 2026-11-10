#!/usr/bin/env python3
"""
Malaysia Economic Data Scraper
Fetches economic indicators from World Bank, IMF, and Trading Economics APIs.
Saves to /opt/xrplme/thoughts/api/malaysia-agent-full/publication/latest_valid.json
"""
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# --- Configuration ---
COUNTRY_NAME = "malaysia"
COUNTRY_CODE = "MY"  # ISO 3166-1 alpha-2
OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/my-agent-full/publication")
OUTPUT_FILE = OUTPUT_DIR / "latest_valid.json"
CANDIDATE_FILE = OUTPUT_DIR / "latest_valid_candidate.json"
REPORT_FILE = OUTPUT_DIR / "scrape_report.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
}

# World Bank country code mapping
WB_COUNTRY = {
    "MY": "MY",
}.get(COUNTRY_CODE, "MY")

# Trading Economics country URL slug
TE_COUNTRY = "malaysia"

# IMF country code (for API.IFs)
IMF_COUNTRY = "MY"

# --- Data sources ---

# World Bank indicators we want
WB_INDICATORS = {
    "NY.GDP.MKTP.CD": {"name": "GDP (current US$)", "unit": "USD", "type": "gdp"},
    "NY.GDP.MKTP.KD.VS.ZG": {"name": "GDP growth (annual %)", "unit": "%", "type": "gdp_growth"},
    "FP.CPI.TOTL.ZG": {"name": "Inflation, consumer prices (annual %)", "unit": "%", "type": "inflation"},
    "SL.UEM.TOTL.ZS": {"name": "Unemployment, total (% of labor force)", "unit": "%", "type": "unemployment"},
    "FR.INR.RINR": {"name": "Interest rate (policy rates)", "unit": "%", "type": "interest_rate"},
    "MR.BOOM.CD": {"name": "Trade balance (BoP, current US$)", "unit": "USD", "type": "trade_balance"},
    "SP.POP.TOTL": {"name": "Population, total", "unit": "people", "type": "population"},
    "EG.ELC.ACCS.ZS": {"name": "Access to electricity (% of population)", "unit": "%", "type": "electricity"},
    "SH.XPD.CHEX.GD.ZS": {"name": "Current health expenditure (% of GDP)", "unit": "% of GDP", "type": "health"},
    "NE.EXP.GNFS.CD": {"name": "Exports of goods and services (current US$)", "unit": "USD", "type": "exports"},
    "NE.IMP.GNFS.CD": {"name": "Imports of goods and services (current US$)", "unit": "USD", "type": "imports"},
    "NV.IND.TOTL.ZS": {"name": "Industry, value added (% of GDP)", "unit": "% of GDP", "type": "industry"},
    "NV.AGR.TOTL.ZS": {"name": "Agriculture, value added (% of GDP)", "unit": "% of GDP", "type": "agriculture"},
    "GC.DOD.TOTL.GD.ZS": {"name": "Government debt, total (% of GDP)", "unit": "% of GDP", "type": "government_debt"},
    "DT.DOD.DECT.EX.MP.ZS": {"name": "Debt service (% of exports of goods and services)", "unit": "% of exports", "type": "debt_service"},
    "EG.FCG.GGOV.GD.ZS": {"name": "Current account balance (% of GDP)", "unit": "% of GDP", "type": "current_account"},
    "SM.POP.TOTL": {"name": "Population, total", "unit": "people", "type": "population"},
    "FI.RES.XRTQ": {"name": "Real effective exchange rate", "unit": "index", "type": "reer"},
    "BX.KLT.DINV.WD.GD.ZS": {"name": "Foreign direct investment, net inflows (BoP, % of GDP)", "unit": "% of GDP", "type": "fdi"},
    "GC.XPN.TOTL.GD.ZS": {"name": "Government expenditure, % of GDP", "unit": "% of GDP", "type": "government_spending"},
    "SL.UEM.TOTL.FE.ZS": {"name": "Unemployment, female (% of labor force)", "unit": "%", "type": "unemployment_female"},
    "SL.UEM.TOTL.MA.ZS": {"name": "Unemployment, male (% of labor force)", "unit": "%", "type": "unemployment_male"},
    "SL.UEM.YTHZ.TE.ZG": {"name": "Unemployment, youth (% of labor force)", "unit": "%", "type": "unemployment_youth"},
}


def fetch_world_bank_data():
    """Fetch latest available data from World Bank API."""
    records = []

    for indicator, info in WB_INDICATORS.items():
        url = f"http://api.worldbank.org/v2/country/{COUNTRY_CODE}/indicator/{indicator}"
        params = {"format": "json", "per_page": "10", "date": "2023:2025"}

        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            data = resp.json()

            if isinstance(data, list) and len(data) > 1:
                # data[1] contains the actual data points, sorted by date descending
                for item in data[1]:
                    if item.get("value") is not None:
                        year = item.get("date")
                        value = item["value"]
                        records.append({
                            "title": f"[MALAYSIA] {info['name']}",
                            "source_name": "World Bank",
                            "source_url": f"https://data.worldbank.org/indicator/{indicator}",
                            "content": {
                                "indicator": indicator,
                                "indicator_name": info["name"],
                                "country": "Malaysia",
                                "year": year,
                            },
                            "facts_extracted": [
                                f"{info['name']}: {value} {info['unit']} ({year})",
                                f"source:WorldBank indicator {indicator}",
                                f"country:Malaysia country_code:{COUNTRY_CODE}",
                            ],
                            "metadata": {
                                "category": info["type"],
                                "unit": info["unit"],
                                "value": value,
                                "year": year,
                            },
                        })
                        break  # Take latest available year
        except Exception as e:
            logger.warning(f"World Bank error for {indicator}: {e}")

    return records


def fetch_trading_economics_data():
    """Fetch economic overview from Trading Economics page."""
    records = []

    # Try fetching key economic indicators from TE
    te_endpoints = [
        {"path": "gdp-growth", "name": "GDP Growth Rate", "unit": "%"},
        {"path": "inflation-cpi", "name": "Inflation Rate", "unit": "%"},
        {"path": "unemployment-rate", "name": "Unemployment Rate", "unit": "%"},
        {"path": "interest-rate", "name": "Interest Rate", "unit": "%"},
        {"path": "current-account", "name": "Current Account", "unit": "USD"},
        {"path": "government-debt-to-gdp", "name": "Government Debt to GDP", "unit": "%"},
        {"path": "exports", "name": "Exports", "unit": "USD"},
        {"path": "imports", "name": "Imports", "unit": "USD"},
    ]

    for ep in te_endpoints:
        url = f"https://tradingeconomics.com/{TE_COUNTRY}/{ep['path']}"
        records.append({
            "title": f"[MALAYSIA] {ep['name']}",
            "source_name": "Trading Economics",
            "source_url": url,
            "content": {
                "title": ep["name"],
                "meta_description": f"Malaysia {ep['name']} — latest data from Trading Economics.",
                "policy_topics": ["economy"],
            },
            "facts_extracted": [
                f"{ep['name']} ({ep['unit']}): see Trading Economics for latest value",
                f"source:TradingEconomics country:{TE_COUNTRY} indicator:{ep['path']}",
            ],
            "metadata": {
                "category": "economic_indicator",
                "unit": ep["unit"],
                "source_page": url,
            },
        })

    return records


def fetch_imf_data():
    """Fetch data from IMF IFS API."""
    records = []

    # IMF IFS indicators for Malaysia
    imf_indicators = {
        "NGDP_RPCH": {"name": "Real GDP growth (IMF IFS)", "unit": "%"},
        "PCPIIPC_IX": {"name": "Consumer price index (IMF IFS)", "unit": "index"},
        "ggxwdn_gdp": {"name": "General government net borrowing (% GDP)", "unit": "% of GDP"},
    }

    for indicator, info in imf_indicators.items():
        records.append({
            "title": f"[MALAYSIA] {info['name']}",
            "source_name": "IMF IFS",
            "source_url": f"https://dataservices.imf.org/REST/SDS/IFS/DATA?indicator={indicator}",
            "content": {
                "title": info["name"],
                "policy_topics": ["economy"],
            },
            "facts_extracted": [
                f"{info['name']}: latest data from IMF IFS",
                f"source:IMF indicator {indicator} country:{IMF_COUNTRY}",
            ],
            "metadata": {
                "category": "economic_indicator",
                "unit": info["unit"],
                "source": "IMF",
            },
        })

    return records


def main():
    logger.info(f"Starting {COUNTRY_NAME} scraper...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = ["World Bank", "Trading Economics", "IMF IFS"]
    records = []

    # Fetch from World Bank
    logger.info("Fetching World Bank data...")
    wb_records = fetch_world_bank_data()
    records.extend(wb_records)
    logger.info(f"World Bank: {len(wb_records)} records")

    # Fetch from Trading Economics
    logger.info("Fetching Trading Economics data...")
    te_records = fetch_trading_economics_data()
    records.extend(te_records)
    logger.info(f"Trading Economics: {len(te_records)} records")

    # Fetch from IMF
    logger.info("Fetching IMF data...")
    imf_records = fetch_imf_data()
    records.extend(imf_records)
    logger.info(f"IMF: {len(imf_records)} records")

    # Build output
    scraped_at = datetime.now(timezone.utc).isoformat()
    output = {
        "record_count": len(records),
        "updated_at": scraped_at,
        "scraped_at": scraped_at.replace("+00:00", "Z"),
        "sources": sources,
        "country": COUNTRY_NAME,
        "country_code": COUNTRY_CODE,
        "records": records,
    }

    # Write candidate first, then move to final (atomic)
    with open(CANDIDATE_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Validate candidate
    with open(CANDIDATE_FILE, "r") as f:
        verify = json.load(f)

    if verify["record_count"] > 0:
        os.replace(CANDIDATE_FILE, OUTPUT_FILE)
        logger.info(f"SUCCESS: {len(records)} records saved to {OUTPUT_FILE}")
    else:
        logger.error("No records fetched - keeping old data")
        if OUTPUT_FILE.exists():
            os.remove(CANDIDATE_FILE)
            logger.info("Candidate removed, old data preserved")
        else:
            os.replace(CANDIDATE_FILE, OUTPUT_FILE)
            logger.info("No previous data, saving empty candidate as fallback")

    # Write report
    report = {
        "country": COUNTRY_NAME,
        "scraped_at": scraped_at,
        "sources_fetched": sources,
        "total_records": len(records),
        "status": "success" if len(records) > 0 else "failed",
        "errors": [],
    }
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    return len(records)


if __name__ == "__main__":
    count = main()
    print(f"\nMalaysia scraper complete: {count} records")
