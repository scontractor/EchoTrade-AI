# plan.md — Reconcile & solidify the existing app

> **Working spec for what we're doing NOW.** Replace this when the chunk ships.
> See `ROADMAP.md` for the full picture, `docs/architecture.md` for the live system,
> `CLAUDE.md` for how we work.

## Context (important — read first)
This is NOT a greenfield build. A working local app already exists: FastAPI backend
(SEC 13F + Form 4 pipelines, diff/clone/scorer), React/Vite frontend, SQLite, Ollama
for AI. The previous greenfield plan is obsolete. This chunk does the cleanup that
makes the existing app honest, solid, and slightly more shippable — chosen because
it's small, high-value, and good for learning the codebase.

## Outcomes (definition of done)

✅ **README fixed** — stale "Claude" references removed; Ollama / OpenAI-compatible
   framing in place.

✅ **Docs committed** — ADRs (`docs/adr/0001–0004`), `docs/architecture.md`,
   `ROADMAP.md`, and `plan.md` are all in the repo.

- [ ] **Ollama verified end-to-end:** confirm AI Signals actually returns results with
      a local model running; if it works, note the exact setup in README; if it
      doesn't, document what's needed. (Currently built-but-unverified.)
- [ ] **First tests exist:** add at least a happy-path + one-edge-case test for the
      diff engine and the Form 4 scorer (pure logic — easiest place to start, and the
      quality bar in CLAUDE.md asks for tests; there are none yet).
- [ ] **Honest UI:** label the mock ticker tape and status pills as demo/placeholder
      so the UI doesn't imply live data it doesn't have.

## Explicitly OUT of scope
- No auth, no Postgres migration, no deployment, no 13F caching yet — those are
  separate roadmap items. This chunk is correctness + honesty + first tests only.

## Suggested approach (Claude: explain as you go — I'm a PM learning this)
1. Verify Ollama end-to-end — this de-risks the headline AI feature.
2. Write the first tests on the pure-logic modules (diff, scorer). Explain what
   a test is and why these modules are the easiest, highest-value place to start.
3. UI honesty labels last (cosmetic but matters for trust).

## Open questions for me
- Is Ollama actually installed and running on your machine? (Decides whether step 2
  is "verify" or "set up first.")
- Any test framework preference, or should Claude pick the Python standard (pytest)
  and explain why?

## Per CLAUDE.md
Branch off main, commit incrementally, open a PR (don't merge it yourself), narrate
in tech + product lenses, teach me new concepts plainly, don't ask permission for
reversible actions but DO push back on direction. Write an ADR for any real decision;
update `docs/architecture.md` if a component or data flow changes.
