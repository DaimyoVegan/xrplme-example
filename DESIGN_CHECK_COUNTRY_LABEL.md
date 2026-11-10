# DESIGN CHECK: COUNTRY-LABEL FIX
## xrplme.online — September 22, 2026
### Classification: READ-ONLY DESIGN ANALYSIS

---

## 1. EXACT IMPLEMENTATION PATH

### How Option A Would Work (Optional Country Parameter)

**Problem**: The x402_xrpl library v0.3.3 calls `invoice_store.put(invoice_id, reqs, *, ttl_seconds)` — no country parameter. The `InvoiceStore` Protocol defines:

```python
async def put(self, invoice_id: str, reqs: Sequence[PaymentRequirements], *, ttl_seconds: int) -> None
```

**Solution**: Override `put()` in `SQLiteInvoiceStore` to accept an optional `country` parameter with a default:

```python
async def put(self, invoice_id: str, reqs, *, ttl_seconds: int = INVOICE_TTL_UNPAID,
              country: str = None) -> None:
    ...
    # In INSERT, replace hardcoded "thailand" with:
    country or "thailand"
```

**Compatibility**: The x402_xrpl library calls `put()` WITHOUT the `country` kwarg, so the default value is used. **The library remains compatible** — `country=None` means "fall back to legacy behavior" (hardcoded "thailand"). Old callers that don't pass country still work.

**But**: The library's `put()` call is `await invoice_store.put(invoice_id, reqs, ttl_seconds=options.invoice_ttl_seconds)` — it does NOT pass `country`. So the country would STILL be "thailand" unless the country server modifies the middleware call.

**Key constraint**: The x402_xrpl library does NOT pass country to `put()`. The `reqs` (PaymentRequirements list) does NOT contain a path or country field. The `path` field exists on `RequireX402Options` (L848 in fastapi.py), not on `PaymentRequirements`.

### How Country Can Be Injected

**Option A1 — Constructor parameter (RECOMMENDED)**:
```python
class SQLiteInvoiceStore:
    def __init__(self, db_path: str = None, country: str = None):
        self._country = country or "thailand"
    
    async def put(self, invoice_id, reqs, *, ttl_seconds=INVOICE_TTL_UNPAID):
        ...  # use self._country instead of "thailand"
```
Country servers would change:
```python
# From:
payment_store = SQLiteInvoiceStore()
# To:
payment_store = SQLiteInvoiceStore(country="italy")
```

**Option A2 — Override put() with country parameter**:
```python
async def put(self, invoice_id: str, reqs, *, ttl_seconds: int = ...,
              country: str = None) -> None:
    # But the library won't call it with country=...
```
**Problem**: The library calls `put(invoice_id, reqs, ttl_seconds=...)` — it won't pass `country`. So this doesn't help unless the library is patched.

**Option A3 — Monkey-patch / custom middleware wrapper**:
Insert a wrapper between the x402 middleware and the invoice store that injects country. This would require modifying the country bot server's middleware setup, not the shared library.

### Option B — Wrapper/Adapter (Viable)

```python
class CountryInvoiceStore(SQLiteInvoiceStore):
    def __init__(self, db_path=None, country="thailand"):
        super().__init__(db_path)
        self._country = country
    
    async def put(self, invoice_id, reqs, *, ttl_seconds=...):
        # Temporarily set country context
        old = SQLiteInvoiceStore._default_country
        SQLiteInvoiceStore._default_country = self._country
        try:
            await super().put(invoice_id, reqs, ttl_seconds=ttl_seconds)
        finally:
            SQLiteInvoiceStore._default_country = old
```

**Problem**: `SQLiteInvoiceStore.put()` hardcodes "thailand" directly in the INSERT SQL. A subclass would need to override `put()` entirely or patch the hardcoded value.

**Better approach**: Add a class-level or instance-level `_country` attribute that `put()` reads:
```python
class SQLiteInvoiceStore:
    def __init__(self, db_path=None, country=None):
        self._country = country
    
    async def put(self, invoice_id, reqs, *, ttl_seconds=...):
        ...
        country_label = self._country or "thailand"  # in INSERT
```

### Option C — Derive from Resource URL (Viable, no library changes)

The `reqs` parameter contains `PaymentRequirements` objects. These have an `extra` dict. We could check if the country bot server puts the country in `extra`:

Looking at the Italy X402_CONFIG:
```python
X402_CONFIG = {
    "pay_to": "...",
    "amount": "100000",
    "network": "xrpl:0",
    "asset": "XRP",
    "scheme": "exact",
    "facilitator_url": "https://xrpl-facilitator-mainnet.t54.ai",
    "description": "Italy policy data API access",
}
```

**No country field is in the config.** But we could add one:
```python
X402_CONFIG["extra"] = {"country": "italy"}
```

Then in `SQLiteInvoiceStore.put()`, extract from `reqs[0].extra["country"]`:
```python
country_label = "thailand"  # default
if reqs and hasattr(reqs[0], 'extra') and reqs[0].extra:
    country_label = reqs[0].extra.get("country", "thailand")
```

This approach requires NO library changes — just adding `extra={"country": "italy"}` to each country's X402_CONFIG. But it requires verifying that `extra` is actually passed through to `reqs`.

### Option D — Separate DB per country (Not recommended)

- 18 DB files (`italy.sqlite3`, `macau.sqlite3`, etc.)
- Each with its own schema
- No cross-country collision risk
- High operational complexity (18 backup strategies, 18 WAL files)
- **Not recommended** for current scale

### Option E — Leave unchanged (Acceptable)

The country label is reporting-only. Payment verification is on-chain via t54. All 30 countries are functional. This is acceptable technical debt.

---

## 2. FILES/CALLERS AFFECTED

### If Option A1 (constructor parameter) is chosen:

**One file to change**:
- `/opt/xrplme/thoughts/api/sqlite_invoice_store.py` — add `country` param to `__init__()` and `put()`, replace hardcoded `"thailand"`

**18 country server files to update** (change `SQLiteInvoiceStore()` → `SQLiteInvoiceStore(country="xxx")`):

| File | Country Param | Current Init |
|---|---|---|
| `thailand_bot_server.py` | country="thailand" | `SQLiteInvoiceStore()` |
| `macau_bot_server.py` | country="macau" | `SQLiteInvoiceStore()` |
| `italy_bot_server.py` | country="italy" | `SQLiteInvoiceStore()` |
| `japan_bot_server.py` | country="japan" | `SQLiteInvoiceStore()` |
| `korea_bot_server.py` | country="korea" | `SQLiteInvoiceStore()` |
| `vietnam_bot_server.py` | country="vietnam" | `SQLiteInvoiceStore()` |
| `usa_bot_server.py` | country="usa" | `SQLiteInvoiceStore()` |
| `canada_bot_server.py` | country="canada" | `SQLiteInvoiceStore()` |
| `uae_bot_server.py` | country="uae" | `SQLiteInvoiceStore()` |
| `uk_bot_server.py` | country="uk" | `SQLiteInvoiceStore()` |
| `india_bot_server.py` | country="india" | `SQLiteInvoiceStore()` |
| `indonesia_bot_server.py` | country="indonesia" | `SQLiteInvoiceStore()` |
| `malaysia_bot_server.py` | country="malaysia" | `SQLiteInvoiceStore()` |
| `mexico_bot_server.py` | country="mexico" | `SQLiteInvoiceStore()` |
| `netherlands_bot_server.py` | country="netherlands" | `SQLiteInvoiceStore()` |
| `newzealand_bot_server.py` | country="newzealand" | `SQLiteInvoiceStore()` |
| `taiwan_bot_server.py` | country="taiwan" | `SQLiteInvoiceStore()` |
| `brasil_bot_server.py` | country="brasil" | `SQLiteInvoiceStore()` |

**18 systemd services to restart** after code change.

### If Option C (derive from extra config) is chosen:

**One file to change**:
- `/opt/xrplme/thoughts/api/sqlite_invoice_store.py` — extract country from `reqs[0].extra.get("country")`

**18 country server files to update**:
- Add `extra={"country": "xxx"}` to each country's X402_CONFIG and AI_X402_CONFIG

### Shared configuration:
- **All 18 services** use `PYTHON_PATH=/opt/xrplme/thoughts/api` (shared module)
- **All 18 services** use the same DB file: `/home/xrpladmin/xrplme-state/x402.sqlite3`
- **DB file**: owner UID 1000 (xrpladmin), mode 644
- **SQLite locking**: WAL mode (`journal_mode=WAL`), `busy_timeout=5000ms`, `timeout=10s`
- **DB_PATH**: `SQLiteInvoiceStore.DB_PATH = "/home/xrpladmin/xrplme-state/x402.sqlite3"` (class-level constant)

---

## 3. COMPATIBILITY RISKS

| Risk | Assessment | Mitigation |
|---|---|---|
| Library doesn't pass country to put() | **YES** — x402_xrpl v0.3.3 calls `put(invoice_id, reqs, *, ttl_seconds)` without country | Use constructor parameter (Option A1) — country is set at service startup, not at call time |
| Async behavior changes | NO — `put()` remains `async def`, no await pattern changes | N/A |
| SQLite locking/concurrency | NO — only field value changes, not locking behavior | WAL mode already handles concurrent access |
| Invoice IDs | NO — still generated by x402_xrpl library (uuid4/hex) | Untouched |
| Replay protection | NO — `used_tx_registry.transaction_hash` UNIQUE constraint | Untouched |
| Request body hashes | NO — `request_body_hash` computed from reqs JSON | Untouched |
| Old callers compatible | YES if default param used (`country=None` → "thailand") | Default preserves existing behavior |
| Schema change required | NO — `country TEXT NOT NULL` column already exists | No ALTER TABLE needed |
| All 18 services need restart | YES — shared module change requires process restart | Canary first (Italy), then batch restart |

### Library compatibility verification:
The x402_xrpl v0.3.3 `InvoiceStore` Protocol defines `put(invoice_id, reqs, *, ttl_seconds)` — 3 parameters. If `SQLiteInvoiceStore.put()` adds `country=None` as an additional keyword parameter with a default, the library's call `put(invoice_id, reqs, ttl_seconds=...)` will still work (country gets default value).

**The library's Protocol is not enforced at runtime** (Python Protocols are structural, not enforced) — extra kwargs with defaults are ignored.

---

## 4. CANARY DESIGN

**Country**: `italy-bot-api` (already running new x402 v2 code, low traffic, isolated)

### Steps:

1. **Backup**: `cp /opt/xrplme/thoughts/api/sqlite_invoice_store.py /home/xrpladmin/xrplme-state/backups/sqlite_invoice_store.py.20260922_italy_canary.bak`

2. **Edit** `sqlite_invoice_store.py` only:
   - `__init__`: add `country: str = None` param → `self._country = country`
   - In `put()`: replace `"thailand"` with `self._country or "thailand"`

3. **Edit** `italy_bot_server.py` only:
   - Change `payment_store = SQLiteInvoiceStore()` → `payment_store = SQLiteInvoiceStore(country="italy")`

4. **Validate**: `python3 -m py_compile sqlite_invoice_store.py italy_bot_server.py`

5. **Restart only**: `sudo systemctl restart italy-bot-api`

6. **Test unpaid challenge**: `curl -X POST http://127.0.0.1:8117/api/v1/italy/bot ...` → 402

7. **Verify DB**: `SELECT country FROM invoices ORDER BY issued_at DESC LIMIT 1` → should show `italy`

8. **Verify old records**: `SELECT DISTINCT country FROM invoices` → should still show `thailand` (old records untouched)

9. **Monitor logs**: `tail -f /home/xrpladmin/logs/country-bots/requests.log | grep italy`

10. **Rollback**: Restore backup + restart `italy-bot-api`

### What if the library version changes?
If x402_xrpl is upgraded and the library starts passing `country`, the constructor parameter can be removed and the `put()` signature can accept it directly. The current approach is backward-compatible with both the current library and future versions.

---

## 5. ROLLBACK DESIGN

### For canary (Italy only):
```bash
# Restore shared module
cp /home/xrpladmin/xrplme-state/backups/sqlite_invoice_store.py.20260922_italy_canary.bak /opt/xrplme/thoughts/api/sqlite_invoice_store.py
# Restore Italy bot server
cp /home/xrpladmin/xrplme-state/backups/italy_bot_server.py.20260922_073619.bak /opt/xrplme/thoughts/api/italy_bot_server.py
# Restart
sudo systemctl restart italy-bot-api
# Verify
curl -s http://127.0.0.1:8117/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])"
```

### For full 18-country rollout:
```bash
# Restore shared module
cp /home/xrpladmin/xrplme-state/backups/sqlite_invoice_store.py.20260922_073619.bak /opt/xrplme/thoughts/api/sqlite_invoice_store.py
# Restart all 18 services (if they were updated)
sudo systemctl restart thailand-bot-api macau-bot-api italy-bot-api japan-bot-api ...
```

### Historical data:
No data migration needed. Old invoices remain labeled "thailand" — this is acceptable since:
1. The country label is for reporting only
2. Historical recovery can be done via log cross-reference (see below)
3. The invoice_id, transaction_hash, and request_body_hash remain correct

---

## 6. HISTORICAL DATA RECOVERY

### Via log cross-reference (Partially recoverable):

The request log at `/home/xrpladmin/logs/country-bots/requests.log` contains:
- **Format**: `timestamp|country_name|endpoint|method|http_status|ip|amount|has_pay_sig|hash|latency|resp_size`
- **Country name**: Field 2 (index 1) — correct country names (italy, macau, singapore, etc.)
- **Timestamps**: ISO 8601 format (e.g., `2026-09-22T09:13:34Z`)

**Recovery approach**:
1. For each invoice in `x402.sqlite3` with `country='thailand'` and `issued_at` timestamp
2. Convert `issued_at` (Unix epoch) to ISO 8601
3. Search logs for entries with matching timestamp and a country != "thailand"
4. If found, the invoice belongs to that country

**Reliability**: **PARTIAL**
- Log timestamps match invoice `issued_at` to within ~1 second (invoice is created in middleware before the log line is written)
- Not all invoice issuances generate log entries (only requests that pass through the logging middleware)
- Unpaid invoices that never resulted in a payment may not have corresponding log entries
- Paid invoices (in `used_tx_registry`) have `authorized_at` which can also be cross-referenced

**Classification**: Historical rows are **PARTIALLY RECOVERABLE** via log cross-reference. Any recovered country values should be labeled as **inferred** (not verified) in reports.

### Via request_body_hash (NOT recoverable):
- The hash is SHA-256 (one-way) — cannot extract path/country from it
- The PaymentRequirements object contains path in `extra`, but the hash doesn't reveal which specific path

### Via transaction_hash (NOT directly recoverable):
- On-chain transaction hashes can be queried on the XRPL ledger
- But the t54 facilitator doesn't store which country originated each payment
- The `sourceTag` (804681468) is the same for ALL countries — NOT country-specific

---

## 7. RECOMMENDED CANONICAL DESIGN

### Short term (before V4):
**Option A1 (constructor parameter)** is the safest:
- Minimal code change (2 lines in shared module + 1 line per country server)
- Full backward compatibility (default = "thailand" preserves existing behavior)
- No library changes required
- SQLite locking/async/uniqueness unaffected

### Long term (V4 schema work):
Consider **Option C (derive from X402_CONFIG.extra)** as a cleaner approach:
- Country is part of the payment requirements config
- No need for constructor parameters
- The x402_xrpl library will eventually support passing context through `extra`
- But requires verifying that `extra` is passed through to `reqs` in the library

### Historical data:
**Do NOT modify existing rows.** Create a reporting view or separate correction process that:
1. Cross-references invoice `issued_at` timestamps with log entries
2. Labels recovered country as `inferred_country` (not `country`)
3. Does NOT update the `country` column in the base table

---

## 8. TIMING RELATIVE TO V4

This fix should happen **BEFORE V4 schema work**:
- V4 may introduce new table structures or separate per-country stores
- Getting country labeling right now means V4 migration has clean source data
- The fix is small and low-risk (constructor parameter with default)
- Doing it after V4 would require V4-specific changes

However, if V4 plans to abandon the shared database entirely (Option D: separate DB per country), then the country label fix is unnecessary — each DB would have its own country implicitly.

**Recommendation**: Implement Option A1 as a quick fix now. Revisit during V4 planning to determine if the shared-DB-with-country-label pattern should be replaced with per-country stores.

DESIGN CHECK COMPLETE.
NO FILES CHANGED.
NO SERVICES RESTARTED.
NO NGINX RELOADED.
NO DATABASE WRITES.
NO PAYMENT PERFORMED.
NO WALLET OR SECRET MATERIAL ACCESSED.
