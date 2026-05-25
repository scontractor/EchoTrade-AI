# EchoTrade AI — Roadmap (current state + next)

> Reflects what's actually built. The detailed spec for the next chunk lives in
> `plan.md`. See `docs/decisions/` for the *why* behind big calls, `docs/architecture.md`
> for the live system picture, and `CLAUDE.md` for how we work.

## North star
A "smart money" tracker: follow funds, institutions, and insiders via SEC filings,
see what they buy/sell with honest per-source timeliness, get notified on filings you
care about, and backtest your own portfolio against theirs.

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
- FastAPI backend with 8 routes; Ollama-based AI signals (OSS, per CLAUDE.md).

## 🔧 IMMEDIATE — correctness & hygiene (do first; small, high-value, good learning)
- Fix README drift ("Claude" → "Ollama / OpenAI-compatible").
- Commit the docs (ADRs, architecture.md, ROADMAP) into the repo so they're real.
- **Verify Ollama end-to-end** — confirm AI Signals actually works, or document the
  setup step. (It's currently built-but-unverified.)
- Add a first test or two (the quality bar in CLAUDE.md asks for this; none exist yet).
- Make the mock TopBar honest: label prices "demo" until real ones land.

## NEXT — pick the order based on learn-vs-ship mood

### A. Make it solid (learning-heavy)
- **13F caching:** stop re-fetching SEC every request — cache snapshots (SQLite is
  fine). Form 4 already does this; mirror the pattern. Big quality + reliability win,
  and a great lesson in caching/persistence.
- Replace mock ticker tape with a **real (likely delayed) price feed** (Phase 2 idea).
  Label delayed vs live honestly.

### B. Make it shippable (shipping-heavy)
- **Deploy a read-only public demo** (no user data, so no auth needed yet) — frontend
  to Vercel, FastAPI to a Python host (Railway/Render/Fly). See ADR 0004. This gets
  something live fast and teaches deployment/CI.

### C. Then multi-user (the migration trigger)
- **Auth + accounts via Supabase** (Google/GitHub + email + 2FA) and migrate
  SQLite → Postgres (ADR 0002). Closes the open API. Unlocks per-user saved data.
- User portfolio + backtesting vs entities (enter at filing date — no lookahead bias).
- Bidirectional filing notifications (timely for Form 4/13D; quarterly-diff for 13F).

## Backlog
- Upgrade sentiment beyond TextBlob (e.g. finance-tuned model).
- Consensus/crowding view, conflict detection, cost-basis & P&L, full clone workflow,
  per-fund concentration/sector breakdown.
- LLM-as-a-judge to validate AI outputs.

---

## How to use this with plan.md
1. Pick the next item here. 2. Spar in a side chat → distill into `plan.md`.
3. Hand `plan.md` to Claude Code in Plan Mode. 4. Branch → PR → review → merge.
5. Update this file + architecture.md, write an ADR if it was a real decision.
