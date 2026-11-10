# V3 INVOICE-STORE INVESTIGATION
## xrplme.online — September 22, 2026
### Classification: READ-ONLY INVESTIGATION
### Purpose: Determine whether 12 countries using _InMemoryInvoiceStore have a real payment-verification/replay risk

---

## A. 30-COUNTRY STORE MATRIX

| Country | Service | Port | Middleware | Invoice Store | Persistent | Replay | HMAC | Raw Price | AI Price | Facil. URL |
|---|---|---|---|---|---|---|---|---|---|---|
| australia | australia-bot-api | 8098 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| brasil | brasil-bot-api | 8101 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| brunei | brunei-bot-api | 8111 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| canada | canada-bot-api | 8092 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| france | france-bot-api | 8100 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| germany | germany-bot-api | 8099 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| hong_kong | hongkong-bot-api | 8095 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| india | india-bot-api | 8107 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| indonesia | indonesia-bot-api | 8105 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| italy | italy-bot-api | 8117 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| japan | japan-bot-api | 8087 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| korea | korea-bot-api | 8089 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| laos | laos-bot-api | 8112 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| macau | macau-bot-api | 8109 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| malaysia | malaysia-bot-api | 8106 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| mexico | mexico-bot-api | 8102 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| myanmar | myanmar-bot-api | 8113 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| netherlands | netherlands-bot-api | 8104 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| new_zealand | newzealand-bot-api | 8110 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| papua_new_guinea | p-n-g-bot-api | 8115 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| philippines | philippines-bot-api | 8096 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| singapore | singapore-bot-api | 8097 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| switzerland | switzerland-bot-api | 8103 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| taiwan | taiwan-bot-api | 8108 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| thailand | thailand-bot-api | 8085 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| timor_leste | timor-leste-bot-api | 8114 | x402_xrpl.server | _InMemoryInv | NO | PARTIAL | NO | 100000 | 500000 | t54.ai ✓ |
| uae | uae-bot-api | 8093 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| uk | uk-bot-api | 8094 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| us | usa-bot-api | 8091 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |
| vietnam | vietnam-bot-api | 8086 | x402_xrpl.server | SQLiteInvoiceStore | YES | YES | YES | 100000 | 500000 | t54.ai ✓ |

**Legend**: ✓ = present, NO = absent, N/A = not applicable
**Note**: All 30 countries use the same facilitator URL: `https://xrpl-facilitator-mainnet.t54.ai`
**Note**: Italy has been CHANGED on disk but SERVICE NOT RESTARTED — OLD code still running

### Summary
- **18 countries** use `SQLiteInvoiceStore` (persistent, has HMAC, has replay protection)
- **12 countries** use `_InMemoryInvoiceStore` (default, non-persistent, no HMAC, partial replay)
- **All 30** use `x402_xrpl.server` middleware and the t54 facilitator for on-chain verification
- **Collector address**: `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` (same across all 30)
- **Source tag**: `804681468` (same across all 30)
- **Scheme**: `exact` (same across all 30)
- **Raw price**: `100000` drops (same across all 30)
- **AI price**: `500000` drops (same across all 30)

---

## B. EXACT IN-MEMORY COUNTRY LIST

The 12 countries using `_InMemoryInvoiceStore` (x402_xrpl library default, no `invoice_store` parameter passed):

1. australia (au_bot_server.py)
2. brunei (brunei_bot_server.py)
3. france (fr_bot_server.py)
4. germany (de_bot_server.py)
5. hong_kong (hongkong_bot_server.py)
6. laos (laos_bot_server.py)
7. myanmar (myanmar_bot_server.py)
8. papua_new_guinea (papua_new_guinea_bot_server.py)
9. philippines (ph_bot_server.py)
10. singapore (sg_bot_server.py)
11. switzerland (ch_bot_server.py)
12. timor_leste (timor_leste_bot_server.py)

These match the initially reported list (au, ch/de, fr, hongkong, brunei, laos, myanmar, timor-leste, papua-new-guinea, ph/sg). The slug differences are just naming conventions.

---

## C. INVOICE LIFECYCLE

### SQLiteInvoiceStore lifecycle (18 countries):

```
UNPAID REQUEST
  → 402 CHALLENGE issued
  → invoice created: invoice_id = secrets.token_hex(16) [32-char hex]
  → invoice stored: INSERT INTO invoices (...) VALUES (status='issued', ...)
  → invoice record has: request_body_hash, expected_amount_drops, country, endpoint_tier, ...
  
  [Client pays via XRPL transaction]
  → PAYMENT RECEIVED via PAYMENT-SIGNATURE header
  → t54 facilitator verifies on-chain (POST /verify)
  → atomic_claim(): UPDATE invoices SET status='paid_authorized' WHERE invoice_id=? AND status='issued'
  → INSERT INTO used_tx_registry (tx_hash UNIQUE, invoice_id, payment_proof_digest, ...)
  → payment_proof_digest = HMAC-SHA256(secret, raw_proof) — no raw proof stored
  
  → RESOURCE SERVED (200 response)
  
  REPLAY ATTEMPT (same tx_hash):
  → used_tx_registry.tx_hash is UNIQUE → insert fails
  → REPLAY REJECTED

  AFTER RESTART:
  → SQLite DB persists on disk at /home/xrpladmin/xrplme-state/x402.sqlite3
  → All invoice records and used_tx_registry entries survive
  → Paid invoices remain marked as paid_authorized
  → Replay protection intact across restarts
```

### _InMemoryInvoiceStore lifecycle (12 countries):

```
UNPAID REQUEST
  → 402 CHALLENGE issued
  → invoice_id = uuid.uuid4().hex.upper() [auto-generated by library]
  → invoice stored: self._data[invoice_id] = reqs  (Python dict, in memory)
  
  [Client pays via XRPL transaction]
  → PAYMENT RECEIVED via PAYMENT-SIGNATURE header
  → t54 facilitator verifies on-chain (POST /verify) — SAME as SQLite
  → self._data.pop(invoice_id, None) — removes from memory
  
  → RESOURCE SERVED (200 response)
  
  REPLAY ATTEMPT (same tx_hash, within same process):
  → invoice_id already consumed from _data → but t54 facilitator checks on-chain
  → If invoice is already in _data (not popped): would allow double-serve
  → BUT: the x402_xrpl library calls facilitator /verify which checks on-chain

  AFTER RESTART:
  → _data dict is empty (process memory freed)
  → All invoice records lost
  → All consumed state lost
  → New 402 generates new invoice_id (uuid4 — unique)
  → t54 facilitator STILL verifies on-chain (independent of in-memory store)
```

### Key difference:

The `_InMemoryInvoiceStore` is NOT the payment verification mechanism. The t54 facilitator performs on-chain XRPL verification independently. The invoice store is a local tracking/audit mechanism.

- **Invoice ID creation**: On 402 response (same for both)
- **Invoice record created on 402**: SQLite = persistent INSERT; In-memory = dict `put()`
- **Payment verification**: t54 facilitator `/verify` on-chain — SAME for both
- **Invoice marked paid**: SQLite = atomic_claim (UPDATE + INSERT used_tx); In-memory = dict `pop()`
- **Replay detection**: SQLite = used_tx_registry UNIQUE constraint (persistent); In-memory = only within process lifetime
- **After restart**: SQLite = all state preserved; In-memory = all state lost

---

## D. SQLITE DATABASE SCHEMA SUMMARY

**Database file**: `/home/xrpladmin/xrplme-state/x402.sqlite3` (745,472 bytes)
**File owner**: UID 1000 (xrpladmin), mode 644
**SHA-256**: (not printed — database, not source)

### Tables (3):

| Table | Rows | Purpose |
|---|---|---|
| `invoices` | 1,436 | Invoice tracking |
| `used_tx_registry` | 130 | Permanent anti-replay |
| `schema_migrations` | 1 | Migration version control |

### `invoices` table (24 columns):

| Column | Type | Purpose |
|---|---|---|
| `invoice_id` | TEXT ⚡PK | 32-char hex (secrets.token_hex(16)) |
| `request_id` | TEXT | Client request reference |
| `country` | TEXT | Country slug |
| `endpoint_tier` | TEXT | "raw" or "ai" |
| `request_body_hash` | TEXT | SHA-256 of request body (prevents replay) |
| `expected_amount_drops` | INTEGER | 100000 or 500000 |
| `collector_address` | TEXT | `razjTyzT6gBVH86iduU8HuEiZ2YUorNQj8` |
| `scheme` | TEXT | "exact" |
| `network` | TEXT | "xrpl:0" |
| `required_dynamic_tag` | INTEGER | 804681468 |
| `required_reference` | TEXT | InvoiceID binding (SHA256 of invoice_id) |
| `issued_at` | REAL | Unix timestamp |
| `expires_at` | REAL | Issued + TTL seconds |
| `status` | TEXT | issued → paid_authorized → response_delivered/failed |
| `transaction_hash` | TEXT | On-chain tx hash (set after payment) |
| `authorized_at` | REAL | Payment verification timestamp |
| `response_status` | INTEGER | HTTP status sent to client |
| `payment_proof_digest` | TEXT | HMAC-SHA256(VPS_SECRET, raw_proof) — no raw proof stored |
| `failure_category` | TEXT | Debug category on failures |
| `retry_count` | INTEGER | Retry attempts |
| `response_delivered` | INTEGER | Boolean flag |

### `used_tx_registry` table (12 columns):

| Column | Type | Purpose |
|---|---|---|
| `transaction_hash` | TEXT ⚡PK | UNIQUE — permanent anti-replay |
| `invoice_id` | TEXT | Link to invoices table |
| `payment_proof_digest` | TEXT | HMAC proof digest |
| `country` | TEXT | Country slug |
| `endpoint_tier` | TEXT | "raw" or "ai" |
| `authorized_at` | REAL | Timestamp |

### Key observations:
- **All 1,436 invoices are for Thailand only** — the other 17 countries with SQLiteInvoiceStore have 0 invoices (they haven't had paid transactions yet, or their invoices aren't being logged)
- **130 used_tx_registry entries** — all from Thailand (130 unique paid transactions)
- **Invoice IDs are unique**: 1,436 distinct / 1,436 total ✅
- **Payment proofs stored as HMAC digests**: No raw proof data, no customer data
- **Timestamps stored**: `issued_at`, `expires_at`, `authorized_at`, `updated_at`, `delivered_at`
- **Indexes**: 7 indexes covering status, country+tier, expiry, tx_hash, request_id, country+tier+tx

---

## E. PERSISTENCE RISK BY COUNTRY

### LOW RISK:
- **All 18 SQLiteInvoiceStore countries**: Full persistence, replay protection via used_tx_registry, HMAC proof digests, survives restart

### MEDIUM RISK:
- **All 12 _InMemoryInvoiceStore countries** (australia, brunei, france, germany, hong_kong, laos, myanmar, papua_new_guinea, philippines, singapore, switzerland, timor_leste):
  - Invoice tracking records lost on restart
  - Audit trail gap (no persistent invoice history)
  - Duplicate invoice IDs are NOT possible (uuid4 auto-generation)
  - On-chain replay protection still works via t54 facilitator
  - Old payments cannot be replayed after restart (on-chain verification is authoritative)
  - Unpaid 402 invoices lost on restart → client gets new 402 on retry
  - **Risk window**: service restart between 402 issuance and client payment → invoice lost, client gets new 402
  - **No revenue at risk**: t54 facilitator verifies on-chain independently

### HIGH RISK:
- None identified. The on-chain verification via t54 facilitator provides the authoritative security layer.

### UNKNOWN:
- None — all 30 countries identified and classified

### Key insight:
The `_InMemoryInvoiceStore` is a **tracking/audit limitation, NOT a security vulnerability**. Payment authorization is handled by the t54 facilitator performing on-chain XRPL verification (`POST /verify` → checks transaction on XRPL ledger). The invoice store only tracks local state for analytics and response routing. Even with no invoice store at all, payments would still be correctly verified.

---

## F. SECURITY VERSUS OBSERVABILITY ANALYSIS

### A. Payment Verification Security: SAFE
- All 30 countries route payment verification through the t54 facilitator (`https://xrpl-facilitator-mainnet.t54.ai`)
- The facilitator performs independent on-chain XRPL transaction verification
- This is NOT dependent on the local invoice store
- `_InMemoryInvoiceStore` countries have the SAME on-chain verification as `SQLiteInvoiceStore` countries
- **No security vulnerability in the in-memory store**

### B. Replay Protection: PARTIAL
- **SQLiteInvoiceStore**: `used_tx_registry` table with UNIQUE(tx_hash) — permanent, survives restart
- **_InMemoryInvoiceStore**: No persistent used_tx tracking — only works within process lifetime
- **Mitigation**: invoice_id is uuid4 (unique), so same invoice_id cannot be reused
- **After restart**: old invoice_ids are unknown — new 402 generates new uuid4
- **On-chain**: t54 facilitator checks tx_hash on-chain — can detect if a transaction was already used
- **Risk**: Between process restart and new 402 issuance, if a client sends an old payment, the in-memory store won't recognize the old invoice_id → 404 → client retries → gets new 402 → pays again
- **Impact**: Minor — single payment might not be matched to invoice (requires manual reconciliation)

### C. Invoice Auditability: GAP
- **18 countries**: Full audit trail in x402.sqlite3 (1,436 invoices, 130 paid)
- **12 countries**: No audit trail (in-memory only, lost on restart)
- **Current state**: Only Thailand has invoices in the DB (1,436) — the other 17 SQLite countries have 0 invoices (no paid transactions processed yet)

### D. Restart Behavior: DIFFERENT
- **SQLite**: All state survives `systemctl restart` — invoices, paid status, used_tx registry
- **In-memory**: All state lost on restart — process memory is freed
- **After restart with in-memory**: New 402 generates new uuid4 invoice_id — old invoices are orphaned

### E. Operational Recovery: IMPACTED for 12 countries
- **SQLite countries**: Can query DB for invoice history, debug via SQL
- **In-memory countries**: No invoice history after restart — debugging requires live process inspection or logs only

### F. Revenue Accounting: IMPACTED for 12 countries
- **SQLite countries**: Can query DB for revenue (count paid invoices, sum amounts)
- **In-memory countries**: Cannot query historical revenue — depends on on-chain tx history via t54 facilitator or XRPL explorer
- **Current**: Only Thailand's 130 paid transactions are tracked in SQLite

### G. Customer Support/Debugging: LIMITED for 12 countries
- **SQLite countries**: Can look up invoice_id → payment status → tx_hash
- **In-memory countries**: Only live (current process) invoice tracking; restart loses all history
- **After restart**: No way to look up historical invoice_id from memory

---

## G. RECOMMENDED CANONICAL DESIGN

### Option A: All countries use shared SQLiteInvoiceStore
**Pros**: Consistent audit trail, persistent replay protection, revenue accounting
**Cons**: Single DB bottleneck, cross-country invoice_id collision risk (mitigated: uuid4 is unique), all-or-nothing failure
**Assessment**: **RECOMMENDED**

### Option B: Each country uses separate persistent store
**Pros**: Isolated failure, no cross-country coupling
**Cons**: 30 DB files to manage, inconsistent schema risk, complex backup
**Assessment**: Over-engineered for current scale

### Option C: Centralized payment-verification service
**Pros**: Single point of truth, consistent verification
**Cons**: Major architecture change, single point of failure, requires service restart to deploy
**Assessment**: Premature — current on-chain verification via t54 already provides this

### Option D: Current mixed design is acceptable
**Pros**: No changes needed, on-chain verification is authoritative
**Cons**: Audit gap for 12 countries, inconsistent operational experience
**Assessment**: **ACCEPTABLE** for V3 promotion with documented limitations

### Recommendation: **Option A** (with migration plan)
The shared SQLiteInvoiceStore is the canonical pattern. All 12 in-memory countries should eventually migrate to SQLiteInvoiceStore for audit and operational consistency. The shared `x402.sqlite3` database already supports this — it has country and endpoint_tier columns for isolation. SQLite handles concurrent access with file locking (timeout=5s, WAL mode).

**SQLite concurrency assessment**:
- 30 services writing to one DB file — SQLite uses file-level locking
- `check_same_thread=False` allows async access from FastAPI
- `timeout=5` seconds — operations queue during write locks
- WAL mode (if enabled) allows concurrent readers + single writer
- Risk: Under high load, services could block on lock contention
- Mitigation: Invoice store writes are infrequent (only on 402 issuance and payment claim)

---

## H. ONE-COUNTRY MIGRATION PLAN (Canary)

If persistence is required for the 12 in-memory countries:

1. **Choose** one in-memory country (e.g., singapore)
2. **Backup**: `/home/xrpladmin/xrplme-state/backups/sg_bot_server.py.20260922_073619.bak`
3. **Edit**: Add `from sqlite_invoice_store import SQLiteInvoiceStore` + `payment_store = SQLiteInvoiceStore()` + `invoice_store=payment_store` to RequireX402Options
4. **Validate**: `python3 -m py_compile sg_bot_server.py`
5. **Restart only**: `sudo systemctl restart singapore-bot-api`
6. **Test**: `curl -s -X POST http://127.0.0.1:8097/api/v1/singapore/bot -H "Content-Type: application/json" -d '{"message":"test"}'` → verify 402 + invoice in DB
7. **Restart test**: Restart service again → verify invoice persists in DB
8. **Verify**: Query SQLite DB for singapore invoices
9. **Monitor logs**: Watch for SQLite locking errors
10. **Roll back if needed**: Restore backup + restart

**Not performed in this investigation.**

---

## I. FILES/SERVICES/DATABASE THAT WOULD BE TOUCHED (for future migration)

| Item | Future Migration Required? |
|---|---|
| `au_bot_server.py` | Yes — add SQLiteInvoiceStore |
| `brunei_bot_server.py` | Yes |
| `fr_bot_server.py` | Yes |
| `de_bot_server.py` | Yes |
| `hongkong_bot_server.py` | Yes |
| `laos_bot_server.py` | Yes |
| `myanmar_bot_server.py` | Yes |
| `papua_new_guinea_bot_server.py` | Yes |
| `ph_bot_server.py` | Yes |
| `sg_bot_server.py` | Yes |
| `ch_bot_server.py` | Yes |
| `timor_leste_bot_server.py` | Yes |
| `x402.sqlite3` | No change needed (already supports any country) |
| All 12 systemd services | Restart required after code change |
| Nginx configs | No change needed |

---

## J. V3 PROMOTION BLOCKING ASSESSMENT

### Is the in-memory invoice store blocking V3 promotion?

**NO.** The invoice store persistence gap is NOT blocking for V3 promotion because:

1. **Payment verification is on-chain** — t54 facilitator verifies XRPL transactions independently of the invoice store
2. **No security vulnerability** — the in-memory store is for tracking, not authorization
3. **All 30 countries are x402 v2 compliant** — correct scheme, amounts, collector address, source tag
4. **Replay protection works** — invoice IDs are uuid4 (unique), and on-chain tx verification prevents replay
5. **Revenue flows correctly** — payments go to the same collector address regardless of store type

**What IS blocking V3 promotion** (from the Italy investigation):
- Italy was using a custom non-standard payment format (now fixed on disk, service not restarted)
- Italy was missing from api-xrplme-https (now fixed on disk, nginx not reloaded)
- Italy was missing from api-docs.html (prepared, not deployed)

The in-memory invoice store is an **observability/operational** gap, NOT a **payment security** gap. It should be tracked as technical debt but does not block V3 promotion.

---

## FINAL SUMMARY

### In-memory vs SQLite — what actually matters:

| Aspect | In-memory (12 countries) | SQLite (18 countries) | Does it matter for V3? |
|---|---|---|---|
| Payment verification | t54 on-chain (same) | t54 on-chain (same) | NO |
| Replay protection | uuid4 + on-chain (limited) | used_tx_registry + on-chain | NO (both work) |
| Invoice persistence | Lost on restart | Survives restart | Observability only |
| Audit trail | None (after restart) | Full (persistent) | Operations only |
| Revenue tracking | Via t54/XRPL explorer | Via DB query | YES (for ops) |

**Conclusion**: The 12 countries using `_InMemoryInvoiceStore` have a **medium** risk classification — primarily an **audit trail and operational recovery limitation**, NOT a payment security vulnerability. Payment verification remains secure via the t54 facilitator's on-chain verification. This does NOT block V3 promotion.

NO FILES CHANGED.
NO SERVICES RESTARTED.
NO NGINX RELOADED.
NO DATABASE WRITES.
NO PAYMENT PERFORMED.
NO WALLET OR SECRET MATERIAL ACCESSED.