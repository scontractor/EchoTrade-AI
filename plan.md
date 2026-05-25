# plan.md — chunk complete

> **This chunk shipped.** See `ROADMAP.md` for what's next.
> See `docs/architecture.md` for the live system, `CLAUDE.md` for how we work.

## What we just shipped (correctness + honesty chunk)

✅ README — stale "Claude/Anthropic" references removed; OSS/Ollama framing.
✅ Docs committed — ADRs (`docs/adr/0001–0004`), `docs/architecture.md`, `ROADMAP.md`.
✅ AI Signals verified end-to-end — Groq free tier (`llama-3.3-70b-versatile`),
   live against Berkshire and ARK Invest. 15 signals, executive summary, risk factors.
✅ Three code fixes — 502 error handling, stale Anthropic docstrings, JSON mode confirmed.
✅ First tests — 6 pytest cases for `_parse_response`, all passing.
✅ Honest UI labels — LIVE→DEMO, OLLAMA→AI, "DEMO PRICES" on ticker tape.

## Next — pick from ROADMAP.md

**A. 13F caching** (solid/learning-heavy)
Stop re-fetching SEC EDGAR on every request. Cache snapshots in SQLite —
Form 4 already does this; mirror the pattern. Big reliability + latency win,
good lesson in caching and persistence.

**B. Deployment** (shippable/shipping-heavy)
Frontend to Vercel, FastAPI to Railway/Render/Fly. Gets something publicly
reachable fast; teaches deployment and CI.

Spar in a side chat → distill into a new plan.md → branch → PR.
