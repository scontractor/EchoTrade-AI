# plan.md — Verify the AI Signals pipeline end-to-end

> **Working spec for what we're doing NOW.** Replace when this chunk ships.
> Goal: prove our headline AI feature actually works, on open-source models,
> without being blocked by slow local inference. Resolves the biggest unknown
> in the app (signals are built but never verified end-to-end).

## Context (verified against the real code)
- `app/signals/analyst.py` uses an OpenAI-compatible client. Backend is set by three
  env vars in `app/config.py`: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (default:
  local Ollama, `llama3.1:8b`).
- The endpoint is `GET /investors/{id}/signals` in `app/main.py`. It builds a diff +
  sentiment prompt, calls the LLM, and parses JSON into `PortfolioAnalysis`.
- Local Ollama is "installed but unverified" AND my machine is CPU-only/16GB, so local
  inference will be slow. **We verify via a free hosted OSS backend instead** — the
  code already supports this with zero changes (see ADR 0001).

## Outcomes (definition of done)

✅ **Picked Groq** (free tier, `llama-3.3-70b-versatile`) — fastest, truly free,
   supports JSON mode. Documented alongside Ollama and other alternatives.

✅ **Configured via `.env` only** — `.env.example` has the Groq block ready to
   uncomment. Zero code changes needed to switch backends.

- [ ] **Run the endpoint end-to-end** for at least 2 investors — confirm real
      `PortfolioAnalysis` output, not an error. *(Groq key obtained; run pending.)*

✅ **Three code issues fixed** — 502 error handling, stale Anthropic docstrings,
   `response_format` confirmed supported on Groq.

✅ **README documented** — Groq key setup, env vars, model choice, JSON mode note,
   local-vs-hosted switch, Running Tests section.

✅ **Tests written** — 6 pytest cases for `_parse_response`: clean JSON, fenced JSON,
   prose-wrapped, garbage → ValueError, empty → ValueError. All passing.

## Issues found in review — fix these here
1. **No graceful failure on bad model output.** `analyze()` calls `_parse_response`,
   which raises `ValueError` on unparseable output, but the route doesn't catch it —
   a malformed LLM response (common with smaller open models) will 500 the endpoint.
   Wrap the LLM call + parse in try/except and return a clear error (e.g. 502 with
   "model returned unparseable output") instead of crashing. Smaller open models are
   exactly the ones that occasionally ignore the JSON instruction, so this matters.
2. **Stale docstrings reference Anthropic.** `app/main.py` line ~8 says signals
   "requires ANTHROPIC_API_KEY" and line ~222 mentions "Claude commentary". The code
   uses the OSS LLM, not Anthropic. Fix these comments to match reality (README was
   already fixed; these inline docs were missed).
3. **`response_format={"type":"json_object"}` isn't universally supported.** Some
   hosted/open backends reject or ignore this param. Confirm the chosen backend
   supports it; if not, rely on the prompt + the existing fence-stripping (which is
   why that parsing safety net exists). Note the outcome in the README.

## Explicitly OUT of scope
- No local-Ollama performance tuning (we're deliberately using hosted to sidestep it).
- No deployment, auth, or 13F caching — those are later roadmap items.

## Open questions for me
- *(resolved)* Groq chosen; `llama-3.3-70b-versatile` confirmed as the model.

## Per CLAUDE.md
Branch off main, commit incrementally, open a PR (don't merge it yourself), narrate in
tech + product lenses, teach me the concepts (I'm a PM learning), don't ask permission
for reversible actions but DO push back on direction. Update `docs/architecture.md` if
the data flow changes (the Ollama node becomes "configurable OSS backend"). Write an
ADR only if we make a real new decision (e.g. "Groq is our default hosted backend").