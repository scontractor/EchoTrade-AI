# ADR 0002 — SQLite for persistence now, Postgres deferred

- **Status:** Accepted
- **Date:** 2026-05-23
- **Supersedes:** none (replaces a phantom "Supabase + Postgres" ADR that
  `plan.md` referenced but was never written)

## Context

Only one feature in the current codebase needs persistence: the Form 4
insider-trade ingestion pipeline (`app/insiders/`) caches scraped
trades so subsequent reads don't re-hit SEC EDGAR. Everything else
(13F snapshots, diffs, clone allocations, AI signals) is computed
on the fly from a live SEC fetch + in-memory CUSIP→ticker map.

The original `plan.md` flagged Supabase (Auth + Postgres) as the
intended backend for a later phase. That phase never started — there
are no user accounts, no multi-tenant data, no need for a hosted
database today.

## Decision

Use **SQLAlchemy 2.0 + SQLite** with the database file `echotrade.db`
at the repo root for all current persistence. `app/insiders/models.py`
defines the engine via `get_engine("sqlite:///echotrade.db")`.

The file is gitignored (see ADR-equivalent change in `.gitignore`).
Schema changes are handled by `Base.metadata.create_all()` at startup
— no migration framework yet.

## Consequences

**Positive**
- Zero infrastructure to spin up. `pip install` and the DB exists.
- SQLAlchemy 2.0 means the eventual swap to Postgres is a connection
  string change, not a rewrite.
- Form 4 ingest stays local-fast: ~50ms reads vs the ~5-10s round trip
  to SEC EDGAR for a fresh ingest.

**Negative**
- Single-writer. The current backend is a single uvicorn process so
  this is fine, but any horizontal scaling would break.
- No migrations. Schema evolution requires a manual drop/rebuild
  today. Acceptable while data is disposable (re-ingestable from SEC).
- Not multi-user. There is no notion of "my saved investors" or
  "my clone history" because there is no user table.

## Alternatives considered

- **Supabase / Postgres now** — overkill. Adds a network dep, account
  signup, and a hosting cost (or container) before any feature
  actually needs them. The plan.md intent is preserved as a future
  step, not abandoned.
- **Pure in-memory cache** — would re-fetch every Form 4 on each
  uvicorn restart and re-ingest ~16 filings × ~1s = ~16s of latency
  on cold path. Worth a small SQLite file to avoid.
- **DuckDB** — interesting for analytical workloads but no advantage
  over SQLite for our current row-shaped insert/select pattern.

## Revisit trigger

Move to Postgres (Supabase or otherwise) when **any one** of these
becomes true:

1. We add user accounts — auth tokens / sessions need a real DB.
2. We deploy to a hosted environment with ephemeral filesystems
   (Vercel functions, Cloud Run, etc.) — SQLite-on-disk dies there.
3. Data we cannot afford to re-ingest enters the schema (user-saved
   portfolios, paid market data we've licensed, audit logs).

Until then, SQLite is the right boring choice.
