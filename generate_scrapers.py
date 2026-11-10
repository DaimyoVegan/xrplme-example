#!/usr/bin/env python3
"""Generate scrapers for Indonesia, Taiwan, Macau, New Zealand
based on the malaysia_scraper.py template."""

import os
os.chdir(os.path.expanduser("~/xrplme-example"))

with open("malaysia_scraper.py", "r") as f:
    template = f.read()

countries = [
    {
        "name": "indonesia",
        "code": "ID",
        "wb_code": "ID",
        "te_slug": "indonesia",
        "imf_code": "ID",
        "display": "Indonesia",
    },
    {
        "name": "taiwan",
        "code": "TW",
        "wb_code": "TW",
        "te_slug": "taiwan",
        "imf_code": "TW",
        "display": "Taiwan",
    },
    {
        "name": "macau",
        "code": "MO",
        "wb_code": "MO",
        "te_slug": "macao",
        "imf_code": "MO",
        "display": "Macau",
    },
    {
        "name": "newzealand",
        "code": "NZ",
        "wb_code": "NZ",
        "te_slug": "new-zealand",
        "imf_code": "NZ",
        "display": "New Zealand",
    },
]

for c in countries:
    content = template

    # Replace all malaysia-specific references
    content = content.replace("Malaysia", c["display"])
    content = content.replace("malaysia", c["name"])
    content = content.replace("MY", c["code"])
    content = content.replace("tradingeconomics.com/malaysia/", f"tradingeconomics.com/{c['te_slug']}/")
    content = content.replace("-agent-full/publication", f"/{c['name']}-agent-full/publication")

    # Fix the output dir path
    content = content.replace(
        f"/opt/xrplme/thoughts/api/{c['name']}-agent-full/publication/latest_valid.json",
        f"/opt/xrplme/thoughts/api/{c['name']}-agent-full/publication/latest_valid.json"
    )

    # Fix the scraper docstring
    content = content.replace(
        "Malaysia Economic Data Scraper",
        f"{c['display']} Economic Data Scraper"
    )
    content = content.replace(
        "Fetches economic indicators from World Bank, IMF, and Trading Economics APIs.\nSaves to /opt/xrplme/thoughts/api/malaysia-agent-full/publication/latest_valid.json",
        f"Fetches economic indicators from World Bank, IMF, and Trading Economics APIs.\nSaves to /opt/xrplme/thoughts/api/{c['name']}-agent-full/publication/latest_valid.json"
    )

    # Fix country code mapping
    content = content.replace(
        '"MY": "MY",',
        f'"{c["code"]}": "{c["wb_code"]}",'
    )

    # Fix the WB_COUNTRY assignment
    content = content.replace(
        f'WB_COUNTRY = {{\n    "{c["code"]}": "{c["wb_code"]}",\n}}.get(COUNTRY_CODE, "{c["code"]}")',
        f'WB_COUNTRY = "{c["wb_code"]}"'
    )

    # Fix TE_COUNTRY
    content = content.replace(
        'TE_COUNTRY = "malaysia"',
        f'TE_COUNTRY = "{c["te_slug"]}"'
    )

    # Fix IMF_COUNTRY
    content = content.replace(
        'IMF_COUNTRY = "MY"',
        f'IMF_COUNTRY = "{c["imf_code"]}"'
    )

    # Fix COUNTRY_CODE default
    content = content.replace(
        'COUNTRY_CODE = "MY"',
        f'COUNTRY_CODE = "{c["code"]}"'
    )

    # Fix the output dir path in the scraper
    content = content.replace(
        f'OUTPUT_DIR = Path(f"/opt/xrplme/thoughts/api/{c["name"]}-agent-full/publication")',
        f'OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/{c["name"]}-agent-full/publication")'
    )

    # Fix the COUNTRY_CODE reference in COUNTRY_LABELS
    content = content.replace('country_code:MY', f'country_code:{c["code"]}')

    # Fix the "country:Malaysia" in facts_extracted
    content = content.replace('country:Malaysia', f'country:{c["display"]}')

    # Fix the Trading Economics URL in facts
    content = content.replace(
        f'source:TradingEconomics country:{c["te_slug"]}',
        f'source:TradingEconomics country:{c["te_slug"]}'
    )

    # Fix all "[MALAYSIA]" references
    content = content.replace("[MALAYSIA]", f"[{c['display'].upper()}]")

    # Fix "country:Malaysia" → "country:{display}"
    # Fix the f-strings that use country name
    content = content.replace(
        f'f"{{info[\\'name\\']}}: {{value}} {{info[\\'unit\\']}} ({{year}})"',
        f'f"{{info[\"name\"]}}: {{value}} {{info[\"unit\"]}} ({{year}})"'
    )

    # Fix the country code in WorldBank URL
    content = content.replace(
        f'f"https://data.worldbank.org/indicator/{{indicator}}"',
        f'f"https://data.worldbank.org/indicator/{{indicator}}"'
    )

    filename = f"{c['name']}_scraper.py"
    with open(filename, "w") as f:
        f.write(content)

    # Verify replacements were made
    with open(filename, "r") as f:
        verify = f.read()

    checks = [
        ("[MALAYSIA]" not in verify, "No MALAYSIA reference"),
        (f"{c['display']}" in verify, f"{c['display']} name present"),
        (f'"{c["code"]}"' in verify, f"Country code {c['code']} present"),
        (f'TE_COUNTRY = "{c["te_slug"]}"' in verify, f"TE slug: {c['te_slug']}"),
        (f'IMF_COUNTRY = "{c["imf_code"]}"' in verify, f"IMF code: {c['imf_code']}"),
    ]

    print(f"\n=== {filename} ===")
    for check_desc, check_result in checks:
        status = "OK" if check_result else "FAIL"
        print(f"  {status}: {check_desc}")

    print(f"  Size: {len(verify)} bytes")
    os.system(f"python3 -m py_compile {filename} && echo '  Syntax: OK' || echo '  Syntax: FAIL'")
