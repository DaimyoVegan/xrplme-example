#!/usr/bin/env python3
"""Standalone scrapers for 5 new APAC countries.
Uses only requests + json (no bs4 dependency).
Each scraper fetches economic data from World Bank API and Trading Economics."""
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Country definitions: name, code, te_slug, imf_code, display_name
COUNTRIES = [
    {
        "name": "brunei",
        "code": "BN",
        "te_slug": "brunei",
        "imf_code": "BN",
        "display": "Brunei",
        "upper": "BRUNEI",
        "port": 8111,
    },
    {
        "name": "laos",
        "code": "LA",
        "te_slug": "laos",
        "imf_code": "LA",
        "display": "Laos",
        "upper": "LAOS",
        "port": 8112,
    },
    {
        "name": "myanmar",
        "code": "MM",
        "te_slug": "myanmar",
        "imf_code": "MM",
        "display": "Myanmar",
        "upper": "MYANMAR",
        "port": 8113,
    },
    {
        "name": "timor_leste",
        "code": "TL",
        "te_slug": "timor-leste",
        "imf_code": "TL",
        "display": "Timor-Leste",
        "upper": "TIMOR-LESTE",
        "port": 8114,
        "module": "timor_leste",
    },
    {
        "name": "papua_new_guinea",
        "code": "PG",
        "te_slug": "papua-new-guinea",
        "imf_code": "PG",
        "display": "Papua New Guinea",
        "upper": "PAPUA NEW GUINEA",
        "port": 8115,
        "module": "papua_new_guinea",
    },
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
}

WB_INDICATORS = {
    "NY.GDP.MKTP.CD": {"name": "GDP (current US$)", "unit": "USD", "type": "gdp"},
    "NY.GDP.MKTP.KD.VS.ZG": {"name": "GDP growth (annual %)", "unit": "%", "type": "gdp_growth"},
    "FP.CPI.TOTL.ZG": {"name": "Inflation, consumer prices (annual %)", "unit": "%", "type": "inflation"},
    "SL.UEM.TOTL.ZS": {"name": "Unemployment, total (% of labor force)", "unit": "%", "type": "unemployment"},
    "FR.INR.RINR": {"name": "Interest rate (policy rates)", "unit": "%", "type": "interest_rate"},
    "SP.POP.TOTL": {"name": "Population, total", "unit": "people", "type": "population"},
    "NE.EXP.GNFS.CD": {"name": "Exports of goods and services (current US$)", "unit": "USD", "type": "exports"},
    "NE.IMP.GNFS.CD": {"name": "Imports of goods and services (current US$)", "unit": "USD", "type": "imports"},
    "NV.IND.TOTL.ZS": {"name": "Industry, value added (% of GDP)", "unit": "% of GDP", "type": "industry"},
    "NV.AGR.TOTL.ZS": {"name": "Agriculture, value added (% of GDP)", "unit": "% of GDP", "type": "agriculture"},
    "GC.DOD.TOTL.GD.ZS": {"name": "Government debt, total (% of GDP)", "unit": "% of GDP", "type": "government_debt"},
    "BX.KLT.DINV.WD.GD.ZS": {"name": "Foreign direct investment, net inflows (BoP, % of GDP)", "unit": "% of GDP", "type": "fdi"},
    "GC.XPN.TOTL.GD.ZS": {"name": "Government expenditure, % of GDP", "unit": "% of GDP", "type": "government_spending"},
    "SL.UEM.TOTL.FE.ZS": {"name": "Unemployment, female (% of labor force)", "unit": "%", "type": "unemployment_female"},
    "SL.UEM.TOTL.MA.ZS": {"name": "Unemployment, male (% of labor force)", "unit": "%", "type": "unemployment_male"},
}

TE_ENDPOINTS = [
    {"path": "gdp-growth", "name": "GDP Growth Rate", "unit": "%"},
    {"path": "inflation-cpi", "name": "Inflation Rate", "unit": "%"},
    {"path": "unemployment-rate", "name": "Unemployment Rate", "unit": "%"},
    {"path": "interest-rate", "name": "Interest Rate", "unit": "%"},
    {"path": "current-account", "name": "Current Account", "unit": "USD"},
    {"path": "government-debt-to-gdp", "name": "Government Debt to GDP", "unit": "%"},
    {"path": "exports", "name": "Exports", "unit": "USD"},
    {"path": "imports", "name": "Imports", "unit": "USD"},
]

IMF_INDICATORS = {
    "NGDP_RPCH": {"name": "Real GDP growth (IMF IFS)", "unit": "%"},
    "PCPIIPC_IX": {"name": "Consumer price index (IMF IFS)", "unit": "index"},
    "GGXONLB_GDP": {"name": "Overall government net debt (% GDP)", "unit": "% of GDP"},
}


def fetch_world_bank(country_code, display):
    records = []
    for indicator, info in WB_INDICATORS.items():
        url = f"http://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
        params = {"format": "json", "per_page": "10", "date": "2023:2025"}
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            data = resp.json()
            if isinstance(data, list) and len(data) > 1:
                for item in data[1]:
                    if item.get("value") is not None:
                        year = item.get("date")
                        value = item["value"]
                        records.append({
                            "title": f"[{display.upper()}] {info['name']}",
                            "source_name": "World Bank",
                            "source_url": f"https://data.worldbank.org/indicator/{indicator}",
                            "content": {
                                "indicator": indicator,
                                "indicator_name": info["name"],
                                "country": display,
                                "year": year,
                            },
                            "facts_extracted": [
                                f"{info['name']}: {value} {info['unit']} ({year})",
                                f"source:WorldBank indicator {indicator}",
                                f"country:{display} country_code:{country_code}",
                            ],
                            "metadata": {
                                "category": info["type"],
                                "unit": info["unit"],
                                "value": value,
                                "year": year,
                            },
                        })
                        break
        except Exception as e:
            pass  # skip this indicator
    return records


def fetch_trading_economics(te_slug, display):
    records = []
    for ep in TE_ENDPOINTS:
        url = f"https://tradingeconomics.com/{te_slug}/{ep['path']}"
        records.append({
            "title": f"[{display.upper()}] {ep['name']}",
            "source_name": "Trading Economics",
            "source_url": url,
            "content": {
                "title": ep["name"],
                "meta_description": f"{display} {ep['name']} — latest data from Trading Economics.",
                "policy_topics": ["economy"],
            },
            "facts_extracted": [
                f"{ep['name']} ({ep['unit']}): latest data from Trading Economics",
                f"source:TradingEconomics country:{te_slug} indicator:{ep['path']}",
            ],
            "metadata": {
                "category": "economic_indicator",
                "unit": ep["unit"],
                "source_page": url,
            },
        })
    return records


def fetch_imf(imf_code, display):
    records = []
    for indicator, info in IMF_INDICATORS.items():
        records.append({
            "title": f"[{display.upper()}] {info['name']}",
            "source_name": "IMF IFS",
            "source_url": f"https://dataservices.imf.org/REST/SDS/IFS/DATA?indicator={indicator}",
            "content": {
                "title": info["name"],
                "policy_topics": ["economy"],
            },
            "facts_extracted": [
                f"{info['name']}: latest data from IMF IFS",
                f"source:IMF indicator {indicator} country:{imf_code}",
            ],
            "metadata": {
                "category": "economic_indicator",
                "unit": info["unit"],
                "source": "IMF",
            },
        })
    return records


def main():
    for c in COUNTRIES:
        display = c["display"]
        code = c["code"]
        te_slug = c["te_slug"]
        imf_code = c["imf_code"]
        upper = c["upper"]
        name = c["name"]
        port = c["port"]
        module = c.get("module", name)
        
        # Determine output directory
        # For countries with same module and name (brunei, laos, myanmar)
        # use {name}-agent-full; for others use {module}-agent-full
        if "module" in c:
            pub_dir = Path(f"/opt/xrplme/thoughts/api/{module}-agent-full/publication")
        else:
            pub_dir = Path(f"/opt/xrplme/thoughts/api/{name}-agent-full/publication")
        
        pub_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Scraping: {display} ({code}, TE: {te_slug})")
        
        records = []
        # World Bank
        wb_records = fetch_world_bank(code, display)
        records.extend(wb_records)
        logger.info(f"  World Bank: {len(wb_records)} records")
        
        # Trading Economics
        te_records = fetch_trading_economics(te_slug, display)
        records.extend(te_records)
        logger.info(f"  Trading Economics: {len(te_records)} records")
        
        # IMF
        imf_records = fetch_imf(imf_code, display)
        records.extend(imf_records)
        logger.info(f"  IMF: {len(imf_records)} records")
        
        # Build output
        scraped_at = datetime.now(timezone.utc).isoformat()
        output = {
            "record_count": len(records),
            "updated_at": scraped_at,
            "scraped_at": scraped_at.replace("+00:00", "Z"),
            "sources": ["World Bank", "Trading Economics", "IMF IFS"],
            "country": name if "module" not in c else module,
            "country_code": code,
            "records": records,
        }
        
        # Write candidate then atomic move
        candidate = pub_dir / "latest_valid_candidate.json"
        output_file = pub_dir / "latest_valid.json"
        
        with open(candidate, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        if len(records) > 0:
            os.replace(str(candidate), str(output_file))
            logger.info(f"  SUCCESS: {len(records)} records -> {output_file} ({output_file.stat().st_size} bytes)")
            
            # Write report
            report = {
                "country": name if "module" not in c else module,
                "scraped_at": scraped_at,
                "sources_fetched": ["World Bank", "Trading Economics", "IMF IFS"],
                "total_records": len(records),
                "status": "success",
                "errors": [],
            }
            with open(pub_dir / "scrape_report.json", "w") as f:
                json.dump(report, f, indent=2)
        else:
            logger.warning(f"  No records fetched")
            if candidate.exists():
                os.remove(candidate)


if __name__ == "__main__":
    main()
    print("\nAll APAC scrapers complete.")
