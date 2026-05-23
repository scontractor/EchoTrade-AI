# plan.md — Phase 0: Foundation & Continuous Deployment

> **Status note (2026-05-23):** This phase was *not* executed as written.
> The team shipped feature code (full SEC EDGAR ingestion + 5-tab React
> terminal) before the deploy/theming foundation described below.
> See `docs/adr/0004-local-only-deployment.md` for the explicit
> trade-off and the triggers that would justify backfilling Phase 0.
> The text below is preserved as the *original intent* — treat it as
> a backlog item, not a current spec.

> **Working spec for the phase we're building NOW.** When this phase ships, replace
> this file with the Phase 1 plan. See `CLAUDE.md` for how we work (plan mode,
> branching, narration, OSS-models rule).

## Why this phase first
Before any feature, we want a real app that is deployed, themeable, and continuously
shippable — so we never integrate deployment or theming as a painful retrofit later.
Light mode and Vercel deployment both get *much* harder if bolted on after feature
code exists, so we lay them as foundation.

## Outcomes (definition of done)
- [ ] A running app scaffold with TypeScript, lint, format, and test all wired.
- [ ] A **CSS-variable theming system** in place: current dark "terminal" aesthetic
      (orange-on-near-black) expressed entirely through variables, with the structure
      ready for a light theme to drop in later. (Don't build light mode yet — just
      make it a one-theme-file addition, not a refactor.)
- [ ] App **deployed to Vercel**, reachable at a public URL.
- [ ] **CI/CD:** merges to `main` auto-deploy; PRs get Vercel preview deployments.
- [ ] **Env-var config** scaffolded: `.env.example` committed with placeholders,
      `.env` gitignored, app reads config from env (no hardcoded secrets — CLAUDE.md).
- [ ] A trivial themed placeholder page proving the theme system + deploy both work.

## Explicitly OUT of scope for this phase
- No SEC/EDGAR data, no real ticker prices, no auth, no AI. Those are later phases.
- No light theme implementation yet — only the *capability* for one.

## Suggested approach (Claude: research in Plan Mode, then propose before building)
1. Recommend a stack that deploys cleanly to Vercel and tell me the trade-offs
   before scaffolding. State your pick and why.
2. Establish the design-token / CSS-variable layer first, then build the placeholder
   page on top of it — not the other way round.
3. Set up the Vercel project + CI so the *first* thing that happens is a successful
   deploy of an near-empty themed page. Prove the pipeline before adding surface area.
4. Confirm the env-var pattern works end to end (a dummy var read at runtime).

## Open questions for me (ask these BEFORE building — they affect architecture)
- Framework preference, or do you want my recommendation? (This is a real fork.)
- Do you already have a Vercel account / GitHub repo connected, or set that up too?
- Any preference on the styling approach (CSS modules / Tailwind / vanilla-extract)?
  This interacts with the theming system, so worth deciding now.

## Notes carried from the roadmap principles
- Theme via CSS variables from day one (this whole phase exists partly for that).
- Ship continuously — keep `main` always deployable from here on.
- **Persistence today is SQLite** (see `docs/adr/0002-sqlite-now-postgres-deferred.md`).
  Postgres / Supabase remains the target if/when we need user accounts or move to
  ephemeral hosting. SQLAlchemy 2.0 means the swap is a connection-string change,
  not a rewrite — but it is still a migration, not a no-op.
- Per CLAUDE.md: branch off main, commit incrementally, open a PR, don't merge it
  yourself, narrate in tech + product lenses, and don't ask permission for
  reversible actions — but DO push back on the architectural choices above.
