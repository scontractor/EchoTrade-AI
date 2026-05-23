# ADR 0004 — Local-only deployment (no cloud yet)

- **Status:** Accepted
- **Date:** 2026-05-23
- **Supersedes:** none (replaces a phantom "Vercel CD" ADR that
  `plan.md` referenced but was never written)

## Context

`plan.md` describes a Phase 0 in which the first deliverable is a
themed React shell deployed to Vercel with PR previews and auto-deploy
on merge. The team did not execute that sequence — we shipped a
working data product (full EDGAR ingestion + 5-tab terminal) on the
local machine, with no cloud deployment, no CI, and no preview
pipeline. This ADR is an honest record of the current state and
the conditions under which we would change it.

## Decision

Everything runs locally:

- Backend: `uvicorn app.main:app` on `localhost:8000`
- Frontend: `vite` dev server on `localhost:5173` (proxies `/api`
  to the backend)
- Persistence: SQLite file `echotrade.db` in the repo root
- LLM: Ollama on `localhost:11434`

There is no Dockerfile, no `.github/workflows/`, no Vercel project
linked. The repo is git-hosted on GitHub for backup and code review
only, not for CD.

## Consequences

**Positive**
- Zero hosting cost.
- No third-party signups required to run the project end-to-end.
- Iteration is instant — no deploy step between editing and seeing
  the result in the browser.
- Privacy-friendly: SEC data + AI inference never leave the device.

**Negative**
- Cannot share a working URL with a non-technical stakeholder.
  Anyone evaluating the product must clone the repo and run two
  servers and Ollama.
- No CI means regressions can land on `main` undetected. We have no
  tests today either, so this gap is real but not the bottleneck.
- The CSS-variable theming layer that `plan.md` Phase 0 specified
  was never built. The current dark theme is hardcoded in
  `tailwind.config.js`. Adding a light theme would now be a
  retrofit, exactly the scenario plan.md tried to prevent.

## Alternatives considered

- **Build the Phase 0 foundation first, as plan.md prescribed.**
  Would have meant no working product to show today. The team's
  implicit choice (correct or not) was to optimise for "real
  feature, no deploy" over "deployed scaffold, no feature." This
  ADR documents that choice rather than relitigating it.
- **Deploy the FastAPI backend to Fly.io / Cloud Run and the
  frontend to Vercel today.** Doable, but pulls in Postgres (see
  ADR 0002) because SQLite-on-ephemeral-disk doesn't survive
  restarts. Also needs an Ollama replacement since hosted Ollama
  isn't free — likely Groq's free tier. Two coupled changes for a
  feature (sharing a URL) we don't urgently need.

## Revisit trigger

Stand up cloud deployment when **any one** of:

1. A non-engineering stakeholder needs to evaluate the live product
   without running it locally.
2. We add user accounts or any feature that requires multi-user
   state (forces ADR 0002's Postgres migration anyway).
3. The codebase grows past a size where "no tests, no CI" stops
   being an acceptable risk — empirically, when a third contributor
   joins.

When that trigger fires, the work is: Postgres migration → Groq or
similar hosted LLM → containerise backend → Vercel frontend +
Fly.io/Cloud Run backend → minimal CI (lint + smoke test). Each of
those deserves its own ADR.

## Related files

- `plan.md` Phase 0 description (now out of date with reality —
  see plan.md update accompanying this ADR)
- `frontend/vite.config.ts` (only the dev-server proxy is configured)
- `pyproject.toml` (no deploy targets defined)
