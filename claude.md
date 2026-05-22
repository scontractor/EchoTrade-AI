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

### Narrate in two lenses
While working, tell me what you're doing from BOTH perspectives:
- **Tech:** what you changed and why (pattern, trade-off, what it touches).
- **Product:** what this means for the user/agent consuming it (why it matters,
  what experience it creates).
Example: "Adding a cursor-based pagination layer (tech) so large result sets load
incrementally instead of timing out, which keeps the UI responsive for power users (product)."

### Commit like a pro
- Commit after each logical unit of work — never one giant commit at the end.
- Conventional commits: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`.
- One concern per commit. Never bundle unrelated changes.
- Never commit secrets, API keys, `.env` files, or generated artifacts.
- After a feature lands and tests pass = a commit boundary.

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
