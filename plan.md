# plan.md — chunk complete

> **This chunk shipped.** See `ROADMAP.md` for what's next.
> See `docs/architecture.md` for the live system, `CLAUDE.md` for how we work.

## What we just shipped (13F snapshot cache)

✅ `app/edgar/cache.py` — FilingCache: SQLite read-through cache keyed on
   accession_number. get() returns a dict or None; put() is a safe upsert.
   Table: `filing_snapshots` in `echotrade.db` alongside `insider_trades`.

✅ `app/edgar/client.py` — cache wired into get_snapshot(): hit → instant return
   from DB; miss → fetch from SEC as before, then cache before returning.
   get_recent_filings() intentionally left uncached (detects new quarterly filings).

✅ Tests — 3 pytest cases: miss returns None, put→get round-trip, idempotent put.
   Full suite: 9/9 passing.

✅ ADR 0005 — records the decision, the JSON-blob trade-off, and the amendment
   edge case.

✅ architecture.md — EDGAR→SEC arrow, DB node, and Edgar→DB edge all updated.

## Result

First request per investor: ~5–15s (cold cache, fetches from SEC).
Repeat requests: <100ms (warm cache, reads from SQLite).

## Next — pick from ROADMAP.md

**A. Deployment** (shippable-heavy)
Frontend to Vercel, FastAPI to Railway/Render/Fly. Gets something publicly
reachable; teaches deployment and CI. See ADR 0004 for context.

**B. Real price feed** (solid-heavy)
Replace the static demo ticker tape with delayed prices (e.g. yfinance).
Removes the last "dishonest" element and teaches external data integration.

**C. Auth + Postgres** (multi-user trigger)
Supabase auth + SQLite → Postgres migration. Only makes sense once there's
something worth protecting behind a login.

Spar in a side chat → distill into a new plan.md → branch → PR.
