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


# 🎓 Learning tracks (which work teaches which skill)
 
> I'm a PM learning engineering by building this. This maps roadmap items to the
> skill each one teaches, so learning goals are visible alongside build goals.
> When working an item tagged here, Claude should explain it in the relevant
> vocabulary as we go (see CLAUDE.md teaching mode).
 
### ETL / data pipelines
*The most transferable skill here — and already partly built.*
- **Already learned (exists in code):** Extract = `edgar/client.py` (fetch SEC XML);
  Transform = `edgar/parser.py` + CUSIP→ticker resolver + X0202 unit normalization
  (ADR 0003); Load = `insiders/` persisting Form 4 to SQLite.
- **Already lived:** schema drift — ADR 0003 documents 3 SEC source changes that
  broke the pipeline. This is the central real-world ETL lesson.
- **Next ETL lessons (tag these as learning):**
  - **13F caching** = completing the missing "Load" stage (13F currently re-extracts
    every request; Form 4 already loads-and-reuses). Mirror the Form 4 pattern.
  - **Incremental / idempotent ingest** = only fetch filings not already stored,
    so re-runs don't duplicate or re-pull everything.
  - **Scheduled ingestion** = move extraction from on-request to a scheduled job
    (e.g. nightly pull of new filings) — classic production ETL shape.
  - **Data validation** = sanity-check transformed data before load (would have
    auto-caught the $263T bug).
- **Out of scope here:** warehouse/orchestration ETL (dbt, Airflow, Spark, Snowflake).
  Same concepts, different tools — a separate future project if wanted.
### Deployment & CI/CD
- **Read-only demo deploy** (frontend → Vercel, FastAPI → Python host) teaches
  build/deploy, environment config, and the frontend/backend split (ADR 0004).
- Adding auto-deploy-on-merge + PR previews teaches CI/CD pipelines.
### Auth & security
- **Supabase auth + SQLite→Postgres migration** (ADR 0002) teaches OAuth, sessions,
  2FA, and closing an open API — triggered when we add multi-user.
### Testing
- **First tests on pure-logic modules** (diff engine, Form 4 scorer) teach test
  structure, happy-path vs edge cases. Threads through every chunk going forward.
### LLM application engineering
- **Signals verification + graceful fallback** teaches structured-output prompting,
  OpenAI-compatible adapters, and handling unreliable model output.
- **LLM-as-a-judge** (backlog) teaches eval/scoring of AI outputs.