# plan.md — chunk complete

> **This chunk shipped.** See `ROADMAP.md` for what's next.
> See `docs/architecture.md` for the live system, `CLAUDE.md` for how we work.

## What we just shipped (real delayed prices + deployment)

✅ `app/prices.py` — fetch_prices() calls yfinance for 18 symbols, returns
   [{sym, price, chg_pct}]. BRK.B mapped to BRK-B (Yahoo convention).
   Runs in a thread executor (same pattern as Form 4 routes).

✅ `GET /prices` route in `app/main.py` — confirmed returning live data.

✅ `frontend/src/components/TopBar.tsx` — fetches /api/prices on mount,
   refreshes every 60s, shows '---' gracefully on null, label: 'DELAYED'.

✅ Tests — 4 pytest cases for prices (happy path, null price, per-symbol
   failure isolation, total batch failure). 13/13 total passing.

✅ Deployed — FastAPI on Render (echotrade-ai.onrender.com), React on Vercel
   with /api/* rewrites to Render. Auto-deploys on merge to main.

## Next — pick from ROADMAP.md

**A. More tests** (solid-heavy)
Tests on diff engine and Form 4 scorer — the pure-logic modules that
have no test coverage yet. Teaches test structure and edge cases.

**B. Auth + Postgres** (multi-user trigger)
Supabase auth + SQLite → Postgres migration. Only makes sense once
there's something worth protecting behind a login.

Spar in a side chat → distill into a new plan.md → branch → PR.
