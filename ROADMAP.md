# EchoTrade AI — Roadmap (current state + next)

> Reflects what's actually built. The detailed spec for the next chunk lives in
> `plan.md`. See `docs/adr/` for the *why* behind big calls, `docs/architecture.md`
> for the live system picture, and `CLAUDE.md` for how we work.

## North star
A StockUnlock-style smart money tracker: follow any fund or insider via SEC filings,
track your own portfolio against theirs, get notified on new filings, and surface
AI-generated signals — all with honest per-source data freshness.

## Guiding principles
- Honesty about data freshness is a feature (Form 4 ≈ 2 days/exact; 13D ≈ 5 days;
  13F/13G ≈ 45-day quarterly snapshots — diff-only, never timestamped to a real trade).
- The LLM interprets, never invents data.
- Open-source by default (see CLAUDE.md). SQLite now, Postgres at multi-user (ADR 0002).
- Goal balance: **learn engineering AND ship a usable product** — sequence below
  alternates "make it real/solid" (learning) with "make it shippable" (shipping).

---

## ✅ DONE (already built)
- SEC EDGAR 13F ingestion: fetch + parse holdings, CUSIP→ticker resolver.
- Diff engine (quarter-over-quarter) and clone allocator.
- Form 4 insider pipeline: parse + role/value-weighted scorer + cluster detection,
  persisted to SQLite.
- React/Vite terminal UI wired across all 5 tabs.
- FastAPI backend with 8 routes; OSS-LLM AI signals (per CLAUDE.md).
- Docs reconciled to reality: ADRs 0001–0005, architecture.md, ROADMAP committed.
- README drift fixed; `.env.example` documents Groq + Ollama options.
- **AI Signals verified end-to-end** — Groq free tier (`llama-3.3-70b-versatile`);
  502 error handling on unparseable model output; stale Anthropic docstrings removed.
- **First tests** — 9 pytest cases (`_parse_response` + `FilingCache`), all passing.
- **Honest UI labels** — DEMO/AI status pills, "DEMO PRICES" ticker tape prefix.
- **13F snapshot cache** — transparent read-through, keyed on accession_number,
  `filing_snapshots` table in `echotrade.db`. Repeat requests <100ms (ADR 0005).
- **Deployed** — FastAPI backend on Render, React frontend on Vercel with `/api/*`
  rewrites. Auto-deploys on merge to main (ADR 0006).
- **Real delayed prices** — ticker tape replaced with ~15-min delayed Yahoo Finance
  prices via yfinance. Refreshes every 60s; honest "DELAYED" label. 13/13 tests passing.

## NEXT

### Phase 1 — Auth foundation (active next chunk)
- **Supabase auth** — Google/GitHub login; JWT validation on protected FastAPI routes.
- **SQLite → Postgres** via Supabase (ADR 0002). User, watchlist, and portfolio tables.
- **Per-user watchlist** — save/remove investors; persisted per account.
- **Dynamic investor search** — search any 13F filer by name via SEC EDGAR search API;
  removes the hardcoded 4-investor limit.

### Phase 2 — Portfolio
- User enters holdings (ticker + shares + cost basis).
- Track current value via yfinance prices (already have the feed).
- Compare portfolio performance vs tracked investors.

### Phase 3 — Metrics & discovery
- **Stock metrics page** — P/E, market cap, revenue, earnings via yfinance fundamentals.
- **Investor metrics** — AUM over time, sector breakdown, concentration score.
- **Universal search bar** — stocks + investors from one input.
- **Filing notifications** — alert on new Form 4 / 13F filings for watched entities.

## Backlog
- Upgrade sentiment beyond TextBlob (e.g. finance-tuned open model).
- Consensus/crowding view, conflict detection, cost-basis & P&L, full clone workflow,
  per-fund concentration/sector breakdown.
- Backtesting vs investors (enter at filing date — no lookahead bias).
- LLM-as-a-judge to validate AI signal outputs.

---

## 🎓 Learning tracks (which work teaches which skill)

> I'm a PM learning engineering by building this. Maps roadmap items to the skill each
> teaches, so learning goals sit alongside build goals. When working a tagged item,
> Claude explains it in the relevant vocabulary as we go (see CLAUDE.md teaching mode).
> Tip: a `plan.md` chunk can add a one-line "Learning focus:" pointer back to here.

### ETL / data pipelines — *primary focus; already partly built*
- **Already in the code:** Extract = `edgar/client.py` (fetch SEC XML); Transform =
  `edgar/parser.py` + CUSIP→ticker resolver + X0202 unit normalization (ADR 0003);
  Load = `insiders/` persisting Form 4 to SQLite.
- **Already lived:** schema drift — ADR 0003 records 3 SEC source changes that broke
  the pipeline. The central real-world ETL lesson.
- **Already shipped:** 13F caching = the missing "Load" stage (ADR 0005, PR #3).
- **Next lessons (in order):** incremental/idempotent ingest (only fetch unseen
  filings) → scheduled ingestion (nightly job vs on-request) → data validation
  before load (would auto-catch the $263T bug).
- **Out of scope:** warehouse/orchestration ETL (dbt, Airflow, Spark). Same concepts,
  different tools — a separate future project if wanted.

### Deployment & CI/CD
- Read-only demo deploy (frontend → Vercel, FastAPI → Python host) teaches build/
  deploy, env config, the frontend/backend split (ADR 0004). Auto-deploy + PR previews
  teach CI/CD.

### Auth & security
- **Phase 1** (next): Supabase auth + SQLite→Postgres migration (ADR 0002) teaches
  OAuth (how "login with Google" works), JWTs (the token sent on every request),
  and closing an open API.
- **Phase 3**: Filing notifications teach webhooks and background job patterns.

### Testing
- Tests on pure-logic modules (diff engine, Form 4 scorer) teach test structure and
  happy-path vs edge cases. Threads through every chunk.

### LLM application engineering
- Signals verification + graceful fallback (shipped PR #1) taught structured-output
  prompting, OpenAI-compatible adapters, handling unreliable model output.
- LLM-as-a-judge (backlog) teaches eval/scoring of AI outputs.

---

## How to use this with plan.md
1. Pick the next item. 2. Spar in a side chat → distill into `plan.md`.
3. Hand `plan.md` to Claude Code in Plan Mode. 4. Branch → PR → review → merge.
5. Update this file + architecture.md; write an ADR if it was a real decision.
