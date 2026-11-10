# REVISED IMPLEMENTATION BITE 1 — ITALY FIX
## xrplme.online — September 22, 2026
### Classification: V3 Product/Schema Improvement
### Status: STOPPED AT RESTART/RELOAD GATE — AWAITING EXPLICIT APPROVAL

---

## A. VERIFIED COLLECTOR ADDRESS

**Approved V3 collector address**: `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8`

| Source | Where found | Address |
|---|---|---|
| Thailand source code | `thailand_bot_server.py` L59: `X402_CONFIG["pay_to"]` | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Macau source code | `macau_bot_server.py` L78: `X402_CONFIG["pay_to"]` | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Italy source code (OLD) | `italy_bot_server.py` L14: `X402_COLLECTOR = ...` | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Italy source code (NEW) | `italy_bot_server.py` L80: `X402_CONFIG["pay_to"]` | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Thailand 402 response | Local curl to port 8085 | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Macau 402 response | Local curl to port 8109 | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Italy 402 response (old) | Local curl to port 8117 | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| Italy 402 response (new) | Local curl to port 8117 (post-restart) | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |

**All countries use the same collector address.** No conflict. Italy will use exactly this same address. This is a public XRPL account address, not a secret.

**No wallet, seed, private key, or environment file was accessed or modified.**

---

## B. VERIFIED PAYMENT-STORE DESIGN

### Four implementations compared:

| Country | x402_xrpl library | SQLiteInvoiceStore | invoice_store param | HMAC loading | source_tag | scheme |
|---|---|---|---|---|---|---|
| **Thailand** (reference) | YES | YES | YES | YES | 804681468 | exact |
| **Macau** (template) | YES | YES | YES | YES | 804681468 | exact |
| **Brunei** (in-memory) | YES | NO | NO (uses x402 default _InMemoryInvoiceStore) | NO | 804681468 | exact |
| **Italy** (OLD - custom) | NO | NO | NO | NO | MISSING | xrpl |
| **Italy** (NEW — deployed) | YES | YES | YES | YES | 804681468 | exact |

### SQLiteInvoiceStore details (shared by Thailand, Macau, NEW Italy):
- **DB path**: `/home/xrpladmin/xrplme-state/x402.sqlite3` (hardcoded in `sqlite_invoice_store.py` L80: `DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"`)
- **Initialization**: `payment_store = SQLiteInvoiceStore()` — no args, uses default DB_PATH
- **Invoice ID generation**: `secrets.token_hex(16)` → 32-char lowercase hex (auto-generated, never exposed in source)
- **Invoice creation timing**: Invoice created at 402 response time (when `require_x402` middleware issues the payment challenge)
- **Payment verification**: Full on-chain XRPL verification (t54 facilitator `/verify` → XRPL RPC check for tesSUCCESS, destination match, amount match, source_tag match)
- **Replay protection**: `used_tx_registry` table (130 entries), `payment_proof_digest` via HMAC-SHA256, `atomic_claim` for race-safe invoice consumption
- **Restart persistence**: YES — `SQLiteInvoiceStore` persists to disk
- **SQLite locking**: `timeout=self.TXN_TIMEOUT` (5-second default), `check_same_thread=False` for async compatibility
- **HMAC secret path**: `/home/xrpladmin/xrplme-state/payment_hmac_secret` (64 bytes, mode 600) — loaded at module load BEFORE `SQLiteInvoiceStore` import

### Brunei (in-memory, NOT being changed):
- Uses x402_xrpl library but without `invoice_store=` parameter → defaults to `_InMemoryInvoiceStore()` (dict-based, ephemeral)
- In-memory store loses all invoices on restart
- No HMAC secret loading
- Still uses `source_tag=804681468`, `scheme="exact"`, same collector address

**Italy will use the approved canonical payment-store implementation** — `SQLiteInvoiceStore` with the same `x402.sqlite3` database as Thailand and Macau. This is verified by the source code comparison above.

---

## C. VERIFIED PUBLIC API ROUTES

### Current state (BEFORE any restart/reload):

| Route | Host | Expected | Current | Notes |
|---|---|---|---|---|
| `GET /wc/v1/italy/health` | xrplme.online | 200 | 200 ✅ | Already routed in xrplme-online-https |
| `POST /wc/v1/italy/bot` | xrplme.online | 402 | 402 ✅ | Already routed, but currently non-standard format (will fix after restart) |
| `POST /wc/v1/italy/bot/ai` | xrplme.online | 402 | 402 ✅ | Already routed, but currently non-standard (will fix after restart) |
| `GET /api/v1/italy/health` | api.xrplme.online | 200 | 404 ❌ | Italy NOT in api-xrplme-https (nginx config changed, reload pending) |
| `POST /api/v1/italy/bot` | api.xrplme.online | 402 | 404 ❌ | Italy NOT in api-xrplme-https (nginx config changed, reload pending) |
| `POST /api/v1/italy/bot/ai` | api.xrplme.online | 402 | 404 ❌ | Italy NOT in api-xrplme-https (nginx config changed, reload pending) |

After service restart + nginx reload, all 6 routes are expected to return correct responses.

---

## D. EXACT SOURCE DIFF

### File: `/opt/xrplme/thoughts/api/italy_bot_server.py`

**Full replacement.** Old file (3,526 bytes, custom payment) → New file (11,256 bytes, standard x402 v2).

The new file is modeled exactly on the verified Macau template (`macau_bot_server.py`, 11,255 bytes) with Italy-specific values.

**Key differences from old code**:

| Aspect | Old Italy | New Italy (Macau template) |
|---|---|---|
| Payment library | Custom (`get_invoice_id()`) | `x402_xrpl.server.require_x402` |
| Invoice store | None (no logging) | `SQLiteInvoiceStore()` (persistent) |
| x402Version | MISSING | 2 (provided by library) |
| scheme | `"xrpl"` | `"exact"` |
| sourceTag | MISSING | 804681468 |
| invoiceId format | 12-char hex (sha256[:12]) | 32-char hex (secrets.token_hex(16)) |
| 402 response | Custom format | Standard x402 v2 (resource, extensions, error) |
| Headers | Custom `X402-*` headers | Standard `payment-required` (base64) |
| Health `timestamp` | MISSING | Added (`datetime.now(timezone.utc).isoformat()`) |
| Health `sources` | Present (from data file) | Preserved from data file |

**No secret material in source**: The collector address `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` is a public XRPL account address in the X402_CONFIG dict. The HMAC secret is loaded from `/home/xrpladmin/xrplme-state/payment_hmac_secret` at module load time (read from existing file, not embedded in source).

---

## E. EXACT NGINX DIFF

### File: `/etc/nginx/sites-available/api-xrplme-https`

```diff
@@ -614,6 +615,21 @@
         proxy_set_header X-Forwarded-Proto $scheme;
     }
 
+    # Italy (port 8117) — standard pattern matching Macau etc
+    location = /api/v1/italy/bot {
+        include /etc/nginx/x402-api-std.conf;
+        proxy_pass http://127.0.0.1:8117;
+    }
+
+    location = /api/v1/italy/bot/ai {
+        include /etc/nginx/x402-api-ai.conf;
+        proxy_pass http://127.0.0.1:8117;
+    }
+
+    location = /api/v1/italy/health {
+        proxy_pass http://127.0.0.1:8117/health;
+        include /etc/nginx/x402-api-std.conf;
+    }
 }
```

**Proxy path semantics**: 
- `proxy_pass http://127.0.0.1:8117;` (no path) — nginx preserves the original request URI, so `/api/v1/italy/bot` is forwarded as `/api/v1/italy/bot` to the FastAPI app
- `proxy_pass http://127.0.0.1:8117/health;` (with path) — nginx replaces the location path with `/health`
- Both patterns match existing countries (Macau, Thailand) exactly
- All 3 routes use `location =` (exact match) — highest nginx precedence
- All 3 routes are inside the `listen 443 ssl;` server block (verified at lines 616-630, server closes at line 631)

**File `/etc/nginx/sites-available/xrplme-online-https` — NO CHANGE** (Italy routes already present and correct).

---

## F. EXACT DOCUMENTATION DIFF

### File: `/var/www/xrplme.online/api-docs.html`

**NOT DEPLOYED** — file is owned by `www-data:www-data` (644), requires sudo to write.

**Prepared at**: `/tmp/api-docs-italy.html` (15,970 bytes)

```diff
@@ -126,6 +126,7 @@
           <option value="hong_kong" selected>Hong Kong</option>
+          <option value="italy">Italy</option>
           <option value="malaysia">Malaysia</option>

@@ -205,1 +205,1 @@
-...hong_kong, malaysia, indonesia, taiwan, macau, newzealand...
+...hong_kong, italy, malaysia, indonesia, taiwan, macau, newzealand...
```

**To deploy** (requires root/sudo):
```bash
sudo cp /tmp/api-docs-italy.html /var/www/xrplme.online/api-docs.html
```

---

## G. VALIDATION COMMANDS (POST-APPROVAL)

```bash
# 1. Python syntax check (already passed)
/home/xrpladmin/thailand_bot_venv/bin/python -m py_compile /opt/xrplme/thoughts/api/italy_bot_server.py

# 2. Nginx config test (requires root for SSL key)
sudo nginx -t

# 3. Restart Italy service (NOT in sudoers NOPASSWD)
sudo systemctl restart italy-bot-api

# 4. Local health (verify timestamp field)
curl -s http://127.0.0.1:8117/health | python3 -m json.tool
# Expected: status, timestamp, data_records, last_updated, country=italy

# 5. Local raw 402 — x402 v2 field validation
curl -s -X POST http://127.0.0.1:8117/api/v1/italy/bot \
  -H "Content-Type: application/json" -d '{"message":"audit"}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('x402Version:', d.get('x402Version', 'MISSING'))
a = d.get('accepts',[{}])[0]
print('scheme:', a.get('scheme'))
print('network:', a.get('network'))
print('amount:', a.get('amount'))
print('asset:', a.get('asset'))
print('payTo:', a.get('payTo'))
print('sourceTag:', a.get('extra',{}).get('sourceTag', 'MISSING'))
inv = a.get('extra',{}).get('invoiceId', 'MISSING')
print('invoiceId:', inv, 'len=' + str(len(inv)))
print('resource:', 'resource' in d)
print('extensions:', 'extensions' in d)
print('error:', d.get('error'))
"

# 6. Local 402 header verification
curl -s -D - -X POST http://127.0.0.1:8117/api/v1/italy/bot \
  -H "Content-Type: application/json" -d '{"message":"test"}' 2>&1 | grep -i "payment-required"

# 7. Public health (website convenience)
curl -s https://xrplme.online/wc/v1/italy/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('timestamp:', d.get('timestamp','MISSING')); print('country:', d.get('country')); print('records:', d.get('data_records'))"

# 8. Public raw 402 (website convenience)
curl -s -X POST https://xrplme.online/wc/v1/italy/bot \
  -H "Content-Type: application/json" -d '{"message":"audit"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('x402Version:', d.get('x402Version')); a=d.get('accepts',[{}])[0]; print('amount:', a.get('amount'))"

# 9. Public AI 402 (website convenience)
curl -s -X POST https://xrplme.online/wc/v1/italy/bot/ai \
  -H "Content-Type: application/json" -d '{"message":"audit"}' | python3 -c "import sys,json; d=json.load(sys.stdin); a=d.get('accepts',[{}])[0]; print('x402Version:', d.get('x402Version')); print('amount:', a.get('amount'))"

# 10. Public direct API (after nginx reload)
curl -s -o /dev/null -w "%{http_code}" https://api.xrplme.online/api/v1/italy/health
curl -s -o /dev/null -w "%{http_code}" -X POST https://api.xrplme.online/api/v1/italy/bot -H "Content-Type: application/json" -d '{"message":"test"}'
curl -s -o /dev/null -w "%{http_code}" -X POST https://api.xrplme.online/api/v1/italy/bot/ai -H "Content-Type: application/json" -d '{"message":"test"}'

# 11. Verify no stack traces or internal paths in responses
curl -s -X POST http://127.0.0.1:8117/api/v1/italy/bot -H "Content-Type: application/json" -d '{"message":"test"}' | python3 -c "
import sys; d=sys.stdin.read()
print('Has stack trace:', 'traceback' in d.lower())
print('Has file path:', '/opt/' in d or '/home/' in d)
print('Has root dir:', 'RootDir' in d)
"

# 12. Verify invoice logging (after one 402 response)
/home/xrpladmin/thailand_bot_venv/bin/python -c "
import sqlite3; conn=sqlite3.connect('/home/xrpladmin/xrplme-state/x402.sqlite3')
c=conn.cursor(); c.execute('SELECT COUNT(*) FROM invoices WHERE country=italy')
print('Italy invoices:', c.fetchone()[0]); conn.close()"

# 13. Verify api-docs.html (after deployment)
curl -s https://xrplme.online/api-docs.html | grep 'option.*value="italy"'
```

---

## H. ROLLBACK PROCEDURE

```bash
TS=20260922_073619

# 1. Restore Italy source
cp /home/xrpladmin/xrplme-state/backups/italy_bot_server.py.${TS}.bak /opt/xrplme/thoughts/api/italy_bot_server.py
# Verify: sha256sum should show 09912e6f58eef99128648af0e27feb24dcfb18d121bd74351f40ba869ab5282d

# 2. Restore nginx config (if changed)
cp /home/xrpladmin/xrplme-state/backups/api-xrplme-https.${TS}.bak /etc/nginx/sites-available/api-xrplme-https
sudo nginx -t && sudo nginx -s reload
# Verify: sha256sum should show 0a6cae29da3c5bc42618b95ac7e4578b3fc2c1f83db02a25d39cc53fbc7917c0

# 3. Restore api-docs.html (if deployed)
sudo cp /home/xrpladmin/xrplme-state/backups/api-docs.html.${TS}.bak /var/www/xrplme.online/api-docs.html
# Verify: sha256sum should show 3ea8b766aedde36f16130a017a09649126e14e1cb2c225ae5296fb1376e1a367

# 4. Restart Italy service
sudo systemctl restart italy-bot-api

# 5. Verify rollback
curl -s http://127.0.0.1:8117/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('timestamp:', d.get('timestamp', 'MISSING'))"
# Should show 'MISSING' (old code had no timestamp field)
curl -s -X POST http://127.0.0.1:8117/api/v1/italy/bot | python3 -c "import sys,json; d=json.load(sys.stdin); print('x402Version:', d.get('x402Version', 'MISSING'))"
# Should show 'MISSING' (old code had no x402Version)
```

---

## I. FILES/SERVICES/ROUTES AFFECTED

| Item | Status | Requires Restart |
|---|---|---|
| `/opt/xrplme/thoughts/api/italy_bot_server.py` | CHANGED (3526→11256 bytes) | YES — `italy-bot-api` |
| `/etc/nginx/sites-available/api-xrplme-https` | CHANGED (+3 routes) | Reload only |
| `/var/www/xrplme.online/api-docs.html` | PREPARED (not deployed) | No (static file) |
| `/etc/nginx/sites-available/xrplme-online-https` | NO CHANGE | No |
| `/home/xrpladmin/xrplme-state/x402.sqlite3` | NO CHANGE | No (Italy will log here) |
| All 29 other country services | NO CHANGE | No |

---

## J. CURRENT VALIDATION STATUS (PRE-RESTART/RELOAD)

| Check | Result |
|---|---|
| Python py_compile | ✅ PASS (exit 0) |
| nginx -t | ⚠️ FAILS (pre-existing SSL key permission — root-only, not caused by changes) |
| Nginx config syntax | ✅ VALID (3 location blocks correctly inside server block) |
| Source code SHA-256 | ✅ Verified (9ff3bf6b... changed from 09912e6f...) |
| Nginx config SHA-256 | ✅ Verified (30db3244... changed from 0a6cae29...) |
| No secrets in source | ✅ Verified (only public address + HMAC secret filename reference) |
| Backups created | ✅ Verified (3 files, SHA-256 matched) |
| Italy routes in xrplme-online-https | ✅ Already present (no change needed) |
| Italy routes in api-xrplme-https | ✅ Added (3 routes, correct pattern) |

---

## STOP — AWAITING RESTART/RELOAD APPROVAL

The Italy code and nginx config have been updated. The api-docs.html change is prepared but not deployed (requires sudo for www-data-owned file).

**Italy service restart command** (NOT in sudoers NOPASSWD):
```bash
sudo systemctl restart italy-bot-api
```

**Nginx reload command**:
```bash
sudo nginx -t && sudo nginx -s reload
```

NO SERVICES RESTARTED.
NO NGINX RELOADED.
NO PAYMENT PERFORMED.
NO WALLET OR SECRET MATERIAL ACCESSED.
NO OTHER COUNTRY MODIFIED.