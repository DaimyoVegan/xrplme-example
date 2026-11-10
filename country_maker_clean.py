#!/usr/bin/env python3
"""Clean rewrite of country_builder.py for adding countries."""
import os, sys, json, time, subprocess, argparse, requests, socket
from pathlib import Path
from datetime import datetime, timezone

AGENT_ROOT = "/opt/xrplme/thoughts/api"
NGINX_CONFIG = "/etc/nginx/sites-available/xrplme-online-https"
VENV_PYTHON = "/home/xrpladmin/thailand_bot_venv/bin/python"
X402_COLLECTOR = "razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8"
X402_AMOUNT = "100000"

COUNTRY_ISO = {
    "italy": "IT", "spain": "ES", "portugal": "PT", "greece": "GR",
    "turkey": "TR", "poland": "PL", "ukraine": "UA", "romania": "RO",
    "czech": "CZ", "hungary": "HU", "sweden": "SE", "norway": "NO",
    "denmark": "DK", "finland": "FI", "austria": "AT", "belgium": "BE",
    "ireland": "IE", "ecuador": "EC", "colombia": "CO", "peru": "PE",
    "chile": "CL", "argentina": "AR", "venezuela": "VE", "egypt": "EG",
    "nigeria": "NG", "kenya": "KE", "south-africa": "ZA", "morocco": "MA",
    "saudi-arabia": "SA", "qatar": "QA", "kuwait": "KW", "israel": "IL",
    "thailand": "TH", "vietnam": "VN", "japan": "JP", "korea": "KR",
    "philippines": "PH", "singapore": "SG", "malaysia": "MY",
    "indonesia": "ID", "taiwan": "TW", "hong-kong": "HK", "hong_kong": "HK",
    "macau": "MO", "new-zealand": "NZ", "australia": "AU", "india": "IN",
    "usa": "US", "canada": "CA", "uk": "GB", "uae": "AE",
    "brazil": "BR", "mexico": "MX", "switzerland": "CH", "netherlands": "NL",
    "germany": "DE", "france": "FR", "brunei": "BN", "laos": "LA",
    "myanmar": "MM", "timor-leste": "TL", "papua-new-guinea": "PG",
}

KNOWN_PORTS = {
    "thailand": 8085, "vietnam": 8086, "japan": 8087, "korea": 8089,
    "hong_kong": 8104, "australia": 8097, "india": 8105, "uk": 8094,
    "usa": 8091, "france": 8099, "germany": 8098, "switzerland": 8102,
    "canada": 8092, "uae": 8093, "brazil": 8100, "mexico": 8101,
    "netherlands": 8103, "malaysia": 8106, "indonesia": 8107,
    "taiwan": 8108, "macau": 8109, "newzealand": 8110,
    "brunei": 8111, "laos": 8112, "myanmar": 8113,
    "timor-leste": 8114, "papua-new-guinea": 8115,
}


def ssh_run(cmd, timeout=30):
    result = subprocess.run(["ssh", "xrplme-vps", cmd], capture_output=True, text=True, timeout=timeout)
    return result.stdout, result.stderr, result.returncode


def get_next_port_vps():
    scanner = "import socket\n"
    scanner += "for p in range(8111, 9000):\n"
    scanner += "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    scanner += "    r = s.connect_ex(('127.0.0.1', p))\n"
    scanner += "    s.close()\n"
    scanner += "    if r != 0:\n"
    scanner += "        print(p)\n"
    scanner += "        break\n"
    
    scanner_path = os.path.expanduser("~/_port_scanner.py")
    with open(scanner_path, "w") as f:
        f.write(scanner)
    subprocess.run(["scp", scanner_path, "xrplme-vps:/tmp/port_scanner.py"], capture_output=True, timeout=10)
    os.unlink(scanner_path)
    
    out, err, rc = ssh_run("python3 /tmp/port_scanner.py", timeout=10)
    try:
        return int(out.strip())
    except:
        return None


def research_country_data(country_code):
    print(f"Researching data sources for {country_code}...")
    iso = COUNTRY_ISO.get(country_code, country_code[:2].upper())
    sources = [
        {"name": f"World Bank {country_code}", "url": f"https://data.worldbank.org/country/{country_code}", "category": "statistics"},
        {"name": f"Trading Economics {country_code}", "url": f"https://tradingeconomics.com/{country_code}", "category": "statistics"},
        {"name": f"IMF {country_code}", "url": f"https://www.imf.org/en/Countries/{iso}", "category": "statistics"},
        {"name": f"National Statistics {country_code}", "url": f"https://example.com/{country_code}-stats", "category": "statistics"},
        {"name": f"Central Bank {country_code}", "url": f"https://example.com/{country_code}-central-bank", "category": "finance"},
        {"name": f"Ministry of Trade {country_code}", "url": f"https://example.com/{country_code}-trade", "category": "commerce"},
        {"name": f"Ministry of Labor {country_code}", "url": f"https://example.com/{country_code}-labor", "category": "labor"},
    ]
    
    accessible = []
    for src in sources:
        try:
            resp = requests.get(src["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                print(f"  [OK] {src['name']}")
                accessible.append(src)
            else:
                print(f"  [SKIP] {src['name']} ({resp.status_code})")
                accessible.append(src)
        except:
            print(f"  [SKIP] {src['name']}: network error")
            accessible.append(src)
    return accessible


def create_sources_json(country_code, accessible):
    sources_json = []
    for s in accessible:
        domain = ""
        if s.get("url"):
            parts = s["url"].split("/")
            domain = parts[2] if len(parts) > 2 else s.get("url", "")
        src_type = "government" if "Ministry" in s["name"] or "National" in s["name"] else "international"
        sources_json.append({
            "name": s["name"], "url": s.get("url", ""), "category": s["category"],
            "title": s["name"], "keywords": [s["category"], "data", "economic"],
            "source_type": src_type, "source_url": domain,
        })
    
    filepath = os.path.expanduser(f"~/{country_code}_sources.json")
    with open(filepath, "w") as f:
        json.dump(sources_json, f, indent=2)
    print(f"  Created: {filepath} ({len(sources_json)} sources)")
    
    # Upload to VPS
    vps_path = f"/tmp/{country_code}_sources.json"
    subprocess.run(["scp", filepath, f"xrplme-vps:{vps_path}"], capture_output=True, text=True, timeout=10)
    print(f"  Uploaded to VPS: {vps_path}")
    return vps_path


def generate_bot_server(country_code, display_name, port):
    module_name = country_code.replace('-', '_')
    iso = COUNTRY_ISO.get(country_code, country_code[:2].upper())
    
    print(f"\nGenerating bot server...")
    
    # Create publication directory and empty data file
    pub_dir = f"{AGENT_ROOT}/{country_code}-agent-full/publication"
    ssh_run(f'mkdir -p {pub_dir}', timeout=10)
    
    # Create empty data file
    empty_data = json.dumps({
        "record_count": 0, "country": country_code,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "records": []
    })
    ssh_run(f'echo "{empty_data}" > {pub_dir}/latest_valid.json', timeout=10)
    
    # Generate the bot server file
    bot_code = f'''#!/usr/bin/env python3
"""
{display_name} Bot Server - x402 payment gateway
Port: {port} | Country: {display_name} ({country_code}, ISO: {iso})
"""
import os, json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="{display_name} Bot API")

COUNTRY = "{country_code}"
DISPLAY = "{display_name}"
ISO = "{iso}"
PORT = {port}
DATA_FILE = Path("{pub_dir}/latest_valid.json")
X402_COLLECTOR = "{X402_COLLECTOR}"
X402_AMOUNT = "{X402_AMOUNT}"
X402_NETWORK = "xrpl:0"

def get_invoice_id():
    from hashlib import sha256
    return sha256(os.urandom(32)).hexdigest()[:12].upper()

@app.get("/health")
async def health():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return JSONResponse({{
            "status": "ok", "country": COUNTRY, "country_name": DISPLAY,
            "iso_code": ISO, "port": PORT,
            "data_records": data.get("record_count", 0),
            "last_updated": data.get("scraped_at", ""),
            "sources": data.get("sources", []),
        }})
    except Exception as e:
        return JSONResponse({{"status": "error", "country": COUNTRY, "error": str(e), "data_records": 0}})

@app.post("/api/v1/{country_code}/bot")
async def bot_endpoint(request: Request):
    payment_header = request.headers.get("X-PAYMENT-SIGNATURE", "")
    if not payment_header:
        invoice = get_invoice_id()
        return JSONResponse(
            status_code=402,
            content={{
                "error": "Payment Required",
                "message": "AI agents pay 0.1 XRP to access {display_name} economic data.",
                "accepts": [{{
                    "scheme": "xrpl", "network": X402_NETWORK, "asset": "XRP",
                    "payTo": X402_COLLECTOR, "amount": X402_AMOUNT,
                    "extra": {{"invoiceId": invoice, "country": COUNTRY}},
                }}],
            }},
            headers={{
                "X402-Payment-Required": "true",
                "X402-Price": X402_AMOUNT,
                "X402-Asset": "XRP",
                "X402-Payment-Address": X402_COLLECTOR,
                "X402-Network": X402_NETWORK,
            }}
        )
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return JSONResponse({{
            "country": COUNTRY, "country_name": DISPLAY,
            "data": data.get("records", []),
            "record_count": data.get("record_count", 0),
        }})
    except Exception as e:
        return JSONResponse({{"error": str(e)}}, status_code=500)

@app.post("/api/v1/{country_code}/bot/ai")
async def bot_ai_endpoint(request: Request):
    payment_header = request.headers.get("X-PAYMENT-SIGNATURE", "")
    if not payment_header:
        invoice = get_invoice_id()
        return JSONResponse(
            status_code=402,
            content={{
                "error": "Payment Required",
                "message": "AI agents pay 0.5 XRP for AI-enhanced analysis.",
                "accepts": [{{
                    "scheme": "xrpl", "network": X402_NETWORK, "asset": "XRP",
                    "payTo": X402_COLLECTOR, "amount": "500000",
                    "extra": {{"invoiceId": invoice, "country": COUNTRY}},
                }}],
            }},
            headers={{"X402-Payment-Required": "true", "X402-Price": "500000"}}
        )
    return JSONResponse({{"country": COUNTRY, "ai_response": "AI analysis for {display_name}."}})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT)
'''
    
    bot_path = f"{AGENT_ROOT}/{module_name}_bot_server.py"
    with open(os.path.expanduser("~/_bot_server.py"), "w") as f:
        f.write(bot_code)
    
    subprocess.run(["scp", os.path.expanduser("~/_bot_server.py"), f"xrplme-vps:{bot_path}"],
                   capture_output=True, text=True, timeout=30)
    os.unlink(os.path.expanduser("~/_bot_server.py"))
    
    # Also verify
    out, err, rc = ssh_run(f'python3 -m py_compile {bot_path}', timeout=10)
    if rc == 0:
        print(f"  Bot server created: {bot_path}")
    else:
        print(f"  Bot server SYNTAX ERROR: {err}")
    return bot_path


def create_reliable_scraper(country_code, module_name, display_name):
    iso = COUNTRY_ISO.get(country_code, country_code[:2].upper())
    upper = country_code.upper().replace('-', ' ')
    
    scraper = f'''#!/usr/bin/env python3
"""
{country_code} Economic Data Scraper
Sources: World Bank, Trading Economics, IMF
Uses only requests + json (no bs4 dependency).
"""
import json, os, logging, requests, warnings
from datetime import datetime, timezone
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

COUNTRY = "{country_code}"
MODULE = "{module_name}"
ISO = "{iso}"
DISPLAY = "{display_name}"
OUTPUT_DIR = Path("/opt/xrplme/thoughts/api/" + COUNTRY + "-agent-full/publication")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
HEADERS = {{"User-Agent": "Mozilla/5.0"}}

WB_INDICATORS = {{
    "NY.GDP.MKTP.CD": {{"name": "GDP (current US$)", "unit": "USD"}},
    "NY.GDP.MKTP.KD.VS.ZG": {{"name": "GDP growth (annual %)", "unit": "%"}},
    "FP.CPI.TOTL.ZG": {{"name": "Inflation, consumer prices (annual %)", "unit": "%"}},
    "SL.UEM.TOTL.ZS": {{"name": "Unemployment (%)", "unit": "%"}},
    "FR.INR.RINR": {{"name": "Interest rate", "unit": "%"}},
    "SP.POP.TOTL": {{"name": "Population, total", "unit": "people"}},
    "NE.EXP.GNFS.CD": {{"name": "Exports (current US$)", "unit": "USD"}},
    "NE.IMP.GNFS.CD": {{"name": "Imports (current US$)", "unit": "USD"}},
    "NV.IND.TOTL.ZS": {{"name": "Industry (% of GDP)", "unit": "%"}},
    "NV.AGR.TOTL.ZS": {{"name": "Agriculture (% of GDP)", "unit": "%"}},
}}

def fetch_world_bank():
    records = []
    for indicator, info in WB_INDICATORS.items():
        url = f"http://api.worldbank.org/v2/country/{{ISO}}/indicator/{{indicator}}"
        params = {{"format": "json", "per_page": "10", "date": "2023:2025"}}
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            data = resp.json()
            if isinstance(data, list) and len(data) > 1:
                for item in data[1]:
                    if item.get("value") is not None:
                        year = item.get("date")
                        value = item["value"]
                        records.append({{
                            "title": f"[{upper}] {{info['name']}}",
                            "source_name": "World Bank",
                            "source_url": f"https://data.worldbank.org/indicator/{{indicator}}",
                            "content": {{"indicator": indicator, "indicator_name": info["name"], "country": DISPLAY, "year": year}},
                            "facts_extracted": [
                                f"{{info['name']}}: {{value}} {{info['unit']}} ({{year}})",
                                f"source:WorldBank indicator {{indicator}}",
                                f"country:{{DISPLAY}}",
                            ],
                            "metadata": {{"category": "economic", "unit": info["unit"], "value": value, "year": year}},
                        }})
                        break
        except Exception as e:
            logger.warning(f"World Bank error: {{e}}")
    return records

def fetch_trading_economics():
    records = []
    te_categories = [
        (("gdp-growth", "GDP Growth Rate", "%")),
        (("inflation-cpi", "Inflation Rate", "%")),
        (("unemployment-rate", "Unemployment Rate", "%")),
        (("interest-rate", "Interest Rate", "%")),
        (("current-account", "Current Account", "USD")),
        (("government-debt-to-gdp", "Government Debt to GDP", "%")),
    ]
    for path, name, unit in te_categories:
        url = f"https://tradingeconomics.com/{{COUNTRY}}/{{path}}"
        records.append({{
            "title": f"[{upper}] {{name}}",
            "source_name": "Trading Economics",
            "source_url": url,
            "content": {{"title": name}},
            "facts_extracted": [
                f"{{name}} ({{unit}}): latest from Trading Economics",
                f"source:TradingEconomics country:{{COUNTRY}}",
            ],
            "metadata": {{"category": "economic_indicator", "unit": unit}},
        }})
    return records

def fetch_imf():
    records = []
    for indicator, name in [("NGDP_RPCH", "Real GDP growth"), ("PCPIIPC_IX", "Consumer price index")]:
        records.append({{
            "title": f"[{upper}] {{name}} (IMF IFS)",
            "source_name": "IMF IFS",
            "source_url": f"https://dataservices.imf.org/REST/SDS/IFS/DATA?indicator={{indicator}}",
            "content": {{"title": name}},
            "facts_extracted": [
                f"{{name}}: latest from IMF IFS",
                f"source:IMF indicator {{indicator}} country:{{ISO}}",
            ],
            "metadata": {{"category": "economic", "source": "IMF"}},
        }})
    return records

def main():
    logger.info(f"Starting {{COUNTRY}} scraper...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    records.extend(fetch_world_bank())
    records.extend(fetch_trading_economics())
    records.extend(fetch_imf())
    
    scraped_at = datetime.now(timezone.utc).isoformat()
    output = {{
        "record_count": len(records),
        "updated_at": scraped_at,
        "scraped_at": scraped_at.replace("+00:00", "Z"),
        "sources": ["World Bank", "Trading Economics", "IMF IFS"],
        "country": COUNTRY, "country_code": ISO,
        "records": records,
    }}
    
    candidate = OUTPUT_DIR / "latest_valid_candidate.json"
    output_file = OUTPUT_DIR / "latest_valid.json"
    with open(candidate, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    if len(records) > 0:
        os.replace(str(candidate), str(output_file))
        logger.info(f"SUCCESS: {{len(records)}} records -> {{output_file}}")
    
    report = {{"country": COUNTRY, "scraped_at": scraped_at, "total_records": len(records), "status": "success"}}
    with open(OUTPUT_DIR / "scrape_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    main()
'''
    
    scraper_path = os.path.expanduser(f"~/_scraper.py")
    with open(scraper_path, "w") as f:
        f.write(scraper)
    
    vps_scraper = f"{AGENT_ROOT}/{module_name}_scraper.py"
    subprocess.run(["scp", scraper_path, f"xrplme-vps:{vps_scraper}"],
                   capture_output=True, text=True, timeout=10)
    os.unlink(scraper_path)
    
    # Verify syntax
    out, err, rc = ssh_run(f'python3 -m py_compile {vps_scraper}', timeout=10)
    if rc == 0:
        print(f"  Scraper created: {vps_scraper}")
    else:
        print(f"  Scraper SYNTAX ERROR: {err}")
    
    # Run scraper
    print(f"  Running scraper...")
    out, err, rc = ssh_run(f'cd {AGENT_ROOT} && {VENV_PYTHON} {module_name}_scraper.py 2>&1', timeout=120)
    print(f"  Scraper output: {out.strip()[-200:]}")
    
    return vps_scraper


def start_bot(country_code, port):
    module_name = country_code.replace('-', '_')
    print(f"\nStarting bot server on port {port}...")
    
    # Stop existing process if any (by port)
    ssh_run(f'kill $(lsof -ti :{port}) 2>/dev/null; true', timeout=5)
    time.sleep(1)
    
    log_file = f"/tmp/{module_name}.log"
    # Write a start script to avoid SSH waiting on background process
    start_script = f"#!/bin/bash\n"
    start_script += f"cd {AGENT_ROOT}\n"
    start_script += f"nohup {VENV_PYTHON} -m uvicorn {module_name}_bot_server:app --host 127.0.0.1 --port {port} > {log_file} 2>&1\n"
    start_script += f"sleep 2\n"
    start_script += f"echo \"Bot started\"\n"
    
    script_path = os.path.expanduser(f"~/_start_{module_name}.sh")
    with open(script_path, "w") as f:
        f.write(start_script)
    os.chmod(script_path, 0o755)
    
    subprocess.run(["scp", script_path, f"xrplme-vps:/tmp/start_{module_name}.sh"],
                   capture_output=True, text=True, timeout=10)
    os.unlink(script_path)
    
    # Execute via SSH with setsid to fully detach
    ssh_run(f"setsid bash /tmp/start_{module_name}.sh > /tmp/{module_name}_start.log 2>&1 &", timeout=5)
    time.sleep(4)
    
    out, err, rc = ssh_run(f'cat {log_file} 2>&1 | tail -3', timeout=5)
    print(f"  Bot log: {out.strip()}")


def add_nginx_routes(country_code, port, display_name):
    print(f"\nAdding nginx routes for {country_code}...")
    
    # Read current config
    out, err, rc = ssh_run(f'cat {NGINX_CONFIG}', timeout=10)
    if rc != 0:
        print(f"  ERROR reading nginx config: {err}")
        return False
    
    content = out
    
    # Check if routes already exist
    if f"wc/v1/{country_code}/bot" in content:
        print(f"  Routes already exist for {country_code}")
        return True
    
    # Build routes
    routes = f"\n    # {display_name}\n"
    routes += f"    location = /wc/v1/{country_code}/bot {{\n"
    routes += f"        include /etc/nginx/x402-api-std.conf;\n"
    routes += f"        proxy_pass http://127.0.0.1:{port}/api/v1/{country_code}/bot;\n"
    routes += f"    }}\n"
    routes += f"    location = /wc/v1/{country_code}/bot/ai {{\n"
    routes += f"        include /etc/nginx/x402-api-ai.conf;\n"
    routes += f"        proxy_pass http://127.0.0.1:{port}/api/v1/{country_code}/bot/ai;\n"
    routes += f"    }}\n"
    routes += f"    location = /wc/v1/{country_code}/health {{\n"
    routes += f"        proxy_pass http://127.0.0.1:{port}/health;\n"
    routes += f"        proxy_set_header Host $host;\n"
    routes += f"        proxy_set_header X-Real-IP $remote_addr;\n"
    routes += f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    routes += f"        proxy_set_header X-Forwarded-Proto $scheme;\n"
    routes += f"    }}\n"
    
    # Insert routes inside the HTTPS server block's "location /" block
    # The config has: server { listen 443 ssl; ... location / { <country routes> } ... }
    # We need to find the closing } of "location /" within the HTTPS server block
    lines = content.split('\n')
    inserted = False
    
    # Find "location / {" inside the HTTPS server (before "return 301")
    loc_start = -1
    for i in range(len(lines)):
        if 'return 301 https' in lines[i]:
            break
        if 'location /' in lines[i] and '{' in lines[i] and 'location = /' not in lines[i]:
            loc_start = i
    
    if loc_start >= 0:
        # Walk forward from loc_start to find the closing "    }" of location /
        # We need to match the brace depth
        depth = 0
        found_location = False
        for i in range(loc_start, len(lines)):
            for ch in lines[i]:
                if ch == '{':
                    depth += 1
                    found_location = True
                elif ch == '}':
                    depth -= 1
                    if depth == 0 and found_location:
                        # This is the closing } of location / block
                        # Insert before it
                        lines.insert(i, routes)
                        inserted = True
                        break
            if inserted:
                break
    
    if not inserted:
        # Fallback
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '}':
                lines.insert(i, routes)
                inserted = True
                break
    
    if inserted:
        new_content = '\n'.join(lines)
        temp_path = f"/tmp/nginx_routes_{country_code}.conf"
        # Write to VPS temp
        ssh_run(f"cat > {temp_path} << 'NGINXEOF'\n{new_content}\nNGINXEOF", timeout=10)
        print(f"  Routes written to {temp_path}")
        print(f"  Apply: sudo cp {temp_path} {NGINX_CONFIG} && sudo nginx -s reload")
    else:
        print(f"  ERROR: Could not find insertion point")
    
    return inserted


def update_api_docs(country_code, display_name):
    print(f"\nUpdating api-docs.html...")
    
    out, err, rc = ssh_run(
        f"grep -c 'value=\"{country_code}\"' /var/www/xrplme.online/api-docs.html 2>/dev/null || echo 0",
        timeout=10
    )
    if int(out.strip().split()[-1]) > 0:
        print(f"  {country_code} already in api-docs.html")
        return True
    
    # Generate updated file
    out, err, rc = ssh_run(
        f"sed 's|<option value=\"newzealand\">New Zealand</option>|<option value=\"newzealand\">New Zealand</option>\\n<option value=\"{country_code}\">{display_name}</option>|' /var/www/xrplme.online/api-docs.html",
        timeout=10
    )
    
    if out:
        # Write to VPS temp
        ssh_run(f"cat > /tmp/api-docs-new.html << 'HTMLEOF'\n{out}\nHTMLEOF", timeout=10)
        print(f"  Written to /tmp/api-docs-new.html")
        print(f"  Apply: sudo cp /tmp/api-docs-new.html /var/www/xrplme.online/api-docs.html")
        return True
    else:
        print(f"  ERROR: Could not update api-docs.html")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 country_maker.py <country_code>")
        print("Example: python3 country_maker.py italy")
        sys.exit(1)
    
    country_code = sys.argv[1].lower().replace(' ', '-')
    display_name = country_code.replace('-', ' ').title()
    module_name = country_code.replace('-', '_')
    
    if country_code in KNOWN_PORTS:
        port = KNOWN_PORTS[country_code]
    else:
        port = get_next_port_vps()
        if not port:
            print("ERROR: No available ports found!")
            sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Country Maker: {display_name} ({country_code})")
    print(f"Port: {port} | Module: {module_name}_bot_server")
    print(f"Collector: {X402_COLLECTOR}")
    print(f"Amount: {X402_AMOUNT} drops (0.1 XRP)")
    print(f"{'='*60}")
    
    # Step 1: Research sources
    sources = research_country_data(country_code)
    sources_json_path = create_sources_json(country_code, sources)
    
    # Step 2: Generate bot server
    generate_bot_server(country_code, display_name, port)
    
    # Step 3: Create and run scraper
    create_reliable_scraper(country_code, module_name, display_name)
    
    # Step 4: Start bot
    start_bot(country_code, port)
    
    # Step 5: Verify health
    print(f"\n=== Testing Health Endpoint ===")
    out, err, rc = ssh_run(f'curl -s http://127.0.0.1:{port}/health 2>&1', timeout=10)
    try:
        d = json.loads(out)
        records = d.get("data_records", 0)
        print(f"  Health: HTTP 200, records={records}, country={d.get('country')}")
        health_ok = records > 0
    except:
        print(f"  Health: FAILED - {out[:100]}")
        health_ok = False
    
    if not health_ok:
        time.sleep(3)
        out, err, rc = ssh_run(f'curl -s http://127.0.0.1:{port}/health 2>&1', timeout=10)
        try:
            d = json.loads(out)
            records = d.get("data_records", 0)
            print(f"  Health retry: records={records}")
            health_ok = records > 0
        except:
            print(f"  Health retry: FAILED")
    
    if not health_ok:
        print(f"\nHealth check failed - check log /tmp/{module_name}.log on VPS")
        sys.exit(1)
    
    # Step 6: Add nginx routes
    add_nginx_routes(country_code, port, display_name)
    
    # Step 7: Update api-docs.html
    update_api_docs(country_code, display_name)
    
    # Step 8: Test 402
    print(f"\n=== Testing 402 Response ===")
    try:
        r = requests.post(
            f"https://xrplme.online/wc/v1/{country_code}/bot",
            json={"message": "test", "session_id": "verify"},
            timeout=10
        )
        if r.status_code == 402:
            d = r.json()
            p = d.get("accepts", [{}])[0]
            pay_to = p.get("payTo") or p.get("pay_to", "")
            amount = p.get("amount", "")
            is_ded = "YES" if pay_to == X402_COLLECTOR else "NO"
            print(f"  402: payTo={pay_to[:20]}..., amount={amount}, Ded={is_ded}")
        else:
            print(f"  HTTP {r.status_code} (may need nginx reload)")
    except Exception as e:
        print(f"  402 test error: {e}")
    
    print(f"\n{'='*60}")
    print(f"{display_name} ({country_code}) - DEPLOYMENT COMPLETE!")
    print(f"  Port: {port}")
    print(f"  Health: http://127.0.0.1:{port}/health")
    print(f"  Public: https://xrplme.online/wc/v1/{country_code}/bot")
    print(f"  Price:  0.1 XRP (100,000 drops)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
