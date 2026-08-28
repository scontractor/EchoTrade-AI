# plan.md — chunk complete

> **This chunk shipped.** See `ROADMAP.md` for what's next.
> See `docs/architecture.md` for the live system, `CLAUDE.md` for how we work.

## What we just shipped (test coverage + a bug it caught)

✅ `tests/test_diff.py` — 6 tests on `compute_diff` / `clone_portfolio`
   (`app/portfolio/diff.py`): all 5 action types, the ±5% unchanged
   boundary, two divide-by-zero edge cases (zero previous shares, an
   investor's first-ever 13F), proportional allocation.

✅ `tests/test_scorer.py` — 7 tests on `score_trades`
   (`app/insiders/scorer.py`): no-trades placeholder, high-conviction
   officer buy, 10b5-1 plan sale flagged as noise, cluster detection,
   plus 2 regression tests added after the fix below.

✅ Bug found while testing, fixed same session — `conviction` was floored
   at 0.0 *before* the SELL/STRONG_SELL thresholds were checked, so
   heavy insider selling always resolved to NEUTRAL. Fixed by keeping
   `raw_score` signed for the direction decision and only taking the
   unsigned magnitude for the displayed `conviction_score`. No frontend
   change needed — `InsiderPanel.tsx` already had SELL/STRONG_SELL
   styling wired up, just unreachable.

✅ PR #6 (tests) + PR #7 (fix, stacked on #6) — both merged to main.
   26/26 tests passing.

## Next — pick from ROADMAP.md

**A. Phase 1 — Auth foundation** (the roadmap's "active next chunk")
Supabase auth (Google/GitHub login), SQLite → Postgres migration,
per-user watchlists, dynamic investor search. Architectural fork —
needs a plan + your "go" before any code per CLAUDE.md.

**B. Something else from the backlog**
See ROADMAP.md's Backlog section (sentiment upgrade, consensus/crowding
view, backtesting, LLM-as-a-judge).

Spar in a side chat → distill into a new plan.md → branch → PR.
