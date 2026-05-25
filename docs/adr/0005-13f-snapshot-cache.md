# ADR 0005 — 13F snapshot cache: transparent read-through, keyed on accession_number

**Status:** Accepted

## Context

Every call to `/snapshot`, `/diff`, `/signals`, or `/clone` triggered
`get_two_latest_snapshots()`, which makes ~5 HTTP round-trips to SEC EDGAR
(submissions JSON + HTML index + infotable XML, for two filings). Response
times were 5–15 seconds per request and put avoidable load on SEC's servers.

13F filings are quarterly and immutable once accepted — the same filing never
changes. The slow part is fetching the infotable XML (the holdings data), not
discovering which filings exist.

## Decision

Add a `filing_snapshots` table to the existing `echotrade.db` SQLite database.
`EDGARClient.get_snapshot()` checks the cache by `accession_number` before
hitting SEC. On a miss it fetches as before and stores the result. On a hit it
reconstructs the `FilingSnapshot` from stored JSON and returns immediately.

`get_recent_filings()` is **not** cached — it's one fast request to SEC that
detects new quarterly filings. Only the slow infotable XML fetch is cached.

Key reasons for this design:
- **Accession numbers are immutable** — a cache hit is always correct, no TTL needed.
- **Transparent to callers** — no API surface change, no new routes required.
- **Mirrors the Form 4 pattern** — same DB, same SQLAlchemy setup, same `merge()` upsert.
- **Holdings stored as a JSON blob** — simple for our scale (a few hundred holdings per
  filing). Not queryable at field level, but we don't need that yet.

## Consequences

- First request per investor is still slow (cold cache, ~5–15s). Every subsequent
  request for the same filing period is <100ms.
- The `echotrade.db` file grows by ~50–200KB per cached filing (JSON-serialised holdings).
  At 10 investors × 2 filings each = ~20 rows — negligible.
- If SEC corrects a filing (rare — they issue a `/A` amendment with a new accession
  number), the old cached snapshot remains but new requests pick up the amendment
  naturally (it has a different accession number and lands as a cache miss).
- Future: if we ever need cross-investor holding queries ("who holds AAPL?") we would
  normalise into a proper `holdings` table. The JSON blob is the right call now.
