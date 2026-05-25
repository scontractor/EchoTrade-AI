# Project Working Agreement

> Most important rules are at the top. Claude pays most attention to what's near the top. Keep this file under ~200 lines.

## TIER 1 — HARD RULES (check before every action)

### Plan before building
- For anything touching 3+ files, introducing a dependency, or making an
  architectural choice: **do not write code yet.** Research, then propose an
  approach with trade-offs, then wait for my "go."
- If I could describe the change as a one-sentence diff, skip the plan and just do it.

### Asking vs. proceeding
- **Do NOT ask me permission questions** for reversible, low-risk actions
  (reading files, running tests, formatting, obvious small edits). Just do them
  and tell me after.
- **DO push back and challenge me** when: the approach has a meaningfully simpler
  alternative, a decision is hard to reverse, there's an architectural fork, or my
  request seems to conflict with an earlier decision or with quality/security.
  Surface the concern, state your recommendation, then let me decide.
- If a request is genuinely ambiguous in a way that affects architecture, ask ONE
  sharp question. Otherwise state your assumption explicitly and proceed.

### Models: open-source only, served via Nebius
- **Use open-source / open-weight models only.** Never use proprietary models
  (OpenAI GPT, Anthropic Claude, Google Gemini, etc.) anywhere in the product —
  not for the core task model, and not for any "LLM-as-a-judge" / evaluation /
  scoring component.
- **Serve them via Nebius Token Factory** as our inference provider. Don't
  introduce a different hosted provider without asking me first.
- **All LLM calls live behind an AI-features flag/toggle.** If AI features are
  not enabled, the app must run with no LLM calls at all. Keep the LLM layer
  cleanly separated so it can be switched off without breaking core functionality.
- Pick the **best open model suited to each specific task**, not one model for
  everything (a strong general model for core reasoning, a smaller/faster open
  model for the judge or latency-sensitive paths). When you choose one, tell me
  which and why.
- Keep the model layer **provider-abstracted** — wrap inference calls so we could
  swap Nebius for local/self-hosted serving later without rewriting the app.
- If a library quietly calls a proprietary LLM API under the hood, surface it
  before adding it.
- **Never hardcode or commit secrets.** Read the Nebius API key (and any other
  credentials) from environment variables — never paste keys into source, configs,
  or commits. Keep `.env` (and any local secrets file) in `.gitignore`, and provide
  a committed `.env.example` with placeholder values so setup is documented. If you
  ever spot a secret about to be committed, stop and flag it.

### Default to open-source tools
- **Prefer open-source software for everything** — frameworks, libraries,
  databases, infra, tooling. When choosing between options, the OSS one wins unless
  there's a clear, stated reason not to.
- Managed hosting *of* open-source software (e.g. Supabase hosting Postgres) is fine
  as a starting point — but prefer choices that keep us **portable**: avoid lock-in
  to closed ecosystems, and favor tools we could self-host later without a rewrite.
- When you pick a dependency, prefer well-maintained OSS with a permissive license.
  If the best option for a task is proprietary, say so and explain the trade-off
  before adding it — don't silently reach for it.

### Narrate in two lenses
While working, tell me what you're doing from BOTH perspectives:
- **Tech:** what you changed and why (pattern, trade-off, what it touches).
- **Product:** what this means for the user/agent consuming it (why it matters,
  what experience it creates).
Example: "Adding a cursor-based pagination layer (tech) so large result sets load
incrementally instead of timing out, which keeps the UI responsive for power users (product)."

### Teach me as we go (I'm a PM, not an engineer)
- I'm a product manager learning engineering by building this. Optimise for my
  learning, not just for shipping code.
- **Explain new concepts in plain language the first time they come up** — what it
  is, why we're using it, and the one-sentence version I could repeat to an engineer.
  Define jargon inline (e.g. "a migration — a versioned change to the database shape").
- Prefer the **standard, conventional way** of doing things over clever tricks, and
  say when something IS the industry-standard pattern so I learn the norm.
- When you make a choice with alternatives, briefly name what else exists and why we
  didn't pick it — that's how I build judgment.
- If I ask "why," treat it as a real question, not a challenge — give me the mental
  model, not just the fix.
- Keep the teaching proportional: a sentence or two inline, not a lecture. Offer to
  go deeper rather than dumping everything.

### Commit like a pro
- Commit after each logical unit of work — never one giant commit at the end.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`.
- One concern per commit. Never bundle unrelated changes.
- Never commit secrets, API keys, `.env` files, or generated artifacts.
- After a feature lands and tests pass = a commit boundary.

### Branch + PR per piece of work
- **For any real piece of functionality, create a fresh branch** off the main
  branch first — don't build real work directly on `main`. Name it descriptively:
  `feat/<short-name>`, `fix/<short-name>`, etc.
- Commit incrementally on that branch (per the rules above).
- When the work is complete and tests pass, **open a PR** with a clear title and a
  short description of what changed and why (tech + product framing).
- For throwaway spikes or tiny experiments, skip the ceremony — work on a scratch
  branch and don't bother with a PR. Use judgment; if unsure whether something is
  "real," ask me.
- One PR = one coherent piece of work. If we pivot to something new mid-stream,
  branch again rather than piling it on.
- Tell me the branch name when you create it, and the PR link when you open it.
- **Open PRs, but never merge them yourself.** Merging is my call — it's my review
  checkpoint before anything hits the main branch.

## TIER 2 — QUALITY BAR

Build things people AND agents actually want to use:
- **Works first, clever second.** Prefer the boring, correct solution.
- **Handle the unhappy path.** Errors, empty states, loading, bad input.
- **Agent-friendly:** clear interfaces, typed/documented inputs and outputs,
  predictable errors, no hidden global state. If an API is awkward for an agent
  to call, it's awkward for a human too.
- **Tests for anything non-trivial.** At minimum, the happy path + one edge case.
- Leave the code readable for the next person (which might be me in a week).

## TIER 3 — PROJECT SPECIFICS  (fill these in)

- **Stack:** <e.g. TypeScript, React, Node, Postgres>
- **Build:** `<command>`
- **Test:** `<command>`
- **Lint/format:** `<command>`
- **Run locally:** `<command>`
- **Architecture notes:** <key patterns, folder conventions, what NOT to touch>
- **Conventions:** <naming, error handling, state management preferences>

## WORKFLOW REMINDERS

- When uncertain, default to research + recommendation over silent guessing.
- When context gets long, suggest `/compact` after we hit a milestone.
- Surface trade-offs I might not see. I'd rather be slowed down by a good question
  than fast on a wrong assumption.

### Record architectural decisions (ADRs)
- When we make a significant, hard-to-reverse, or non-obvious technical decision,
  record it as an **ADR** (Architecture Decision Record) in `docs/decisions/`.
- One file per decision, numbered: `0001-short-title.md`, `0002-...`, etc.
- Keep each ADR short and use this structure:
  - **Title** — the decision in a phrase.
  - **Status** — Accepted / Superseded / Proposed.
  - **Context** — what problem/constraint forced a choice.
  - **Decision** — what we chose.
  - **Consequences** — trade-offs, what it enables, what to revisit later.
- Before re-opening a settled question, check `docs/decisions/` first — if it's
  already decided, don't re-litigate it unless something material has changed.
- When you make a decision worth recording, write the ADR as part of the same PR.

### Standard repo files
- During Phase 0 scaffolding, create `README.md` (what it is + setup + run),
  `.gitignore` (must cover `.env`, secrets, deps, build artifacts), and
  `.env.example` (placeholder env vars). Keep the README current as the app grows.

### Keep a living architecture diagram
- Maintain `docs/architecture.md` with a **Mermaid diagram** of the system: the
  main components (frontend, backend/API, database, external services like Supabase,
  Nebius, EDGAR, market-data), and how data flows between them.
- Mermaid is text-based, so it lives in git and renders automatically on GitHub —
  no diagramming tool needed, and it diffs like code.
- **Update the diagram in the same PR whenever we add or change a component or a
  data flow.** A stale diagram is worse than none.
- Keep it readable for a non-engineer: label arrows with what flows ("user watchlist
  saved", "filing data fetched"), not just connections.
- When you update it, give me a one-line plain-English summary of what changed in
  the architecture and why.
