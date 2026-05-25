# ADR 0006 — Deployment: Vercel (frontend) + Railway (backend)

**Status:** Accepted
**Supersedes:** ADR 0004 (local-only deployment) — revisit trigger #1 fired:
a non-engineering stakeholder needs to evaluate the live product.

## Context

The app runs locally only (ADR 0004). Sharing it requires cloning the repo,
running two servers, and configuring Groq. The goal is a public read-only demo
reachable at a URL, with auto-deploy on every merge to `main`.

The frontend is a static Vite/React build. The backend is FastAPI + uvicorn.
Both have no auth and serve public SEC data only, so no user-data concerns.

## Decision

- **Frontend → Vercel.** Auto-detects Vite, deploys on push to `main`, free.
- **Backend → Railway.** Auto-detects Python from `pyproject.toml`, free tier
  (500 hrs/month). Start command in `Procfile`: `uvicorn app.main:app --host
  0.0.0.0 --port $PORT`.
- **API routing → Vercel rewrites.** `vercel.json` rewrites `/api/:path*` to the
  Railway URL. The frontend keeps its relative `/api/...` paths unchanged — zero
  frontend code changes. The browser sees one origin (Vercel domain), so no CORS
  configuration needed.

## SQLite on Railway

Railway's filesystem is ephemeral — wiped on every deploy. The SQLite DB starts
empty each time, which is acceptable for the read-only demo:
- **13F data:** re-fetches from SEC on first request per investor (5–15s cold,
  then fast via the in-memory cache within the same process lifetime).
- **Form 4 data:** always required an explicit `POST /insiders/ingest/{ticker}`
  anyway — no regression.

If persistence becomes necessary: Railway persistent volumes (straightforward)
or the Postgres migration from ADR 0002. Neither is needed for the demo.

## Env vars

Railway dashboard must have: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`
(the Groq settings — same as local `.env` Groq block).

Vercel needs no extra env vars (the rewrite is in `vercel.json`).

## CI/CD (free, automatic)

Both platforms auto-deploy on push to `main`. Every merged PR triggers a
production deploy — the CI/CD pipeline from the ROADMAP, at zero cost.
PR preview deployments are available on Vercel (frontend only).

## Consequences

- **Enables:** sharing a live URL with anyone; demonstrates the full product
  without local setup.
- **Limitation:** Railway cold start ~5s if the free-tier dyno has been idle.
  First 13F request per investor is additionally slow (SEC fetch). Acceptable
  for a demo.
- **Not included:** auth, rate-limiting, or any user-data protection — this is
  a public read-only demo. Add auth before any user-specific features (ADR 0002).
- **Future:** if Railway free tier is insufficient, Render or Fly.io are
  drop-in alternatives with the same Procfile/env-var pattern.
